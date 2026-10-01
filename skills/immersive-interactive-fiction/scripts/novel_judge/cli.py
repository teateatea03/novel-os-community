from __future__ import annotations

import argparse, json
from pathlib import Path
from .store import FileStore
from .engine import commit_turn, recover_store, replay_events
from .migrations import migrate_state_file
from .graph_projector import rebuild_projection
from .structured_output import adapter_contract
from .event_log import build_event_index, repair_corrupt_tail, compact_event_log
from .longform_projector import project_longform_markdown, projection_status
from .author_console import author_console_report


AUTHOR_COMMANDS = {
    "resume", "scenes", "preview-context", "inspect-scene", "export-manuscript", "playtest",
    "draft-scene", "diff-scene", "accept-scene", "workbench-refresh", "record-decision",
}

REVIEW_COMMANDS = {
    "inspect-prose", "diagnose", "cold-read", "open-beta", "pairwise",
}


def _dump(out) -> int:
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def _author_text(args, root: Path) -> tuple[str, str]:
    if args.text is not None:
        return str(args.text), args.path or "stdin"
    if args.output:
        path = Path(args.output)
        if path.is_file():
            return path.read_text(encoding="utf-8"), str(path)
    relative = args.path or ""
    if relative:
        path = Path(relative)
        if not path.is_absolute():
            path = (root / relative).resolve()
            if root.resolve() not in path.parents and path != root.resolve():
                raise SystemExit("path escapes project root")
        if path.is_file():
            return path.read_text(encoding="utf-8"), relative
    raise SystemExit("inspect-prose/cold-read requires --text, --output file, or --path")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="novel-judge")
    p.add_argument("command", choices=[
        "recover", "replay", "judge", "migrate", "project-graph", "schema", "index-events",
        "repair-events", "compact-events", "project-longform", "projection-status", "author-console",
        "resume", "scenes", "preview-context", "inspect-scene", "export-manuscript", "playtest",
        "draft-scene", "diff-scene", "accept-scene", "workbench-refresh", "record-decision",
        "inspect-prose", "diagnose", "cold-read", "open-beta", "pairwise",
    ])
    p.add_argument("root")
    p.add_argument("project", nargs="?", default=None)
    p.add_argument("session", nargs="?", default=None)
    p.add_argument("--branch", default="main")
    p.add_argument("--intent")
    p.add_argument("--path")
    p.add_argument("--task", default="render")
    p.add_argument("--provider", default="generic")
    p.add_argument("--retain-active", type=int, default=200)
    p.add_argument("--actor", default=None)
    p.add_argument("--query", default="")
    p.add_argument("--limit", type=int, default=40)
    p.add_argument("--output")
    p.add_argument("--draft-id")
    p.add_argument("--text")
    p.add_argument("--note")
    p.add_argument("--author-id", default="author")
    p.add_argument("--decision", choices=["accept", "revise", "reject"])
    p.add_argument("--candidate-hash")
    p.add_argument("--reason-codes", default="")
    p.add_argument("--revision-round", type=int)
    args = p.parse_args(argv)
    if args.command in REVIEW_COMMANDS:
        root = Path(args.root)
        if args.command == "inspect-prose":
            from .scene_review import review_scene_text
            text, source = _author_text(args, root)
            return _dump(review_scene_text(text, scene_id=Path(source).stem, source=source))
        if args.command == "diagnose":
            from .editorial_diagnosis import diagnose_manuscript, diagnose_text
            if args.path:
                target = root / args.path
                if target.is_dir():
                    return _dump(diagnose_manuscript(target))
                return _dump(diagnose_text(target.read_text(encoding="utf-8") if target.is_file() else "", source=str(target)))
            return _dump(diagnose_manuscript(root))
        if args.command == "cold-read":
            from .cold_read import cold_read_text
            text, source = _author_text(args, root)
            return _dump(cold_read_text(text, source=source))
        if args.command == "open-beta":
            from .cold_read import open_beta_session
            return _dump(open_beta_session(root, session_id=args.draft_id or "beta", readers=[args.author_id] if args.author_id else None))
        from .pairwise_judge import DEFAULT_ADVERSARIAL_FIXTURES, evaluate_fixture_set
        return _dump(evaluate_fixture_set(DEFAULT_ADVERSARIAL_FIXTURES))
    if args.command in AUTHOR_COMMANDS:
        from .author_resume import load_project_adapter, build_resume_card
        adapter = load_project_adapter(args.root)
        if args.command == "resume":
            return _dump(build_resume_card(adapter))
        if args.command == "scenes":
            from .scene_studio import list_scenes
            return _dump(list_scenes(adapter, query=args.query, limit=args.limit))
        if args.command == "preview-context":
            from .scene_studio import preview_context
            actor_id = args.actor or next(iter((adapter.store.load_state() or {}).get("actors") or {"player": None}), "player")
            return _dump(preview_context(adapter, actor_id=actor_id))
        if args.command == "inspect-scene":
            from .scene_studio import inspect_scene_file
            return _dump(inspect_scene_file(adapter, relative_path=args.path or ""))
        if args.command == "draft-scene":
            from .scene_studio import save_scene_draft
            text = args.text
            if args.output and Path(args.output).is_file() and text is None:
                text = Path(args.output).read_text(encoding="utf-8")
            if text is None:
                p.error("draft-scene requires --text or --output pointing to a draft file")
            actor_id = args.actor
            return _dump(save_scene_draft(adapter, relative_path=args.path or "", text=text, actor_id=actor_id, note=args.note))
        if args.command == "diff-scene":
            from .scene_studio import diff_scene_draft
            return _dump(diff_scene_draft(adapter, draft_id=args.draft_id or Path(args.path or "").stem))
        if args.command == "accept-scene":
            from .scene_studio import accept_scene_draft
            return _dump(accept_scene_draft(adapter, draft_id=args.draft_id or Path(args.path or "").stem, author_id=args.author_id, reason=args.note))
        if args.command == "export-manuscript":
            from .manuscript_export import export_manuscript
            return _dump(export_manuscript(adapter, output_dir=args.output))
        if args.command == "workbench-refresh":
            from .scene_studio import write_workbench_projection
            return _dump(write_workbench_projection(adapter))
        if args.command == "record-decision":
            from .author_workbench import record_author_decision_action
            if not args.decision or not args.candidate_hash:
                p.error("record-decision requires --decision and --candidate-hash")
            codes = [x.strip() for x in str(args.reason_codes or "").split(",") if x.strip()]
            return _dump(record_author_decision_action(
                adapter, decision=args.decision, candidate_hash=args.candidate_hash,
                author_id=args.author_id, reason=args.note, reason_codes=codes or None,
                turn_id=args.draft_id, scene_id=args.path, revision_round=args.revision_round,
            ))
        from .playtest_coverage import analyze_playtest_coverage
        state = adapter.store.load_state() or {}
        actor_id = args.actor or next(iter(state.get("actors") or {"player": None}), "player")
        return _dump(analyze_playtest_coverage(state, actor_id=actor_id))
    if not args.project or not args.session:
        p.error("project and session are required for kernel commands")
    store = FileStore(args.root, args.project, args.session, args.branch)
    if args.command == "recover": out = recover_store(store)
    elif args.command == "judge": out = commit_turn(store, json.loads(args.intent))
    elif args.command == "migrate": out = migrate_state_file(args.path or str(store.current_path))
    elif args.command == "project-graph": out = rebuild_projection(store)
    elif args.command == "schema": out = adapter_contract(args.task, provider=args.provider)
    elif args.command == "index-events": out = build_event_index(store)
    elif args.command == "repair-events": out = store.repair_events()
    elif args.command == "compact-events": out = store.compact_events(retain_active=args.retain_active)
    elif args.command == "project-longform": out = project_longform_markdown(store, args.path or args.root)
    elif args.command == "projection-status": out = projection_status(store, args.path or args.root)
    elif args.command == "author-console": out = author_console_report(store, project_root=args.path or args.root)
    else:
        state = store.load_state(); out = replay_events(state, store.read_events())
    return _dump(out)

if __name__ == "__main__": raise SystemExit(main())
