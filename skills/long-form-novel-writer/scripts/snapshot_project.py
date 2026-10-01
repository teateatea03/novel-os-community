#!/usr/bin/env python3
"""Snapshot project files before a canonical revision."""
from __future__ import annotations
import argparse,hashlib,json,shutil
from datetime import datetime,timezone
from pathlib import Path
SKIP={'snapshots','.git','context-packs','__pycache__'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--reason',required=True);a=p.parse_args();root=Path(a.root).resolve();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); dest=root/'snapshots'/stamp; dest.mkdir(parents=True)
 files=[]
 for x in root.rglob('*'):
  if not x.is_file() or any(i in SKIP for i in x.parts):continue
  rel=x.relative_to(root); data=x.read_bytes(); files.append({'path':str(rel),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}); target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(x,target)
 manifest={'schema':'minis.novel-snapshot.v1','created_at':datetime.now(timezone.utc).isoformat(),'reason':a.reason,'files':files}
 (dest/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,'snapshot':str(dest),'files':len(files)},ensure_ascii=False))
if __name__=='__main__':main()
