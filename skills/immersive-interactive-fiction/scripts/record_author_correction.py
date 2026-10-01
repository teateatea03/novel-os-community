#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from novel_judge.author_corrections import (  # noqa: E402
    ACTIONS,
    append_correction,
    project_quality_dir,
    read_corrections,
    recommend_action,
    active_guards,
    render_preflight_notes,
)


def _load_card(args: argparse.Namespace) -> dict:
    if args.file:
        return json.loads(Path(args.file).read_text(encoding="utf-8"))
    card = {
        "title": args.title,
        "rule": args.rule,
        "if_condition": args.if_condition,
        "must_not": args.must_not,
        "should": args.should,
        "reason_codes": args.reason_codes or [],
        "character_id": args.character_id,
        "turn_id": args.turn_id,
        "scene_id": args.scene_id,
        "bad_excerpt": args.bad_excerpt,
        "accepted_excerpt": args.accepted_excerpt,
        "status": args.status,
        "recurrence": args.recurrence,
        "one_off": args.one_off,
        "machine_checkable": args.machine_checkable,
        "applies_when": {},
        "promotion_target": args.promotion_target,
        "author_id": args.author_id,
        "feedback_event_id": args.feedback_event_id,
    }
    if args.character_id:
        card["applies_when"]["character_id"] = args.character_id
    if args.scene_kind:
        card["applies_when"]["scene_kind"] = args.scene_kind
    if args.recommended_action:
        card["recommended_action"] = args.recommended_action
    return {k: v for k, v in card.items() if v not in (None, [], {})}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Record non-canonical author-correction cards")
    sub = p.add_subparsers(dest="command", required=True)

    rec = sub.add_parser("record", help="append a note or promoted card")
    rec.add_argument("project_root")
    rec.add_argument("--file", help="JSON card payload")
    rec.add_argument("--title")
    rec.add_argument("--rule")
    rec.add_argument("--if-condition")
    rec.add_argument("--must-not")
    rec.add_argument("--should")
    rec.add_argument("--reason-codes", nargs="*")
    rec.add_argument("--character-id")
    rec.add_argument("--turn-id")
    rec.add_argument("--scene-id")
    rec.add_argument("--scene-kind")
    rec.add_argument("--bad-excerpt")
    rec.add_argument("--accepted-excerpt")
    rec.add_argument("--status", default="note", choices=["note", "promoted", "rejected", "superseded"])
    rec.add_argument("--recommended-action", choices=sorted(ACTIONS))
    rec.add_argument("--recurrence", type=int, default=1)
    rec.add_argument("--one-off", action="store_true")
    rec.add_argument("--machine-checkable", action="store_true")
    rec.add_argument("--promotion-target")
    rec.add_argument("--author-id", default="project-author")
    rec.add_argument("--feedback-event-id")

    recm = sub.add_parser("recommend", help="print recommended promotion action")
    recm.add_argument("project_root", nargs="?")
    recm.add_argument("--file", required=True)

    lst = sub.add_parser("list", help="list correction cards")
    lst.add_argument("project_root")
    lst.add_argument("--status")
    lst.add_argument("--character-id")

    pre = sub.add_parser("preflight", help="render promoted guards for a character/scene")
    pre.add_argument("project_root")
    pre.add_argument("--character-id")
    pre.add_argument("--scene-kind")

    args = p.parse_args(argv)
    if args.command == "record":
        card = _load_card(args)
        if not card.get("title") or not card.get("rule"):
            raise SystemExit("record requires --title and --rule, or --file")
        out = append_correction(args.project_root, card)
        out["_quality_dir"] = str(project_quality_dir(args.project_root))
    elif args.command == "recommend":
        card = json.loads(Path(args.file).read_text(encoding="utf-8"))
        out = {"recommended_action": recommend_action(card), "input": card}
    elif args.command == "list":
        rows = read_corrections(args.project_root)
        if args.status:
            rows = [x for x in rows if x.get("status") == args.status]
        if args.character_id:
            rows = [x for x in rows if x.get("character_id") == args.character_id]
        out = {"count": len(rows), "quality_dir": str(project_quality_dir(args.project_root)), "events": rows}
    else:
        cards = active_guards(args.project_root, character_id=args.character_id, scene_kind=args.scene_kind)
        out = {"count": len(cards), "notes": render_preflight_notes(cards), "events": cards}
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
