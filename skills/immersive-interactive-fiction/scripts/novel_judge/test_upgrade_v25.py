from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash, sha256_json
from .random_events import random_event_health, request_random_suggestion, set_random_event_mode
from .state import empty_state
from .store import FileStore

POOL = Path(__file__).resolve().parents[2] / "references" / "random-event-starter-pool.json"


class UpgradeV25Tests(unittest.TestCase):
    def test_v25_audit_chain_is_readable_but_legacy_id_is_reserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "upgrade", "s"); state = empty_state("upgrade", "s")
            state["actors"] = {"player": {"kind": "player", "location": "x", "status": {}, "commitments": []}}
            store.save_state(refresh_state_hash(state)); set_random_event_mode(store, "on-suggestion")
            root = store.base / "random-events"; root.mkdir(exist_ok=True)
            record = {"schema": "minis.random-event-suggestion-audit.v1", "recorded_at": "2026-08-09T00:00:00Z", "request_id": "legacy-r1", "mode": "on-suggestion", "branch_id": "main",
                      "result": {"schema": "minis.random-event-draw.v1", "status": "no_event", "source_state_hash": store.load_state()["state_hash"]}, "previous_audit_hash": None}
            record["audit_hash"] = sha256_json(record)
            (root / "suggestion-audit.jsonl").write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            store._atomic_json(root / "audit-manifest.json", {"schema": "minis.random-event-audit-manifest.v1", "record_count": 1, "head_hash": record["audit_hash"]})
            self.assertEqual(random_event_health(store)["status"], "pass")
            pool = json.loads(POOL.read_text(encoding="utf-8"))
            with self.assertRaisesRegex(Exception, "legacy request_id"):
                request_random_suggestion(store, pool, trigger="scene_boundary", seed=1, window={"natural_break": True}, request_id="legacy-r1")
            fresh = request_random_suggestion(store, pool, trigger="scene_boundary", seed=1, window={"natural_break": True}, request_id="new-r2")
            self.assertEqual(fresh["request_id"], "new-r2"); self.assertEqual(random_event_health(store)["noncanonical_audit_records"], 2)


if __name__ == "__main__": unittest.main()
