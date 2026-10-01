from __future__ import annotations
"""Quality Eval v2: explicit truth, observed revisions, and proxies never mix."""
import difflib,hashlib,json,re,statistics
from pathlib import Path
from typing import Any
from .canonical import now_iso,sha256_json

SCHEMA='minis.author-quality-eval.v2';FIXTURE_SCHEMA='minis.author-quality-fixture.v2'
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
def _adapter_for_root(project_root:str|Path):
 try:
  from .author_resume import load_project_adapter
  return load_project_adapter(project_root)
 except Exception:
  return None
def _candidate_dirs(root:Path, adapter:Any|None)->list[Path]:
 dirs=[]
 if adapter is not None:
  dirs.append(Path(adapter.store.base)/'candidates')
 dirs.extend(sorted(root.glob('interactive/sessions/*/branches/*/candidates')))
 seen=set(); out=[]
 for d in dirs:
  key=str(d)
  if key in seen or not d.is_dir():
   continue
  seen.add(key); out.append(d)
 return out
def _event_rows(adapter:Any|None)->list[dict[str,Any]]:
 if adapter is None:
  return []
 path=adapter.store.events_path
 if not path.is_file():
  return []
 rows=[]
 for line in path.read_text(encoding='utf-8').splitlines():
  if not line.strip():
   continue
  event=json.loads(line)
  if event.get('verdict') in {'allow','allow_with_cost','partial','meta'}:
   rows.append(event)
 return rows

def text_stats(a:str,b:str)->dict[str,Any]:
 sm=difflib.SequenceMatcher(a=a,b=b,autojunk=False);changed=[]
 for tag,i1,i2,j1,j2 in sm.get_opcodes():
  if tag!='equal':changed.append({'tag':tag,'before':[i1,i2],'after':[j1,j2],'before_chars':i2-i1,'after_chars':j2-j1})
 return {'similarity':round(sm.ratio(),6),'normalized_edit_distance':round(1-sm.ratio(),6),'changed_span_count':len(changed),'changed_chars_before':sum(x['before_chars'] for x in changed),'changed_chars_after':sum(x['after_chars'] for x in changed),'changed_spans':changed[:200]}
def category(turn:str,snapshot:str)->list[str]:
 s=(turn+' '+snapshot).lower();out=[]
 for needle,label in [('voice','character_voice'),('human','human_voice'),('prose','prose_style'),('grammar','clarity'),('badge','agency'),('continuity','continuity'),('timeline','pacing'),('sound','sensory_sound'),('intimacy','relationship'),('meal','continuity')]:
  if needle in s:out.append(label)
 return out or ['other']
def _split(lineage:str)->str:return 'hidden_test' if int(hashlib.sha256(lineage.encode()).hexdigest()[:8],16)%5==0 else 'calibration'
def _write_records(out:Path,records:list[dict[str,Any]])->None:
 keep={f"{r['fixture_id']}.json" for r in records}
 for old in out.glob('*.json'):
  if old.name not in keep and old.name not in {'manifest.json','baseline-report.json'}:old.unlink()
 for r in records:(out/f"{r['fixture_id']}.json").write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
