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

def _unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("duplicate JSON key")
        obj[key] = value
    return obj


def _invalid_constant(value):
    raise ValueError("non-finite JSON number")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                      parse_constant=_invalid_constant)


def load_jsonl(path):
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line, object_pairs_hook=_unique_object,
                                      parse_constant=_invalid_constant))
            except ValueError:
                raise ValueError(f"{path.name}:{n}:invalid JSON") from None
    return out


def _shape_errors(protocol, tables):
    """Check consumed field types before indexing; do not impose a new schema."""
    errors = []

    def check(obj, key, typ, label, nullable=False):
        if key not in obj or (nullable and obj[key] is None):
            return
        value = obj[key]
        if not isinstance(value, typ) or (typ is int and isinstance(value, bool)):
            errors.append(f"invalid:type:{label}.{key}")

    def strings(obj, key, label):
        check(obj, key, list, label)
        if isinstance(obj.get(key), list):
            if any(not isinstance(x, str) or not x.strip() for x in obj[key]):
                errors.append(f"invalid:string_list:{label}.{key}")

    def objects(obj, key, label):
        check(obj, key, list, label)
        rows = obj.get(key, [])
        if not isinstance(rows, list):
            return []
        if any(not isinstance(x, dict) for x in rows):
            errors.append(f"invalid:object_list:{label}.{key}")
        return [x for x in rows if isinstance(x, dict)]

    if not isinstance(protocol, dict):
        return ["invalid:type:protocol"]
    for key in ("schema", "depth"):
        check(protocol, key, str, "protocol")
    for key in ("identity_resolution", "stop_policy"):
        check(protocol, key, dict, "protocol")
    for key in ("questions", "source_plan", "benchmark_items"):
        for row in objects(protocol, key, "protocol"):
            for field in ("id", "priority", "surface", "method"):
                check(row, field, str, key, nullable=True)
            strings(row, "question_ids", key)
    stop = protocol.get("stop_policy", {})
    if isinstance(stop, dict):
        for key in ("min_distinct_routes", "no_new_family_window"):
            check(stop, key, int, "stop_policy")
            if type(stop.get(key)) is int and stop[key] < 1:
                errors.append(f"invalid:stop_policy.{key}")
    scalar_fields = {
        "events": ("event_id", "type", "plan_id", "platform", "protocol_hash", "prev_hash", "event_hash"),
        "candidates": ("candidate_id", "discovered_by", "disposition", "priority"),
        "artifacts": ("artifact_id", "candidate_id", "sha256", "raw_or_derived", "source_family_id", "local_path", "path", "input_hash", "output_hash", "content_sha256"),
        "claims": ("claim_id", "question_id", "status"),
        "reviews": ("review_id", "checkpoint"),
    }
    for name, rows in tables.items():
        for i, row in enumerate(rows):
            label = f"{name}[{i}]"
            if not isinstance(row, dict):
                errors.append(f"invalid:type:{label}")
                continue
            for key in scalar_fields[name]:
                check(row, key, str, label, nullable=True)
            if name == "events":
                strings(row, "question_ids", label)
                for key in ("input", "result"):
                    check(row, key, dict, label)
                if isinstance(row.get("input"), dict):
                    check(row["input"], "exact_query", str, label + ".input", nullable=True)
                if isinstance(row.get("result"), dict):
                    check(row["result"], "status", str, label + ".result", nullable=True)
                    for key in ("new_candidate_ids", "new_source_family_ids", "benchmark_ids_found"):
                        strings(row["result"], key, label + ".result")
            elif name == "artifacts":
                check(row, "size", int, label, nullable=True)
                if "derived_from" in row and row["derived_from"] is not None:
                    if isinstance(row["derived_from"], list):
                        strings(row, "derived_from", label)
                    else:
                        check(row, "derived_from", str, label)
            elif name == "claims":
                for key in ("evidence", "counterevidence"):
                    for ref in objects(row, key, label):
                        for field in ("artifact_id", "source_family_id", "mode"):
                            check(ref, field, str, label + "." + key, nullable=True)
            elif name == "reviews":
                strings(row, "claim_ids", label)
    return errors


def _check_ids(rows, field, label, errors):
    seen = set()
    for i, row in enumerate(rows):
        value = row.get(field)
        if not isinstance(value, str) or not value.strip() or value in seen:
            errors.append(f"invalid:{label}_id:{value or i}")
        seen.add(value)


