"""Synthetic examples must not be presented as actual model measurements."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from luna_baseline_gate import REQUIRED


class SyntheticCapabilityExamplesTests(unittest.TestCase):
    def test_illustrative_examples_are_explicit_and_host_only(self):
        for name in ('synthetic-reasoning-budget-example.json', 'synthetic-task-capability-example.json'):
            with self.subTest(name=name):
                data = json.loads((ROOT / 'fixtures' / name).read_text(encoding='utf-8'))
                self.assertIs(data['synthetic'], True)
                self.assertEqual(data['fixture_kind'], 'illustrative_not_measurement')
                self.assertNotIn('date', data)
                self.assertNotIn('benchmark', data)
                for model in data.get('models', {}).values():
                    self.assertEqual(model['task_level'], 'unrated_synthetic_example')
                    self.assertEqual(model['production_authority'], 'host_only')
                if 'required_route' in data:
                    self.assertEqual(data['required_route']['canonical_commit'], 'host_only')
                    self.assertIsNone(data['settings_change'])

    def run_gate(self, report):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'report.json'
            path.write_text(json.dumps(report), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/luna_baseline_gate.py'),
                                     '--report', str(path)], capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout)

    def test_design_baseline_requires_every_probe(self):
        report = {'active_model': 'synthetic-model', 'probes': {key: {'passed': True} for key in REQUIRED}}
        code, result = self.run_gate(report)
        self.assertEqual(code, 0)
        self.assertEqual(result['baseline'], 'novel-os-candidate-baseline-v1')
        for key in REQUIRED:
            incomplete = {'probes': {name: value for name, value in report['probes'].items() if name != key}}
            code, result = self.run_gate(incomplete)
            self.assertEqual(code, 2)
            self.assertFalse(result['ok'])
            self.assertIn(key, {item.get('probe') for item in result['findings']})


if __name__ == '__main__':
    unittest.main()
