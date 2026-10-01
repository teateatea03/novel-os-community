from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash
from .event_log import verify_event_log_integrity
from .model_activities import claim_model_activity, complete_model_activity, recover_model_activities, schedule_model_activity
from .model_tasks import compile_model_task
from .random_events import random_event_health, recover_random_event_audit, request_random_suggestion, set_random_event_mode
from .state import empty_state
from .store import FileStore

POOL_PATH = Path(__file__).resolve().parents[2] / "references" / "random-event-starter-pool.json"
PACKAGE_ROOT = str(Path(__file__).resolve().parents[1])


def fixture() -> dict:
    state = empty_state("v10", "s")
    state["actors"] = {"player": {"kind": "player", "location": "station", "status": {}, "commitments": []},
                       "n1": {"kind": "npc", "location": "station", "tags": ["random_hook_eligible"], "status": {}}}
    state["threads"]["open"] = [{"id": "thread"}]
    return refresh_state_hash(state)


def worker_script(root: str, mode: str) -> str:
    return f'''import json,sys\nsys.path.insert(0,{PACKAGE_ROOT!r})\nfrom novel_judge import *\nfrom novel_judge.canonical import refresh_state_hash\nroot={root!r}\ns=FileStore(root,"v10","s")\npool=json.load(open({str(POOL_PATH)!r},encoding="utf-8"))\nif {mode!r}=="request": request_random_suggestion(s,pool,trigger="scene_boundary",seed=4,window={{"natural_break":True}},request_id="kill-r1")\n'''


