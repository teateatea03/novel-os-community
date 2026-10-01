#!/usr/bin/env python3
"""Store public comparison images beside a character DB. Graph JSON stays text."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA = "minis.character-visual.v1"
VERSION = "1.0.0"
UA = "MinisCharacterVisual/1.0"
ROLES = {"official_avatar", "work_visual", "event_photo", "comparison_still", "other"}
MIME_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_BYTES = 5 * 1024 * 1024
FORBIDDEN_HOST = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def db_root(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    if (p / "graphify-out" / "graph.json").exists():
        return p
    if p.name == "graphify-out" and (p / "graph.json").exists():
        return p.parent
    if p.name == "graph.json":
        return p.parent.parent
    raise SystemExit(f"not a character database root: {path}")


def visuals_dir(root: Path) -> Path:
    d = root / "visuals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_graph(root: Path) -> dict[str, Any]:
    p = root / "graphify-out" / "graph.json"
    if not p.exists():
        raise SystemExit(f"missing graph: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def atomic_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def sniff_mime(data: bytes, declared: str | None) -> str:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if declared and declared.split(";")[0].strip().lower() in MIME_EXT:
        return declared.split(";")[0].strip().lower()
    raise SystemExit("not a supported image (jpeg/png/webp/gif)")


def read_local(path: str) -> bytes:
    p = Path(path).expanduser()
    data = p.read_bytes()
    if len(data) > MAX_BYTES:
        raise SystemExit(f"image larger than {MAX_BYTES} bytes")
    return data


def fetch_url(url: str) -> tuple[bytes, str | None]:
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise SystemExit("only http(s) image URLs")
    host = (p.hostname or "").lower()
    if host in FORBIDDEN_HOST or host.endswith(".local"):
        raise SystemExit("local image URL denied")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,*/*;q=0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        ctype = resp.headers.get("Content-Type")
        data = resp.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SystemExit(f"image larger than {MAX_BYTES} bytes")
    return data, ctype


def sidecar_path(root: Path, digest: str) -> Path:
    return visuals_dir(root) / f"{digest}.json"


def load_sidecar(root: Path, digest: str) -> dict[str, Any] | None:
    p = sidecar_path(root, digest)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def write_bytes(root: Path, data: bytes, mime: str) -> tuple[str, Path]:
    digest = sha256_bytes(data)
    ext = MIME_EXT[mime]
    img = visuals_dir(root) / f"{digest}{ext}"
    if not img.exists():
        img.write_bytes(data)
    else:
        if sha256_bytes(img.read_bytes()) != digest:
            raise SystemExit(f"hash collision at {img}")
    return digest, img


def cmd_add(args: argparse.Namespace) -> int:
    root = db_root(args.db)
    role = args.role
    if role not in ROLES:
        raise SystemExit(f"role must be one of {sorted(ROLES)}")
    if args.file:
        data = read_local(args.file)
        declared = None
    elif args.url:
        data, declared = fetch_url(args.url)
    else:
        raise SystemExit("need --file or --url")
    mime = sniff_mime(data, declared)
    digest, img = write_bytes(root, data, mime)
    rel = f"visuals/{img.name}"
    existing = load_sidecar(root, digest) or {}
    visual_id = existing.get("visual_id") or f"visual:{root.name}-{digest[:10]}"
    sources = list(existing.get("source_urls") or [])
    src = args.source_url or args.url
    if src and src not in sources:
        sources.append(src)
    rec = {
        "schema": SCHEMA,
        "ingester_version": VERSION,
        "visual_id": visual_id,
        "role": role,
        "source_url": src,
        "source_urls": sources,
        "page_url": args.page_url,
        "captured_at": existing.get("captured_at") or now(),
        "updated_at": now(),
        "sha256": digest,
        "mime": mime,
        "bytes": len(data),
        "local_path": rel,
        "access_mode": args.access_mode,
        "privacy_class": "P1",
        "rights_note": args.rights_note,
        "person_id": args.person,
        "label": args.label or role,
    }
    atomic_json(sidecar_path(root, digest), rec)
    graph_note = {
        "id": visual_id,
        "label": rec["label"],
        "entity_type": "resource",
        "properties": {
            "kind": "public_visual",
            "visual_schema": SCHEMA,
            "role": role,
            "sha256": digest,
            "local_path": rel,
            "source_url": src,
            "mime": mime,
            "access_mode": args.access_mode,
            "privacy_class": "P1",
        },
        "source_url": src,
        "confidence": "EXTRACTED",
    }
    print(json.dumps({"ok": True, "record": rec, "resource_node": graph_note, "has_visual": {"source": args.person, "relation": "has_visual", "target": visual_id}}, ensure_ascii=False, indent=2))
    if args.write_graph:
        _merge_graph(root, args.person, rec, graph_note)
    return 0


def _merge_graph(root: Path, person_id: str, rec: dict[str, Any], node: dict[str, Any]) -> None:
    data = load_graph(root)
    nodes = {n.get("id"): n for n in data.get("nodes") or []}
    if rec["visual_id"] not in nodes:
        data.setdefault("nodes", []).append(
            {
                **node,
                "aliases": [],
                "status": "active",
                "confidence_score": 0.9,
                "captured_at": rec["captured_at"],
                "evidence": [{"source_url": rec.get("source_url"), "quote": rec.get("role"), "captured_at": rec["captured_at"]}],
            }
        )
    if person_id:
        person = nodes.get(person_id)
        if person is None:
            raise SystemExit(f"person node not found: {person_id}")
        props = person.setdefault("properties", {})
        refs = props.setdefault("visual_refs", [])
        entry = {
            "visual_id": rec["visual_id"],
            "role": rec["role"],
            "local_path": rec["local_path"],
            "sha256": rec["sha256"],
            "source_url": rec.get("source_url"),
        }
        if not any(x.get("sha256") == rec["sha256"] for x in refs if isinstance(x, dict)):
            refs.append(entry)
        if rec["role"] == "official_avatar":
            props.setdefault("primary_visual_id", rec["visual_id"])
        links = data.setdefault("links", [])
        if not any(
            e.get("source") == person_id and e.get("target") == rec["visual_id"] and e.get("relation") == "has_visual"
            for e in links
        ):
            links.append(
                {
                    "id": f"edge:has-visual-{rec['sha256'][:10]}",
                    "source": person_id,
                    "target": rec["visual_id"],
                    "relation": "has_visual",
                    "relation_category": "evidence",
                    "status": "active",
                    "confidence": "EXTRACTED",
                    "confidence_score": 0.9,
                    "evidence": [{"source_url": rec.get("source_url")}],
                }
            )
        bak = root / "graphify-out" / "graph.json.bak"
        src = root / "graphify-out" / "graph.json"
        shutil.copyfile(src, bak)
        atomic_json(src, data)


def list_visuals(root: Path) -> list[dict[str, Any]]:
    out = []
    for p in sorted(visuals_dir(root).glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


def resolve_visual(root: Path, ident: str) -> dict[str, Any]:
    for rec in list_visuals(root):
        if ident in {rec.get("visual_id"), rec.get("sha256"), rec.get("local_path")} or ident.endswith(rec.get("sha256") or "---"):
            return rec
        if ident == rec.get("role") and rec.get("role") == "official_avatar":
            return rec
    raise SystemExit(f"visual not found: {ident}")


def cmd_list(args: argparse.Namespace) -> int:
    root = db_root(args.db)
    rows = [
        {k: r.get(k) for k in ("visual_id", "role", "sha256", "local_path", "source_url", "person_id")}
        for r in list_visuals(root)
    ]
    print(json.dumps({"ok": True, "count": len(rows), "visuals": rows}, ensure_ascii=False, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    root = db_root(args.db)
    recs = [resolve_visual(root, i) for i in args.id]
    if len(recs) < 2:
        raise SystemExit("compare needs at least two --id")
    paths = []
    for r in recs:
        p = root / r["local_path"]
        if not p.exists():
            raise SystemExit(f"missing file {p}")
        paths.append(str(p))
    vision = shutil.which("apple-vision")
    if not vision:
        print(json.dumps({"ok": False, "error": "apple_vision_not_found", "paths": paths}, ensure_ascii=False, indent=2))
        return 2
    cmd = [vision, "similarity", *paths, "--threshold", str(args.threshold)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    raw = proc.stdout or proc.stderr
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"raw": raw[-4000:]}
    report = {
        "ok": proc.returncode == 0,
        "tool": "apple-vision similarity",
        "threshold": args.threshold,
        "visual_ids": [r.get("visual_id") for r in recs],
        "sha256": [r.get("sha256") for r in recs],
        "source_url": [r.get("source_url") for r in recs],
        "result": parsed,
        "note": "similarity is a comparison aid, not biometric identification",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--db", required=True)
    a.add_argument("--person", default="")
    a.add_argument("--file")
    a.add_argument("--url")
    a.add_argument("--source-url")
    a.add_argument("--page-url")
    a.add_argument("--role", default="comparison_still")
    a.add_argument("--label")
    a.add_argument("--access-mode", default="anonymous_public")
    a.add_argument("--rights-note", default="public_page")
    a.add_argument("--write-graph", action="store_true")
    a.set_defaults(func=cmd_add)
    l = sub.add_parser("list")
    l.add_argument("--db", required=True)
    l.set_defaults(func=cmd_list)
    c = sub.add_parser("compare")
    c.add_argument("--db", required=True)
    c.add_argument("--id", action="append", required=True)
    c.add_argument("--threshold", type=float, default=0.9)
    c.set_defaults(func=cmd_compare)
    return p


def main() -> int:
    a = parser().parse_args()
    try:
        return a.func(a)
    except KeyboardInterrupt:
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
