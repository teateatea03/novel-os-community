from __future__ import annotations

"""Rebuild event-derived memory, context packs, and storylet availability."""

import json,re
from pathlib import Path
from typing import Any

from .canonical import deep_copy, now_iso, sha256_json
from .context import build_context
from .epistemic import filter_private
from .memory import make_episode

INPUTS_SCHEMA="minis.production-writing-inputs.v1"
USED_SOURCES_SCHEMA="minis.generation-used-sources.v1"

def discover_project_root(state:dict[str,Any]|None=None, *, store:Any=None, project_root:str|Path|None=None)->Path|None:
    """Resolve novel root from explicit arg, working state, or FileStore. Never writes canon."""
    if project_root:
        return Path(str(project_root))
    state = state if isinstance(state, dict) else {}
    for key in ("_production_project_root", "project_root"):
        value = state.get(key)
        if value:
            return Path(str(value))
    if store is not None:
        root = getattr(store, "root", None)
        if root:
            return Path(root)
    return None

def bind_generation_root(state:dict[str,Any]|None, *, store:Any=None, project_root:str|Path|None=None)->dict[str,Any]:
    """Working copy only. Canonical state is not modified."""
    working = dict(state or {})
    root = discover_project_root(working, store=store, project_root=project_root)
    if root and not working.get("_production_project_root"):
        working["_production_project_root"] = str(root)
    return working

def resolve_writing_inputs_manifest(state:dict[str,Any]|None=None, *, project_root:str|Path|None=None, store:Any=None)->tuple[Path|None, Path|None]:
    """Find verified writing-inputs without requiring a hardcoded novel slug."""
    state = state if isinstance(state, dict) else {}
    if store is not None:
        base = getattr(store, "base", None)
        if base:
            direct = Path(base) / "writing-inputs" / "manifest.json"
            if direct.is_file():
                return direct.parent, direct
    root = discover_project_root(state, store=store, project_root=project_root)
    if not root:
        return None, None
    session = str(state.get("session_id") or "")
    branch = str(state.get("branch_id") or "main")
    candidates = [
        root / "runtime" / "writing-inputs" / "manifest.json",
        root / "writing-inputs" / "manifest.json",
    ]
    if session:
        candidates.extend([
            root / "interactive" / "sessions" / session / "branches" / branch / "writing-inputs" / "manifest.json",
            root / "runtime" / "sessions" / session / "branches" / branch / "writing-inputs" / "manifest.json",
        ])
    for path in candidates:
        if path.is_file():
            return path.parent, path
    return None, None

def _safe_actor_name(actor_id:str)->str:
    text="".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(actor_id or "actor"))
    return (text or "actor")[:80]

def record_used_sources(project_root:str|Path|None, actor_id:str, used_ids:list[str], *, store:Any=None, state:dict[str,Any]|None=None, extra:dict[str,Any]|None=None)->dict[str,Any]|None:
    """Sidecar audit next to writing-inputs. Does not change context_hash or canon."""
    inputs_root, _manifest = resolve_writing_inputs_manifest(state, project_root=project_root, store=store)
    if not inputs_root:
        return None
    payload={
        "schema": USED_SOURCES_SCHEMA,
        "actor_id": actor_id,
        "used_source_ids": list(used_ids or []),
        "generated_at": now_iso(),
        "source_state_hash": (state or {}).get("state_hash"),
        "canon_write": False,
    }
    if extra:
        payload.update(extra)
    payload["report_hash"]=sha256_json({k:v for k,v in payload.items() if k!="report_hash"})
    folder=inputs_root/"used-sources"
    folder.mkdir(parents=True, exist_ok=True)
    path=folder/f"{_safe_actor_name(actor_id)}.json"
    tmp=path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    tmp.replace(path)
    return payload

def read_used_sources(project_root:str|Path|None, actor_id:str, *, store:Any=None, state:dict[str,Any]|None=None)->dict[str,Any]|None:
    inputs_root, _manifest = resolve_writing_inputs_manifest(state, project_root=project_root, store=store)
    if not inputs_root:
        return None
    path=inputs_root/"used-sources"/f"{_safe_actor_name(actor_id)}.json"
    if not path.is_file():
        return None
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None

def _event_text(event:dict[str,Any])->str:
 scene=event.get('scene') if isinstance(event.get('scene'),dict) else {}
 semantic=event.get('semantic_delta') if isinstance(event.get('semantic_delta'),dict) else {}
 return ' '.join(str(semantic.get('summary') or scene.get('summary') or event.get('summary') or f"{event.get('turn_id')} {event.get('action_type')}").split())

