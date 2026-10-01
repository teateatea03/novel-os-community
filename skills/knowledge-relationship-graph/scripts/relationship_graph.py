#!/usr/bin/env python3
"""Temporal, provenance-aware relationship graph CLI backed by Graphify-compatible JSON."""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = "minis.relationship-graph.v1"
CONF = {"EXTRACTED": 1.0, "INFERRED": 0.75, "AMBIGUOUS": 0.25}
TYPES = {"person","organization","group","place","event","object","document","concept","project","task","decision","claim","resource","system","role","other"}
CHARACTER_CATEGORIES = {"real", "novel", "anime", "film", "other"}
CHARACTER_KINDS = {"real_person", "historical_person", "fictional_character", "original_character", "unknown"}
CHARACTER_CANONS = {"public_record", "novel_canon", "anime_canon", "film_canon", "cross_adaptation", "user_created", "unknown"}


def now(): return datetime.now(timezone.utc).isoformat(timespec="seconds")
def root_path(v): return Path(v).expanduser().resolve()
def out_dir(root): return root_path(root) / "graphify-out"
def graph_path(root): return out_dir(root) / "graph.json"

def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def empty_graph(title):
    t = now()
    return {"directed":True,"multigraph":True,"graph":{"schema":SCHEMA,"title":title,"created_at":t,"updated_at":t,"sources":[]},"nodes":[],"links":[],"hyperedges":[]}

def normalize(data):
    data.setdefault("directed", True); data.setdefault("multigraph", True)
    meta=data.setdefault("graph",{}); meta.setdefault("schema",SCHEMA); meta.setdefault("sources",[])
    data.setdefault("nodes",[]); data.setdefault("links",data.pop("edges",[])); data.setdefault("hyperedges",[])
    for i,e in enumerate(data["links"]):
        e.setdefault("id", e.get("key") or f"edge:{i+1}"); e.setdefault("key",e["id"])
        e.setdefault("status","active"); e.setdefault("confidence","EXTRACTED")
        e.setdefault("confidence_score",CONF.get(e["confidence"],.5)); e.setdefault("evidence",[])
    return data

def load(root):
    p=graph_path(root)
    if not p.exists(): raise SystemExit(f"Graph not initialized: {p}")
    return normalize(json.loads(p.read_text(encoding="utf-8")))

def audit(root, operation, details):
    p=out_dir(root)/"audit.jsonl"; p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f: f.write(json.dumps({"at":now(),"operation":operation,"details":details},ensure_ascii=False)+"\n")

def save(root,data,operation,details):
    p=graph_path(root)
    if p.exists(): shutil.copyfile(p,p.with_suffix(".json.bak"))
    data["graph"]["updated_at"]=now(); atomic_json(p,data); audit(root,operation,details)

def slug(s):
    x=re.sub(r"[^\w.-]+","-",s.strip().lower(),flags=re.UNICODE).strip("-.")
    return x or hashlib.sha1(s.encode()).hexdigest()[:10]

def parse_json(s, default):
    if not s: return default
    try: return json.loads(s)
    except json.JSONDecodeError as e: raise SystemExit(f"Invalid JSON: {e}")

def evidence(args):
    if not any(getattr(args,k,None) for k in ("source_file","source_location","source_url","quote")): return []
    return [{"source_file":getattr(args,"source_file",None),"source_location":getattr(args,"source_location",None),"source_url":getattr(args,"source_url",None),"quote":getattr(args,"quote",None),"captured_at":now()}]

def node_map(data): return {n["id"]:n for n in data["nodes"]}
def resolve(data,q):
    if q in node_map(data): return q
    nq=q.casefold(); hits=[]
    for n in data["nodes"]:
        props=n.get("properties",{})
        names=[n.get("label",""),props.get("name_zh", ""),*n.get("aliases",[])]
        if any(str(x).casefold()==nq for x in names): hits.append(n["id"])
    if len(hits)==1:return hits[0]
    if not hits: raise SystemExit(f"Unknown node: {q}")
    raise SystemExit(f"Ambiguous node '{q}': {', '.join(hits)}")

