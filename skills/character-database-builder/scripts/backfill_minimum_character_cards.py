#!/usr/bin/env python3
"""Backfill bounded minimum cards across character graphs without inventing facts.
Creates evidence-scoped cards from pre-existing graph properties.  It does not claim
individual feats/stats/psychology that are absent from the source graph.
"""
import argparse,glob,json,os,shutil
from datetime import datetime,timezone

TYPE_USE={
 '驅逐':'近距離警戒、快速機動與護航', '輕巡':'巡洋艦隊的護航、偵察或火力支援',
 '重巡':'中型艦隊火力與防護任務', '超巡':'大型巡洋艦火力與艦隊支援',
 '戰列':'重火力支援與主力艦作戰', '戰列巡洋':'高速主力艦火力支援',
 '航空母':'以艦載航空兵器投射航空戰力', '輕航':'以較輕型航空兵器提供航空支援',
 '潛艇':'水下隱蔽、偵察或伏擊任務', '潛母':'水下平台與航空／支援任務',
 '維修':'艦隊維修與後勤支援', '運輸':'補給與運輸支援', '重炮':'遠程砲擊支援',
 '風帆':'風帆艦的航行與火力支援'
}
def val(x): return x is not None and x!='' and x!=[] and x!={}
def card_complete(c): return all(val(c.get(k)) and c.get(k)!='UNKNOWN' for k in ('what_it_does','preconditions','limits_cost_risk','observable_evidence'))
def roles(p):
 return p.get('public_identity') or p.get('public_roles') or p.get('public_role_in_this_database') or p.get('role') or p.get('identity_summary')
def ship_card(n,p):
 t=str(p.get('ship_type','艦娘個體')); use=next((v for k,v in TYPE_USE.items() if k in t),'依該個體正式艦種與遊戲內裝備／技能資料決定')
 label=n.get('label',n['id']); ev=p.get('source_evidence_urls') or n.get('source_url') or '既有圖譜的艦種、陣營、艦級與 documented_in 關係'
 return {'name':'艦種定位下的基礎戰術職能','name_zh':'艦種定位下的基礎戰術職能','category':'combat','scope_version':p.get('version_scope','碧藍航線遊戲本篇；未鎖定特定技能等級或變體'),'what_it_does':f'{label}在既有名錄中被標為{t}；此艦種定位可支持「{use}」作為場景中的基礎任務語彙，不等同個體必定具備所有同型艦的特殊技能。','basis_or_mechanism':f'既有圖譜欄位：ship_type={t}；class_or_hull={p.get("class_or_hull","UNKNOWN")}；faction={p.get("faction","UNKNOWN")}。','preconditions':'須處於艦隊／作戰情境，並有與該角色版本相符的艦裝、資源、指揮與任務授權；具體觸發、裝填、航空編隊或技能效果需回到遊戲資料。','limits_cost_risk':'艦種不是萬用能力，也不能決定人格；本卡沒有個體技能倍率、裝備、耐久、改造／META／μ兵裝條件或劇情戰績，這些一律不得自行外推。','observable_evidence':str(ev),'confidence':'INFERRED','inference_chain':'既有資料的艦種／艦級（EXTRACTED）→一般任務定位（INFERRED）；個體特殊能力與數值仍待逐一查證。','last_verified':'UNKNOWN','verification_status':'not_independently_verified'}
def public_card(n,p):
 r=roles(p); label=n.get('label',n['id']); ev=n.get('source_url') or n.get('source_file') or '既有節點 evidence／公開帳號與關係來源'
 if r:
  return {'name':'公開職能／創作活動範圍','name_zh':'公開職能／創作活動範圍','category':'professional','scope_version':p.get('version_scope','公開資料範圍'),'what_it_does':f'公開資料將{label}定位為：{r}。此卡僅描述已公開身分、作品或活動所支持的可見職能範圍。','basis_or_mechanism':'既有角色主節點的 public_identity／public_roles 與其連結來源。','preconditions':'須在公開作品、公開活動或明示的職業／創作脈絡中使用；應回查原始來源確認日期與上下文。','limits_cost_risk':'公開身分不等於經認證的熟練度、持續工作狀態、收入、私人技能或心理特質；不得從單次內容推定專業資格。','observable_evidence':str(ev),'confidence':'EXTRACTED' if n.get('source_url') or n.get('evidence') else 'AMBIGUOUS','last_verified':'UNKNOWN','verification_status':'not_independently_verified'}
 return {'name':'公開職能資料待查','name_zh':'公開職能資料待查','category':'other','scope_version':p.get('version_scope','公開資料範圍'),'what_it_does':'UNKNOWN：此節點目前僅作關係、名錄或消歧錨點，沒有可安全引用的獨立職能資料。','basis_or_mechanism':'既有圖譜未保存可回查的個體職能來源。','preconditions':'不可將其用作能力、職業或情節解法依據。','limits_cost_risk':'不得從姓名、外貌、關係或同名節點推斷技能、私生活或人格；若要升格為主角／重要 NPC，必須先個別研究。','observable_evidence':'UNKNOWN；待補可回查的公開來源或正典出場定位。','confidence':'AMBIGUOUS','last_verified':'UNKNOWN','verification_status':'not_independently_verified'}
