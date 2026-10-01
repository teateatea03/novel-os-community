#!/usr/bin/env python3
"""Check a model capability report against the Luna Novel OS baseline."""
import argparse, json
from pathlib import Path
REQUIRED=['text_exact','structured_json','scene_manifest','fact_anchored_local_repair','isolated_luna_blind_read','host_state_validate','host_graph_validate','host_reality_engine']
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--report',required=True); ap.add_argument('--out'); a=ap.parse_args()
 d=json.loads(Path(a.report).read_text()); p=d.get('probes',{}); findings=[]
 for k in REQUIRED:
  if not p.get(k,{}).get('passed'): findings.append({'code':'BASELINE_PROBE_FAIL','probe':k})
 if p.get('naked_prose',{}).get('passed') is False and not p.get('fact_anchored_local_repair',{}).get('passed'):
  findings.append({'code':'NO_SCAFFOLDED_PROSE_RECOVERY'})
 result={'ok':not findings,'baseline':'novel-os-candidate-baseline-v1','model':d.get('active_model'),'model_level':d.get('model_level'),'host_managed_level':d.get('host_managed_level'),'findings':findings,'tool_authority':'host-only unless native tool artifact separately verified'}
 raw=json.dumps(result,ensure_ascii=False,indent=2); print(raw)
 if a.out: Path(a.out).write_text(raw+'\n')
 raise SystemExit(0 if result['ok'] else 2)
if __name__=='__main__': main()
