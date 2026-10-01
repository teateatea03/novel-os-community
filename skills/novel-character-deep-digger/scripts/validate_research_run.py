#!/usr/bin/env python3
"""Validate minis.character-research-run.v2 as an auditable evidence run."""
import argparse, hashlib, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ZERO="0"*64
EVENT_TYPES={"QUERY","BROWSE","CITATION_BACKWARD","CITATION_FORWARD","PIVOT","CONTACT","ARCHIVE_REQUEST","CAPTURE","TRANSFORM","REVIEW"}
VALID_RESULTS={"success","zero","noise","blocked","error"}
DISPOSITIONS={"include","exclude","defer"}
CLAIM_STATUSES={"SUPPORTED","CONTESTED","AMBIGUOUS","UNAVAILABLE","REFUTED"}
CHECKPOINTS={"START_CHALLENGE","MIDPOINT_REVIEW","CLAIM_AUDIT"}
ROUTE_TYPES={"QUERY","BROWSE","CITATION_BACKWARD","CITATION_FORWARD","PIVOT","CONTACT","ARCHIVE_REQUEST"}

def load_json(path): return json.loads(path.read_text(encoding="utf-8"))
def load_jsonl(path):
    out=[]
    if not path.exists(): return out
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if line.strip():
            try: out.append(json.loads(line))
            except Exception as x: raise ValueError(f"{path.name}:{n}:{x}")
    return out

def canonical_event_hash(ev):
    x=dict(ev); x.pop("event_hash",None)
    raw=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def norm_query(s):
    stop={"專業","著名","知名","完整","資料","人物","角色","the","a","an"}
    toks=re.findall(r"[\w\u3400-\u9fff]+",(s or "").lower())
    return tuple(sorted({x for x in toks if x not in stop}))

