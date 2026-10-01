#!/usr/bin/env python3
import argparse, json, subprocess
from datetime import datetime
from pathlib import Path

IGNORE="""# 衍生資料，可重建
story-index.json
mention-index.json
context-packs/
gates/
reviews/
cascade-impact.json
snapshots/
__pycache__/
.DS_Store
"""
ATTR="""*.md text eol=lf
*.json text eol=lf
"""

def run(cmd,root,check=True):
    return subprocess.run(cmd,cwd=root,text=True,capture_output=True,check=check)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=["init","status","branch","commit"])
    ap.add_argument("--root",required=True); ap.add_argument("--name")
    ap.add_argument("--message"); ap.add_argument("--chapter")
    ap.add_argument("--override-reason")
    a=ap.parse_args(); root=Path(a.root).resolve()
    if a.command=="init":
        if not (root/".git").exists(): run(["git","init"],root)
        for name,content in ((".gitignore",IGNORE),(".gitattributes",ATTR)):
            p=root/name
            if not p.exists(): p.write_text(content,encoding="utf-8")
        print(root/".git"); return
    if not (root/".git").exists(): raise SystemExit("not a git repository; run init")
    if a.command=="status": print(run(["git","status","--short","--branch"],root).stdout,end=""); return
    if a.command=="branch":
        if not a.name: raise SystemExit("--name required")
        if any(x in a.name for x in (".."," ","~","^",":","?","*","[","\\")): raise SystemExit("unsafe branch name")
        run(["git","switch","-c",a.name],root); print(a.name); return
    if not a.message: raise SystemExit("--message required")
    if a.chapter:
        gate=root/"gates"/f"{a.chapter}-gate.json"
        if not gate.exists(): raise SystemExit("missing gate report for chapter")
        data=json.loads(gate.read_text(encoding="utf-8"))
        blocked=(data.get("result") or data.get("status"))=="FAIL" or any(i.get("severity")=="P0" for i in data.get("issues",[]))
        if blocked and not a.override_reason: raise SystemExit("gate FAIL/P0; provide --override-reason to record author decision")
        if blocked:
            d=root/"decisions.md"
            with d.open("a",encoding="utf-8") as f:
                f.write(f"\n- {datetime.now().astimezone().isoformat(timespec='seconds')} [OVERRIDE] {a.chapter}: {a.override_reason}\n")
    run(["git","add","-A"],root)
    staged=run(["git","diff","--cached","--quiet"],root,check=False)
    if staged.returncode==0: raise SystemExit("nothing to commit")
    run(["git","commit","-m",a.message],root)
    print(run(["git","rev-parse","--short","HEAD"],root).stdout.strip())
if __name__=="__main__": main()
