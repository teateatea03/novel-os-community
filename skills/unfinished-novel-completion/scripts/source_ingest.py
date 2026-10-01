#!/usr/bin/env python3
"""Register and validate unfinished-novel source metadata without copying source text."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = "source-manifest.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(root: Path) -> dict:
    path = root / MANIFEST
    if not path.exists():
        return {"schema": "minis.unfinished-source-manifest.v1", "project": root.name, "updated_at": None, "sources": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "minis.unfinished-source-manifest.v1":
        raise SystemExit(f"Unsupported source manifest schema: {data.get('schema')}")
    data.setdefault("sources", [])
    return data


def save(root: Path, data: dict) -> None:
    data["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (root / MANIFEST).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register(args) -> int:
    root = Path(args.root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    data = load(root)
    if any(x.get("source_id") == args.source_id for x in data["sources"]):
        raise SystemExit(f"Duplicate source_id: {args.source_id}")
    if not args.source_path and not args.source_url:
        raise SystemExit("register needs --source-path or --source-url")
    item = {
        "source_id": args.source_id, "title": args.title or args.source_id,
        "author": args.author or "UNKNOWN", "type": args.type,
        "edition": args.edition or "UNKNOWN", "chapter_range": args.chapter_range or "UNKNOWN",
        "source_url": args.source_url, "source_path": None, "captured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "completeness": args.completeness, "permission_status": args.permission_status,
        "provided_by_user": bool(args.provided_by_user), "notes": args.notes or "",
    }
    if args.source_path:
        path = Path(args.source_path).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"Source file not found: {path}")
        item["source_path"] = str(path)
        item["bytes"] = path.stat().st_size
        item["sha256"] = digest(path)
    else:
        item["bytes"] = None
        item["sha256"] = None
    data["sources"].append(item)
    save(root, data)
    print(json.dumps({"ok": True, "source": item}, ensure_ascii=False, indent=2))
    return 0


def validate(args) -> int:
    root = Path(args.root).expanduser().resolve()
    data = load(root)
    errors, warnings, seen = [], [], set()
    for item in data.get("sources", []):
        sid = item.get("source_id")
        if not sid: errors.append("source missing source_id")
        if sid in seen: errors.append(f"duplicate source_id: {sid}")
        seen.add(sid)
        if not item.get("source_path") and not item.get("source_url"):
            errors.append(f"source has no path or URL: {sid}")
        path_value = item.get("source_path")
        if path_value:
            path = Path(path_value).expanduser()
            if not path.is_file(): errors.append(f"missing local source: {sid}: {path}")
            else:
                actual = digest(path)
                if item.get("sha256") and actual != item["sha256"]:
                    errors.append(f"sha256 mismatch: {sid}")
        if item.get("permission_status") in (None, "", "unknown"):
            warnings.append(f"permission status unknown: {sid}")
        if item.get("completeness") in (None, "", "unknown"):
            warnings.append(f"completeness unknown: {sid}")
    result = {"schema": "minis.unfinished-source-validation.v1", "ok": not errors, "errors": errors, "warnings": warnings, "source_count": len(data.get("sources", []))}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Manage unfinished-novel source manifest")
    ap.add_argument("--root", required=True)
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("register")
    r.add_argument("--source-id", required=True); r.add_argument("--title"); r.add_argument("--author"); r.add_argument("--type", default="unknown")
    r.add_argument("--edition"); r.add_argument("--chapter-range"); r.add_argument("--source-path"); r.add_argument("--source-url")
    r.add_argument("--completeness", default="unknown"); r.add_argument("--permission-status", default="unknown")
    r.add_argument("--provided-by-user", action="store_true"); r.add_argument("--notes")
    r.set_defaults(func=register)
    v = sub.add_parser("validate"); v.set_defaults(func=validate)
    args = ap.parse_args(); return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
