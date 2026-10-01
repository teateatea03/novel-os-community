from __future__ import annotations
"""Deterministic semantic state invariants and grandfathered migration debt."""
import copy, datetime as dt, re
from typing import Any
from .canonical import sha256_json
from .delta import apply_operations
from .errors import JudgeError

SCHEMA='minis.semantic-invariant-report.v1';POLICY_SCHEMA='minis.semantic-invariant-policy.v1'
NON_OVERRIDABLE={'ACTOR_LOCATION_CONFLICT','CLOCK_NOW_REVERSED','CLOCK_TICK_REVERSED','OBJECT_HOLDER_LOCATION_CONFLICT','THREAD_LIFECYCLE_CONFLICT','FACET_INTERVAL_INVALID','KNOWLEDGE_AUTHORITY_VIOLATION'}

def _issue(code,severity,confidence,path,message,repair,**details):
 v={'code':code,'severity':severity,'confidence':confidence,'path':path,'message':message,'minimal_repair':repair,'details':details}
 v['fingerprint']=sha256_json({k:v[k] for k in ('code','path')});return v

def _iso(v):
 try:return dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
 except Exception:return None

def _turn_num(v):
 m=re.match(r'^T(\d+)',str(v or ''));return int(m.group(1)) if m else None

def inspect_state(state:dict[str,Any])->dict[str,Any]:
 issues=[];actors=state.get('actors',{});objects=state.get('world_truth',{}).get('objects',{})
 for aid,a in sorted(actors.items()):
  if not isinstance(a,dict):continue
  loc=a.get('location');cond=a.get('condition') if isinstance(a.get('condition'),dict) else {}
  cloc=cond.get('location')
  if loc and cloc and loc!=cloc:issues.append(_issue('ACTOR_LOCATION_CONFLICT','P0','high',f'/actors/{aid}/condition/location','actor.location and condition.location disagree','replace or expire the stale condition.location',actor_id=aid,actor_location=loc,condition_location=cloc))
  pos=cond.get('position')
  if isinstance(pos,str) and pos and any(x in pos.lower() for x in ('bath','浴池','浴缸','bed','床上','dining table','餐桌')):
   loc_text=str(loc or '').lower()
   cues={'bath':('bath','浴'),'浴池':('bath','浴'),'浴缸':('bath','浴'),'bed':('bed','bedroom','臥室'),'床上':('bed','bedroom','臥室'),'dining table':('dining','餐'),'餐桌':('dining','餐')}
   matched=[k for k in cues if k in pos.lower()]
   if matched and not any(any(x in loc_text for x in cues[k]) for k in matched):issues.append(_issue('STALE_POSITION_FACET','P1','medium',f'/actors/{aid}/condition/position','position text implies a different place than actor.location','expire/supersede the old position facet or replace it with current position',actor_id=aid,location=loc,position=pos))
  for key,val in cond.items():
   if isinstance(val,dict) and any(k in val for k in ('value','valid_from','valid_to','supersedes')):
    start=_iso(val.get('valid_from')) if val.get('valid_from') else None;end=_iso(val.get('valid_to')) if val.get('valid_to') else None
    if start and end and end<start:issues.append(_issue('FACET_INTERVAL_INVALID','P0','high',f'/actors/{aid}/condition/{key}','valid_to precedes valid_from','correct the interval or supersede with a new facet',actor_id=aid,facet=key))
    if val.get('supersedes')==val.get('id') and val.get('id'):issues.append(_issue('FACET_SUPERSEDES_SELF','P0','high',f'/actors/{aid}/condition/{key}','facet supersedes itself','point supersedes to the prior facet id',actor_id=aid,facet=key))
 for oid,o in sorted(objects.items()):
  if not isinstance(o,dict):continue
  holder=o.get('holder');loc=o.get('location')
  if holder is not None and loc is not None and holder!=loc:issues.append(_issue('OBJECT_HOLDER_LOCATION_CONFLICT','P0','high',f'/world_truth/objects/{oid}','object has both a holder and an independent location','set location=null while held, or holder=null while placed',object_id=oid,holder=holder,location=loc))
  if holder in actors and oid not in (actors[holder].get('inventory') or []):issues.append(_issue('OBJECT_INVENTORY_MISMATCH','P1','high',f'/world_truth/objects/{oid}/holder','object holder does not list object in inventory','add object to holder inventory or correct holder',object_id=oid,holder=holder))
 for aid,a in sorted(actors.items()):
  for oid in a.get('inventory',[]) if isinstance(a,dict) else []:
   if oid in objects and objects[oid].get('holder') not in {aid,None}:issues.append(_issue('INVENTORY_HOLDER_MISMATCH','P1','high',f'/actors/{aid}/inventory','inventory conflicts with object holder','align object holder and actor inventory',actor_id=aid,object_id=oid,holder=objects[oid].get('holder')))
 threads=state.get('threads',{});opens=threads.get('open',[]) if isinstance(threads,dict) else [];resolved=threads.get('resolved',[]) if isinstance(threads,dict) else []
 def ids(xs):return [str(x.get('id')) for x in xs if isinstance(x,dict) and x.get('id')]
 oi,ri=ids(opens),ids(resolved)
 for x in sorted(set(oi)&set(ri)):issues.append(_issue('THREAD_LIFECYCLE_CONFLICT','P0','high',f'/threads/{x}','thread is both open and resolved','remove it from one lifecycle collection and preserve a resolution event',thread_id=x))
 for x in sorted(set(i for i in oi if oi.count(i)>1)):issues.append(_issue('THREAD_DUPLICATE_OPEN','P0','high',f'/threads/open/{x}','open thread id is duplicated','keep one authoritative open record',thread_id=x))
 head_n=_turn_num(state.get('last_turn_id'))
 for i,t in enumerate(opens):
  if not isinstance(t,dict):continue
  status=str(t.get('status','')).lower()
  if any(status.startswith(x) for x in ('resolved','closed','completed','done')):issues.append(_issue('RESOLVED_THREAD_LEFT_OPEN','P0','high',f'/threads/open/{i}','resolved-status thread remains in open collection','move it to threads.resolved with resolved_at/source event',thread_id=t.get('id'),status=status))
  last=_turn_num(t.get('last_touched'))
  if head_n is not None and last is not None and head_n-last>=20:issues.append(_issue('STALE_OPEN_THREAD','P2','medium',f'/threads/open/{i}','open thread has not been reconciled for 20+ turns','confirm still open or move to resolved/dormant with provenance',thread_id=t.get('id'),last_touched=t.get('last_touched')))
 clock=state.get('clock',{})
 if not isinstance(clock.get('tick'),int) or clock.get('tick',0)<0:issues.append(_issue('CLOCK_TICK_INVALID','P0','high','/clock/tick','clock tick must be a non-negative integer','write a non-negative monotonic tick'))
 if clock.get('now') and _iso(clock.get('now')) is None:issues.append(_issue('CLOCK_NOW_INVALID','P0','high','/clock/now','clock.now is not ISO-8601','write an ISO-8601 timestamp with timezone'))
 # Knowledge remains event-provenanced but legacy scalar/list facts are migration debt.
 for group in ('player','npcs','reader'):
  for aid,rec in (state.get('knowledge',{}).get(group,{}) or {}).items():
   if isinstance(rec,dict):
    for key,val in rec.items():
     if isinstance(val,list) and val and any(not isinstance(x,dict) for x in val):issues.append(_issue('LEGACY_KNOWLEDGE_WITHOUT_INLINE_PROVENANCE','P2','medium',f'/knowledge/{group}/{aid}/{key}','knowledge facts rely on event/checkpoint provenance rather than inline source records','on next fact change, use sourced claim records or preserve event id',actor_id=aid,field=key))
 report={'schema':SCHEMA,'state_hash':state.get('state_hash'),'last_turn_id':state.get('last_turn_id'),'issues':issues,'counts':{s:sum(x['severity']==s for x in issues) for s in ('P0','P1','P2')}}
 report['report_hash']=sha256_json(report);return report

