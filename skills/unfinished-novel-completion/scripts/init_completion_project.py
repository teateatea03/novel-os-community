#!/usr/bin/env python3
"""Initialize a Novel OS project with unfinished-work completion ledgers."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MODES = ("undecided", "intent-reconstruction", "textual-continuation", "creative-completion")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_template(src: Path, dst: Path, slug: str) -> None:
    text = src.read_text(encoding="utf-8").replace("{{slug}}", slug)
    dst.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize a Novel OS unfinished-novel completion project")
    ap.add_argument("--title", required=True)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--root", default=os.environ.get("NOVEL_PROJECTS_ROOT", "~/.novel-os/novels"))
    ap.add_argument("--completion-mode", choices=MODES, default="undecided")
    ap.add_argument("--purpose", default="private-only")
    ap.add_argument("--rights-status", default="unknown")
    args = ap.parse_args()

    skill_dir = Path(__file__).resolve().parent.parent
    long_init = skill_dir.parent / "long-form-novel-writer" / "scripts" / "init_novel_project.py"
    if not long_init.is_file():
        raise SystemExit(f"Missing long-form initializer: {long_init}")
    root = Path(args.root).expanduser().resolve()
    project = root / args.slug
    result = subprocess.run(
        [sys.executable, str(long_init), "--title", args.title, "--slug", args.slug, "--root", str(root)],
        text=True, capture_output=True,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or result.stdout.strip() or "long-form initializer failed")
    if not project.is_dir():
        raise SystemExit(f"Initializer did not create project: {project}")

    templates = skill_dir / "templates"
    names = (
        "completion-brief.md", "source-manifest.json", "textual-canon.md",
        "evidence-ledger.md", "author-intent-ledger.md", "version-conflicts.md",
        "feasibility-report.md", "hypothesis-ledger.md", "unfinished-thread-ledger.md",
        "rights-and-publication.md", "completion-provenance.md", "completion-state.json",
        "generation-log.jsonl",
    )
    for name in names:
        src = templates / name
        if not src.is_file():
            raise SystemExit(f"Missing completion template: {src}")
        copy_template(src, project / name, args.slug)

    brief = project / "completion-brief.md"
    brief_text = brief.read_text(encoding="utf-8")
    brief_text = brief_text.replace("- source_work: ", f"- source_work: {args.title}")
    brief_text = brief_text.replace("- original_author: ", "- original_author: UNKNOWN")
    brief_text = brief_text.replace("- completion_mode: undecided", f"- completion_mode: {args.completion_mode}")
    brief_text = brief_text.replace("- purpose: private-only", f"- purpose: {args.purpose}")
    brief_text = brief_text.replace("- rights_status: unknown", f"- rights_status: {args.rights_status}")
    brief.write_text(brief_text, encoding="utf-8")

    rights = project / "rights-and-publication.md"
    rights_text = rights.read_text(encoding="utf-8")
    rights_text = rights_text.replace("- rights_status: unknown", f"- rights_status: {args.rights_status}")
    rights_text = rights_text.replace("- purpose: private-only", f"- purpose: {args.purpose}")
    rights.write_text(rights_text, encoding="utf-8")

    state_path = project / "completion-state.json"
    state = load_json(state_path)
    state.update({
        "project": args.slug, "completion_mode": args.completion_mode,
        "rights_status": args.rights_status, "purpose": args.purpose,
        "updated_at": utc_now(),
    })
    write_json(state_path, state)

    for metadata_name in ("project.json", "workflow-state.json"):
        path = project / metadata_name
        if not path.is_file():
            continue
        data = load_json(path)
        data["completion_mode"] = args.completion_mode
        data["completion_project"] = True
        data["rights_status"] = args.rights_status
        data["completion_phase"] = "intake"
        data["updated_at"] = utc_now()
        write_json(path, data)

    print(json.dumps({"ok": True, "project": str(project), "completion_mode": args.completion_mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
