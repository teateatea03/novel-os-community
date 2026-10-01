#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from novel_judge import (  # noqa: E402
    FileStore, calibrate_random_event_pool, load_random_event_settings,
    request_random_suggestion, set_random_event_mode, validate_random_event_pool,
)

DEFAULT_POOL = HERE.parent / "references" / "random-event-starter-pool.json"


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Novel OS non-canonical random-event suggestion control")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("status", "mode", "suggest", "validate-pool", "calibrate"):
        x = sub.add_parser(name)
        if name not in {"validate-pool"}: 
            x.add_argument("root"); x.add_argument("project"); x.add_argument("session"); x.add_argument("--branch", default="main"); x.add_argument("--namespace", default="interactive")
        if name == "mode": x.add_argument("value", choices=["off", "on-suggestion"]); x.add_argument("--changed-by", choices=["user", "author"], default="user")
        if name in {"suggest", "validate-pool", "calibrate"}: x.add_argument("--pool", default=str(DEFAULT_POOL))
        if name in {"suggest", "calibrate"}: x.add_argument("--trigger", required=True); x.add_argument("--window"); x.add_argument("--seed", default="0")
        if name == "suggest": x.add_argument("--expected-state-hash")
        if name == "calibrate": x.add_argument("--seeds", type=int, default=1000)
    args = p.parse_args(argv)
    if args.command == "validate-pool": out = validate_random_event_pool(load_json(args.pool))
    else:
        store = FileStore(args.root, args.project, args.session, args.branch, namespace=args.namespace)
        if args.command == "status": out = load_random_event_settings(store)
        elif args.command == "mode": out = set_random_event_mode(store, args.value, changed_by=args.changed_by)
        elif args.command == "suggest": out = request_random_suggestion(store, load_json(args.pool), trigger=args.trigger, seed=args.seed, window=load_json(args.window) if args.window else {}, expected_state_hash=args.expected_state_hash)
        else: out = calibrate_random_event_pool(store.load_state(), load_json(args.pool), trigger=args.trigger, seeds=args.seeds, window=load_json(args.window) if args.window else {})
    print(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
