from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash
from .errors import JudgeError, PRODUCTION_AUTHORITY_REQUIRED
from .production import COMMIT_API, ProjectRuntimeAdapter
from .state import empty_state
from .gate_authority import make_gate_envelope

PACKAGE_ROOT = str(Path(__file__).resolve().parents[1])


def fixture(project: str = "production-fixture", session: str = "session") -> dict:
    state = empty_state(project, session)
    state["canon_scope"] = "canon"
    state["actors"] = {
        "world": {"kind": "world", "location": "room", "status": {}, "commitments": []},
        "player": {"kind": "player", "location": "room", "status": {}, "commitments": []},
    }
    state["world_truth"]["locations"] = {"room": {"connections": {}}}
    return refresh_state_hash(state)


def adapter(root: str) -> ProjectRuntimeAdapter:
    return ProjectRuntimeAdapter(root, "production-fixture", "session")


def initialize(root: str) -> tuple[ProjectRuntimeAdapter, dict]:
    a = adapter(root); state = fixture()
    a.initialize(state, baseline_id="baseline", provenance={"shadow": True, "source": "test"}, migration_authorized=True)
    return a, state


def approve(a: ProjectRuntimeAdapter, turn: str, state_hash: str) -> str:
    import hashlib
    scene_hash = hashlib.sha256(("scene:" + turn).encode()).hexdigest()
    envelopes = [make_gate_envelope(gate_type=gate, turn_id=turn, scene_sha256=scene_hash,
                                    source_state_hash=state_hash)
                 for gate in a.gate_policy()["required_gate_types"]]
    a.approve_gate_bundle(turn_id=turn, scene_sha256=scene_hash,
                          source_state_hash=state_hash, envelopes=envelopes)
    return scene_hash


WORKER = r'''
import json,sys
sys.path.insert(0,sys.argv[1])
from novel_judge import ProjectRuntimeAdapter,make_gate_envelope
root,expected,turn=sys.argv[2:5]
a=ProjectRuntimeAdapter(root,"production-fixture","session")
try:
 scene=__import__('hashlib').sha256(("scene:"+turn).encode()).hexdigest()
 envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene,source_state_hash=expected) for g in a.gate_policy()["required_gate_types"]]
 a.approve_gate_bundle(turn_id=turn,scene_sha256=scene,source_state_hash=expected,envelopes=envs)
 r=a.commit(turn_id=turn,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=expected,scene_sha256=scene)
 print(json.dumps({"kind":"ok","state_hash":r["post_state_hash"]}))
except Exception as e:
 print(json.dumps({"kind":"error","type":type(e).__name__,"message":str(e)}))
'''

KILL_WORKER = r'''
import sys
sys.path.insert(0,sys.argv[1])
from novel_judge import ProjectRuntimeAdapter,make_gate_envelope
root,expected,point=sys.argv[2:5]
a=ProjectRuntimeAdapter(root,"production-fixture","session")
turn="kill-"+point
scene=__import__('hashlib').sha256(("scene:"+turn).encode()).hexdigest()
envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene,source_state_hash=expected) for g in a.gate_policy()["required_gate_types"]]
a.approve_gate_bundle(turn_id=turn,scene_sha256=scene,source_state_hash=expected,envelopes=envs)
a.commit(turn_id=turn,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=expected,scene_sha256=scene)
'''


