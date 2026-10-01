#!/usr/bin/env python3
"""Small local helper for immersive-interactive-fiction state files.
No external dependencies. It validates required continuity fields, creates
checkpoint copies, and appends a concise turn log. YAML is JSON-compatible by
convention so Python's json module can preserve deterministic state files.
"""
from __future__ import annotations
import argparse, datetime as dt, json, shutil, sys
from pathlib import Path

REQUIRED_TOP = {"session", "world", "player", "npcs", "threads", "knowledge_ledger", "events"}

def read_state(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise SystemExit(f"ERROR invalid JSON-compatible state: {e}")

def validate(data):
    errors=[]; warnings=[]
    missing=REQUIRED_TOP-set(data)
    if missing: errors.append("missing top-level keys: "+", ".join(sorted(missing)))
    for k in ("session","world","player","npcs","threads","knowledge_ledger"):
        if k in data and not isinstance(data[k], dict): errors.append(f"{k} must be an object")
    if "events" in data and not isinstance(data["events"], list): errors.append("events must be a list")
    if isinstance(data.get("session"),dict):
        for k in ("id","mode","player_character","turn"):
            if k not in data["session"]: warnings.append(f"session.{k} absent")
    if isinstance(data.get("world"),dict):
        for k in ("now","location","objects","pressures"):
            if k not in data["world"]: warnings.append(f"world.{k} absent")
    for i,npc in enumerate(data.get("npcs",{}).get("characters",[]) if isinstance(data.get("npcs"),dict) else []):
        if not all(k in npc for k in ("id","immediate_goal","knowledge")):
            warnings.append(f"npcs.characters[{i}] lacks id/immediate_goal/knowledge")
    return errors,warnings

def cmd_validate(args):
    data=read_state(Path(args.state)); e,w=validate(data)
    print(json.dumps({"ok":not e,"errors":e,"warnings":w},ensure_ascii=False,indent=2))
    raise SystemExit(1 if e else 0)

def cmd_checkpoint(args):
    root=Path(args.root); state=root/"state/current.json"; data=read_state(state)
    e,w=validate(data)
    if e: raise SystemExit("Refusing checkpoint:\n"+"\n".join(e))
    turn=int(data.get("session",{}).get("turn",0)); name=args.name or f"checkpoint-{turn:04d}"
    dest=root/"state/checkpoints"/f"{name}.json"; dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists() and not args.force: raise SystemExit(f"Exists: {dest}; use --force")
    shutil.copy2(state,dest); print(dest)

def cmd_log(args):
    root=Path(args.root); state=root/"state/current.json"; data=read_state(state)
    turn=int(data.get("session",{}).get("turn",0)); now=dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M")
    log=root/"logs/turns.md"; log.parent.mkdir(parents=True,exist_ok=True)
    with log.open("a",encoding="utf-8") as f:
        f.write(f"\n## T{turn:04d} — {now}\n- 玩家輸入：{args.player}\n- 可見結果：{args.result}\n- 狀態差異：{args.delta}\n- 延遲後果：{args.delayed}\n")
    print(log)

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(required=True)
    x=sub.add_parser("validate"); x.add_argument("--state",required=True); x.set_defaults(func=cmd_validate)
    x=sub.add_parser("checkpoint"); x.add_argument("--root",required=True); x.add_argument("--name"); x.add_argument("--force",action="store_true"); x.set_defaults(func=cmd_checkpoint)
    x=sub.add_parser("log"); x.add_argument("--root",required=True); x.add_argument("--player",required=True); x.add_argument("--result",required=True); x.add_argument("--delta",default="無"); x.add_argument("--delayed",default="無"); x.set_defaults(func=cmd_log)
    args=p.parse_args(); args.func(args)
if __name__=="__main__": main()
