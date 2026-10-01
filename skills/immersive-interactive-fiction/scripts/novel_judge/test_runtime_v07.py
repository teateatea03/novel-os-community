from __future__ import annotations

import tempfile
import unittest

from .canonical import refresh_state_hash
from .engine import commit_turn, replay_events
from .intent import make_intent
from .model_activities import claim_model_activity, complete_model_activity, recover_model_activities, schedule_model_activity
from .model_tasks import compile_model_task
from .runtime_versioning import RUNTIME_BUILD, replay_compatibility_report
from .state import empty_state
from .store import FileStore
from .story_solver import solve_storylets


def fixture() -> dict:
    state = empty_state("v07", "s")
    state["actors"] = {"player": {"kind": "player", "location": "room", "status": {}, "commitments": []}}
    return refresh_state_hash(state)


class RuntimeV07Tests(unittest.TestCase):
    def test_new_events_stamp_runtime_contract_and_legacy_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v07", "s"); initial = fixture(); store.save_state(initial)
            commit_turn(store, make_intent("player", "wait", turn_id="t1", parameters={"seconds": 1}))
            event = store.read_events()[0]
            self.assertEqual(event["runtime_build"], RUNTIME_BUILD)
            self.assertEqual(event["transition_contract"], "minis.transition-contract.v1")
            self.assertEqual(replay_events(initial, [event])["state_hash"], store.load_state()["state_hash"])
            fixture_doc = __import__("novel_judge.runtime_versioning", fromlist=["make_replay_fixture"]).make_replay_fixture(initial, [event], store.load_state()["state_hash"])
            self.assertEqual(fixture_doc["expected_state_hash"], replay_events(fixture_doc["initial_state"], fixture_doc["events"])["state_hash"])
            legacy = dict(event); legacy.pop("runtime_build"); legacy.pop("transition_contract")
            self.assertEqual(replay_compatibility_report([legacy])["status"], "pass")

    def test_unknown_event_contract_fails_closed(self):
        event = {"schema": "minis.world-event.v1", "event_id": "e", "verdict": "reject", "transition_contract": "future-v99"}
        report = replay_compatibility_report([event]); self.assertEqual(report["status"], "blocked")
        with self.assertRaises(Exception): replay_events(fixture(), [event])

    def test_model_activity_retries_invalid_result_then_completes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v07", "s"); store.save_state(fixture())
            packet = compile_model_task(store.load_state(), task="render", actor_id="player", approved_manifest={"scene_function": "test"})
            activity = schedule_model_activity(store, packet, max_attempts=2)
            claimed = claim_model_activity(store, activity["activity_id"], worker_id="w")
            self.assertEqual(claimed["attempt"], 1)
            retry = complete_model_activity(store, activity["activity_id"], worker_id="w", lease_token=claimed["lease_token"], result={"task_hash": packet["task_hash"]})
            self.assertEqual(retry["status"], "scheduled")
            claimed = claim_model_activity(store, activity["activity_id"], worker_id="w")
            result = {"task_hash": packet["task_hash"], "text": "門開了。", "claimed_facts": [], "action_manifest": [], "player_actions": []}
            done = complete_model_activity(store, activity["activity_id"], worker_id="w", lease_token=claimed["lease_token"], result=result)
            self.assertEqual(done["status"], "completed")

    def test_model_activity_stale_state_and_expired_lease(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v07", "s"); store.save_state(fixture())
            packet = compile_model_task(store.load_state(), task="blind_read", actor_id="player")
            activity = schedule_model_activity(store, packet, max_attempts=2)
            claim_model_activity(store, activity["activity_id"], worker_id="w", lease_seconds=1)
            recovery = recover_model_activities(store, at="2999-01-01T00:00:00Z")
            self.assertIn(activity["activity_id"], recovery["recovered"])
            claimed = claim_model_activity(store, activity["activity_id"], worker_id="w")
            changed = store.load_state(); changed["clock"]["tick"] = 1; store.save_state(refresh_state_hash(changed))
            result = {"task_hash": packet["task_hash"], "status": "pass", "issues": [], "summary": "ok"}
            stale = complete_model_activity(store, activity["activity_id"], worker_id="w", lease_token=claimed["lease_token"], result=result)
            self.assertEqual(stale["status"], "stale")

    def test_schema_valid_render_rejects_hash_leak_and_safety_narration(self):
        packet = {"task": "render", "task_hash": "sha256:q", "source_state_hash": "s"}
        bad = {"task_hash": "sha256:q", "text": "你靜坐。你未起身、未開門。task_hash=sha256:q", "claimed_facts": [], "action_manifest": ["sha256:q"], "player_actions": []}
        report = __import__("novel_judge.model_tasks", fromlist=["validate_model_result"]).validate_model_result(packet, bad)
        codes = {x["code"] for x in report["errors"]}
        self.assertIn("MODEL_RESULT_TASK_HASH_LEAK_IN_PROSE", codes)
        self.assertIn("MODEL_RESULT_NEGATIVE_SAFETY_NARRATION", codes)

    def test_author_console_blocks_pending_activity(self):
        from .author_console import author_console_report
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v07", "s"); store.save_state(fixture())
            packet = compile_model_task(store.load_state(), task="render", actor_id="player")
            schedule_model_activity(store, packet)
            report = author_console_report(store)
            self.assertIn("PENDING_MODEL_ACTIVITY", report["blockers"])

    def test_archive_tamper_is_rejected_even_without_index(self):
        from .event_log import verify_event_log_integrity
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v07", "s"); store.save_state(fixture())
            for n in range(4): commit_turn(store, make_intent("player", "wait", turn_id=f"a{n}", parameters={"seconds": 1}))
            store.compact_events(retain_active=1)
            manifest = store._read_json(store.events_dir / "event-log-manifest.json"); archive = store.events_dir / manifest["archives"][0]["file"]
            data = archive.read_bytes(); archive.write_bytes(data.replace(b'"action_type":"wait"', b'"action_type":"wAit"', 1))
            if store.events_index_path.exists(): store.events_index_path.unlink()
            self.assertEqual(verify_event_log_integrity(store)["status"], "blocked")
            with self.assertRaises(ValueError): store.find_event(event_id="anything")

    def test_story_solver_finds_unreachable_and_soft_lock(self):
        state = fixture(); state["threads"]["open"] = [{"id": "goal"}]
        state["storylets"]["active"] = [
            {"id": "start", "conditions": {"state_equals": {"clock.tick": 0}}, "effects": [{"op": "replace", "path": "/clock/tick", "value": 1}], "next_storylets": ["middle"]},
            {"id": "middle", "conditions": {"state_equals": {"clock.tick": 1}}, "effects": [{"op": "replace", "path": "/clock/tick", "value": 2}]},
            {"id": "never", "conditions": {"state_equals": {"clock.tick": 99}}, "effects": []},
            {"id": "broken", "conditions": {"state_equals": {"clock.tick": 99}}, "next_storylets": ["missing"], "effects": []},
        ]
        state = refresh_state_hash(state); report = solve_storylets(state, actor_id="player")
        codes = {x["code"] for x in report["issues"]}
        self.assertIn("UNREACHABLE_STORYLET", codes); self.assertIn("BROKEN_STORYLET_TARGET", codes); self.assertIn("SOFT_LOCK", codes)
        self.assertIn("start", report["reachable"]); self.assertIn("middle", report["reachable"])


if __name__ == "__main__": unittest.main()
