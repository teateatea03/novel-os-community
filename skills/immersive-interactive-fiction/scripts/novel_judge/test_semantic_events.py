from __future__ import annotations
import hashlib,tempfile,unittest
from .semantic_events import compile_semantic_delta,validate_semantic_delta
from .test_production_authority import initialize,approve

class TypedSemanticEventTests(unittest.TestCase):
 def test_compile_hash_bound_domain_effects(self):
  ops=[{'op':'replace','path':'/actors/player/location','value':'hall'}]
  s=compile_semantic_delta(turn_id='T1',actor_id='player',action_type='move',operations=ops,summary='Player moves to hall')
  self.assertEqual(s['semantic_kind'],'actor_movement');self.assertEqual(s['effects'][0]['effect_type'],'move_actor');validate_semantic_delta(s,ops)
  with self.assertRaises(ValueError):validate_semantic_delta(s,[])
  with self.assertRaises(ValueError):compile_semantic_delta(turn_id='T1',actor_id='player',action_type='move',operations=ops,declared_effects=[{'effect_type':'move_actor','operation_indices':[]}])
 def test_production_commit_persists_typed_delta(self):
  with tempfile.TemporaryDirectory() as td:
   a,state=initialize(td);turn='T-TYPED';scene=approve(a,turn,state['state_hash']);ops=[{'op':'replace','path':'/clock/tick','value':1}]
   r=a.commit(turn_id=turn,operations=ops,expected_state_hash=state['state_hash'],action_type='world_tick',summary='Clock advances one tick',scene_sha256=scene)
   e=r['event'];self.assertEqual(e['semantic_delta']['summary'],'Clock advances one tick');self.assertEqual(e['semantic_delta_hash'],e['semantic_delta']['semantic_hash']);self.assertEqual(a.assert_conformant()['status'],'pass')
 def test_meta_empty_is_explicit_metadata_only(self):
  s=compile_semantic_delta(turn_id='M1',actor_id='world',action_type='meta',operations=[])
  self.assertEqual(s['semantic_kind'],'metadata_only');self.assertTrue(s['summary'])
if __name__=='__main__':unittest.main()
