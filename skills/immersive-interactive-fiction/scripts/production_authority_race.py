#!/usr/bin/env python3
from __future__ import annotations

import json, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent; PACKAGE_ROOT=str(HERE)
sys.path.insert(0,PACKAGE_ROOT)
from novel_judge import ProjectRuntimeAdapter, empty_state
from novel_judge.canonical import refresh_state_hash

WORKER=r'''
import json,sys
sys.path.insert(0,sys.argv[1])
from novel_judge import ProjectRuntimeAdapter,make_gate_envelope
a=ProjectRuntimeAdapter(sys.argv[2],"step1-race","session")
try:
 turn=sys.argv[4]; expected=sys.argv[3]; scene=__import__('hashlib').sha256(("scene:"+turn).encode()).hexdigest()
 envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene,source_state_hash=expected) for g in a.gate_policy()["required_gate_types"]]
 a.approve_gate_bundle(turn_id=turn,scene_sha256=scene,source_state_hash=expected,envelopes=envs)
 r=a.commit(turn_id=turn,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=expected,scene_sha256=scene)
 print(json.dumps({"kind":"ok","state_hash":r["post_state_hash"]}))
except Exception as e:
 print(json.dumps({"kind":"error","type":type(e).__name__,"message":str(e)}))
'''

def main():
 with tempfile.TemporaryDirectory(prefix='step1-production-race-') as root:
  a=ProjectRuntimeAdapter(root,'step1-race','session'); s=empty_state('step1-race','session'); s['canon_scope']='experiment'; s['actors']={'world':{'kind':'world','location':'fixture','status':{},'commitments':[]}}; s['world_truth']['locations']={'fixture':{'connections':{}}}; s=refresh_state_hash(s)
  a.initialize(s,baseline_id='baseline',provenance={'shadow':True,'test':'race'},migration_authorized=True)
  ps=[subprocess.Popen([sys.executable,'-c',WORKER,PACKAGE_ROOT,root,s['state_hash'],f'R000{n}'],stdout=subprocess.PIPE,text=True) for n in (1,2)]
  results=[json.loads(p.communicate(timeout=30)[0]) for p in ps]; conf=a.assert_conformant(); report={'schema':'minis.production-authority-race-report.v1','results':results,'successes':sum(x['kind']=='ok' for x in results),'stale_rejects':sum('stale' in x.get('message','') for x in results),'event_count':len(a.store.read_events()),'conformance':conf['status']}; report['ok']=report['successes']==1 and report['stale_rejects']==1 and report['event_count']==1 and report['conformance']=='pass'; print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if report['ok'] else 1
if __name__=='__main__': raise SystemExit(main())
