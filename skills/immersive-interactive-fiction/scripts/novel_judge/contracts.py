from __future__ import annotations

from typing import Any

from .canonical import canonical_json, state_hash
from .errors import JudgeError, SCHEMA_ERROR

STATE_SCHEMA = "minis.interactive-state.v3"
INTENT_SCHEMA = "minis.interactive-intent.v1"
DELTA_SCHEMA = "minis.interactive-state-delta.v1"
TURN_SCHEMA = "minis.interactive-turn-record.v1"
BRANCH_SCHEMA = "minis.interactive-branch-manifest.v1"
VALID_SCOPES = {"session", "experiment", "candidate-canon", "canon"}
ACTION_TYPES = {
    "observe", "observe_local", "move", "move_short", "speak", "ask", "take", "drop", "use", "wait",
    "rest_awake", "inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment",
    "explore", "explore_house", "macro_explore", "hide", "promise", "attempt", "npc_act", "world_tick", "scene_commit", "chapter_commit", "artifact_revision", "semantic_correction", "open", "close", "meta",
}
SOURCES = {"player_input", "npc_plan", "world_tick", "author", "model", "system"}


def require_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    missing = sorted(keys - set(value))
    if missing:
        raise JudgeError(SCHEMA_ERROR, f"{label} missing required keys", details={"missing": missing})


def validate_state_shape(state: dict[str, Any]) -> None:
    if not isinstance(state, dict):
        raise JudgeError(SCHEMA_ERROR, "state must be an object")
    require_keys(
        state,
        {"schema", "project_id", "session_id", "branch_id", "canon_scope", "revision",
         "clock", "world_truth", "actors", "knowledge", "reality", "events_head"},
        "state",
    )
    if state["schema"] != STATE_SCHEMA:
        raise JudgeError(SCHEMA_ERROR, "unsupported state schema", details={"schema": state.get("schema")})
    if state["canon_scope"] not in VALID_SCOPES:
        raise JudgeError(SCHEMA_ERROR, "invalid canon scope")
    if not isinstance(state["revision"], int) or state["revision"] < 0:
        raise JudgeError(SCHEMA_ERROR, "revision must be a non-negative integer")
    for key in ("world_truth", "actors", "knowledge", "reality"):
        if not isinstance(state[key], dict):
            raise JudgeError(SCHEMA_ERROR, f"state.{key} must be an object")
    if not isinstance(state["clock"], dict):
        raise JudgeError(SCHEMA_ERROR, "state.clock must be an object")


def validate_intent(intent: dict[str, Any]) -> None:
    if not isinstance(intent, dict):
        raise JudgeError(SCHEMA_ERROR, "intent must be an object")
    require_keys(intent, {"schema", "intent_id", "turn_id", "actor_id", "source", "type", "targets", "parameters"}, "intent")
    if intent["schema"] != INTENT_SCHEMA:
        raise JudgeError(SCHEMA_ERROR, "unsupported intent schema")
    if intent["source"] not in SOURCES:
        raise JudgeError(SCHEMA_ERROR, "invalid intent source")
    if intent["type"] not in ACTION_TYPES:
        raise JudgeError(SCHEMA_ERROR, "unsupported action type")
    if not isinstance(intent["targets"], list) or not isinstance(intent["parameters"], dict):
        raise JudgeError(SCHEMA_ERROR, "intent targets/parameters have invalid shape")


def validate_delta(delta: dict[str, Any]) -> None:
    require_keys(delta, {"schema", "delta_id", "turn_id", "source_intent_id", "operations", "candidate"}, "delta")
    if delta["schema"] != DELTA_SCHEMA or not isinstance(delta["operations"], list):
        raise JudgeError(SCHEMA_ERROR, "invalid delta schema")


def state_fingerprint(state: dict[str, Any]) -> str:
    return state_hash(state)


def stable_contract(value: Any) -> str:
    return canonical_json(value)
