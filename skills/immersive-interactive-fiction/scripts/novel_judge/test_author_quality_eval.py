from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from .author_quality_eval import text_stats,build_project_fixtures,evaluate_fixture_dir
from .author_feedback import append_author_feedback,feedback_status
from .test_command_executor import setup

class AuthorQualityEvalTests(unittest.TestCase):
 def test_changed_spans_and_distance(self):
  r=text_stats('abc','axc');self.assertGreater(r['normalized_edit_distance'],0);self.assertEqual(r['changed_span_count'],1)
 def test_lineage_dedup_and_proxy_separation(self):
  with tempfile.TemporaryDirectory() as td:
   r=Path(td);current=r/'interactive/scenes';current.mkdir(parents=True);(current/'T0001.md').write_text('after')
   for n,text in [('a','before one'),('b','before two')]:
    d=r/f'snapshots/{n}/interactive/scenes';d.mkdir(parents=True);(d/'T0001.md').write_text(text)
   for k in ('approved','rejected'):(r/f'interactive/prose-fixtures/{k}').mkdir(parents=True);(r/f'interactive/prose-fixtures/{k}/{k}.md').write_text(k)
   out=r/'eval';m=build_project_fixtures(r,out,minimum=50);self.assertEqual(m['observed_pair_count'],1);self.assertTrue(m['minimum_is_not_filled_with_duplicate_lineages'])
   q=evaluate_fixture_dir(out);self.assertIn('explicit_author_pass_at_1',q['metrics']);self.assertNotIn('pass_at_1_author_acceptance',q['metrics'])
 def test_append_only_feedback_is_explicit_truth(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td);f=append_author_feedback(a.store,decision='accept',author_id='author',candidate_hash='sha256:candidate',source_state_hash=s['state_hash'],source_event_head=None,turn_id='T1',reason_codes=['character_voice'],revision_round=0)
   self.assertEqual(feedback_status(a.store)['explicit_count'],1);self.assertEqual(f['decision'],'accept')
   same=append_author_feedback(a.store,decision='accept',author_id='author',candidate_hash='sha256:candidate',source_state_hash=s['state_hash'],source_event_head=None,turn_id='T1',reason_codes=['character_voice'],revision_round=0)
   self.assertEqual(same['event_id'],f['event_id']);self.assertEqual(feedback_status(a.store)['event_count'],1)
 def test_isolated_project_explicit_pass_at_1_moves_without_proxy_mix(self):
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td)
   Path(td,'project.json').write_text(json.dumps({
    'project_id':'p','interactive_runtime':{'session_id':'s','branch':'main'}
   }))
   from .author_workbench import record_author_decision_action
   from .author_quality_eval import production_quality_telemetry, refresh_quality_evaluation
   empty=production_quality_telemetry(td)
   self.assertIsNone(empty['explicit_author_pass_at_1'])
   first=record_author_decision_action(
    a, decision='accept', candidate_hash='sha256:first', author_id='author',
    reason_codes=['character_voice'], turn_id='T1', revision_round=0,
   )
   self.assertTrue(first['ok'])
   second=record_author_decision_action(
    a, decision='accept', candidate_hash='sha256:second', author_id='author',
    reason_codes=['pacing'], reason='after rewrite', turn_id='T2', revision_round=2,
   )
   self.assertTrue(second['ok'])
   tel=production_quality_telemetry(td)
   self.assertEqual(tel['explicit_feedback_count'], 2)
   self.assertEqual(tel['explicit_accept_count'], 2)
   self.assertEqual(tel['explicit_author_pass_at_1'], 0.5)
   self.assertIsNone(tel['workflow_commit_proxy'])
   report=refresh_quality_evaluation(a)
   self.assertEqual(report['metrics']['explicit_author_pass_at_1'], 0.5)
   self.assertIsNone(report['metrics']['workflow_commit_proxy_pass_at_1'])
   self.assertEqual(a.store.load_state()['state_hash'], s['state_hash'])
if __name__=='__main__':unittest.main()
