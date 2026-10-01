from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .context import build_context
from .author_corrections import infer_project_root, attach_author_corrections
from .storylets import available_storylets
from .contracts import ACTION_TYPES
from .canonical import sha256_json
from .context_budget import (
    admit_context_dict, CONTEXT_WINDOW_64K, POLICY_LOSSLESS,
    context_policy_for_window, default_context_window,
)
from .memory import compile_memory_context
from .production_inputs import (
    bind_generation_root, record_used_sources, resolve_writing_inputs_manifest,
)


def _production_input_context(state: dict[str, Any], *, actor_id: str, store: Any = None) -> dict[str, Any] | None:
    """Load the verified event-derived read model when available."""
    working = bind_generation_root(state, store=store)
    inputs_root, status_path = resolve_writing_inputs_manifest(working, store=store)
    if not status_path:
        return None
    project_root = Path(str(working.get('_production_project_root') or working.get('project_root') or ''))
    if not str(project_root):
        return None
    manifest = json.loads(status_path.read_text(encoding='utf-8'))
    meta = (manifest.get('context') or {}).get(actor_id)
    if not isinstance(meta, dict): return None
    path = project_root / meta.get('path','')
    if not path.is_file(): return None
    pack = json.loads(path.read_text(encoding='utf-8'))
    if pack.get('context_hash') != meta.get('context_hash'): return None
    memory_meta = (manifest.get('memory') or {}).get(actor_id, {})
    memory_path = project_root / memory_meta.get('path','')
    if not memory_path.is_file(): return None
    memory = json.loads(memory_path.read_text(encoding='utf-8'))
    if memory.get('projection_hash') != memory_meta.get('projection_hash'): return None
    return {'schema':'minis.verified-production-read-model.v1','manifest_hash':manifest.get('manifest_hash'),
            'context':pack,'episodes':memory.get('episodes',[]),'source_state_hash':manifest.get('source_state_hash'),
            'inputs_root':str(inputs_root),'project_root':str(project_root)}

TASK_SCHEMAS = {
    "intent_extract": {"required": ["type", "targets", "parameters", "confidence", "ambiguities"]},
    "npc_plan": {"required": ["actor_id", "goal", "action_type", "targets", "reason_fact_ids"]},
    "scene_manifest": {"required": ["scene_function", "focal_change", "beats", "protected_unknowns", "handoff_owner"]},
    "render": {"required": ["text", "claimed_facts", "action_manifest", "player_actions"]},
    "repair": {"required": ["text", "fixed_issue_ids"]},
    "blind_read": {"required": ["status", "issues", "summary"]},
}


def _compact_storylets(state: dict[str, Any], actor_id: str) -> list[dict[str, Any]]:
    return [
        {"id": s.get("id"), "dramatic_question": s.get("dramatic_question"),
         "pressure": s.get("pressure"), "candidate_intents": s.get("candidate_intents", [])[:4]}
        for s in available_storylets(state, actor_id=actor_id)[:5]
    ]


def _episode_ids(records: list[Any]) -> list[str]:
    return [x.get("memory_id") for x in records if isinstance(x, dict) and x.get("memory_id")]