class RuntimeV10Tests(unittest.TestCase):
    def test_request_fingerprint_replay_and_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v10", "s"); store.save_state(fixture()); set_random_event_mode(store, "on-suggestion")
            pool = json.loads(POOL_PATH.read_text(encoding="utf-8")); kwargs = {"trigger": "scene_boundary", "seed": 4, "window": {"natural_break": True}, "request_id": "r1"}
            first = request_random_suggestion(store, pool, **kwargs); second = request_random_suggestion(store, pool, **kwargs)
            self.assertTrue(second["replayed_from_audit"]); self.assertEqual(first["request_fingerprint"], second["request_fingerprint"])
            with self.assertRaisesRegex(Exception, "request_id"):
                request_random_suggestion(store, pool, trigger="scene_boundary", seed=5, window={"natural_break": True}, request_id="r1")
            self.assertEqual(random_event_health(store)["noncanonical_audit_records"], 1)

    def test_activity_v1_running_migrates_and_old_worker_is_fenced(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v10", "s"); store.save_state(fixture())
            packet = compile_model_task(store.load_state(), task="blind_read", actor_id="player")
            rec = schedule_model_activity(store, packet, max_attempts=3); path = store.base / "model-activities" / f"{rec['activity_id']}.json"
            legacy = json.loads(path.read_text()); legacy.update({"schema": "minis.model-activity.v1", "status": "running", "lease_owner": "old", "lease_expires_at": "2999-01-01T00:00:00Z"}); legacy.pop("lease_token", None); store._atomic_json(path, legacy)
            recovered = recover_model_activities(store); self.assertIn(rec["activity_id"], recovered["pending"])
            migrated = json.loads(path.read_text()); self.assertEqual(migrated["status"], "scheduled"); self.assertEqual(migrated["migrated_from"], "minis.model-activity.v1")
            result = {"task_hash": packet["task_hash"], "status": "pass", "issues": [], "summary": "ok"}
            with self.assertRaises(ValueError): complete_model_activity(store, rec["activity_id"], worker_id="old", result=result)
            fresh = claim_model_activity(store, rec["activity_id"], worker_id="new")
            self.assertEqual(complete_model_activity(store, rec["activity_id"], worker_id="new", lease_token=fresh["lease_token"], result=result)["status"], "completed")

    def test_event_integrity_verification_has_zero_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v10", "s"); store.save_state(fixture())
            def snapshot(): return {str(p.relative_to(store.base)): (p.stat().st_mtime_ns, p.read_bytes()) for p in store.base.rglob("*") if p.is_file()}
            before = snapshot(); verify_event_log_integrity(store); after = snapshot(); self.assertEqual(before, after)
            self.assertFalse((store.events_dir / ".active-extension-check.jsonl").exists())

    def test_random_audit_real_sigkill_matrix_recovers_exactly_once(self):
        for point in ("random_audit_after_journal", "random_audit_after_append", "random_audit_after_manifest"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "v10", "s"); store.save_state(fixture()); set_random_event_mode(store, "on-suggestion")
                env = os.environ.copy(); env["PYTHONPATH"] = PACKAGE_ROOT; env["NOVEL_JUDGE_SIGKILL_AT"] = point
                proc = subprocess.run([sys.executable, "-c", worker_script(tmp, "request")], env=env)
                self.assertEqual(proc.returncode, -9)
                with store.transaction_lock(): recovery = recover_random_event_audit(store)
                self.assertTrue(recovery["recovered"]); self.assertEqual(random_event_health(store)["status"], "pass")
                pool = json.loads(POOL_PATH.read_text(encoding="utf-8")); replay = request_random_suggestion(store, pool, trigger="scene_boundary", seed=4, window={"natural_break": True}, request_id="kill-r1")
                self.assertTrue(replay["replayed_from_audit"]); self.assertEqual(random_event_health(store)["noncanonical_audit_records"], 1)


    def test_event_active_manifest_real_sigkill_matrix_replays(self):
        event_worker = f'''import sys\nsys.path.insert(0,{PACKAGE_ROOT!r})\nfrom novel_judge import FileStore,make_intent,commit_turn\ns=FileStore(sys.argv[1],"v10","s")\ncommit_turn(s,make_intent("player","wait",turn_id="event-kill",parameters={{"seconds":1}}))\n'''
        for point in ("event_after_append", "event_after_active_manifest", "event_after_index"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "v10", "s"); initial = fixture(); store.save_state(initial)
                env = os.environ.copy(); env["PYTHONPATH"] = PACKAGE_ROOT; env["NOVEL_JUDGE_SIGKILL_AT"] = point
                proc = subprocess.run([sys.executable, "-c", event_worker, tmp], env=env); self.assertEqual(proc.returncode, -9)
                from .engine import recover_store, replay_events
                with store.transaction_lock(): recovery = recover_store(store)
                self.assertTrue(recovery["recovered"]); events = store.read_events(); self.assertEqual(len(events), 1)
                self.assertEqual(store.load_state()["state_hash"], replay_events(initial, events)["state_hash"])
                self.assertEqual(verify_event_log_integrity(store)["status"], "pass"); self.assertIsNone(store.load_journal())

    def test_activity_real_sigkill_schedule_claim_complete_and_migration(self):
        activity_worker = f'''import json,sys\nsys.path.insert(0,{PACKAGE_ROOT!r})\nfrom novel_judge import *\ns=FileStore(sys.argv[1],"v10","s"); mode=sys.argv[2]\npacket=compile_model_task(s.load_state(),task="blind_read",actor_id="player")\nif mode=="schedule": schedule_model_activity(s,packet,max_attempts=4)\nelse:\n aid=sys.argv[3]\n if mode=="claim": claim_model_activity(s,aid,worker_id="kill-worker")\n elif mode=="complete":\n  rec=json.load(open(s.base/"model-activities"/(aid+".json"),encoding="utf-8")); result={{"task_hash":packet["task_hash"],"status":"pass","issues":[],"summary":"ok"}}; complete_model_activity(s,aid,worker_id=rec["lease_owner"],lease_token=rec["lease_token"],result=result)\n elif mode=="migrate": recover_model_activities(s)\n'''
        for mode, point in (("schedule", "activity_after_schedule"), ("claim", "activity_after_claim"), ("complete", "activity_after_complete"), ("migrate", "activity_after_migration")):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "v10", "s"); store.save_state(fixture()); packet = compile_model_task(store.load_state(), task="blind_read", actor_id="player")
                aid = ""
                if mode != "schedule":
                    rec = schedule_model_activity(store, packet, max_attempts=4); aid = rec["activity_id"]
                    if mode == "complete": claim_model_activity(store, aid, worker_id="kill-worker")
                    if mode == "migrate":
                        path = store.base / "model-activities" / f"{aid}.json"; legacy = json.loads(path.read_text()); legacy["schema"] = "minis.model-activity.v1"; store._atomic_json(path, legacy)
                env = os.environ.copy(); env["PYTHONPATH"] = PACKAGE_ROOT; env["NOVEL_JUDGE_SIGKILL_AT"] = point
                proc = subprocess.run([sys.executable, "-c", activity_worker, tmp, mode, aid], env=env); self.assertEqual(proc.returncode, -9)
                directory = store.base / "model-activities"; files = list(directory.glob("*.json")); self.assertEqual(len(files), 1)
                durable = json.loads(files[0].read_text()); self.assertEqual(durable["schema"], "minis.model-activity.v2")
                if mode == "schedule": self.assertEqual(durable["status"], "scheduled")
                elif mode == "claim": self.assertEqual(durable["status"], "running"); self.assertTrue(durable["lease_token"])
                elif mode == "complete": self.assertEqual(durable["status"], "completed")
                else: self.assertEqual(durable["migrated_from"], "minis.model-activity.v1")


if __name__ == "__main__": unittest.main()
