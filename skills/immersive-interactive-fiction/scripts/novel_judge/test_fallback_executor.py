from __future__ import annotations

import unittest
from .canonical import refresh_state_hash
from .fallback_executor import execute_host_fallback
from .state import empty_state


class FallbackExecutorTests(unittest.TestCase):
    def fixture(self):
        s = empty_state("fallback", "s")
        s["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []},
                        "npc": {"kind": "npc", "location": "room", "status": {}, "commitments": []}}
        return refresh_state_hash(s)

    def test_intent_is_deterministic_and_clarifies_continue(self):
        s = self.fixture(); r = execute_host_fallback(s, task="intent_extract", actor_id="player", input_text="繼續")
        self.assertEqual(r["status"], "clarification"); self.assertFalse(r["authority"]["may_commit_state"])

    def test_npc_plan_without_storylet_returns_safe_wait(self):
        s = self.fixture(); r = execute_host_fallback(s, task="npc_plan", actor_id="npc")
        self.assertEqual(r["output"]["actor_id"], "npc"); self.assertEqual(r["output"]["action_type"], "wait")

    def test_scene_render_and_blind_read_are_scaffolds_not_commit(self):
        s = self.fixture(); manifest = execute_host_fallback(s, task="scene_manifest", actor_id="npc")
        render = execute_host_fallback(s, task="render", actor_id="npc", approved_manifest=manifest["output"])
        review = execute_host_fallback(s, task="blind_read", actor_id="npc", candidate=render["output"])
        self.assertEqual(render["status"], "scaffold"); self.assertEqual(review["output"]["status"], "pass")
        self.assertFalse(render["authority"]["may_write_files"])

    def test_repair_only_applies_explicit_meta_patch(self):
        s = self.fixture(); r = execute_host_fallback(s, task="repair", actor_id="npc", input_text="[META] text", issues=[{"code":"META_LEAK","issue_id":"i1"}])
        self.assertEqual(r["output"]["fixed_issue_ids"], ["i1"]); self.assertNotIn("META", r["output"]["text"])


if __name__ == "__main__": unittest.main()
