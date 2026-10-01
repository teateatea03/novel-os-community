from __future__ import annotations

import unittest

from .authority_layers import build_authority_report, classify_findings


class AuthorityLayerTests(unittest.TestCase):
    def test_layers_are_separated_and_only_configured_blockers_stop_commit(self):
        report = build_authority_report(findings=[
            {"layer": "CANON_INTEGRITY", "code": "KNOWLEDGE_LEAK", "severity": "P0", "confidence": "high", "claim": "leak"},
            {"layer": "EDITORIAL_DIAGNOSIS", "code": "PACING", "severity": "P1", "confidence": "medium", "claim": "slow"},
            {"layer": "READER_RESPONSE", "code": "BORED", "severity": "P1", "confidence": "low", "claim": "skim"},
        ])
        self.assertEqual(report["layers"]["CANON_INTEGRITY"]["status"], "FAIL")
        self.assertEqual(report["layers"]["EDITORIAL_DIAGNOSIS"]["status"], "WARN")
        self.assertEqual(report["layers"]["READER_RESPONSE"]["status"], "WARN")
        self.assertFalse(report["commit"]["may_commit"])
        self.assertEqual(report["commit"]["blockers"][0]["code"], "KNOWLEDGE_LEAK")

    def test_editorial_findings_alone_do_not_block(self):
        report = build_authority_report(findings=[
            {"layer": "EDITORIAL_DIAGNOSIS", "code": "CLICHE", "severity": "P1", "confidence": "high", "claim": "stock"},
        ])
        self.assertTrue(report["commit"]["may_commit"])
        self.assertEqual(report["summary"]["layer_status"]["EDITORIAL_DIAGNOSIS"], "WARN")

    def test_narrative_qa_requires_high_confidence_p0_to_block(self):
        soft = build_authority_report(findings=[
            {"layer": "NARRATIVE_QA", "code": "X", "severity": "P0", "confidence": "medium", "claim": "maybe"},
        ])
        hard = build_authority_report(findings=[
            {"layer": "NARRATIVE_QA", "code": "Y", "severity": "P0", "confidence": "high", "claim": "sure"},
        ])
        self.assertTrue(soft["commit"]["may_commit"])
        self.assertFalse(hard["commit"]["may_commit"])

    def test_classify_unknown_layer_falls_back(self):
        buckets = classify_findings([{"layer": "NOPE", "code": "A", "claim": "x"}])
        self.assertEqual(len(buckets["NARRATIVE_QA"]), 1)


if __name__ == "__main__":
    unittest.main()
