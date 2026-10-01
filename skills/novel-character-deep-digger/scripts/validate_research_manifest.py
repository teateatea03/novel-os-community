#!/usr/bin/env python3
"""Validate minis.character-research-manifest.v1 research reproducibility."""
import argparse, json, sys
from pathlib import Path

SURFACES={"official","archive","news","scholarly","adjacent","web_archive","av","public_record","canon","library"}
STATUSES={"searched","not_applicable","blocked"}
RESULTS={"useful","zero","noise","blocked"}

def filled(v): return v is not None and v != "" and v != [] and v != {}
def err_if(e, cond, msg):
    if cond: e.append(msg)

def validate(d):
    e,w=[],[]
    if d.get("schema") != "minis.character-research-manifest.v1": e.append("invalid:schema")
    depth=d.get("research_depth")
    if depth not in {"R0","R1","R2"}: e.append("invalid:research_depth")
    questions=d.get("questions",[])
    if not questions: e.append("missing:questions")
    qids={q.get("id") for q in questions if isinstance(q,dict) and q.get("id")}
    identity=d.get("identity_resolution",{})
    if not isinstance(identity,dict) or not filled(identity.get("aliases")): e.append("missing:identity_resolution.aliases")
    if not isinstance(identity,dict) or not filled(identity.get("disambiguators")): e.append("missing:identity_resolution.disambiguators")
    source_map=d.get("source_map",[])
    valid_map=[]
    for i,s in enumerate(source_map):
        if not isinstance(s,dict): e.append(f"invalid:source_map[{i}]"); continue
        if s.get("surface") not in SURFACES: e.append(f"invalid:source_surface:{s.get('surface')}")
        if s.get("status") not in STATUSES: e.append(f"invalid:source_status:{s.get('status')}")
        if s.get("status") in {"not_applicable","blocked"} and not filled(s.get("reason")): e.append(f"missing:source_map_reason:{s.get('surface')}")
        valid_map.append(s)
    searched={s.get("surface") for s in valid_map if s.get("status")=="searched"}
    required_count={"R0":1,"R1":3,"R2":5}.get(depth,99)
    if len(searched)<required_count: e.append(f"gate:{depth}_requires_{required_count}_searched_surfaces")
    if depth=="R2":
        if not ({"official","canon","archive"}&searched): e.append("gate:R2_requires_primary_canon_or_archive_surface")
        if "adjacent" not in searched: e.append("gate:R2_requires_adjacent_cluster_surface")
    queries=d.get("queries",[])
    if not queries: e.append("missing:queries")
    seen_q=set()
    for i,q in enumerate(queries):
        if not isinstance(q,dict): e.append(f"invalid:queries[{i}]"); continue
        for k in ("id","question_id","platform","exact_query","searched_at","result"):
            if not filled(q.get(k)): e.append(f"missing:query.{k}:{i}")
        if q.get("question_id") not in qids: e.append(f"invalid:query.question_id:{q.get('question_id')}")
        if q.get("result") not in RESULTS: e.append(f"invalid:query.result:{q.get('result')}")
        sig=(q.get("platform"),q.get("exact_query"),q.get("searched_at"))
        if sig in seen_q: w.append(f"duplicate_query_log:{q.get('id')}")
        seen_q.add(sig)
    artifacts=d.get("artifacts",[])
    if depth in {"R1","R2"} and not artifacts: e.append(f"gate:{depth}_requires_artifacts")
    aids=set()
    for i,a in enumerate(artifacts):
        if not isinstance(a,dict): e.append(f"invalid:artifacts[{i}]"); continue
        aid=a.get("id")
        if not aid: e.append(f"missing:artifact.id:{i}")
        else: aids.add(aid)
        if not (filled(a.get("url")) or filled(a.get("local_path"))): e.append(f"missing:artifact.url_or_local_path:{aid or i}")
        for k in ("retrieved_at","locator","capture_status"):
            if not filled(a.get(k)): e.append(f"missing:artifact.{k}:{aid or i}")
        if filled(a.get("local_path")) and not filled(a.get("sha256")): e.append(f"missing:artifact.sha256:{aid or i}")
    claims=d.get("claims",[])
    if depth in {"R1","R2"} and not claims: e.append(f"gate:{depth}_requires_claims")
    families=set()
    for i,c in enumerate(claims):
        if not isinstance(c,dict): e.append(f"invalid:claims[{i}]"); continue
        if c.get("question_id") not in qids: e.append(f"invalid:claim.question_id:{c.get('id',i)}")
        if not filled(c.get("source_family_id")): e.append(f"missing:claim.source_family_id:{c.get('id',i)}")
        else: families.add(c.get("source_family_id"))
        for aid in c.get("artifact_ids",[]):
            if aid not in aids: e.append(f"invalid:claim.artifact_id:{aid}")
    if depth=="R2" and not d.get("negative_checks"): e.append("gate:R2_requires_negative_checks")
    saturation=d.get("saturation",{})
    if depth in {"R1","R2"}:
        if not isinstance(saturation,dict) or not filled(saturation.get("stop_reason")): e.append("missing:saturation.stop_reason")
        last=saturation.get("last_queries",[]) if isinstance(saturation,dict) else []
        if len(last)<3: e.append(f"gate:{depth}_requires_three_saturation_checks")
        if any(x not in {q.get('id') for q in queries if isinstance(q,dict)} for x in last): e.append("invalid:saturation.last_queries")
        if saturation.get("new_independent_families") not in {0,"0"}: w.append("saturation:not_yet_reached")
    if depth=="R0" and not artifacts: w.append("R0 has no captured artifact; keep conclusions provisional")
    return e,w

def main():
    p=argparse.ArgumentParser(); p.add_argument("manifest"); a=p.parse_args()
    d=json.loads(Path(a.manifest).read_text(encoding="utf-8")); e,w=validate(d)
    print(json.dumps({"valid":not e,"errors":e,"warnings":w},ensure_ascii=False,indent=2))
    return 1 if e else 0
if __name__=="__main__": sys.exit(main())