def add_node_obj(data,obj,force_new=False):
    nodes=node_map(data); nid=obj["id"]
    if nid in nodes: raise ValueError(f"duplicate node id: {nid}")
    names={str(obj.get("label","")).casefold(),*(str(x).casefold() for x in obj.get("aliases",[]))}
    clashes=[]
    for n in data["nodes"]:
        other={str(n.get("label","")).casefold(),*(str(x).casefold() for x in n.get("aliases",[]))}
        if (names-{""}) & (other-{""}): clashes.append(n["id"])
    if clashes and not force_new: raise ValueError(f"alias/name collision with {clashes}; merge or use force_new")
    data["nodes"].append(obj)

def edge_id(src,rel,tgt,vf=None):
    raw=f"{src}|{rel}|{tgt}|{vf or ''}|{now()}"; return "edge:"+hashlib.sha1(raw.encode()).hexdigest()[:14]

def add_edge_obj(data,obj,allow_duplicate=False):
    ids=set(node_map(data)); src=obj["source"]; tgt=obj["target"]
    if src not in ids or tgt not in ids: raise ValueError(f"dangling edge {src}->{tgt}")
    if not allow_duplicate:
        for e in data["links"]:
            if e.get("status","active")=="active" and all(e.get(k)==obj.get(k) for k in ("source","target","relation","valid_from","valid_to")):
                raise ValueError(f"duplicate active relation: {e.get('id')}")
    obj.setdefault("id",edge_id(src,obj["relation"],tgt,obj.get("valid_from"))); obj.setdefault("key",obj["id"])
    data["links"].append(obj)

def active_edge(e,as_of=None):
    if e.get("status","active") not in ("active","planned","disputed"): return False
    if not as_of:return True
    vf=e.get("valid_from"); vt=e.get("valid_to")
    return (not vf or vf<=as_of) and (not vt or as_of<=vt)

def validation(data):
    errors=[]; warnings=[]; ids=[]
    for n in data["nodes"]:
        if not n.get("id") or not n.get("label"): errors.append(f"node missing id/label: {n}")
        ids.append(n.get("id"))
        if n.get("entity_type") not in TYPES: warnings.append(f"custom entity_type {n.get('entity_type')} on {n.get('id')}")
        # World root classification is mandatory for world databases. Legacy graphs
        # without a world root remain valid; any present world root must be complete.
        if n.get("properties", {}).get("world_category") == "world" or str(n.get("id", "")).startswith("world:"):
            required_world = ("subject_category", "subject_subcategory", "subject_kind", "source_medium", "canon_scope", "version_scope", "franchise", "genre", "classification_basis", "classification_confidence")
            props = n.get("properties", {})
            missing = [f for f in required_world if (props.get(f) is None and f != "franchise") or props.get(f) == "" or props.get(f) == []]
            if missing: errors.append(f"world root missing classification fields {missing}: {n.get('id')}")
            if props.get("classification_confidence") not in {"EXTRACTED", "INFERRED", "AMBIGUOUS"}:
                errors.append(f"world root invalid classification_confidence: {n.get('id')}")
        # Character subject classification is required for person nodes created by
        # the character database; legacy/non-character person nodes remain valid.
        if n.get("entity_type") == "person" and n.get("properties", {}).get("character_record") is True:
            props = n.get("properties", {})
            if props.get("subject_category") not in CHARACTER_CATEGORIES:
                errors.append(f"person character missing/invalid subject_category: {n.get('id')}")
            if props.get("subject_kind") not in CHARACTER_KINDS:
                errors.append(f"person character missing/invalid subject_kind: {n.get('id')}")
            if props.get("canon_scope") not in CHARACTER_CANONS:
                errors.append(f"person character missing/invalid canon_scope: {n.get('id')}")
            for field in ("subject_subcategory", "source_medium", "version_scope", "classification_basis", "classification_confidence"):
                if not props.get(field): warnings.append(f"person character missing {field}: {n.get('id')}")
    dup={x for x in ids if x and ids.count(x)>1}
    if dup: errors.append(f"duplicate node ids: {sorted(dup)}")
    idset=set(ids); aliases={}
    for n in data["nodes"]:
        for a in [n.get("label",""),*n.get("aliases",[]),n.get("properties",{}).get("name_zh","")]: aliases.setdefault(str(a).casefold(),[]).append(n.get("id"))
    for a,v in aliases.items():
        if a and len(set(v))>1: warnings.append(f"ambiguous alias '{a}': {sorted(set(v))}")
    edgeids=[]
    for e in data["links"]:
        edgeids.append(e.get("id"))
        if e.get("source") not in idset or e.get("target") not in idset: errors.append(f"dangling edge {e.get('id')}")
        if not e.get("relation"): errors.append(f"edge missing relation: {e.get('id')}")
        s=e.get("confidence_score",0)
        if not isinstance(s,(int,float)) or not 0<=s<=1: errors.append(f"invalid confidence_score: {e.get('id')}")
        if e.get("confidence")=="EXTRACTED" and not (e.get("evidence") or e.get("source_file")): warnings.append(f"EXTRACTED edge lacks provenance: {e.get('id')}")
        if e.get("valid_from") and e.get("valid_to") and e["valid_from"]>e["valid_to"]: errors.append(f"invalid valid interval: {e.get('id')}")
    dup_e={x for x in edgeids if x and edgeids.count(x)>1}
    if dup_e: errors.append(f"duplicate edge ids: {sorted(dup_e)}")
    try:
        import networkx as nx
        for rel in ("causes","depends_on","parent_of","precedes"):
            g=nx.DiGraph((e["source"],e["target"]) for e in data["links"] if active_edge(e) and e.get("relation")==rel)
            cyc=list(nx.simple_cycles(g))[:3]
            if cyc: warnings.append(f"cycle in {rel}: {cyc}")
    except Exception: pass
    return errors,warnings

