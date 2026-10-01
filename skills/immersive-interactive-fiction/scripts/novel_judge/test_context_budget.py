from __future__ import annotations

import unittest

from .context_budget import (
    CONTEXT_WINDOW_64K, CONTEXT_WINDOW_LARGE, POLICY_LOSSLESS, POLICY_LOSSY,
    admit_context_dict, admit_sources, context_policy_for_window, estimate_tokens,
    render_admitted_sources,
)
from .state import empty_state
from .canonical import refresh_state_hash
from .model_tasks import compile_model_task
from .memory import add_episode, make_episode


class ContextBudgetTests(unittest.TestCase):
    def test_estimator_handles_chinese_and_json(self):
        self.assertGreater(estimate_tokens("觀測員在圓頂下。"), 1)
        self.assertGreater(estimate_tokens({"a": "中文"}), 1)

    def test_64k_reserves_output_and_safety(self):
        r = admit_sources([], profile="render", context_window=CONTEXT_WINDOW_64K)
        self.assertEqual(r["admission"], "pass")
        self.assertLess(r["input_budget"], CONTEXT_WINDOW_64K)
        self.assertEqual(r["output_reserve"], 8000)

    def test_required_sources_are_preserved_and_archive_evicted(self):
        sources = [{"source_id": "core", "tier": "CORE", "required": True, "text": "核心"}]
        sources += [{"source_id": f"archive-{i}", "tier": "ARCHIVE", "priority": 0, "text": "archive " * 200} for i in range(20)]
        r = admit_sources(sources, profile="render", context_window=5000, output_reserve=100, safety_margin=100,
                          context_policy="lossy")
        self.assertIn("core", r["selected_sources"])
        self.assertTrue(r["evicted_sources"])
        self.assertEqual(r["admission"], "compressed_pass")
        self.assertEqual(r["context_policy"], POLICY_LOSSY)

    def test_required_overflow_fails_closed(self):
        r = admit_sources([{"source_id": "must", "required": True, "text": "x" * 30000}], context_window=5000, output_reserve=20, safety_margin=20)
        self.assertEqual(r["admission"], "reject")

    def test_context_pack_has_admission_and_model_task_hashes_it(self):
        state = empty_state("budget", "s")
        state["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []}}
        state = refresh_state_hash(state)
        packet = compile_model_task(state, task="blind_read", actor_id="player", context_window=CONTEXT_WINDOW_64K)
        self.assertIn("context_admission", packet)
        self.assertIn("context_hash", packet["context"])
        self.assertTrue(packet["task_hash"])

    def test_lossy_policy_still_evicts_and_compacts(self):
        sources = [{"source_id": "core", "tier": "CORE", "required": True, "text": "核心\n\n保留"}]
        sources += [{"source_id": f"archive-{i}", "tier": "ARCHIVE", "priority": 0, "text": "archive " * 200} for i in range(20)]
        r = admit_sources(sources, profile="render", context_window=5000, output_reserve=100, safety_margin=100,
                          context_policy="lossy")
        self.assertEqual(r["context_policy"], POLICY_LOSSY)
        self.assertTrue(r["evicted_sources"])
        self.assertEqual(r["forgotten_sources"], r["evicted_sources"])
        self.assertEqual(r["admission"], "compressed_pass")

    def test_lossless_policy_does_not_forget_overflow(self):
        sources = [{"source_id": "core", "tier": "CORE", "required": True, "text": "核心  空白"}]
        sources += [{"source_id": f"archive-{i}", "tier": "ARCHIVE", "priority": 0, "text": "archive " * 80} for i in range(12)]
        r = admit_sources(sources, profile="render", context_window=5000, output_reserve=100, safety_margin=100,
                          context_policy="astra")
        self.assertEqual(r["context_policy"], POLICY_LOSSLESS)
        self.assertEqual(r["evicted_sources"], [])
        self.assertEqual(r["forgotten_sources"], [])
        self.assertTrue(r["addressable_overflow"])
        self.assertEqual(r["admission"], "addressable_pass")
        self.assertEqual(r["detail_preservation"], "verbatim")
        rendered = render_admitted_sources(sources, r)
        self.assertIn("核心  空白", rendered)
        self.assertIn("<addressable-overflow>", rendered)
        self.assertIn('id="archive-0"', rendered)

    def test_every_window_defaults_to_lossless(self):
        self.assertEqual(context_policy_for_window(CONTEXT_WINDOW_LARGE), POLICY_LOSSLESS)
        self.assertEqual(context_policy_for_window(CONTEXT_WINDOW_64K), POLICY_LOSSLESS)
        self.assertEqual(context_policy_for_window(4096), POLICY_LOSSLESS)
        self.assertEqual(context_policy_for_window(CONTEXT_WINDOW_64K, "lossy"), POLICY_LOSSY)

    def test_64k_default_does_not_forget_overflow(self):
        sources = [{"source_id": "core", "tier": "CORE", "required": True, "text": "核心  空白"}]
        sources += [{"source_id": f"archive-{i}", "tier": "ARCHIVE", "priority": 0, "text": "archive " * 80} for i in range(12)]
        r = admit_sources(sources, profile="render", context_window=5000, output_reserve=100, safety_margin=100)
        self.assertEqual(r["context_policy"], POLICY_LOSSLESS)
        self.assertEqual(r["forgotten_sources"], [])
        self.assertEqual(r["evicted_sources"], [])
        self.assertTrue(r["addressable_overflow"])
        self.assertEqual(r["admission"], "addressable_pass")

    def test_lossless_compile_keeps_every_episode_addressable(self):
        state = empty_state("budget", "s")
        state["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []}}
        for i in range(8):
            state = add_episode(state, make_episode("player", event_id=f"e{i}", text=f"細節{i} 不能被摘要丟掉", tick=i, importance=2))
        state = refresh_state_hash(state)
        small = compile_model_task(state, task="render", actor_id="player", context_window=CONTEXT_WINDOW_64K)
        self.assertEqual(small["context_policy"], POLICY_LOSSLESS)
        self.assertEqual(small["forgotten_source_ids"], [])
        self.assertGreaterEqual(len(small["addressable_source_ids"]), 8)
        packet = compile_model_task(state, task="render", actor_id="player",
                                    context_window=CONTEXT_WINDOW_LARGE)
        self.assertEqual(packet["context_policy"], POLICY_LOSSLESS)
        self.assertEqual(packet["forgotten_source_ids"], [])
        self.assertGreaterEqual(len(packet["addressable_source_ids"]), 8)
        memories = (packet["context"].get("memory_context") or {}).get("memories") or []
        self.assertGreaterEqual(len(memories), 8)
        self.assertFalse((packet["context"].get("memory_context") or {}).get("retrieval_cut"))

    def test_promoted_corrections_survive_admission(self):
        context = {
            "schema": "minis.interactive-context.v2",
            "audience": "player",
            "actor_id": "player",
            "provenance": {"state_hash": "x"},
            "author_corrections": [{"title": "技術員見熟人直接打招呼", "rule": "直接打招呼"}],
            "author_correction_notes": "- [technician] 直接打招呼",
            "memory_context": {"memories": ["archive " * 400]},
        }
        admitted = admit_context_dict(context, profile="render")
        self.assertIn("author_corrections", admitted)
        self.assertIn("author_correction_notes", admitted)


if __name__ == "__main__":
    unittest.main()
