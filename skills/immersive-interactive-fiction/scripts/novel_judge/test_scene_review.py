from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from .cli import main
from .cold_read import record_reader_reaction
from .scene_review import review_scene_text


class SceneReviewTests(unittest.TestCase):
    def test_review_is_prescan_not_beta(self):
        report = review_scene_text("他們談了很多，關係因此改變，事情也往前推進了。", scene_id="s1")
        self.assertEqual(report["schema"], "minis.scene-review.v1")
        self.assertTrue(report["claims"]["machine_prescan_only"])
        self.assertFalse(report["claims"]["is_beta_reader"])
        self.assertFalse(report["claims"]["is_literary_score"])
        codes = {x["code"] for x in report["narrative_qa"]["findings"]}
        self.assertIn("SUMMARY_ONLY_SCENE", codes)

    def test_cli_inspect_prose_does_not_need_session(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "T0001.md"
            path.write_text("觀測員翻開器材清單。技術員說：「鏡頭蓋在第二格。」\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = main(["inspect-prose", td, "--path", "T0001.md"])
            self.assertEqual(rc, 0)
            payload = json.loads(buf.getvalue())
            self.assertEqual(payload["schema"], "minis.scene-review.v1")
            self.assertTrue(payload["claims"]["machine_prescan_only"])

    def test_machine_prescan_origin_is_stripped_from_human_record(self):
        report = record_reader_reaction(
            reader_id="r1", source="x", role="beta_reader",
            reactions=[
                {"code": "SUMMARY_ONLY_SCENE", "claim": "machine", "origin": "deterministic_pre_scan"},
                {"code": "LOST_INTEREST", "claim": "第三章略讀"},
            ],
        )
        self.assertTrue(report["claims"]["is_human_reader"])
        self.assertEqual([t["code"] for t in report["tickets"]], ["LOST_INTEREST"])