def _safe_file(root, value):
    """Absolute in-run paths remain valid; traversal and symlink escape do not."""
    path = Path(value)
    path = (path if path.is_absolute() else root / path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("outside run")
    if not path.is_file():
        raise OSError("not a regular file")
    return path


def _file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _artifact_integrity(root, artifacts, errors, warnings):
    by_id = {a.get("artifact_id"): a for a in artifacts}
    graph = {}
    for artifact in artifacts:
        aid = artifact.get("artifact_id")
        paths = [artifact[k] for k in ("local_path", "path") if artifact.get(k)]
        if not paths:
            warnings.append(f"unverified:artifact_file:{aid}")
        for value in paths:
            try:
                path = _safe_file(root, value)
                if _file_hash(path) != artifact.get("sha256"):
                    errors.append(f"broken:artifact_file_hash:{aid}")
                if artifact.get("size") is not None and path.stat().st_size != artifact["size"]:
                    errors.append(f"broken:artifact_file_size:{aid}")
            except (ValueError, RuntimeError):
                errors.append(f"invalid:artifact_path_escape:{aid}")
            except OSError:
                errors.append(f"missing:artifact_file:{aid}")
        if artifact.get("content_sha256") and artifact["content_sha256"] != artifact.get("sha256"):
            errors.append(f"broken:artifact_content_hash:{aid}")
        if artifact.get("raw_or_derived") != "derived":
            continue
        for field in ("input_hash", "output_hash"):
            if artifact.get(field) and not re.fullmatch(r"[0-9a-f]{64}", artifact[field]):
                errors.append(f"invalid:derived_{field}:{aid}")
        if artifact.get("output_hash") and artifact["output_hash"] != artifact.get("sha256"):
            errors.append(f"broken:derived_output_hash:{aid}")
        parents = artifact.get("derived_from") or []
        parents = [parents] if isinstance(parents, str) else parents
        graph[aid] = [parent for parent in parents if parent in by_id]
        for parent in parents:
            if parent not in by_id:
                # v2 has existing URL/path/descriptive lineage; do not recast it as IDs.
                warnings.append(f"unverified:derived_parent:{aid}")
            elif len(parents) == 1 and artifact.get("input_hash") != by_id[parent].get("sha256"):
                errors.append(f"broken:derived_input_hash:{aid}")
        if len(parents) > 1:
            warnings.append(f"unverified:derived_multi_input_hash:{aid}")
    # Iterative DFS avoids recursion limits for long, otherwise legal lineage chains.
    done, active = set(), set()
    for aid in graph:
        stack = [(aid, False)]
        while stack:
            node, exiting = stack.pop()
            if exiting:
                active.discard(node)
                done.add(node)
            elif node in active:
                errors.append(f"broken:derived_cycle:{node}")
            elif node not in done:
                active.add(node)
                stack.append((node, True))
                stack.extend((parent, False) for parent in graph.get(node, []))

def canonical_event_hash(ev):
    x=dict(ev); x.pop("event_hash",None)
    raw=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def norm_query(s):
    stop={"專業","著名","知名","完整","資料","人物","角色","the","a","an"}
    toks=re.findall(r"[\w\u3400-\u9fff]+",(s or "").lower())
    return tuple(sorted({x for x in toks if x not in stop}))

def _saturation_observations(events, candidates, artifacts, warnings):
    """Observable lower bound, NOT proof of independent families or web exhaustion.

    An artifact's registered family is attributed to its candidate's discovery
    event, not to the later capture/recognition time (which v2 cannot reconstruct).
    Compute first appearances from artifacts alone: an earlier event declaration
    must not erase an observable first appearance. Claim-local family labels and
    candidate hints cannot safely be promoted to an artifact-wide genealogy,
    even when repeated across claims. Missing labels remain compatible but visible.
    """
    event_index = {ev['event_id']: i for i, ev in enumerate(events)}
    candidate_by_id = {c['candidate_id']: c for c in candidates}
    first = {}
    unknown, unlocated = [], []
    for artifact in artifacts:
        aid = artifact['artifact_id']
        family = artifact.get('source_family_id')
        if not family or not family.strip() or family.strip().upper() == 'UNKNOWN':
            unknown.append(aid)
            warnings.append(f"unverified:saturation_artifact_family:{aid}")
            continue
        eid = candidate_by_id.get(artifact.get('candidate_id'), {}).get('discovered_by')
        if eid not in event_index:
            unlocated.append(aid)
            warnings.append(f"unverified:saturation_family_discovery:{aid}")
            continue
        index = event_index[eid]
        first[family] = min(first.get(family, index), index)
    observed = defaultdict(set)
    for family, index in first.items():
        observed[events[index]['event_id']].add(family)
    curve = []
    for ev in events:
        eid = ev['event_id']
        declared = set(ev.get('result', {}).get('new_source_family_ids', []))
        recovered = observed[eid]
        omitted = recovered - declared
        if omitted:
            warnings.append(f"unreported:saturation_family_yield:{eid}:" + ','.join(sorted(omitted)))
        curve.append({'event_id': eid, 'declared': sorted(declared),
                      'observed_first': sorted(recovered),
                      'effective': sorted(declared | recovered),
                      'undeclared_observed': sorted(omitted)})
    return curve, {'saturation_family_basis': 'registered_artifact_candidate_discovery_lower_bound',
                   'saturation_independence_verified': False,
                   'saturation_capture_timing_verified': False,
                   'saturation_observed_families': len(first),
                   'saturation_unknown_family_artifacts': unknown,
                   'saturation_unlocated_family_artifacts': unlocated,
                   'saturation_undeclared_family_occurrences': sum(len(x['undeclared_observed']) for x in curve)}


def validate(root):
    e,w=[],[]; root=Path(root).resolve()
    needed=["protocol.json","events.jsonl","candidates.jsonl","artifacts.jsonl","claims.jsonl","reviews.jsonl"]
    for n in needed:
        try:
            _safe_file(root, n)
        except (ValueError, RuntimeError):
            e.append(f"invalid:ledger_path_escape:{n}")
        except OSError:
            e.append(f"missing:{n}")
    if e: return e,w,{}
    try:
        p=load_json(root/"protocol.json"); events=load_jsonl(root/"events.jsonl"); candidates=load_jsonl(root/"candidates.jsonl")
        artifacts=load_jsonl(root/"artifacts.jsonl"); claims=load_jsonl(root/"claims.jsonl"); reviews=load_jsonl(root/"reviews.jsonl")
        protocol_bytes=(root/"protocol.json").read_bytes()
    except (ValueError, OSError, RecursionError):
        return ["parse:invalid_or_unreadable_run"],w,{}
    tables = dict(events=events, candidates=candidates, artifacts=artifacts, claims=claims, reviews=reviews)
    e.extend(_shape_errors(p, tables))
    if e: return e,w,{}
    for name, field in (("questions", "id"), ("source_plan", "id"), ("benchmark_items", "id")):
        _check_ids(p.get(name, []), field, name, e)
    for name, field in (("events", "event_id"), ("candidates", "candidate_id"), ("artifacts", "artifact_id"), ("claims", "claim_id"), ("reviews", "review_id")):
        _check_ids(tables[name], field, name.rstrip("s"), e)
    if e: return e,w,{}
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
    for row in p.get("source_plan", []) + p.get("benchmark_items", []):
        if not set(row.get("question_ids", [])) <= set(qs):
            e.append(f"invalid:protocol_question_reference:{row['id']}")
    prev=ZERO; ids=set(); valid_plan_events=set(); distinct_routes=set(); yields=[]
    attempts = set()
    candidate_by_id = {c['candidate_id']: c for c in candidates}
    benchmark_ids = {b['id'] for b in p.get('benchmark_items', [])}
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
        if ev.get('type') in ROUTE_TYPES and status in VALID_RESULTS:
            attempts.update(ev.get('question_ids', []))
        for candidate_id in ev.get('result', {}).get('new_candidate_ids', []):
            candidate = candidate_by_id.get(candidate_id)
            if candidate is None:
                e.append(f"invalid:event_candidate:{eid}:{candidate_id}")
            elif candidate.get('discovered_by') != eid:
                if candidate.get('discovered_by') in ids:
                    # Existing runs re-list a known candidate on browse/capture.
                    w.append(f"repeated:event_candidate:{eid}:{candidate_id}")
                else:
                    e.append(f"broken:event_candidate_discovery:{eid}:{candidate_id}")
        if not set(ev.get('result', {}).get('benchmark_ids_found', [])) <= benchmark_ids:
            e.append(f"invalid:event_benchmark:{eid}")
        pid=ev.get("plan_id")
        if pid and pid not in plans: e.append(f"invalid:event_plan:{eid}")
        if pid and ev.get("type") in ROUTE_TYPES and status in {"success","zero","noise"}: valid_plan_events.add(pid)
        if ev.get("type") in ROUTE_TYPES and status in {"success","zero","noise"}:
            surface=plans.get(pid,{}).get("surface","unknown")
            method=plans.get(pid,{}).get("method",ev.get("type"))
            platform=ev.get("platform","unknown")
            qnorm=norm_query(ev.get("input",{}).get("exact_query",""))
            signature = (surface,method,platform,qnorm)
            distinct_routes.add(signature)
            yields.append((eid, signature))
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
    _artifact_integrity(root, artifacts, e, w)
    claim_q=set(); independent_ok={}; evidence_families={}
    for c in claims:
        cid=c.get("claim_id"); qid=c.get("question_id")
        if qid not in qs: e.append(f"invalid:claim_question:{cid}")
        else: claim_q.add(qid)
        if c.get("status") not in CLAIM_STATUSES: e.append(f"invalid:claim_status:{cid}")
        evs=c.get("evidence",[])
        if c.get("status") in {"SUPPORTED","CONTESTED","REFUTED"} and not evs: e.append(f"missing:claim_evidence:{cid}")
        if not evs and not c.get('counterevidence') and qid not in attempts:
            e.append(f"gate:claim_without_evidence_or_attempts:{cid}")
        fams=[]; seen_artifacts=set()
        for x in evs+c.get("counterevidence",[]):
            aid=x.get("artifact_id")
            if aid not in aids: e.append(f"invalid:claim_artifact:{cid}:{aid}")
            declared=x.get("source_family_id")
            registered=family_by_art.get(aid)
            if declared and registered and declared != registered:
                e.append(f"broken:claim_source_family:{cid}:{aid}")
            fam=registered or declared
            if aid in evidence_families and fam and evidence_families[aid] != fam:
                e.append(f"broken:claim_source_family:{cid}:{aid}")
            if fam:
                evidence_families.setdefault(aid, fam)
                if aid in aids and aid not in seen_artifacts: fams.append(fam)
            seen_artifacts.add(aid)
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
    claim_ids={c['claim_id'] for c in claims}
    for r in reviews:
        if not set(r.get('claim_ids', [])) <= claim_ids:
            e.append(f"invalid:review_claim:{r['review_id']}")
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
    # Inspect the literal final N eligible events, never backfill with older,
    # more convenient distinct routes. Blocked/error attempts do not fill slots.
    tail = yields[-window:]
    tail_routes = {signature for _, signature in tail}
    curve, saturation_metrics = _saturation_observations(events, candidates, artifacts, w)
    # Include intervening/trailing non-route events in the yield check: a capture
    # cannot hide new families merely because it is not eligible to fill a slot.
    start = next((i for i, row in enumerate(curve) if tail and row['event_id'] == tail[0][0]), len(curve))
    window_families = sorted({family for row in curve[start:] for family in row['effective']})
    if depth in {"R1","R2"}:
        if len(yields)<window: e.append("gate:insufficient_saturation_window")
        else:
            if len(tail_routes)<window: e.append("gate:saturation_window_duplicate_routes")
            if window_families: e.append("gate:not_saturated_new_family_in_window")
    saturation_metrics.update(saturation_window_required=window,
                              saturation_window_event_ids=[eid for eid, _ in tail],
                              saturation_window_distinct_routes=len(tail_routes),
                              saturation_window_new_families=window_families,
                              family_yield_curve=curve)
    if deferred: e.append("gate:high_value_candidates_deferred:"+",".join(deferred))
    metrics={"depth":depth,"events":len(events),"distinct_routes":len(distinct_routes),"must_routes":len(must),"must_routes_executed":len(must&valid_plan_events),"candidates":len(candidates),"included":len(included),"artifacts":len(artifacts),"claims":len(claims),"p0_questions":len(p0),"p0_claims":len(p0_claims),"checkpoints":dict(review_types),"benchmark_total":len(bench),"benchmark_found":len({b.get('id') for b in bench}&found),"deferred_high":len(deferred)}
    metrics.update(saturation_metrics)
    return e,w,metrics

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("run_dir"); ap.add_argument("--summary"); a=ap.parse_args()
    e,w,m=validate(a.run_dir); out={"valid":not e,"errors":e,"warnings":w,"metrics":m}
    txt=json.dumps(out,ensure_ascii=False,indent=2); print(txt)
    if a.summary: Path(a.summary).write_text(txt+"\n",encoding="utf-8")
    return 1 if e else 0
if __name__=="__main__": sys.exit(main())
