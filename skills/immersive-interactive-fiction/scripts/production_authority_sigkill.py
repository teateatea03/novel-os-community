#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKAGE_ROOT = str(HERE)
sys.path.insert(0, PACKAGE_ROOT)
from novel_judge import ProjectRuntimeAdapter, empty_state
from novel_judge.canonical import refresh_state_hash

WORKER = r'''
import sys
sys.path.insert(0,sys.argv[1])
from novel_judge import ProjectRuntimeAdapter,make_gate_envelope
a=ProjectRuntimeAdapter(sys.argv[2],"step1-sigkill","session")
turn="kill-"+sys.argv[4]; expected=sys.argv[3]; scene=__import__('hashlib').sha256(("scene:"+turn).encode()).hexdigest()
envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene,source_state_hash=expected) for g in a.gate_policy()["required_gate_types"]]
a.approve_gate_bundle(turn_id=turn,scene_sha256=scene,source_state_hash=expected,envelopes=envs)
a.commit(turn_id=turn,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=expected,scene_sha256=scene)
'''


def initial():
    s=empty_state("step1-sigkill","session"); s["canon_scope"]="experiment"
    s["actors"]={"world":{"kind":"world","location":"fixture","status":{},"commitments":[]}}
    s["world_truth"]["locations"]={"fixture":{"connections":{}}}
    return refresh_state_hash(s)


def main() -> int:
    points=("event_after_append","event_after_active_manifest","event_after_index",
            "production_after_state","production_after_head","production_after_runtime_head",
            "production_after_project_pointer")
    results=[]
    for point in points:
        with tempfile.TemporaryDirectory(prefix="step1-production-kill-") as root:
            a=ProjectRuntimeAdapter(root,"step1-sigkill","session"); state=initial()
            a.initialize(state,baseline_id="baseline",provenance={"shadow":True,"test":point},migration_authorized=True)
            env=os.environ.copy(); env["NOVEL_JUDGE_SIGKILL_AT"]=point
            proc=subprocess.run([sys.executable,"-c",WORKER,PACKAGE_ROOT,root,state["state_hash"],point],env=env)
            recovery=a.recover(); conformance=a.assert_conformant()
            killed=proc.returncode in {-signal.SIGKILL,128+signal.SIGKILL,137}
            ok=killed and conformance["status"]=="pass" and len(a.store.read_events())==1 and a.store.load_journal() is None
            results.append({"point":point,"returncode":proc.returncode,"killed":killed,"recovery":recovery,
                            "event_count":len(a.store.read_events()),"conformance":conformance["status"],
                            "journal_cleared":a.store.load_journal() is None,"ok":ok})
    report={"schema":"minis.production-authority-sigkill-report.v1","ok":all(x["ok"] for x in results),"results":results}
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report["ok"] else 1


if __name__=="__main__": raise SystemExit(main())
