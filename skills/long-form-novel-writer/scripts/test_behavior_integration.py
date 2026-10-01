from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SKILL=Path(__file__).resolve().parents[1]
INIT=SKILL/'scripts'/'init_novel_project.py'
GATE=SKILL/'scripts'/'behavior_gate.py'
CAL=SKILL.parent/'human-behavior-personality-consultant'/'scripts'/'behavior_calibration.py'
class LongformBehaviorIntegrationTests(unittest.TestCase):
 def cli(self,cmd,ok=True):
  p=subprocess.run(cmd,capture_output=True,text=True)
  if ok and p.returncode:self.fail(p.stdout+p.stderr)
  if not ok:self.assertNotEqual(p.returncode,0)
  return json.loads(p.stdout)
 def write(self,p,obj):p.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8');return str(p)
 def lock(self,pid='P001',rep='ordinal'):
  cs=[{'id':'A','description':'退後觀察','rank':1,'observable_predictions':['短答'],'falsifiers':['立即攻擊']},{'id':'B','description':'直接質問','rank':2,'observable_predictions':['追問'],'falsifiers':['完全離場']}]
  return {'prediction_id':pid,'node_id':'001-S1','actor_id':'hero','source_state_hash':'sha256:'+'a'*64,'evidence_level':'E2','situation_strength':'medium','representation':rep,'candidates':cs,'protectors':['同伴'],'inhibitors':['監視器'],'counterfactual_tests':['移除監視器後 B 上升'],'unknowns':['是否錄音']}
 def project(self,d):
  root=Path(d)/'projects';o=self.cli([sys.executable,str(INIT),'--title','校準測試','--slug','calibration-test','--root',str(root)]);p=Path(o['project']);(p/'chapters'/'001.md').write_text('BEHAVIOR_LOCK_REQUIRED: P001\n'+'這是一個重大抉擇場景。'*80,encoding='utf-8');return p
 def test_initialized_project_has_runtime_and_missing_lock_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.project(d);self.assertTrue((p/'behavior-calibration'/'predictions.jsonl').exists());self.cli([sys.executable,str(GATE),'--root',str(p),'--chapter','001'],ok=False)
 def test_lock_allows_gate_and_resolution_closes_loop(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.project(d);f=Path(d)/'l.json';self.write(f,self.lock());self.cli([sys.executable,str(CAL),'lock','--root',str(p),'--input',str(f)]);self.assertEqual(self.cli([sys.executable,str(GATE),'--root',str(p),'--chapter','001'])['status'],'PASS')
   (p/'chapters'/'001.md').write_text('BEHAVIOR_LOCK_REQUIRED: P001\nBEHAVIOR_RESOLUTION_REQUIRED: P001\n'+'結果已經發生。'*80,encoding='utf-8');self.cli([sys.executable,str(GATE),'--root',str(p),'--chapter','001'],ok=False)
   r={'resolution_id':'R001','prediction_id':'P001','outcome':'A','cause':'prediction_hit','observed_hits':['短答'],'observed_misses':[],'model_updates':['保留規則']};rf=Path(d)/'r.json';self.write(rf,r);self.cli([sys.executable,str(CAL),'resolve','--root',str(p),'--input',str(rf)]);self.assertEqual(self.cli([sys.executable,str(GATE),'--root',str(p),'--chapter','001'])['status'],'PASS')
 def test_unvalidated_precise_marker_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=self.project(d);f=Path(d)/'l.json';self.write(f,self.lock());self.cli([sys.executable,str(CAL),'lock','--root',str(p),'--input',str(f)]);(p/'chapters'/'001.md').write_text('BEHAVIOR_LOCK_REQUIRED: P001\nPRECISE_BEHAVIOR_PERCENT: P001\n'+'百分比測試。'*80,encoding='utf-8');self.cli([sys.executable,str(GATE),'--root',str(p),'--chapter','001'],ok=False)
if __name__=='__main__':unittest.main()
