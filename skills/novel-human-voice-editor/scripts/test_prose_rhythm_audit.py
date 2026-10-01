#!/usr/bin/env python3
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("prose_rhythm_audit.py")

def run(text):
    with tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False) as f:
        f.write(text); path=f.name
    try:
        out=subprocess.check_output([sys.executable,str(SCRIPT),"--file",path,"--format","json"],text=True)
        return json.loads(out)
    finally: Path(path).unlink(missing_ok=True)

def codes(data): return {x['code'] for x in data['issues']}

class ProseRhythmAuditTests(unittest.TestCase):
    def test_action_stack(self):
        self.assertIn('ACTION_STACK', codes(run('他走進門，看見杯子，聽見水聲，順手把外套掛上，又往廚房看。')))

    def test_short_run(self):
        self.assertIn('SHORT_BEAT_RUN', codes(run('門開了。雨落下。她沒動。誰也沒說話。')))

    def test_dialogue_tag_stutter(self):
        self.assertIn('DIALOGUE_TAG_STUTTER', codes(run('她說：「好。」她說：「等等。」她說：「你先坐。」')))

    def test_small_passage_no_rhythm_verdict(self):
        d=run('她看著門。')
        self.assertEqual(d['summary']['sentences'],1)
        self.assertTrue(all(x['severity']=='review' for x in d['issues']))
        self.assertFalse(any('score' in k.lower() for k in d))

    def test_html(self):
        with tempfile.TemporaryDirectory() as td:
            src=Path(td)/'x.md'; out=Path(td)/'r.html'; src.write_text('她看著門。雨一直下。',encoding='utf-8')
            subprocess.check_call([sys.executable,str(SCRIPT),'--file',str(src),'--format','html','--output',str(out)])
            self.assertIn('<div class="bars">', out.read_text(encoding='utf-8'))

if __name__=='__main__':
    unittest.main()