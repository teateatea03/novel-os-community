"""Reality gates exercised with an independently invented observatory fixture."""
import copy
import json
import subprocess
import tempfile
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import reality_state

FIX = Path(__file__).parents[1] / 'fixtures/minimal-state.json'


class RealityStateTests(unittest.TestCase):
    def setUp(self):
        self.state = reality_state.load(FIX)
        self.card = reality_state.infer(self.state)

    def test_card_capacity(self):
        self.assertIs(self.state['fixture']['synthetic'], True)
        self.assertFalse(self.card['cognition']['long_analysis_allowed'])
        self.assertEqual(self.card['physical']['hunger'], 'high')
        self.assertEqual(self.card['physical']['thermal_load'], 'wet_cold')
        self.assertEqual(self.card['knowledge_boundary'], self.state['knowledge_ledger'])

    def test_gate_rejects_overclean_analysis(self):
        text = '觀測員完整整理全部器材紀錄，列出十種替代解釋及四個遠期維修計畫。'
        self.assertTrue(reality_state.gate(self.card, text))

    def test_gate_rejects_consent_equation(self):
        self.assertTrue(reality_state.gate(self.card, '角色的身體反應代表同意。'))

    def test_gate_rejects_thermal_contradiction(self):
        self.assertTrue(reality_state.gate(self.card, '觀測員在冷雨下完全不受影響。'))

    def test_food_state_is_independent_of_actor_names(self):
        state = copy.deepcopy(self.state)
        for event in state['events']:
            event['actor'] = 'independent-actor'
            event['observed_by'] = ['independent-observer']
        self.assertEqual(reality_state.infer(state)['physical']['hunger'], 'high')

    def test_generic_food_absence_marker_remains_supported(self):
        state = {'world': {'now': 'test'}, 'events': [{'id': 'event-1', 'action': 'food_absence'}]}
        self.assertEqual(reality_state.infer(state)['physical']['hunger'], 'high')


class RealityInputTests(unittest.TestCase):
    def test_infer_rejects_missing_or_malformed_state(self):
        valid = {'world': {'now': 'synthetic-day'}, 'events': [{'id': 'synthetic-1'}]}
        invalid = [{}, None, [], {'events': [], 'world': {'now': 'day'}},
                   {**valid, 'world': {'now': '  '}}, {**valid, 'events': [None]},
                   {**valid, 'events': [{}]}, {**valid, 'world': []},
                   {**valid, 'world': {'now': 'day', 'resources': []}},
                   {**valid, 'npcs': {'characters': [None]}}]
        for state in invalid:
            with self.subTest(state=state), self.assertRaises(ValueError):
                reality_state.infer(state)

    def test_gate_rejects_empty_or_whitespace_prose(self):
        card = reality_state.infer({'world': {'now': 'day'}, 'events': [{'id': 'event-1'}]})
        for text in ('', ' \t\n\u3000'):
            with self.subTest(text=text):
                self.assertIn('missing nonempty draft', reality_state.gate(card, text))

    def test_cli_invalid_inputs_do_not_evaluate_or_write_card(self):
        script = Path(reality_state.__file__)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = root / 'state.json'
            draft = root / 'draft.md'
            output = root / 'card.json'
            draft.write_text('Synthetic prose.', encoding='utf-8')
            for command in ('validate', 'card', 'gate'):
                state.write_text('{}', encoding='utf-8')
                args = [sys.executable, str(script), command, '--state', str(state), '--out', str(output)]
                if command == 'gate':
                    args += ['--text', str(draft)]
                result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 2, result.stderr)
                data = json.loads(result.stdout)
                self.assertFalse(data['ok'])
                self.assertEqual(data['status'], 'invalid_input')
                self.assertEqual(data['evaluation'], 'not_evaluated')
                self.assertIsNone(data.get('card'))
                self.assertFalse(output.exists())

    def test_cli_rejects_empty_missing_and_invalid_utf8_drafts(self):
        script = Path(reality_state.__file__)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state, draft = root / 'state.json', root / 'draft.md'
            state.write_text(json.dumps({'world': {'now': 'day'}, 'events': [{'id': 'event-1'}]}), encoding='utf-8')
            for raw in (b'', b' \r\n\t', b'\xff'):
                draft.write_bytes(raw)
                result = subprocess.run([sys.executable, str(script), 'gate', '--state', str(state),
                                         '--text', str(draft)], capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 2, result.stderr)
                data = json.loads(result.stdout)
                self.assertEqual(data['status'], 'invalid_input')
                self.assertEqual(data['evaluation'], 'not_evaluated')
                self.assertIsNone(data.get('card'))
            result = subprocess.run([sys.executable, str(script), 'gate', '--state', str(state)],
                                    capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
