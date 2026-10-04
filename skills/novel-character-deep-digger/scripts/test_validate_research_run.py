#!/usr/bin/env python3
import copy,hashlib,json,subprocess,sys,tempfile,unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('validate_research_run.py')
def dumpj(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def dumpjl(p,xs): p.write_text('\n'.join(json.dumps(x,ensure_ascii=False,sort_keys=True) for x in xs)+'\n',encoding='utf-8')
def chain(events,protocol_hash):
 prev='0'*64
 for x in events:
  x.pop('event_hash',None)
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
 # Synthetic complete run: discovery precedes three genuinely quiet routes.
 # The historical three-event fixture actually has SF1 first appear in-window.
 for i,source in enumerate(list(ev),4):
  quiet=copy.deepcopy(source);quiet['event_id']=f'E{i}'
  quiet['started_at']=f'2026-08-19T00:0{i}:00Z';quiet['ended_at']=f'2026-08-19T00:0{i}:01Z'
  quiet['result'].update(status='zero',raw_hit_count=0,new_candidate_ids=[],benchmark_ids_found=[])
  ev.append(quiet)
 dumpjl(root/'events.jsonl',chain(ev,hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()))
 dumpjl(root/'candidates.jsonl',[{'candidate_id':'K1','discovered_by':'E1','canonical_locator':'https://e','title':'t','creator':'c','published_at':'2020','source_role':'primary','source_family_hint':'SF1','disposition':'include','reason_code':'answers_question','screened_by':'agent','screened_at':'2026'}])
 h='a'*64
 dumpjl(root/'artifacts.jsonl',[{'artifact_id':'A1','candidate_id':'K1','kind':'web','raw_or_derived':'raw','canonical_url':'https://e','retrieved_at':'2026','sha256':h,'locator':'para 1','source_family_id':'SF1'}])
 dumpjl(root/'claims.jsonl',[{'claim_id':'C1','question_id':'Q1','text':'甲是本人','claim_type':'fact','status':'SUPPORTED','hypotheses':[{'id':'H1','fit':'supports'}],'evidence':[{'artifact_id':'A1','locator':'para 1','mode':'direct','source_family_id':'SF1','weight_reason':'official'}],'counterevidence':[],'conflict_resolution':'none','sensitivity':'移除此來源則降級','required_before_story_use':False}])
 rev=[{'review_id':'R1','checkpoint':'START_CHALLENGE','reviewer':'devil','performed_at':'2026','claim_ids':[]},{'review_id':'R2','checkpoint':'MIDPOINT_REVIEW','reviewer':'editor','performed_at':'2026','claim_ids':[]},{'review_id':'R3','checkpoint':'CLAIM_AUDIT','reviewer':'blind','performed_at':'2026','claim_ids':['C1']}]
 dumpjl(root/'reviews.jsonl',rev)
def run(root):
 r=subprocess.run([sys.executable,'-B',str(SCRIPT),str(root)],capture_output=True,text=True); return r.returncode,json.loads(r.stdout)
class T(unittest.TestCase):
 def mk(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);return Path(temp.name)
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
  for i,z in enumerate(es): z['plan_id']='SP1';z['type']='QUERY';z['platform']='Google';z['input']['exact_query']=['甲 音樂','甲 專業音樂','甲 著名音樂'][i % 3]
  dumpjl(x/'events.jsonl',chain(es,hashlib.sha256((x/'protocol.json').read_bytes()).hexdigest()));c,o=run(x);self.assertTrue(any('must_route_not_executed' in z or 'insufficient_distinct_routes' in z for z in o['errors']))
class Integrity(unittest.TestCase):
 def setUp(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
  self.outer=Path(temp.name);self.root=self.outer/'run';self.root.mkdir();base(self.root)
 def rows(self,name):
  return [json.loads(x) for x in (self.root/(name+'.jsonl')).read_text().splitlines() if x.strip()]
 def save(self,name,rows):dumpjl(self.root/(name+'.jsonl'),rows)
 def rechain(self,events=None):
  events=self.rows('events') if events is None else events
  self.save('events',chain(events,hashlib.sha256((self.root/'protocol.json').read_bytes()).hexdigest()))
 def protocol(self,mutate):
  p=json.loads((self.root/'protocol.json').read_text());mutate(p);dumpj(self.root/'protocol.json',p);self.rechain()
 def fail(self,error):
  code,out=run(self.root);self.assertEqual(code,1,out)
  self.assertTrue(any(x.startswith(error) for x in out['errors']),out)
  return out
 def passes(self):
  code,out=run(self.root);self.assertEqual(code,0,out);return out
 def local(self,key='local_path',absolute=False):
  path=self.root/'artifacts'/'raw'/'sample.txt';path.parent.mkdir(parents=True,exist_ok=True)
  path.write_bytes(b'original evidence\n')
  rows=self.rows('artifacts');rows[0].update({key:str(path) if absolute else str(path.relative_to(self.root)), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':path.stat().st_size})
  self.save('artifacts',rows);return path
 def derived(self,parents='A1'):
  rows=self.rows('artifacts');a=copy.deepcopy(rows[0]);a.update(artifact_id='A2',raw_or_derived='derived',derived_from=parents,input_hash=rows[0]['sha256'],output_hash='b'*64,sha256='b'*64,operation='extract',tool={'name':'fixture','version':'1'})
  rows.append(a);self.save('artifacts',rows)
 def test_legacy_no_local_file_warns_not_fails(self):
  self.assertIn('unverified:artifact_file:A1',self.passes()['warnings'])
 def test_relative_local_file_valid(self):
  self.local();self.passes()
 def test_absolute_in_run_file_valid(self):
  self.local(absolute=True);self.passes()
 def test_path_alias_valid(self):
  self.local(key='path');self.passes()
 def test_file_tampering_rejected(self):
  self.local().write_bytes(b'tampered');self.fail('broken:artifact_file_hash:A1')
 def test_missing_local_file_rejected(self):
  self.local().unlink();self.fail('missing:artifact_file:A1')
 def test_wrong_file_size_rejected(self):
  self.local();rows=self.rows('artifacts');rows[0]['size']+=1;self.save('artifacts',rows);self.fail('broken:artifact_file_size:A1')
 def test_directory_not_artifact_file(self):
  self.local();rows=self.rows('artifacts');rows[0]['local_path']='artifacts/raw';self.save('artifacts',rows);self.fail('missing:artifact_file:A1')
 def test_relative_path_escape_rejected(self):
  (self.outer/'outside.txt').write_text('public synthetic fixture')
  rows=self.rows('artifacts');rows[0]['local_path']='../outside.txt';self.save('artifacts',rows);self.fail('invalid:artifact_path_escape:A1')
 def test_absolute_path_escape_rejected(self):
  rows=self.rows('artifacts');rows[0]['local_path']=str(self.outer/'outside.txt');self.save('artifacts',rows);self.fail('invalid:artifact_path_escape:A1')
 def test_symlink_escape_rejected(self):
  (self.outer/'outside.txt').write_text('public synthetic fixture');(self.root/'link').symlink_to(self.outer/'outside.txt')
  rows=self.rows('artifacts');rows[0]['local_path']='link';self.save('artifacts',rows);self.fail('invalid:artifact_path_escape:A1')
 def test_ledger_symlink_escape_rejected(self):
  path=self.root/'claims.jsonl';external=self.outer/'external.jsonl';path.rename(external);path.symlink_to(external)
  self.fail('invalid:ledger_path_escape:claims.jsonl')
 def test_secondary_path_cannot_bypass_validation(self):
  self.local();rows=self.rows('artifacts');rows[0]['path']='../outside';self.save('artifacts',rows);self.fail('invalid:artifact_path_escape:A1')
 def test_content_hash_alias_mismatch(self):
  rows=self.rows('artifacts');rows[0]['content_sha256']='b'*64;self.save('artifacts',rows);self.fail('broken:artifact_content_hash:A1')
 def test_valid_single_parent_lineage(self):
  self.derived();self.passes()
 def test_valid_singleton_list_lineage(self):
  self.derived(['A1']);self.passes()
 def test_legacy_url_lineage_warns_not_fails(self):
  self.derived('https://example.invalid/source');self.assertIn('unverified:derived_parent:A2',self.passes()['warnings'])
 def test_legacy_descriptive_lineage_warns_not_fails(self):
  self.derived('manual transcription source');self.assertIn('unverified:derived_parent:A2',self.passes()['warnings'])
 def test_multi_parent_lineage_hash_limit_explicit(self):
  rows=self.rows('artifacts');a=copy.deepcopy(rows[0]);a['artifact_id']='A3';a['sha256']='c'*64;rows.append(a);self.save('artifacts',rows)
  self.derived(['A1','A3']);self.assertIn('unverified:derived_multi_input_hash:A2',self.passes()['warnings'])
 def test_wrong_derived_input_hash(self):
  self.derived();rows=self.rows('artifacts');rows[1]['input_hash']='c'*64;self.save('artifacts',rows);self.fail('broken:derived_input_hash:A2')
 def test_wrong_derived_output_hash(self):
  self.derived();rows=self.rows('artifacts');rows[1]['output_hash']='c'*64;self.save('artifacts',rows);self.fail('broken:derived_output_hash:A2')
 def test_malformed_derived_hash(self):
  self.derived();rows=self.rows('artifacts');rows[1]['input_hash']='placeholder';self.save('artifacts',rows);self.fail('invalid:derived_input_hash:A2')
 def test_self_referential_lineage(self):
  self.derived('A2');self.fail('broken:derived_cycle:A2')
 def test_two_node_lineage_cycle(self):
  self.derived();rows=self.rows('artifacts');rows[0].update(raw_or_derived='derived',derived_from='A2',input_hash='b'*64,operation='extract',tool='fixture',output_hash='a'*64);self.save('artifacts',rows);self.fail('broken:derived_cycle:')

 def test_duplicate_claim_id(self):
  rows=self.rows('claims');rows.append(copy.deepcopy(rows[0]));self.save('claims',rows);self.fail('invalid:claim_id:C1')
 def test_duplicate_review_id(self):
  rows=self.rows('reviews');rows[1]['review_id']='R1';self.save('reviews',rows);self.fail('invalid:review_id:R1')
 def test_duplicate_question_id(self):
  self.protocol(lambda p:p['questions'].append(copy.deepcopy(p['questions'][0])));self.fail('invalid:questions_id:Q1')
 def test_duplicate_plan_id(self):
  self.protocol(lambda p:p['source_plan'].append(copy.deepcopy(p['source_plan'][0])));self.fail('invalid:source_plan_id:SP1')
 def test_duplicate_benchmark_id(self):
  self.protocol(lambda p:p['benchmark_items'].append(copy.deepcopy(p['benchmark_items'][0])));self.fail('invalid:benchmark_items_id:B1')
 def test_duplicate_event_id(self):
  rows=self.rows('events');rows[1]['event_id']='E1';self.rechain(rows);self.fail('invalid:event_id:E1')
 def test_duplicate_candidate_id(self):
  rows=self.rows('candidates');rows.append(copy.deepcopy(rows[0]));self.save('candidates',rows);self.fail('invalid:candidate_id:K1')
 def test_duplicate_artifact_id(self):
  rows=self.rows('artifacts');rows.append(copy.deepcopy(rows[0]));self.save('artifacts',rows);self.fail('invalid:artifact_id:A1')
 def test_blank_claim_id(self):
  rows=self.rows('claims');rows[0]['claim_id']='   ';self.save('claims',rows);self.fail('invalid:claim_id:')
 def test_missing_review_id(self):
  rows=self.rows('reviews');rows[0].pop('review_id');self.save('reviews',rows);self.fail('invalid:review_id:')
 def test_unknown_claim_evidence_artifact(self):
  rows=self.rows('claims');rows[0]['evidence'][0]['artifact_id']='A404';self.save('claims',rows);self.fail('invalid:claim_artifact:C1:A404')
 def test_unknown_counterevidence_artifact(self):
  rows=self.rows('claims');rows[0]['counterevidence']=[dict(rows[0]['evidence'][0],artifact_id='A404')];self.save('claims',rows);self.fail('invalid:claim_artifact:C1:A404')
 def test_unknown_candidate_in_event(self):
  rows=self.rows('events');rows[0]['result']['new_candidate_ids']=['K404'];self.rechain(rows);self.fail('invalid:event_candidate:E1:K404')
 def test_candidate_cannot_be_discovered_in_future(self):
  rows=self.rows('candidates');rows[0]['discovered_by']='E2';self.save('candidates',rows);self.fail('broken:event_candidate_discovery:E1:K1')
 def test_rediscovered_candidate_legacy_passes_with_warning(self):
  rows=self.rows('events');rows[1]['result']['new_candidate_ids']=['K1'];self.rechain(rows)
  self.assertIn('repeated:event_candidate:E2:K1',self.passes()['warnings'])
 def test_unknown_benchmark_found(self):
  rows=self.rows('events');rows[0]['result']['benchmark_ids_found']=['B404'];self.rechain(rows);self.fail('invalid:event_benchmark:E1')
 def test_unknown_review_claim(self):
  rows=self.rows('reviews');rows[-1]['claim_ids'].append('C404');self.save('reviews',rows);self.fail('invalid:review_claim:R3')
 def test_unknown_plan_question(self):
  self.protocol(lambda p:p['source_plan'][0].update(question_ids=['Q404']));self.fail('invalid:protocol_question_reference:SP1')
 def test_evidence_family_override_rejected(self):
  rows=self.rows('claims');rows[0]['evidence'][0]['source_family_id']='SF404';self.save('claims',rows);self.fail('broken:claim_source_family:C1:A1')
 def test_same_artifact_cannot_invent_independence(self):
  rows=self.rows('claims');c=rows[0];c['requires_independent_review']=True;c['evidence'].append(dict(c['evidence'][0],source_family_id='SF2'));self.save('claims',rows)
  out=self.fail('broken:claim_source_family:C1:A1');self.assertIn('gate:independent_sources_missing:C1',out['errors'])
 def test_no_registered_family_still_cannot_invent_independence(self):
  arts=self.rows('artifacts');arts[0].pop('source_family_id');self.save('artifacts',arts)
  rows=self.rows('claims');c=rows[0];c['requires_independent_review']=True;c['evidence'].append(dict(c['evidence'][0],source_family_id='SF2'));self.save('claims',rows)
  out=self.fail('broken:claim_source_family:C1:A1');self.assertIn('gate:independent_sources_missing:C1',out['errors'])
 def test_two_independent_artifacts_still_pass(self):
  arts=self.rows('artifacts');arts.append(dict(arts[0],artifact_id='A2',source_family_id='SF2'));self.save('artifacts',arts)
  rows=self.rows('claims');c=rows[0];c['requires_independent_review']=True;c['evidence'].append(dict(c['evidence'][0],artifact_id='A2',source_family_id='SF2'));self.save('claims',rows);self.passes()
 def test_family_in_evidence_only_legacy_passes(self):
  rows=self.rows('artifacts');rows[0].pop('source_family_id');self.save('artifacts',rows);self.passes()
 def test_empty_ambiguous_claim_without_attempts_rejected(self):
  rows=self.rows('claims');rows[0].update(status='AMBIGUOUS',evidence=[]);self.save('claims',rows)
  events=self.rows('events')
  for ev in events:ev['question_ids']=[]
  self.rechain(events);self.fail('gate:claim_without_evidence_or_attempts:C1')
 def test_empty_unavailable_claim_without_attempts_rejected(self):
  rows=self.rows('claims');rows[0].update(status='UNAVAILABLE',evidence=[]);self.save('claims',rows)
  events=self.rows('events')
  for ev in events:ev['question_ids']=[]
  self.rechain(events);self.fail('gate:claim_without_evidence_or_attempts:C1')
 def test_attempt_backed_unavailable_without_artifacts_passes(self):
  rows=self.rows('claims');rows[0].update(status='UNAVAILABLE',evidence=[]);self.save('claims',rows)
  self.save('artifacts',[]);self.save('candidates',[]);events=self.rows('events')
  for ev in events:ev['result'].update(status='zero',raw_hit_count=0,new_candidate_ids=[])
  self.rechain(events);self.passes()
 def test_supported_claim_needs_evidence_even_with_attempts(self):
  rows=self.rows('claims');rows[0]['evidence']=[];self.save('claims',rows);self.fail('missing:claim_evidence:C1')
 def test_negative_evidence_needs_expectation_basis(self):
  rows=self.rows('claims');rows[0]['evidence'][0]['mode']='negative';self.save('claims',rows);self.fail('invalid:negative_evidence:C1:A1')

 def test_protocol_must_be_object(self):
  dumpj(self.root/'protocol.json',[]);self.fail('invalid:type:protocol')
 def test_jsonl_record_must_be_object(self):
  self.save('claims',[None]);self.fail('invalid:type:claims[0]')
 def test_evidence_must_be_list(self):
  rows=self.rows('claims');rows[0]['evidence']='A1';self.save('claims',rows);self.fail('invalid:type:claims[0].evidence')
 def test_evidence_item_must_be_object(self):
  rows=self.rows('claims');rows[0]['evidence']=[None];self.save('claims',rows);self.fail('invalid:object_list:claims[0].evidence')
 def test_event_result_must_be_object(self):
  rows=self.rows('events');rows[0]['result']=None;self.rechain(rows);self.fail('invalid:type:events[0].result')
 def test_event_input_must_be_object(self):
  rows=self.rows('events');rows[0]['input']=[];self.rechain(rows);self.fail('invalid:type:events[0].input')
 def test_id_must_be_string(self):
  rows=self.rows('artifacts');rows[0]['artifact_id']=['A1'];self.save('artifacts',rows);self.fail('invalid:type:artifacts[0].artifact_id')
 def test_event_question_ids_cannot_be_scalar(self):
  rows=self.rows('events');rows[0]['question_ids']='Q1';self.rechain(rows);self.fail('invalid:type:events[0].question_ids')
 def test_review_claim_ids_cannot_contain_objects(self):
  rows=self.rows('reviews');rows[-1]['claim_ids']=[{'claim_id':'C1'}];self.save('reviews',rows);self.fail('invalid:string_list:reviews[2].claim_ids')
 def test_hash_must_be_string(self):
  rows=self.rows('artifacts');rows[0]['sha256']=42;self.save('artifacts',rows);self.fail('invalid:type:artifacts[0].sha256')
 def test_duplicate_json_keys_rejected(self):
  (self.root/'claims.jsonl').write_text('{"claim_id":"C1","claim_id":"C2"}\n');self.fail('parse:invalid_or_unreadable_run')
 def test_non_finite_json_rejected(self):
  p=json.loads((self.root/'protocol.json').read_text());p['extra']=float('nan');dumpj(self.root/'protocol.json',p);self.fail('parse:invalid_or_unreadable_run')
 def test_truncated_json_rejected(self):
  (self.root/'claims.jsonl').write_text('{');self.fail('parse:invalid_or_unreadable_run')
 def test_zero_saturation_window_rejected(self):
  self.protocol(lambda p:p['stop_policy'].update(no_new_family_window=0));self.fail('invalid:stop_policy.no_new_family_window')
 def test_negative_saturation_window_rejected(self):
  self.protocol(lambda p:p['stop_policy'].update(no_new_family_window=-1));self.fail('invalid:stop_policy.no_new_family_window')
 def test_boolean_min_routes_rejected(self):
  self.protocol(lambda p:p['stop_policy'].update(min_distinct_routes=True));self.fail('invalid:type:stop_policy.min_distinct_routes')
 def test_string_window_rejected(self):
  self.protocol(lambda p:p['stop_policy'].update(no_new_family_window='3'));self.fail('invalid:type:stop_policy.no_new_family_window')
 def test_r0_legacy_valid_shape_passes(self):
  self.protocol(lambda p:p.update(depth='R0'));self.passes()
 def test_r1_legacy_valid_shape_passes(self):
  self.protocol(lambda p:p.update(depth='R1'));rows=[r for r in self.rows('reviews') if r['checkpoint']!='MIDPOINT_REVIEW'];self.save('reviews',rows);self.passes()
 def test_unknown_extension_metadata_preserved(self):
  rows=self.rows('artifacts');rows[0]['extension']={'custom':['opaque',42]};self.save('artifacts',rows);self.passes()

class Saturation(unittest.TestCase):
 # Reuse only helpers, not the 72 integrity test methods.
 setUp=Integrity.setUp
 rows=Integrity.rows
 save=Integrity.save
 rechain=Integrity.rechain
 protocol=Integrity.protocol
 fail=Integrity.fail
 passes=Integrity.passes
 def add_artifact(self,event='E6',family='SF2',aid='A2',candidate='K2'):
  cs=self.rows('candidates');cs.append(dict(cs[0],candidate_id=candidate,discovered_by=event));self.save('candidates',cs)
  arts=self.rows('artifacts');arts.append(dict(arts[0],artifact_id=aid,candidate_id=candidate,source_family_id=family));self.save('artifacts',arts)
  events=self.rows('events')
  for ev in events:
   if ev['event_id']==event:ev['result']['new_candidate_ids'].append(candidate)
  self.rechain(events)
 def test_final_distinct_routes_pass_even_if_seen_before(self):
  m=self.passes()['metrics'];self.assertEqual(m['saturation_window_event_ids'],['E4','E5','E6']);self.assertEqual(m['saturation_window_distinct_routes'],3)
 def test_duplicate_window_fails_despite_global_diversity(self):
  events=self.rows('events');events[-1].update(plan_id='SP2',type='PIVOT',platform='Registry',input={'exact_query':'id1'});self.rechain(events)
  out=self.fail('gate:saturation_window_duplicate_routes');self.assertEqual(out['metrics']['distinct_routes'],3);self.assertEqual(out['metrics']['saturation_window_event_ids'],['E4','E5','E6'])
 def test_normalized_duplicate_window_fails(self):
  events=self.rows('events');events[-1].update(plan_id='SP1',type='QUERY',platform='Google',input={'exact_query':'官方 甲 著名 the 甲'});self.rechain(events)
  self.fail('gate:saturation_window_duplicate_routes')
 def test_different_plan_ids_do_not_make_distinct_routes(self):
  self.protocol(lambda p:p['source_plan'].append(dict(p['source_plan'][0],id='SP4',priority='could')))
  events=self.rows('events');events[-1].update(plan_id='SP4',type='QUERY',platform='Google',input={'exact_query':'甲 官方'});self.rechain(events)
  self.fail('gate:saturation_window_duplicate_routes')
 def test_same_query_different_platform_counts(self):
  events=self.rows('events');events[-1].update(plan_id='SP1',type='QUERY',platform='Other',input={'exact_query':'甲 官方'});self.rechain(events);self.passes()
 def test_same_query_different_surface_counts(self):
  self.protocol(lambda p:p['source_plan'].append(dict(p['source_plan'][0],id='SP4',surface='archive',priority='could')))
  events=self.rows('events');events[-1].update(plan_id='SP4',type='QUERY',platform='Google',input={'exact_query':'甲 官方'});self.rechain(events);self.passes()
 def test_same_query_different_method_counts(self):
  self.protocol(lambda p:p['source_plan'].append(dict(p['source_plan'][0],id='SP4',method='browse',priority='could')))
  events=self.rows('events');events[-1].update(plan_id='SP4',type='BROWSE',platform='Google',input={'exact_query':'甲 官方'});self.rechain(events);self.passes()
 def test_noise_fills_window_but_blocked_and_error_do_not(self):
  events=self.rows('events');events[-1]['result']['status']='noise'
  for n,status in enumerate(['blocked','error'],7):
   ev=copy.deepcopy(events[-1]);ev['event_id']=f'E{n}';ev['result']['status']=status;events.append(ev)
  self.rechain(events);self.assertEqual(self.passes()['metrics']['saturation_window_event_ids'],['E4','E5','E6'])
 def test_window_insufficient_does_not_backfill_capture(self):
  events=self.rows('events')[:2];ev=copy.deepcopy(events[-1]);ev.update(event_id='E3',type='CAPTURE',plan_id='SP3');events.append(ev);self.rechain(events)
  self.fail('gate:insufficient_saturation_window')
 def test_omitted_registered_family_in_window_rejected(self):
  self.add_artifact();out=self.fail('gate:not_saturated_new_family_in_window')
  self.assertIn('unreported:saturation_family_yield:E6:SF2',out['warnings']);self.assertEqual(out['metrics']['saturation_window_new_families'],['SF2'])
 def test_earliest_window_boundary_rejected(self):
  self.add_artifact(event='E4');self.fail('gate:not_saturated_new_family_in_window')
 def test_before_window_first_appearance_passes(self):
  self.add_artifact(event='E3');self.passes()
 def test_declared_yield_still_blocks_without_artifacts(self):
  events=self.rows('events');events[-1]['result']['new_source_family_ids']=['DECLARED_ONLY'];self.rechain(events);self.fail('gate:not_saturated_new_family_in_window')
 def test_declared_and_observed_are_conservative_union(self):
  self.add_artifact();events=self.rows('events');events[-1]['result']['new_source_family_ids']=['SF3'];self.rechain(events)
  out=self.fail('gate:not_saturated_new_family_in_window');self.assertEqual(out['metrics']['saturation_window_new_families'],['SF2','SF3'])
 def test_earlier_declaration_cannot_erase_first_observation(self):
  self.add_artifact();events=self.rows('events');events[0]['result']['new_source_family_ids']=['SF2'];self.rechain(events);self.fail('gate:not_saturated_new_family_in_window')
 def test_later_repeat_declaration_still_blocks(self):
  events=self.rows('events');events[-1]['result']['new_source_family_ids']=['SF1'];self.rechain(events);self.fail('gate:not_saturated_new_family_in_window')
 def test_same_registered_family_later_artifact_not_new(self):
  self.add_artifact(family='SF1');self.assertEqual(self.passes()['metrics']['saturation_observed_families'],1)
 def test_artifact_ledger_order_does_not_move_first_appearance(self):
  self.add_artifact(family='SF1');self.save('artifacts',list(reversed(self.rows('artifacts'))));self.passes()
 def test_multiple_artifacts_same_family_single_first_yield(self):
  self.add_artifact();self.add_artifact(aid='A3',candidate='K3')
  out=self.fail('gate:not_saturated_new_family_in_window');self.assertEqual(out['metrics']['family_yield_curve'][-1]['observed_first'],['SF2'])
 def test_capture_candidate_first_seen_in_window_blocks(self):
  events=self.rows('events');ev=copy.deepcopy(events[-1]);ev.update(event_id='E7',type='CAPTURE');events.append(ev);self.rechain(events)
  self.add_artifact(event='E7');self.fail('gate:not_saturated_new_family_in_window')
 def test_capture_declared_yield_after_window_blocks(self):
  events=self.rows('events');ev=copy.deepcopy(events[-1]);ev.update(event_id='E7',type='CAPTURE');ev['result']['new_source_family_ids']=['SF2'];events.append(ev);self.rechain(events);self.fail('gate:not_saturated_new_family_in_window')
 def test_late_capture_does_not_invent_recognition_timestamp(self):
  events=self.rows('events');ev=copy.deepcopy(events[-1]);ev.update(event_id='E7',type='CAPTURE');ev['result']['new_candidate_ids']=['K1'];events.append(ev);self.rechain(events)
  out=self.passes();self.assertFalse(out['metrics']['saturation_capture_timing_verified']);self.assertEqual(out['metrics']['family_yield_curve'][0]['observed_first'],['SF1'])
 def test_sparse_raw_missing_family_still_passes_with_warning(self):
  arts=self.rows('artifacts');arts[0].pop('source_family_id');self.save('artifacts',arts)
  self.rechain(self.rows('events')[:3]);out=self.passes();self.assertIn('unverified:saturation_artifact_family:A1',out['warnings']);self.assertEqual(out['metrics']['saturation_unknown_family_artifacts'],['A1']);self.assertEqual(out['metrics']['saturation_observed_families'],0)
 def test_original_three_event_registered_fixture_is_not_complete(self):
  self.rechain(self.rows('events')[:3]);self.fail('gate:not_saturated_new_family_in_window')
 def test_unknown_family_marker_not_independence_proof(self):
  self.add_artifact(family='UNKNOWN');out=self.passes();self.assertIn('A2',out['metrics']['saturation_unknown_family_artifacts']);self.assertFalse(out['metrics']['saturation_independence_verified'])
 def test_blank_family_warns_without_schema_rejection(self):
  self.add_artifact(family='   ');self.assertIn('unverified:saturation_artifact_family:A2',self.passes()['warnings'])
 def test_claim_only_family_not_promoted_across_claims(self):
  self.add_artifact(family=None);claims=self.rows('claims');ref=dict(claims[0]['evidence'][0],artifact_id='A2',source_family_id='SF2')
  claims[0]['counterevidence']=[ref];claims.append(dict(claims[0],claim_id='C2',evidence=[ref],counterevidence=[]));self.save('claims',claims)
  reviews=self.rows('reviews');reviews[-1]['claim_ids'].append('C2');self.save('reviews',reviews)
  out=self.passes();self.assertEqual(out['metrics']['saturation_observed_families'],1);self.assertIn('unverified:saturation_artifact_family:A2',out['warnings'])
 def test_cross_claim_conflicting_labels_remain_rejected(self):
  arts=self.rows('artifacts');arts[0].pop('source_family_id');self.save('artifacts',arts)
  claims=self.rows('claims');claims.append(dict(claims[0],claim_id='C2',evidence=[dict(claims[0]['evidence'][0],source_family_id='SF2')]));self.save('claims',claims);self.fail('broken:claim_source_family:C2:A1')
 def test_missing_discovery_reports_unlocated_family_metric(self):
  self.add_artifact(event='MISSING');out=self.fail('invalid:candidate_discovery:K2')
  self.assertIn('unverified:saturation_family_discovery:A2',out['warnings']);self.assertEqual(out['metrics']['saturation_unlocated_family_artifacts'],['A2'])
 def test_r0_diagnostic_does_not_add_r1_gate(self):
  self.protocol(lambda p:p.update(depth='R0'));self.add_artifact();out=self.passes();self.assertEqual(out['metrics']['saturation_window_new_families'],['SF2'])

if __name__=='__main__':unittest.main()
