#!/usr/bin/env python3
"""Validate a hash-bound semantic NPC drift review artifact.

This script validates the review record, not personality semantics themselves.
A human or a configured independent model must create the evidence-backed JSON.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
P0_LABELS={"HELPFUL_ASSISTANT_FALLBACK","ANALYST_REPORT_VOICE","HOST_DIRECTOR_VOICE","THERAPIST_RELATIONSHIP_MEDIATOR","OMNISCIENT_KNOWLEDGE_LEAK","KNOWLEDGE_BOUNDARY_BREACH","FORBIDDEN_ACT_EXECUTION"}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--scene',required=True); ap.add_argument('--review',required=True); a=ap.parse_args()
 scene=Path(a.scene); d=json.loads(Path(a.review).read_text()); errs=[]
 if d.get('scene_sha256')!=sha(scene): errs.append('SCENE_HASH_MISMATCH')
 reviews=d.get('reviews');
 if not isinstance(reviews,list): errs.append('REVIEWS_NOT_LIST'); reviews=[]
 for i,r in enumerate(reviews):
  if not isinstance(r,dict) or not r.get('speaker'): errs.append(f'REVIEW_{i}_MALFORMED'); continue
  if not isinstance(r.get('labels',[]),list): errs.append(f'REVIEW_{i}_LABELS_MALFORMED')
  if any(x in P0_LABELS for x in r.get('labels',[])) and not r.get('evidence_spans'): errs.append(f'REVIEW_{i}_P0_NO_EVIDENCE')
 p0=sorted({x for r in reviews if isinstance(r,dict) for x in r.get('labels',[]) if x in P0_LABELS})
 if p0 and d.get('verdict')=='pass': errs.append('P0_LABEL_CANNOT_PASS')
 out={'ok':not errs,'scene_sha256':sha(scene),'p0_labels':p0,'errors':errs,'verdict':d.get('verdict')}
 print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(0 if out['ok'] else 2)
if __name__=='__main__': main()
