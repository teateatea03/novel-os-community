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


class PovDialogueTests(unittest.TestCase):
    def findings(self, text):
        return [f for f in inspect_prose(text)["findings"] if f["code"] == "POV_DRIFT"]

    def test_quoted_personas_do_not_count_as_narration(self):
        for opening, closing in (("「", "」"), ("『", "』"), ("“", "”"), ('"', '"'), ("‘", "’"), ("'", "'")):
            with self.subTest(opening=opening):
                text = f"# Synthetic heading\n她關上窗。\n{opening}我會留下。\n你先走。{closing}她說。"
                self.assertEqual(self.findings(text), [])

    def test_nested_and_escaped_dialogue(self):
        cases = [
            '她關上窗。「他說：『我會留下，你先走。』」她回答。',
            r'她關上窗。"我說：\"你先走。\""她回答。',
            "她關上窗。'I don't know. 我會留下，你先走。'她回答。",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(self.findings(text), [])

    def test_first_person_narration_and_dialogue_are_not_drift(self):
        self.assertEqual(self.findings('我關上窗。「你知道，她看見自己了。」我說。'), [])

    def test_unbalanced_quotes_do_not_claim_high_confidence_drift(self):
        for text in ('我關上窗。「你知道，他看見自己了。', '我關上窗。「你知道。』他看見自己。'):
            with self.subTest(text=text):
                self.assertEqual(self.findings(text), [])

    def test_heading_personas_are_not_narration(self):
        self.assertEqual(self.findings('# 我和你\n\n她關上窗。她知道天色暗了。'), [])

    def test_real_drift_after_dialogue_has_exact_narration_span(self):
        text = '# Synthetic heading\n「我關上窗。」她說。\n我關上窗。他看見自己，而你知道結果。'
        finding = self.findings(text)[0]
        span = finding['span']
        self.assertEqual(span['start'], text.rindex('我關上窗。'))
        self.assertEqual(text[span['start']:span['end']], span['quote'])
        self.assertNotIn('#', span['quote'])
        self.assertNotIn('「', span['quote'])

    def test_possessive_apostrophes_do_not_hide_real_drift(self):
        drift = '我握住門把。他看見自己的背影，而你知道結果。'
        for prefix in ("她拿起 James’ book。\n", "她拿起 James' book。\n",
                       '她說：「That is James’ book.」\n',
                       "她說：\"That is James' book.\"\n"):
            with self.subTest(prefix=prefix):
                finding = self.findings(prefix + drift)[0]
                self.assertEqual(finding['span']['start'], len(prefix))

    def test_unclosed_or_mismatched_quote_keeps_prior_certain_narration(self):
        drift = '我握住門把。他看見自己的背影，而你知道結果。'
        for suffix in ('\n她說：「明天再談。', '\n她說：「明天再談。』', '\n」我不知道。'):
            with self.subTest(suffix=suffix):
                self.assertEqual(len(self.findings(drift + suffix)), 1)

    def test_single_quote_closure_keeps_following_narration(self):
        drift = '我握住門把。他看見自己的背影，而你知道結果。'
        for prefix in ("她說：'That is James.'\n", '她說：‘That is James.’\n'):
            with self.subTest(prefix=prefix):
                finding = self.findings(prefix + drift)[0]
                self.assertEqual(finding['span']['start'], len(prefix))

    def test_same_mark_possessive_inside_single_quotes(self):
        drift = '我握住門把。他看見自己，而你知道結果。'
        for prefix in ("‘That is James’ book,’ she said.\n", "'That is James' book,' she said.\n",
                       "‘That is James’ book.’\n", "'That is James' book.'\n"):
            with self.subTest(prefix=prefix):
                self.assertEqual(len(self.findings(prefix + drift)), 1)

    def test_single_quote_closure_is_not_possessive_before_another_quote(self):
        drift = '我握住門把。他看見自己，而你知道結果。'
        for separator in (' ', ':'):
            with self.subTest(separator=separator):
                prefix = "'James' she said" + separator
                self.assertEqual(len(self.findings(prefix + "'明天見。'\n" + drift)), 1)
                self.assertEqual(self.findings(prefix + "'" + drift + "'\n她關上窗。"), [])

    def test_dialogue_boundary_preserves_adjacent_narration(self):
        for text in ('我說：「走。」他看見自己。', '我說："走。"他看見自己。',
                     '我說：「走」他看見自己。'):
            with self.subTest(text=text):
                self.assertEqual(len(self.findings(text)), 1)

    def test_long_embedded_quote_is_not_reintroduced_in_span(self):
        text = '我說：「' + '合成台詞。' * 60 + '」然後離開。他看見自己，而你知道真相。'
        span = self.findings(text)[0]['span']
        self.assertEqual(span['quote'], '我說：')
        self.assertEqual(text[span['start']:span['end']], span['quote'])

    def test_adjacent_cognition_flip_still_detected(self):
        text = '「你先走。」她說。\n我關上窗。他看見自己。'
        findings = self.findings(text)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]['span']['start'], text.rindex('我關上窗。'))


if __name__ == "__main__":
    unittest.main()
