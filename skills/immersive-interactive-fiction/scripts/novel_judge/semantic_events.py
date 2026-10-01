from __future__ import annotations

"""Typed semantic manifests for replayable world events.

JSON Patch remains the executable delta.  This module adds a hash-bound,
queryable description of intent/effects without becoming a second state
transition authority.
"""

from typing import Any
from .canonical import deep_copy, sha256_json

SCHEMA = "minis.event-semantic-delta.v1"


def _tokens(path: str) -> list[str]:
    return [x.replace("~1", "/").replace("~0", "~") for x in str(path).strip("/").split("/") if x]


def _effect(op: dict[str, Any]) -> dict[str, Any]:
    path = str(op.get("path", "")); parts = _tokens(path); verb = str(op.get("op", "unknown"))
    base: dict[str, Any] = {"effect_type": "state_field_changed", "operation": verb, "path": path}
    if verb != "remove": base["value"] = deep_copy(op.get("value"))
    if len(parts) >= 3 and parts[0] == "actors" and parts[2] == "location":
        base.update({"effect_type": "move_actor", "actor_id": parts[1], "location_id": op.get("value")})
    elif len(parts) >= 4 and parts[:2] == ["world_truth", "objects"] and parts[3] == "holder":
        base.update({"effect_type": "set_object_holder", "object_id": parts[2], "holder_id": op.get("value")})
    elif len(parts) >= 4 and parts[:2] == ["world_truth", "objects"] and parts[3] == "location":
        base.update({"effect_type": "set_object_location", "object_id": parts[2], "location_id": op.get("value")})
    elif len(parts) >= 3 and parts[0] == "knowledge" and parts[1] in {"player", "npcs"}:
        base.update({"effect_type": "update_actor_knowledge", "audience": parts[1], "actor_id": parts[2]})
    elif len(parts) >= 2 and parts[0] == "threads":
        base.update({"effect_type": "update_thread", "thread_scope": parts[1], "thread_path": "/".join(parts[2:])})
    elif len(parts) >= 3 and parts[0] == "relations":
        base.update({"effect_type": "update_relation", "source_actor_id": parts[1], "target_actor_id": parts[2]})
    elif len(parts) >= 2 and parts[0] == "clock":
        base.update({"effect_type": "set_clock", "clock_field": parts[1]})
    elif len(parts) >= 3 and parts[0] == "actors" and parts[2] in {"condition", "status"}:
        base.update({"effect_type": "update_actor_condition", "actor_id": parts[1]})
    elif len(parts) >= 3 and parts[0] == "reality" and parts[1] == "actors":
        base.update({"effect_type": "update_actor_reality", "actor_id": parts[2]})
    elif len(parts) >= 2 and parts[0] == "reality" and parts[1] == "environment":
        base.update({"effect_type": "update_environment"})
    return base


def _kind(action_type: str, effects: list[dict[str, Any]], scene_id: str | None) -> str:
    kinds = {x.get("effect_type") for x in effects}
    if not effects and scene_id: return "artifact_revision"
    if action_type == "meta": return "semantic_correction" if effects else "metadata_only"
    if action_type == "scene_commit": return "scene_state_transition"
    if action_type == "chapter_commit": return "chapter_state_transition"
    if action_type == "artifact_revision": return "artifact_revision"
    if kinds == {"move_actor"}: return "actor_movement"
    if kinds and kinds <= {"set_object_holder", "set_object_location"}: return "object_state_change"
    if "update_actor_knowledge" in kinds: return "knowledge_transition"
    if "update_thread" in kinds: return "thread_transition"
    if "set_clock" in kinds: return "scene_state_transition"
    return "world_state_transition" if effects else "no_state_change"


def compile_semantic_delta(*, turn_id: str, actor_id: str, action_type: str,
                           operations: list[dict[str, Any]], summary: str | None = None,
                           scene_id: str | None = None,
                           declared_effects: list[dict[str, Any]] | None = None,
                           semantic_kind: str | None = None) -> dict[str, Any]:
    inferred = [_effect(op) for op in operations]
    declared = deep_copy(declared_effects or [])
    if declared:
        covered: set[int] = set()
        inferred_by_index = {index: _effect(op) for index, op in enumerate(operations)}
        for index, effect in enumerate(declared):
            indices = effect.get("operation_indices") if isinstance(effect, dict) else None
            if not isinstance(indices, list) or not indices or not all(isinstance(x, int) and 0 <= x < len(operations) for x in indices):
                raise ValueError(f"declared semantic effect {index} requires non-empty valid operation_indices")
            covered.update(indices)
            for op_index in indices:
                inferred = inferred_by_index[op_index]
                # A declaration is descriptive metadata, never a second
                # transition authority.  Its executable identity must agree
                # with the operation it claims to describe.
                for key in ("effect_type", "operation", "path", "actor_id", "object_id",
                            "location_id", "holder_id", "audience", "source_actor_id",
                            "target_actor_id", "clock_field"):
                    if key in effect and effect.get(key) != inferred.get(key):
                        raise ValueError(f"declared semantic effect {index} contradicts operation {op_index}: {key}")
                if "value" in effect and effect.get("value") != inferred.get("value"):
                    raise ValueError(f"declared semantic effect {index} contradicts operation {op_index}: value")
        if covered != set(range(len(operations))):
            raise ValueError("declared semantic effects must cover every executable operation")
    effects = declared if declared else inferred
    for index, effect in enumerate(effects):
        if not isinstance(effect, dict) or not effect.get("effect_type"):
            raise ValueError(f"semantic effect {index} requires effect_type")
    kind = semantic_kind or _kind(action_type, effects, scene_id)
    readable = " ".join(str(summary or "").split())
    if not readable:
        labels = [str(x.get("effect_type")) for x in effects[:4]]
        readable = f"{turn_id}: " + (", ".join(labels) if labels else kind.replace("_", " "))
    value = {
        "schema": SCHEMA,
        "turn_id": str(turn_id),
        "semantic_kind": str(kind),
        "domain_intent": {"actor_id": str(actor_id), "action_type": str(action_type)},
        "summary": readable,
        "effects": effects,
        "effect_count": len(effects),
        "operations_hash": sha256_json(operations),
        "effect_source": "declared_and_validated" if declared else "deterministic_operation_inference",
    }
    value["semantic_hash"] = sha256_json(value)
    return value


def validate_semantic_delta(value: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA: raise ValueError("unsupported semantic delta schema")
    if not str(value.get("summary", "")).strip(): raise ValueError("semantic delta summary is empty")
    if value.get("operations_hash") != sha256_json(operations): raise ValueError("semantic delta is not bound to executable operations")
    if value.get("effect_count") != len(value.get("effects", [])): raise ValueError("semantic delta effect count mismatch")
    if value.get("semantic_hash") != sha256_json({k: v for k, v in value.items() if k != "semantic_hash"}): raise ValueError("semantic delta hash mismatch")
    return value
