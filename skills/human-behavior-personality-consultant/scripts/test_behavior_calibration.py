from __future__ import annotations
import json, subprocess, sys, tempfile, unittest
from pathlib import Path
SCRIPT=Path(__file__).with_name('behavior_calibration.py')
class BehaviorCalibrationTests(unittest.TestCase):
 def cli(self,*args,ok=True):
  p=subprocess.run([sys.executable,str(SCRIPT),*args],capture_output=True,text=True)
  if ok and p.returncode: self.fail(p.stdout+p.stderr)
  if not ok: self.assertNotEqual(p.returncode,0)
  return json.loads(p.stdout)
 def payload(self,rep='ordinal'):
  cs=[{'id':'A','description':'先退開觀察','rank':1,'observable_predictions':['縮短回答'],'falsifiers':['立即公開對抗']},{'id':'B','description':'直接質問','rank':2,'observable_predictions':['提高音量'],'falsifiers':['完全離場']}]
  x={'prediction_id':'P001','node_id':'S001','actor_id':'c1','source_state_hash':'sha256:'+'a'*64,'evidence_level':'E2','situation_strength':'medium','representation':rep,'candidates':cs,'protectors':['朋友在場'],'inhibitors':['留下紀錄'],'counterfactual_tests':['移除旁觀者後 B 上升'],'unknowns':['對方是否錄音']}
  return x
 def write(self,d,name,obj):
  p=Path(d)/name;p.write_text(json.dumps(obj,ensure_ascii=False),encoding='utf-8');return str(p)
 def test_ordinal_lock_and_resolution(self):
  with tempfile.TemporaryDirectory() as d:
   x=self.payload(); f=self.write(d,'l.json',x); self.cli('lock','--root',d,'--input',f)
   r={'resolution_id':'R001','prediction_id':'P001','outcome':'A','cause':'prediction_hit','observed_hits':['縮短回答'],'observed_misses':[],'model_updates':['保留 if–then']}
   self.cli('resolve','--root',d,'--input',self.write(d,'r.json',r));v=self.cli('validate','--root',d);self.assertEqual(v['status'],'PASS');self.assertEqual(v['resolved_predictions'],1)
 def test_lock_is_immutable(self):
  with tempfile.TemporaryDirectory() as d:
   f=self.write(d,'l.json',self.payload());self.cli('lock','--root',d,'--input',f);x=self.payload();x['unknowns']=['changed'];self.cli('lock','--root',d,'--input',self.write(d,'l2.json',x),ok=False)
 def test_precise_percent_requires_calibration(self):
  with tempfile.TemporaryDirectory() as d:
   x=self.payload('precise_percent');
   for c,n in zip(x['candidates'],(60,40)):c.pop('rank');c['percent']=n
   self.cli('lock','--root',d,'--input',self.write(d,'l.json',x),ok=False)
 def test_precise_percent_allowed_after_threshold(self):
  with tempfile.TemporaryDirectory() as d:
   x=self.payload('precise_percent');x.update(similar_context_samples=5,resolved_predictions=10,calibration_record=True)
   for c,n in zip(x['candidates'],(60,40)):c.pop('rank');c['percent']=n
   self.cli('lock','--root',d,'--input',self.write(d,'l.json',x));self.assertEqual(self.cli('validate','--root',d)['status'],'PASS')
if __name__=='__main__':unittest.main()
