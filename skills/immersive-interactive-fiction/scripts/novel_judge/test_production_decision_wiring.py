from __future__ import annotations
import hashlib, tempfile, unittest
from pathlib import Path
from .author_feedback import feedback_status
from .author_workbench import build_workbench_report, record_author_decision_action
from .canonical import refresh_state_hash
from .gate_authority import make_gate_envelope
from .longform import commit_scene_event, initialize_longform_production
from .production import make_candidate_binding
from .semantic_events import compile_semantic_delta
from .state import empty_state
from .production import ProjectRuntimeAdapter

class ProductionDecisionWiringTests(unittest.TestCase):
 def test_workbench_can_record_accept_revise_reject(self):
  with tempfile.TemporaryDirectory() as td:
   a=initialize_longform_production(td,'novel')
   # revise/reject before any scene
   r=record_author_decision_action(a, decision='revise', candidate_hash='sha256:cand1', reason_codes=['pacing'], reason='too fast', turn_id='T1')
   self.assertEqual(r['decision'],'revise'); self.assertEqual(r['explicit_count'],1)
   r2=record_author_decision_action(a, decision='reject', candidate_hash='sha256:cand2', reason='nope', turn_id='T2')
   self.assertEqual(r2['explicit_count'],2)
   r3=record_author_decision_action(a, decision='accept', candidate_hash='sha256:cand3', reason_codes=['continuity'], reason='ok', turn_id='T3')
   self.assertEqual(r3['authority_layer'],'AUTHOR_DECISION')
   self.assertEqual(feedback_status(a.store)['explicit_count'],3)
   wb=build_workbench_report(a)
   self.assertIn('decision_actions', wb['actions'])
   self.assertEqual(wb['quality']['author_feedback_ledger']['explicit_count'],3)

 def test_scene_commit_via_longform_writes_decision_and_workbench_sees_it(self):
  with tempfile.TemporaryDirectory() as td:
   a=initialize_longform_production(td,'novel'); root=Path(td)
   scene_path=root/'chapters/chapter-001.md'; scene_path.parent.mkdir(); scene_path.write_text('scene',encoding='utf-8')
   scene_hash=hashlib.sha256(scene_path.read_bytes()).hexdigest(); state=a.store.load_state(); turn='scene-001'
   envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene_hash,source_state_hash=state['state_hash']) for g in a.gate_policy()['required_gate_types']]
   ops=[{'op':'add','path':'/world_truth/events/scene-001','value':{'summary':'door opens'}}]
   sem=compile_semantic_delta(turn_id=turn,actor_id='world',action_type='scene_commit',operations=ops,summary='Door opens',scene_id=turn)
   binding=make_candidate_binding(turn_id=turn,operations=ops,actor_id='world',action_type='scene_commit',summary='Door opens',scene_id=turn,chapter_id='chapter-001',scene_sha256=scene_hash,semantic_hash=sem['semantic_hash'])
   a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash,source_state_hash=state['state_hash'],envelopes=envs,candidate_binding=binding)
   r=commit_scene_event(a,scene_id=turn,chapter_id='chapter-001',operations=ops,summary='Door opens',author_approved=True,expected_state_hash=state['state_hash'],source_artifact_hash=scene_hash,source_artifact_path='chapters/chapter-001.md',scene_sha256=scene_hash,author_decision={'decision':'accept','reason_codes':['continuity'],'reason':'ok'})
   self.assertEqual(r['status'],'committed')
   self.assertEqual(feedback_status(a.store)['explicit_count'],1)
   wb=build_workbench_report(a)
   self.assertEqual(wb['quality']['author_feedback_ledger']['explicit_count'],1)

if __name__=='__main__': unittest.main()
