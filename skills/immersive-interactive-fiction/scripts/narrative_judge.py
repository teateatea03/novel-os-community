"""Deterministic narrative state judge for Novel OS.

The judge never writes prose and never invents player intent. It evaluates a
candidate action against a small, explicit world state, then returns an
immutable next state, event, and diff. Standard-library only by design.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Tuple


class JudgeError(ValueError):
    pass


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def state_hash(state: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical(state).encode("utf-8")).hexdigest()


def _path_diff(before: Any, after: Any, path: str = "") -> List[Dict[str, Any]]:
    if type(before) is not type(after):
        return [{"path": path or "/", "before": before, "after": after}]
    if isinstance(before, dict):
        out: List[Dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            p = f"{path}/{key}"
            if key not in before:
                out.append({"path": p, "before": None, "after": after[key]})
            elif key not in after:
                out.append({"path": p, "before": before[key], "after": None})
            else:
                out.extend(_path_diff(before[key], after[key], p))
        return out
    if isinstance(before, list):
        out: List[Dict[str, Any]] = []
        for i in range(max(len(before), len(after))):
            p = f"{path}/{i}"
            if i >= len(before):
                out.append({"path": p, "before": None, "after": after[i]})
            elif i >= len(after):
                out.append({"path": p, "before": before[i], "after": None})
            else:
                out.extend(_path_diff(before[i], after[i], p))
        return out
    return [] if before == after else [{"path": path or "/", "before": before, "after": after}]


def _fail(action: Dict[str, Any], before: Dict[str, Any], code: str, message: str) -> Dict[str, Any]:
    return {
        "verdict": "deny",
        "reason_code": code,
        "message": message,
        "action_id": action.get("action_id"),
        "pre_state_hash": state_hash(before),
        "post_state_hash": state_hash(before),
        "diff": [],
        "events": [],
        "state": copy.deepcopy(before),
    }


def _actor(state: Dict[str, Any], actor_id: str) -> Dict[str, Any] | None:
    return state.get("actors", {}).get(actor_id)


def _connection(state: Dict[str, Any], location: str, target: str, via: str | None = None) -> Tuple[str, Dict[str, Any]] | None:
    loc = state.get("locations", {}).get(location, {})
    for name, edge in loc.get("connections", {}).items():
        if via and name != via:
            continue
        if isinstance(edge, dict) and edge.get("to") == target:
            return name, edge
    return None


def _connection_by_name(state: Dict[str, Any], location: str, via: str) -> Dict[str, Any] | None:
    edge = state.get("locations", {}).get(location, {}).get("connections", {}).get(via)
    return edge if isinstance(edge, dict) else None


def _agency_guard(state: Dict[str, Any], action: Dict[str, Any]) -> Tuple[str, str] | None:
    actor = _actor(state, action.get("actor_id", ""))
    if not actor:
        return ("UNKNOWN_ACTOR", "actor does not exist")
    if actor.get("kind") == "player" and action.get("source") != "player_input":
        return ("PLAYER_AGENCY_PROTECTED", "model or background process cannot decide the player's action")
    return None


def _validate_shape(state: Dict[str, Any], action: Dict[str, Any]) -> str | None:
    if not isinstance(state, dict) or not isinstance(action, dict):
        return "INVALID_INPUT"
    if state.get("schema_version") != "novel-state.v1":
        return "UNSUPPORTED_STATE_SCHEMA"
    if not action.get("action_id") or not action.get("actor_id") or not action.get("type"):
        return "INVALID_ACTION_SHAPE"
    return None


def _apply_domain(state: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, str, str, str]:
    actor_id = action["actor_id"]
    actor = state["actors"][actor_id]
    kind = action["type"]
    here = actor.get("location")

    if kind == "observe":
        return True, "OBSERVATION_RECORDED", "observation recorded without inventing facts", "observe"

    if kind == "speak":
        if not isinstance(action.get("text"), str) or not action["text"].strip():
            return False, "EMPTY_SPEECH", "speech must contain explicit text", ""
        return True, "SPEECH_RECORDED", "explicit speech recorded; no consent or inner state inferred", "speak"

    if kind == "move":
        target = action.get("target")
        if target not in state.get("locations", {}):
            return False, "UNKNOWN_LOCATION", "target location does not exist", ""
        edge_info = _connection(state, here, target, action.get("via"))
        if not edge_info:
            return False, "NO_CONNECTION", "no declared connection from current location", ""
        edge_name, edge = edge_info
        if edge.get("locked", False):
            return False, "LOCKED_CONNECTION", "the connection is locked", ""
        if edge.get("open", True) is False:
            return False, "CLOSED_CONNECTION", "the connection is closed", ""
        actor["location"] = target
        return True, "MOVED", f"moved via {edge_name}", "move"

    if kind == "open":
        via = action.get("via")
        edge = _connection_by_name(state, here, via) if via else None
        if not edge:
            return False, "UNKNOWN_CONNECTION", "connection does not exist here", ""
        if edge.get("locked", False):
            return False, "LOCKED_CONNECTION", "the connection is locked", ""
        edge["open"] = True
        return True, "OPENED", "connection opened", "open"

    if kind == "take":
        object_id = action.get("object_id")
        obj = state.get("objects", {}).get(object_id)
        if not obj:
            return False, "UNKNOWN_OBJECT", "object does not exist", ""
        if obj.get("held_by") is not None:
            return False, "OBJECT_NOT_AVAILABLE", "object is already held", ""
        if obj.get("location") != here:
            return False, "OBJECT_NOT_HERE", "object is not at the actor's location", ""
        if obj.get("portable", True) is False:
            return False, "OBJECT_NOT_PORTABLE", "object is not portable", ""
        obj["location"] = None
        obj["held_by"] = actor_id
        return True, "OBJECT_TAKEN", "object moved into actor inventory", "take"

    if kind == "drop":
        object_id = action.get("object_id")
        obj = state.get("objects", {}).get(object_id)
        if not obj:
            return False, "UNKNOWN_OBJECT", "object does not exist", ""
        if obj.get("held_by") != actor_id:
            return False, "NOT_HELD", "actor does not hold this object", ""
        obj["held_by"] = None
        obj["location"] = here
        return True, "OBJECT_DROPPED", "object placed at actor location", "drop"

    if kind == "wait":
        seconds = action.get("seconds")
        if not isinstance(seconds, int) or seconds <= 0 or seconds > 86400:
            return False, "INVALID_WAIT", "wait must be 1..86400 seconds", ""
        state.setdefault("clock", {})["tick"] = state.get("clock", {}).get("tick", 0) + seconds
        return True, "TIME_ADVANCED", f"time advanced by {seconds} seconds", "wait"

    if kind == "commit":
        if actor.get("kind") == "player" and action.get("source") != "player_input":
            return False, "PLAYER_AGENCY_PROTECTED", "the system cannot create a player commitment", ""
        text = action.get("text")
        if not isinstance(text, str) or not text.strip():
            return False, "EMPTY_COMMITMENT", "commitment must be explicit", ""
        state.setdefault("commitments", []).append({"actor_id": actor_id, "text": text})
        return True, "COMMITMENT_RECORDED", "explicit commitment recorded", "commit"

    return False, "UNKNOWN_ACTION", f"unsupported action type: {kind}", ""


def judge_action(state: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    before = copy.deepcopy(state)
    shape_error = _validate_shape(before, action)
    if shape_error:
        return _fail(action, before, shape_error, "state or action shape is invalid")

    for event in before.get("event_log", []):
        if event.get("action_id") == action["action_id"]:
            return {
                "verdict": "duplicate",
                "reason_code": "IDEMPOTENT_REPLAY",
                "message": "action_id was already applied; no second mutation",
                "action_id": action["action_id"],
                "pre_state_hash": state_hash(before),
                "post_state_hash": state_hash(before),
                "diff": [],
                "events": [],
                "state": before,
            }

    guard = _agency_guard(before, action)
    if guard:
        return _fail(action, before, guard[0], guard[1])

    after = copy.deepcopy(before)
    ok, code, message, _ = _apply_domain(after, action)
    if not ok:
        return _fail(action, before, code, message)

    pre_hash = state_hash(before)
    after.pop("event_log", None)
    event_core = {"action_id": action["action_id"], "action": copy.deepcopy(action), "reason_code": code}
    event_id = "evt_" + hashlib.sha256((pre_hash + canonical(event_core)).encode("utf-8")).hexdigest()[:24]
    event = {"event_id": event_id, **event_core}
    after["event_log"] = copy.deepcopy(before.get("event_log", [])) + [event]
    return {
        "verdict": "allow",
        "reason_code": code,
        "message": message,
        "action_id": action["action_id"],
        "pre_state_hash": pre_hash,
        "post_state_hash": state_hash(after),
        "diff": _path_diff(before, after),
        "events": [event],
        "state": after,
    }


def replay(initial_state: Dict[str, Any], events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    current = copy.deepcopy(initial_state)
    for event in events:
        result = judge_action(current, event["action"])
        if result["verdict"] != "allow" or result["events"][0]["event_id"] != event["event_id"]:
            raise JudgeError(f"replay mismatch at {event.get('event_id')}")
        current = result["state"]
    return current
