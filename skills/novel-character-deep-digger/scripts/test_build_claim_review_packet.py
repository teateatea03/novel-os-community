import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from build_claim_review_packet import packet


class PacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'raw.txt').write_text('Original neutral material')
        digest = hashlib.sha256((self.root/'raw.txt').read_bytes()).hexdigest()
        self.protocol = {'schema':'minis.character-research-run.v2', 'run_id':'synthetic',
                         'questions':[{'id':'Q1','text':'事件何時發生？'}]}
        self.claims = [{'claim_id':'C1','question_id':'Q1','text':'SECRET_CONCLUSION',
                        'status':'SUPPORTED','hypotheses':['SECRET_HYPOTHESIS'],
                        'evidence':[{'artifact_id':'A1','locator':'paragraph 1',
                                     'weight_reason':'SECRET_REASON'}],
                        'counterevidence':[{'artifact_id':'A1','locator':'paragraph 2'}]}]
        self.artifacts = [{'artifact_id':'A1','local_path':'raw.txt','sha256':digest,
                           'analysis':'SECRET_ANALYSIS','raw_or_derived':'raw'}]

    def tearDown(self):
        self.temp.cleanup()

    def write(self):
        (self.root/'protocol.json').write_text(json.dumps(self.protocol))
        for n, rows in [('claims',self.claims),('artifacts',self.artifacts)]:
            (self.root/(n+'.jsonl')).write_text(''.join(json.dumps(x)+'\n' for x in rows))

    def result(self):
        self.write()
        return packet(self.root,'C1')

    def test_omits_conclusions(self):
        r = self.result()
        text = json.dumps(r)
        for marker in ['SECRET_CONCLUSION','SECRET_HYPOTHESIS','SECRET_REASON','SECRET_ANALYSIS']:
            self.assertNotIn(marker,text)
        self.assertFalse(r['independent_review_established'])

    def test_includes_both_sides_without_labels(self):
        r = self.result()
        self.assertEqual(len(r['materials']),2)
        self.assertEqual(r['materials'][0]['file_check'],'hash_verified')
        self.assertNotIn('evidence_role',r['materials'][0])

    def test_bad_hash(self):
        self.artifacts[0]['sha256'] = '0'*64
        with self.assertRaises(ValueError): self.result()

    def test_missing_artifact(self):
        self.artifacts = []
        with self.assertRaises(ValueError): self.result()

    def test_external_path(self):
        self.artifacts[0]['local_path'] = '../elsewhere.txt'
        with self.assertRaises(ValueError): self.result()

    def test_external_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'outside'
            p.write_text('not a research artifact')
            (self.root/'link').symlink_to(p)
            self.artifacts[0]['local_path'] = 'link'
            with self.assertRaises(ValueError): self.result()

    def test_missing_path_legacy(self):
        self.artifacts[0].pop('local_path')
        self.assertEqual(self.result()['materials'][0]['file_check'],'unverified_no_local_path')

    def test_missing_question(self):
        self.protocol['questions'] = []
        with self.assertRaises(ValueError): self.result()

    def test_duplicate_claim(self):
        self.claims.append(dict(self.claims[0]))
        with self.assertRaises(ValueError): self.result()

    def test_empty_evidence_not_review(self):
        self.claims[0].update(evidence=[],counterevidence=[])
        r=self.result()
        self.assertEqual(r['materials'],[])
        self.assertFalse(r['independent_review_established'])

    def test_dedup(self):
        self.claims[0]['counterevidence'] = list(self.claims[0]['evidence'])
        self.assertEqual(len(self.result()['materials']),1)

    def test_run_unchanged(self):
        self.write()
        before={p.name:p.read_bytes() for p in self.root.iterdir()}
        packet(self.root,'C1')
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.root.iterdir()})

    def test_output_never_overwrites(self):
        self.write()
        output=self.root/'claims.jsonl'
        before=output.read_bytes()
        p=subprocess.run([sys.executable,str(Path(__file__).with_name('build_claim_review_packet.py')),
                          str(self.root),'--claim-id','C1','--output',str(output)],capture_output=True)
        self.assertEqual(p.returncode,2)
        self.assertEqual(output.read_bytes(),before)

    def test_cli_creates_packet(self):
        self.write()
        output=self.root/'packet.json'
        p=subprocess.run([sys.executable,str(Path(__file__).with_name('build_claim_review_packet.py')),
                          str(self.root),'--claim-id','C1','--output',str(output)],capture_output=True)
        self.assertEqual(p.returncode,0)
        self.assertFalse(json.loads(p.stdout)['review_completed'])
        self.assertEqual(json.loads(output.read_text())['claim_id'],'C1')


if __name__ == '__main__': unittest.main()
