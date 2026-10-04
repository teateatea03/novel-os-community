#!/usr/bin/env python3
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from research_gap_planner import plan


class GapPlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.p = {'schema': 'minis.character-research-run.v2', 'run_id': 'fixture',
                  'questions': [{'id': 'Q1', 'priority': 'P0'}],
                  'source_plan': [{'id': 'SP1', 'priority': 'must'}]}
        self.data = {'events': [{'event_id': 'E1', 'type': 'QUERY', 'plan_id': 'SP1',
                                'result': {'status': 'success'}}],
                     'candidates': [{'candidate_id': 'K1', 'disposition': 'include'}],
                     'artifacts': [{'artifact_id': 'A1', 'source_family_id': 'SF1'}],
                     'claims': [{'claim_id': 'C1', 'question_id': 'Q1', 'status': 'SUPPORTED',
                                 'evidence': [{'artifact_id': 'A1', 'source_family_id': 'SF1', 'locator': 'p1'}]}],
                     'reviews': [{'review_id': 'R1', 'checkpoint': 'CLAIM_AUDIT', 'claim_ids': ['C1']}]}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        (self.root / 'protocol.json').write_text(json.dumps(self.p))
        for name, rows in self.data.items():
            (self.root / (name + '.jsonl')).write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def result(self):
        self.write()
        return plan(self.root)

    def kinds(self):
        return {t['kind'] for t in self.result()['tasks']}

    def test_single_family_is_advisory(self):
        r = self.result()
        self.assertTrue(r['advisory_only'])
        self.assertFalse(r['completion_assessed'])
        self.assertIn('limited_source_diversity', self.kinds())

    def test_missing_p0(self):
        self.data['claims'] = []
        self.assertIn('question_without_claim', self.kinds())

    def test_conflict_and_audit(self):
        self.data['claims'][0]['status'] = 'CONTESTED'
        self.data['reviews'] = []
        self.assertTrue({'conflicting_claim', 'p0_not_audited'} <= self.kinds())

    def test_unknown_and_no_evidence(self):
        self.data['claims'][0].update(status='UNAVAILABLE', evidence=[])
        self.assertTrue({'unresolved_claim', 'no_supporting_evidence'} <= self.kinds())

    def test_broken_artifact(self):
        self.data['artifacts'] = []
        self.assertIn('broken_artifact_reference', self.kinds())

    def test_family_conflict(self):
        self.data['artifacts'][0]['source_family_id'] = 'SF2'
        self.assertIn('family_label_conflict', self.kinds())

    def test_partial_capture(self):
        self.data['artifacts'][0]['capture_status'] = 'metadata_only'
        self.assertIn('incomplete_capture', self.kinds())

    def test_identity_is_first(self):
        self.data['candidates'][0]['identity_binding'] = 'PROBABLE'
        self.assertEqual(self.result()['tasks'][0]['kind'], 'identity_not_verified')

    def test_defer(self):
        self.data['candidates'][0].update(disposition='defer', priority='high')
        self.assertIn('deferred_candidate', self.kinds())

    def test_blocked_not_zero(self):
        self.data['events'][0]['result']['status'] = 'blocked'
        self.assertTrue({'last_attempt_blocked', 'must_route_unfinished'} <= self.kinds())
        self.data['events'][0]['result']['status'] = 'zero'
        self.assertNotIn('must_route_unfinished', self.kinds())

    def test_duplicate_rejected(self):
        self.data['claims'].append(copy.deepcopy(self.data['claims'][0]))
        with self.assertRaises(ValueError):
            self.result()

    def test_non_object_rejected(self):
        self.data['claims'] = [None]
        with self.assertRaises(ValueError):
            self.result()

    def test_symlink_rejected(self):
        self.write()
        with tempfile.TemporaryDirectory() as d:
            outside = Path(d) / 'data'
            outside.write_text('[]')
            (self.root / 'claims.jsonl').unlink()
            (self.root / 'claims.jsonl').symlink_to(outside)
            with self.assertRaises(ValueError):
                plan(self.root)

    def test_read_only(self):
        self.write()
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        plan(self.root)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.iterdir()}
        self.assertEqual(before, after)

    def test_output_never_overwrites(self):
        self.write()
        path = self.root / 'protocol.json'
        before = path.read_bytes()
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name('research_gap_planner.py')),
                               str(self.root), '--output', str(path)], capture_output=True)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(path.read_bytes(), before)

    def test_missing_file(self):
        self.write()
        (self.root / 'reviews.jsonl').unlink()
        with self.assertRaises(ValueError):
            plan(self.root)


if __name__ == '__main__':
    unittest.main()