def compile_model_task(state: dict[str, Any], *, task: str, actor_id: str,
                       input_text: str = "", approved_manifest: dict[str, Any] | None = None,
                       issues: list[dict[str, Any]] | None = None,
                       context_window: int | None = None,
                       context_policy: str | None = None,
                       store: Any = None, project_root: str | Path | None = None,
                       persist_used_sources: bool = True) -> dict[str, Any]:
    """Compile one small, capability-agnostic model job.

    The model receives no hidden truth and no write authority. Even an L1
    model can be restricted to prose-only output; JSON repair/parsing remains
    a host responsibility. Canonical state is never mutated.

    Every model uses lossless-addressable by default: original text is
    inlined or catalogued, never summarized away. Window size only limits
    this turn's inline budget. lossy-admission requires an explicit opt-in.
    """
    if task not in TASK_SCHEMAS:
        raise ValueError(f"unsupported task: {task}")
    if context_window is None:
        context_window = default_context_window()
    policy = context_policy_for_window(int(context_window), context_policy)
    working = bind_generation_root(state, store=store, project_root=project_root)
    context = build_context(working, audience="player" if actor_id in {"player", "user"} else "npc", actor_id=actor_id)
    production_read_model = _production_input_context(working, actor_id=actor_id, store=store)
    if production_read_model is not None:
        # Use the verified pack as-is. Do not dump every projected episode into
        # a 64K prompt; selected_source_ids already record the retrieval cut.
        # Lossless windows may expand to the full episode list without summarizing.
        context = production_read_model["context"]
        context["production_read_model"] = {
            "schema": production_read_model["schema"],
            "manifest_hash": production_read_model["manifest_hash"],
            "source_state_hash": production_read_model["source_state_hash"],
            "episode_count": len(production_read_model.get("episodes") or []),
        }
        episodes = production_read_model.get("episodes") or []
        addressable = _episode_ids(episodes) or list(context.get("addressable_source_ids") or [])
        if addressable:
            context["addressable_source_ids"] = addressable
        if policy == POLICY_LOSSLESS and episodes:
            memory = dict(context.get("memory_context") or {})
            memory["memories"] = episodes
            memory["retrieval_cut"] = False
            context["memory_context"] = memory
    elif policy == POLICY_LOSSLESS and actor_id:
        actor = (working.get("actors") or {}).get(actor_id) or {}
        here = actor.get("location")
        memory_query = " ".join(str(x) for x in (actor.get("immediate_goal"), here) if x)
        context["memory_context"] = compile_memory_context(
            working, actor_id, query=memory_query, top_k=None,
        )
        context["addressable_source_ids"] = _episode_ids((context.get("memory_context") or {}).get("memories") or [])
    project_root = infer_project_root(state)
    character_ids = list((context.get("actors") or {}))
    if actor_id:
        character_ids = list(dict.fromkeys([actor_id, *character_ids]))
    scene_kind = state.get("scene_kind") or (state.get("scene") or {}).get("kind")
    attach_author_corrections(
        context,
        project_root,
        character_ids=character_ids or None,
        scene_kind=scene_kind,
    )
    profile = "render" if task in {"render", "repair"} else ("blind_read" if task == "blind_read" else ("plan" if task in {"npc_plan", "scene_manifest"} else "interactive"))
    context = admit_context_dict(context, profile=profile, context_window=int(context_window),
                                 context_policy=policy)
    context_admission = context.get("context_admission", {})
    if context_admission.get("admission") == "reject":
        raise ValueError("context admission rejected: required sources exceed budget")
    packet = {
        "schema": "minis.model-task.v1", "task": task, "actor_id": actor_id,
        "input_text": input_text, "context": context,
        "context_admission": context_admission,
        "context_policy": policy,
        "storylet_candidates": _compact_storylets(state, actor_id),
        "approved_manifest": approved_manifest or {}, "issues": issues or [],
        "output_contract": TASK_SCHEMAS[task],
        "authority": {
            "may_propose": True, "may_write_files": False, "may_commit_state": False,
            "may_modify_graph": False, "may_control_player": False,
        },
        "failure_policy": "return the smallest valid output; use UNKNOWN instead of inventing",
        "structured_output": {"preferred": "provider JSON schema or grammar-constrained decoding", "fallback": "host JSON extraction then semantic validation", "schema_task": task},
        "source_state_hash": state.get("state_hash"),
    }
    packet["production_read_model"] = production_read_model["schema"] if production_read_model else None
    packet["production_source_manifest_hash"] = production_read_model["manifest_hash"] if production_read_model else None
    packet["generation_read_model"] = "verified" if production_read_model else "canonical_fallback"
    admitted = set((context_admission or {}).get("selected_sources") or [])
    inline_ids = _episode_ids((context.get("memory_context") or {}).get("memories") or [])
    addressable = list(context.get("addressable_source_ids") or [])
    if production_read_model is not None:
        all_ids = _episode_ids(production_read_model.get("episodes") or []) or addressable
        if policy == POLICY_LOSSLESS:
            used = inline_ids or all_ids
            addressable = all_ids or addressable or used
            packet["generation_read_model"] = "verified"
        elif "context.memory_context" in admitted:
            selected = list(production_read_model["context"].get("selected_source_ids") or inline_ids)
            used = [x for x in selected if x in inline_ids] if inline_ids else selected
            addressable = all_ids or addressable or used
        else:
            used = inline_ids
            packet["generation_read_model"] = "verified_without_memory_admission"
            addressable = all_ids or addressable or used
    else:
        used = inline_ids
        addressable = addressable or used
    packet["used_source_ids"] = used
    packet["addressable_source_ids"] = addressable
    packet["forgotten_source_ids"] = list(context_admission.get("forgotten_sources") or [])
    context["used_source_ids"] = used
    packet["generation_root"] = working.get("_production_project_root")
    if persist_used_sources and used:
        sidecar = record_used_sources(
            working.get("_production_project_root"), actor_id, used,
            store=store, state=working,
            extra={"generation_read_model": packet["generation_read_model"],
                   "task": task, "source_state_hash": working.get("state_hash"),
                   "context_policy": policy},
        )
        packet["used_sources_sidecar"] = bool(sidecar)
    else:
        packet["used_sources_sidecar"] = False
    packet["task_hash"] = sha256_json({k: v for k, v in packet.items() if k != "task_hash"})
    return packet


