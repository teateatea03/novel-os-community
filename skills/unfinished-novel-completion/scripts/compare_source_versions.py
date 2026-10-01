#!/usr/bin/env python3
"""Compare two registered local source versions with a bounded unified diff."""
from __future__ import annotations
import argparse
import difflib
import json
from datetime import datetime, timezone
from pathlib import Path


def manifest(root: Path) -> dict:
    return json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))


def find(data: dict, sid: str) -> dict:
    for item in data.get("sources", []):
        if item.get("source_id") == sid:
            return item
    raise SystemExit(f"Unknown source_id: {sid}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare two registered unfinished-work sources")
    ap.add_argument("--root", required=True); ap.add_argument("--source-a", required=True); ap.add_argument("--source-b", required=True)
    ap.add_argument("--output")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); data = manifest(root)
    a, b = find(data, args.source_a), find(data, args.source_b)
    if not a.get("source_path") or not b.get("source_path"):
        raise SystemExit("Both sources need local --source-path entries")
    pa, pb = Path(a["source_path"]), Path(b["source_path"])
    if not pa.is_file() or not pb.is_file():
        raise SystemExit("One or both source files are missing")
    la = pa.read_text(encoding="utf-8", errors="replace").splitlines()
    lb = pb.read_text(encoding="utf-8", errors="replace").splitlines()
    diff = list(difflib.unified_diff(la, lb, fromfile=args.source_a, tofile=args.source_b, lineterm=""))
    changed = sum(1 for line in diff if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    report = [
        "# Source Version Diff｜來源版本差異",
        "", f"- generated_at: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- source_a: `{args.source_a}` — {a.get('title')}", f"- source_b: `{args.source_b}` — {b.get('title')}",
        f"- lines_a: {len(la)}", f"- lines_b: {len(lb)}", f"- changed_lines: {changed}", "",
        "```diff", "\n".join(diff[:20000]), "```", "",
        "> 差異報告是衍生資料；重要衝突另記入 `version-conflicts.md`，不自動覆寫正典。",
    ]
    out = Path(args.output).expanduser().resolve() if args.output else root / "research" / f"version-diff-{args.source_a}-vs-{args.source_b}.md"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(out), "lines_a": len(la), "lines_b": len(lb), "changed_lines": changed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