def _involved(event:dict[str,Any],actors:set[str])->set[str]:
 found=set();aid=str(event.get('actor_id') or '')
 if aid in actors:found.add(aid)
 text=_event_text(event).lower()
 for actor in actors:
  if re.search(rf'(?<![\w-]){re.escape(actor.lower())}(?![\w-])',text):found.add(actor)
 for op in event.get('operations',[]) if isinstance(event.get('operations'),list) else []:
  path=str(op.get('path',''))
  m=re.match(r'^/(?:actors|knowledge/npcs)/([^/]+)',path)
  if m and m.group(1) in actors:found.add(m.group(1))
 return found

def production_events(events:list[dict[str,Any]])->list[dict[str,Any]]:
 """Only accepted, replayable canonical events feed generation projections."""
 return [e for e in events if isinstance(e,dict) and (e.get('verdict') in {'allow','allow_with_cost','partial','meta'} or 'verdict' not in e)]

def project_event_memories(state:dict[str,Any],events:list[dict[str,Any]])->dict[str,list[dict[str,Any]]]:
 actors=set(state.get('actors',{}));out={a:[] for a in sorted(actors)}
 for event in production_events(events):
  event_id=event.get('event_id');turn=event.get('turn_id')
  if not event_id:continue
  text=_event_text(event);tags=[str(event.get('action_type') or 'event'),str(turn or '').lower()]
  for actor in sorted(_involved(event,actors)):
   out[actor].append(make_episode(actor,event_id=str(event_id),turn_id=str(turn) if turn else None,text=text,tags=tags,importance=2 if event.get('source')!='step3_history_migration' else 1,location=None,tick=None,visibility='private'))
 return out

def project_thread_storylets(state:dict[str,Any])->list[dict[str,Any]]:
 cards=[]
 for raw in state.get('threads',{}).get('open',[]):
  if not isinstance(raw,dict) or not raw.get('id'):continue
  status=str(raw.get('status','active'))
  if status.lower() in {'resolved','closed','completed'}:continue
  card={'id':'thread-'+str(raw['id']),'source_thread_id':str(raw['id']),'status':status,
        'pressure':str(raw.get('question') or raw.get('pressure') or 'unresolved canonical thread'),
        'priority':0,'conditions':{},'candidate_intents':[],'projection':'event_state_thread'}
  card['availability_hash']=sha256_json({'id':card['id'],'state':state.get('state_hash')})
  cards.append(card)
 return sorted(cards,key=lambda x:x['id'])

def refresh_production_writing_inputs(adapter:Any)->dict[str,Any]:
 state=adapter.store.load_state();events=adapter.store.read_events()
 if state is None:raise ValueError('production state missing')
 root=adapter.store.base/'writing-inputs';memory_dir=root/'memory';context_dir=root/'context';root.mkdir(parents=True,exist_ok=True)
 memories=project_event_memories(state,events);storylets=project_thread_storylets(state)
 memory_outputs={};context_outputs={}
 projected=deep_copy(state);projected.setdefault('memory',{})['schema']='minis.actor-memory.v2';projected['memory']['episodic']=memories;projected['memory'].setdefault('reflections',{});projected['memory'].setdefault('working',{});projected.setdefault('storylets',{})['active']=storylets
 for actor,episodes in memories.items():
  m={'schema':'minis.actor-memory-projection.v1','actor_id':actor,'source_state_hash':state.get('state_hash'),'source_events_hash':sha256_json(events),'episodes':episodes,'episode_count':len(episodes)}
  m['projection_hash']=sha256_json(m);path=memory_dir/f'{adapter.store._safe_segment(actor,"actor_id")}.json';adapter.store._atomic_json(path,m);memory_outputs[actor]={'path':str(path.relative_to(adapter.project_root)),'episode_count':len(episodes),'projection_hash':m['projection_hash']}
  pack=build_context(projected,audience='npc' if state.get('actors',{}).get(actor,{}).get('role')!='player' else 'player',actor_id=actor)
  legacy_group='player' if state.get('actors',{}).get(actor,{}).get('role')=='player' else 'npcs'
  legacy_record=state.get('knowledge',{}).get(legacy_group,{}).get(actor,{})
  pack['legacy_knowledge']=filter_private(legacy_record if isinstance(legacy_record,dict) else {'fact_ids':legacy_record})
  pack['legacy_knowledge_provenance']={'mode':'canonical_state_checkpoint_and_events','inline_claims_complete':False,'source_state_hash':state.get('state_hash')}
  pack['schema']='minis.production-context-pack.v1'
  pack['source_manifest']={'state_hash':state.get('state_hash'),'events_hash':sha256_json(events),'event_head':state.get('events_head'),'actor_memory_hash':m['projection_hash'],'storylet_hash':sha256_json(storylets)}
  pack['selected_source_ids']=[x['memory_id'] for x in pack.get('memory_context',{}).get('memories',[])]
  pack['addressable_source_ids']=[x.get('memory_id') for x in episodes if x.get('memory_id')]
  pack['used_source_ids']=None
  pack['context_hash']=sha256_json({k:v for k,v in pack.items() if k!='context_hash'})
  cpath=context_dir/f'{adapter.store._safe_segment(actor,"actor_id")}.json';adapter.store._atomic_json(cpath,pack);context_outputs[actor]={'path':str(cpath.relative_to(adapter.project_root)),'context_hash':pack['context_hash'],'selected_source_count':len(pack['selected_source_ids']),'addressable_source_count':len(pack['addressable_source_ids'])}
 story={'schema':'minis.storylet-availability-projection.v1','source_state_hash':state.get('state_hash'),'source_events_hash':sha256_json(events),'available':storylets,'count':len(storylets)};story['projection_hash']=sha256_json(story);adapter.store._atomic_json(root/'storylets.json',story)
 manifest={'schema':INPUTS_SCHEMA,'generated_at':now_iso(),'source_state_hash':state.get('state_hash'),'source_event_head':state.get('events_head'),'source_events_hash':sha256_json(events),'event_count':len(events),'memory':memory_outputs,'context':context_outputs,'storylets':{'path':str((root/'storylets.json').relative_to(adapter.project_root)),'count':len(storylets),'projection_hash':story['projection_hash']}}
 manifest['manifest_hash']=sha256_json(manifest);adapter.store._atomic_json(root/'manifest.json',manifest);return manifest