def build_project_fixtures(project_root:str|Path,output:str|Path,*,minimum:int=50)->dict[str,Any]:
 root=Path(project_root);out=Path(output);out.mkdir(parents=True,exist_ok=True);current=root/'interactive/scenes';records=[]
 # One latest before→current pair per scene lineage. Older snapshots are not
 # repeated independent preferences for the same accepted artifact.
 latest={}
 snapshots=root/'snapshots'
 for d in sorted(snapshots.iterdir()) if snapshots.is_dir() else []:
  scenes=d/'interactive/scenes'
  if not scenes.is_dir():continue
  for before in sorted(scenes.glob('T*.md')):
   after=current/before.name
   if after.is_file() and before.read_bytes()!=after.read_bytes():
    previous=latest.get(before.stem);cats=set(category(before.stem,d.name))
    if previous:cats.update(previous[3])
    latest[before.stem]=(d,before,after,sorted(cats))
 for turn,(d,before,after,categories) in sorted(latest.items()):
  bt,at=before.read_text(),after.read_text();lineage=f'{root.name}:{turn}'
  records.append({'schema':FIXTURE_SCHEMA,'fixture_id':f'pair-{d.name}-{turn}','kind':'observed_revision_pair','turn_id':turn,'lineage_id':lineage,'split':_split(lineage),'author_preference':'after','explicit_author_decision':False,'before':{'path':str(before.relative_to(root)),'sha256':sha(before),'chars':len(bt)},'after':{'path':str(after.relative_to(root)),'sha256':sha(after),'chars':len(at)},'categories':categories,'evidence':{'snapshot':d.name,'status':'observed_file_revision','lineage_deduplicated':True,'categories_accumulated_across_lineage':True},'diff':text_stats(bt,at)})
 for label in ('approved','rejected'):
  directory=root/f'interactive/prose-fixtures/{label}'
  for p in sorted(directory.glob('*.md')) if directory.is_dir() else []:
   lineage=f'curated:{p.stem}'
   records.append({'schema':FIXTURE_SCHEMA,'fixture_id':f'label-{label}-{p.stem}','kind':'curated_quality_label','lineage_id':lineage,'split':_split(lineage),'quality_label':label,'explicit_author_decision':True,'artifact':{'path':str(p.relative_to(root)),'sha256':sha(p),'chars':len(p.read_text())},'categories':[label,'prose_quality'],'evidence':{'directory_label':label}})
 # Feedback is the only direct candidate-decision truth for pass@1.
 try:
  adapter=_adapter_for_root(root)
  from .author_feedback import read_author_feedback
  for f in read_author_feedback(adapter.store) if adapter is not None else []:
   lineage=f"feedback:{f.get('scene_id') or f.get('turn_id') or f['candidate_hash']}"
   rr=f.get('revision_round');passed=f['decision']=='accept' and (rr in {None,0})
   records.append({'schema':FIXTURE_SCHEMA,'fixture_id':f['event_id'],'kind':'explicit_author_feedback','turn_id':f.get('turn_id'),'lineage_id':lineage,'split':_split(lineage),'candidate_hash':f['candidate_hash'],'author_decision':f['decision'],'gate_pass':f.get('gate_pass'),'explicit_author_decision':True,'explicit_pass_at_1':passed if f['decision']=='accept' else False,'revision_rounds_to_accept':rr if f['decision']=='accept' else None,'categories':f.get('reason_codes') or ['other'],'changed_spans':f.get('changed_spans',[]),'evidence':{'feedback_event_hash':f['event_hash']}})
 except (OSError,ValueError,KeyError):pass
 # Workflow observations remain proxies and are excluded from author truth.
 adapter=_adapter_for_root(root)
 for cand in _candidate_dirs(root, adapter):
  for d in sorted(cand.glob('T*')):
   p=d/'candidate.json'
   if not p.is_file():continue
   c=json.loads(p.read_text());
   if c.get('status')!='committed':continue
   rev=sum(x.get('action')=='author_revision' for x in c.get('history',[]));lineage=f'workflow:{d.name}'
   records.append({'schema':FIXTURE_SCHEMA,'fixture_id':f'proxy-committed-{d.name}','kind':'workflow_commit_proxy','turn_id':d.name,'lineage_id':lineage,'split':'telemetry_only','explicit_author_decision':False,'proxy_pass_at_1':rev==0,'proxy_revision_rounds':rev,'categories':['production_proxy'],'evidence':{'candidate_path':str(p.relative_to(root)),'confidence':'proxy_not_explicit'}})
 _write_records(out,records)
 manifest={'schema':'minis.author-quality-fixture-manifest.v2','project_id':root.name,'fixture_count':len(records),'lineage_count':len({r['lineage_id'] for r in records}),'explicit_feedback_count':sum(r['kind']=='explicit_author_feedback' for r in records),'observed_pair_count':sum(r['kind']=='observed_revision_pair' for r in records),'proxy_count':sum(r['kind']=='workflow_commit_proxy' for r in records),'split_counts':{s:sum(r['split']==s for r in records) for s in ('calibration','hidden_test','telemetry_only')},'minimum_target':minimum,'minimum_is_not_filled_with_duplicate_lineages':True,'fixtures':[{'id':r['fixture_id'],'sha256':sha(out/f"{r['fixture_id']}.json")} for r in records],'built_at':now_iso()};manifest['manifest_hash']=sha256_json(manifest);(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n');return manifest
def production_quality_telemetry(project_root:str|Path)->dict[str,Any]:
 adapter=_adapter_for_root(project_root)
 events=_event_rows(adapter)
 rows=[]
 for e in events:rows.append({'turn_id':e.get('turn_id'),'event_id':e.get('event_id'),'created_at':e.get('created_at'),'semantic_delta_hash':e.get('semantic_delta_hash'),'status':'committed','gate_authorized':bool(e.get('gate_authorization_hash')),'typed_semantic':bool(e.get('semantic_delta_hash')),'author_decision':None})
 feedback=[];typed_activated=None
 if adapter is not None:
  try:
   from .author_feedback import feedback_status
   feedback=feedback_status(adapter.store).get('events',[])
   typed_activated=(adapter.authority_record() or {}).get('typed_semantic_events_activated_at')
  except (OSError,ValueError,KeyError,TypeError):
   feedback=[];typed_activated=None
 by_turn={str(x.get('turn_id')):x for x in feedback if x.get('turn_id')}
 for row in rows:
  if str(row['turn_id']) in by_turn:row['author_decision']=by_turn[str(row['turn_id'])]['decision']
 explicit_accept=[x for x in feedback if x.get('explicit') and x.get('decision')=='accept'];explicit_first=[x for x in explicit_accept if x.get('revision_round') in {None,0}]
 active=[x for x in rows if str(x.get('created_at') or '')>=str(typed_activated)] if typed_activated else []
 typed_coverage=round(sum(bool(x.get('semantic_delta_hash')) for x in active)/len(active),6) if active else None
 return {'schema':'minis.production-quality-telemetry.v2','canonical_turn_count':len(rows),'coverage_last_turn':rows[-1]['turn_id'] if rows else None,'explicit_feedback_count':len(feedback),'explicit_accept_count':len(explicit_accept),'explicit_author_pass_at_1':round(len(explicit_first)/len(explicit_accept),6) if explicit_accept else None,'workflow_commit_proxy':None,'typed_semantic_coverage_since_activation':typed_coverage,'typed_semantic_activation':typed_activated,'typed_semantic_event_count_since_activation':len(active),'rows':rows}
def evaluate_fixture_dir(path:str|Path,*,split:str|None=None)->dict[str,Any]:
 p=Path(path);records=[]
 for q in p.glob('*.json'):
  if q.name in {'manifest.json','baseline-report.json'}:continue
  value=json.loads(q.read_text());
  if value.get('schema') in {FIXTURE_SCHEMA,'minis.author-quality-fixture.v1'}:records.append(value)
 if split:records=[r for r in records if r.get('split')==split]
 explicit=[r for r in records if r.get('kind')=='explicit_author_feedback'];accepts=[r for r in explicit if r.get('author_decision')=='accept'];pairs=[r for r in records if r.get('kind') in {'observed_revision_pair','pairwise_revision'}];proxies=[r for r in records if r.get('kind') in {'workflow_commit_proxy','committed_pass_proxy'}]
 labels=[r for r in records if r.get('kind')=='curated_quality_label'];joint=[r for r in explicit if r.get('gate_pass') is not None]
 cm={'true_positive':0,'false_positive':0,'true_negative':0,'false_negative':0,'unlabeled':len(records)-len(joint)}
 for r in joint:
  g=bool(r['gate_pass']);a=r.get('author_decision')=='accept';cm['true_positive' if g and a else 'false_positive' if g else 'false_negative' if a else 'true_negative']+=1
 voice=[r for r in pairs if set(r.get('categories',[]))&{'character_voice','human_voice'}]
 rounds=[r.get('revision_rounds_to_accept') for r in accepts if isinstance(r.get('revision_rounds_to_accept'),int)]
 report={'schema':SCHEMA,'fixture_count':len(records),'split':split or 'all','evidence_counts':{'explicit_author_feedback':len(explicit),'curated_quality_labels':len(labels),'observed_revision_pairs':len(pairs),'workflow_proxies':len(proxies)},'metrics':{'explicit_author_pass_at_1':round(sum(bool(r.get('explicit_pass_at_1')) for r in accepts)/len(accepts),6) if accepts else None,'explicit_revision_rounds_mean':round(statistics.mean(rounds),4) if rounds else None,'observed_revision_pair_rate':round(len(pairs)/len({r.get('lineage_id',r.get('turn_id')) for r in records if r.get('lineage_id') or r.get('turn_id')}),6) if records else None,'workflow_commit_proxy_pass_at_1':round(sum(bool(r.get('proxy_pass_at_1',r.get('pass_at_1'))) for r in proxies)/len(proxies),6) if proxies else None,'author_edit_distance_mean':round(statistics.mean(r['diff']['normalized_edit_distance'] for r in pairs),6) if pairs else None,'pairwise_fixture_count':len(pairs),'character_voice_pairwise_fixture_count':len(voice),'gate_confusion_explicit_only':cm},'claims':{'quality_improved':False,'reason':'baseline only; improvement requires unseen hidden production evidence'},'limitations':['workflow proxies are reported separately and never enter explicit_author_pass_at_1','observed file revisions are lineage-deduplicated but are not automatically explicit reasons','Gate calibration uses only feedback with a joint Gate outcome'],'evaluated_at':now_iso()};report['report_hash']=sha256_json(report);return report
def refresh_quality_evaluation(adapter:Any)->dict[str,Any]:
 out=adapter.project_root/'benchmarks/author-quality-hidden';manifest=build_project_fixtures(adapter.project_root,out);all_report=evaluate_fixture_dir(out);hidden=evaluate_fixture_dir(out,split='hidden_test');report={**all_report,'manifest_hash':manifest['manifest_hash'],'hidden_test':hidden,'telemetry':production_quality_telemetry(adapter.project_root),'source_state_hash':(adapter.store.load_state() or {}).get('state_hash'),'source_event_head':(adapter.store.load_state() or {}).get('events_head')};report['report_hash']=sha256_json({k:v for k,v in report.items() if k!='report_hash'});adapter.store._atomic_json(out/'baseline-report.json',report);return report

from .pairwise_judge import DEFAULT_ADVERSARIAL_FIXTURES, evaluate_fixture_set

def evaluate_default_pairwise_harness()->dict:
    return evaluate_fixture_set(DEFAULT_ADVERSARIAL_FIXTURES)
