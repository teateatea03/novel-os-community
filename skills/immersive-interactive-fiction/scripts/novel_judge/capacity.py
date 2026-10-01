from __future__ import annotations

from typing import Any

# Capacity is an executable contract, not a prose hint.  The defaults are
# intentionally conservative when the state says the actor is cold, hungry,
# fatigued, sleep-fragmented, or cognitively narrowed.
CONSTRAINED_CLARITY = {"fragmented_clear", "confused", "impaired"}
HIGH_LOAD = {"high", "critical", "severe"}
MAJOR_ACTIONS = {
    "move", "move_short", "open", "close", "take", "drop", "use",
    "inspect_object", "search_container", "eat_small", "drink_small",
    "map_read_fragment",
}
MICRO_ACTIONS = {
    "observe_local", "inspect_object", "search_container", "move_short",
    "rest_awake", "eat_small", "drink_small", "map_read_fragment",
}
MACRO_ACTIONS = {"explore", "explore_house", "macro_explore"}

DEFAULT_CONSTRAINED_BUDGET = {
    "max_major_actions_per_turn": 1,
    "max_minor_actions_per_turn": 2,
    "max_new_entities_attended": 2,
    "max_explicit_plan_steps": 1,
    "max_zones": 1,
    "must_reanchor_after_actions": 1,
    "requires_action_manifest": True,
    "action_granularity": "micro",
}


def actor_record(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    return state.get("actors", {}).get(actor_id, {})


def is_ai_autonomous_protagonist(record: dict[str, Any]) -> bool:
    return record.get("kind") == "protagonist" and record.get("control_mode") == "ai_autonomous"


def is_constrained(state: dict[str, Any], actor_id: str) -> bool:
    rec = state.get("reality", {}).get("actors", {}).get(actor_id, {})
    physical = rec.get("physical", {}) if isinstance(rec, dict) else {}
    cognition = rec.get("cognition", {}) if isinstance(rec, dict) else {}
    if cognition.get("clarity") in CONSTRAINED_CLARITY:
        return True
    if cognition.get("working_memory") in {"reduced", "poor"}:
        return True
    if cognition.get("planning_horizon") in {"immediate", "minutes"}:
        return True
    return any(physical.get(k) in HIGH_LOAD for k in ("hunger", "fatigue", "cold", "thermal_load"))


def capacity_budget(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    rec = state.get("reality", {}).get("actors", {}).get(actor_id, {})
    capacity = rec.get("capacity", {}) if isinstance(rec, dict) else {}
    result: dict[str, Any] = {}
    if is_constrained(state, actor_id):
        result.update(DEFAULT_CONSTRAINED_BUDGET)
    explicit = capacity.get("cognitive_budget", {}) if isinstance(capacity, dict) else {}
    if isinstance(explicit, dict):
        result.update(explicit)
    # A top-level capacity field may be supplied by an external compiler.
    for key in DEFAULT_CONSTRAINED_BUDGET:
        if isinstance(capacity, dict) and key in capacity:
            result[key] = capacity[key]
    return result


def action_is_major(action_type: str) -> bool:
    return action_type in MAJOR_ACTIONS


def action_is_micro(action_type: str) -> bool:
    return action_type in MICRO_ACTIONS


def action_zone(state: dict[str, Any], actor_id: str, claim: dict[str, Any]) -> str:
    zone = claim.get("zone") or claim.get("location")
    if zone:
        return str(zone)
    return str(actor_record(state, actor_id).get("location", "unknown"))


def capacity_summary(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    rec = state.get("reality", {}).get("actors", {}).get(actor_id, {})
    return {
        "actor_id": actor_id,
        "budget": capacity_budget(state, actor_id),
        "physical": rec.get("physical", {}),
        "cognition": rec.get("cognition", {}),
        "control_mode": actor_record(state, actor_id).get("control_mode"),
        "agency_policy": actor_record(state, actor_id).get("agency_policy"),
    }
