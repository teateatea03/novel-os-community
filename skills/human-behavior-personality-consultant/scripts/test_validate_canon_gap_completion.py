#!/usr/bin/env python3
import json,tempfile,subprocess,unittest
from pathlib import Path
S=Path(__file__).with_name('validate_canon_gap_completion.py')
def base(mode='HUMAN_BASELINE'):
 dims={k:'humanlike' for k in ['body','perception','memory','emotion','social_attachment','time','death_loss','agency','language','self_continuity']}
 def c(i,t,label='CANON_CONSTRAINED_INFERENCE'):
  return {'id':i,'tier':t,'label':label,'scene_objective':'讓對方交出資訊','playable_action':'試探','canon_compatibility':'pass','mind_compatibility':'pass','added_assumption_cost':'low','observable_prediction':'先問來源','falsifier':'直接無條件相信','claims_source_canon':False,'uses_human_prior':False}
 cs=[c('A',0),c('B',1,'PERFORMANCE_HYPOTHESIS')]
 return {'schema':'minis.canon-gap-behavior-completion.v1','canon_constraint_envelope':{'character_instance':'x','continuity':'c','scene_time':'t','source_state_hash':'h','known_facts':['f'],'observed_behavior_anchors':['b'],'known_voice_constraints':['v'],'knowledge_limits':['k'],'relationship_state':['r'],'world_and_body_constraints':['w'],'explicit_unknowns':['u'],'forbidden_inferences':['no trauma'],'future_continuity_constraints':['f']},'research_exhaustion':{'canon_gap_confirmed':True},'mind_architecture':{'mode':mode,'dimensions':dims},'candidates':cs,'selection':{'candidate_id':'A','reason':'least assumption','status':'SCENE_TESTED_PROPOSAL','author_approved':False,'promoted_to_source_canon':False},'scene_lab':[{'candidate_id':i,'sample_id':'s'+i,'playable_action_test':'pass','interchangeability_test':'pass','counterexample_test':'pass','consequence_test':'pass','result':'pass'} for i in ['A','B']],'canon_conflict_check':[]}
def run(d):
 p=Path(tempfile.mktemp(suffix='.json'));p.write_text(json.dumps(d));r=subprocess.run(['python3',str(S),str(p)],capture_output=True,text=True);p.unlink();return r.returncode,json.loads(r.stdout)
class T(unittest.TestCase):
 def test_valid_human_gap(self):c,o=run(base());self.assertEqual(c,0,o)
 def test_unconfirmed_gap_fails(self):d=base();d['research_exhaustion']['canon_gap_confirmed']=False;c,o=run(d);self.assertIn('gate:canon_gap_not_confirmed',o['errors'])
 def test_proposal_cannot_claim_canon(self):d=base();d['candidates'][1]['claims_source_canon']=True;c,o=run(d);self.assertTrue(any('proposal_claims' in x for x in o['errors']))
 def test_nonhuman_rejects_human_prior(self):
  d=base('NONHUMAN_MODEL');d['candidates'][1].update({'uses_human_prior':True,'label':'HUMAN_PRIOR','human_prior':{'population_context':'humans','transferability':'low','world_difference':'major','prediction':'withdraw','failure_condition':'nonhuman'}});c,o=run(d);self.assertTrue(any('human_prior_not_authorized' in x for x in o['errors']))
 def test_backstory_needs_proposal_label(self):d=base();d['candidates'][1]['tier']=4;d['candidates'][1]['label']='CANON_CONSTRAINED_INFERENCE';c,o=run(d);self.assertTrue(any('backstory_wrong_label' in x for x in o['errors']))
 def test_author_canon_needs_approval(self):d=base();d['selection']['status']='AUTHOR_CANON';c,o=run(d);self.assertIn('gate:author_canon_requires_approval',o['errors'])
 def test_scene_lab_required(self):d=base();d['scene_lab']=d['scene_lab'][:1];c,o=run(d);self.assertIn('gate:scene_lab_requires_top_two',o['errors'])
 def test_cannot_promote_source_canon(self):d=base();d['selection']['promoted_to_source_canon']=True;c,o=run(d);self.assertIn('gate:cannot_promote_to_source_canon',o['errors'])
if __name__=='__main__':unittest.main()
