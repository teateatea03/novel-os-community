"""Synthetic regression fixtures for detached, hash-stable model inputs."""
from __future__ import annotations

import unittest

from .canonical import deep_copy, sha256_json
from .context import build_context
from .model_tasks import TASK_SCHEMAS, compile_model_task


class TaskSnapshotIsolationTests(unittest.TestCase):
    def state(self):
        return {"state_hash": "sha256:synthetic-snapshot", "actors": {},
                "storylets": {"active": [{"id": "synthetic-storylet",
                    "candidate_intents": [{"type": "inspect", "targets": ["synthetic-object"]}]}]}}

    def packet(self, **kwargs):
        return compile_model_task(self.state(), task="repair", actor_id="player",
                                  persist_used_sources=False, **kwargs)

    def assert_hash_matches(self, value, key):
        self.assertEqual(value[key], sha256_json({k: v for k, v in value.items() if k != key}))

    def test_caller_edits_do_not_change_compiled_task(self):
        manifest = {"beats": [{"purpose": "synthetic original"}]}
        issues = [{"id": "synthetic-issue", "details": ["synthetic original"]}]
        packet = self.packet(approved_manifest=manifest, issues=issues)
        before = deep_copy(packet)
        manifest["beats"][0]["purpose"] = "synthetic changed"
        issues[0]["details"].append("synthetic changed")
        self.assertEqual(packet, before)
        self.assert_hash_matches(packet, "task_hash")

    def test_packet_edits_do_not_change_caller_inputs(self):
        manifest = {"beats": [{"purpose": "synthetic original"}]}
        issues = [{"id": "synthetic-issue", "details": ["synthetic original"]}]
        originals = deep_copy((manifest, issues))
        packet = self.packet(approved_manifest=manifest, issues=issues)
        packet["approved_manifest"]["beats"][0]["purpose"] = "synthetic changed"
        packet["issues"][0]["details"].append("synthetic changed")
        self.assertEqual((manifest, issues), originals)

    def test_packet_contract_edits_do_not_change_global_or_other_packet(self):
        original = deep_copy(TASK_SCHEMAS)
        first = self.packet()
        second = self.packet()
        before = deep_copy(second)
        try:
            first["output_contract"]["required"].append("synthetic_extra")
            self.assertEqual(TASK_SCHEMAS, original)
            self.assertEqual(second, before)
            self.assertEqual(self.packet(), before)
            self.assert_hash_matches(second, "task_hash")
        finally:
            # Keep a failing regression run from contaminating unrelated tests.
            TASK_SCHEMAS.clear()
            TASK_SCHEMAS.update(original)

    def test_state_edits_do_not_change_context_snapshot(self):
        state = self.state()
        context = build_context(state)
        before = deep_copy(context)
        state["storylets"]["active"].append("synthetic-later")
        self.assertEqual(context, before)
        self.assert_hash_matches(context, "context_hash")

    def test_context_edits_do_not_change_state(self):
        state = self.state()
        before = deep_copy(state)
        context = build_context(state)
        context["storylets"]["active"].append("synthetic-later")
        self.assertEqual(state, before)

    def test_state_intent_edits_do_not_change_compiled_candidates(self):
        state = self.state()
        packet = compile_model_task(state, task="repair", actor_id="player",
                                    persist_used_sources=False)
        before = deep_copy(packet)
        self.assertEqual(len(packet["storylet_candidates"]), 1)
        state["storylets"]["active"][0]["candidate_intents"][0]["targets"].append("synthetic-later")
        self.assertEqual(packet, before)
        self.assert_hash_matches(packet, "task_hash")

    def test_candidate_edits_do_not_change_state_intents(self):
        state = self.state()
        before = deep_copy(state)
        packet = compile_model_task(state, task="repair", actor_id="player",
                                    persist_used_sources=False)
        packet["storylet_candidates"][0]["candidate_intents"][0]["targets"].append("synthetic-later")
        self.assertEqual(state, before)

    def test_default_and_empty_inputs_keep_deterministic_hashes(self):
        default = self.packet()
        explicit = self.packet(approved_manifest={}, issues=[])
        self.assertEqual(default, explicit)
        self.assertEqual(default, self.packet())
        self.assert_hash_matches(default, "task_hash")
        context = build_context({})
        self.assertEqual(context["storylets"], {"active": []})
        self.assert_hash_matches(context, "context_hash")


if __name__ == "__main__":
    unittest.main()