def fictional_card(n,p):
 identity=roles(p); label=n.get('label',n['id']); ev=n.get('source_url') or n.get('source_file') or '既有圖譜文件節點、版本／正典欄位與關係'
 return {'name':'正典角色定位下的可引用職能','name_zh':'正典角色定位下的可引用職能','category':'other','scope_version':p.get('version_scope','未指定版本'),'what_it_does':f'{label}的既有定位：{identity or "UNKNOWN"}。本卡只允許依已保存的正典／版本定位使用其可見職務或敘事功能。','basis_or_mechanism':'既有角色主節點 public_identity、版本範圍與圖譜來源；不以名稱或同類角色補完。','preconditions':'需使用同一版本／媒介；涉及特殊技能、裝備、戰力或事件結果時，必須另有對應篇章／官方／遊戲證據。','limits_cost_risk':'未保存的能力保持 UNKNOWN；跨媒體版本不可混用，職務／身份也不能自動推出全能技巧或心理特質。','observable_evidence':str(ev),'confidence':'EXTRACTED' if identity else 'AMBIGUOUS','last_verified':'UNKNOWN','verification_status':'not_independently_verified'}
def anchor(p):
 return [{'trigger':'角色被故事引用','visible_action':'僅在既有來源所支持的身份、關係或版本範圍內行動；資訊不足時停止外推並列待查。','consequence':'未知能力、動機與限制不得拿來解決關鍵情節。','confidence':'AMBIGUOUS'}]
def enrich(root,dry=False):
 paths=glob.glob(os.path.join(root,'*','graphify-out','graph.json')); stats={'graphs':0,'persons':0,'cards_added':0,'complete':0,'partial':0,'archive':0}
 for path in paths:
  d=json.load(open(path)); slug=path.split(os.sep)[-3]; changed=[]
  for n in d.get('nodes',[]):
   if n.get('entity_type')!='person': continue
   stats['persons']+=1;p=n.setdefault('properties',{}); cs=p.get('capability_cards') or []
   # Preserve researched detailed cards; supplement only if no card exists.
   if not cs:
    if slug.startswith('azur-lane') and (p.get('ship_type') or p.get('class_or_hull')): c=ship_card(n,p)
    elif p.get('subject_category')=='real': c=public_card(n,p)
    else: c=fictional_card(n,p)
    cs=[c];p['capability_cards']=cs;stats['cards_added']+=1;changed.append(n['id'])
   if not p.get('behavioral_anchor'): p['behavioral_anchor']=anchor(p);changed.append(n['id'])
   old=p.get('data_completeness',{}); standalone=not p.get('not_a_full_profile') and p.get('profile_status')!='roster_catalog_only'
   detailed=any(card_complete(c) for c in cs)
   status='complete' if detailed and standalone else 'partial'
   if p.get('profile_status')=='roster_catalog_only': status='partial';standalone=False;stats['archive']+=1
   p['data_completeness']={**old,'minimum_citable_card':status,'identity_scope':'complete' if roles(p) or p.get('ship_type') else 'partial','evidence':'complete' if n.get('source_url') or n.get('evidence') or p.get('source_evidence_urls') else 'partial','capability_detail':'complete' if detailed else 'partial','behavioral_anchor':'complete' if p.get('behavioral_anchor') else 'missing','relationship_context':'complete' if any(e.get('source')==n['id'] or e.get('target')==n['id'] for e in d.get('links',[])) else 'partial'}
   p['required_before_story_use']=standalone and status!='complete'
   gaps=p.setdefault('open_research_gaps',[])
   gap='逐一補原始／官方／正典來源、版本條件、可觀察效果與限制；目前僅可在已保存範圍內引用。'
   if gap not in gaps and status!='complete': gaps.append(gap)
   stats['complete' if status=='complete' else 'partial']+=1
  if changed and not dry:
   snap=os.path.join(os.path.dirname(path),'snapshots');os.makedirs(snap,exist_ok=True);stamp=datetime.now().strftime('%Y%m%d-%H%M%S');shutil.copy2(path,os.path.join(snap,f'graph-{stamp}.json'));shutil.copy2(path,path+'.bak')
   d['graph']['updated_at']=datetime.now(timezone.utc).isoformat(); tmp=path+'.tmp';json.dump(d,open(tmp,'w'),ensure_ascii=False,indent=2);os.replace(tmp,path)
   with open(os.path.join(os.path.dirname(path),'audit.jsonl'),'a') as f:f.write(json.dumps({'at':d['graph']['updated_at'],'operation':'bounded_minimum_character_card_backfill','updated_nodes':sorted(set(changed))},ensure_ascii=False)+'\n')
  stats['graphs']+=1
 return stats
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--dry-run',action='store_true');z=a.parse_args();print(json.dumps(enrich(z.root,z.dry_run),ensure_ascii=False,indent=2))
