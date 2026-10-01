from __future__ import annotations
import tempfile, unittest
from .branches import fork_branch, promote_branch
from .canonical import refresh_state_hash
from .engine import commit_turn, replay_events, recover_store
from .errors import JudgeError, PLAYER_SOVEREIGNTY
from .graph_patch import build_graph_patch
from .intent import make_intent
from .narrative import validate_prose
from .reality import gate_reality
from .epistemic import knowledge_gate
from .state import empty_state
from .store import FileStore
from .world_tick import candidate_ticks
from .memory import make_episode, add_episode, retrieve_memories, validate_reflection
from .model_tasks import compile_model_task, validate_model_result
from .graph_projector import project_events


def fixture() -> dict:
    s = empty_state("acceptance", "session")
    s["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []},
                    "npc": {"kind": "npc", "location": "room", "status": {}, "commitments": []}}
    s["world_truth"]["locations"] = {"room": {"connections": {"hall": {"to": "hall", "open": True}}},
                                      "hall": {"connections": {"room": {"to": "room", "open": True}}}}
    s["world_truth"]["objects"] = {"coin": {"location": "room", "holder": None}}
    return refresh_state_hash(s)

class JudgeAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.store = FileStore(self.tmp.name, "acceptance", "session")
        self.initial = fixture(); self.store.save_state(self.initial)
    def tearDown(self): self.tmp.cleanup()
    def test_20_turn_deterministic_vertical_slice(self):
        actions = [("observe", []), ("move", ["hall"]), ("move", ["room"])] + [("wait", [])] * 17
        for n, (typ, targets) in enumerate(actions, 1):
            params = {"seconds": 1} if typ == "wait" else {}
            commit_turn(self.store, make_intent("player", typ, turn_id=f"t{n}", targets=targets, parameters=params))
        self.assertEqual(len(self.store.read_events()), 20)
        self.assertEqual(replay_events(self.initial, self.store.read_events())["state_hash"], self.store.load_state()["state_hash"])
    def test_player_sovereignty_and_narrative_gate(self):
        i = make_intent("player", "promise", turn_id="bad", parameters={"text": "secret"}, source="model", player_authored=False, model_generated=True)
        with self.assertRaises(JudgeError) as cm: commit_turn(self.store, i)
        self.assertEqual(cm.exception.code, PLAYER_SOVEREIGNTY)
        r = commit_turn(self.store, make_intent("player", "observe", turn_id="gate"), generated_output={"text": "x", "player_actions": [{"type": "move"}]})
        self.assertEqual(r["verdict"], "rejected"); self.assertEqual(len(self.store.read_events()), 2)
    def test_branch_isolation_and_promotion_report(self):
        commit_turn(self.store, make_intent("player", "move", turn_id="base", targets=["hall"]))
        self.store.write_checkpoint("base", self.store.load_state()); child = fork_branch(self.store, "candidate", checkpoint_id="base")
        commit_turn(child, make_intent("player", "move", turn_id="child", targets=["room"]))
        self.assertNotEqual(child.load_state()["state_hash"], self.store.load_state()["state_hash"])
        self.assertEqual(promote_branch(child, author_decision="approve")["canon_write"], "not_performed")
    def test_recovery_clears_interrupted_journal(self):
        self.store.write_journal({"phase": "prepared", "after_state_hash": "sha256:not-current"})
        self.assertEqual(recover_store(self.store)["status"], "rolled_back_to_last_state")
        self.assertIsNone(self.store.load_journal())
    def test_background_tick_candidates_are_non_mutating_and_deterministic(self):
        self.initial["plans"] = {"npcs": {"npc": {"action_type": "observe"}}, "world": {}}
        before = self.initial["state_hash"]; a = candidate_ticks(self.initial, steps=3, seed=7); b = candidate_ticks(self.initial, steps=3, seed=7)
        self.assertEqual(a, b); self.assertEqual(before, self.initial["state_hash"]); self.assertTrue(all(x["source"] == "npc_plan" for x in a))

    def test_unknown_exit_and_missing_source_cannot_control_player(self):
        self.initial["world_truth"]["locations"]["room"]["connections"]["hall"]["open"] = "unknown"
        self.store.save_state(refresh_state_hash(self.initial))
        with self.assertRaises(JudgeError):
            commit_turn(self.store, make_intent("player", "move", turn_id="unknown-door", targets=["hall"]))
        with self.assertRaises(JudgeError) as cm:
            commit_turn(self.store, make_intent("player", "move", turn_id="model-no-flag", targets=["hall"], source="model"))
        self.assertEqual(cm.exception.code, PLAYER_SOVEREIGNTY)

    def test_reality_knowledge_and_prose_gates(self):
        self.initial["reality"]["actors"]["player"] = {"blocked_actions": ["move"], "available_actions": ["observe"]}
        self.store.save_state(refresh_state_hash(self.initial))
        with self.assertRaises(JudgeError) as cm:
            commit_turn(self.store, make_intent("player", "move", turn_id="blocked", targets=["hall"]))
        self.assertEqual(cm.exception.code, "CAPACITY_BLOCKED")
        self.initial["knowledge"]["truth"] = {"secret": {"visibility": "private"}}
        self.initial["knowledge"]["player"] = {"player": []}
        self.assertFalse(knowledge_gate(self.initial, ["secret"], audience="player", actor_id="player")["ok"])
        report = validate_prose({"text": "leak", "claimed_facts": ["secret"]}, self.initial, self.initial, {"actor_id": "player", "type": "observe"}, audience="player", actor_id="player")
        self.assertEqual(report["status"], "fail")

    def test_graph_patch_and_event_provenance(self):
        result = commit_turn(self.store, make_intent("player", "move", turn_id="provenance", targets=["hall"]))
        patch = self.store._read_json(self.store.patch_dir / "provenance.json")
        event = result["event"]
        self.assertEqual(event["branch_id"], "main")
        self.assertEqual(patch["before_state_hash"], result["pre_state_hash"])
        self.assertEqual(patch["after_state_hash"], result["post_state_hash"])

    def test_cost_defer_and_connection_command_gates(self):
        self.initial["reality"]["actors"]["player"] = {"action_costs": {"wait": {"cold": "increases"}}}
        self.store.save_state(refresh_state_hash(self.initial))
        waited = commit_turn(self.store, make_intent("player", "wait", turn_id="cost", parameters={"seconds": 2}))
        self.assertEqual(waited["verdict"], "allow_with_cost")
        self.assertEqual(waited["event"]["delayed_effects"][0]["kind"], "world_tick_eligible")
        deferred = commit_turn(self.store, make_intent("player", "observe", turn_id="defer", parameters={"defer_author": True}))
        self.assertEqual(deferred["verdict"], "defer")
        self.assertEqual(deferred["post_state_hash"], deferred["pre_state_hash"])
        opened = commit_turn(self.store, make_intent("player", "open", turn_id="open", targets=["hall"]))
        self.assertEqual(opened["verdict"], "allow")

    def test_manifest_head_tracks_committed_state(self):
        result = commit_turn(self.store, make_intent("player", "observe", turn_id="head"))
        manifest = self.store.load_manifest()
        self.assertEqual(manifest["head_event_id"], result["event"]["event_id"])
        self.assertEqual(manifest["head_state_hash"], result["post_state_hash"])

    def test_world_tick_candidate_can_be_judged_without_player_mutation(self):
        self.initial["plans"] = {"world": {"actions": [{"action_type": "world_tick", "parameters": {"operations": [{"op": "replace", "path": "/clock/tick", "value": 1}]} }]}, "npcs": {}}
        candidates = candidate_ticks(self.initial, steps=1, seed=2)
        self.assertEqual(candidates[0]["actor_id"], "world")
        result = commit_turn(self.store, candidates[0])
        self.assertEqual(result["verdict"], "allow")
        self.assertEqual(self.store.load_state()["clock"]["tick"], 1)


        before = self.store.load_state()
        after = dict(before); after["revision"] = 1; after["last_turn_id"] = "crash"; after["events_head"] = "head-crash"; refresh_state_hash(after)
        intent = make_intent("player", "observe", turn_id="crash")
        event = {"schema": "minis.world-event.v1", "event_id": "event-crash", "idempotency_key": "crash:" + intent["intent_id"], "verdict": "allow", "turn_id": "crash", "operations": [], "after_state_hash": after["state_hash"]}
        self.store.append_event(event); self.store.write_journal({"event_id": "event-crash", "idempotency_key": event["idempotency_key"], "after_state_hash": after["state_hash"], "after_state": after})
        self.assertEqual(recover_store(self.store)["status"], "reconciled_state_from_event")
        self.assertEqual(self.store.load_state()["state_hash"], after["state_hash"])

    def test_recovery_rebuilds_all_transaction_sidecars(self):
        before = self.store.load_state()
        after = dict(before); after["revision"] = int(before["revision"]) + 1; after["last_turn_id"] = "sidecars"; after["events_head"] = "head-sidecars"; refresh_state_hash(after)
        intent = make_intent("player", "observe", turn_id="sidecars")
        event = {"schema": "minis.world-event.v1", "event_id": "event-sidecars", "idempotency_key": "sidecars:" + intent["intent_id"], "verdict": "allow", "turn_id": "sidecars", "operations": [], "after_state_hash": after["state_hash"]}
        turn = {"schema": "minis.interactive-turn-record.v1", "turn_id": "sidecars", "status": "committed"}
        audit = {"turn_id": "sidecars", "verdict": "allow"}
        patch = {"schema": "minis.graph-patch.v1", "patch_id": "p", "turn_id": "sidecars", "event_id": "event-sidecars", "branch_id": "main", "changes": [], "requires_promotion": True}
        self.store.append_event(event)
        self.store.write_journal({"turn_id": "sidecars", "event_id": "event-sidecars", "idempotency_key": event["idempotency_key"], "after_state_hash": after["state_hash"], "after_state": after, "turn": turn, "audit": audit, "patch": patch, "status": "committed"})
        report = recover_store(self.store)
        self.assertEqual(report["status"], "reconciled_state_from_event")
        self.assertTrue((self.store.turns_dir / "sidecars.json").exists())
        self.assertTrue((self.store.audit_dir / "sidecars.json").exists())
        self.assertTrue((self.store.patch_dir / "sidecars.json").exists())
        self.assertEqual(self.store.load_manifest()["head_event_id"], "event-sidecars")

    def test_memory_retrieval_reflection_and_context_are_externalized(self):
        episode_a = make_episode("npc", event_id="e1", turn_id="t1", text="在房間看見硬幣", tags=["coin", "room"], importance=2, tick=1)
        episode_b = make_episode("npc", event_id="e2", turn_id="t2", text="硬幣後來不見了", tags=["coin"], importance=4, tick=2)
        state = add_episode(add_episode(self.initial, episode_a), episode_b)
        hits = retrieve_memories(state, "npc", query="硬幣 coin", top_k=2)
        self.assertEqual(len(hits), 2)
        reflection = {"actor_id": "npc", "text": "硬幣可能被移動", "evidence_memory_ids": [episode_a["memory_id"], episode_b["memory_id"]]}
        self.assertTrue(validate_reflection(state, reflection)["ok"])
        packet = compile_model_task(state, task="npc_plan", actor_id="npc", input_text="下一步")
        self.assertFalse(packet["authority"]["may_commit_state"])
        self.assertIn("memory_context", packet["context"])

    def test_weak_model_task_contract_and_graph_projection(self):
        packet = compile_model_task(self.initial, task="render", actor_id="player", input_text="觀察")
        good = {"text": "房裡很安靜。", "claimed_facts": [], "action_manifest": [], "player_actions": [], "task_hash": packet["task_hash"]}
        self.assertTrue(validate_model_result(packet, good)["ok"])
        self.assertFalse(validate_model_result(packet, {"text": "x"})["ok"])
        commit_turn(self.store, make_intent("player", "observe", turn_id="projection"))
        graph = project_events(self.store.read_events(), project_id="acceptance", session_id="session", branch_id="main")
        self.assertTrue(any(n["entity_type"] == "event" for n in graph["nodes"]))
        self.assertTrue(any(e["relation"] == "performed" for e in graph["links"]))

    def test_branch_transaction_lock_is_reentrant_across_turns(self):
        first = commit_turn(self.store, make_intent("player", "observe", turn_id="lock-1"))
        second = commit_turn(self.store, make_intent("player", "observe", turn_id="lock-2"), expected_state_hash=first["post_state_hash"])
        self.assertEqual(second["status"], "committed")

if __name__ == "__main__": unittest.main()
