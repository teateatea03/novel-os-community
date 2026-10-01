#!/usr/bin/env python3
"""Compare branch rows in the hypothesis ledger and report divergence."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path


def rows(path: Path):
    text = path.read_text(encoding="utf-8")
    result = {}
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if not cells or cells[0] in ("分支 ID", "branch_id", ""):
            continue
        result[cells[0]] = cells
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare unfinished completion branches")
    ap.add_argument("--root", required=True); ap.add_argument("--branch-a", required=True); ap.add_argument("--branch-b", required=True); ap.add_argument("--output")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); ledger = root / "hypothesis-ledger.md"
    if not ledger.is_file(): raise SystemExit(f"Missing hypothesis ledger: {ledger}")
    data = rows(ledger); a, b = data.get(args.branch_a), data.get(args.branch_b)
    if not a or not b: raise SystemExit("Both branch IDs must have rows in hypothesis-ledger.md")
    width = max(len(a), len(b)); differences = []
    for i in range(width):
        av, bv = a[i] if i < len(a) else "", b[i] if i < len(b) else ""
        if av != bv: differences.append({"column": i + 1, "branch_a": av, "branch_b": bv})
    report = {"schema": "minis.unfinished-branch-diff.v1", "branch_a": args.branch_a, "branch_b": args.branch_b, "differences": differences, "same": not differences}
    out = Path(args.output).expanduser().resolve() if args.output else root / "research" / f"branch-diff-{args.branch_a}-vs-{args.branch_b}.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(out), "same": not differences, "difference_count": len(differences)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
