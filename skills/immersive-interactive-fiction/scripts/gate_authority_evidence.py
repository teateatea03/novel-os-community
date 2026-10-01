#!/usr/bin/env python3
from __future__ import annotations

"""Produce adversarial Step 2 Gate-authority evidence in isolated shadows."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from novel_judge import ProjectRuntimeAdapter, empty_state, make_gate_envelope
from novel_judge.canonical import refresh_state_hash, sha256_json


def initial(project: str) -> dict:
    state = empty_state(project, "step2-session")
    state["canon_scope"] = "experiment"
    state["actors"] = {"world": {"kind": "world", "location": "fixture", "status": {}, "commitments": []}}
    state["world_truth"]["locations"] = {"fixture": {"connections": {}}}
    return refresh_state_hash(state)


def setup(root: Path, project: str) -> tuple[ProjectRuntimeAdapter, dict]:
    adapter = ProjectRuntimeAdapter(root, project, "step2-session")
    state = initial(project)
    adapter.initialize(
        state,
        baseline_id="step2-baseline",
        provenance={"shadow": True, "purpose": "Step 2 Gate authority evidence; never production canon"},
        migration_authorized=True,
    )
    return adapter, state


def scene_hash(turn: str) -> str:
    return hashlib.sha256(("step2-scene:" + turn).encode()).hexdigest()


def bundle(adapter: ProjectRuntimeAdapter, turn: str, state_hash: str, *, fail_gate: str | None = None) -> list[dict]:
    result = []
    for gate in adapter.gate_policy()["required_gate_types"]:
        kwargs = {}
        if gate == fail_gate:
            kwargs = {"verdict": "FAIL", "severity": "P0", "findings": [{"code": "PLAYER_AGENCY_BREACH" if gate == "interactive_agency" else f"{gate.upper()}_P0"}]}
        result.append(make_gate_envelope(
            gate_type=gate,
            turn_id=turn,
            scene_sha256=scene_hash(turn),
            source_state_hash=state_hash,
            **kwargs,
        ))
    return result


def rejected(call) -> dict:
    try:
        call()
    except Exception as exc:
        return {"blocked": True, "type": type(exc).__name__, "code": getattr(exc, "code", None), "message": str(exc)}
    return {"blocked": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if root.exists() and any(root.iterdir()):
        parser.error("--root must not exist or must be empty; remove the prior shadow explicitly")
    root.mkdir(parents=True, exist_ok=True)
    cases: dict[str, object] = {}

    # Exact sixth-review bypass: a validly hashed interactive-agency FAIL/P0 artifact.
    a, state = setup(root / "original-bypass", "step2-original-bypass")
    turn = "BYPASS-P0"
    envs = bundle(a, turn, state["state_hash"], fail_gate="interactive_agency")
    approve_result = rejected(lambda: a.approve_gate_bundle(
        turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=envs,
    ))
    commit_result = rejected(lambda: a.commit(
        turn_id=turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn),
    ))
    cases["original_interactive_agency_p0_bypass"] = {
        "approve": approve_result,
        "commit": commit_result,
        "event_count": len(a.store.read_events()),
        "ok": approve_result["blocked"] and commit_result["blocked"] and len(a.store.read_events()) == 0,
    }

    # Required missing Gate.
    a, state = setup(root / "missing", "step2-missing")
    turn = "MISSING-GATE"
    envs = bundle(a, turn, state["state_hash"])
    envs = [entry for entry in envs if entry["payload"]["gate_type"] != "interactive_agency"]
    approve_result = rejected(lambda: a.approve_gate_bundle(
        turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=envs,
    ))
    commit_result = rejected(lambda: a.commit(
        turn_id=turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn),
    ))
    cases["missing_gate"] = {"approve": approve_result, "commit": commit_result, "ok": approve_result["blocked"] and commit_result["blocked"]}

    # Invalid schema.
    a, state = setup(root / "schema", "step2-schema")
    turn = "BAD-SCHEMA"
    envs = bundle(a, turn, state["state_hash"])
    envs[0]["schema"] = "invalid"
    schema_result = rejected(lambda: a.approve_gate_bundle(
        turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=envs,
    ))
    cases["bad_schema"] = {**schema_result, "ok": schema_result["blocked"]}

    # Approved bundle hash drift before commit.
    a, state = setup(root / "hash-drift", "step2-hash-drift")
    turn = "HASH-DRIFT"
    a.approve_gate_bundle(turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=bundle(a, turn, state["state_hash"]))
    path = a.gate_bundle_dir / f"{turn}.json"
    value = json.loads(path.read_text())
    value["created_at"] = "tampered-after-approval"
    path.write_text(json.dumps(value))
    drift_result = rejected(lambda: a.commit(
        turn_id=turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn),
    ))
    cases["hash_drift"] = {**drift_result, "event_count": len(a.store.read_events()), "ok": drift_result["blocked"] and len(a.store.read_events()) == 0}

    # Authorization stale after another valid commit advances state.
    a, state = setup(root / "stale", "step2-stale")
    old_turn, new_turn = "STALE-OLD", "STALE-NEW"
    a.approve_gate_bundle(turn_id=old_turn, scene_sha256=scene_hash(old_turn), source_state_hash=state["state_hash"], envelopes=bundle(a, old_turn, state["state_hash"]))
    a.approve_gate_bundle(turn_id=new_turn, scene_sha256=scene_hash(new_turn), source_state_hash=state["state_hash"], envelopes=bundle(a, new_turn, state["state_hash"]))
    a.commit(turn_id=new_turn, operations=[{"op": "replace", "path": "/clock/tick", "value": 1}], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(new_turn))
    stale_result = rejected(lambda: a.commit(turn_id=old_turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(old_turn)))
    cases["state_stale"] = {**stale_result, "event_count": len(a.store.read_events()), "ok": stale_result["blocked"] and len(a.store.read_events()) == 1}

    # Clean PASS path and complete HEAD evidence projection.
    a, state = setup(root / "pass", "step2-pass")
    turn = "PASS-ALL"
    authorization = a.approve_gate_bundle(turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=bundle(a, turn, state["state_hash"]))
    result = a.commit(turn_id=turn, operations=[{"op": "replace", "path": "/clock/tick", "value": 1}], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn))
    head = json.loads(a.runtime_head_path.read_text())
    required = a.gate_policy()["required_gate_types"]
    projected = [entry["gate_type"] for entry in head["gate_bundle"]["gates"]]
    pass_ok = result["status"] == "committed" and projected == required and head["gate_bundle"]["authorization_hash"] == authorization["authorization_hash"] and a.assert_conformant()["status"] == "pass"
    cases["pass_fixture"] = {
        "status": result["status"],
        "authorization_hash": authorization["authorization_hash"],
        "event_authorization_hash": result["event"]["gate_authorization_hash"],
        "head_required_gate_types": head["gate_bundle"]["required_gate_types"],
        "head_projected_gate_types": projected,
        "interactive_agency": next(x for x in head["gate_bundle"]["gates"] if x["gate_type"] == "interactive_agency"),
        "conformance": a.assert_conformant()["status"],
        "ok": pass_ok,
    }

    # Per-required-Gate positive/negative/tamper/stale matrix.
    matrix = []
    for gate in required:
        row = {"gate_type": gate}
        a, state = setup(root / "matrix" / gate / "positive", f"step2-{gate}-positive")
        turn = f"POS-{gate}"
        a.approve_gate_bundle(turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=bundle(a, turn, state["state_hash"]))
        positive = a.commit(turn_id=turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn))
        row["positive"] = positive["status"] == "committed"

        a, state = setup(root / "matrix" / gate / "negative", f"step2-{gate}-negative")
        turn = f"NEG-{gate}"
        neg = rejected(lambda a=a, state=state, turn=turn, gate=gate: a.approve_gate_bundle(
            turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=bundle(a, turn, state["state_hash"], fail_gate=gate),
        ))
        row["negative"] = neg

        a, state = setup(root / "matrix" / gate / "tamper", f"step2-{gate}-tamper")
        turn = f"TAMPER-{gate}"
        a.approve_gate_bundle(turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=bundle(a, turn, state["state_hash"]))
        path = a.gate_bundle_dir / f"{turn}.json"
        value = json.loads(path.read_text())
        target = next(x for x in value["envelopes"] if x["payload"]["gate_type"] == gate)
        target["payload"]["details"]["tampered"] = True
        value["bundle_hash"] = sha256_json({k: v for k, v in value.items() if k != "bundle_hash"})
        path.write_text(json.dumps(value))
        tamper = rejected(lambda a=a, state=state, turn=turn: a.commit(turn_id=turn, operations=[], expected_state_hash=state["state_hash"], scene_sha256=scene_hash(turn)))
        row["tamper"] = tamper

        a, state = setup(root / "matrix" / gate / "stale", f"step2-{gate}-stale")
        turn = f"SOURCE-{gate}"
        envs = bundle(a, turn, state["state_hash"])
        target = next(x for x in envs if x["payload"]["gate_type"] == gate)
        target["payload"]["source_state_hash"] = "sha256:" + "0" * 64
        target["payload_hash"] = sha256_json(target["payload"])
        target["envelope_hash"] = sha256_json({k: v for k, v in target.items() if k != "envelope_hash"})
        stale = rejected(lambda a=a, state=state, turn=turn, envs=envs: a.approve_gate_bundle(
            turn_id=turn, scene_sha256=scene_hash(turn), source_state_hash=state["state_hash"], envelopes=envs,
        ))
        row["stale"] = stale
        row["ok"] = row["positive"] and neg["blocked"] and tamper["blocked"] and stale["blocked"]
        matrix.append(row)

    report = {
        "schema": "minis.gate-authority-step2-evidence.v1",
        "shadow_root": str(root),
        "production_cutover": False,
        "required_gate_types": required,
        "cases": cases,
        "required_gate_matrix": matrix,
    }
    report["ok"] = all(bool(case.get("ok")) for case in cases.values()) and all(row["ok"] for row in matrix)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
