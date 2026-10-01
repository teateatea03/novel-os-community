from __future__ import annotations
import hashlib,tempfile,unittest,subprocess,sys,os,json
from pathlib import Path
from .canonical import refresh_state_hash
from .command_executor import make_author_command,write_author_command,claim_author_command,execute_author_command,recover_author_commands,load_author_command
from .gate_authority import make_gate_envelope
from .production import ProjectRuntimeAdapter
from .state import empty_state


def setup(root):
 s=empty_state('p','s');s['canon_scope']='experiment';s['actors']={'world':{'kind':'world','location':'room','status':{},'commitments':[]}};s['world_truth']['locations']={'room':{'connections':{}}};s=refresh_state_hash(s)
 a=ProjectRuntimeAdapter(root,'p','s');a.initialize(s,baseline_id='b',provenance={'shadow':True},migration_authorized=True);return a,s

def envs(a,turn,scene,state_hash):
 return [make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene,source_state_hash=state_hash) for g in a.gate_policy()['required_gate_types']]

class CommandExecutorTests(unittest.TestCase):
 def test_create_candidate_lifecycle_and_lease_fencing(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);scene=hashlib.sha256(b'candidate').hexdigest();payload={'turn_id':'C1','scene_sha256':scene,'operations':[]}
   rec=write_author_command(a.store,make_author_command(kind='create_candidate',author_id='author',reason='test',source_state_hash=s['state_hash'],source_event_head=s.get('events_head'),payload=payload))
   claimed=claim_author_command(a.store,rec['command_id'],worker_id='w')
   with self.assertRaises(ValueError):execute_author_command(a,rec['command_id'],worker_id='w',lease_token='wrong')
   done=execute_author_command(a,rec['command_id'],worker_id='w',lease_token=claimed['lease_token'])
   self.assertEqual(done['status'],'completed');self.assertEqual(len(a.store.read_events()),0)
   self.assertTrue((a.store.base/'command-candidates'/f"{done['candidate_id']}.json").is_file())
 def test_stale_request_is_terminal_without_rebase(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);rec=write_author_command(a.store,make_author_command(kind='create_candidate',author_id='a',reason='x',source_state_hash='sha256:'+'0'*64,source_event_head=None,payload={}))
   stale=claim_author_command(a.store,rec['command_id'],worker_id='w');self.assertEqual(stale['status'],'stale');self.assertEqual(len(a.store.read_events()),0)
 def test_expired_lease_recovers_and_old_token_is_fenced(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);scene=hashlib.sha256(b'x').hexdigest();rec=write_author_command(a.store,make_author_command(kind='create_candidate',author_id='a',reason='x',source_state_hash=s['state_hash'],source_event_head=None,payload={'turn_id':'C2','scene_sha256':scene}))
   claimed=claim_author_command(a.store,rec['command_id'],worker_id='old',lease_seconds=1);future='2999-01-01T00:00:00Z';r=recover_author_commands(a.store,at=future);self.assertIn(rec['command_id'],r['recovered'])
   new=claim_author_command(a.store,rec['command_id'],worker_id='new')
   with self.assertRaises(ValueError):execute_author_command(a,rec['command_id'],worker_id='old',lease_token=claimed['lease_token'])
   self.assertEqual(execute_author_command(a,rec['command_id'],worker_id='new',lease_token=new['lease_token'])['status'],'completed')
 def test_approval_full_e2e_commits_once(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);turn='C3';scene=hashlib.sha256(b'approval').hexdigest();payload={'candidate':{'turn_id':turn,'scene_sha256':scene,'operations':[{'op':'replace','path':'/clock/tick','value':1}]},'envelopes':envs(a,turn,scene,s['state_hash'])}
   rec=write_author_command(a.store,make_author_command(kind='request_approval',author_id='author',reason='approve',source_state_hash=s['state_hash'],source_event_head=s.get('events_head'),payload=payload));claimed=claim_author_command(a.store,rec['command_id'],worker_id='executor')
   done=execute_author_command(a,rec['command_id'],worker_id='executor',lease_token=claimed['lease_token']);self.assertEqual(done['status'],'committed');self.assertEqual(len(a.store.read_events()),1);self.assertEqual(a.store.load_state()['clock']['tick'],1);self.assertEqual(a.assert_conformant()['status'],'pass');self.assertEqual(done['author_feedback']['decision'],'accept');self.assertTrue(a.store.read_events()[0].get('semantic_delta_hash'))
   with self.assertRaises(ValueError):claim_author_command(a.store,rec['command_id'],worker_id='again')
 def test_two_workers_race_exactly_one_claims(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);scene=hashlib.sha256(b'race').hexdigest();rec=write_author_command(a.store,make_author_command(kind='create_candidate',author_id='a',reason='race',source_state_hash=s['state_hash'],source_event_head=None,payload={'turn_id':'RACE','scene_sha256':scene}))
   code="""import sys,json\nfrom novel_judge.production import ProjectRuntimeAdapter\nfrom novel_judge.command_executor import claim_author_command\na=ProjectRuntimeAdapter(sys.argv[1],'p','s')\ntry: print(json.dumps({'ok':True,'r':claim_author_command(a.store,sys.argv[2],worker_id=sys.argv[3])}))\nexcept Exception as e: print(json.dumps({'ok':False,'error':str(e)}))\n"""
   env=dict(os.environ);env['PYTHONPATH']=str(Path(__file__).parent.parent)
   ps=[subprocess.Popen([sys.executable,'-c',code,td,rec['command_id'],w],stdout=subprocess.PIPE,text=True,env=env) for w in ('w1','w2')]
   rows=[json.loads(p.communicate(timeout=20)[0]) for p in ps];self.assertEqual(sum(x['ok'] for x in rows),1)
 def test_validation_failure_is_durable_terminal(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);rec=write_author_command(a.store,make_author_command(kind='create_candidate',author_id='a',reason='bad',source_state_hash=s['state_hash'],source_event_head=None,payload={}))
   claimed=claim_author_command(a.store,rec['command_id'],worker_id='w')
   with self.assertRaises(ValueError):execute_author_command(a,rec['command_id'],worker_id='w',lease_token=claimed['lease_token'])
   self.assertEqual(load_author_command(a.store,rec['command_id'])['status'],'failed')
 def test_legacy_v1_migrates_then_stale(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);old={'schema':'minis.author-command-request.v1','command_id':'legacy','kind':'create_candidate','status':'pending','author_id':'a','reason':'old','source_state_hash':'sha256:'+'0'*64,'source_event_head':None,'payload':{},'created_at':'2026-01-01T00:00:00Z'}
   from .canonical import sha256_json
   old['request_hash']=sha256_json(old);p=a.store.base/'commands/legacy.json';a.store._atomic_json(p,old)
   self.assertEqual(load_author_command(a.store,'legacy')['schema'],'minis.author-command.v2');self.assertEqual(claim_author_command(a.store,'legacy',worker_id='w')['status'],'stale')
if __name__=='__main__':unittest.main()