def nx_graph(data,as_of=None):
    import networkx as nx
    g=nx.MultiDiGraph(**data.get("graph",{}))
    for n in data["nodes"]:
        attrs={k:v for k,v in n.items() if k!="id"}; g.add_node(n["id"],**attrs)
    for e in data["links"]:
        if not active_edge(e,as_of): continue
        attrs={k:v for k,v in e.items() if k not in ("source","target","key")}
        g.add_edge(e["source"],e["target"],key=e.get("key") or e.get("id"),**attrs)
    g.graph["hyperedges"]=data.get("hyperedges",[])
    return g

def cmd_init(a):
    p=graph_path(a.root)
    if p.exists() and not a.force: raise SystemExit(f"Refusing to overwrite: {p}")
    out_dir(a.root).mkdir(parents=True,exist_ok=True)
    atomic_json(p,empty_graph(a.title)); audit(a.root,"init",{"title":a.title}); print(p)

def cmd_add_node(a):
    d=load(a.root); conf=a.confidence
    obj={"id":a.id,"label":a.label,"entity_type":a.type,"file_type":"document" if a.type=="document" else "concept","aliases":a.alias or [],"properties":parse_json(a.properties,{}),"status":a.status,"valid_from":a.valid_from,"valid_to":a.valid_to,"confidence":conf,"confidence_score":a.confidence_score if a.confidence_score is not None else CONF[conf],"source_file":a.source_file,"source_location":a.source_location,"source_url":a.source_url,"captured_at":now(),"evidence":evidence(a)}
    try:add_node_obj(d,obj,a.force_new)
    except ValueError as e: raise SystemExit(str(e))
    save(a.root,d,"add_node",{"id":a.id}); print(a.id)

