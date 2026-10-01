from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json
from .semantic_projection import project_semantic_deltas
from .temporal_graph import project_temporal_relations


def project_events(events: list[dict[str, Any]], *, project_id: str, session_id: str,
                   branch_id: str) -> dict[str, Any]:
    """Build a reproducible Graphify-compatible event/turn dependency graph."""
    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    seen: set[str] = set()

    def node(node_id: str, label: str, entity_type: str, **properties: Any) -> None:
        if node_id in seen: return
        seen.add(node_id)
        nodes.append({"id": node_id, "label": label, "entity_type": entity_type,
                      "properties": properties})

    branch_node = f"branch:{session_id}:{branch_id}"
    node(branch_node, branch_id, "branch", project_id=project_id, session_id=session_id)
    previous = None
    for event in events:
        event_id = str(event.get("event_id"))
        eid = f"event:{event_id}"
        actor_id = str(event.get("actor_id", "unknown"))
        aid = f"actor:{actor_id}"
        semantic = event.get("semantic_delta") if isinstance(event.get("semantic_delta"), dict) else {}
        node(eid, semantic.get("summary") or f"{event.get('turn_id')} {event.get('action_type')}", "event",
             turn_id=event.get("turn_id"), action_type=event.get("action_type"),
             semantic_kind=semantic.get("semantic_kind"), semantic_delta_hash=event.get("semantic_delta_hash"),
             verdict=event.get("verdict"), valid_from=event.get("created_at"),
             source=event.get("source"), state_hash=event.get("after_state_hash"))
        node(aid, actor_id, "person" if actor_id != "world" else "system")
        links.append({"source": aid, "target": eid, "relation": "performed",
                      "status": "active", "confidence": "EXTRACTED", "evidence": [{"event_id": event_id}]})
        links.append({"source": eid, "target": branch_node, "relation": "occurred_in",
                      "status": "active", "confidence": "EXTRACTED", "evidence": [{"event_id": event_id}]})
        if previous:
            links.append({"source": previous, "target": eid, "relation": "precedes",
                          "status": "active", "confidence": "EXTRACTED", "evidence": [{"event_id": event_id}]})
        previous = eid
    semantic = project_semantic_deltas(events)
    for item in semantic["nodes"]:
        if item["id"] not in seen:
            seen.add(item["id"])
            nodes.append(item)
    # State-like relations use one active edge per semantic slot and preserve
    # invalidated history for point-in-time queries. Non-state event edges
    # remain append-only in the simple semantic projection.
    temporal = project_temporal_relations(events)
    temporal_relations = {"located_in", "possessed_by", "knows", "relation_changed"}
    links.extend(x for x in semantic["links"] if x.get("relation") not in temporal_relations)
    links.extend(temporal)
    graph = {"directed": True, "multigraph": True,
             "graph": {"schema": "minis.relationship-graph.v1", "title": f"{project_id} interactive events",
                       "projection_schema": "minis.interactive-graph-projection.v3", "created_at": now_iso(),
                       "source_hash": sha256_json(events)},
             "nodes": nodes, "links": links, "hyperedges": []}
    return graph


def rebuild_projection(store: Any, output_root: str | Path | None = None) -> dict[str, Any]:
    graph = project_events(store.read_events(), project_id=store.project_id,
                           session_id=store.session_id, branch_id=store.branch_id)
    root = Path(output_root) if output_root else store.root / "graphify-out" / "interactive"
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{store.session_id}-{store.branch_id}.json"
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(graph, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return {"status": "pass", "path": str(path), "node_count": len(graph["nodes"]),
            "edge_count": len(graph["links"]), "source_hash": graph["graph"]["source_hash"]}
