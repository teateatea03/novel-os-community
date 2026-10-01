#!/usr/bin/env python3
"""Install a portable Novel OS bundle atomically into any writable skills directory."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
VERSION = "2.10.1"
CORE=["novel-operating-system","long-form-novel-writer","novel-character-deep-digger","human-behavior-personality-consultant","novel-worldbuilding-architect","novel-style-craft-director","novel-human-voice-editor","knowledge-relationship-graph","character-database-builder","immersive-interactive-fiction","unfinished-novel-completion","novel-world-database-builder", "special-object-database-builder", "novel-reality-state-engine", "novel-model-capability-compatibility", "novel-sensory-sound-prose", "public-web-research"]
NOTICE_DIR = "novel-operating-system/DISTRIBUTION_NOTICES"

def bundle_tools():
    # Load the sibling shipped with this installer, independent of the host's
    # module search path. Verification policy has a single implementation.
    spec=importlib.util.spec_from_file_location("novel_os_bundle_tools", HERE/"build_novel_os_bundle.py")
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def hash_file(p:Path):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def bundle_root(value:str|None):
    p=Path(value).expanduser().resolve() if value else ROOT
    return p/"payload" if (p/"payload").is_dir() else p

def verify(root:Path):
    m=root/"MANIFEST.json"
    if not m.exists(): raise SystemExit(f"MANIFEST.json not found under {root}")
    errors=bundle_tools().verify_root(root, compile_python=False)
    if errors: raise SystemExit("Bundle integrity check failed:\n"+"\n".join(errors))
    return json.loads(m.read_text(encoding="utf-8"))

def installed_notice_path(source_path: str) -> str:
    return source_path[len("skills/"):] if source_path.startswith("skills/") else f"{NOTICE_DIR}/{source_path}"

def stage_notices(root: Path, stage: Path, manifest: dict) -> list[dict]:
    destination=stage/NOTICE_DIR
    if destination.exists() or destination.is_symlink():
        raise RuntimeError(f"Reserved installed notice directory already exists: {NOTICE_DIR}")
    entries={entry["path"]:entry for entry in manifest["files"]}
    installed=[]
    for rel in manifest["distribution_notices"]:
        target_rel=installed_notice_path(rel)
        # A complete notice-only source layout also keeps relative links in
        # THIRD_PARTY.md working without changing the licensed source bytes.
        document_copy=f"{NOTICE_DIR}/{rel}"
        dest=stage/document_copy
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/rel, dest)
        installed.append({**entries[rel], "path":target_rel, "source_path":rel,
                          "document_copy_path":document_copy})
    return installed

def verify_installed_notices(target: Path) -> list[str]:
    """Check retained root and upstream notices against installation digests."""
    tools=bundle_tools()
    record="novel-operating-system/INSTALLATION.json"
    if not tools.regular_file(target, record): return ["missing or unsafe installation record"]
    try: info=json.loads((target/record).read_text(encoding="utf-8"))
    except (OSError, ValueError): return ["invalid installation record"]
    if not isinstance(info, dict): return ["invalid installation record"]
    entries=info.get("distribution_notices")
    if not isinstance(entries, list) or not entries: return ["missing installed notice inventory"]
    errors=[]; sources=set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("invalid installed notice entry"); continue
        rel=entry.get("source_path")
        if (not tools.safe_relative_path(rel)
                or (rel not in tools.ROOT_NOTICE_PATHS and not tools.is_skill_notice(rel))):
            errors.append("invalid installed notice source path"); continue
        if rel in sources: errors.append(f"duplicate installed notice: {rel}")
        sources.add(rel)
        expected=installed_notice_path(rel)
        if entry.get("path") != expected or not tools.regular_file(target, expected):
            errors.append(f"missing or unsafe installed notice: {rel}"); continue
        path=target/expected
        if hash_file(path)!=entry.get("sha256") or path.stat().st_size!=entry.get("bytes"):
            errors.append(f"modified installed notice: {rel}")
        document_copy=f"{NOTICE_DIR}/{rel}"
        if entry.get("document_copy_path") != document_copy or not tools.regular_file(target, document_copy):
            errors.append(f"missing or unsafe notice document copy: {rel}")
        else:
            copy=target/document_copy
            if hash_file(copy)!=entry.get("sha256") or copy.stat().st_size!=entry.get("bytes"):
                errors.append(f"modified notice document copy: {rel}")
    for rel in (*tools.REQUIRED_ROOT_NOTICES, *tools.REQUIRED_SKILL_NOTICES):
        if rel not in sources: errors.append(f"required installed notice not declared: {rel}")
    return errors

def smoke(target:Path):
    long=target/"long-form-novel-writer"; graph=target/"knowledge-relationship-graph"; worlddb=target/"novel-world-database-builder"; objectdb=target/"special-object-database-builder"; interactive=target/"immersive-interactive-fiction"; completion=target/"unfinished-novel-completion"; pwr=target/"public-web-research"
    with tempfile.TemporaryDirectory(prefix="novel-os-smoke-") as td:
        base=Path(td); novels=base/"novels"
        r=subprocess.run([sys.executable,str(long/"scripts"/"init_novel_project.py"),"--title","Smoke Test","--slug","smoke-test","--root",str(novels)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("initializer failed: "+(r.stderr or r.stdout))
        project=novels/"smoke-test"
        if not (project/"runtime"/"sessions"/"manuscript"/"branches"/"main"/"state"/"current.json").is_file(): raise RuntimeError("long-form shared event kernel was not initialized")
        for name in ("predictions.jsonl","resolutions.jsonl","ledger.json"):
            if not (project/"behavior-calibration"/name).is_file(): raise RuntimeError(f"behavior calibration runtime missing: {name}")
        behavior=target/"human-behavior-personality-consultant"; bgate=long/"scripts"/"behavior_gate.py"
        chapter=project/"chapters"/"001.md"; chapter.write_text("BEHAVIOR_LOCK_REQUIRED: smoke-P001\n"+"重大行為決策。"*80,encoding="utf-8")
        r=subprocess.run([sys.executable,str(bgate),"--root",str(project),"--chapter","001"],capture_output=True,text=True)
        if r.returncode==0: raise RuntimeError("behavior gate did not reject missing Prediction Lock")
        lock={"prediction_id":"smoke-P001","node_id":"001-S1","actor_id":"hero","source_state_hash":"sha256:"+"a"*64,"evidence_level":"E2","situation_strength":"medium","representation":"ordinal","candidates":[{"id":"A","description":"退後觀察","rank":1,"observable_predictions":["短答"],"falsifiers":["立即攻擊"]},{"id":"B","description":"直接質問","rank":2,"observable_predictions":["追問"],"falsifiers":["完全離場"]}],"protectors":["同伴"],"inhibitors":["監視器"],"counterfactual_tests":["移除監視器後 B 上升"],"unknowns":["是否錄音"]}
        lock_file=base/"behavior-lock.json"; lock_file.write_text(json.dumps(lock,ensure_ascii=False),encoding="utf-8")
        r=subprocess.run([sys.executable,str(behavior/"scripts"/"behavior_calibration.py"),"lock","--root",str(project),"--input",str(lock_file)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("behavior lock failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(bgate),"--root",str(project),"--chapter","001"],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("behavior gate rejected valid Lock: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"validate","--root",str(project)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("graph validation failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"init","--root",str(base/"world-db"),"--title","World DB Smoke"] ,capture_output=True,text=True)
        if r.returncode: raise RuntimeError("world database init failed: "+(r.stderr or r.stdout))
        batch=worlddb/"templates"/"world-extraction-batch.json"
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"import","--root",str(base/"world-db"),"--file",str(batch),"--strict"],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("world database import failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"validate","--root",str(base/"world-db")],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("world database validation failed: "+(r.stderr or r.stdout))
        object_db=base/"special-object-db"
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"init","--root",str(object_db),"--title","Special Object DB Smoke"],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("special object database init failed: "+(r.stderr or r.stdout))
        object_batch=objectdb/"fixtures"/"minimal-special-object-batch.json"
        r=subprocess.run([sys.executable,str(objectdb/"scripts"/"validate_special_object_classification.py"),"--batch",str(object_batch)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("special object classification failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"import","--root",str(object_db),"--file",str(object_batch),"--strict"],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("special object database import failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(graph/"scripts"/"relationship_graph.py"),"validate","--root",str(object_db)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("special object graph validation failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(objectdb/"scripts"/"validate_special_object_classification.py"),"--batch",str(object_batch),"--graph",str(object_db/"graphify-out"/"graph.json")],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("special object graph classification failed: "+(r.stderr or r.stdout))
        fixture=interactive/"fixtures"/"minimal-state.json"
        r=subprocess.run([sys.executable,str(interactive/"scripts"/"interactive_state.py"),"validate","--state",str(fixture)],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("interactive fixture failed: "+(r.stderr or r.stdout))
        clean_env={k:v for k,v in os.environ.items() if k not in {"PYTHONPATH","PYTHONHOME"}}
        clean_env["PYTHONPATH"]=str(interactive/"scripts")
        r=subprocess.run([sys.executable,"-m","unittest","discover","-s","novel_judge","-t",".","-p","test_*.py"],cwd=str(interactive/"scripts"),env=clean_env,capture_output=True,text=True)
        if r.returncode: raise RuntimeError("narrative judge acceptance failed: "+(r.stderr or r.stdout))
        authority=json.loads((project/"runtime"/"sessions"/"manuscript"/"branches"/"main"/"production-authority.json").read_text(encoding="utf-8"))
        if authority.get("status")!="active" or not authority.get("born_under_single_authority") or not authority.get("typed_semantic_events_activated_at"):
            raise RuntimeError("new long-form project lacks active v2.7 production authority")
        # Cross-process writer test: one commit succeeds, one stale writer is rejected.
        race_script=base/"race.py"
        race_script.write_text('''import json,subprocess,sys,tempfile\nfrom novel_judge import FileStore,empty_state,replay_events\nW="""import json,sys\\nfrom novel_judge import FileStore,make_intent,commit_turn\\ns=FileStore(sys.argv[1],'race','s')\\ntry: r=commit_turn(s,make_intent('player','observe',turn_id=sys.argv[3]),expected_state_hash=sys.argv[2]); print(json.dumps(['ok',r['post_state_hash']]))\\nexcept Exception as e: print(json.dumps([type(e).__name__,str(e)]))\\n"""\nwith tempfile.TemporaryDirectory() as root:\n s=FileStore(root,'race','s'); initial=empty_state('race','s'); initial['actors']={'player':{'kind':'player','location':'room','status':{},'commitments':[]}}; s.save_state(initial); h=s.load_state()['state_hash']; ps=[subprocess.Popen([sys.executable,'-c',W,root,h,'t'+str(n)],stdout=subprocess.PIPE,text=True) for n in (1,2)]; results=[json.loads(p.communicate()[0]) for p in ps]; current=s.load_state(); replayed=replay_events(initial,s.read_events()); assert sum(x[0]=='ok' for x in results)==1 and len(s.read_events())==1 and current['state_hash']==replayed['state_hash']; print(json.dumps({'ok':True,'results':results}))\n''',encoding="utf-8")
        r=subprocess.run([sys.executable,str(race_script)],env={**os.environ,"PYTHONPATH":str(interactive/"scripts")},capture_output=True,text=True)
        if r.returncode: raise RuntimeError("narrative judge race test failed: "+(r.stderr or r.stdout))
        r=subprocess.run([sys.executable,str(long/"scripts"/"run_regression.py")],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("long-form regression failed: "+(r.stderr or r.stdout))
        long_regression=json.loads(r.stdout)
        r=subprocess.run([sys.executable,str(completion/"scripts"/"run_regression.py")],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("unfinished-completion regression failed: "+(r.stderr or r.stdout))
        completion_regression=json.loads(r.stdout)
        r=subprocess.run([sys.executable,str(pwr/"scripts"/"test_public_web_research.py")],capture_output=True,text=True)
        if r.returncode: raise RuntimeError("public-web-research regression failed: "+(r.stderr or r.stdout))
        return {"initializer":True,"shared_event_kernel":True,"behavior_calibration":True,"behavior_gate":True,"longform_active_authority":True,"typed_semantic_events":True,"graph":True,"world_database":True,"special_object_database":True,"interactive":True,"interactive_race":True,"public_web_research":True,"regression":long_regression,"completion_regression":completion_regression}

def install(args):
    if sys.version_info < (3, 10): raise SystemExit(f"Novel OS automated installer requires Python 3.10+; found {sys.version.split()[0]}. Use document/manual mode or upgrade Python.")
    root=bundle_root(args.bundle_root); manifest=verify(root)
    source=root/"skills"; target=Path(args.target).expanduser().resolve(); target.mkdir(parents=True,exist_ok=True)
    missing=[n for n in CORE if not (source/n/"SKILL.md").is_file()]
    if missing: raise SystemExit("Missing source skills: "+", ".join(missing))
    exists=[n for n in CORE if (target/n).exists() or (target/n).is_symlink()]
    if exists and not args.upgrade: raise SystemExit("Refusing to overwrite existing skills: "+", ".join(exists)+". Re-run with --upgrade.")
    if exists and (target/"backups").is_symlink():
        raise SystemExit("Refusing to write skill backups through a symlink")
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stage=Path(tempfile.mkdtemp(prefix=".novel-os-stage-",dir=target))
    backup=target/"backups"/f"novel-os-{stamp}-{stage.name.rsplit('-',1)[-1]}"
    moved=[]; installed=[]
    try:
        # Copy exactly verified files, not unlisted caches, environment files,
        # or links a host may have inserted in the unpacked bundle.
        for entry in manifest["files"]:
            rel=entry["path"]
            if rel.startswith("skills/"):
                dest=stage/rel[len("skills/"):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root/rel,dest)
        notices=stage_notices(root,stage,manifest)
        info={"schema":"novel-os-installation.v1","bundle_version":manifest.get("version"),"installed_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),"python_version":sys.version.split()[0],"runtime_requirements":manifest.get("runtime_requirements",{}),"bundle_manifest_sha256":hash_file(root/"MANIFEST.json"),"skills":CORE,"backup":str(backup) if exists else None,"smoke_test":bool(args.smoke_test),"distribution_notices":notices}
        (stage/"novel-operating-system"/"INSTALLATION.json").write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        errors=verify_installed_notices(stage)
        if errors: raise RuntimeError("Staged notice integrity check failed:\n"+"\n".join(errors))
        if args.smoke_test: smoke(stage)
        if exists:
            backup.mkdir(parents=True)
            for n in exists:
                shutil.move(str(target/n),str(backup/n)); moved.append(n)
        for n in CORE:
            os.replace(stage/n,target/n); installed.append(n)
        errors=verify_installed_notices(target)
        if errors: raise RuntimeError("Installed notice integrity check failed:\n"+"\n".join(errors))
        print(json.dumps({"ok":True,"target":str(target),"skills":CORE,"backup":info["backup"],"smoke_test":info["smoke_test"],"requirements":info["runtime_requirements"],"distribution_notices":NOTICE_DIR,"note":"For non-Minis hosts, replace independent_review.py's minis-model-use adapter or keep independent review disabled."},ensure_ascii=False,indent=2))
    except Exception:
        for n in installed:
            if (target/n).is_symlink(): (target/n).unlink()
            elif (target/n).exists(): shutil.rmtree(target/n)
        for n in moved:
            shutil.move(str(backup/n),str(target/n))
        raise
    finally:
        shutil.rmtree(stage,ignore_errors=True)

def main():
    p=argparse.ArgumentParser(); p.add_argument("--target",required=True); p.add_argument("--bundle-root"); p.add_argument("--upgrade",action="store_true"); p.add_argument("--smoke-test",action="store_true")
    p.add_argument("--verify-installed-notices",action="store_true",help="only check installed notice hashes; do not install")
    args=p.parse_args()
    if args.verify_installed_notices:
        errors=verify_installed_notices(Path(args.target).expanduser().resolve())
        print(json.dumps({"ok":not errors,"errors":errors},ensure_ascii=False,indent=2))
        raise SystemExit(1 if errors else 0)
    install(args)
if __name__=="__main__":main()