def cmd_add_edge(a):
    d=load(a.root); src=resolve(d,a.source); tgt=resolve(d,a.target); conf=a.confidence
    obj={"source":src,"target":tgt,"relation":a.relation,"relation_category":a.category,"inverse_relation":a.inverse,"directed":not a.undirected,"polarity":a.polarity,"properties":parse_json(a.properties,{}),"status":a.status,"valid_from":a.valid_from,"valid_to":a.valid_to,"transaction_from":now(),"transaction_to":None,"confidence":conf,"confidence_score":a.confidence_score if a.confidence_score is not None else CONF[conf],"source_file":a.source_file,"source_location":a.source_location,"source_url":a.source_url,"evidence":evidence(a)}
    try:add_edge_obj(d,obj,a.allow_duplicate)
    except ValueError as e: raise SystemExit(str(e))
    save(a.root,d,"add_edge",{"id":obj["id"],"source":src,"target":tgt,"relation":a.relation}); print(obj["id"])

def cmd_add_event(a):
    d=load(a.root); conf=a.confidence
    obj={"id":a.id,"label":a.label,"entity_type":"event","file_type":"concept","aliases":[],"properties":parse_json(a.properties,{}),"event_time":a.time,"event_end":a.end_time,"status":a.status,"confidence":conf,"confidence_score":CONF[conf],"source_file":a.source_file,"source_location":a.source_location,"source_url":a.source_url,"captured_at":now(),"evidence":evidence(a)}
    try:add_node_obj(d,obj,a.force_new)
    except ValueError as e: raise SystemExit(str(e))
    if a.place:
        place=resolve(d,a.place); add_edge_obj(d,{"source":a.id,"target":place,"relation":"occurred_at","relation_category":"spatial","status":"active","confidence":conf,"confidence_score":CONF[conf],"evidence":evidence(a)},False)
    for spec in a.participant or []:
        bits=spec.split(":",1); pid=resolve(d,bits[0]); role=bits[1] if len(bits)>1 else "participant"
        add_edge_obj(d,{"source":pid,"target":a.id,"relation":"participated_in","relation_category":"event","properties":{"role":role},"status":"active","confidence":conf,"confidence_score":CONF[conf],"evidence":evidence(a)},True)
    save(a.root,d,"add_event",{"id":a.id}); print(a.id)

def cmd_import(a):
    d=load(a.root); batch=json.loads(Path(a.file).read_text(encoding="utf-8")); added={"nodes":0,"links":0,"hyperedges":0}; errs=[]
    classification = batch.get("classification")
    if classification is None:
        raise SystemExit("Missing mandatory top-level classification; refusing import")
    required = ("subject_category", "subject_subcategory", "subject_kind", "source_medium", "canon_scope", "version_scope", "franchise", "genre", "classification_basis", "classification_confidence")
    missing = [k for k in required if k not in classification or classification[k] == "" or classification[k] == [] or (classification[k] is None and k != "franchise")]
    if missing:
        raise SystemExit("Incomplete mandatory classification; refusing import: " + ", ".join(missing))
    d.setdefault("graph", {})["classification"] = classification
    if batch.get("sources"):
        d["graph"]["sources"] = sorted(set(d["graph"].get("sources", []) + batch["sources"]))
    for meta_key in ("world_id", "as_of", "timezone", "scope", "provenance_note"):
        if meta_key in batch:
            d["graph"][meta_key] = batch[meta_key]
    for n in batch.get("nodes",[]):
        n.setdefault("entity_type",n.get("type","other")); n.setdefault("file_type","concept"); n.setdefault("aliases",[]); n.setdefault("status","active"); n.setdefault("confidence","INFERRED"); n.setdefault("confidence_score",CONF.get(n["confidence"],.75)); n.setdefault("captured_at",now())
        try:add_node_obj(d,n,a.force_new); added["nodes"]+=1
        except ValueError as e: errs.append(str(e))
    for e in batch.get("links",batch.get("edges",[])):
        try:
            e["source"]=resolve(d,e["source"]); e["target"]=resolve(d,e["target"]); e.setdefault("status","active"); e.setdefault("confidence","INFERRED"); e.setdefault("confidence_score",CONF.get(e["confidence"],.75)); e.setdefault("transaction_from",now()); e.setdefault("evidence",[])
            add_edge_obj(d,e,a.allow_duplicate); added["links"]+=1
        except (ValueError,SystemExit) as x: errs.append(str(x))
    d["hyperedges"].extend(batch.get("hyperedges",[])); added["hyperedges"]=len(batch.get("hyperedges",[]))
    if errs and a.strict: raise SystemExit("\n".join(errs))
    save(a.root,d,"import",{"file":str(a.file),**added,"errors":errs}); print(json.dumps({"added":added,"errors":errs},ensure_ascii=False,indent=2))

