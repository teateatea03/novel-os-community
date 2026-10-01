from __future__ import annotations

"""Read-only audit for legacy project-specific canonical writers.

Step 1 does not edit a live novel project. This scanner proves which files
would conflict with ProjectRuntimeAdapter before Step 3 cutover.
"""

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

MUTATION_PATTERNS = {
    "event_log_replace": [re.compile(r"targets\[['\"]event['\"]\]"), re.compile(r"MAP\s*=.*['\"]event['\"]\s*:", re.S), re.compile(r"os\.replace\s*\([^\n]*events")],
    "state_direct_write": [re.compile(r"targets\[['\"]state['\"]\]"), re.compile(r"MAP\s*=.*['\"]state['\"]\s*:", re.S), re.compile(r"(?:write|copy2|os\.replace)\s*\([^\n]*state/current\.json")],
    "runtime_head_direct_write": [re.compile(r"write\s*\(ROOT\s*/\s*['\"]runtime-head\.json['\"]"), re.compile(r"(?:copy2|os\.replace)\s*\([^\n]*runtime-head\.json")],
    "project_pointer_direct_write": [re.compile(r"\[['\"](?:canon_through|latest_draft)['\"]\]\s*="), re.compile(r"write\s*\([^\n]*project\.json")],
    "branch_manifest_direct_write": [re.compile(r"write\s*\(BASE\s*/\s*['\"]branch-manifest\.json['\"]"), re.compile(r"(?:copy2|os\.replace)\s*\([^\n]*branch-manifest\.json"), re.compile(r"update_head\s*\(")],
    "canonical_scene_direct_write": [re.compile(r"targets\[['\"]scene['\"]\]"), re.compile(r"MAP\s*=.*['\"]scene['\"]\s*:", re.S), re.compile(r"(?:write|copy2|os\.replace)\s*\([^\n]*interactive/scenes")],
}
LEGACY_NAMES = {"atomic-canon-writer.py", "build-runtime-head.py", "candidate-lifecycle.py"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_project(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    candidates: set[Path] = set()
    for directory in (root / "interactive" / "runtime", root / "runtime", root / "scripts"):
        if directory.exists():
            candidates.update(p for p in directory.rglob("*.py") if p.is_file())
    findings = []
    for path in sorted(candidates):
        text = path.read_text(encoding="utf-8", errors="replace")
        capabilities = sorted(name for name, patterns in MUTATION_PATTERNS.items() if any(pattern.search(text) for pattern in patterns))
        if capabilities or path.name in LEGACY_NAMES:
            findings.append({
                "path": str(path.relative_to(root)),
                "sha256": sha(path),
                "legacy_name": path.name in LEGACY_NAMES,
                "canonical_mutation_capabilities": capabilities,
                "required_mode_before_cutover": "migration_read_only" if capabilities else "review",
            })
    authority = root / "interactive" / "sessions"
    records = list(authority.rglob("production-authority.json")) if authority.exists() else []
    active_legacy = [x for x in findings if x["canonical_mutation_capabilities"]]
    return {
        "schema": "minis.legacy-writer-inventory.v1",
        "project_root": str(root),
        "status": "cutover_blocked" if active_legacy else "no_legacy_writer_detected",
        "production_authority_records": [str(p.relative_to(root)) for p in records],
        "legacy_writers": findings,
        "active_canonical_mutation_paths": len(active_legacy),
        "required_next": "Step 3 migration and cutover; do not modify live project during Step 1" if active_legacy else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", required=True); parser.add_argument("--out")
    args = parser.parse_args(); report = scan_project(args.root)
    raw = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out: Path(args.out).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0


if __name__ == "__main__": raise SystemExit(main())
