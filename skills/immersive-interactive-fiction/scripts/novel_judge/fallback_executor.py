from __future__ import annotations

"""Host-owned fallback executor for weak or unavailable model tasks.

Fallbacks produce candidates/scaffolds only. They never write canonical state,
Graph, files, or Gate records. A caller must still run the normal host gates.
"""

from typing import Any

from .canonical import sha256_json
from .input_router import classify_input
from .intent import make_intent, parse_player_text
from .storylets import available_storylets


def _envelope(task: str, *, status: str, method: str, state: dict[str, Any], output: dict[str, Any], reason: str = "") -> dict[str, Any]:
    return {"schema": "minis.host-fallback-result.v1", "task": task, "status": status,
            "method": method, "reason": reason, "source_state_hash": state.get("state_hash"),
            "authority": {"may_write_files": False, "may_commit_state": False, "may_modify_graph": False},
            "output": output, "output_hash": sha256_json(output)}


def fallback_intent(state: dict[str, Any], actor_id: str, raw_input: str) -> dict[str, Any]:
    route = classify_input(raw_input)
    if route.get("requires_clarification"):
        return _envelope("intent_extract", status="clarification", method="deterministic_router",
                         state=state, output={"type": "ambiguous_intent", "confidence": route.get("confidence", 0.0),
                                               "ambiguities": [route.get("clarification_prompt") or "input is underspecified"],
                                               "routing": route})
    try:
        intent = parse_player_text(actor_id, raw_input)
        return _envelope("intent_extract", status="candidate", method="deterministic_parser", state=state,
                         output={"type": intent["type"], "targets": intent["targets"], "parameters": intent["parameters"],
                                 "confidence": 1.0, "ambiguities": [], "intent": intent})
    except Exception as exc:
        return _envelope("intent_extract", status="clarification", method="deterministic_router", state=state,
                         output={"type": "ambiguous_intent", "confidence": 0.0, "ambiguities": [type(exc).__name__]})


