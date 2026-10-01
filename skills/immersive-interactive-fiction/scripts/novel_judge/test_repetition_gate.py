from __future__ import annotations

import unittest
from .canonical import refresh_state_hash
from .model_tasks import validate_model_result
from .state import empty_state
from .narrative_gate import validate_generated_output


class RepetitionGateIntegrationTests(unittest.TestCase):
    def test_model_semantics_rejects_repeated_render(self):
        packet = {"task": "render", "task_hash": "h", "source_state_hash": "s"}
        text = "門邊的燈亮了一下。她沒有說話。風從窗縫進來。" * 3
        result = {"task_hash": "h", "text": text, "claimed_facts": [], "action_manifest": [], "player_actions": []}
        report = validate_model_result(packet, result)
        self.assertIn("REPETITION_LOOP", {x["code"] for x in report["errors"]})

    def test_narrative_gate_rejects_repeated_render(self):
        state = empty_state("rep", "s"); state["actors"] = {"npc": {"kind": "npc", "location": "room"}}
        state = refresh_state_hash(state)
        output = {"text": "門邊的燈亮了一下。她沒有說話。風從窗縫進來。" * 3,
                  "claimed_facts": [], "action_manifest": [], "player_actions": []}
        report = validate_generated_output(output, state, audience="reader", actor_id="npc")
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "REPETITION_LOOP" for x in report["errors"]))


if __name__ == "__main__": unittest.main()
