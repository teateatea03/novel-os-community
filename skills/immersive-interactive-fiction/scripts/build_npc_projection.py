#!/usr/bin/env python3
"""Build an egocentric, bounded NPC context projection from canonical state.

The caller supplies the scene-local visible facts and a single noticed point.
This prevents handing an NPC the global open-pressure list or other actors'
private state by default.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--state',required=True); ap.add_argument('--registry',required=True)
    ap.add_argument('--actor',required=True); ap.add_argument('--noticed-one',default='')
    ap.add_argument('--trigger',default=''); ap.add_argument('--visible-fact',action='append',default=[])
    ap.add_argument('--act',required=True); ap.add_argument('--out',required=True)
    a=ap.parse_args(); state=yaml.safe_load(Path(a.state).read_text()); registry=json.loads(Path(a.registry).read_text())
    if a.actor not in registry.get('actors',{}): raise SystemExit('UNREGISTERED_NPC')
    root=Path(a.registry).parent; cp=root/registry['actors'][a.actor]['contract']; contract=json.loads(cp.read_text())
    actor_state=(state.get('npcs') or {}).get(a.actor,{})
    allowed=contract.get('allowed_dialogue_acts',[])
    if a.act not in allowed: raise SystemExit(f'FORBIDDEN_ACT:{a.act}')
    projection={
      'schema':'minis.npc-egocentric-projection.v1', 'scene_turn':state.get('turn'),
      'actor':a.actor, 'actor_kind':registry['actors'][a.actor]['kind'],
      'location':{'name':(state.get('location') or {}).get('name'), 'time':(state.get('time') or {}).get('clock')},
      'local_actor_state':{k:actor_state.get(k) for k in ('position','body','boundary','lodging_decision','mood_signals_observable') if k in actor_state},
      'trigger':a.trigger, 'noticed_one':a.noticed_one or None,
      'visible_facts':a.visible_fact, 'dialogue_act':a.act,
      'limits':{'max_sentences':contract.get('max_sentences'),'max_information_units':contract.get('max_information_units')},
      'allowed_dialogue_acts':allowed, 'forbidden_dialogue_acts':contract.get('forbidden_dialogue_acts',[]),
      'fallback_ladder':contract.get('fallback_ladder',[]), 'positive_examples':contract.get('positive_examples',[]),
      'excluded_by_design':['global_open_pressure','other_npc_private_state','other_actor_internal_state','unselected_event_ledger']
    }
    Path(a.out).write_text(json.dumps(projection,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(projection,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
