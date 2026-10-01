#!/usr/bin/env python3
from __future__ import annotations

"""Create and exercise an isolated ProjectRuntimeAdapter shadow fixture."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from novel_judge import ProjectRuntimeAdapter, empty_state, make_gate_envelope
from novel_judge.canonical import refresh_state_hash


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--root", required=True); p.add_argument("--turn", default="S0001")
    args = p.parse_args(); root = Path(args.root).resolve()
    adapter = ProjectRuntimeAdapter(root, "step1-shadow", "shadow-session")
    state = empty_state("step1-shadow", "shadow-session")
    state["canon_scope"] = "experiment"
    state["actors"] = {"world": {"kind": "world", "location": "fixture", "status": {}, "commitments": []}}
    state["world_truth"]["locations"] = {"fixture": {"connections": {}}}
    state = refresh_state_hash(state)
    if not adapter.authority_record():
        adapter.initialize(state, baseline_id="step1-baseline",
                           provenance={"shadow": True, "purpose": "Step 1 isolated conformance; never production canon"},
                           migration_authorized=True)
    before = adapter.store.load_state()
    import hashlib
    scene_sha256 = hashlib.sha256(f"shadow scene {args.turn}".encode()).hexdigest()
    envelopes = [make_gate_envelope(gate_type=gate, turn_id=args.turn,
                                    scene_sha256=scene_sha256, source_state_hash=before["state_hash"])
                 for gate in adapter.gate_policy()["required_gate_types"]]
    adapter.approve_gate_bundle(turn_id=args.turn, scene_sha256=scene_sha256,
                                source_state_hash=before["state_hash"], envelopes=envelopes)
    result = adapter.commit(turn_id=args.turn,
                            operations=[{"op": "replace", "path": "/clock/tick", "value": int(before["clock"]["tick"]) + 1}],
                            expected_state_hash=before["state_hash"], scene_sha256=scene_sha256)
    print(json.dumps({"commit": {"turn_id": result["turn_id"], "status": result["status"]},
                      "conformance": adapter.assert_conformant()}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
