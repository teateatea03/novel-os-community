from __future__ import annotations
import hashlib,tempfile,unittest
from pathlib import Path
from .gate_authority import make_gate_envelope
from .production import make_candidate_binding
from .semantic_events import compile_semantic_delta
from .longform import initialize_longform_production,commit_scene_event

class LongformProductionAuthorityTests(unittest.TestCase):
 def test_new_longform_project_is_active_single_authority(self):
  with tempfile.TemporaryDirectory() as td:
   a=initialize_longform_production(td,'novel');self.assertEqual(a.authority_record()['status'],'active');self.assertTrue(a.authority_record()['born_under_single_authority'])
   with self.assertRaises(Exception):a.store.save_state(a.store.load_state())
   self.assertEqual(a.assert_conformant()['status'],'pass')
 def test_scene_commit_requires_gate_and_persists_typed_event(self):
  with tempfile.TemporaryDirectory() as td:
   a=initialize_longform_production(td,'novel');root=Path(td);scene_path=root/'chapters/chapter-001.md';scene_path.parent.mkdir();scene_path.write_text('scene',encoding='utf-8');scene_hash=hashlib.sha256(scene_path.read_bytes()).hexdigest();state=a.store.load_state();turn='scene-001'
   envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene_hash,source_state_hash=state['state_hash']) for g in a.gate_policy()['required_gate_types']]
   ops=[{'op':'add','path':'/world_truth/events/scene-001','value':{'summary':'door opens'}}];sem=compile_semantic_delta(turn_id=turn,actor_id='world',action_type='scene_commit',operations=ops,summary='Door opens',scene_id=turn);binding=make_candidate_binding(turn_id=turn,operations=ops,actor_id='world',action_type='scene_commit',summary='Door opens',scene_id=turn,chapter_id='chapter-001',scene_sha256=scene_hash,semantic_hash=sem['semantic_hash'])
   a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash,source_state_hash=state['state_hash'],envelopes=envs,candidate_binding=binding)
   r=commit_scene_event(a,scene_id=turn,chapter_id='chapter-001',operations=[{'op':'add','path':'/world_truth/events/scene-001','value':{'summary':'door opens'}}],summary='Door opens',author_approved=True,expected_state_hash=state['state_hash'],source_artifact_hash=scene_hash,source_artifact_path='chapters/chapter-001.md',scene_sha256=scene_hash)
   self.assertEqual(r['status'],'committed');self.assertEqual(r['event']['action_type'],'scene_commit');self.assertEqual(r['event']['semantic_delta']['semantic_kind'],'scene_state_transition');self.assertEqual(a.assert_conformant()['status'],'pass')
 def test_direct_filestore_longform_commit_fails_closed(self):
  with tempfile.TemporaryDirectory() as td:
   a=initialize_longform_production(td,'novel')
   with self.assertRaises(Exception):a.store.save_state(a.store.load_state())
if __name__=='__main__':unittest.main()
