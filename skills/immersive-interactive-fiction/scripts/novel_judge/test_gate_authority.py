from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash, sha256_json
from .errors import GATE_AUTHORIZATION_FAILED, GATE_ENVELOPE_INVALID, GATE_OVERRIDE_INVALID, JudgeError
from .gate_authority import default_gate_policy, make_author_override, make_gate_envelope
from .production import ProjectRuntimeAdapter
from .state import empty_state


def fixture() -> dict:
    state = empty_state("gate-authority", "session")
    state["canon_scope"] = "experiment"
    state["actors"] = {"world": {"kind": "world", "location": "room", "status": {}, "commitments": []}}
    state["world_truth"]["locations"] = {"room": {"connections": {}}}
    return refresh_state_hash(state)


def setup(root: str) -> tuple[ProjectRuntimeAdapter, dict]:
    a = ProjectRuntimeAdapter(root, "gate-authority", "session"); state = fixture()
    a.initialize(state, baseline_id="baseline", provenance={"shadow": True, "source": "step2-test"}, migration_authorized=True)
    return a, state


def scene_hash(turn: str) -> str:
    return hashlib.sha256(("scene:" + turn).encode()).hexdigest()


def envelopes(a: ProjectRuntimeAdapter, *, turn: str, state_hash: str,
              mutate: dict[str, dict] | None = None) -> list[dict]:
    out=[]; mutate=mutate or {}
    for gate in a.gate_policy()["required_gate_types"]:
        kw={"gate_type":gate,"turn_id":turn,"scene_sha256":scene_hash(turn),"source_state_hash":state_hash}
        kw.update(mutate.get(gate,{})); out.append(make_gate_envelope(**kw))
    return out


