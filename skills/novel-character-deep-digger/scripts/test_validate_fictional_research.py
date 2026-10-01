#!/usr/bin/env python3
import json,tempfile,subprocess,unittest
from pathlib import Path
S=Path(__file__).with_name('validate_fictional_research.py')
def wr(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def jl(p,x):p.write_text('\n'.join(json.dumps(z,ensure_ascii=False) for z in x)+'\n')
def base(r,cross=False):
 prim=['c1','c2'] if cross else ['c1']; ws=[]
 for i,c in enumerate(prim,1):ws.append({'witness_id':f'W{i}','work_id':f'work{i}','expression_id':f'exp{i}','manifestation_id':f'man{i}','instance_id':f'item{i}','medium':'anime','title':f'v{i}','creator_roles':[{'name':'x','role':'director'}],'language':'ja','publication_or_release':'2020','platform':'disc','region':'JP','edition_cut_build_patch':'v1','continuity_id':c,'canon_authority':'primary_text','access_mode':'owned','completeness':'complete'})
 p={'schema':'minis.character-research-run.v2','subject':{'category':'anime'},'fictional_scope':{'target_character_instance':'char:x','primary_continuity_ids':prim,'excluded_continuity_ids':['cx'],'allowed_relation_types':['SAME_CONTINUITY'],'languages':['ja'],'translation_policy':'source first','spoiler_boundary':'all','rights_access_boundary':'owned'},'witnesses':ws,'canon_matrix':[]};wr(r/'protocol.json',p)
 c={'claim_id':'C1','claim_type':'behavior','canon_status':'TEXT_CANON','narrative_level':'diegetic_fact','version_portability':'CROSS_VERSION_STABLE' if cross else 'SINGLE_WITNESS','witness_ids':[x['witness_id'] for x in ws],'continuity_ids':prim}
 jl(r/'claims.jsonl',[c]);jl(r/'reviews.jsonl',[{'checkpoint':'VERSION_CONTRADICTION_AUDIT'}] if cross else [])
def run(r):
 x=subprocess.run(['python3',str(S),str(r)],capture_output=True,text=True);return x.returncode,json.loads(x.stdout)
class T(unittest.TestCase):
 def mk(self):return Path(tempfile.mkdtemp())
 def test_single_version_pass(self):r=self.mk();base(r);c,o=run(r);self.assertEqual(c,0,o)
 def test_cross_version_pass(self):r=self.mk();base(r,True);c,o=run(r);self.assertEqual(c,0,o)
 def test_summary_cannot_prove_behavior(self):
  r=self.mk();base(r);p=json.loads((r/'protocol.json').read_text());p['witnesses'][0]['completeness']='summary_only';p['witnesses'][0]['canon_authority']='official_paratext';wr(r/'protocol.json',p);c,o=run(r);self.assertTrue(any('behavior_requires' in z or 'text_canon_without' in z for z in o['errors']))
 def test_version_pollution_fails(self):
  r=self.mk();base(r,True);cs=[json.loads(z) for z in (r/'claims.jsonl').read_text().splitlines()];cs[0]['witness_ids']=['W1'];jl(r/'claims.jsonl',cs);c,o=run(r);self.assertTrue(any('stable_claim_missing_primary_witness' in z for z in o['errors']))
 def test_excluded_continuity_fails(self):
  r=self.mk();base(r);cs=[json.loads(z) for z in (r/'claims.jsonl').read_text().splitlines()];cs[0]['continuity_ids']=['c1','cx'];jl(r/'claims.jsonl',cs);c,o=run(r);self.assertIn('gate:excluded_continuity_used:C1',o['errors'])
 def test_missing_contradiction_audit_fails(self):
  r=self.mk();base(r,True);jl(r/'reviews.jsonl',[]);c,o=run(r);self.assertIn('gate:missing_VERSION_CONTRADICTION_AUDIT',o['errors'])
if __name__=='__main__':unittest.main()
