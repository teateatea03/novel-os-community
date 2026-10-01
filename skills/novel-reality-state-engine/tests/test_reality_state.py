"""Reality gates exercised with an independently invented observatory fixture."""
import copy
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


if __name__ == '__main__':
    unittest.main()
