#!/usr/bin/env python3
"""Gate chapter promotion on immutable behavior prediction locks."""
from __future__ import annotations
import argparse, importlib.util, json, re
from pathlib import Path

def load_runtime():
 p=Path(__file__).resolve().parents[2]/'human-behavior-personality-consultant'/'scripts'/'behavior_calibration.py'
 s=importlib.util.spec_from_file_location('behavior_calibration',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def issue(sev,claim,a,b,fix):return {'severity':sev,'category':'Characterization','claim':claim,'evidence_a':a,'evidence_b':b,'minimal_fix':fix}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--chapter',required=True);a=ap.parse_args();root=Path(a.root);out=[];m=load_runtime();v=m.validate_all(root)
 for e in v['errors']:out.append(issue('P0','行為校準帳本完整性失敗',e,'behavior-calibration','修復 hash／schema／重複 ID，不可覆寫舊 Lock'))
 texts=[]
 chapter=root/'chapters'/f'{a.chapter}.md'
 if chapter.exists():texts.append((chapter,chapter.read_text(encoding='utf-8',errors='replace')))
 for p in [root/'chapter-plans'/f'{a.chapter}.md',root/'chapter-plans'/f'chapter-{a.chapter}.md']:
  if p.exists():texts.append((p,p.read_text(encoding='utf-8',errors='replace')))
 for p in (root/'scenes').glob(f'*{a.chapter}*.md') if (root/'scenes').exists() else []:texts.append((p,p.read_text(encoding='utf-8',errors='replace')))
 req=set();rreq=set()
 for p,t in texts:
  req.update(re.findall(r'BEHAVIOR_LOCK_REQUIRED\s*:\s*([A-Za-z0-9._-]+)',t,re.I))
  rreq.update(re.findall(r'BEHAVIOR_RESOLUTION_REQUIRED\s*:\s*([A-Za-z0-9._-]+)',t,re.I))
 _,lp,rp,_=m.paths(root);locks={x.get('prediction_id'):x for x in m.rows(lp)};resolved={x.get('prediction_id') for x in m.rows(rp) if x.get('cause')!='unresolved'}
 for pid in sorted(req):
  if pid not in locks:out.append(issue('P0','重大行為節點缺少事前 Prediction Lock',pid,str(chapter),'生成正文前用 behavior_calibration.py lock 建立不可覆寫紀錄'))
 for pid in sorted(rreq):
  if pid not in locks:out.append(issue('P0','章後校準引用不存在的 Prediction Lock',pid,str(chapter),'先建立或修正 Prediction ID'))
  elif pid not in resolved:out.append(issue('P0','重大行為節點缺少章後 Resolution',pid,str(chapter),'用 behavior_calibration.py resolve 追加結果；不要改寫 Lock'))
 # Explicit precise-percent declarations must point to a validated precise lock.
 for p,t in texts:
  for pid in re.findall(r'PRECISE_BEHAVIOR_PERCENT\s*:\s*([A-Za-z0-9._-]+)',t,re.I):
   lock=locks.get(pid)
   if not lock or lock.get('representation')!='precise_percent':out.append(issue('P0','精細百分比未通過校準門檻',pid,str(p),'改用序位／寬區間，或提供已驗證 precise_percent Lock'))
 status='FAIL' if any(x['severity']=='P0' for x in out) else ('WARN' if out else 'PASS')
 report={'schema':'minis.behavior-calibration-gate.v1','chapter':a.chapter,'status':status,'issues':out,'prediction_locks':sorted(req),'resolution_required':sorted(rreq),'ledger':v}
 d=root/'gates';d.mkdir(exist_ok=True);dest=d/f'{a.chapter}-behavior-gate.json';dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'ok':status!='FAIL','status':status,'issues':out,'output':str(dest)},ensure_ascii=False));return 1 if status=='FAIL' else 0
if __name__=='__main__':raise SystemExit(main())
