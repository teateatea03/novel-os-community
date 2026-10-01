#!/usr/bin/env python3
"""Add detailed, evidence-linked character cards to existing graph nodes."""
import argparse,json,os,shutil
from datetime import datetime,timezone

def main():
 a=argparse.ArgumentParser();a.add_argument('--graph',required=True);a.add_argument('--cards',required=True);a.add_argument('--audit');x=a.parse_args()
 d=json.load(open(x.graph)); cards=json.load(open(x.cards)); lookup={n['id']:n for n in d['nodes']}
 updated=[]
 for nid, patch in cards['characters'].items():
  n=lookup[nid]; p=n.setdefault('properties',{}); p.update(patch); updated.append(nid)
 d.setdefault('graph',{})['updated_at']=datetime.now(timezone.utc).isoformat()
 shutil.copy2(x.graph,x.graph+'.bak')
 tmp=x.graph+'.tmp';json.dump(d,open(tmp,'w'),ensure_ascii=False,indent=2);os.replace(tmp,x.graph)
 if x.audit:
  with open(x.audit,'a') as f:f.write(json.dumps({'at':d['graph']['updated_at'],'operation':'patch_character_cards','updated':updated},ensure_ascii=False)+'\n')
 print(json.dumps({'updated':updated},ensure_ascii=False))
if __name__=='__main__':main()