class ProductionAuthorityConformanceTests(unittest.TestCase):
    def test_requires_explicit_one_time_migration_authority(self):
        with tempfile.TemporaryDirectory() as root:
            a = adapter(root)
            with self.assertRaises(JudgeError) as cm:
                a.initialize(fixture(), baseline_id="baseline", provenance={})
            self.assertEqual(cm.exception.code, PRODUCTION_AUTHORITY_REQUIRED)
            with self.assertRaises(JudgeError) as cm:
                a.initialize(fixture(), baseline_id="baseline", provenance={"shadow": False}, migration_authorized=True)
            self.assertEqual(cm.exception.code, PRODUCTION_AUTHORITY_REQUIRED)
            a.initialize(fixture(), baseline_id="baseline", provenance={"shadow": True}, migration_authorized=True)
            with self.assertRaises(JudgeError):
                a.initialize(fixture(), baseline_id="again", provenance={"shadow": True}, migration_authorized=True)

    def test_one_commit_api_and_direct_store_mutations_are_fenced(self):
        with tempfile.TemporaryDirectory() as root:
            a, initial = initialize(root)
            self.assertEqual(a.authority_record()["canonical_commit_api"], COMMIT_API)
            with self.assertRaises(JudgeError): a.store.save_state(initial)
            with self.assertRaises(JudgeError): a.store.append_event({"event_id": "bypass"})
            with self.assertRaises(JudgeError): a.store.update_head({}, initial)
            from .store import FileStore
            bypass = FileStore(root, "production-fixture", "session")
            with self.assertRaises(JudgeError): bypass.save_state(initial)
            with self.assertRaises(JudgeError): bypass.append_event({"event_id": "cross-instance-bypass"})
            with self.assertRaises(JudgeError): bypass.write_checkpoint("bypass", initial)
            with self.assertRaises(JudgeError): bypass.save_turn({"turn_id": "bypass"})
            with self.assertRaises(JudgeError): bypass.write_journal({"turn_id": "bypass"})
            with self.assertRaises(JudgeError): bypass.save_workflow({"status": "bypass"})
            with self.assertRaises(JudgeError): bypass.compact_events()
            from .engine import commit_turn, recover_store
            from .intent import make_intent
            with self.assertRaises(JudgeError): commit_turn(bypass, make_intent("world", "world_tick", turn_id="bypass", source="author", parameters={"operations": []}), expected_state_hash=initial["state_hash"], source="author")
            with self.assertRaises(JudgeError): recover_store(bypass)
            scene_hash = approve(a, "T0001", initial["state_hash"])
            result = a.commit(turn_id="T0001", operations=[{"op": "replace", "path": "/clock/tick", "value": 1}], expected_state_hash=initial["state_hash"], scene_sha256=scene_hash)
            self.assertEqual(result["status"], "committed")

    def test_normal_commit_synchronizes_event_state_manifest_head_and_project(self):
        with tempfile.TemporaryDirectory() as root:
            a, initial = initialize(root)
            scene_hash = approve(a, "T0001", initial["state_hash"])
            r = a.commit(turn_id="T0001", operations=[{"op": "replace", "path": "/clock/tick", "value": 3}], expected_state_hash=initial["state_hash"], scene_sha256=scene_hash)
            state = a.store.load_state(); events = a.store.read_events(); manifest = a.store.load_manifest()
            head = json.loads((Path(root) / "runtime-head.json").read_text())
            project = json.loads((Path(root) / "project.json").read_text())
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event_id"], r["event"]["event_id"])
            self.assertEqual(manifest["head_state_hash"], state["state_hash"])
            self.assertEqual(head["state_hash"], state["state_hash"])
            self.assertEqual(head["event_head"], state["events_head"])
            self.assertEqual(project["production_authority"]["state_hash"], state["state_hash"])
            self.assertEqual(a.assert_conformant()["status"], "pass")

    def test_two_processes_one_source_hash_exactly_one_commit(self):
        with tempfile.TemporaryDirectory() as root:
            a, initial = initialize(root); expected = initial["state_hash"]
            procs = [subprocess.Popen([sys.executable, "-c", WORKER, PACKAGE_ROOT, root, expected, f"T000{n}"], stdout=subprocess.PIPE, text=True) for n in (1, 2)]
            out = [json.loads(p.communicate(timeout=30)[0]) for p in procs]
            self.assertEqual(sum(x["kind"] == "ok" for x in out), 1)
            self.assertEqual(sum("stale" in x.get("message", "") for x in out), 1)
            self.assertEqual(len(a.store.read_events()), 1)
            self.assertEqual(a.assert_conformant()["status"], "pass")

    def test_real_sigkill_matrix_recovers_all_authority_projections(self):
        points = ("event_after_append", "event_after_active_manifest", "event_after_index",
                  "production_after_state", "production_after_head", "production_after_runtime_head",
                  "production_after_project_pointer")
        for point in points:
            with self.subTest(point=point), tempfile.TemporaryDirectory() as root:
                a, initial = initialize(root); env = os.environ.copy(); env["NOVEL_JUDGE_SIGKILL_AT"] = point
                proc = subprocess.run([sys.executable, "-c", KILL_WORKER, PACKAGE_ROOT, root, initial["state_hash"], point], env=env)
                self.assertIn(proc.returncode, {-signal.SIGKILL, 128 + signal.SIGKILL, 137})
                recovery = a.recover()
                if point == "production_after_project_pointer":
                    self.assertEqual(recovery["status"], "clean")
                else:
                    self.assertTrue(recovery["recovered"])
                self.assertIsNone(a.store.load_journal())
                self.assertEqual(a.assert_conformant()["status"], "pass")
                self.assertEqual(len(a.store.read_events()), 1)
    def test_rejected_audit_tail_does_not_replace_canonical_head(self):
        with tempfile.TemporaryDirectory() as root:
            a, initial = initialize(root); scene_hash = approve(a, "T-REJECT", initial["state_hash"])
            with self.assertRaises(JudgeError):
                a.commit(turn_id="T-REJECT", operations=[], expected_state_hash=initial["state_hash"], actor_id="missing", action_type="meta", scene_sha256=scene_hash)
            self.assertEqual(a.store.read_events()[-1]["verdict"], "reject")
            self.assertEqual(a.store.load_state()["state_hash"], initial["state_hash"])
            self.assertEqual(a.assert_conformant()["status"], "pass")


if __name__ == "__main__": unittest.main()
