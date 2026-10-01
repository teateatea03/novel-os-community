from __future__ import annotations

from typing import Any

from .canonical import sha256_json


def _get_path(value: Any, path: str) -> Any:
    cur = value
    for part in path.split("."):
        if isinstance(cur, dict): cur = cur.get(part)
        else: return None
    return cur


def _conditions(state: dict[str, Any], storylet: dict[str, Any], actor_id: str | None) -> tuple[bool, list[str]]:
    why: list[str] = []
    cond = storylet.get("conditions", {})
    if not isinstance(cond, dict): return False, ["invalid_conditions"]
    actor = state.get("actors", {}).get(actor_id or storylet.get("actor_id"), {})
    if "location" in cond and actor.get("location") != cond["location"]: return False, ["location"]
    if "actor_in" in cond and actor.get("location") not in set(cond["actor_in"] if isinstance(cond["actor_in"], list) else [cond["actor_in"]]): return False, ["actor_in"]
    for fid in cond.get("requires_facts", []):
        if fid not in state.get("knowledge", {}).get("player", {}).get(actor_id, []) and fid not in state.get("knowledge", {}).get("reader", []): return False, [f"fact:{fid}"]
    for oid in cond.get("requires_items", []):
        obj = state.get("world_truth", {}).get("objects", {}).get(oid, {})
        if obj.get("holder") != actor_id: return False, [f"item:{oid}"]
    for key, expected in cond.get("state_equals", {}).items():
        if _get_path(state, key) != expected: return False, [f"state:{key}"]
    for key, minimum in cond.get("clock_at_least", {}).items():
        if int(state.get("clocks", {}).get(key, 0)) < int(minimum): return False, [f"clock:{key}"]
    if storylet.get("id") in state.get("metadata", {}).get("solver_completed_storylets", []): return False, ["solver_completed"]
    if storylet.get("id") in state.get("storylets", {}).get("cooldowns", {}): return False, ["cooldown"]
    why.append("all_conditions_pass")
    return True, why


def available_storylets(state: dict[str, Any], *, actor_id: str | None = None) -> list[dict[str, Any]]:
    result = []
    for storylet in state.get("storylets", {}).get("active", []):
        if not isinstance(storylet, dict) or not storylet.get("id"): continue
        ok, reasons = _conditions(state, storylet, actor_id)
        if ok:
            item = dict(storylet); item["availability_reason"] = reasons
            item["availability_hash"] = sha256_json({"id": item["id"], "state": state.get("state_hash"), "actor": actor_id})
            result.append(item)
    return sorted(result, key=lambda x: (-int(x.get("priority", 0)), x["id"]))


def storylet_candidates(state: dict[str, Any], *, actor_id: str | None = None) -> list[dict[str, Any]]:
    return [{"storylet_id": s["id"], "pressure": s.get("pressure", ""), "candidate_intents": s.get("candidate_intents", [])} for s in available_storylets(state, actor_id=actor_id)]
