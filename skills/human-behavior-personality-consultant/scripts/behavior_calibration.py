#!/usr/bin/env python3
"""Immutable behavior prediction locks and post-scene calibration ledger."""
from __future__ import annotations
import argparse, hashlib, json, re
from datetime import datetime, timezone
from pathlib import Path

LOCK_SCHEMA = "minis.behavior-prediction-lock.v1"
RES_SCHEMA = "minis.behavior-prediction-resolution.v1"
LEVELS = {f"E{i}" for i in range(1, 7)}
STRENGTHS = {"strong", "medium", "weak"}
REPS = {"ordinal", "range", "precise_percent"}
CAUSES = {"prediction_hit", "model_miss", "author_override", "new_information", "mixed", "unresolved"}

def now(): return datetime.now(timezone.utc).isoformat()
def canon(v): return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def digest(v): return "sha256:" + hashlib.sha256(canon(v).encode()).hexdigest()
def paths(root):
    d = Path(root) / "behavior-calibration"
    return d, d / "predictions.jsonl", d / "resolutions.jsonl", d / "ledger.json"
def rows(path):
    if not path.exists(): return []
    out=[]
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            try: out.append(json.loads(line))
            except Exception as e: raise ValueError(f"invalid JSONL {path}:{n}: {e}")
    return out
