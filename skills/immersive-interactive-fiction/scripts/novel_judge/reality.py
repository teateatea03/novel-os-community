from __future__ import annotations

from typing import Any

from .capacity import capacity_budget, capacity_summary
from .errors import CAPACITY_BLOCKED, JudgeError


def reality_gate(state: dict[str, Any], actor_id: str, intent: dict[str, Any] | None = None) -> dict[str, Any]:
    card = build_reality_card(state, actor_id, intent)
    action = (intent or {}).get("type")
    if action and action in set(card.get("blocked_actions", [])):
        raise JudgeError(CAPACITY_BLOCKED, "current reality state blocks this action", details=card)
    available = card.get("available_actions")
    if action and isinstance(available, list) and action not in available:
        raise JudgeError(CAPACITY_BLOCKED, "action is not currently available", details={"action": action, "available": available})
    return card


def build_reality_card(state: dict[str, Any], actor_id: str, intent: dict[str, Any] | None = None) -> dict[str, Any]:
    rec = state.get("reality", {}).get("actors", {}).get(actor_id, {})
    actor = state.get("actors", {}).get(actor_id, {})
    card = {
        "schema": "minis.reality-card.v1", "actor_id": actor_id,
        "as_of": state.get("clock", {}).get("now"), "tick": state.get("clock", {}).get("tick", 0),
        "physical": rec.get("physical", {}), "cognition": rec.get("cognition", {}),
        "psychology": rec.get("psychology", {}), "capacity": rec.get("capacity", {}),
        "cognitive_budget": capacity_budget(state, actor_id),
        "capacity_summary": capacity_summary(state, actor_id),
        "blocked_actions": list(rec.get("blocked_actions", [])),
        "available_actions": rec.get("available_actions"),
        "action_costs": rec.get("action_costs", {}),
        "source": rec.get("source", "state"), "confidence": rec.get("confidence", "unknown"),
    }
    if intent:
        card["requested_action"] = intent.get("type")
        card["requested_parameters"] = intent.get("parameters", {})
    # Keep state-level actor condition available to renderers without treating
    # it as a diagnosis or an invented private fact.
    if actor.get("condition") is not None:
        card["actor_condition"] = actor.get("condition")
    return card


def gate_reality(state: dict[str, Any], intent: dict[str, Any]) -> dict[str, Any]:
    card = build_reality_card(state, intent["actor_id"], intent)
    typ = intent["type"]
    if typ in set(card["blocked_actions"]):
        raise JudgeError(CAPACITY_BLOCKED, "current reality state blocks this action", details=card)
    available = card.get("available_actions")
    if isinstance(available, list) and typ not in available:
        raise JudgeError(CAPACITY_BLOCKED, "action is not currently available", details={"action": typ, "available": available, "card": card})
    return card


def action_cost(card: dict[str, Any], action_type: str) -> dict[str, Any]:
    value = card.get("action_costs", {}).get(action_type, {})
    return value if isinstance(value, dict) else {"value": value}