def validate(root):
    e,w=[],[]; root=Path(root)
    needed=["protocol.json","events.jsonl","candidates.jsonl","artifacts.jsonl","claims.jsonl","reviews.jsonl"]
    for n in needed:
        if not (root/n).exists(): e.append(f"missing:{n}")
    if e: return e,w,{}
    try:
        p=load_json(root/"protocol.json"); events=load_jsonl(root/"events.jsonl"); candidates=load_jsonl(root/"candidates.jsonl")
        artifacts=load_jsonl(root/"artifacts.jsonl"); claims=load_jsonl(root/"claims.jsonl"); reviews=load_jsonl(root/"reviews.jsonl")
    except Exception as x: return [f"parse:{x}"],w,{}
    protocol_bytes=(root/"protocol.json").read_bytes()
    protocol_hash=hashlib.sha256(protocol_bytes).hexdigest()
    if p.get("schema")!="minis.character-research-run.v2": e.append("invalid:schema")
    depth=p.get("depth");
    if depth not in {"R0","R1","R2"}: e.append("invalid:depth")
    qs={q.get("id"):q for q in p.get("questions",[]) if isinstance(q,dict) and q.get("id")}
    p0={k for k,q in qs.items() if q.get("priority")=="P0"}
    if not qs: e.append("missing:questions")
    ident=p.get("identity_resolution",{})
    for k in ("aliases","disambiguators"):
        if not ident.get(k): e.append(f"missing:identity_resolution.{k}")
    plans={x.get("id"):x for x in p.get("source_plan",[]) if x.get("id")}
    must={k for k,x in plans.items() if x.get("priority")=="must"}
    if depth in {"R1","R2"} and not must: e.append("missing:must_source_plan")
    prev=ZERO; ids=set(); valid_plan_events=set(); distinct_routes=set(); yields=[]
    for i,ev in enumerate(events):
        eid=ev.get("event_id")
        if not eid or eid in ids: e.append(f"invalid:event_id:{eid or i}")
        ids.add(eid)
        if ev.get("type") not in EVENT_TYPES: e.append(f"invalid:event_type:{eid}")
        if ev.get("protocol_hash")!=protocol_hash: e.append(f"broken:event_protocol_binding:{eid}")
        if ev.get("prev_hash")!=prev: e.append(f"broken:event_chain:{eid}")
        calc=canonical_event_hash(ev)
        if ev.get("event_hash")!=calc: e.append(f"broken:event_hash:{eid}")
        prev=ev.get("event_hash","")
        if not set(ev.get("question_ids",[])) <= set(qs): e.append(f"invalid:event_questions:{eid}")
        status=ev.get("result",{}).get("status")
        if status not in VALID_RESULTS: e.append(f"invalid:event_result:{eid}")
        pid=ev.get("plan_id")
        if pid and pid not in plans: e.append(f"invalid:event_plan:{eid}")
        if pid and ev.get("type") in ROUTE_TYPES and status in {"success","zero","noise"}: valid_plan_events.add(pid)
        if ev.get("type") in ROUTE_TYPES and status in {"success","zero","noise"}:
            surface=plans.get(pid,{}).get("surface","unknown")
            method=plans.get(pid,{}).get("method",ev.get("type"))
            platform=ev.get("platform","unknown")
            qnorm=norm_query(ev.get("input",{}).get("exact_query",""))
            distinct_routes.add((surface,method,platform,qnorm))
            yields.append((eid,ev.get("result",{}).get("new_source_family_ids",[])))
        if ev.get("type")=="QUERY":
            inp=ev.get("input",{})
            if not inp.get("exact_query") or not ev.get("platform"): e.append(f"missing:query_reproduction:{eid}")
            if status=="success" and "raw_hit_count" not in ev.get("result",{}): w.append(f"missing:raw_hit_count:{eid}")
    for pid in sorted(must-valid_plan_events): e.append(f"gate:must_route_not_executed:{pid}")
    cids=set(); included=set(); deferred=[]
    for c in candidates:
        cid=c.get("candidate_id")
        if not cid or cid in cids: e.append(f"invalid:candidate_id:{cid}")
        cids.add(cid)
        if c.get("discovered_by") not in ids: e.append(f"invalid:candidate_discovery:{cid}")
        if c.get("disposition") not in DISPOSITIONS: e.append(f"invalid:candidate_disposition:{cid}")
        if not c.get("reason_code"): e.append(f"missing:candidate_reason:{cid}")
        if c.get("disposition")=="include": included.add(cid)
        if c.get("disposition")=="defer" and c.get("priority") in {"P0","high"}: deferred.append(cid)
    aids=set(); family_by_art={}; derived=[]
    for a in artifacts:
        aid=a.get("artifact_id")
        if not aid or aid in aids: e.append(f"invalid:artifact_id:{aid}")
        aids.add(aid)
        if a.get("candidate_id") not in included: e.append(f"invalid:artifact_candidate:{aid}")
        if not a.get("sha256") or not re.fullmatch(r"[0-9a-f]{64}",a.get("sha256","")): e.append(f"missing:artifact_hash:{aid}")
        if not a.get("locator"): e.append(f"missing:artifact_locator:{aid}")
        if a.get("raw_or_derived")=="derived":
            derived.append(aid)
            for k in ("derived_from","input_hash","operation","tool","output_hash"):
                if not a.get(k): e.append(f"missing:derived_{k}:{aid}")
        family_by_art[aid]=a.get("source_family_id")
    claim_q=set(); independent_ok={}
    for c in claims:
        cid=c.get("claim_id"); qid=c.get("question_id")
        if qid not in qs: e.append(f"invalid:claim_question:{cid}")
        else: claim_q.add(qid)
        if c.get("status") not in CLAIM_STATUSES: e.append(f"invalid:claim_status:{cid}")
        evs=c.get("evidence",[])
        if c.get("status") in {"SUPPORTED","CONTESTED","REFUTED"} and not evs: e.append(f"missing:claim_evidence:{cid}")
        fams=[]
        for x in evs+c.get("counterevidence",[]):
            aid=x.get("artifact_id")
            if aid not in aids: e.append(f"invalid:claim_artifact:{cid}:{aid}")
            fam=x.get("source_family_id") or family_by_art.get(aid)
            if fam: fams.append(fam)
            if not x.get("locator"): e.append(f"missing:claim_locator:{cid}:{aid}")
            if x.get("mode")=="negative" and not x.get("expectation_basis"): e.append(f"invalid:negative_evidence:{cid}:{aid}")
        independent_ok[cid]=len(set(fams))>=2
        if c.get("requires_independent_review") and not independent_ok[cid]: e.append(f"gate:independent_sources_missing:{cid}")
        if not c.get("sensitivity"): w.append(f"missing:claim_sensitivity:{cid}")
    for qid in sorted(p0-claim_q): e.append(f"gate:P0_without_claim:{qid}")
    review_types=Counter(r.get("checkpoint") for r in reviews)
    required={"R0":set(),"R1":{"START_CHALLENGE","CLAIM_AUDIT"},"R2":CHECKPOINTS}.get(depth,set())
    for x in sorted(required-set(review_types)): e.append(f"gate:missing_checkpoint:{x}")
    audited=set()
    for r in reviews:
        if r.get("checkpoint") not in CHECKPOINTS: e.append(f"invalid:checkpoint:{r.get('review_id')}")
        if not r.get("reviewer") or not r.get("performed_at"): e.append(f"missing:review_metadata:{r.get('review_id')}")
        audited.update(r.get("claim_ids",[]) if r.get("checkpoint")=="CLAIM_AUDIT" else [])
    p0_claims={c.get("claim_id") for c in claims if c.get("question_id") in p0}
    for cid in sorted(p0_claims-audited): e.append(f"gate:P0_claim_not_audited:{cid}")
    bench=p.get("benchmark_items",[]); hold=[b for b in bench if b.get("holdout")]
    found={x for ev in events for x in ev.get("result",{}).get("benchmark_ids_found",[])}
    if depth=="R2" and not hold and not any(r.get("search_strategy_review") for r in reviews): e.append("gate:R2_requires_holdout_or_search_review")
    for b in hold:
        if b.get("id") not in found: w.append(f"benchmark_missed:{b.get('id')}")
    stop=p.get("stop_policy",{}); minroutes=stop.get("min_distinct_routes",1)
    if depth in {"R1","R2"} and len(distinct_routes)<minroutes: e.append(f"gate:insufficient_distinct_routes:{len(distinct_routes)}<{minroutes}")
    window=stop.get("no_new_family_window",3)
    if depth in {"R1","R2"}:
        if len(yields)<window: e.append("gate:insufficient_saturation_window")
        elif any(fs for _,fs in yields[-window:]): e.append("gate:not_saturated_new_family_in_window")
    if deferred: e.append("gate:high_value_candidates_deferred:"+",".join(deferred))
    metrics={"depth":depth,"events":len(events),"distinct_routes":len(distinct_routes),"must_routes":len(must),"must_routes_executed":len(must&valid_plan_events),"candidates":len(candidates),"included":len(included),"artifacts":len(artifacts),"claims":len(claims),"p0_questions":len(p0),"p0_claims":len(p0_claims),"checkpoints":dict(review_types),"benchmark_total":len(bench),"benchmark_found":len({b.get('id') for b in bench}&found),"deferred_high":len(deferred)}
    return e,w,metrics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--summary"); a=ap.parse_args()
    e,w,m=validate(a.run_dir); out={"valid":not e,"errors":e,"warnings":w,"metrics":m}
    txt=json.dumps(out,ensure_ascii=False,indent=2); print(txt)
    if a.summary: Path(a.summary).write_text(txt+"\n",encoding="utf-8")
    return 1 if e else 0
if __name__=="__main__": sys.exit(main())
