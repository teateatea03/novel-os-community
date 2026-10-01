#!/usr/bin/env python3
"""Phase C generalization pilot: second project and 100k+ traditional novel."""
from __future__ import annotations
import argparse,hashlib,json,random,subprocess,sys,tempfile,time
from pathlib import Path

JUDGE=Path(__file__).resolve().parents[2] / 'immersive-interactive-fiction' / 'scripts'
LONG=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(JUDGE))
from novel_judge import ProjectRuntimeAdapter,make_gate_envelope
from novel_judge.longform import initialize_longform_production,commit_scene_event
from novel_judge.canonical import sha256_json
from novel_judge.event_log import verify_event_log_integrity


def approve(a,turn,scene_hash,state_hash,operations=None,actor_id='world',action_type='scene_commit',summary=None,scene_id=None,chapter_id=None):
 from novel_judge.production import make_candidate_binding
 from novel_judge.semantic_events import compile_semantic_delta
 ops=operations or []
 sem=compile_semantic_delta(turn_id=turn,actor_id=actor_id,action_type=action_type,operations=ops,summary=summary,scene_id=scene_id)
 binding=make_candidate_binding(turn_id=turn,operations=ops,actor_id=actor_id,action_type=action_type,summary=summary,scene_id=scene_id,chapter_id=chapter_id,scene_sha256=scene_hash,semantic_hash=sem['semantic_hash'])
 env=[make_gate_envelope(gate_type=g,turn_id=turn,scene_sha256=scene_hash,source_state_hash=state_hash) for g in a.gate_policy()['required_gate_types']]
 return a.approve_gate_bundle(turn_id=turn,scene_sha256=scene_hash,source_state_hash=state_hash,envelopes=env,candidate_binding=binding)

def second_project_probe(root:Path):
 # Independently generated synthetic project; no external story tree is loaded.
 a=ProjectRuntimeAdapter(root,'synthetic-observatory-pilot','manuscript','main',namespace='runtime')
 from novel_judge.longform import init_longform_state
 a.initialize_new_project(init_longform_state('synthetic-observatory-pilot'),baseline_id='synthetic-empty-baseline',provenance={'mode':'isolated_second_project_probe','synthetic':True,'external_source_loaded':False})
 artifact=root/'chapters/chapter-001.md';artifact.parent.mkdir(parents=True);artifact.write_text('觀測站的合成測試：技術員核對鏡頭蓋編號。',encoding='utf-8');h=hashlib.sha256(artifact.read_bytes()).hexdigest();s=a.store.load_state();ops=[{'op':'add','path':'/world_truth/events/OBS-PROBE-001','value':{'summary':'isolated contract probe'}}];approve(a,'OBS-PROBE-001',h,s['state_hash'],ops,scene_id='OBS-PROBE-001',chapter_id='chapter-001',summary='Second-project isolated production contract probe')
 r=commit_scene_event(a,scene_id='OBS-PROBE-001',chapter_id='chapter-001',operations=[{'op':'add','path':'/world_truth/events/OBS-PROBE-001','value':{'summary':'isolated contract probe'}}],summary='Second-project isolated production contract probe',author_approved=True,expected_state_hash=s['state_hash'],source_artifact_hash=h,source_artifact_path='chapters/chapter-001.md',scene_sha256=h)
 return {'status':'pass','event':r['event'],'conformance':a.assert_conformant(),'integrity':verify_event_log_integrity(a.store),'external_source_loaded':False}

def longform_100k(root:Path,chapters:int=40):
 a=initialize_longform_production(root,'traditional-100k-pilot',provenance={'purpose':'Phase C 100k+ generalization pilot'});started=time.time();total=0
 for i in range(1,chapters+1):
  cid=f'chapter-{i:03d}';turn=f'scene-{i:03d}-01';motif='潮汐檔案' if i%7==0 else '城市通訊';body=(f'# {cid}\n\n'+('角色沿著'+motif+'核對資訊、資源、時間與承諾。視角只使用當下可知內容。\n')*95)
  p=root/'chapters'/f'{cid}.md';p.parent.mkdir(exist_ok=True);p.write_text(body,encoding='utf-8');total+=len(body)
  h=hashlib.sha256(p.read_bytes()).hexdigest();s=a.store.load_state();ops=[{'op':'add','path':f'/world_truth/events/{turn}','value':{'summary':f'{cid} canonical scene','chapter':cid,'knowledge_reversal':i==21}}];approve(a,turn,h,s['state_hash'],ops,scene_id=turn,chapter_id=cid,summary=f'{cid}: the investigation advances with bounded knowledge')
  commit_scene_event(a,scene_id=turn,chapter_id=cid,operations=ops,summary=f'{cid}: the investigation advances with bounded knowledge',author_approved=True,expected_state_hash=s['state_hash'],source_artifact_hash=h,source_artifact_path=f'chapters/{cid}.md',scene_sha256=h)
 # Mid-book reversal and rewrite cascade are derivative-only probes.
 cmd=[sys.executable,str(LONG/'scripts/cascade_impact.py'),'--root',str(root),'--query','潮汐檔案 中段知識反轉','--mark'];cascade=subprocess.run(cmd,capture_output=True,text=True)
 cmd=[sys.executable,str(LONG/'scripts/build_story_index.py'),'--root',str(root)];index=subprocess.run(cmd,capture_output=True,text=True)
 cmd=[sys.executable,str(LONG/'scripts/build_context_pack.py'),'--root',str(root),'--chapter','chapter-021','--query','潮汐檔案 知識反轉'];context=subprocess.run(cmd,capture_output=True,text=True)
 events=a.store.read_events();replayed=a.read_state_at();return {'status':'pass' if cascade.returncode==index.returncode==context.returncode==0 else 'fail','chapters':chapters,'characters':total,'over_100k':total>100000,'events':len(events),'typed_semantic_count':sum(bool(e.get('semantic_delta_hash')) for e in events),'knowledge_reversal_chapter':21,'cascade':json.loads(cascade.stdout) if cascade.returncode==0 else {'error':cascade.stderr},'index_ok':index.returncode==0,'context_ok':context.returncode==0,'replay_matches':replayed.get('state_hash')==a.store.load_state().get('state_hash'),'conformance':a.assert_conformant(),'integrity':verify_event_log_integrity(a.store),'elapsed_seconds':round(time.time()-started,3)}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
 with tempfile.TemporaryDirectory(prefix='novel-os-phase-c-') as td:
  base=Path(td);report={'schema':'minis.phase-c-generalization-pilot.v1','second_project':second_project_probe(base/'synthetic-observatory-isolated'),'traditional_longform':longform_100k(base/'traditional-100k')}
  report['status']='pass' if report['second_project']['status']==report['traditional_longform']['status']=='pass' and report['traditional_longform']['over_100k'] else 'fail';report['report_hash']=sha256_json(report);Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2));return 0 if report['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
