#!/usr/bin/env python3
"""Offline prompt/evidence contracts, not model or literary-quality evaluations."""
import hashlib
from pathlib import Path
import tempfile
import unittest

from independent_review import ROLES
from review_evidence import capture_source, make_report, recheck_report


class ReaderTermGuidanceTests(unittest.TestCase):
    def test_beta_reader_prompt_preserves_advisory_and_uncertainty_boundaries(self):
        prompt = ROLES['beta-reader']
        for phrase in ('類別／眼前行動效果', '刻意保留的真相', 'unknown', 'questions',
                       '不可靠敘事', '已介紹別名', '非阻斷', '來源 hash', 'anchored'):
            self.assertIn(phrase, prompt)

    def test_reader_advice_uses_existing_v2_binding_without_semantic_acceptance(self):
        # Both sentences and the proposed critique are synthetic. The assertion
        # covers quoted bytes and report status, not whether the critique is fair.
        text = '霧扣過了逆衡，於是他選了第三條路。\n她問選路的理由，他把門關上。\n'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'chapters').mkdir()
            draft = root / 'chapters/demo.md'
            draft.write_text(text, encoding='utf-8')
            sources = {'chapters/demo.md': capture_source(root, 'chapters/demo.md')}
            issue = {'category': 'reader', 'severity': 'P2',
                     'claim': '讀者可能無法追蹤眼前選路依據；作者意圖 unknown。',
                     'evidence_a': {'file': 'chapters/demo.md', 'line': 1, 'quote': text.splitlines()[0]},
                     'evidence_b': {'file': 'chapters/demo.md', 'line': 2, 'quote': text.splitlines()[1]},
                     'minimal_fix': '考慮增加一個可見後果，或保留原文。', 'confidence': 0.5}
            data = {'summary': '合成建議', 'issues': [issue], 'questions': []}
            report = make_report(data, sources, 'chapters/demo.md', 'beta-reader',
                                 'synthetic', 'raw.txt', ROLES['beta-reader'], {})
            self.assertEqual(report['schema'], 'minis.novel-review.v2')
            finding = report['validation']['findings'][0]
            self.assertEqual(finding['status'], 'anchored')
            self.assertEqual(finding['semantic_status'], 'unverified')
            self.assertEqual(finding['resolution'], 'unresolved')
            self.assertEqual(report['source_binding'][0]['sha256'], hashlib.sha256(draft.read_bytes()).hexdigest())
            del issue['evidence_b']
            incomplete = make_report(data, sources, 'chapters/demo.md', 'beta-reader',
                                     'synthetic', 'raw.txt', ROLES['beta-reader'], {})
            self.assertEqual(incomplete['validation']['findings'][0]['status'], 'unverified')
            question = {'summary': 'unknown：未提供前文', 'issues': [],
                        'questions': ['霧扣是否已在前文介紹？目前上下文不足。']}
            questions = make_report(question, sources, 'chapters/demo.md', 'beta-reader',
                                    'synthetic', 'raw.txt', ROLES['beta-reader'], {})
            self.assertEqual(questions['validation']['findings'], [])
            self.assertEqual(questions['questions'], question['questions'])
            draft.write_text(text + '\n', encoding='utf-8')
            self.assertEqual(recheck_report(root, report)['status'], 'stale')


if __name__ == '__main__':
    unittest.main()
