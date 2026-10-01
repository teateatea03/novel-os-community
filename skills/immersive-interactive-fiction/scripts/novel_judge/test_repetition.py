from __future__ import annotations

import unittest
from .repetition import detect_repetition, validate_no_repetition


class RepetitionTests(unittest.TestCase):
    def test_three_sentence_loop_fails(self):
        text = "門邊的燈亮了一下。她沒有說話。風從窗縫進來。" * 3
        report = detect_repetition(text)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(any(x["code"] == "REPETITION_LOOP" for x in report["findings"]))

    def test_long_duplicate_sentence_is_detected(self):
        sentence = "她把杯子放回桌面，指尖停在杯沿，像還在等一個沒有說出口的回答。"
        report = detect_repetition(sentence + sentence + "最後她轉身離開。")
        self.assertIn(report["status"], {"warn", "fail"})
        self.assertTrue(report["duplicate_units"])

    def test_short_dialogue_echo_is_not_rejected(self):
        self.assertEqual(detect_repetition("好。好。")['status'], "pass")

    def test_unique_prose_passes(self):
        text = "圓頂的開口露出一線星光。觀測員收好刻度尺，技術員將電池插回充電座。清單最後一欄留著空格，等下一班核對。"
        self.assertEqual(detect_repetition(text)['status'], "pass")
        self.assertEqual(validate_no_repetition(text), [])


if __name__ == "__main__": unittest.main()