def cmd_close_edge(a):
    d=load(a.root); hit=False
    for e in d["links"]:
        if e.get("id")==a.id:
            e["status"]=a.status; e["transaction_to"]=a.at or now();
            if a.valid_to:e["valid_to"]=a.valid_to
            hit=True;break
    if not hit: raise SystemExit(f"Unknown edge id: {a.id}")
    save(a.root,d,"close_edge",{"id":a.id,"status":a.status}); print(a.id)

def cmd_validate(a):
    d=load(a.root); er,wa=validation(d); out={"ok":not er,"errors":er,"warnings":wa,"nodes":len(d["nodes"]),"links":len(d["links"]),"hyperedges":len(d["hyperedges"])}; print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(1 if er else 0)

def find_nodes(d,q,limit=10):
    from difflib import SequenceMatcher
    terms=q.casefold().split(); scored=[]
    for n in d["nodes"]:
        props=n.get("properties",{})
        text=" ".join([n.get("id",""),n.get("label",""),props.get("name_zh", ""),*n.get("aliases",[]),n.get("entity_type",""),json.dumps(props,ensure_ascii=False)]).casefold()
        exact=sum(3 for t in terms if t in text); fuzzy=max((SequenceMatcher(None,t,text[:max(len(t)*4,40)]).ratio() for t in terms),default=0)
        score=exact+fuzzy
        if score>0.25: scored.append((score,n))
    return [n for _,n in sorted(scored,key=lambda x:(-x[0],x[1].get("label","")))[:limit]]

def cmd_search(a): print(json.dumps(find_nodes(load(a.root),a.query,a.limit),ensure_ascii=False,indent=2))
def cmd_neighbors(a):
    d=load(a.root); nid=resolve(d,a.node); rows=[]
    for e in d["links"]:
        if active_edge(e,a.as_of) and (e["source"]==nid or e["target"]==nid): rows.append(e)
    print(json.dumps({"node":node_map(d)[nid],"relations":rows},ensure_ascii=False,indent=2))
def cmd_timeline(a):
    d=load(a.root); ev=[n for n in d["nodes"] if n.get("entity_type")=="event"]
    ev.sort(key=lambda n:(n.get("event_time") or "9999",n.get("label",""))); print(json.dumps(ev,ensure_ascii=False,indent=2))
def cmd_path(a):
    import networkx as nx
    d=load(a.root); s=resolve(d,a.source); t=resolve(d,a.target); g=nx_graph(d,a.as_of); h=g if a.directed else g.to_undirected()
    try:p=nx.shortest_path(h,s,t)
    except nx.NetworkXNoPath: raise SystemExit("No path")
    seg=[]
    for x,y in zip(p,p[1:]):
        ed=g.get_edge_data(x,y) or g.get_edge_data(y,x) or {}; vals=list(ed.values()) if isinstance(ed,dict) else []
        seg.append({"source":x,"target":y,"relations":[v.get("relation") for v in vals]})
    print(json.dumps({"nodes":p,"segments":seg},ensure_ascii=False,indent=2))
def cmd_affected(a):
    d=load(a.root); start=resolve(d,a.node); rels=set(a.relation or []); seen={start}; frontier=[start]; rows=[]
    for depth in range(1,a.depth+1):
        nxt=[]
        for cur in frontier:
            for e in d["links"]:
                if not active_edge(e,a.as_of) or e["source"]!=cur or (rels and e.get("relation") not in rels): continue
                rows.append({"depth":depth,**e}); tgt=e["target"]
                if tgt not in seen:seen.add(tgt);nxt.append(tgt)
        frontier=nxt
    print(json.dumps({"start":start,"affected":rows,"nodes":[node_map(d)[x] for x in seen]},ensure_ascii=False,indent=2))
