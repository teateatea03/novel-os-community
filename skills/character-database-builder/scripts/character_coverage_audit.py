#!/usr/bin/env python3
"""Audit character-graph coverage; read-only except for requested report output."""
import argparse, glob, json, os, re
from collections import Counter

CLASS = ['subject_category','subject_subcategory','subject_kind','source_medium','canon_scope','version_scope','classification_basis','classification_confidence']
IDENTITY = ['public_identity','identity_summary','role','occupation','character_summary','name_zh']
VISUAL = ['visual_refs','primary_visual_id']
ENGINE = ['core_engine','external_goal','inner_need','core_fear','false_belief','habit_cost','motivation','behavior_model','personality_model','behavioral_anchor']
SKILLS = ['skills','capabilities','competencies','ability_profile','skill_profile','combat_profile','professional_skills','limitations','weaknesses','capability_cards']

def has(v): return v is not None and v != '' and v != [] and v != {}
def check(n, edges):
 p=n.get('properties') or {}; nid=n.get('id','')
 rel=[e for e in edges if e.get('source')==nid or e.get('target')==nid]
 evidence=n.get('evidence') or []; source=bool(n.get('source_url') or n.get('source_file') or evidence or p.get('source_evidence_urls') or p.get('source_page_url'))
 groups={'分類':CLASS,'身份／定位':IDENTITY,'角色引擎／行為':ENGINE,'能力／限制':SKILLS}
 visual_n=len(p.get('visual_refs') or []) if isinstance(p.get('visual_refs'), list) else int(bool(p.get('visual_refs') or p.get('primary_visual_id')))
 found={g:[k for k in ks if has(p.get(k))] for g,ks in groups.items()}
 missing=[g for g,x in found.items() if not x]
 rel_evidence=sum(1 for e in rel if e.get('evidence') or e.get('source_url') or e.get('source_file'))
 points=sum(bool(x) for x in found.values())+int(source)+int(len(rel)>0)+int(rel_evidence>0)
 # Needs a human-readable profile/card as well as machine graph coverage.
 return dict(id=nid,label=n.get('label',nid),score=points,missing=missing,source=source,edges=len(rel),edge_sources=rel_evidence,fields=found,visuals=visual_n)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
 rows=[]; dbs=[]
 for path in sorted(glob.glob(os.path.join(args.root,'*','graphify-out','graph.json'))):
  slug=path.split(os.sep)[-3]
  try:
   data=json.load(open(path)); nodes=data.get('nodes',[]); edges=data.get('links',data.get('edges',[]))
  except Exception as e: dbs.append((slug, 'ERROR '+str(e), [])); continue
  persons=[n for n in nodes if n.get('entity_type')=='person']
  rec=[check(n,edges) for n in persons]
  dbs.append((slug, data.get('graph',{}).get('title',slug),rec)); rows += [(slug,r) for r in rec]
 total=len(rows); missing=Counter(m for _,r in rows for m in r['missing'])
 low=sorted(rows,key=lambda x:(x[1]['score'],x[0],x[1]['id']))
 out=['# 角色資料庫完整度稽核','',f'- 稽核時間：由 `character_coverage_audit.py` 產生','- 範圍：`novel-character-database/*/graphify-out/graph.json`','- 方法：檢查每個 `person` 節點的分類、身份定位、角色引擎／行為、能力／限制，以及節點與關係來源。','- 注意：缺欄不等於可憑空補寫；只能以有來源的【明示】、有推論鏈的【推論】或明確【待定】補齊。','', '## 總覽','',f'- 資料庫：{len(dbs)}；人物節點：{total}','- 缺少的覆蓋面：'+'；'.join(f'{k} {v}' for k,v in missing.items()),'', '## 優先補件規則','','1. **P0（不得只用名稱）**：缺身份定位或能力／限制，或完全無來源的角色；先建最低可引用卡。','2. **P1**：缺角色引擎／行為模型；以行為證據、觸發、代價與不同壓力反應補足。','3. **P2**：缺可追溯關係、版本／正典、事件與細節；增量研究後補。','4. 真人只補公開可驗證的工作／作品／公開活動與明示表述；不填未公開私生活或遠端心理診斷。','', '## 各資料庫']
 for slug,title,rec in dbs:
  out += ['',f'### {title}（`{slug}`）', '',f'- 人物節點：{len(rec)}；P0：{sum(1 for r in rec if "身份／定位" in r["missing"] or "能力／限制" in r["missing"] or not r["source"])}；P1：{sum(1 for r in rec if "角色引擎／行為" in r["missing"])}']
  for r in sorted(rec,key=lambda x:(x['score'],x['id'])):
   miss='、'.join(r['missing']) or '無（仍應核對細項與版本）'
   out.append(f'- `{r["id"]}`｜{r["label"]}｜coverage {r["score"]}/7｜缺：{miss}｜節點來源：{"有" if r["source"] else "無"}｜關係 {r["edges"]}（具證據 {r["edge_sources"]}）｜公開圖 {r.get("visuals",0)}')
 out += ['', '## 最低可引用卡（每個角色都必須有）','', '```yaml','identity_and_scope: 身分／作品或公開範圍／版本','evidence: 至少一項來源與短引文或章節／集數定位','capability_cards:','  - name: 能力原名（不能只填名稱）','    what_it_does: 可觀察效果與操作方式','    preconditions: 前提、資源、訓練或授權','    limits_cost_risk: 限制、代價、失敗模式與反制','    evidence_or_reasoning: 來源；推論則寫推論鏈','    confidence: EXTRACTED|INFERRED|AMBIGUOUS','behavioral_anchor: 觸發 → 第一反應 → 行動 → 代價','relationships_or_context: 至少一項有證據的關係／組織／情境','```','']
 os.makedirs(os.path.dirname(args.output),exist_ok=True); open(args.output,'w').write('\n'.join(out))
 print(json.dumps({'databases':len(dbs),'persons':total,'report':args.output},ensure_ascii=False))
if __name__=='__main__': main()
