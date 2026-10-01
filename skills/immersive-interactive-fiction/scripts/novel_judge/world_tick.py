from __future__ import annotations

from typing import Any

from .canonical import sha256_json
from .errors import PLAYER_SOVEREIGNTY
from .intent import make_intent
from .canonical import stable_id
from .plans import evaluate_plan


def tick(state: dict[str, Any], seconds: int = 0, *, steps: int = 1, seed: int | None = None) -> list[dict[str, Any]]:
    """Produce background candidates only; this function never commits or mutates state."""
    if seconds < 0: raise ValueError("seconds cannot be negative")
    return candidate_ticks(state, steps=steps, seed=seed)


def candidate_ticks(state: dict[str, Any], *, steps: int = 1, seed: int | None = None) -> list[dict[str, Any]]:
    """Return deterministic NPC/world candidates; this function never mutates state."""
    steps = max(0, min(int(steps), 100))
    out: list[dict[str, Any]] = []
    current = state
    base = seed if seed is not None else 0
    for step in range(steps):
        plans = current.get("plans", {})
        for actor_id, plan in sorted((plans.get("npcs", {}) or {}).items()):
            if not isinstance(plan, dict) or not plan.get("action_type"): continue
            lifecycle = evaluate_plan(current, plan)
            if not lifecycle.get("available"): continue
            actor = current.get("actors", {}).get(actor_id, {})
            if actor.get("kind") == "player" or actor_id in {"player", "user"}:
                continue
            params = dict(plan.get("parameters", {}))
            if plan.get("operations"): params["operations"] = plan["operations"]
            intent = make_intent(actor_id, plan["action_type"], turn_id=f"tick-{step}-{actor_id}",
                                 intent_id=stable_id("intent", state.get("state_hash"), base, step, actor_id, plan),
                                 targets=list(plan.get("targets", [])), parameters=params,
                                 source="npc_plan", player_authored=False, model_generated=False)
            intent["seed"] = base
            intent["candidate"] = True
            intent["plan_id"] = plan.get("plan_id", actor_id)
            out.append(intent)
        for index, plan in enumerate((plans.get("world", {}) or {}).get("actions", []) if isinstance(plans.get("world", {}), dict) else []):
            if not isinstance(plan, dict) or not plan.get("action_type"): continue
            intent = make_intent("world", plan["action_type"], turn_id=f"tick-{step}-world-{index}",
                                 intent_id=stable_id("intent", state.get("state_hash"), base, step, "world", index, plan),
                                 targets=list(plan.get("targets", [])), parameters=dict(plan.get("parameters", {})),
                                 source="world_tick", player_authored=False)
            intent["seed"] = base
            intent["candidate"] = True
            out.append(intent)
    for item in out:
        item["candidate_hash"] = sha256_json(item)
    return out


def validate_tick_candidate(intent: dict[str, Any]) -> dict[str, Any]:
    if intent.get("actor_id") in {"player", "user"} and intent.get("source") != "player_input":
        return {"ok": False, "code": PLAYER_SOVEREIGNTY, "message": "background tick cannot act for player"}
    return {"ok": True, "code": None, "message": "candidate only; judge must commit"}
