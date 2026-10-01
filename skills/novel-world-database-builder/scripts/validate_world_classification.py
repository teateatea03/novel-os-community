#!/usr/bin/env python3
"""Validate the mandatory classification contract for a world batch or graph."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REQUIRED = (
    "subject_category", "subject_subcategory", "subject_kind", "source_medium",
    "canon_scope", "version_scope", "franchise", "genre",
    "classification_basis", "classification_confidence",
)
CATEGORIES = {"real", "novel", "anime", "film", "game", "stage", "myth", "original", "other"}
KINDS = {"real_world", "fictional_world", "adapted_world", "shared_world", "unknown"}
CANONS = {"real_record", "novel_canon", "manga_canon", "anime_canon", "film_canon", "cross_adaptation", "user_created", "unknown"}
CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_classification(c: object, where: str, errors: list[str]) -> None:
    if not isinstance(c, dict):
        errors.append(f"{where}: missing classification object")
        return
    for key in REQUIRED:
        if key not in c or c[key] == "" or c[key] == [] or (c[key] is None and key != "franchise"):
            errors.append(f"{where}: missing classification.{key}")
    if c.get("subject_category") not in CATEGORIES:
        errors.append(f"{where}: invalid subject_category")
    if c.get("subject_kind") not in KINDS:
        errors.append(f"{where}: invalid subject_kind")
    if c.get("canon_scope") not in CANONS:
        errors.append(f"{where}: invalid canon_scope")
    if c.get("classification_confidence") not in CONFIDENCE:
        errors.append(f"{where}: invalid classification_confidence")
    for key in ("source_medium", "genre"):
        if not isinstance(c.get(key), list) or not all(isinstance(x, str) and x for x in c.get(key, [])):
            errors.append(f"{where}: classification.{key} must be a non-empty string array")
    for key in ("subject_subcategory", "version_scope", "classification_basis"):
        if not isinstance(c.get(key), str) or not c.get(key).strip():
            errors.append(f"{where}: classification.{key} must be a non-empty string")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--graph")
    args = ap.parse_args()
    errors: list[str] = []
    batch = load(args.batch)
    classification = batch.get("classification")
    check_classification(classification, "batch", errors)
    roots = [n for n in batch.get("nodes", []) if n.get("id", "").startswith("world:") or n.get("properties", {}).get("world_category") == "world"]
    if not roots:
        errors.append("batch: missing world root node")
    for n in roots:
        props = n.get("properties", {})
        root_class = {k: props.get(k) for k in REQUIRED}
        if isinstance(classification, dict) and root_class != {k: classification.get(k) for k in REQUIRED}:
            errors.append(f"batch: classification mismatch on world root {n.get('id')}")
    if args.graph:
        graph = load(args.graph)
        check_classification(graph.get("graph", {}).get("classification"), "graph", errors)
        roots = [n for n in graph.get("nodes", []) if n.get("id", "").startswith("world:") or n.get("properties", {}).get("world_category") == "world"]
        if not roots:
            errors.append("graph: missing world root node")
        for n in roots:
            props = n.get("properties", {})
            if isinstance(classification, dict) and any(props.get(k) != classification.get(k) for k in REQUIRED):
                errors.append(f"graph: classification mismatch on world root {n.get('id')}")
    result = {"ok": not errors, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
