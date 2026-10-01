#!/usr/bin/env python3
"""Synchronize unfinished-work sources, evidence claims, and branches into Graphify JSON."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

CONF = {"EXTRACTED": 1.0, "INFERRED": 0.75, "AMBIGUOUS": 0.25}

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def stable(value: str) -> str:
    text = re.sub(r"[^\w.-]+", "-", value.strip().lower(), flags=re.UNICODE).strip("-.")
    return text or hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def rows(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.is_file(): return [], []
    table = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or line.startswith("|---"): continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if cells: table.append(cells)
    return (table[0], table[1:]) if table else ([], [])

def add_node(nodes: dict, nid: str, label: str, entity_type: str, properties: dict, confidence="EXTRACTED", evidence=None):
    item = nodes.get(nid)
    if item is None:
        nodes[nid] = {"id": nid, "label": label, "entity_type": entity_type, "file_type": "concept", "aliases": [], "properties": properties, "status": "active", "confidence": confidence, "confidence_score": CONF.get(confidence, 0.5), "captured_at": now(), "evidence": evidence or []}
    else:
        item.setdefault("properties", {}).update(properties)
        if evidence: item.setdefault("evidence", []).extend(evidence)

def add_link(links: dict, source: str, target: str, relation: str, confidence="INFERRED", properties=None, evidence=None):
    key = f"{source}|{relation}|{target}"
    if key in links: return
    eid = "edge:" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:14]
    links[key] = {"id": eid, "key": eid, "source": source, "target": target, "relation": relation, "relation_category": "completion", "directed": True, "status": "active", "confidence": confidence, "confidence_score": CONF.get(confidence, 0.5), "properties": properties or {}, "transaction_from": now(), "transaction_to": None, "evidence": evidence or []}

def main() -> int:
    ap = argparse.ArgumentParser(description="Sync unfinished-completion ledgers into Graphify JSON")
    ap.add_argument("--root", required=True); ap.add_argument("--output")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); graph_path = root / "graphify-out" / "graph.json"
    if not graph_path.is_file(): raise SystemExit(f"Missing graph: {graph_path}")
    graph = load_json(graph_path); graph.setdefault("nodes", []); graph.setdefault("links", []); graph.setdefault("hyperedges", [])
    graph.setdefault("directed", True); graph.setdefault("multigraph", True); graph.setdefault("graph", {}).setdefault("schema", "minis.relationship-graph.v1")
    nodes = {n.get("id"): n for n in graph["nodes"] if n.get("id")}; links = {f"{e.get('source')}|{e.get('relation')}|{e.get('target')}": e for e in graph["links"] if e.get("source") and e.get("target") and e.get("relation")}
    project_id = "completion-project:" + stable(root.name)
    add_node(nodes, project_id, root.name, "project", {"completion_project": True, "completion_mode": json.loads((root / "completion-state.json").read_text(encoding="utf-8")).get("completion_mode", "undecided")})
    manifest = load_json(root / "source-manifest.json")
    source_ids = set()
    for item in manifest.get("sources", []):
        sid = str(item.get("source_id", "unknown")); source_ids.add(sid); nid = "source:" + stable(sid)
        add_node(nodes, nid, str(item.get("title", sid)), "document", {k: item.get(k) for k in ("source_id", "type", "edition", "chapter_range", "completeness", "permission_status", "source_url", "sha256")})
        add_link(links, project_id, nid, "has_source", "EXTRACTED")
    headers, evidence_rows = rows(root / "evidence-ledger.md")
    for cells in evidence_rows:
        if not cells or cells[0] in ("ID", "分支 ID", "主張"): continue
        cells += [""] * max(0, 10 - len(cells)); cid = cells[0]; claim_id = "claim:" + stable(cid); level = cells[2] or "INFERENCE"
        add_node(nodes, claim_id, cells[1] or cid, "claim", {"claim_id": cid, "evidence_layer": level, "confidence": cells[8] if len(cells) > 8 else "UNKNOWN"}, level if level in CONF else "INFERRED")
        raw_sources = re.split(r"[,，;； ]+", cells[3]) if len(cells) > 3 else []
        for sid in raw_sources:
            sid = sid.strip().strip("`")
            if not sid or sid.startswith("http") or sid not in source_ids: continue
            add_link(links, claim_id, "source:" + stable(sid), "supported_by", "EXTRACTED", evidence=[{"source_id": sid, "captured_at": now()}])
    _, hypothesis_rows = rows(root / "hypothesis-ledger.md")
    for cells in hypothesis_rows:
        if not cells or cells[0] in ("ID", "分支 ID"): continue
        cells += [""] * max(0, 11 - len(cells)); bid = cells[0]; branch_id = "branch:" + stable(bid)
        add_node(nodes, branch_id, cells[2] or bid, "concept", {"branch_id": bid, "completion_mode": cells[1], "status": cells[10] if len(cells) > 10 else "[PROPOSAL]"}, "INFERRED")
        add_link(links, project_id, branch_id, "has_branch", "INFERRED")
        for eid in re.split(r"[,，;； ]+", cells[3]):
            eid = eid.strip().strip("`")
            if eid: add_link(links, branch_id, "claim:" + stable(eid), "uses_evidence", "INFERRED")
    graph["nodes"] = list(nodes.values()); graph["links"] = list(links.values()); graph["graph"]["updated_at"] = now()
    audit = root / "graphify-out" / "audit.jsonl"; audit.parent.mkdir(parents=True, exist_ok=True)
    with audit.open("a", encoding="utf-8") as fh: fh.write(json.dumps({"at": now(), "operation": "sync_completion", "details": {"sources": len(source_ids), "nodes": len(graph["nodes"]), "links": len(graph["links"])}}, ensure_ascii=False) + "\n")
    save_path = Path(args.output).expanduser().resolve() if args.output else graph_path
    save_json(save_path, graph)
    print(json.dumps({"ok": True, "output": str(save_path), "sources": len(source_ids), "nodes": len(graph["nodes"]), "links": len(graph["links"])}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
