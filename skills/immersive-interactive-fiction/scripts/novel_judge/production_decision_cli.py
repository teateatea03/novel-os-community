#!/usr/bin/env python3
from __future__ import annotations

"""Record explicit AUTHOR_DECISION events for any production project.

Examples:
  python3 -m novel_judge.production_decision_cli \
    --root /path/to/project --project-id X --session-id S \
    --decision accept --candidate-hash sha256:... --turn T0255 \
    --reason-codes continuity,character_voice --reason 'ok'
"""

import argparse
import json
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Record explicit author decisions into production feedback ledger")
    ap.add_argument("--root", required=True)
    ap.add_argument("--project-id", required=True)
    ap.add_argument("--session-id", required=True)
    ap.add_argument("--branch-id", default="main")
    ap.add_argument("--decision", required=True, choices=["accept", "revise", "reject"])
    ap.add_argument("--candidate-hash", required=True)
    ap.add_argument("--turn")
    ap.add_argument("--scene-id")
    ap.add_argument("--author-id", default="author")
    ap.add_argument("--reason-codes", default="")
    ap.add_argument("--reason")
    ap.add_argument("--revision-round", type=int)
    ap.add_argument("--confidence", default="high", choices=["high", "medium", "low"])
    ap.add_argument("--reluctant", action="store_true")
    ap.add_argument("--source-state-hash", help="defaults to current production state hash")
    args = ap.parse_args(argv)

    # Ensure package import when executed as a file.
    here = Path(__file__).resolve().parent.parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    from novel_judge.production import ProjectRuntimeAdapter
    from novel_judge.author_decision import record_author_decision
    from novel_judge.author_feedback import feedback_status

    adapter = ProjectRuntimeAdapter(args.root, args.project_id, args.session_id, args.branch_id)
    state = adapter.store.load_state() or {}
    source_state_hash = args.source_state_hash or state.get("state_hash")
    if not source_state_hash:
        raise SystemExit("no source state hash available")
    codes = [x.strip() for x in args.reason_codes.split(",") if x.strip()]
    report = record_author_decision(
        adapter.store,
        decision=args.decision,
        author_id=args.author_id,
        candidate_hash=args.candidate_hash,
        source_state_hash=source_state_hash,
        source_event_head=state.get("events_head"),
        turn_id=args.turn,
        scene_id=args.scene_id or args.turn,
        reason_codes=codes,
        reason=args.reason,
        revision_round=args.revision_round,
        confidence=args.confidence,
        reluctant_accept=args.reluctant,
        provenance={"source": "production_decision_cli"},
    )
    status = feedback_status(adapter.store)
    print(
        json.dumps(
            {
                "ok": True,
                "event_id": report["event"]["event_id"],
                "decision": args.decision,
                "explicit_count": status.get("explicit_count"),
                "event_count": status.get("event_count"),
                "authority_layer": "AUTHOR_DECISION",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