def inspect_transition(before:dict[str,Any],after:dict[str,Any],*,operations:list[dict[str,Any]])->dict[str,Any]:
 b=inspect_state(before);a=inspect_state(after);bf={x['fingerprint'] for x in b['issues']};new=[x for x in a['issues'] if x['fingerprint'] not in bf]
 bc=before.get('clock',{});ac=after.get('clock',{});extra=[]
 if isinstance(bc.get('tick'),int) and isinstance(ac.get('tick'),int) and ac['tick']<bc['tick']:extra.append(_issue('CLOCK_TICK_REVERSED','P0','high','/clock/tick','clock tick moved backward','use a tick >= current tick',before=bc['tick'],after=ac['tick']))
 bi,ai=_iso(bc.get('now')),_iso(ac.get('now'))
 if bi and ai and ai<bi:extra.append(_issue('CLOCK_NOW_REVERSED','P0','high','/clock/now','simulation time moved backward','use a timestamp >= current time or create an explicit branch',before=bc.get('now'),after=ac.get('now')))
 new+=extra;block=[x for x in new if x['severity']=='P0' and x['confidence']=='high']
 r={'schema':'minis.semantic-invariant-transition.v1','before_state_hash':before.get('state_hash'),'candidate_operation_hash':sha256_json(operations),'legacy_issue_fingerprints':sorted(bf),'after_issues':a['issues'],'new_issues':new,'blockers':block,'status':'blocked' if block else 'pass'};r['report_hash']=sha256_json(r);return r

def apply_and_check(before:dict[str,Any],operations:list[dict[str,Any]])->tuple[dict[str,Any],dict[str,Any]]:
 after=apply_operations(before,operations,source='author');return after,inspect_transition(before,after,operations=operations)

def enforce_transition(before:dict[str,Any],operations:list[dict[str,Any]])->dict[str,Any]:
 _,report=apply_and_check(before,operations)
 if report['blockers']:raise JudgeError('SEMANTIC_INVARIANT_FAILED','candidate introduces new high-confidence semantic invariant violations',details=report)
 return report