def init(root):
    d,p,r,m=paths(root); d.mkdir(parents=True,exist_ok=True)
    p.touch(exist_ok=True); r.touch(exist_ok=True)
    if not m.exists():
        m.write_text(json.dumps({"schema":"minis.behavior-calibration-ledger.v1","created_at":now(),"append_only":True,"prediction_file":p.name,"resolution_file":r.name},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return d

def require_list(obj,key):
    v=obj.get(key)
    if not isinstance(v,list) or not v: raise ValueError(f"{key} must be a non-empty list")
    return v

def validate_lock(x):
    errs=[]
    for k in ("prediction_id","node_id","actor_id","source_state_hash","evidence_level","situation_strength","representation","candidates"):
        if x.get(k) in (None,"",[]): errs.append(f"missing {k}")
    if x.get("source_state_hash") and not re.fullmatch(r"sha256:[0-9a-f]{64}", str(x.get("source_state_hash"))): errs.append("source_state_hash must be sha256:<64 lowercase hex>")
    if x.get("evidence_level") not in LEVELS: errs.append("evidence_level must be E1..E6")
    if x.get("situation_strength") not in STRENGTHS: errs.append("invalid situation_strength")
    rep=x.get("representation")
    if rep not in REPS: errs.append("invalid representation")
    cs=x.get("candidates",[])
    if not isinstance(cs,list) or not 2 <= len(cs) <= 4: errs.append("candidates must contain 2..4 items")
    ids=[]
    for i,c in enumerate(cs):
        if not isinstance(c,dict): errs.append(f"candidate {i} must be object"); continue
        for k in ("id","description","observable_predictions","falsifiers"):
            if c.get(k) in (None,"",[]): errs.append(f"candidate {i} missing {k}")
        ids.append(c.get("id"))
        if rep=="ordinal" and not isinstance(c.get("rank"),int): errs.append(f"candidate {i} requires integer rank")
        if rep=="range":
            v=c.get("range")
            if not isinstance(v,list) or len(v)!=2 or not all(isinstance(n,(int,float)) for n in v) or not 0<=v[0]<=v[1]<=100: errs.append(f"candidate {i} invalid range")
        if rep=="precise_percent" and not isinstance(c.get("percent"),(int,float)): errs.append(f"candidate {i} requires percent")
    if len(ids)!=len(set(ids)): errs.append("candidate IDs must be unique")
    if rep=="ordinal" and cs:
        ranks=[c.get("rank") for c in cs if isinstance(c,dict)]
        if all(isinstance(n,int) for n in ranks) and sorted(ranks)!=list(range(1,len(cs)+1)): errs.append("ordinal ranks must be contiguous from 1")
    if rep=="precise_percent":
        samples=x.get("similar_context_samples",0); resolved=x.get("resolved_predictions",0); calibrated=x.get("calibration_record",False)
        if samples<5 or resolved<10 or calibrated is not True: errs.append("precise_percent requires >=5 similar samples, >=10 resolved predictions, and calibration_record=true")
        vals=[c.get("percent") for c in cs if isinstance(c,dict)]
        if len(vals)==len(cs) and all(isinstance(n,(int,float)) for n in vals) and abs(sum(vals)-100)>1e-9: errs.append("precise percentages must sum to 100")
    for k in ("protectors","inhibitors","counterfactual_tests","unknowns"):
        if not isinstance(x.get(k),list): errs.append(f"{k} must be a list")
    return errs

def validate_resolution(x,lock_ids):
    errs=[]
    for k in ("resolution_id","prediction_id","outcome","cause"):
        if x.get(k) in (None,""): errs.append(f"missing {k}")
    for k in ("observed_hits","observed_misses","model_updates"):
        if not isinstance(x.get(k),list): errs.append(f"{k} must be a list")
    if x.get("prediction_id") not in lock_ids: errs.append("prediction_id has no lock")
    if x.get("cause") not in CAUSES: errs.append("invalid cause")
    return errs

def append_unique(path,obj,key):
    old=rows(path)
    same=[x for x in old if x.get(key)==obj.get(key)]
    if same:
        if same[0].get("record_hash")==obj.get("record_hash"): return False
        raise ValueError(f"immutable ID conflict: {obj.get(key)}")
    with path.open("a",encoding="utf-8") as f: f.write(canon(obj)+"\n")
    return True

def load_input(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def add_lock(root,data):
    init(root); _,p,_,_=paths(root)
    x=dict(data); x["schema"]=LOCK_SCHEMA; x.setdefault("created_at",now()); x.setdefault("similar_context_samples",0); x.setdefault("resolved_predictions",0); x.setdefault("calibration_record",False)
    errs=validate_lock(x)
    if errs: raise ValueError("; ".join(errs))
    x["record_hash"]=digest({k:v for k,v in x.items() if k!="record_hash"})
    return x,append_unique(p,x,"prediction_id")
def add_resolution(root,data):
    init(root); _,p,r,_=paths(root); lock_ids={x.get("prediction_id") for x in rows(p)}
    x=dict(data); x["schema"]=RES_SCHEMA; x.setdefault("created_at",now())
    errs=validate_resolution(x,lock_ids)
    if errs: raise ValueError("; ".join(errs))
    x["record_hash"]=digest({k:v for k,v in x.items() if k!="record_hash"})
    return x,append_unique(r,x,"resolution_id")
def validate_all(root):
    init(root); _,p,r,_=paths(root); ls=rows(p); rs=rows(r); errs=[]; seen=set()
    for i,x in enumerate(ls,1):
        e=validate_lock(x)
        expected=digest({k:v for k,v in x.items() if k!="record_hash"})
        if x.get("record_hash")!=expected:e.append("record_hash mismatch")
        if x.get("prediction_id") in seen:e.append("duplicate prediction_id")
        seen.add(x.get("prediction_id")); errs += [f"lock line {i}: {z}" for z in e]
    rseen=set()
    for i,x in enumerate(rs,1):
        e=validate_resolution(x,seen)
        expected=digest({k:v for k,v in x.items() if k!="record_hash"})
        if x.get("record_hash")!=expected:e.append("record_hash mismatch")
        if x.get("resolution_id") in rseen:e.append("duplicate resolution_id")
        rseen.add(x.get("resolution_id")); errs += [f"resolution line {i}: {z}" for z in e]
    resolved={x.get("prediction_id") for x in rs if x.get("cause")!="unresolved"}
    return {"schema":"minis.behavior-calibration-validation.v1","status":"PASS" if not errs else "FAIL","locks":len(ls),"resolutions":len(rs),"resolved_predictions":len(resolved),"errors":errs}

def main():
    ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
    for name in ("init","validate","stats"):
        q=sub.add_parser(name); q.add_argument("--root",required=True)
    for name in ("lock","resolve"):
        q=sub.add_parser(name); q.add_argument("--root",required=True); q.add_argument("--input",required=True)
    a=ap.parse_args()
    try:
        if a.cmd=="init": out={"ok":True,"directory":str(init(a.root))}
        elif a.cmd=="lock":
            x,w=add_lock(a.root,load_input(a.input)); out={"ok":True,"written":w,"prediction_id":x["prediction_id"],"record_hash":x["record_hash"]}
        elif a.cmd=="resolve":
            x,w=add_resolution(a.root,load_input(a.input)); out={"ok":True,"written":w,"resolution_id":x["resolution_id"],"record_hash":x["record_hash"]}
        else: out=validate_all(a.root); out["ok"]=out["status"]=="PASS"
    except Exception as e:
        out={"ok":False,"status":"FAIL","error":str(e)}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if out.get("ok") else 1
if __name__=="__main__": raise SystemExit(main())
