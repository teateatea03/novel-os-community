#!/usr/bin/env python3
"""Flag files likely affected by a revision; never changes canonical source."""
from __future__ import annotations
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
SKIP={'snapshots','.git','graphify-out','context-packs'}
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--query',required=True);p.add_argument('--mark',action='store_true');a=p.parse_args();root=Path(a.root); words=[x.lower() for x in re.findall(r'[\w\u3400-\u9fff]{2,}',a.query)]
 hits=[]
 for x in root.rglob('*.md'):
  if any(i in SKIP for i in x.parts):continue
  text=x.read_text(encoding='utf-8',errors='replace').lower(); count=sum(text.count(w) for w in words)
  if count:hits.append({'file':str(x.relative_to(root)),'matches':count})
 # Operational derivatives always become stale after source revision.
 for f in ['story-index.json','reader-ledger.md','timeline.md','current-state.md','plot-threads.md','workflow-state.json']:
  if (root/f).exists() and not any(x['file']==f for x in hits):hits.append({'file':f,'matches':0,'reason':'derived_or_cross-ledger'})
 hits.sort(key=lambda x:(-x['matches'],x['file'])); report={'schema':'minis.novel-cascade.v1','created_at':datetime.now(timezone.utc).isoformat(),'query':a.query,'status':'cascade_pending','affected':hits,'required_next':['update canonical sources','reconcile ledgers','rebuild story index/context packs','run chapter gate']}
 (root/'cascade-impact.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 if a.mark:
  state=root/'workflow-state.json'; data=json.loads(state.read_text(encoding='utf-8')) if state.exists() else {};data['cascade_status']='cascade_pending';data['author_decisions_needed']=[f'Review cascade impact: {a.query}'];state.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,'output':str(root/'cascade-impact.json'),'affected':len(hits),'status':'cascade_pending'},ensure_ascii=False))
if __name__=='__main__':main()