def _file_sha256(path:Path)->str:
 import hashlib
 return hashlib.sha256(path.read_bytes()).hexdigest()

def production_writing_inputs_status(adapter:Any)->dict[str,Any]:
 state=adapter.store.load_state() or {};events=adapter.store.read_events();path=adapter.store.base/'writing-inputs/manifest.json';m=adapter.store._read_json(path,{}) or {};errors=[]
 expected={'source_state_hash':state.get('state_hash'),'source_event_head':state.get('events_head'),'source_events_hash':sha256_json(events),'event_count':len(events)}
 if not path.is_file():errors.append('missing_manifest')
 for k,v in expected.items():
  if m.get(k)!=v:errors.append(k+'_stale')
 if m and m.get('manifest_hash')!=sha256_json({k:v for k,v in m.items() if k!='manifest_hash'}):errors.append('manifest_hash_mismatch')
 for section in ('memory','context'):
  for actor,meta in (m.get(section,{}) if isinstance(m.get(section),dict) else {}).items():
   target=adapter.project_root/meta.get('path','')
   if not target.is_file():errors.append(f'missing:{section}:{actor}');continue
   value=adapter.store._read_json(target,{}) or {}
   key='projection_hash' if section=='memory' else 'context_hash'
   if value.get(key)!=meta.get(key):errors.append(f'{section}_hash_mismatch:{actor}')
   if section=='memory' and value.get('source_events_hash')!=expected['source_events_hash']:errors.append(f'memory_source_stale:{actor}')
   if section=='context':
    manifest=value.get('source_manifest',{})
    if manifest.get('state_hash')!=expected['source_state_hash'] or manifest.get('events_hash')!=expected['source_events_hash']:errors.append(f'context_source_stale:{actor}')
 story_meta=m.get('storylets') or {};story_path=adapter.project_root/story_meta.get('path','')
 if not story_path.is_file():errors.append('missing:storylets')
 else:
  story=adapter.store._read_json(story_path,{}) or {}
  if story.get('projection_hash')!=story_meta.get('projection_hash'):errors.append('storylets_hash_mismatch')
  if story.get('source_events_hash')!=expected['source_events_hash']:errors.append('storylets_source_stale')
 actor_count=len(state.get('actors',{}));episode_count=sum(int(x.get('episode_count',0)) for x in (m.get('memory',{}) or {}).values());context_count=len(m.get('context',{}) or {})
 if actor_count and episode_count==0 and expected['event_count']:errors.append('unexpectedly_empty_memory')
 if context_count!=actor_count and expected['event_count']:errors.append('context_actor_coverage')
 return {'schema':'minis.production-writing-inputs-status.v1','status':'pass' if not errors else 'stale','stale':bool(errors),'errors':errors,'actor_count':actor_count,'episode_count':episode_count,'context_count':context_count,'storylet_count':(m.get('storylets') or {}).get('count',0),'manifest':m,'expected':expected}
