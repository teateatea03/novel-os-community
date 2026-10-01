#!/usr/bin/env python3
"""Validate medium/version evidence for non-real character research runs."""
import argparse,json,sys
from pathlib import Path
PRIMARY={"TEXT_CANON","AUTHOR_CANON"}
VALID_CANON=PRIMARY|{"OFFICIAL_PARATEXT","PRODUCTION_WITNESS","ADAPTATION_ONLY","LOCALIZATION_VARIANT","CUT_UNUSED","RECEPTION","FAN_NAVIGATION","PROPOSAL"}
PORT={"SINGLE_WITNESS","SAME_CONTINUITY","CROSS_VERSION_STABLE","CONFLICTING","UNKNOWN"}
LEVELS={"diegetic_fact","narrator_assertion","character_belief","rumor","dream_vision","performance_choice","gameplay_state"}
REL={"SAME_CONTINUITY","PREQUEL_OF","SEQUEL_OF","SIDE_STORY_OF","ADAPTS","EXTENDS","REBOOTS","REMAKES","PARALLEL_TO","LOCALIZES","TRANSLATES","CENSORS_OR_REEDITS","INSPIRED_BY","NON_CANON_PROMOTION","UNKNOWN_RELATION"}
def jl(p):
 if not p.exists(): return []
 return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def validate(root):
 root=Path(root);e=[];w=[]
 try:p=json.loads((root/'protocol.json').read_text()); claims=jl(root/'claims.jsonl'); reviews=jl(root/'reviews.jsonl')
 except Exception as x:return [f'parse:{x}'],w,{}
 if p.get('subject',{}).get('category')=='real': return ['invalid:real_subject_for_fictional_validator'],w,{}
 fs=p.get('fictional_scope')
 if not fs:return ['missing:fictional_scope'],w,{}
 target=fs.get('target_character_instance'); prim=set(fs.get('primary_continuity_ids',[])); excluded=set(fs.get('excluded_continuity_ids',[]))
 if not target:e.append('missing:target_character_instance')
 if not prim:e.append('missing:primary_continuity_ids')
 if prim&excluded:e.append('invalid:continuity_both_primary_and_excluded')
 witnesses={x.get('witness_id'):x for x in p.get('witnesses',[]) if x.get('witness_id')}
 if not witnesses:e.append('missing:witnesses')
 required_w={"work_id","expression_id","manifestation_id","instance_id","medium","title","language","continuity_id","canon_authority","access_mode","completeness"}
 primary_by_cont={c:[] for c in prim}
 for wid,x in witnesses.items():
  for k in required_w:
   if not x.get(k):e.append(f'missing:witness.{k}:{wid}')
  if x.get('continuity_id') in primary_by_cont and x.get('canon_authority')=='primary_text' and x.get('completeness') in {'complete','excerpt'}:primary_by_cont[x['continuity_id']].append(wid)
 matrix=p.get('canon_matrix',[])
 for x in matrix:
  if x.get('relation_type') not in REL:e.append(f"invalid:canon_relation:{x.get('relation_id')}")
  if x.get('from_witness_id') not in witnesses or x.get('to_witness_id') not in witnesses:e.append(f"invalid:canon_relation_witness:{x.get('relation_id')}")
 review_types={r.get('checkpoint') for r in reviews}
 cross=[]; claim_witness_use={}
 for c in claims:
  cid=c.get('claim_id'); cs=c.get('canon_status'); vp=c.get('version_portability'); nl=c.get('narrative_level')
  if cs not in VALID_CANON:e.append(f'invalid:canon_status:{cid}')
  if vp not in PORT:e.append(f'invalid:version_portability:{cid}')
  if nl not in LEVELS:e.append(f'invalid:narrative_level:{cid}')
  ws=set(c.get('witness_ids',[])); cont=set(c.get('continuity_ids',[])); claim_witness_use[cid]=ws
  if not ws:e.append(f'missing:claim_witness_ids:{cid}')
  for z in ws:
   if z not in witnesses:e.append(f'invalid:claim_witness:{cid}:{z}')
  if not cont:e.append(f'missing:claim_continuity_ids:{cid}')
  if cont&excluded:e.append(f'gate:excluded_continuity_used:{cid}')
  if cs in PRIMARY:
   for z in ws:
    wx=witnesses.get(z,{})
    if wx.get('canon_authority')!='primary_text':e.append(f'gate:text_canon_without_primary_witness:{cid}:{z}')
    if wx.get('completeness')=='summary_only':e.append(f'gate:summary_used_as_text_canon:{cid}:{z}')
  if c.get('claim_type') in {'behavior','voice','counterexample','relationship','capability'}:
   if not any(witnesses.get(z,{}).get('canon_authority')=='primary_text' and witnesses.get(z,{}).get('completeness')!='summary_only' for z in ws):e.append(f'gate:behavior_requires_primary_story_witness:{cid}')
  if vp=='CROSS_VERSION_STABLE':
   cross.append(cid)
   if not prim<=cont:e.append(f'gate:stable_claim_missing_continuity:{cid}')
   for pc in prim:
    if not any(witnesses.get(z,{}).get('continuity_id')==pc and witnesses.get(z,{}).get('canon_authority')=='primary_text' and witnesses.get(z,{}).get('completeness')!='summary_only' for z in ws):e.append(f'gate:stable_claim_missing_primary_witness:{cid}:{pc}')
 if cross and 'VERSION_CONTRADICTION_AUDIT' not in review_types:e.append('gate:missing_VERSION_CONTRADICTION_AUDIT')
 if len(prim)>1:
  for pc,ws in primary_by_cont.items():
   if not ws:w.append(f'continuity_without_complete_primary_witness:{pc}')
 metrics={'witnesses':len(witnesses),'primary_continuities':len(prim),'claims':len(claims),'cross_version_stable_claims':len(cross),'canon_relations':len(matrix),'review_types':sorted(x for x in review_types if x)}
 return e,w,metrics
def main():
 a=argparse.ArgumentParser();a.add_argument('run_dir');z=a.parse_args();e,w,m=validate(z.run_dir);print(json.dumps({'valid':not e,'errors':e,'warnings':w,'metrics':m},ensure_ascii=False,indent=2));return 1 if e else 0
if __name__=='__main__':sys.exit(main())
