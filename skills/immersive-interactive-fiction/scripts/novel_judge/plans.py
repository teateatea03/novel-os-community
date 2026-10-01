from __future__ import annotations

"""Host-owned NPC plan lifecycle. Models may propose plans; only host validates transitions."""

from typing import Any
from .canonical import deep_copy, stable_id

PLAN_STATUSES = {"candidate", "active", "blocked", "interrupted", "completed", "failed", "abandoned"}
TERMINAL = {"completed", "failed", "abandoned"}
ALLOWED = {
    "candidate": {"active", "abandoned"}, "active": {"blocked", "interrupted", "completed", "failed", "abandoned"},
    "blocked": {"active", "failed", "abandoned"}, "interrupted": {"active", "failed", "abandoned"},
    "completed": set(), "failed": set(), "abandoned": set(),
}


def make_plan(actor_id: str, goal: str, *, action_type: str, targets: list[str] | None = None,
              parameters: dict[str, Any] | None = None, preconditions: list[dict[str, Any]] | None = None,
              deadline_tick: int | None = None, interrupt_on: list[str] | None = None,
              source: str = "host", status: str = "candidate") -> dict[str, Any]:
    if status not in PLAN_STATUSES: raise ValueError("invalid plan status")
    value = {"schema": "minis.npc-plan.v1", "actor_id": actor_id, "goal": str(goal), "action_type": action_type,
             "targets": list(targets or []), "parameters": dict(parameters or {}), "preconditions": list(preconditions or []),
             "deadline_tick": deadline_tick, "interrupt_on": list(interrupt_on or []), "source": source, "status": status,
             "created_tick": None, "updated_tick": None, "attempt_count": 0, "status_reason": None, "history": []}
    value["plan_id"] = stable_id("plan", actor_id, goal, action_type, value["targets"], deadline_tick)
    return value


def _path(state: dict[str, Any], pointer: str) -> Any:
    cur: Any = state
    for token in pointer.strip("/").split("/") if pointer.strip("/") else []:
        if not isinstance(cur, dict) or token not in cur: return None
        cur = cur[token]
    return cur


def evaluate_plan(state: dict[str, Any], plan: dict[str, Any], *, event_tags: list[str] | None = None) -> dict[str, Any]:
    errors = []
    status = plan.get("status", "active")
    if status not in PLAN_STATUSES: errors.append("invalid_status")
    if not plan.get("actor_id") or not plan.get("goal") or not plan.get("action_type"): errors.append("missing_required")
    now = int(state.get("clock", {}).get("tick", 0) or 0)
    deadline = plan.get("deadline_tick")
    if isinstance(deadline, int) and now > deadline and plan.get("status") not in TERMINAL:
        return {"ok": False, "available": False, "reason": "deadline_expired", "recommended_status": "failed"}
    tags = set(event_tags or [])
    hit = sorted(tags & set(plan.get("interrupt_on", [])))
    if hit and plan.get("status") == "active":
        return {"ok": True, "available": False, "reason": "interrupt_triggered", "triggers": hit, "recommended_status": "interrupted"}
    missing = []
    for cond in plan.get("preconditions", []):
        if not isinstance(cond, dict) or not cond.get("path"): continue
        actual = _path(state, str(cond["path"]))
        if "equals" in cond and actual != cond["equals"]: missing.append(cond["path"])
        if cond.get("exists") is True and actual is None: missing.append(cond["path"])
    if missing:
        return {"ok": True, "available": False, "reason": "preconditions_unmet", "missing": missing, "recommended_status": "blocked"}
    return {"ok": not errors, "available": not errors and status == "active", "reason": errors[0] if errors else "ready", "recommended_status": status}


def transition_plan(plan: dict[str, Any], new_status: str, *, tick: int, reason: str, event_id: str | None = None) -> dict[str, Any]:
    old = str(plan.get("status"))
    if new_status not in ALLOWED.get(old, set()): raise ValueError(f"illegal plan transition: {old} -> {new_status}")
    result = deep_copy(plan)
    result["status"] = new_status; result["updated_tick"] = int(tick); result["status_reason"] = reason
    if result.get("created_tick") is None: result["created_tick"] = int(tick)
    result.setdefault("history", []).append({"from": old, "to": new_status, "tick": int(tick), "reason": reason, "event_id": event_id})
    return result


def select_ready_plans(state: dict[str, Any], *, event_tags: list[str] | None = None) -> list[dict[str, Any]]:
    out = []
    for actor_id, plan in sorted((state.get("plans", {}).get("npcs", {}) or {}).items()):
        if not isinstance(plan, dict): continue
        report = evaluate_plan(state, plan, event_tags=event_tags)
        if report.get("available"):
            out.append({**deep_copy(plan), "actor_id": actor_id, "lifecycle_report": report})
    return out
