from __future__ import annotations

"""Bi-temporal-ish lifecycle projection for state-derived semantic edges."""

from typing import Any
from .canonical import deep_copy, stable_id

REPLAYABLE = {"allow", "allow_with_cost", "partial", "meta"}


def _tokens(path: str) -> list[str]:
    return [x.replace("~1", "/").replace("~0", "~") for x in str(path).strip("/").split("/") if x]


def _semantic_change(event: dict[str, Any], op: dict[str, Any]) -> dict[str, Any] | None:
    t = _tokens(op.get("path", "")); value = op.get("value"); path = str(op.get("path", ""))
    if len(t) >= 3 and t[0] == "actors" and t[2] == "location":
        return {"slot": f"actor:{t[1]}:location", "source": f"actor:{t[1]}", "target": None if value is None else f"location:{value}", "relation": "located_in", "path": path}
    if len(t) >= 4 and t[:2] == ["world_truth", "objects"] and t[3] == "holder":
        return {"slot": f"object:{t[2]}:holder", "source": f"object:{t[2]}", "target": None if value is None else f"actor:{value}", "relation": "possessed_by", "path": path}
    if len(t) >= 4 and t[:2] == ["world_truth", "objects"] and t[3] == "location":
        return {"slot": f"object:{t[2]}:location", "source": f"object:{t[2]}", "target": None if value is None else f"location:{value}", "relation": "located_in", "path": path}
    if len(t) >= 4 and t[:2] in (["knowledge", "player"], ["knowledge", "npcs"]):
        fact = t[3] if len(t) == 4 else "/".join(t[3:])
        return {"slot": f"actor:{t[2]}:knows:{fact}", "source": f"actor:{t[2]}", "target": f"fact:{fact}", "relation": "knows", "path": path, "remove": op.get("op") == "remove"}
    if len(t) >= 3 and t[0] == "relations":
        return {"slot": f"relation:{t[1]}:{t[2]}:{'/'.join(t[3:])}", "source": f"actor:{t[1]}", "target": f"actor:{t[2]}", "relation": "relation_changed", "path": path, "value": deep_copy(value), "remove": op.get("op") == "remove"}
    return None


def project_temporal_relations(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}; history: list[dict[str, Any]] = []
    for event in events:
        if event.get("verdict") not in REPLAYABLE: continue
        event_id = str(event.get("event_id")); at = event.get("created_at") or event.get("after_revision")
        operations = event.get("operations", [])
        if any(isinstance(op, dict) and op.get("op") == "replace_snapshot" for op in operations):
            # Migration checkpoints are expanded to ordinary JSON-pointer
            # changes for semantic/temporal projections; replace_snapshot
            # itself remains a replay-only marker.
            from .history_migration import migration_event_semantic_operations
            operations = migration_event_semantic_operations(event)
        for op in operations:
            change = _semantic_change(event, op)
            if not change: continue
            slot = change["slot"]; old = active.pop(slot, None)
            if old:
                old["status"] = "invalidated"; old["valid_to"] = at; old["invalidated_by_event_id"] = event_id
                history.append(old)
            remove = bool(change.get("remove")) or change.get("target") is None
            if remove: continue
            edge = {"edge_id": stable_id("edge", slot, event_id, change.get("target"), change.get("value")),
                    "source": change["source"], "target": change["target"], "relation": change["relation"],
                    "slot": slot, "status": "active", "valid_from": at, "valid_to": None,
                    "recorded_from": event.get("created_at"), "recorded_to": None,
                    "confidence": "EXTRACTED", "property_path": change["path"],
                    "value": change.get("value"), "evidence": [{"event_id": event_id, "operation": deep_copy(op)}]}
            active[slot] = edge
    return history + list(active.values())


def query_relations_at(edges: list[dict[str, Any]], at: Any, *, relation: str | None = None,
                       source: str | None = None, target: str | None = None) -> list[dict[str, Any]]:
    """Return edges valid at a logical/ISO timestamp without an LLM."""
    key = str(at)
    out = []
    for edge in edges:
        start = edge.get("valid_from"); end = edge.get("valid_to")
        if start is not None and str(start) > key: continue
        if end is not None and key >= str(end): continue
        if relation and edge.get("relation") != relation: continue
        if source and edge.get("source") != source: continue
        if target and edge.get("target") != target: continue
        out.append(deep_copy(edge))
    out.sort(key=lambda x: (str(x.get("source")), str(x.get("relation")), str(x.get("target")), str(x.get("valid_from"))))
    return out


def relation_history(edges: list[dict[str, Any]], *, slot: str) -> list[dict[str, Any]]:
    out = [deep_copy(x) for x in edges if x.get("slot") == slot]
    out.sort(key=lambda x: (str(x.get("valid_from")), str(x.get("edge_id"))))
    return out
