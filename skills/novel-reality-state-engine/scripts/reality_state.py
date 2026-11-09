#!/usr/bin/env python3
import argparse,json,math,re,sys
from pathlib import Path

def _finite_float(value):
 number=float(value)
 if not math.isfinite(number): raise ValueError('non-finite number in state JSON')
 return number

def _reject_constant(value):
 raise ValueError('non-finite number in state JSON')

def load(p):
 return json.loads(Path(p).read_text(encoding='utf-8'),parse_float=_finite_float,parse_constant=_reject_constant)

def write(p,d): Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def flat(s): return json.dumps(s,ensure_ascii=False,allow_nan=False).lower()

def validate_state(state):
 """Minimum input shape for this heuristic; not full canon/provenance validation."""
 if not isinstance(state,dict): return ['state must be an object']
 errors=[]
 events=state.get('events')
 if not isinstance(events,list) or not events:
  errors.append('missing nonempty events array')
 else:
  for index,event in enumerate(events):
   if not isinstance(event,dict):
    errors.append(f'events[{index}] must be an object')
   elif not any((isinstance(event.get(key),str) and event[key].strip()) or type(event.get(key)) is int for key in ('id','turn')):
    errors.append(f'events[{index}] requires an id or turn')
 world=state.get('world')
 if not isinstance(world,dict):
  errors.append('world must be an object')
 else:
  if not isinstance(world.get('now'),str) or not world['now'].strip(): errors.append('missing nonempty world.now')
  for key in ('resources','environment'):
   if key in world and not isinstance(world[key],dict): errors.append(f'world.{key} must be an object')
 if 'knowledge_ledger' in state and not isinstance(state['knowledge_ledger'],dict):
  errors.append('knowledge_ledger must be an object')
 if 'npcs' in state:
  npcs=state['npcs']
  if not isinstance(npcs,dict):
   errors.append('npcs must be an object')
  elif 'characters' in npcs:
   characters=npcs['characters']
   if not isinstance(characters,list):
    errors.append('npcs.characters must be an array')
   else:
    for index,character in enumerate(characters):
     if not isinstance(character,dict):
      errors.append(f'npcs.characters[{index}] must be an object')
     elif 'current_psychology' in character and not isinstance(character['current_psychology'],dict):
      errors.append(f'npcs.characters[{index}].current_psychology must be an object')
 return errors
def infer(state):
 errors=validate_state(state)
 if errors: raise ValueError('; '.join(errors))
 ev=state['events']; text=flat(ev[-8:]); characters=state.get('npcs',{}).get('characters',[])
 psych=characters[0].get('current_psychology',{}) if characters else {}
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
 if not isinstance(text,str) or not text.strip(): return ['missing nonempty draft']
 errs=[]
 if card['cognition']['long_analysis_allowed'] is False and (len(text)>1000 or any(x in text for x in ('完整整理','十種替代','四個遠期','超過兩千字','從容寫下'))): errs.append('draft too analytically continuous for current cognitive capacity')
 if card['physical']['thermal_load'] in ('cold','wet_cold') and re.search(r'comfortably|暖洋洋|毫不費力|完全不受影響',text,re.I): errs.append('draft contradicts thermal load')
 if re.search(r'身體反應.{0,20}(代表|就是).{0,10}(慾望|同意|信任)',text): errs.append('body response incorrectly equated with desire/consent/trust')
 return errs
def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest='cmd',required=True)
 for c in ('validate','card','gate'):
  q=sub.add_parser(c); q.add_argument('--state',required=True); q.add_argument('--out'); q.add_argument('--text')
 a=ap.parse_args()
 def invalid(errors):
  print(json.dumps({'ok':False,'status':'invalid_input','evaluation':'not_evaluated','errors':errors,'card':None},ensure_ascii=True))
  return 2
 try:
  s=load(a.state)
  errors=validate_state(s)
  if errors: return invalid(errors)
  text=None
  if a.cmd=='gate':
   if not a.text: return invalid(['missing draft path'])
   text=Path(a.text).read_text(encoding='utf-8')
   if not text.strip(): return invalid(['missing nonempty draft'])
  c=infer(s)
 except (OSError,ValueError) as error:
  return invalid([str(error)])
 if a.cmd=='card':
  if a.out: write(a.out,c)
  print(json.dumps(c,ensure_ascii=False,indent=2,allow_nan=False)); return 0
 errs=gate(c,text) if a.cmd=='gate' else []
 print(json.dumps({'ok':not errs,'status':'fail' if errs else 'pass','evaluation':'evaluated','errors':errs,'card':c},ensure_ascii=False,indent=2,allow_nan=False))
 return 0 if not errs else 2
if __name__=='__main__': sys.exit(main())
