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

class FeedbackEvidenceRegressionTests(unittest.TestCase):
 def check_rows(self, rows, expected_rate, known, unknown, explicit_count):
  from .author_quality_eval import production_quality_telemetry
  from .author_feedback import _paths
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td)
   Path(td,'project.json').write_text(json.dumps({'project_id':'p','interactive_runtime':{'session_id':'s','branch':'main'}}))
   for i,(explicit,rr) in enumerate(rows):
    append_author_feedback(a.store,decision='accept',author_id='synthetic-test',candidate_hash=f'sha256:synthetic-{i}',source_state_hash=s['state_hash'],source_event_head=None,turn_id=f'T{i}',explicit=explicit,revision_round=rr,gate_pass=True)
   originals={p:p.read_bytes() for p in _paths(a.store)}
   out=Path(td)/'eval';manifest=build_project_fixtures(td,out);report=evaluate_fixture_dir(out);tel=production_quality_telemetry(td)
   for metrics in (report['metrics'],tel):
    self.assertEqual(metrics['explicit_author_pass_at_1'],expected_rate)
    self.assertEqual(metrics['explicit_accept_known_round_count'],known)
    self.assertEqual(metrics['explicit_accept_unknown_round_count'],unknown)
    self.assertEqual(metrics['explicit_accept_round_coverage'],known/(known+unknown) if known+unknown else None)
   self.assertEqual(tel['explicit_feedback_count'],explicit_count)
   self.assertEqual(manifest['explicit_feedback_count'],explicit_count)
   self.assertEqual(report['evidence_counts']['explicit_author_feedback'],explicit_count)
   self.assertEqual(report['metrics']['gate_confusion_explicit_only']['true_positive'],explicit_count)
   self.assertEqual(a.store.load_state()['state_hash'],s['state_hash'])
   for p,before in originals.items():self.assertEqual(p.read_bytes(),before)
 def test_unknown_round_is_not_first_acceptance(self):self.check_rows([(True,None)],None,0,1,1)
 def test_nonexplicit_feedback_is_not_author_truth(self):self.check_rows([(False,0)],None,0,0,0)
 def test_known_rounds_keep_accepted_only_denominator(self):self.check_rows([(True,0),(True,2)],0.5,2,0,2)
 def test_unknown_round_reduces_coverage_not_known_rate(self):self.check_rows([(True,0),(True,2),(True,None),(False,0)],0.5,2,1,3)
 def test_invalid_rounds_remain_unknown(self):self.check_rows([(True,False),(True,-1),(True,'0')],None,0,3,3)
 def test_missing_explicit_is_not_promoted(self):
  from unittest import mock
  from .author_quality_eval import production_quality_telemetry
  from . import author_quality_eval as quality
  from . import author_feedback as feedback
  with tempfile.TemporaryDirectory() as td:
   a,s=setup(td)
   row={'event_id':'synthetic-missing','event_hash':'sha256:synthetic','candidate_hash':'sha256:synthetic','decision':'accept','revision_round':0,'gate_pass':True}
   with mock.patch.object(quality,'_adapter_for_root',return_value=a), mock.patch.object(feedback,'read_author_feedback',return_value=[row]), mock.patch.object(feedback,'feedback_status',return_value={'events':[row]}):
    out=Path(td)/'eval';m=build_project_fixtures(td,out);r=evaluate_fixture_dir(out);t=production_quality_telemetry(td)
   self.assertEqual(m['explicit_feedback_count'],0)
   self.assertIsNone(r['metrics']['explicit_author_pass_at_1'])
   self.assertEqual(r['metrics']['gate_confusion_explicit_only']['true_positive'],0)
   self.assertEqual(t['explicit_feedback_count'],0)

if __name__=='__main__':unittest.main()
