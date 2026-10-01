from __future__ import annotations
import json,tempfile,unittest
from .canonical import refresh_state_hash
from .semantic_invariants import inspect_state,inspect_transition,enforce_transition
from .state import empty_state

class SemanticInvariantTests(unittest.TestCase):
 def fixture(self):
  s=empty_state('p','s');s['actors']={'a':{'location':'room','condition':{},'inventory':[]}};s['world_truth']['locations']={'room':{},'bath':{}};s['world_truth']['objects']={'x':{'holder':None,'location':'room'}};return refresh_state_hash(s)
 def test_actor_location_conflict_blocks(self):
  s=self.fixture();ops=[{'op':'add','path':'/actors/a/condition/location','value':'bath'}];r=inspect_transition(s,__import__('novel_judge.delta',fromlist=['apply_operations']).apply_operations(s,ops,source='author'),operations=ops);self.assertEqual(r['status'],'blocked');self.assertEqual(r['blockers'][0]['code'],'ACTOR_LOCATION_CONFLICT')
 def test_legacy_debt_is_grandfathered_but_new_debt_blocks(self):
  s=self.fixture();s['actors']['a']['condition']['location']='bath';refresh_state_hash(s);ops=[{'op':'replace','path':'/clock/tick','value':1}];self.assertEqual(enforce_transition(s,ops)['status'],'pass')
  bad=[{'op':'replace','path':'/world_truth/objects/x/holder','value':'a'}];self.assertEqual(inspect_transition(s,__import__('novel_judge.delta',fromlist=['apply_operations']).apply_operations(s,bad,source='author'),operations=bad)['status'],'blocked')
 def test_clock_reversal_blocks(self):
  s=self.fixture();s['clock'].update({'tick':10,'now':'2026-01-02T00:00:00+00:00'});refresh_state_hash(s);ops=[{'op':'replace','path':'/clock/tick','value':9}];after=__import__('novel_judge.delta',fromlist=['apply_operations']).apply_operations(s,ops,source='author');self.assertIn('CLOCK_TICK_REVERSED',[x['code'] for x in inspect_transition(s,after,operations=ops)['blockers']])
 def test_thread_lifecycle_conflict_blocks(self):
  s=self.fixture();s['threads']={'open':[{'id':'q','status':'active'}],'resolved':[]};refresh_state_hash(s);ops=[{'op':'add','path':'/threads/resolved/-','value':{'id':'q'}}];after=__import__('novel_judge.delta',fromlist=['apply_operations']).apply_operations(s,ops,source='author');self.assertIn('THREAD_LIFECYCLE_CONFLICT',[x['code'] for x in inspect_transition(s,after,operations=ops)['blockers']])
 def test_facet_interval_invalid_blocks(self):
  s=self.fixture();ops=[{'op':'add','path':'/actors/a/condition/pain','value':{'id':'p','value':'high','valid_from':'2026-01-02T00:00:00+00:00','valid_to':'2026-01-01T00:00:00+00:00'}}];after=__import__('novel_judge.delta',fromlist=['apply_operations']).apply_operations(s,ops,source='author');self.assertIn('FACET_INTERVAL_INVALID',[x['code'] for x in inspect_transition(s,after,operations=ops)['blockers']])
if __name__=='__main__':unittest.main()
