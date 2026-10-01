from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .editorial_diagnosis import diagnose_manuscript, diagnose_text


class EditorialDiagnosisTests(unittest.TestCase):
    def test_diagnose_text_makes_tickets_and_does_not_claim_full_edit(self):
        report = diagnose_text("甲說：「我認為我們應該離開。」乙說：「我認為我們應該留下。」")
        self.assertGreaterEqual(len(report["tickets"]), 1)
        self.assertFalse(report["editorial_letter_outline"]["claims"]["is_developmental_edit"])
        self.assertEqual(report["authority"]["layers"]["EDITORIAL_DIAGNOSIS"]["status"], "WARN")

    def test_manuscript_board_aggregates_chapters(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            chapters = root / "chapters"
            chapters.mkdir()
            (chapters / "ch01.md").write_text("他們談了很多，關係因此改變，事情也往前推進了。\n", encoding="utf-8")
            (chapters / "ch02.md").write_text("觀測員翻到清單末頁。技術員說：「還差一枚鏡頭蓋。」\n", encoding="utf-8")
            report = diagnose_manuscript(root)
            self.assertEqual(report["chapter_count"], 2)
            self.assertIn("revision_board", report)
            self.assertGreaterEqual(report["ticket_count"], 1)
            self.assertIn("not a full human developmental edit", report["limitations"][0])


if __name__ == "__main__":
    unittest.main()
