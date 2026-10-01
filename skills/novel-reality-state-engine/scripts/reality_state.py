#!/usr/bin/env python3
import argparse,json,re,sys
from pathlib import Path

def load(p): return json.loads(Path(p).read_text())
def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def flat(s): return json.dumps(s,ensure_ascii=False).lower()
def infer(state):
 ev=state.get('events',[]); text=flat(ev[-8:]); psych=state.get('npcs',{}).get('characters',[{}])[0].get('current_psychology',{})
 world=state.get('world',{}); res=world.get('resources',{})
 food_resource=str(res.get('food','')).lower()
 event_text=' '.join(str(e) for e in ev[-12:])
 recent_text=' '.join(str(e) for e in ev[-2:])
 food='none' if food_resource in ('none','empty','unavailable') or ('no food' in text or '沒有食物' in text or 'no_meal' in text) or any(x in recent_text for x in ('food_absence',)) else 'unknown'
 if food != 'none' and ('粥' in text or 'porridge' in text or food_resource in ('recent','available','meal')): food='recent'
 water='available' if str(res.get('water','')).lower() in ('available','present','plain') or ('water' in text or '水' in text) else 'unknown'
 cold='wet_cold' if ('冷水' in text or 'cold' in text) and (world.get('environment',{}).get('wet') is True or 'wet' in text or '灑水' in event_text) else ('cold' if 'cold' in text or '寒' in text or world.get('environment',{}).get('temperature')=='cold' else 'unknown')
 meal_gap='high' if food=='none' else 'rising'
 clarity='fragmented_clear' if meal_gap=='high' or cold in ('cold','wet_cold') else 'clear'
 return {'as_of':world.get('now','unknown'),'last_events':[e.get('id',e.get('turn')) for e in ev[-8:]],'physical':{'hunger':meal_gap,'thirst':'rising' if water=='available' else 'unknown','fatigue':'high' if meal_gap=='high' else 'moderate','thermal_load':cold,'pain_or_drug_effect':'uncertain'},'cognition':{'clarity':clarity,'working_memory':'reduced' if clarity!='clear' else 'normal','planning_horizon':'minutes' if clarity!='clear' else 'hours','speech':'shorter' if clarity!='clear' else 'full','long_analysis_allowed':clarity=='clear'},'psychology':psych,'affordances':['drink available water','conserve movement','short request for food','listen for external cues'],'likely_errors':['repeat thoughts','act before full analysis','misread absence as intention'],'knowledge_boundary':state.get('knowledge_ledger',{}),'state_confidence':'medium' if len(ev)>=2 else 'low'}
def gate(card,text):
 errs=[]
 if card['cognition']['long_analysis_allowed'] is False and (len(text)>1000 or any(x in text for x in ('完整整理','十種替代','四個遠期','超過兩千字','從容寫下'))): errs.append('draft too analytically continuous for current cognitive capacity')
 if card['physical']['thermal_load'] in ('cold','wet_cold') and re.search(r'comfortably|暖洋洋|毫不費力|完全不受影響',text,re.I): errs.append('draft contradicts thermal load')
 if re.search(r'身體反應.{0,20}(代表|就是).{0,10}(慾望|同意|信任)',text): errs.append('body response incorrectly equated with desire/consent/trust')
 return errs
def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 for c in ('validate','card','gate'):
  q=sub.add_parser(c); q.add_argument('--state',required=True); q.add_argument('--out'); q.add_argument('--text')
 a=ap.parse_args(); s=load(a.state); c=infer(s)
 if a.cmd=='card':
  if a.out: write(a.out,c)
  print(json.dumps(c,ensure_ascii=False,indent=2)); return 0
 if a.cmd=='validate':
  errs=[]
  if not s.get('events'): errs.append('missing events')
  if not s.get('world',{}).get('now'): errs.append('missing world.now')
  print(json.dumps({'ok':not errs,'errors':errs,'card':c},ensure_ascii=False,indent=2)); return 0 if not errs else 2
 errs=gate(c,Path(a.text).read_text() if a.text else '')
 print(json.dumps({'ok':not errs,'errors':errs,'card':c},ensure_ascii=False,indent=2)); return 0 if not errs else 2
if __name__=='__main__': sys.exit(main())
