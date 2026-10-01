#!/usr/bin/env python3
import json, subprocess, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name("validate_research_manifest.py")

def base(depth="R0"):
    return {"schema":"minis.character-research-manifest.v1","research_depth":depth,
      "questions":[{"id":"Q1","text":"身份？","priority":"P0"}],
      "identity_resolution":{"aliases":["甲"],"disambiguators":["作品A"],"excluded_homonyms":[]},
      "source_map":[{"surface":"official","status":"searched","reason":""}],
      "queries":[{"id":"q1","question_id":"Q1","platform":"Google","exact_query":"\"甲\" 作品A","language":"zh","searched_at":"2026-08-19","filters":{},"result":"useful","new_source_families":1,"notes":""}],
      "artifacts":[],"claims":[],"negative_checks":[],"saturation":{},"scope_exceptions":[]}

def run(d):
    with tempfile.NamedTemporaryFile("w",suffix=".json",delete=False,encoding="utf-8") as f:
        json.dump(d,f,ensure_ascii=False); name=f.name
    r=subprocess.run(["python3",str(SCRIPT),name],capture_output=True,text=True)
    Path(name).unlink(); return r.returncode,json.loads(r.stdout)

class TestResearchManifest(unittest.TestCase):
    def test_r0_minimum_passes(self):
        code,out=run(base()); self.assertEqual(code,0,out)
    def test_r1_without_reproducible_capture_fails(self):
        d=base("R1"); d["source_map"] += [{"surface":"news","status":"searched","reason":""},{"surface":"library","status":"searched","reason":""}]
        code,out=run(d); self.assertEqual(code,1); self.assertIn("gate:R1_requires_artifacts",out["errors"])
    def test_r2_complete_passes(self):
        d=base("R2")
        d["source_map"] += [{"surface":"news","status":"searched","reason":""},{"surface":"archive","status":"searched","reason":""},{"surface":"adjacent","status":"searched","reason":""},{"surface":"scholarly","status":"searched","reason":""}]
        d["queries"] += [
          {"id":"q2","question_id":"Q1","platform":"Archive","exact_query":"甲 collection","language":"en","searched_at":"2026-08-19T01:01Z","filters":{},"result":"zero","new_source_families":0,"notes":""},
          {"id":"q3","question_id":"Q1","platform":"News","exact_query":"甲 否認","language":"zh","searched_at":"2026-08-19T01:02Z","filters":{},"result":"noise","new_source_families":0,"notes":""}]
        d["artifacts"]=[{"id":"a1","url":"https://example.org/a","archived_url":"","retrieved_at":"2026-08-19","local_path":"","sha256":"","locator":"para 3","capture_status":"full"}]
        d["claims"]=[{"id":"c1","question_id":"Q1","artifact_ids":["a1"],"source_family_id":"sf1","status":"EXTRACTED","counterevidence":[]}]
        d["negative_checks"]=[{"question_id":"Q1","where":"News","query":"甲 否認","meaning":"not_found_not_absent"}]
        d["saturation"]={"last_queries":["q1","q2","q3"],"new_independent_families":0,"open_p0_gaps":[],"stop_reason":"三條不同路徑無新證據家族"}
        code,out=run(d); self.assertEqual(code,0,out)
    def test_local_artifact_requires_hash(self):
        d=base("R1"); d["source_map"] += [{"surface":"news","status":"searched","reason":""},{"surface":"library","status":"searched","reason":""}]
        d["queries"] += [dict(d["queries"][0],id="q2",searched_at="2026-08-19T01:01Z"),dict(d["queries"][0],id="q3",searched_at="2026-08-19T01:02Z")]
        d["artifacts"]=[{"id":"a1","url":"","retrieved_at":"2026-08-19","local_path":"/tmp/a.pdf","sha256":"","locator":"p.1","capture_status":"full"}]
        d["claims"]=[{"id":"c1","question_id":"Q1","artifact_ids":["a1"],"source_family_id":"sf1","status":"EXTRACTED","counterevidence":[]}]
        d["saturation"]={"last_queries":["q1","q2","q3"],"new_independent_families":0,"open_p0_gaps":[],"stop_reason":"done"}
        code,out=run(d); self.assertEqual(code,1); self.assertIn("missing:artifact.sha256:a1",out["errors"])
if __name__=="__main__": unittest.main()
