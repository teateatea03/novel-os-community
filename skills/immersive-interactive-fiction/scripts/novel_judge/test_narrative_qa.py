from __future__ import annotations

import unittest

from .fallback_executor import fallback_blind_read
from .narrative_gate import validate_generated_output
from .narrative_qa import inspect_prose
from .state import empty_state
from .canonical import refresh_state_hash


def _state():
    s = empty_state("qa", "s")
    s["actors"] = {"npc": {"kind": "npc", "location": "room"}}
    return refresh_state_hash(s)


class NarrativeQATests(unittest.TestCase):
    def test_unexplained_death_resume_is_p0(self):
        text = "他已經死了。下一秒，他沒有任何解釋地起身煮咖啡。"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("UNEXPLAINED_DEATH_RESUME", codes)
        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["may_commit"])

    def test_explained_death_or_fake_death_is_not_p0(self):
        text = "他已經死了。後來大家才知道那是假死，他其實被救走了。"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertNotIn("UNEXPLAINED_DEATH_RESUME", codes)

    def test_pov_drift_is_detected(self):
        text = "我握住門把。他看見自己的背影，而你知道兇手其實是她。"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("POV_DRIFT", codes)

    def test_flat_voice_is_detected(self):
        text = "甲說：「我認為我們應該離開。」乙說：「我認為我們應該留下。」"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("FLAT_CHARACTER_VOICE", codes)

    def test_summary_only_scene_is_detected(self):
        text = "他們談了很多，關係因此改變，事情也往前推進了。"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("SUMMARY_ONLY_SCENE", codes)

    def test_stock_cliche_is_detected(self):
        text = "命運的齒輪開始轉動，一切都將不再一樣。"
        report = inspect_prose(text)
        codes = {x["code"] for x in report["findings"]}
        self.assertIn("STOCK_CLICHE", codes)

    def test_clean_scene_can_pass(self):
        text = "觀測員把圓蓋放進泡棉凹槽。技術員說：「編號對上了。」鉛筆在清單末行畫出一個勾，儀器箱隨即扣緊。"
        report = inspect_prose(text)
        self.assertEqual(report["status"], "PASS")
        self.assertTrue(report["may_commit"])

    def test_narrative_gate_fails_death_resume_and_keeps_authority_layers(self):
        out = validate_generated_output({
            "text": "他已經死了。下一秒，他沒有任何解釋地起身煮咖啡。",
            "claimed_facts": [],
            "player_actions": [],
        }, _state())
        self.assertEqual(out["status"], "fail")
        self.assertTrue(any(e.get("code") == "UNEXPLAINED_DEATH_RESUME" for e in out["errors"]))
        self.assertIn("authority", out)
        self.assertEqual(out["authority"]["layers"]["NARRATIVE_QA"]["status"], "FAIL")

    def test_narrative_gate_warns_on_cliche_without_hard_fail(self):
        out = validate_generated_output({
            "text": "觀測員合上儀器箱。命運的齒輪開始轉動，箱底卻只傳出螺絲滾動的聲音。",
            "claimed_facts": [],
            "player_actions": [],
        }, _state())
        self.assertEqual(out["status"], "pass")
        self.assertTrue(any(w.get("code") == "STOCK_CLICHE" for w in out["warnings"]))

    def test_fallback_blind_read_reports_qa_and_denies_quality_claim(self):
        result = fallback_blind_read(_state(), {
            "text": "他們談了很多，關係因此改變，事情也往前推進了。",
            "player_actions": [],
        })
        payload = result["output"]
        self.assertIn(payload["status"], {"warn", "fail", "pass"})
        self.assertTrue(any(i.get("code") == "SUMMARY_ONLY_SCENE" for i in payload["issues"]))
        self.assertFalse(payload["claims"]["literary_quality_judged"])
        self.assertIn("authority", payload)


if __name__ == "__main__":
    unittest.main()
