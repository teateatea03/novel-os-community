#!/usr/bin/env python3
import argparse, json, subprocess, tempfile, shutil
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--cases"); ap.add_argument("--script-root")
    a=ap.parse_args(); here=Path(__file__).resolve().parent; skill=Path(a.script_root).resolve() if a.script_root else here.parent
    cases=Path(a.cases).resolve() if a.cases else skill/"benchmarks"/"cases"; results=[]
    for case in sorted(p for p in cases.iterdir() if p.is_dir()):
        expected=json.loads((case/"expected.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"project"; shutil.copytree(case/"project",root); (root/"gates").mkdir(exist_ok=True)
            chapter=expected.get("chapter")
            cmd=["python3",str(skill/"scripts"/"deep_consistency.py"),"--root",str(root)]
            if chapter: cmd += ["--chapter",chapter]
            r=subprocess.run(cmd,text=True,capture_output=True)
            if r.returncode:
                results.append({"case":case.name,"pass":False,"error":r.stderr.strip()}); continue
            report=json.loads((root/"gates"/f"deep-{chapter or 'project'}.json").read_text(encoding="utf-8"))
            blobs=[json.dumps(i,ensure_ascii=False) for i in report.get("issues",[])]
            missing=[]
            for want in expected.get("issues",[]):
                if not any(want.get("category") in b and all(k in b for k in want.get("keywords",[])) for b in blobs): missing.append(want)
            ok=report.get("result")==expected.get("result") and not missing
            results.append({"case":case.name,"pass":ok,"result":report.get("result"),"missing":missing,"issue_count":len(blobs)})
    summary={"schema":"minis.novel-regression.v1","passed":sum(x["pass"] for x in results),"total":len(results),"results":results}
    print(json.dumps(summary,ensure_ascii=False,indent=2)); raise SystemExit(0 if summary["passed"]==summary["total"] else 1)
if __name__=="__main__": main()
