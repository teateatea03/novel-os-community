#!/usr/bin/env python3
"""Validate special-object database classification and object contracts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REQUIRED = (
    "subject_category", "subject_subcategory", "subject_kind", "source_medium",
    "canon_scope", "version_scope", "franchise", "genre",
    "classification_basis", "classification_confidence",
)
CATEGORIES = {"real", "novel", "anime", "film", "game", "comic", "stage", "myth", "original", "other"}
KINDS = {"fictional_object_catalog", "real_technology_catalog", "original_object_catalog", "cross_media_catalog", "unknown"}
CANONS = {"real_record", "manga_canon", "anime_canon", "film_canon", "novel_canon", "game_canon", "cross_adaptation", "user_created", "unknown"}
CONFIDENCE = {"EXTRACTED", "INFERRED", "AMBIGUOUS"}
OBJECT_CATEGORIES = {"gadget", "powered_armor", "mecha", "mobile_suit", "vehicle", "weapon", "tool", "artifact", "device", "robot", "sentient_machine", "equipment_system", "other"}
OBJECT_KINDS = {"fictional_object", "real_technology", "original_object", "hybrid", "unknown"}
IDENTITY_MODES = {"singleton", "model_line", "variant", "loadout", "component", "copy", "prototype", "unknown"}
OBJECT_REQUIRED = ("object_category", "object_subcategory", "object_kind", "identity_mode", "version_scope", "canon_scope", "franchise", "classification_confidence")


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def check_classification(c: object, where: str, errors: list[str]) -> None:
    if not isinstance(c, dict):
        errors.append(f"{where}: missing classification object")
        return
    for key in REQUIRED:
        if key not in c or c[key] == "" or c[key] == [] or (c[key] is None and key != "franchise"):
            errors.append(f"{where}: missing classification.{key}")
    if c.get("subject_category") not in CATEGORIES: errors.append(f"{where}: invalid subject_category")
    if c.get("subject_kind") not in KINDS: errors.append(f"{where}: invalid subject_kind")
    if c.get("canon_scope") not in CANONS: errors.append(f"{where}: invalid canon_scope")
    if c.get("classification_confidence") not in CONFIDENCE: errors.append(f"{where}: invalid classification_confidence")
    for key in ("source_medium", "genre"):
        if not isinstance(c.get(key), list) or not all(isinstance(x, str) and x for x in c.get(key, [])):
            errors.append(f"{where}: classification.{key} must be a non-empty string array")
    for key in ("subject_subcategory", "version_scope", "classification_basis"):
        if not isinstance(c.get(key), str) or not c.get(key).strip(): errors.append(f"{where}: classification.{key} must be a non-empty string")


def check_object(n: dict, classification: dict, where: str, errors: list[str], warnings: list[str]) -> None:
    if n.get("entity_type") != "object" or n.get("properties", {}).get("special_object_record") is not True: return
    p = n.get("properties", {})
    for key in OBJECT_REQUIRED:
        if key not in p or p[key] == "" or p[key] == [] or (p[key] is None and key != "franchise"):
            errors.append(f"{where}: missing properties.{key}")
    if p.get("object_category") not in OBJECT_CATEGORIES: errors.append(f"{where}: invalid object_category")
    if p.get("object_kind") not in OBJECT_KINDS: errors.append(f"{where}: invalid object_kind")
    if p.get("identity_mode") not in IDENTITY_MODES: errors.append(f"{where}: invalid identity_mode")
    if p.get("canon_scope") not in CANONS: errors.append(f"{where}: invalid object canon_scope")
    if p.get("classification_confidence") not in CONFIDENCE: errors.append(f"{where}: invalid object classification_confidence")
    for key in REQUIRED:
        if p.get(key) != classification.get(key) and key in ("subject_category", "subject_subcategory", "subject_kind", "source_medium", "canon_scope", "version_scope", "franchise", "genre", "classification_basis", "classification_confidence"):
            # Object-level schema does not require all database classification fields in properties.
            pass
    if p.get("version_scope") in (None, "", "請填寫具體版本", "請填寫具體版本；不得只寫系列名"):
        errors.append(f"{where}: version_scope is not concrete")
    if n.get("confidence") == "EXTRACTED" and not (n.get("source_file") or n.get("source_url") or n.get("evidence")):
        warnings.append(f"{where}: EXTRACTED object lacks provenance")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True)
    ap.add_argument("--graph")
    args = ap.parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    batch = load(args.batch)
    classification = batch.get("classification")
    check_classification(classification, "batch", errors)
    objects = [n for n in batch.get("nodes", []) if n.get("entity_type") == "object" and n.get("properties", {}).get("special_object_record") is True]
    if not objects: warnings.append("batch: no special object root nodes")
    for n in objects: check_object(n, classification if isinstance(classification, dict) else {}, f"batch node {n.get('id')}", errors, warnings)
    if args.graph:
        graph = load(args.graph)
        graph_classification = graph.get("graph", {}).get("classification")
        check_classification(graph_classification, "graph", errors)
        if isinstance(classification, dict) and isinstance(graph_classification, dict):
            if {k: classification.get(k) for k in REQUIRED} != {k: graph_classification.get(k) for k in REQUIRED}:
                errors.append("graph: classification mismatch with batch")
        graph_objects = [n for n in graph.get("nodes", []) if n.get("entity_type") == "object" and n.get("properties", {}).get("special_object_record") is True]
        if not graph_objects: errors.append("graph: missing special object nodes")
        for n in graph_objects: check_object(n, graph_classification if isinstance(graph_classification, dict) else {}, f"graph node {n.get('id')}", errors, warnings)
    result = {"ok": not errors, "errors": errors, "warnings": warnings, "object_nodes": len(objects)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__": raise SystemExit(main())
