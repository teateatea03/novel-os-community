from __future__ import annotations

from typing import Any

from .capacity import (
    capacity_budget, is_ai_autonomous_protagonist, is_constrained,
    action_is_major, MACRO_ACTIONS,
)
from .errors import (
    JudgeError, ILLEGAL_ACTION, KNOWLEDGE_BOUNDARY, NOT_FOUND, PLAYER_SOVEREIGNTY,
    PRECONDITION_FAILED, MACRO_INTENT_REQUIRES_EXPANSION,
)
from .state import actor, location, object_record


MAJOR_PLAYER_ACTIONS = {"move", "move_short", "speak", "ask", "take", "drop", "use", "hide", "promise", "attempt", "wait", "open", "close", "inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment"}


def _target(intent: dict[str, Any], key: str = "target") -> str | None:
    return intent.get("parameters", {}).get(key) or (intent.get("targets") or [None])[0]


def check_player_sovereignty(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    if intent.get("actor_id") == "world" and intent.get("type") in {"world_tick", "scene_commit", "chapter_commit", "artifact_revision", "semantic_correction"}:
        return {"ok": True, "reason": "world_tick_actor"}
    actor_rec = actor(state, intent["actor_id"])
    is_player = actor_rec.get("kind") == "player" or intent["actor_id"] == "player"
    autonomous = is_ai_autonomous_protagonist(actor_rec)
    if autonomous:
        # The model may propose an autonomous protagonist action; the judge
        # still owns commit. Explicit user/author input remains authoritative.
        if intent.get("type") in {"promise"} and not intent.get("player_authored"):
            raise JudgeError(PLAYER_SOVEREIGNTY, "autonomous protagonist cannot receive an un-authored commitment")
        return {"ok": True, "reason": "ai_autonomous_protagonist_proposal"}
    if not is_player:
        return {"ok": True, "reason": "non_player_actor"}
    if intent.get("source") not in {"player_input", "author"} and intent["type"] in MAJOR_PLAYER_ACTIONS:
        raise JudgeError(PLAYER_SOVEREIGNTY, "only explicit player input or author decision can control player action", details={"action": intent["type"], "source": intent.get("source")})
    if intent.get("model_generated") and intent["type"] in MAJOR_PLAYER_ACTIONS:
        raise JudgeError(PLAYER_SOVEREIGNTY, "model cannot authorize a major player action", details={"action": intent["type"]})
    if intent["type"] == "promise" and not intent.get("player_authored"):
        raise JudgeError(PLAYER_SOVEREIGNTY, "model cannot create a player promise")
    return {"ok": True, "reason": "player_input_or_non_major"}


def check_reality_capacity(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    reality = state.get("reality", {}).get("actors", {}).get(intent["actor_id"], {})
    blocked = set(reality.get("blocked_actions", []))
    if intent["type"] in blocked:
        raise JudgeError("CAPACITY_BLOCKED", "current reality state blocks this action", details={"action": intent["type"], "actor_id": intent["actor_id"]})
    available = reality.get("available_actions")
    if isinstance(available, list) and intent["type"] not in available:
        # The compiled capacity may add micro actions to an otherwise legacy
        # affordance list. Only reject when the action is explicitly blocked.
        if intent["type"] not in {"observe_local", "move_short", "rest_awake", "inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment"}:
            raise JudgeError("CAPACITY_BLOCKED", "action is not currently available", details={"action": intent["type"], "available": available})
    cost = reality.get("action_costs", {}).get(intent.get("type"), {}) if isinstance(reality, dict) else {}
    return {"ok": True, "capacity": reality.get("capacity", {}), "action_cost": cost}


def preflight_intent(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    actor_rec = {"kind": "world"} if intent.get("actor_id") == "world" else actor(state, intent["actor_id"])
    report: dict[str, Any] = {"ok": True, "checks": [], "warnings": []}
    check_player_sovereignty(state, intent); report["checks"].append("player_sovereignty")
    if intent["type"] in MACRO_ACTIONS and not intent.get("parameters", {}).get("expanded_micro"):
        raise JudgeError(MACRO_INTENT_REQUIRES_EXPANSION, "macro intent must be expanded into micro actions", details={"type": intent["type"], "budget": capacity_budget(state, intent["actor_id"])})
    check_reality_capacity(state, intent); report["checks"].append("reality_capacity")
    typ = intent["type"]
    if typ in MACRO_ACTIONS:
        # Macro requests are never directly committed. The host must call
        # micro.expand_macro_intent and submit children individually.
        if not intent.get("parameters", {}).get("expanded_micro"):
            raise JudgeError(MACRO_INTENT_REQUIRES_EXPANSION, "macro intent must be expanded into micro actions", details={"type": typ, "budget": capacity_budget(state, intent["actor_id"])})
        report["checks"].append("macro_expanded")
    if typ in {"move", "move_short"}:
        target = _target(intent)
        if not target:
            raise JudgeError(PRECONDITION_FAILED, "move requires a target")
        current = actor_rec.get("location")
        current_loc = location(state, current)
        if target not in state["world_truth"]["locations"]:
            raise JudgeError(NOT_FOUND, "target location not found", details={"target": target})
        exits = current_loc.get("connections", current_loc.get("exits", {}))
        edge = exits.get(target) if isinstance(exits, dict) else None
        if edge is None:
            raise JudgeError(ILLEGAL_ACTION, "no connection from current location", details={"from": current, "to": target})
        if isinstance(edge, str):
            edge = {"to": edge}
        if edge.get("open", True) is not True or edge.get("locked", False) is True:
            raise JudgeError(ILLEGAL_ACTION, "connection is not verified open", details={"from": current, "to": target, "edge": edge})
        report["checks"].append("movement_connection")
    elif typ in {"take", "drop", "use"}:
        object_id = _target(intent, "object_id") or _target(intent)
        if not object_id:
            raise JudgeError(PRECONDITION_FAILED, f"{typ} requires an object")
        obj = object_record(state, object_id)
        if typ == "take" and obj.get("holder") not in (None, "") and obj.get("holder") != intent["actor_id"]:
            raise JudgeError(ILLEGAL_ACTION, "object is held by another actor", details={"object_id": object_id})
        if typ == "take" and obj.get("portable", True) is False:
            raise JudgeError(ILLEGAL_ACTION, "object is not portable", details={"object_id": object_id})
        if typ == "take" and obj.get("location") != actor_rec.get("location"):
            raise JudgeError(ILLEGAL_ACTION, "object is not at actor location", details={"object_id": object_id})
        if typ in {"drop", "use"} and obj.get("holder") != intent["actor_id"]:
            raise JudgeError(ILLEGAL_ACTION, "actor does not hold object", details={"object_id": object_id})
        report["checks"].append("object_precondition")
    elif typ in {"observe", "rest_awake"}:
        report["checks"].append("local_observation")
    elif typ in {"inspect_object", "search_container", "eat_small", "drink_small", "map_read_fragment"}:
        object_id = _target(intent, "object_id") or _target(intent)
        if not object_id:
            raise JudgeError(PRECONDITION_FAILED, f"{typ} requires an object")
        obj = object_record(state, object_id)
        if obj.get("location") != actor_rec.get("location") and obj.get("holder") != intent["actor_id"]:
            raise JudgeError(ILLEGAL_ACTION, "object is not locally accessible", details={"object_id": object_id, "location": actor_rec.get("location")})
        report["checks"].append("micro_object_precondition")
    elif typ in {"open", "close"}:
        via = _target(intent, "via") or _target(intent)
        here = actor_rec.get("location")
        if not via:
            raise JudgeError(PRECONDITION_FAILED, f"{typ} requires a connection")
        connections = state["world_truth"]["locations"].get(here, {}).get("connections", {})
        edge = connections.get(via)
        if not isinstance(edge, dict):
            raise JudgeError(NOT_FOUND, "connection not found", details={"location": here, "via": via})
        if edge.get("locked", False) is True:
            raise JudgeError(ILLEGAL_ACTION, "connection is locked", details={"via": via})
        report["checks"].append("connection_precondition")
    elif typ in {"speak", "ask"}:
        text = intent.get("parameters", {}).get("text")
        if not isinstance(text, str) or not text.strip():
            raise JudgeError(PRECONDITION_FAILED, f"{typ} requires explicit text")
        report["checks"].append("speech_precondition")
    elif typ in {"observe", "observe_local", "wait", "hide", "promise", "attempt", "npc_act", "world_tick", "scene_commit", "chapter_commit", "artifact_revision", "semantic_correction", "meta"}:
        pass
    else:
        raise JudgeError(ILLEGAL_ACTION, "unsupported action")
    if intent.get("parameters", {}).get("requires_knowledge"):
        fact = intent["parameters"]["requires_knowledge"]
        known = state.get("knowledge", {}).get("player", {}).get(intent["actor_id"], [])
        if fact not in known:
            raise JudgeError(KNOWLEDGE_BOUNDARY, "actor lacks required knowledge", details={"fact": fact})
        report["checks"].append("knowledge_precondition")
    return report
