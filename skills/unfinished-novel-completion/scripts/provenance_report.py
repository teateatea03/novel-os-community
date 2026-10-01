#!/usr/bin/env python3
"""Summarize human and model decisions recorded in generation-log.jsonl."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path


def load(path: Path):
    entries, errors = [], []
    if not path.exists(): return entries, errors
    for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip(): continue
        try: entries.append(json.loads(line))
        except json.JSONDecodeError as exc: errors.append(f"line {no}: {exc}")
    return entries, errors


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a completion provenance report")
    ap.add_argument("--root", required=True); ap.add_argument("--format", choices=("json", "markdown"), default="json"); ap.add_argument("--output")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); entries, errors = load(root / "generation-log.jsonl")
    report = {"schema": "minis.unfinished-provenance-report.v1", "entry_count": len(entries), "parse_errors": errors,
              "by_stage": dict(Counter(str(x.get("stage", "unknown")) for x in entries)),
              "by_agent": dict(Counter(str(x.get("agent", "unknown")) for x in entries)),
              "by_action": dict(Counter(str(x.get("action", "unknown")) for x in entries)),
              "entries": entries}
    if args.format == "markdown":
        lines = ["# Completion Provenance Report｜補完溯源報告", "", f"- entries: {len(entries)}", f"- parse_errors: {len(errors)}", "", "## Summary", "", "| 維度 | 統計 |", "|---|---|"]
        for key in ("by_stage", "by_agent", "by_action"):
            lines.append(f"| {key} | `{json.dumps(report[key], ensure_ascii=False)}` |")
        lines += ["", "## Entries", "", "```json", json.dumps(entries, ensure_ascii=False, indent=2), "```", ""]
        content = "\n".join(lines)
    else:
        content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    out = Path(args.output).expanduser().resolve() if args.output else root / "research" / f"provenance-report.{ 'md' if args.format == 'markdown' else 'json' }"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(content, encoding="utf-8")
    print(json.dumps({"ok": not errors, "output": str(out), "entry_count": len(entries), "parse_errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
