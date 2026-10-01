#!/usr/bin/env python3
"""Validate the evidence and publication boundary of a completion project."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

REQUIRED = (
    "completion-brief.md", "source-manifest.json", "textual-canon.md",
    "evidence-ledger.md", "author-intent-ledger.md", "version-conflicts.md",
    "feasibility-report.md", "hypothesis-ledger.md", "unfinished-thread-ledger.md",
    "rights-and-publication.md", "completion-provenance.md", "completion-state.json",
    "generation-log.jsonl",
)
MODES = {"undecided", "intent-reconstruction", "textual-continuation", "creative-completion"}
RIGHTS = {"own-work", "licensed", "public-domain", "private-only", "research", "public-noncommercial", "commercial", "unknown", "unlicensed", "restricted"}


def read(root: Path, name: str) -> str:
    path = root / name
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def table_rows(text: str):
    rows = []
    for line in text.splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            cells = [x.strip() for x in line.strip().strip("|").split("|")]
            if cells and cells[0] not in ("ID", "分支 ID", "問題", "線索／承諾", "主張", "日期"):
                rows.append(cells)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Run unfinished-novel completion gates")
    ap.add_argument("--root", required=True); ap.add_argument("--phase", choices=("intake", "evidence", "branch", "draft", "publication", "all"), default="all")
    ap.add_argument("--output")
    args = ap.parse_args(); root = Path(args.root).expanduser().resolve(); errors, warnings, checks = [], [], []
    for name in REQUIRED:
        ok = (root / name).is_file(); checks.append({"check": f"required:{name}", "ok": ok})
        if not ok: errors.append(f"missing required file: {name}")
    state = {}
    try:
        state = json.loads(read(root, "completion-state.json"))
        if state.get("schema") != "minis.unfinished-completion-state.v1": errors.append("unsupported completion-state schema")
    except Exception as exc:
        errors.append(f"invalid completion-state.json: {exc}")
    mode = state.get("completion_mode", "undecided")
    rights = state.get("rights_status", "unknown")
    if mode not in MODES: errors.append(f"invalid completion_mode: {mode}")
    if rights not in RIGHTS: warnings.append(f"unrecognized rights_status: {rights}")
    try:
        manifest = json.loads(read(root, "source-manifest.json"));
        if manifest.get("schema") != "minis.unfinished-source-manifest.v1": errors.append("unsupported source-manifest schema")
        if not isinstance(manifest.get("sources"), list): errors.append("source manifest sources must be a list")
    except Exception as exc:
        errors.append(f"invalid source-manifest.json: {exc}")
    brief = read(root, "completion-brief.md")
    intent = read(root, "author-intent-ledger.md")
    evidence = read(root, "evidence-ledger.md")
    hypotheses = read(root, "hypothesis-ledger.md")
    rights_text = read(root, "rights-and-publication.md")
    provenance = read(root, "completion-provenance.md")
    for label in ("TEXT-CANON", "AUTHOR-NOTE", "AUTHOR-STATEMENT", "INFERENCE", "PROPOSAL", "UNKNOWN"):
        checks.append({"check": f"evidence-label:{label}", "ok": label in evidence or label in intent or label in hypotheses})
    if "作者一定" in intent or "唯一原意" in intent or "這就是原本結局" in intent:
        errors.append("author-intent ledger contains overclaim language")
    if mode == "intent-reconstruction" and not table_rows(intent):
        warnings.append("intent-reconstruction selected but author-intent ledger has no data rows")
    if mode in ("textual-continuation", "creative-completion", "intent-reconstruction") and not table_rows(hypotheses):
        warnings.append(f"{mode} selected but hypothesis ledger has no branch rows")
    if rights in ("unknown", "unlicensed", "restricted") and state.get("purpose") not in ("private-only", "research"):
        errors.append("unknown/unlicensed/restricted rights cannot be marked for public or commercial purpose")
    if state.get("purpose") in ("public-noncommercial", "commercial"):
        if "non-official" not in rights_text.lower() and "非官方" not in rights_text:
            errors.append("public purpose requires non-official disclosure in rights file")
        if "ai" not in provenance.lower() and "AI" not in provenance:
            errors.append("public purpose requires AI disclosure field in provenance file")
    checks.append({"check": "rights-boundary", "ok": not any("rights" in x for x in errors)})
    checks.append({"check": "intent-no-overclaim", "ok": not any("overclaim" in x for x in errors)})
    result = {"schema": "minis.unfinished-completion-gate.v1", "project": root.name, "phase": args.phase, "result": "PASS" if not errors else "FAIL", "errors": errors, "warnings": warnings, "checks": checks, "completion_mode": mode, "rights_status": rights}
    out = Path(args.output).expanduser().resolve() if args.output else root / "gates" / "completion-gate.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