class GateAuthorityTests(unittest.TestCase):
    def test_all_pass_bundle_approves_and_commit_revalidates(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G0001"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
            auth=a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            result=a.commit(turn_id=turn,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
            self.assertEqual(auth["decision"],"AUTHORIZED"); self.assertEqual(result["status"],"committed")
            self.assertEqual(result["event"]["scene"],None)
            self.assertEqual(result["intent"]["parameters"]["gate_authorization_hash"],auth["authorization_hash"])

    def test_each_required_gate_has_positive_and_fail_p0_regression(self):
        required = default_gate_policy()["required_gate_types"]
        for gate in required:
            with self.subTest(gate=gate, case="pass"), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn=f"PASS-{gate}"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
                auth=a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
                result=a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
                self.assertEqual(auth["decision"],"AUTHORIZED"); self.assertEqual(result["status"],"committed")
            with self.subTest(gate=gate, case="fail_p0"), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn=f"FAIL-{gate}"
                envs=envelopes(a,turn=turn,state_hash=state["state_hash"],mutate={gate:{"verdict":"FAIL","severity":"P0","findings":[{"code":f"{gate.upper()}_P0"}]}})
                with self.assertRaises(JudgeError) as cm:
                    a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
                self.assertEqual(cm.exception.code,GATE_AUTHORIZATION_FAILED)

    def test_each_required_gate_has_tamper_and_stale_regression(self):
        required = default_gate_policy()["required_gate_types"]
        for gate in required:
            with self.subTest(gate=gate, case="tamper"), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn=f"TAMPER-{gate}"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
                path=a.gate_bundle_dir/f"{turn}.json"; bundle=json.loads(path.read_text())
                target=next(x for x in bundle["envelopes"] if x["payload"]["gate_type"]==gate)
                target["payload"]["details"]["tampered"]=True
                bundle["bundle_hash"]=sha256_json({k:v for k,v in bundle.items() if k!="bundle_hash"}); path.write_text(json.dumps(bundle))
                with self.assertRaises(JudgeError):
                    a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
            with self.subTest(gate=gate, case="stale"), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn=f"STALE-{gate}"; stale="sha256:"+"0"*64
                envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
                target=next(x for x in envs if x["payload"]["gate_type"]==gate)
                target["payload"]["source_state_hash"]=stale
                target["payload_hash"]=sha256_json(target["payload"])
                target["envelope_hash"]=sha256_json({k:v for k,v in target.items() if k!="envelope_hash"})
                with self.assertRaises(JudgeError) as cm:
                    a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
                self.assertEqual(cm.exception.code,GATE_ENVELOPE_INVALID)

    def test_missing_gate_fails_at_approval_and_commit_without_bundle_fails(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G0002"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"]); envs.pop()
            with self.assertRaises(JudgeError) as cm:
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            self.assertEqual(cm.exception.code,GATE_AUTHORIZATION_FAILED)
            with self.assertRaises(JudgeError) as cm:
                a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
            self.assertEqual(cm.exception.code,GATE_AUTHORIZATION_FAILED)

    def test_fail_and_p0_gate_cannot_be_overridden(self):
        for gate in ("interactive_agency","reality"):
            with self.subTest(gate=gate), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn="G0003"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"],mutate={gate:{"verdict":"FAIL","severity":"P0","findings":[{"code":"P0_BREACH"}]}})
                failed=next(x for x in envs if x["payload"]["gate_type"]==gate)
                override=make_author_override(envelope=failed,author_id="author",reason="try",finding_codes=["P0_BREACH"])
                with self.assertRaises(JudgeError):
                    a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs,overrides=[override])

    def test_warn_requires_hash_bound_author_override(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G0004"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"],mutate={"prose":{"verdict":"WARN","severity":"P1","findings":[{"code":"STYLE_WARN"}]}})
            warned=next(x for x in envs if x["payload"]["gate_type"]=="prose")
            with self.assertRaises(JudgeError):
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            override=make_author_override(envelope=warned,author_id="author",reason="accepted localized style risk",finding_codes=["STYLE_WARN"])
            auth=a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs,overrides=[override])
            self.assertEqual(auth["decision"],"AUTHORIZED")

    def test_override_requires_explicit_complete_finding_scope(self):
        for codes in ([], ["STYLE_ONE"]):
            with self.subTest(codes=codes), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn="G0005"
                envs=envelopes(a,turn=turn,state_hash=state["state_hash"],mutate={"prose":{"verdict":"WARN","severity":"P1","findings":[{"code":"STYLE_ONE"},{"code":"STYLE_TWO"}]}})
                warned=next(x for x in envs if x["payload"]["gate_type"]=="prose")
                override=make_author_override(envelope=warned,author_id="author",reason="scoped decision",finding_codes=codes)
                with self.assertRaises(JudgeError) as cm:
                    a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs,overrides=[override])
                self.assertEqual(cm.exception.code,GATE_OVERRIDE_INVALID)

    def test_bad_schema_runner_payload_hash_scene_and_state_fail_closed(self):
        mutators=[]
        mutators.append(lambda e: e.update(schema="bad"))
        mutators.append(lambda e: e["runner"].update(id="untrusted.runner"))
        mutators.append(lambda e: e["payload"].update(verdict="PASS",severity="P0"))
        mutators.append(lambda e: e.update(payload_hash="sha256:bad"))
        mutators.append(lambda e: e["payload"].update(scene_sha256="0"*64))
        mutators.append(lambda e: e["payload"].update(source_state_hash="sha256:"+"0"*64))
        for n,mutate in enumerate(mutators):
            with self.subTest(n=n), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn=f"G1{n:03d}"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"]); mutate(envs[0])
                with self.assertRaises(JudgeError):
                    a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)

    def test_gate_policy_tamper_and_duplicate_approval_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G1500"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
            a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            with self.assertRaises(JudgeError):
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            policy=json.loads(a.gate_policy_path.read_text()); policy["required_gate_types"].remove("interactive_agency"); a.gate_policy_path.write_text(json.dumps(policy))
            with self.assertRaises(JudgeError):
                a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))

    def test_canonical_event_and_projections_preserve_authorization_hash(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G1600"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
            auth=a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
            event=a.store.read_events()[-1]; head=json.loads(a.runtime_head_path.read_text()); project=json.loads(a.project_pointer_path.read_text())
            self.assertEqual(event["gate_authorization_hash"],auth["authorization_hash"])
            self.assertEqual(head["gate_authorization_hash"],auth["authorization_hash"])
            self.assertEqual(head["gate_bundle"]["authorization_hash"],auth["authorization_hash"])
            self.assertEqual(head["gate_bundle"]["required_gate_types"],a.gate_policy()["required_gate_types"])
            self.assertEqual([x["gate_type"] for x in head["gate_bundle"]["gates"]],a.gate_policy()["required_gate_types"])
            self.assertEqual(next(x for x in head["gate_bundle"]["gates"] if x["gate_type"]=="interactive_agency")["verdict"],"PASS")
            self.assertEqual(project["production_authority"]["gate_authorization_hash"],auth["authorization_hash"])
            self.assertEqual(a.assert_conformant()["status"],"pass")

    def test_commit_detects_bundle_envelope_authorization_override_and_artifact_tamper(self):
        cases=("bundle","envelope","authorization")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as root:
                a,state=setup(root); turn="G2001"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
                b=a.gate_bundle_dir/f"{turn}.json"; r=a.gate_authorization_dir/f"{turn}.json"
                if case=="bundle":
                    d=json.loads(b.read_text()); d["created_at"]="tampered"; b.write_text(json.dumps(d))
                elif case=="envelope":
                    d=json.loads(b.read_text()); d["envelopes"][0]["payload"]["details"]["x"]=1
                    d["bundle_hash"]=sha256_json({k:v for k,v in d.items() if k!="bundle_hash"}); b.write_text(json.dumps(d))
                else:
                    d=json.loads(r.read_text()); d["issued_at"]="tampered"; r.write_text(json.dumps(d))
                with self.assertRaises(JudgeError):
                    a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G2002"; artifact=Path(root)/"gate.txt"; artifact.write_text("ok")
            binding={"path":"gate.txt","sha256":hashlib.sha256(artifact.read_bytes()).hexdigest()}
            envs=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],artifact=binding if g=="prose" else None) for g in a.gate_policy()["required_gate_types"]]
            a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs); artifact.write_text("tampered")
            with self.assertRaises(JudgeError): a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))

    def test_stale_state_after_approval_blocks_commit(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G3001"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"])
            a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            other="G3000"; other_env=envelopes(a,turn=other,state_hash=state["state_hash"]); a.approve_gate_bundle(turn_id=other,scene_sha256=scene_hash(other),source_state_hash=state["state_hash"],envelopes=other_env)
            a.commit(turn_id=other,operations=[{"op":"replace","path":"/clock/tick","value":1}],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(other))
            with self.assertRaises(JudgeError): a.commit(turn_id=turn,operations=[],expected_state_hash=state["state_hash"],scene_sha256=scene_hash(turn))

    def test_original_interactive_agency_bypass_probe_is_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            a,state=setup(root); turn="G4001"; envs=envelopes(a,turn=turn,state_hash=state["state_hash"],mutate={"interactive_agency":{"verdict":"FAIL","severity":"P0","findings":[{"code":"PLAYER_AGENCY_BREACH"}]}})
            with self.assertRaises(JudgeError) as cm:
                a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash(turn),source_state_hash=state["state_hash"],envelopes=envs)
            self.assertEqual(cm.exception.code,GATE_AUTHORIZATION_FAILED)
            self.assertEqual(len(a.store.read_events()),0)


if __name__=="__main__": unittest.main()
