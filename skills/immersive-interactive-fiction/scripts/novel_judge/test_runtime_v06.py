from __future__ import annotations

import random
import tempfile
import unittest

from .canonical import refresh_state_hash
from .engine import commit_turn, replay_events
from .event_log import build_event_index, inspect_jsonl
from .graph_projector import project_events
from .intent import make_intent
from .longform import commit_scene_event, init_longform_state, longform_store
from .longform_projector import project_longform_markdown, projection_status
from .model_tasks import validate_model_result
from .state import empty_state
from .store import FileStore


def fixture() -> dict:
    s = empty_state("fuzz", "s"); s["actors"] = {"player": {"kind": "player", "location": "a", "status": {}, "commitments": []}}
    s["world_truth"]["locations"] = {"a": {"connections": {"b": {"to": "b", "open": True}}}, "b": {"connections": {"a": {"to": "a", "open": True}}}}
    return refresh_state_hash(s)


class RuntimeV06Tests(unittest.TestCase):
    def test_seeded_fuzz_replay_and_index(self):
        for seed in range(12):
            rnd = random.Random(seed)
            with tempfile.TemporaryDirectory() as tmp:
                store = FileStore(tmp, "fuzz", "s"); initial = fixture(); store.save_state(initial)
                for n in range(35):
                    current = store.load_state(); here = current["actors"]["player"]["location"]
                    if rnd.random() < .35: intent = make_intent("player", "move", turn_id=f"{seed}-{n}", targets=["b" if here == "a" else "a"])
                    else: intent = make_intent("player", "wait", turn_id=f"{seed}-{n}", parameters={"seconds": rnd.randint(0, 5)})
                    commit_turn(store, intent, expected_state_hash=current["state_hash"])
                events = store.read_events(); self.assertEqual(len(events), 35)
                self.assertEqual(replay_events(initial, events)["state_hash"], store.load_state()["state_hash"])
                index = build_event_index(store); self.assertEqual(index["event_count"], 35)
                sample = rnd.choice(events); self.assertEqual(store.find_event(event_id=sample["event_id"])["event_id"], sample["event_id"])

    def test_corrupt_tail_repair_backs_up_and_preserves_valid_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "p", "s"); initial = fixture(); store.save_state(initial)
            for n in range(3): commit_turn(store, make_intent("player", "wait", turn_id=f"t{n}", parameters={"seconds": 1}))
            valid = store.read_events();
            with store.events_path.open("ab") as fh: fh.write(b'{"broken":')
            self.assertEqual(inspect_jsonl(store.events_path)["status"], "corrupt_tail")
            with self.assertRaises(ValueError): store.read_events()
            report = store.repair_events(); self.assertTrue(report["repaired"]); self.assertTrue(report["backup"])
            self.assertEqual(store.read_events(), valid); self.assertEqual(inspect_jsonl(store.events_path)["status"], "clean")

    def test_middle_corruption_refuses_automatic_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "p", "s"); store.save_state(fixture())
            for n in range(3): commit_turn(store, make_intent("player", "wait", turn_id=f"t{n}", parameters={"seconds": 1}))
            lines = store.events_path.read_bytes().splitlines(keepends=True); lines[1] = b"not-json\n"; store.events_path.write_bytes(b"".join(lines))
            self.assertEqual(inspect_jsonl(store.events_path)["status"], "corrupt_middle")
            with self.assertRaises(ValueError): store.repair_events()

    def test_compaction_keeps_hash_order_and_index_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "p", "s"); initial = fixture(); store.save_state(initial)
            for n in range(12): commit_turn(store, make_intent("player", "wait", turn_id=f"t{n}", parameters={"seconds": 1}))
            before = store.read_events(); report = store.compact_events(retain_active=4)
            self.assertEqual(report["archived"], 8); self.assertEqual(store.read_events(), before)
            self.assertEqual(replay_events(initial, store.read_events())["state_hash"], store.load_state()["state_hash"])
            self.assertEqual(store.find_event(event_id=before[0]["event_id"])["event_id"], before[0]["event_id"])

    def test_event_maintenance_journal_rolls_back_partial_compaction(self):
        from .event_log import recover_event_maintenance
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "p", "s"); store.save_state(fixture())
            for n in range(3): commit_turn(store, make_intent("player", "wait", turn_id=f"t{n}", parameters={"seconds": 1}))
            original = store.events_path.read_bytes(); backup = store.events_dir / "manual-backup.bak"; backup.write_bytes(original)
            archive = store.events_dir / "partial-archive.jsonl"; archive.write_text("partial", encoding="utf-8")
            store.events_path.write_text("broken", encoding="utf-8")
            store._atomic_json(store.events_dir / "event-maintenance.json", {"operation": "compact", "active_backup": str(backup), "previous_manifest": None, "new_archive": str(archive)})
            report = recover_event_maintenance(store); self.assertTrue(report["recovered"])
            self.assertEqual(store.events_path.read_bytes(), original); self.assertFalse(archive.exists())

    def test_same_size_log_tamper_invalidates_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = FileStore(tmp, "p", "s"); store.save_state(fixture()); commit_turn(store, make_intent("player", "wait", turn_id="t", parameters={"seconds": 1}))
            event = store.read_events()[0]; build_event_index(store)
            data = store.events_path.read_bytes(); marker = str(event["event_id"]).encode(); replacement = b"x" * len(marker)
            store.events_path.write_bytes(data.replace(marker, replacement, 1))
            with self.assertRaises(ValueError): store.find_event(event_id=event["event_id"])

    def test_temporal_projection_invalidates_old_location(self):
        events = [{"event_id": "e1", "turn_id": "t1", "actor_id": "a", "action_type": "move", "verdict": "allow", "created_at": "1", "operations": [{"op": "replace", "path": "/actors/a/location", "value": "x"}]},
                  {"event_id": "e2", "turn_id": "t2", "actor_id": "a", "action_type": "move", "verdict": "allow", "created_at": "2", "operations": [{"op": "replace", "path": "/actors/a/location", "value": "y"}]}]
        graph = project_events(events, project_id="p", session_id="s", branch_id="main")
        located = [x for x in graph["links"] if x.get("relation") == "located_in"]
        self.assertEqual(len(located), 2); self.assertEqual(sum(x["status"] == "active" for x in located), 1)
        old = next(x for x in located if x["target"] == "location:x"); self.assertEqual(old["valid_to"], "2"); self.assertEqual(old["invalidated_by_event_id"], "e2")

    def test_longform_projection_rebuild_and_stale_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = longform_store(tmp, "novel"); initial = init_longform_state("novel"); store.save_state(initial)
            result = commit_scene_event(store, scene_id="s1", chapter_id="ch1", operations=[{"op": "add", "path": "/world_truth/events/s1", "value": {"summary": "門打開"}}], summary="門打開", author_approved=True, expected_state_hash=initial["state_hash"])
            manifest = project_longform_markdown(store, tmp); self.assertFalse(projection_status(store, tmp)["stale"])
            from pathlib import Path
            self.assertIn("門打開", Path(tmp, "timeline.md").read_text(encoding="utf-8"))
            with open(f"{tmp}/timeline.md", "a", encoding="utf-8") as fh: fh.write("manual edit")
            self.assertTrue(projection_status(store, tmp)["stale"])

    def test_point_in_time_query_and_author_console_html(self):
        from .temporal_graph import project_temporal_relations, query_relations_at
        from .author_console_html import write_author_console_html
        from pathlib import Path
        events = [{"event_id": "e1", "verdict": "allow", "created_at": "1", "operations": [{"op": "replace", "path": "/actors/a/location", "value": "x"}]},
                  {"event_id": "e2", "verdict": "allow", "created_at": "2", "operations": [{"op": "replace", "path": "/actors/a/location", "value": "y"}]}]
        edges = project_temporal_relations(events); self.assertEqual(query_relations_at(edges, "1", source="actor:a")[0]["target"], "location:x")
        self.assertEqual(query_relations_at(edges, "2", source="actor:a")[0]["target"], "location:y")
        with tempfile.TemporaryDirectory() as tmp:
            store = longform_store(tmp, "novel"); state = init_longform_state("novel"); store.save_state(state)
            project_longform_markdown(store, tmp); output = Path(tmp, "console.html")
            report = write_author_console_html(store, output, project_root=tmp); self.assertEqual(report["status"], "pass"); self.assertIn("Author Console", output.read_text(encoding="utf-8"))

    def test_semantics_reject_invalid_intent_and_confidence(self):
        packet = {"task": "intent_extract", "task_hash": "h", "source_state_hash": "s"}
        bad = {"type": "imperative", "targets": ["continue_task"], "parameters": {}, "confidence": 100, "ambiguities": [], "task_hash": "h"}
        report = validate_model_result(packet, bad); codes = {x["code"] for x in report["errors"]}
        self.assertIn("MODEL_RESULT_INVALID_INTENT_TYPE", codes); self.assertIn("MODEL_RESULT_INVALID_CONFIDENCE", codes)


if __name__ == "__main__": unittest.main()
