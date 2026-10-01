from __future__ import annotations

import tempfile
import unittest

from .canonical import refresh_state_hash
from .graph_projector import project_events
from .input_router import classify_input, resolve_extractor_candidates
from .longform import commit_scene_event, init_longform_state, longform_store
from .memory import add_episode, add_reflection, consolidate_memory, make_episode, retrieve_memories
from .migrations import migrate_state
from .plans import evaluate_plan, make_plan, transition_plan
from .state import empty_state, normalize_state
from .structured_output import adapter_contract


class RuntimeV05Tests(unittest.TestCase):
    def test_explicit_migration_is_pure_and_auditable(self):
        v1 = empty_state("p", "s"); v1["schema"] = "minis.interactive-state.v1"; v1["memory"]["schema"] = "minis.actor-memory.v1"; v1.pop("state_hash", None)
        original = dict(v1)
        migrated, report = migrate_state(v1)
        self.assertEqual(v1, original); self.assertEqual(migrated["schema"], "minis.interactive-state.v3")
        self.assertEqual(migrated["memory"]["schema"], "minis.actor-memory.v2"); self.assertIn("archive", migrated["memory"])
        self.assertEqual(len(report["steps"]), 2); self.assertFalse(report["lossy"])
        self.assertEqual(normalize_state(migrated, verify_hash=False)["schema"], "minis.interactive-state.v3")

    def test_ambiguous_input_never_advances_world(self):
        for text in ("繼續", "好", "那個", "whatever"):
            report = classify_input(text); self.assertTrue(report["requires_clarification"]); self.assertFalse(report["advance_world"])
        conflict = resolve_extractor_candidates("去那裡", [{"type": "move", "confidence": .76}, {"type": "speak", "confidence": .70}])
        self.assertTrue(conflict["requires_clarification"])

    def test_plan_lifecycle_deadline_interrupt_and_terminal_guard(self):
        state = empty_state("p", "s"); state["clock"]["tick"] = 5
        plan = make_plan("npc", "送信", action_type="move", deadline_tick=10, interrupt_on=["fire"])
        plan = transition_plan(plan, "active", tick=1, reason="approved")
        self.assertTrue(evaluate_plan(state, plan)["available"])
        self.assertEqual(evaluate_plan(state, plan, event_tags=["fire"])["recommended_status"], "interrupted")
        state["clock"]["tick"] = 11; self.assertEqual(evaluate_plan(state, plan)["recommended_status"], "failed")
        done = transition_plan(plan, "completed", tick=9, reason="delivered")
        with self.assertRaises(ValueError): transition_plan(done, "active", tick=10, reason="illegal")

    def test_memory_consolidation_preserves_event_source_and_supersedes_reflection(self):
        state = empty_state("p", "s"); state["actors"]["npc"] = {"kind": "npc", "location": "x"}
        ids = []
        for n in range(5):
            ep = make_episode("npc", event_id=f"e{n}", text=f"事件 {n} 硬幣", tick=n, importance=n % 3); ids.append(ep["memory_id"]); state = add_episode(state, ep)
        state = add_reflection(state, {"actor_id": "npc", "text": "硬幣移動了", "evidence_memory_ids": ids[:2]})
        state = add_reflection(state, {"actor_id": "npc", "text": "硬幣移動了", "evidence_memory_ids": ids[2:4]})
        consolidated, report = consolidate_memory(state, "npc", hot_episode_limit=2, hot_reflection_limit=1)
        self.assertTrue(report["event_source_preserved"]); self.assertEqual(report["hot_episodes"], 2)
        self.assertEqual(len(consolidated["memory"]["archive"]["npc"]["episodes"]), 3)
        self.assertEqual(len(retrieve_memories(consolidated, "npc", query="硬幣", top_k=10)), 3)

    def test_crash_matrix_reconciles_every_replayable_verdict(self):
        from .engine import recover_store
        from .canonical import refresh_state_hash
        from .store import FileStore
        for verdict in ("allow", "allow_with_cost", "partial", "meta"):
            with tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "p", "s"); before = empty_state("p", "s"); store.save_state(before)
                after = dict(before); after["revision"] = 1; after["events_head"] = "head"; after["last_turn_id"] = verdict; refresh_state_hash(after)
                event = {"event_id": "e-" + verdict, "idempotency_key": "i-" + verdict, "turn_id": verdict, "verdict": verdict, "after_state_hash": after["state_hash"]}
                store.append_event(event); store.write_journal({"event_id": event["event_id"], "idempotency_key": event["idempotency_key"], "after_state_hash": after["state_hash"], "after_state": after, "status": "committed"})
                self.assertEqual(recover_store(store)["status"], "reconciled_state_from_event")
                self.assertEqual(store.load_state()["state_hash"], after["state_hash"])

    def test_semantic_projection_emits_typed_edges(self):
        event = {"event_id": "e", "turn_id": "t", "actor_id": "a", "action_type": "move", "verdict": "allow", "created_at": "x", "operations": [{"op": "replace", "path": "/actors/a/location", "value": "hall"}]}
        graph = project_events([event], project_id="p", session_id="s", branch_id="main")
        self.assertIn("located_in", {x["relation"] for x in graph["links"]})
        self.assertEqual(graph["graph"]["projection_schema"], "minis.interactive-graph-projection.v3")

    def test_local_model_contract_and_longform_event_kernel(self):
        contract = adapter_contract("intent_extract", provider="llama.cpp")
        self.assertFalse(contract["json_schema"]["additionalProperties"])
        with tempfile.TemporaryDirectory() as tmp:
            store = longform_store(tmp, "novel")
            initial = init_longform_state("novel"); store.save_state(initial); store.write_checkpoint("initial", initial)
            result = commit_scene_event(store, scene_id="scene-1", chapter_id="ch-1", operations=[{"op": "add", "path": "/world_truth/events/scene-1", "value": {"summary": "變化"}}], summary="變化", author_approved=True, expected_state_hash=initial["state_hash"])
            self.assertEqual(result["status"], "committed"); self.assertEqual(len(store.read_events()), 1)
            self.assertIn("runtime/sessions", str(store.base))


if __name__ == "__main__": unittest.main()