def cmd_snapshot(a):
    p=graph_path(a.root); sd=out_dir(a.root)/"snapshots"; sd.mkdir(parents=True,exist_ok=True); target=sd/f"graph-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"; shutil.copyfile(p,target); audit(a.root,"snapshot",{"path":str(target)}); print(target)

def mermaid(g,path):
    def mid(x): return "n_"+hashlib.sha1(str(x).encode()).hexdigest()[:10]
    lines=["flowchart LR"]
    for nid,d in g.nodes(data=True): lines.append(f'  {mid(nid)}["{str(d.get("label",nid)).replace(chr(34),chr(39))}"]')
    for u,v,d in g.edges(data=True): lines.append(f'  {mid(u)} -->|"{str(d.get("relation","related_to")).replace(chr(34),chr(39))}"| {mid(v)}')
    path.write_text("```mermaid\n"+"\n".join(lines)+"\n```\n",encoding="utf-8")
def cmd_export(a):
    d=load(a.root); er,wa=validation(d)
    if er: raise SystemExit("Graph invalid; run validate\n"+"\n".join(er))
    g=nx_graph(d,a.as_of); od=out_dir(a.root); od.mkdir(parents=True,exist_ok=True)
    from graphify.cluster import cluster,label_communities_by_hub
    from graphify.export import to_html,to_cypher
    from graphify.analyze import god_nodes
    comm=cluster(g); labels=label_communities_by_hub(g,comm)
    outputs=[]
    try: to_html(g,comm,str(od/"graph.html"),community_labels=labels); outputs.append(str(od/"graph.html"))
    except Exception as e: wa.append(f"HTML export failed: {e}")
    if a.graphml:
        try:
            import networkx as nx
            h=nx.DiGraph()
            for nid,attrs in g.nodes(data=True): h.add_node(nid,**{k:(json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else ("" if v is None else v)) for k,v in attrs.items()})
            for u,v,attrs in g.edges(data=True):
                clean={k:(json.dumps(x,ensure_ascii=False,sort_keys=True) if isinstance(x,(dict,list)) else ("" if x is None else x)) for k,x in attrs.items()}
                if h.has_edge(u,v): clean["parallel_relations"]=(h.edges[u,v].get("parallel_relations","")+";"+str(clean.get("relation",""))).strip(";")
                h.add_edge(u,v,**clean)
            nx.write_graphml(h,str(od/"graph.graphml")); outputs.append(str(od/"graph.graphml"))
        except Exception as e: wa.append(f"GraphML export failed: {e}")
    if a.cypher:
        try: to_cypher(g,str(od/"cypher.txt")); outputs.append(str(od/"cypher.txt"))
        except Exception as e: wa.append(f"Cypher export failed: {e}")
    mermaid(g,od/"graph.mmd.md"); outputs.append(str(od/"graph.mmd.md"))
    report=[f"# {d['graph'].get('title','Relationship Graph')}","",f"- Nodes: {g.number_of_nodes()}",f"- Relations: {g.number_of_edges()}",f"- Communities: {len(comm)}","", "## Hubs"]
    for x in god_nodes(g,10): report.append(f"- {x}")
    report += ["","## Communities"]+[f"- {cid} — {labels.get(cid)}: {len(ns)} nodes" for cid,ns in comm.items()]
    report += ["","## Validation warnings"]+[f"- {x}" for x in wa] if wa else ["","## Validation warnings","- None"]
    (od/"GRAPH_REPORT.md").write_text("\n".join(report)+"\n",encoding="utf-8"); outputs.append(str(od/"GRAPH_REPORT.md"))
    print(json.dumps({"outputs":outputs,"warnings":wa},ensure_ascii=False,indent=2))

def add_prov(p):
    p.add_argument("--source-file");p.add_argument("--source-location");p.add_argument("--source-url");p.add_argument("--quote")