def fallback_npc_plan(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    cards = available_storylets(state, actor_id=actor_id)
    if not cards:
        return _envelope("npc_plan", status="no_candidate", method="host_storylet_solver", state=state,
                         output={"actor_id": actor_id, "goal": "maintain current scene state", "action_type": "wait",
                                 "targets": [], "reason_fact_ids": []}, reason="no available storylet")
    card = cards[0]
    candidates = card.get("candidate_intents") or [{"type": "wait", "targets": []}]
    candidate = candidates[0] if isinstance(candidates[0], dict) else {"type": str(candidates[0]), "targets": []}
    return _envelope("npc_plan", status="candidate", method="host_storylet_solver", state=state,
                     output={"actor_id": actor_id, "goal": card.get("dramatic_question") or card.get("pressure") or "advance active thread",
                             "action_type": candidate.get("type", "wait"), "targets": list(candidate.get("targets", [])),
                             "reason_fact_ids": list(card.get("requires_facts", [])), "storylet_id": card.get("id")})


def fallback_scene_manifest(state: dict[str, Any], actor_id: str, *, handoff_owner: str | None = None) -> dict[str, Any]:
    actor = state.get("actors", {}).get(actor_id, {})
    owner = handoff_owner or actor_id
    location = actor.get("location", "UNKNOWN")
    return _envelope("scene_manifest", status="candidate", method="host_scene_skeleton", state=state,
                     output={"scene_function": "transition", "focal_change": "one observable local change",
                             "beats": [f"anchor {location}", "present one bounded pressure", "leave an open handoff"],
                             "protected_unknowns": ["unobserved motives", "unrevealed facts"], "handoff_owner": owner})


def fallback_render(state: dict[str, Any], actor_id: str, *, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    actor = state.get("actors", {}).get(actor_id, {})
    location = actor.get("location", "未知位置")
    focal = (manifest or {}).get("focal_change", "一個可觀察的局部變化")
    text = f"【場景骨架】{location}。\n{focal}。\n（此為模型不可用時的可恢復骨架，尚未是可提交正文。）"
    return _envelope("render", status="scaffold", method="deterministic_scene_skeleton", state=state,
                     output={"text": text, "claimed_facts": [], "action_manifest": [], "player_actions": []},
                     reason="deterministic fallback is not prose-quality approval")


def fallback_repair(state: dict[str, Any], text: str, issues: list[dict[str, Any]]) -> dict[str, Any]:
    # Do not invent a rewrite. Only remove obvious meta markers when explicitly
    # requested; otherwise preserve text and report author escalation.
    cleaned = text
    fixed: list[str] = []
    for issue in issues:
        iid = str(issue.get("issue_id") or issue.get("id") or "")
        if issue.get("code") in {"META_LEAK", "meta_leak"}:
            cleaned = cleaned.replace("[DRAFT]", "").replace("[META]", "").strip()
            if iid: fixed.append(iid)
    return _envelope("repair", status="candidate" if fixed else "escalate", method="deterministic_issue_patch", state=state,
                     output={"text": cleaned, "fixed_issue_ids": fixed}, reason="only explicit deterministic patches applied")


def fallback_blind_read(state: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    """Host fallback blind read: safety + high-confidence Narrative QA only.

    This never claims literary quality, reader enjoyment, or author preference.
    """
    from .authority_layers import build_authority_report, normalize_finding
    from .narrative_qa import inspect_prose

    issues: list[dict[str, Any]] = []
    layered: list[dict[str, Any]] = []
    if not isinstance(output, dict) or not isinstance(output.get("text"), str) or not output["text"].strip():
        issues.append({"code": "EMPTY_RENDER", "severity": "P0"})
        layered.append(normalize_finding({
            "layer": "CANON_INTEGRITY", "code": "EMPTY_RENDER", "severity": "P0", "confidence": "high",
            "claim": "render text is empty", "blocks_commit": True, "author_overridable": False,
        }))
    for item in output.get("player_actions", []) if isinstance(output, dict) and isinstance(output.get("player_actions"), list) else []:
        issues.append({"code": "PLAYER_AGENCY_CLAIM", "severity": "P0", "claim": item})
        layered.append(normalize_finding({
            "layer": "CANON_INTEGRITY", "code": "PLAYER_AGENCY_CLAIM", "severity": "P0", "confidence": "high",
            "claim": "output claims a player action", "blocks_commit": True, "author_overridable": False,
            "details": {"claim": item},
        }))
    text = output.get("text", "") if isinstance(output, dict) else ""
    if isinstance(text, str) and text.strip():
        qa = inspect_prose(text)
        for item in qa.get("findings") or []:
            layered.append(item)
            issues.append({
                "code": item.get("code"),
                "severity": item.get("severity"),
                "claim": item.get("claim"),
                "layer": item.get("layer"),
                "confidence": item.get("confidence"),
                "evidence": item.get("evidence"),
                "span": item.get("span"),
                "minimal_fix": item.get("minimal_fix"),
            })
    authority = build_authority_report(
        findings=layered,
        source="fallback_blind_read",
        subject={"state_hash": state.get("state_hash"), "task": "blind_read"},
    )
    hard_fail = any(i.get("severity") == "P0" for i in issues)
    status = "fail" if hard_fail else ("warn" if issues else "pass")
    summary = (
        "deterministic safety + narrative QA completed; not a literary quality score"
        if not hard_fail else
        "deterministic blind read found blocking issues"
    )
    return _envelope(
        "blind_read",
        status=status,
        method="deterministic_narrative_checks",
        state=state,
        output={
            "status": status,
            "issues": issues,
            "summary": summary,
            "authority": authority,
            "may_commit": authority["commit"]["may_commit"],
            "claims": {
                "literary_quality_judged": False,
                "reader_preference_judged": False,
                "author_preference_judged": False,
                "is_beta_reader": False,
                "machine_prescan_only": True,
            },
        },
        reason="fallback blind read is safety/QA only",
    )


def execute_host_fallback(state: dict[str, Any], *, task: str, actor_id: str, input_text: str = "",
                          approved_manifest: dict[str, Any] | None = None, issues: list[dict[str, Any]] | None = None,
                          candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    if task == "intent_extract": return fallback_intent(state, actor_id, input_text)
    if task == "npc_plan": return fallback_npc_plan(state, actor_id)
    if task == "scene_manifest": return fallback_scene_manifest(state, actor_id, handoff_owner=(approved_manifest or {}).get("handoff_owner"))
    if task == "render": return fallback_render(state, actor_id, manifest=approved_manifest)
    if task == "repair": return fallback_repair(state, input_text, issues or [])
    if task == "blind_read": return fallback_blind_read(state, candidate or {"text": input_text})
    raise ValueError(f"unsupported fallback task: {task}")
