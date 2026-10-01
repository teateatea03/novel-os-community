from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash
from .engine import commit_turn
from .event_log import verify_event_log_integrity
from .intent import make_intent
from .model_activities import claim_model_activity, complete_model_activity, recover_model_activities, schedule_model_activity
from .model_tasks import compile_model_task
from .random_events import make_adoption_handoff, random_event_health, request_random_suggestion, set_random_event_mode
from .state import empty_state
from .store import FileStore

POOL_PATH = Path(__file__).resolve().parents[2] / "references" / "random-event-starter-pool.json"


def fixture() -> dict:
    state = empty_state("v09", "s")
    state["actors"] = {"player": {"kind": "player", "location": "station", "status": {}, "commitments": []},
                       "n1": {"kind": "npc", "location": "station", "tags": ["random_hook_eligible"], "status": {}}}
    state["threads"]["open"] = [{"id": "thread"}]
    return refresh_state_hash(state)


class RuntimeV09Tests(unittest.TestCase):
    def test_active_segment_tamper_fails_after_index_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v09", "s"); store.save_state(fixture())
            commit_turn(store, make_intent("player", "wait", turn_id="t", parameters={"seconds": 1}))
            store.events_index_path.unlink()
            raw = store.events_path.read_bytes(); store.events_path.write_bytes(raw.replace(b'"action_type":"wait"', b'"action_type":"wAit"', 1))
            self.assertEqual(verify_event_log_integrity(store)["status"], "blocked")
            with self.assertRaises(ValueError): store.read_events()

    def test_v24_fresh_index_can_upgrade_active_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v09", "s"); store.save_state(fixture())
            commit_turn(store, make_intent("player", "wait", turn_id="t1", parameters={"seconds": 1}))
            manifest_path = store.events_dir / "event-log-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8")); manifest.pop("active_segment", None)
            store._atomic_json(manifest_path, manifest)
            commit_turn(store, make_intent("player", "wait", turn_id="t2", parameters={"seconds": 1}))
            upgraded = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertIn("active_segment", upgraded); self.assertEqual(len(store.read_events()), 2)

    def test_path_identifiers_are_single_safe_segments(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError): FileStore(tmp, "v09", "../session")
            store = FileStore(tmp, "v09", "s"); store.save_state(fixture())
            with self.assertRaises(ValueError): store.save_turn({"turn_id": "../../escape"})
            with self.assertRaises(ValueError): store.write_checkpoint("../escape", fixture())

    def test_activity_fencing_rejects_old_and_missing_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v09", "s"); store.save_state(fixture())
            packet = compile_model_task(store.load_state(), task="blind_read", actor_id="player")
            activity = schedule_model_activity(store, packet, max_attempts=3)
            first = claim_model_activity(store, activity["activity_id"], worker_id="same", lease_seconds=1)
            recover_model_activities(store, at="2999-01-01T00:00:00Z")
            second = claim_model_activity(store, activity["activity_id"], worker_id="same")
            result = {"task_hash": packet["task_hash"], "status": "pass", "issues": [], "summary": "ok"}
            with self.assertRaises(ValueError): complete_model_activity(store, activity["activity_id"], worker_id="same", lease_token=first["lease_token"], result=result)
            with self.assertRaises(ValueError): complete_model_activity(store, activity["activity_id"], worker_id="same", result=result)
            done = complete_model_activity(store, activity["activity_id"], worker_id="same", lease_token=second["lease_token"], result=result)
            self.assertEqual(done["status"], "completed")

    def test_random_request_is_idempotent_and_audit_is_chained(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v09", "s"); store.save_state(fixture()); set_random_event_mode(store, "on-suggestion")
            pool = json.loads(POOL_PATH.read_text(encoding="utf-8")); window = {"natural_break": True}
            first = request_random_suggestion(store, pool, trigger="scene_boundary", seed=4, window=window, request_id="r1")
            second = request_random_suggestion(store, pool, trigger="scene_boundary", seed=4, window=window, request_id="r1")
            self.assertEqual(first.get("suggestion"), second.get("suggestion")); self.assertTrue(second["replayed_from_audit"])
            with self.assertRaises(Exception): request_random_suggestion(store, pool, trigger="scene_boundary", seed=999, window=window, request_id="r1")
            self.assertEqual(random_event_health(store)["noncanonical_audit_records"], 1)
            audit = store.base / "random-events" / "suggestion-audit.jsonl"
            lines = audit.read_text(encoding="utf-8").splitlines(); value = json.loads(lines[0]); value["result"]["status"] = "tampered"
            audit.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
            self.assertEqual(random_event_health(store)["status"], "warning")

    def test_stale_suggestion_cannot_create_adoption_handoff(self):
        pool = json.loads(POOL_PATH.read_text(encoding="utf-8")); state = fixture(); suggestion = None
        for seed in range(100):
            with tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "v09", "s"); store.save_state(state); set_random_event_mode(store, "on-suggestion")
                result = request_random_suggestion(store, pool, trigger="scene_boundary", seed=seed, window={"natural_break": True})
                if result["status"] == "suggested": suggestion = result["suggestion"]; break
        self.assertIsNotNone(suggestion)
        changed = dict(state); changed["clock"] = dict(state["clock"]); changed["clock"]["tick"] += 1; changed = refresh_state_hash(changed)
        with self.assertRaises(Exception): make_adoption_handoff(changed, suggestion, requested_by="user")


if __name__ == "__main__": unittest.main()
