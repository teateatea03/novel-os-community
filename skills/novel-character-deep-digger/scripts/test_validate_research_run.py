#!/usr/bin/env python3
import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('validate_research_run.py')
def dumpj(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def dumpjl(p,xs): p.write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in xs)+'\n',encoding='utf-8')
def chain(events,protocol_hash):
 prev='0'*64
 for x in events:
  x['protocol_hash']=protocol_hash
  x['prev_hash']=prev
  raw=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(); x['event_hash']=hashlib.sha256(raw).hexdigest(); prev=x['event_hash']
 return events
def base(root,depth='R2'):
 q={'id':'Q1','text':'身份？','priority':'P0','decision_use':'版本','candidate_answers':['H1','UNKNOWN'],'required_source_roles':['primary'],'negative_evidence_expectation':'官方名冊應出現'}
 plans=[{'id':'SP1','question_ids':['Q1'],'surface':'official','method':'query','priority':'must','expected_yield':'身份'},{'id':'SP2','question_ids':['Q1'],'surface':'adjacent','method':'pivot','priority':'must','expected_yield':'關係'},{'id':'SP3','question_ids':['Q1'],'surface':'news','method':'query','priority':'must','expected_yield':'同期'}]
 p={'schema':'minis.character-research-run.v2','run_id':'r1','subject':{'label':'甲','category':'real','identity_keys':['id1']},'depth':depth,'started_at':'2026-08-19T00:00:00Z','questions':[q],'identity_resolution':{'aliases':['甲'],'language_variants':['zh'],'disambiguators':['作品'],'excluded_homonyms':[],'identity_keys':['id1']},'source_plan':plans,'benchmark_items':[{'id':'B1','question_ids':['Q1'],'locator':'known','holdout':True}],'risks':{'subject_harm':'low','investigator_risk':'low','sensitive_data':[],'mitigations':[]},'stop_policy':{'min_distinct_routes':3,'no_new_family_window':3,'p0_must_close':True}}
 dumpj(root/'protocol.json',p)
 ev=[]
 for i,(pid,typ,plat,qry) in enumerate([('SP1','QUERY','Google','甲 官方'),('SP2','PIVOT','Registry','id1'),('SP3','QUERY','News','甲 作品')],1):
  ev.append({'event_id':f'E{i}','type':typ,'question_ids':['Q1'],'plan_id':pid,'started_at':f'2026-08-19T00:0{i}:00Z','ended_at':f'2026-08-19T00:0{i}:01Z','actor':'agent','platform':plat,'input':{'exact_query':qry,'filters':{}},'result':{'status':'success','raw_hit_count':1,'new_candidate_ids':['K1'] if i==1 else [],'new_source_family_ids':[],'benchmark_ids_found':['B1'] if i==1 else []},'tool':{'name':'browser','version':'1'}})
 dumpjl(root/'events.jsonl',chain(ev,hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()))
 dumpjl(root/'candidates.jsonl',[{'candidate_id':'K1','discovered_by':'E1','canonical_locator':'https://e','title':'t','creator':'c','published_at':'2020','source_role':'primary','source_family_hint':'SF1','disposition':'include','reason_code':'answers_question','screened_by':'agent','screened_at':'2026'}])
 h='a'*64
 dumpjl(root/'artifacts.jsonl',[{'artifact_id':'A1','candidate_id':'K1','kind':'web','raw_or_derived':'raw','canonical_url':'https://e','retrieved_at':'2026','sha256':h,'locator':'para 1','source_family_id':'SF1'}])
 dumpjl(root/'claims.jsonl',[{'claim_id':'C1','question_id':'Q1','text':'甲是本人','claim_type':'fact','status':'SUPPORTED','hypotheses':[{'id':'H1','fit':'supports'}],'evidence':[{'artifact_id':'A1','locator':'para 1','mode':'direct','source_family_id':'SF1','weight_reason':'official'}],'counterevidence':[],'conflict_resolution':'none','sensitivity':'移除此來源則降級','required_before_story_use':False}])
 rev=[{'review_id':'R1','checkpoint':'START_CHALLENGE','reviewer':'devil','performed_at':'2026','claim_ids':[]},{'review_id':'R2','checkpoint':'MIDPOINT_REVIEW','reviewer':'editor','performed_at':'2026','claim_ids':[]},{'review_id':'R3','checkpoint':'CLAIM_AUDIT','reviewer':'blind','performed_at':'2026','claim_ids':['C1']}]
 dumpjl(root/'reviews.jsonl',rev)
def run(root):
 r=subprocess.run(['python3',str(SCRIPT),str(root)],capture_output=True,text=True); return r.returncode,json.loads(r.stdout)
class T(unittest.TestCase):
 def mk(self): return Path(tempfile.mkdtemp())
 def test_complete_passes(self):
  x=self.mk();base(x);c,o=run(x);self.assertEqual(c,0,o)
 def test_false_complete_v1_shape_fails(self):
  x=self.mk();base(x); dumpjl(x/'events.jsonl',[]); c,o=run(x);self.assertEqual(c,1);self.assertTrue(any('must_route' in z or 'checkpoint' in z for z in o['errors']))
 def test_broken_chain_fails(self):
  x=self.mk();base(x); es=[json.loads(z) for z in (x/'events.jsonl').read_text().splitlines()];es[0]['input']['exact_query']='tampered';dumpjl(x/'events.jsonl',es);c,o=run(x);self.assertIn('broken:event_hash:E1',o['errors'])
 def test_p0_missing_claim_fails(self):
  x=self.mk();base(x);dumpjl(x/'claims.jsonl',[]);c,o=run(x);self.assertIn('gate:P0_without_claim:Q1',o['errors'])
 def test_same_family_not_independent(self):
  x=self.mk();base(x); cs=[json.loads(z) for z in (x/'claims.jsonl').read_text().splitlines()];cs[0]['requires_independent_review']=True;cs[0]['evidence'].append(dict(cs[0]['evidence'][0]));dumpjl(x/'claims.jsonl',cs);c,o=run(x);self.assertIn('gate:independent_sources_missing:C1',o['errors'])
 def test_derived_without_lineage_fails(self):
  x=self.mk();base(x); a=[json.loads(z) for z in (x/'artifacts.jsonl').read_text().splitlines()][0];a['raw_or_derived']='derived';dumpjl(x/'artifacts.jsonl',[a]);c,o=run(x);self.assertTrue(any('missing:derived_' in z for z in o['errors']))
 def test_protocol_rewrite_breaks_binding(self):
  x=self.mk();base(x); p=json.loads((x/'protocol.json').read_text());p['questions'][0]['text']='事後改題';dumpj(x/'protocol.json',p);c,o=run(x);self.assertTrue(any('event_protocol_binding' in z for z in o['errors']))
 def test_near_duplicate_queries_not_three_routes(self):
  x=self.mk();base(x); es=[json.loads(z) for z in (x/'events.jsonl').read_text().splitlines()]
  for i,z in enumerate(es): z['plan_id']='SP1';z['type']='QUERY';z['platform']='Google';z['input']['exact_query']=['甲 音樂','甲 專業音樂','甲 著名音樂'][i]
  dumpjl(x/'events.jsonl',chain(es,hashlib.sha256((x/'protocol.json').read_bytes()).hexdigest()));c,o=run(x);self.assertTrue(any('must_route_not_executed' in z or 'insufficient_distinct_routes' in z for z in o['errors']))
if __name__=='__main__':unittest.main()
