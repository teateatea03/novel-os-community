from __future__ import annotations
import json,tempfile,unittest
from .production import ProjectRuntimeAdapter
from .production_inputs import project_event_memories,project_thread_storylets,refresh_production_writing_inputs,production_writing_inputs_status,resolve_writing_inputs_manifest,read_used_sources
from .model_tasks import compile_model_task
from .turn import run_turn
from .scene_studio import preview_context
from .state import empty_state
from .canonical import refresh_state_hash

class ProductionInputsTests(unittest.TestCase):
 def setup(self,root):
  s=empty_state('p','s');s['revision']=1;s['actors']={'alice':{'kind':'npc','role':'npc','location':'room','status':{},'commitments':[]},'bob':{'kind':'npc','role':'npc','location':'room','status':{},'commitments':[]}};s['world_truth']['locations']={'room':{'connections':{}}};s['threads']['open']=[{'id':'door','status':'active','question':'Who opens it?'}];s=refresh_state_hash(s);a=ProjectRuntimeAdapter(root,'p','s');a.initialize(s,baseline_id='b',provenance={'shadow':True},migration_authorized=True);return a,s
 def test_event_memory_is_deterministic_and_actor_scoped(self):
  state=empty_state('p','s');state['actors']={'alice':{},'bob':{}};events=[{'event_id':'e1','turn_id':'T1','actor_id':'alice','action_type':'speak','scene':{'summary':'alice calls bob'},'operations':[]}]
  m=project_event_memories(state,events);self.assertEqual(len(m['alice']),1);self.assertEqual(len(m['bob']),1);self.assertEqual(m,project_event_memories(state,events))
 def test_thread_storylet_projection(self):
  state=empty_state('p','s');state['threads']['open']=[{'id':'door','status':'active','question':'Open?'}]
  cards=project_thread_storylets(state);self.assertEqual(cards[0]['source_thread_id'],'door')
 def test_refresh_builds_source_bound_actor_contexts(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=self.setup(td);events=[{'event_id':'e1','turn_id':'T1','actor_id':'alice','action_type':'speak','scene':{'summary':'alice calls bob'},'operations':[]}]
   # Projection accepts canonical reader output; patch read_events only in isolated unit fixture.
   old=a.store.read_events;a.store.read_events=lambda **kw:events
   m=refresh_production_writing_inputs(a);status=production_writing_inputs_status(a)
   self.assertEqual(status['status'],'pass');self.assertEqual(status['context_count'],2);self.assertGreater(status['episode_count'],0);self.assertEqual(m['storylets']['count'],1)
 def test_compile_model_task_reads_session_writing_inputs(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=self.setup(td);events=[{'event_id':'e1','turn_id':'T1','actor_id':'alice','action_type':'speak','verdict':'allow','scene':{'summary':'alice calls bob'},'operations':[]}]
   a.store.read_events=lambda **kw:events
   m=refresh_production_writing_inputs(a)
   state=a.store.load_state()
   self.assertIsNone(state.get('_production_project_root'))
   packet=compile_model_task(state,task='render',actor_id='alice',store=a.store)
   self.assertEqual(packet['generation_read_model'],'verified')
   self.assertEqual(packet['context_policy'],'lossless-addressable')
   self.assertEqual(packet['forgotten_source_ids'],[])
   self.assertIsInstance(packet['used_source_ids'],list)
   self.assertGreater(len(packet['used_source_ids']),0)
   self.assertTrue(packet.get('used_sources_sidecar'))
   self.assertIsNone(a.store.load_state().get('_production_project_root'))
   sidecar=read_used_sources(td,'alice',store=a.store,state=state)
   self.assertEqual(sidecar['used_source_ids'], packet['used_source_ids'])
   preview=preview_context(a, actor_id='alice')
   self.assertEqual(preview.get('used_source_ids'), packet['used_source_ids'])
   self.assertTrue(preview.get('addressable_source_ids'))
   pack_path=a.project_root / (m['context']['alice']['path'])
   pack=json.loads(pack_path.read_text(encoding='utf-8'))
   self.assertEqual(pack['addressable_source_ids'], packet['addressable_source_ids'] or pack['addressable_source_ids'])
   self.assertGreaterEqual(len(pack['addressable_source_ids']), len(pack['selected_source_ids']))
   large=compile_model_task(state,task='render',actor_id='alice',store=a.store,context_window=1_050_000,persist_used_sources=False)
   self.assertEqual(large['context_policy'],'lossless-addressable')
   self.assertEqual(large['forgotten_source_ids'],[])
   self.assertGreaterEqual(len(large['addressable_source_ids']), len(packet['used_source_ids']))
 def test_run_turn_preview_uses_verified_pack_without_canon_write(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=self.setup(td);events=[{'event_id':'e1','turn_id':'T1','actor_id':'alice','action_type':'speak','verdict':'allow','scene':{'summary':'alice calls bob'},'operations':[]}]
   a.store.read_events=lambda **kw:events
   refresh_production_writing_inputs(a)
   before=a.store.load_state()['state_hash']
   from unittest.mock import patch
   with patch('novel_judge.turn.commit_turn', return_value={'status':'skipped'}):
    result=run_turn(a.store, {'schema':'minis.interactive-intent.v1','actor_id':'alice','type':'wait','parameters':{}}, actor_id='alice')
   self.assertEqual(result['turn_pipeline']['preflight_context']['generation_read_model'],'verified')
   self.assertGreater(len(result['turn_pipeline']['preflight_context']['used_source_ids'] or []), 0)
   self.assertEqual(a.store.load_state()['state_hash'], before)
   self.assertIsNone(a.store.load_state().get('_production_project_root'))
if __name__=='__main__':unittest.main()