def add_conf(p):
    p.add_argument("--confidence",choices=CONF,default="EXTRACTED");p.add_argument("--confidence-score",type=float);add_prov(p)
def parser():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
    q=sp.add_parser("init");q.add_argument("--root",required=True);q.add_argument("--title",required=True);q.add_argument("--force",action="store_true");q.set_defaults(fn=cmd_init)
    q=sp.add_parser("add-node");q.add_argument("--root",required=True);q.add_argument("--id",required=True);q.add_argument("--label",required=True);q.add_argument("--type",choices=sorted(TYPES),default="other");q.add_argument("--alias",action="append");q.add_argument("--properties");q.add_argument("--status",default="active");q.add_argument("--valid-from");q.add_argument("--valid-to");q.add_argument("--force-new",action="store_true");add_conf(q);q.set_defaults(fn=cmd_add_node)
    q=sp.add_parser("add-edge");q.add_argument("--root",required=True);q.add_argument("--source",required=True);q.add_argument("--target",required=True);q.add_argument("--relation",required=True);q.add_argument("--category",default="general");q.add_argument("--inverse");q.add_argument("--undirected",action="store_true");q.add_argument("--polarity",default="neutral");q.add_argument("--properties");q.add_argument("--status",default="active");q.add_argument("--valid-from");q.add_argument("--valid-to");q.add_argument("--allow-duplicate",action="store_true");add_conf(q);q.set_defaults(fn=cmd_add_edge)
    q=sp.add_parser("add-event");q.add_argument("--root",required=True);q.add_argument("--id",required=True);q.add_argument("--label",required=True);q.add_argument("--time");q.add_argument("--end-time");q.add_argument("--place");q.add_argument("--participant",action="append",help="NODE[:ROLE]");q.add_argument("--properties");q.add_argument("--status",default="active");q.add_argument("--force-new",action="store_true");add_conf(q);q.set_defaults(fn=cmd_add_event)
    q=sp.add_parser("import");q.add_argument("--root",required=True);q.add_argument("--file",required=True);q.add_argument("--strict",action="store_true");q.add_argument("--force-new",action="store_true");q.add_argument("--allow-duplicate",action="store_true");q.set_defaults(fn=cmd_import)
    q=sp.add_parser("close-edge");q.add_argument("--root",required=True);q.add_argument("--id",required=True);q.add_argument("--status",default="superseded");q.add_argument("--at");q.add_argument("--valid-to");q.set_defaults(fn=cmd_close_edge)
    q=sp.add_parser("validate");q.add_argument("--root",required=True);q.set_defaults(fn=cmd_validate)
    q=sp.add_parser("search");q.add_argument("--root",required=True);q.add_argument("query");q.add_argument("--limit",type=int,default=10);q.set_defaults(fn=cmd_search)
    q=sp.add_parser("neighbors");q.add_argument("--root",required=True);q.add_argument("node");q.add_argument("--as-of");q.set_defaults(fn=cmd_neighbors)
    q=sp.add_parser("timeline");q.add_argument("--root",required=True);q.set_defaults(fn=cmd_timeline)
    q=sp.add_parser("path");q.add_argument("--root",required=True);q.add_argument("source");q.add_argument("target");q.add_argument("--directed",action="store_true");q.add_argument("--as-of");q.set_defaults(fn=cmd_path)
    q=sp.add_parser("affected");q.add_argument("--root",required=True);q.add_argument("node");q.add_argument("--relation",action="append");q.add_argument("--depth",type=int,default=3);q.add_argument("--as-of");q.set_defaults(fn=cmd_affected)
    q=sp.add_parser("snapshot");q.add_argument("--root",required=True);q.set_defaults(fn=cmd_snapshot)
    q=sp.add_parser("export");q.add_argument("--root",required=True);q.add_argument("--as-of");q.add_argument("--graphml",action="store_true");q.add_argument("--cypher",action="store_true");q.set_defaults(fn=cmd_export)
    return p
if __name__=="__main__":
    a=parser().parse_args(); a.fn(a)
