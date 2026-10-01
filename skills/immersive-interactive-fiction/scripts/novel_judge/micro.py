from __future__ import annotations

from typing import Any

from .capacity import MACRO_ACTIONS, capacity_budget
from .canonical import deep_copy
from .errors import JudgeError, MACRO_INTENT_REQUIRES_EXPANSION, PRECONDITION_FAILED
from .intent import make_intent


def is_macro_intent(intent: dict[str, Any]) -> bool:
    return intent.get("type") in MACRO_ACTIONS


def _child_type(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("type") or item.get("action_type") or "observe_local")
    return "observe_local"


def expand_macro_intent(state: dict[str, Any], intent: dict[str, Any]) -> list[dict[str, Any]]:
    """Compile one narrative macro request into bounded micro intents.

    Expansion is deliberately lossy: an intent such as "explore the house"
    does not authorize the model to invent a tour. If no explicit micro plan
    exists, it produces exactly one local observation. A supplied plan is
    capped by the current cognitive budget and each child is independently
    judged/committed by Novel Judge.
    """
    if not is_macro_intent(intent):
        return [intent]
    actor_id = intent["actor_id"]
    budget = capacity_budget(state, actor_id)
    params = intent.get("parameters", {})
    raw = params.get("micro_actions") or params.get("actions") or []
    if not raw:
        raw = [{"type": "observe_local", "zone": state.get("actors", {}).get(actor_id, {}).get("location")}]
    if not isinstance(raw, list):
        raise JudgeError(PRECONDITION_FAILED, "macro micro_actions must be a list")
    max_major = int(budget.get("max_major_actions_per_turn", 1))
    max_minor = int(budget.get("max_minor_actions_per_turn", 2))
    children: list[dict[str, Any]] = []
    major = 0
    minor = 0
    for index, item in enumerate(raw):
        typ = _child_type(item)
        is_major = typ in {"move", "move_short", "open", "close", "take", "drop", "use"}
        if is_major:
            if major >= max_major:
                break
            major += 1
        else:
            if minor >= max_minor:
                break
            minor += 1
        spec = deep_copy(item) if isinstance(item, dict) else {"type": typ}
        parameters = dict(spec.get("parameters", {}))
        for key in ("seconds", "object_id", "via", "text", "zone", "location"):
            if key in spec and key not in parameters:
                parameters[key] = spec[key]
        targets = list(spec.get("targets", []))
        if not targets and spec.get("target") is not None:
            targets = [spec["target"]]
        if not targets and isinstance(spec.get("location"), str) and typ in {"move", "move_short"}:
            targets = [spec["location"]]
        child_params = dict(parameters)
        child_params["expanded_micro"] = True
        child_params["parent_macro_turn_id"] = intent["turn_id"]
        child_params["micro_index"] = index
        children.append(make_intent(
            actor_id, typ, turn_id=f"{intent['turn_id']}.micro-{index+1}",
            targets=targets, parameters=child_params, source=intent.get("source", "model"),
            raw_input=intent.get("raw_input"),
            player_authored=bool(intent.get("player_authored", False)),
            model_generated=bool(intent.get("model_generated", False)),
        ))
    if not children:
        raise JudgeError(MACRO_INTENT_REQUIRES_EXPANSION, "macro intent has no capacity-valid micro action", details={"budget": budget})
    return children


def macro_compile_report(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    children = expand_macro_intent(state, intent)
    return {"macro_turn_id": intent.get("turn_id"), "source_type": intent.get("type"),
            "child_turn_ids": [x["turn_id"] for x in children],
            "child_types": [x["type"] for x in children],
            "budget": capacity_budget(state, intent["actor_id"])}
