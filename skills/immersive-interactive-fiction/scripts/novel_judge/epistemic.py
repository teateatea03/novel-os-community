from __future__ import annotations

from typing import Any

from .canonical import sha256_json
from .errors import KNOWLEDGE_BOUNDARY
from .errors import JudgeError


def build_permission_report(state: dict[str, Any], actor_id: str) -> dict[str, Any]:
    return {"actor_id": actor_id, "audience": "player" if actor_id in {"player", "user"} else "npc",
            "visible_fact_ids": sorted(visible_fact_ids(state, audience="player" if actor_id in {"player", "user"} else "npc", actor_id=actor_id)),
            "state_hash": state.get("state_hash"), "branch_id": state.get("branch_id")}


def _truth(state: dict[str, Any]) -> dict[str, Any]:
    value = state.get("knowledge", {}).get("truth", {})
    return value if isinstance(value, dict) else {}


def visible_fact_ids(state: dict[str, Any], *, audience: str, actor_id: str | None = None) -> set[str]:
    truth = _truth(state)
    result = {fid for fid, fact in truth.items() if isinstance(fact, dict) and fact.get("visibility") == "public"}
    knowledge = state.get("knowledge", {})
    if audience == "player" and actor_id:
        result.update(knowledge.get("player", {}).get(actor_id, []))
    elif audience == "npc" and actor_id:
        result.update(knowledge.get("npcs", {}).get(actor_id, []))
    elif audience == "reader":
        result.update(knowledge.get("reader", []))
    return {str(x) for x in result}


def visible_facts(state: dict[str, Any], *, audience: str, actor_id: str | None = None) -> dict[str, Any]:
    ids = visible_fact_ids(state, audience=audience, actor_id=actor_id)
    truth = _truth(state)
    return {fid: truth[fid] for fid in sorted(ids) if fid in truth}


def knowledge_gate(state: dict[str, Any], fact_ids: list[str], *, audience: str, actor_id: str | None = None) -> dict[str, Any]:
    allowed = visible_fact_ids(state, audience=audience, actor_id=actor_id)
    denied = [fid for fid in fact_ids if fid not in allowed]
    return {"ok": not denied, "allowed": [fid for fid in fact_ids if fid in allowed], "denied": denied,
            "audience": audience, "actor_id": actor_id, "context_hash": sha256_json(sorted(allowed))}


def require_knowledge(state: dict[str, Any], fact_ids: list[str], *, audience: str, actor_id: str | None = None) -> dict[str, Any]:
    report = knowledge_gate(state, fact_ids, audience=audience, actor_id=actor_id)
    if not report["ok"]:
        raise JudgeError(KNOWLEDGE_BOUNDARY, "one or more facts are outside actor knowledge", details=report)
    return report


def filter_private(record: Any) -> Any:
    """Remove common author/private fields from a context record."""
    if isinstance(record, dict):
        return {k: filter_private(v) for k, v in record.items() if k not in {"secrets", "private_notes", "secret", "use_effects", "author_only"}}
    if isinstance(record, list):
        return [filter_private(v) for v in record]
    return record
