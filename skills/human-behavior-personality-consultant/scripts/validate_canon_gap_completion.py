#!/usr/bin/env python3
"""Validate psychological behavior completion of a fictional canon gap."""
import argparse,json,sys
MODES={"HUMAN_BASELINE","HUMAN_DERIVED","ANTHROPOMORPHIC_ANALOGY","NONHUMAN_MODEL","SYMBOLIC_OR_FLAT","UNKNOWN"}
DIMS={"humanlike","modified","nonhuman","unknown"}
LABELS={"SOURCE_CANON","CANON_UNKNOWN","CANON_CONSTRAINED_INFERENCE","HUMAN_PRIOR","PERFORMANCE_HYPOTHESIS","ADAPTATION_PROPOSAL","AUTHOR_CANON","REFUTED_BY_CANON"}
def filled(x):return x not in (None,"",[],{})
def validate(d):
 e=[];w=[]
 if d.get('schema')!='minis.canon-gap-behavior-completion.v1':e.append('invalid:schema')
 env=d.get('canon_constraint_envelope',{})
 for k in ('character_instance','continuity','scene_time','source_state_hash','known_facts','observed_behavior_anchors','knowledge_limits','world_and_body_constraints','explicit_unknowns','forbidden_inferences'):
  if not filled(env.get(k)):e.append(f'missing:envelope.{k}')
 if not d.get('research_exhaustion',{}).get('canon_gap_confirmed'):e.append('gate:canon_gap_not_confirmed')
 ma=d.get('mind_architecture',{});mode=ma.get('mode')
 if mode not in MODES:e.append('invalid:mind_architecture.mode')
 for k in ('body','perception','memory','emotion','social_attachment','time','death_loss','agency','language','self_continuity'):
  if ma.get('dimensions',{}).get(k) not in DIMS:e.append(f'missing_or_invalid:mind_dimension.{k}')
 candidates=d.get('candidates',[])
 if len(candidates)<2:e.append('gate:requires_competing_candidates')
 ids=set();has_min=False
 for c in candidates:
  cid=c.get('id');
  if not cid or cid in ids:e.append(f'invalid:candidate_id:{cid}')
  ids.add(cid)
  if c.get('tier')==0:has_min=True
  if c.get('label') not in LABELS:e.append(f'invalid:candidate_label:{cid}')
  for k in ('scene_objective','playable_action','canon_compatibility','mind_compatibility','added_assumption_cost','observable_prediction','falsifier'):
   if not filled(c.get(k)):e.append(f'missing:candidate.{k}:{cid}')
  if c.get('label') in {'HUMAN_PRIOR','PERFORMANCE_HYPOTHESIS','ADAPTATION_PROPOSAL'} and c.get('claims_source_canon'):e.append(f'gate:proposal_claims_source_canon:{cid}')
  if c.get('uses_human_prior'):
   hp=c.get('human_prior',{})
   for k in ('population_context','transferability','world_difference','prediction','failure_condition'):
    if not filled(hp.get(k)):e.append(f'missing:human_prior.{k}:{cid}')
   if mode in {'NONHUMAN_MODEL','UNKNOWN'}:e.append(f'gate:human_prior_not_authorized:{cid}:{mode}')
   if mode=='ANTHROPOMORPHIC_ANALOGY' and not c.get('human_prior',{}).get('textual_function_anchor'):e.append(f'gate:anthropomorphic_prior_needs_anchor:{cid}')
  if c.get('tier')==4 and c.get('label') not in {'ADAPTATION_PROPOSAL','AUTHOR_CANON'}:e.append(f'gate:backstory_wrong_label:{cid}')
 if not has_min:e.append('gate:missing_tier0_minimal_extension')
 sel=d.get('selection',{})
 if sel.get('candidate_id') not in ids:e.append('invalid:selection')
 if not filled(sel.get('reason')):e.append('missing:selection.reason')
 if sel.get('promoted_to_source_canon'):e.append('gate:cannot_promote_to_source_canon')
 if sel.get('status')=='AUTHOR_CANON' and not sel.get('author_approved'):e.append('gate:author_canon_requires_approval')
 lab=d.get('scene_lab',[]);tested={x.get('candidate_id') for x in lab if x.get('result') in {'pass','revise','fail'}}
 if len(tested)<min(2,len(candidates)):e.append('gate:scene_lab_requires_top_two')
 for x in lab:
  for k in ('candidate_id','sample_id','playable_action_test','interchangeability_test','counterexample_test','consequence_test','result'):
   if not filled(x.get(k)):e.append(f'missing:scene_lab.{k}:{x.get("candidate_id")}')
 for x in d.get('canon_conflict_check',[]):
  if x.get('status')=='conflict' and sel.get('status')=='AUTHOR_CANON' and not sel.get('adaptation_divergence_recorded'):e.append('gate:canon_conflict_without_divergence')
 return e,w
def main():
 a=argparse.ArgumentParser();a.add_argument('file');z=a.parse_args();d=json.load(open(z.file));e,w=validate(d);print(json.dumps({'valid':not e,'errors':e,'warnings':w},ensure_ascii=False,indent=2));return 1 if e else 0
if __name__=='__main__':sys.exit(main())
