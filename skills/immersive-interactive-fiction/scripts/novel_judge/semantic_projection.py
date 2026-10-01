from __future__ import annotations

"""Semantic Graphify projection from authoritative event operations."""

from typing import Any
from .canonical import deep_copy


def _tokens(path: str) -> list[str]:
    return [x.replace("~1", "/").replace("~0", "~") for x in str(path).strip("/").split("/") if x]


def project_operation(event: dict[str, Any], op: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    t = _tokens(op.get("path", "")); nodes: list[dict[str, Any]] = []; links: list[dict[str, Any]] = []
    if not t: return nodes, links
    event_id = str(event.get("event_id")); evidence = [{"event_id": event_id, "operation": deep_copy(op)}]
    def node(i: str, label: str, typ: str, **props: Any) -> None:
        nodes.append({"id": i, "label": label, "entity_type": typ, "properties": props})
    def edge(src: str, dst: str, rel: str, **props: Any) -> None:
        links.append({"source": src, "target": dst, "relation": rel, "status": "active", "confidence": "EXTRACTED", "evidence": evidence, **props})
    if len(t) >= 3 and t[:1] == ["actors"] and t[2] == "location" and op.get("op") != "remove":
        actor, loc = t[1], op.get("value"); node(f"actor:{actor}", actor, "person"); node(f"location:{loc}", str(loc), "location")
        edge(f"actor:{actor}", f"location:{loc}", "located_in", valid_from=event.get("created_at"))
    elif len(t) >= 4 and t[:2] == ["world_truth", "objects"] and t[3] == "holder" and op.get("op") != "remove":
        oid, holder = t[2], op.get("value"); node(f"object:{oid}", oid, "object")
        if holder is not None: node(f"actor:{holder}", str(holder), "person"); edge(f"object:{oid}", f"actor:{holder}", "possessed_by", valid_from=event.get("created_at"))
    elif len(t) >= 4 and t[:2] == ["world_truth", "objects"] and t[3] == "location" and op.get("op") != "remove":
        oid, loc = t[2], op.get("value"); node(f"object:{oid}", oid, "object")
        if loc is not None: node(f"location:{loc}", str(loc), "location"); edge(f"object:{oid}", f"location:{loc}", "located_in", valid_from=event.get("created_at"))
    elif len(t) >= 4 and t[:2] in (["knowledge", "player"], ["knowledge", "npcs"]):
        actor = t[2]; fact = t[3] if len(t) == 4 else "/".join(t[3:]); node(f"actor:{actor}", actor, "person"); node(f"fact:{fact}", fact, "claim")
        edge(f"actor:{actor}", f"fact:{fact}", "knows", valid_from=event.get("created_at"))
    elif len(t) >= 3 and t[0] == "relations":
        a, b = t[1], t[2]; node(f"actor:{a}", a, "person"); node(f"actor:{b}", b, "person")
        edge(f"actor:{a}", f"actor:{b}", "relation_changed", property_path="/".join(t[3:]), value=deep_copy(op.get("value")), valid_from=event.get("created_at"))
    elif len(t) >= 3 and t[0] == "threads":
        thread_id = str(op.get("value") if t[-1] == "-" else t[-1]); node(f"thread:{thread_id}", thread_id, "narrative_thread")
        edge(f"event:{event_id}", f"thread:{thread_id}", "affects")
    return nodes, links


def project_semantic_deltas(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []; links: list[dict[str, Any]] = []; seen_nodes: set[str] = set(); seen_edges: set[tuple[str, str, str, str]] = set()
    for event in events:
        if event.get("verdict") not in {"allow", "allow_with_cost", "partial", "meta"}: continue
        operations = event.get("operations", [])
        if any(isinstance(op, dict) and op.get("op") == "replace_snapshot" for op in operations):
            from .history_migration import migration_event_semantic_operations
            operations = migration_event_semantic_operations(event)
        for op in operations:
            ns, es = project_operation(event, op)
            for n in ns:
                if n["id"] not in seen_nodes: seen_nodes.add(n["id"]); nodes.append(n)
            for e in es:
                key = (e["source"], e["target"], e["relation"], str(event.get("event_id")))
                if key not in seen_edges: seen_edges.add(key); links.append(e)
    return {"nodes": nodes, "links": links}