def validate_model_result(packet: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    task = packet.get("task")
    required = set(TASK_SCHEMAS.get(str(task), {}).get("required", []))
    missing = sorted(required - set(result if isinstance(result, dict) else {}))
    stale = result.get("task_hash") != packet.get("task_hash") if isinstance(result, dict) else True
    errors = ([{"code": "MODEL_RESULT_NOT_OBJECT"}] if not isinstance(result, dict) else [])
    errors += [{"code": "MODEL_RESULT_MISSING_FIELDS", "fields": missing}] if missing else []
    errors += [{"code": "MODEL_RESULT_STALE_TASK"}] if stale else []
    if isinstance(result, dict) and task == "npc_plan" and packet.get("actor_id") and result.get("actor_id") != packet.get("actor_id"):
        errors.append({"code": "MODEL_RESULT_ACTOR_ID_DRIFT", "expected": packet.get("actor_id"), "actual": result.get("actor_id")})
    if isinstance(result, dict) and task == "scene_manifest":
        owner = (packet.get("approved_manifest") or {}).get("handoff_owner")
        if owner and result.get("handoff_owner") != owner:
            errors.append({"code": "MODEL_RESULT_HANDOFF_OWNER_DRIFT", "expected": owner, "actual": result.get("handoff_owner")})
    if isinstance(result, dict) and task == "intent_extract" and not missing:
        typ = result.get("type"); confidence = result.get("confidence"); ambiguities = result.get("ambiguities")
        if typ not in ACTION_TYPES | {"ambiguous_intent"}:
            errors.append({"code": "MODEL_RESULT_INVALID_INTENT_TYPE", "value": typ})
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0.0 <= float(confidence) <= 1.0:
            errors.append({"code": "MODEL_RESULT_INVALID_CONFIDENCE", "value": confidence})
        if not isinstance(ambiguities, list) or any(not isinstance(x, str) for x in ambiguities):
            errors.append({"code": "MODEL_RESULT_INVALID_AMBIGUITIES"})
        if typ == "ambiguous_intent" and not ambiguities:
            errors.append({"code": "MODEL_RESULT_AMBIGUITY_REASON_REQUIRED"})
    if isinstance(result, dict):
        from .model_semantics import validate_task_semantics
        errors += validate_task_semantics(str(task), result)
    return {"ok": not errors, "status": "pass" if not errors else "fail", "task": task,
            "errors": errors, "source_state_hash": packet.get("source_state_hash")}
