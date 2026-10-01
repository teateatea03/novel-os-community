#!/usr/bin/env python3
"""Build a dependency-free searchable index for a novel project."""
from __future__ import annotations
import argparse, hashlib, json, math, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

INCLUDE = ("*.md",)
SKIP = {"snapshots", "context-packs", "graphify-out", ".git"}

def terms(s: str):
    latin = re.findall(r"[A-Za-z0-9_]{2,}", s.lower())
    han = re.findall(r"[\u3400-\u9fff]", s)
    grams = ["".join(han[i:i+2]) for i in range(len(han)-1)] if len(han)>1 else han
    return latin + grams

def main():
 p=argparse.ArgumentParser(); p.add_argument('--root',required=True); p.add_argument('--output',default='story-index.json'); a=p.parse_args()
 root=Path(a.root).resolve(); docs=[]
 for path in root.rglob('*.md'):
  if any(x in SKIP for x in path.parts): continue
  text=path.read_text(encoding='utf-8',errors='replace'); rel=str(path.relative_to(root))
  lines=text.splitlines(); chunks=[]; heading=''
  for i in range(0,len(lines),80):
   block='\n'.join(lines[i:i+80]); m=re.findall(r'^#+\s+(.+)$',block,re.M)
   if m: heading=m[0]
   if block.strip(): chunks.append({'id':f'{rel}:L{i+1}-L{min(i+80,len(lines))}','file':rel,'start_line':i+1,'end_line':min(i+80,len(lines)),'heading':heading,'text':block,'terms':Counter(terms(block))})
  docs.extend(chunks)
 df=Counter();
 for d in docs: df.update(d['terms'].keys())
 out={'schema':'minis.novel-story-index.v1','built_at':datetime.now(timezone.utc).isoformat(),'root':str(root),'document_count':len(docs),'df':df,'documents':docs}
 # Counters are JSON serializable; retain source text for evidence/context packs.
 dest=root/a.output; dest.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'ok':True,'output':str(dest),'chunks':len(docs),'unique_terms':len(df)},ensure_ascii=False))
if __name__=='__main__': main()
