from __future__ import annotations

from typing import Any

from .canonical import deep_copy, refresh_state_hash
from .contracts import STATE_SCHEMA, validate_state_shape
from .errors import JudgeError, SCHEMA_ERROR, STATE_HASH_MISMATCH
from .migrations import migrate_state


def empty_state(project_id: str, session_id: str, branch_id: str = "main", *, now: str = "", timezone: str = "Asia/Taipei") -> dict[str, Any]:
    state: dict[str, Any] = {
        "schema": STATE_SCHEMA,
        "project_id": project_id,
        "session_id": session_id,
        "branch_id": branch_id,
        "canon_scope": "session",
        "revision": 0,
        "state_hash": "",
        "clock": {"now": now, "tick": 0, "timezone": timezone},
        "world_truth": {"locations": {}, "objects": {}, "rules": {}, "events": {}},
        "world_public": {},
        "actors": {},
        "relations": {},
        "knowledge": {"truth": {}, "player": {}, "npcs": {}, "reader": {}},
        "reality": {"actors": {}, "environment": {}},
        "storylets": {"active": [], "cooldowns": {}, "beats": {}},
        "clocks": {},
        "threads": {"open": [], "resolved": []},
        "plans": {"npcs": {}, "world": {}},
        "memory": {"schema": "minis.actor-memory.v2", "episodic": {}, "reflections": {}, "working": {}, "archive": {}},
        "events_head": None,
        "last_turn_id": None,
        "metadata": {},
    }
    return refresh_state_hash(state)


def normalize_state(state: dict[str, Any], *, verify_hash: bool = True) -> dict[str, Any]:
    state = deep_copy(state)
    supplied = state.get("state_hash")
    if state.get("schema") != STATE_SCHEMA:
        state, _migration_report = migrate_state(state, target_schema=STATE_SCHEMA)
        supplied = None
    validate_state_shape(state)
    for key, default in {
        "world_public": {}, "relations": {}, "storylets": {"active": [], "cooldowns": {}, "beats": {}},
        "clocks": {}, "threads": {"open": [], "resolved": []}, "plans": {"npcs": {}, "world": {}},
        "memory": {"schema": "minis.actor-memory.v2", "episodic": {}, "reflections": {}, "working": {}, "archive": {}},
        "last_turn_id": None, "metadata": {},
    }.items():
        state.setdefault(key, default)
    supplied = supplied if supplied is not None else state.get("state_hash")
    refreshed = refresh_state_hash(state)
    if verify_hash and supplied and supplied != refreshed["state_hash"]:
        raise JudgeError(STATE_HASH_MISMATCH, "state hash does not match content", details={"supplied": supplied, "computed": refreshed["state_hash"]})
    return refreshed


def validate_state(state: dict[str, Any]) -> dict[str, Any]:
    return normalize_state(state, verify_hash=True)


def actor(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    try:
        return state["actors"][actor_id]
    except KeyError as exc:
        raise JudgeError("ACTOR_OR_ENTITY_NOT_FOUND", f"actor not found: {actor_id}", details={"actor_id": actor_id}) from exc


def location(state: dict[str, Any], location_id: str) -> dict[str, Any]:
    try:
        return state["world_truth"]["locations"][location_id]
    except KeyError as exc:
        raise JudgeError("ACTOR_OR_ENTITY_NOT_FOUND", f"location not found: {location_id}", details={"location_id": location_id}) from exc


def object_record(state: dict[str, Any], object_id: str) -> dict[str, Any]:
    try:
        return state["world_truth"]["objects"][object_id]
    except KeyError as exc:
        raise JudgeError("ACTOR_OR_ENTITY_NOT_FOUND", f"object not found: {object_id}", details={"object_id": object_id}) from exc
