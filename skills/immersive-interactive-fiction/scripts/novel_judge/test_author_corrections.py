#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from .author_corrections import (
    append_correction,
    recommend_action,
    active_guards,
    read_corrections,
    attach_author_corrections,
    project_quality_dir,
)


class AuthorCorrectionTests(unittest.TestCase):
    def test_one_off_stays_note(self):
        self.assertEqual(recommend_action({"one_off": True, "reason_codes": ["pacing"]}), "note")

    def test_character_continuity_promotes_to_guard(self):
        card = {
            "reason_codes": ["continuity", "character_voice"],
            "character_id": "actor_b",
            "bad_excerpt": "不知姓名的來訪者",
            "accepted_excerpt": "觀測員，備用鏡頭已經編好號了。",
        }
        self.assertEqual(recommend_action(card), "character_guard")

    def test_human_voice_pair_becomes_rejected_fixture(self):
        card = {
            "reason_codes": ["human_voice", "pacing"],
            "bad_excerpt": "不是猶豫，而是對每一道刻度都負責的慎重",
            "accepted_excerpt": "技術員把游標移回零點。",
        }
        self.assertEqual(recommend_action(card), "rejected_fixture")

    def test_append_and_filter_promoted(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "interactive").mkdir()
            note = append_correction(
                root,
                {
                    "title": "單次口味",
                    "rule": "這段再短一點",
                    "reason_codes": ["pacing"],
                    "one_off": True,
                    "status": "note",
                },
            )
            promoted = append_correction(
                root,
                {
                    "title": "角色乙見熟人直接喊",
                    "rule": "角色乙看見已認識的人時直接打招呼，不得先當陌生人觀察",
                    "reason_codes": ["continuity", "character_voice"],
                    "character_id": "actor_b",
                    "status": "promoted",
                    "recommended_action": "character_guard",
                    "applies_when": {"character_id": "actor_b"},
                    "bad_excerpt": "不知姓名的來訪者",
                    "accepted_excerpt": "觀測員，備用鏡頭已經編好號了。",
                },
            )
            rows = read_corrections(root)
            self.assertEqual(len(rows), 2)
            self.assertEqual(note["status"], "note")
            self.assertEqual(promoted["recommended_action"], "character_guard")
            guards = active_guards(root, character_id="actor_b")
            self.assertEqual(len(guards), 1)
            self.assertEqual(guards[0]["event_id"], promoted["event_id"])
            empty = active_guards(root, character_id="actor_c")
            self.assertEqual(empty, [])
            manifest = json.loads((project_quality_dir(root) / "author-corrections-manifest.json").read_text())
            self.assertEqual(manifest["event_count"], 2)
            self.assertEqual(manifest["promoted_count"], 1)
            packed = attach_author_corrections({}, root, character_ids=["actor_b"])
            self.assertEqual(len(packed["author_corrections"]), 1)
            self.assertIn("直接打招呼", packed["author_correction_notes"])
            skipped = attach_author_corrections({}, root, character_ids=["actor_c"])
            self.assertNotIn("author_corrections", skipped)

    def test_scene_kind_guard_does_not_leak_into_other_scenes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "interactive").mkdir()
            append_correction(
                root,
                {
                    "title": "校準場景刪旁白解釋",
                    "rule": "校準用可見的工具操作寫，不得用旁白替角色解釋",
                    "reason_codes": ["human_voice", "pacing"],
                    "status": "promoted",
                    "recommended_action": "rejected_fixture",
                    "applies_when": {"scene_kind": "calibration"},
                    "bad_excerpt": "不是猶豫",
                    "accepted_excerpt": "技術員把游標移回零點。",
                },
            )
            arrival = attach_author_corrections({}, root, scene_kind="arrival")
            self.assertNotIn("author_corrections", arrival)
            calibration = attach_author_corrections({}, root, scene_kind="calibration")
            self.assertEqual(len(calibration["author_corrections"]), 1)


if __name__ == "__main__":
    unittest.main()
