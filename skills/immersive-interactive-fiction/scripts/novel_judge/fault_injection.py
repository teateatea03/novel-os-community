#!/usr/bin/env python3
from __future__ import annotations

"""SIGKILL fault-injection harness for real cross-process commit points."""

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

WORKER = r'''
import os,sys
from novel_judge import FileStore,make_intent,commit_turn
from novel_judge import store as sm
point=sys.argv[2]; root=sys.argv[1]
s=FileStore(root,'kill','s')
orig_append=s.append_event; orig_save=s.save_state; orig_head=s.update_head
if point=='after_event':
 def f(e,**kwargs):
  r=orig_append(e,**kwargs); os.kill(os.getpid(),9); return r
 s.append_event=f
elif point=='after_state':
 def f(st,**kwargs):
  r=orig_save(st,**kwargs); os.kill(os.getpid(),9); return r
 s.save_state=f
elif point=='after_head':
 def f(e,st,**kwargs):
  r=orig_head(e,st,**kwargs); os.kill(os.getpid(),9); return r
 s.update_head=f
commit_turn(s,make_intent('player','wait',turn_id='kill-'+point,parameters={'seconds':1}))
'''


def run_point(point: str) -> dict:
    from novel_judge import FileStore, empty_state, recover_store, replay_events
    with tempfile.TemporaryDirectory(prefix="novel-kill-") as root:
        store = FileStore(root, "kill", "s"); initial = empty_state("kill", "s")
        initial["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []}}
        store.save_state(initial)
        proc = subprocess.run([sys.executable, "-c", WORKER, root, point], env={**os.environ, "PYTHONPATH": str(HERE.parent)})
        killed = proc.returncode in {-signal.SIGKILL, 128 + signal.SIGKILL, 137}
        recovery = recover_store(store); state = store.load_state(); events = store.read_events()
        replayed = replay_events(initial, events)
        return {"point": point, "returncode": proc.returncode, "killed": killed, "recovery": recovery,
                "event_count": len(events), "hash_match": state["state_hash"] == replayed["state_hash"],
                "journal_cleared": store.load_journal() is None}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--points", default="after_event,after_state,after_head"); args = parser.parse_args()
    results = [run_point(x) for x in args.points.split(",") if x]
    ok = all(x["killed"] and x["hash_match"] and x["journal_cleared"] for x in results)
    print(json.dumps({"schema": "minis.sigkill-fault-report.v1", "ok": ok, "results": results}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__": raise SystemExit(main())
