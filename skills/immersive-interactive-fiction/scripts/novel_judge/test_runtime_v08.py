from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from .canonical import refresh_state_hash
from .random_events import (
    calibrate_random_event_pool, load_random_event_settings, make_adoption_handoff,
    random_event_health, request_random_suggestion, set_random_event_mode,
    suggest_random_event, validate_random_event_pool,
)
from .state import empty_state
from .store import FileStore

POOL_PATH = Path(__file__).resolve().parents[2] / "references" / "random-event-starter-pool.json"


def fixture() -> dict:
    state = empty_state("v08", "s")
    state["actors"] = {
        "player": {"kind": "player", "location": "station", "status": {}, "commitments": []},
        "n1": {"kind": "npc", "location": "station", "tags": ["random_hook_eligible"], "status": {}},
        "n2": {"kind": "npc", "location": "elsewhere", "tags": ["background_simulation_eligible"], "status": {}},
    }
    state["threads"]["open"] = [{"id": "missing-letter"}]
    return refresh_state_hash(state)


def pool() -> dict:
    return json.loads(POOL_PATH.read_text(encoding="utf-8"))


class RuntimeV08RandomEventTests(unittest.TestCase):
    def test_default_is_off_and_does_not_draw_or_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v08", "s"); store.save_state(fixture())
            result = request_random_suggestion(store, {"not": "a pool"}, trigger="scene_boundary", seed=1)
            self.assertEqual(result["status"], "off"); self.assertFalse(result["draw_performed"])
            self.assertFalse((store.base / "random-events" / "suggestion-audit.jsonl").exists())
            self.assertEqual(load_random_event_settings(store)["mode"], "off")

    def test_only_user_or_author_can_enable(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v08", "s")
            with self.assertRaises(Exception): set_random_event_mode(store, "on-suggestion", changed_by="model")
            self.assertEqual(set_random_event_mode(store, "on-suggestion", changed_by="user")["mode"], "on-suggestion")

    def test_suggestion_never_mutates_canonical_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v08", "s"); store.save_state(fixture()); before = copy.deepcopy(store.load_state())
            set_random_event_mode(store, "on-suggestion")
            result = request_random_suggestion(store, pool(), trigger="scene_boundary", seed=4, window={"natural_break": True})
            self.assertIn(result["status"], {"suggested", "no_event"})
            self.assertEqual(before, store.load_state())
            for key in ("state_delta", "graph_patch", "knowledge_patch", "prose_patch"): self.assertEqual(result[key], [])
            self.assertEqual(len(store.read_events()), 0)

    def test_meta_and_unfinished_high_intensity_are_suppressed(self):
        p = pool(); state = fixture()
        meta = suggest_random_event(state, p, trigger="scene_boundary", seed=1, window={"input_kind": "meta"})
        self.assertEqual(meta["status"], "suppressed")
        peak = suggest_random_event(state, p, trigger="scene_boundary", seed=1, window={"high_intensity_active": True, "natural_break": False})
        self.assertEqual(peak["status"], "suppressed")

    def test_deterministic_consequence_prevents_oracle_pile_on(self):
        result = suggest_random_event(fixture(), pool(), trigger="action_resolution", seed=1,
                                      window={"randomness_needed": True, "deterministic_consequence_available": True})
        self.assertEqual(result["status"], "suppressed")
        self.assertIn("deterministic_consequence_available", result["suppression_reasons"])

    def test_role_binding_happens_before_selection(self):
        p = pool(); p["events"] = [x for x in p["events"] if x["id"] == "character-hook-opportunity"]; p["no_event_weight"] = 1
        state = fixture(); state["actors"]["n1"]["tags"] = []
        result = suggest_random_event(refresh_state_hash(state), p, trigger="travel", seed=1, window={})
        self.assertEqual(result["status"], "no_event"); self.assertEqual(result["reason"], "empty_eligible_pool")
        self.assertIn("role_unbound:focus_npc", result["rejected"][0]["reasons"])

    def test_same_seed_and_state_reproduce_draw(self):
        p = pool(); state = fixture(); window = {"natural_break": True}
        a = suggest_random_event(state, p, trigger="scene_boundary", seed="replay", window=window)
        b = suggest_random_event(state, p, trigger="scene_boundary", seed="replay", window=window)
        self.assertEqual(a, b)

    def test_no_event_is_a_real_weighted_result(self):
        p = pool(); p["events"] = [p["events"][0]]; p["events"][0]["frequency_weight"] = 1; p["no_event_weight"] = 100000
        results = [suggest_random_event(fixture(), p, trigger="scene_boundary", seed=n, window={"natural_break": True}) for n in range(20)]
        self.assertTrue(any(x["status"] == "no_event" and x.get("reason") == "weighted_no_event" for x in results))

    def test_pool_rejects_decisive_player_or_irreversible_result(self):
        p = pool(); p["events"][0]["pressure_direction"] = "你必須接受，某人已背叛你"
        report = validate_random_event_pool(p)
        self.assertFalse(report["ok"]); self.assertIn("RANDOM_EVENT_DECISIVE_OUTCOME", {x["code"] for x in report["errors"]})

    def test_adoption_is_still_noncanonical_and_requires_all_gates(self):
        p = pool(); state = fixture(); result = None
        for seed in range(100):
            candidate = suggest_random_event(state, p, trigger="scene_boundary", seed=seed, window={"natural_break": True})
            if candidate["status"] == "suggested": result = candidate; break
        self.assertIsNotNone(result)
        handoff = make_adoption_handoff(state, result["suggestion"], requested_by="user")
        self.assertEqual(handoff["canon_status"], "NON_CANONICAL"); self.assertEqual(handoff["state_delta"], [])
        self.assertIn("PlayerAgency", handoff["required_gates"]); self.assertIn("Canon", handoff["required_gates"])

    def test_audit_is_separate_and_integrity_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v08", "s"); store.save_state(fixture()); set_random_event_mode(store, "on-suggestion")
            request_random_suggestion(store, pool(), trigger="scene_boundary", seed=2, window={"natural_break": True})
            health = random_event_health(store)
            self.assertEqual(health["status"], "pass"); self.assertEqual(health["noncanonical_audit_records"], 1)
            self.assertEqual(store.read_events(), [])

    def test_author_console_exposes_mode_and_audit_health(self):
        from .author_console import author_console_report
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "v08", "s"); store.save_state(fixture()); set_random_event_mode(store, "on-suggestion")
            report = author_console_report(store)
            self.assertEqual(report["random_events"]["mode"], "on-suggestion")
            self.assertEqual(report["random_events"]["noncanonical_audit_records"], 0)

    def test_calibration_reports_distribution_without_writes(self):
        state = fixture(); before = copy.deepcopy(state)
        report = calibrate_random_event_pool(state, pool(), trigger="scene_boundary", seeds=200, window={"natural_break": True})
        self.assertEqual(report["seeds"], 200); self.assertAlmostEqual(sum(report["rates"].values()), 1.0)
        self.assertEqual(state, before)


if __name__ == "__main__": unittest.main()
