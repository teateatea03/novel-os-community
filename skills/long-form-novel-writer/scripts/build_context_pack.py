#!/usr/bin/env python3
import argparse, json, math, re, sys
from collections import Counter
from pathlib import Path
from context_evidence import SCHEMA, sha256_bytes, source_path, source_record, text_hash
from writing_anchors import load_anchors, source_id

# Reuse the same token-aware admission contract as interactive runtime.
SKILLS_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "immersive-interactive-fiction" / "scripts"))
from novel_judge.context_budget import admit_sources, context_policy_for_window, estimate_tokens

SKIP={".git","snapshots","context-packs","gates","reviews","benchmarks"}
TOKEN=re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")
def toks(s): return [x.lower() for x in TOKEN.findall(s)]
def chunks(path,root,size=1200):
    path=source_path(root, path.relative_to(root).as_posix())
    raw=path.read_bytes(); text=raw.decode("utf-8"); lines=text.splitlines(); out=[]; buf=[]; start=1; n=0
    for i,line in enumerate(lines,1):
        if buf and (n+len(line)>size or re.match(r"^#{1,3} ",line)):
            out.append({"file":path.relative_to(root).as_posix(),"start":start,"end":i-1,"text":"\n".join(buf)}); buf=[]; start=i; n=0
        buf.append(line); n+=len(line)+1
    if buf: out.append({"file":path.relative_to(root).as_posix(),"start":start,"end":len(lines),"text":"\n".join(buf)})
    for item in out:
        item["source_sha256"]=sha256_bytes(raw)
        item["excerpt_sha256"]=text_hash(item["text"])
    return out
def registry_terms(root,query):
    p=source_path(root,"entity-registry.json"); selected=[]; always=[]
    if not p.exists(): return selected,always
    data=json.loads(p.read_text(encoding="utf-8")); hay=query.lower()
    for e in data.get("entities",[]):
        names=[e.get("canonical","")]+e.get("aliases",[]); mode=e.get("context_mode","detected")
        if mode=="always": always.append(e)
        elif mode=="detected" and any(n and n.lower() in hay for n in names): selected.append(e)
    return selected,always
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--chapter",required=True); ap.add_argument("--query",default=""); ap.add_argument("--top-k",type=int,default=14); ap.add_argument("--budget",type=int,default=18000, help="legacy character budget; used as a soft prefilter"); ap.add_argument("--context-window",type=int,default=65536); ap.add_argument("--context-policy",choices=["lossy-admission","lossless-addressable","lossy","lossless","astra"],default=None); ap.add_argument("--profile",choices=["interactive","plan","render","research","blind_read"],default="research")
    ap.add_argument("--writing-anchors", help="project-relative optional author-selected anchor config")
    ap.add_argument("--pov", default="")
    ap.add_argument("--scene", default="")
    a=ap.parse_args()
    if not a.chapter or a.chapter in {".", ".."} or any(c in a.chapter for c in ("/", "\\")):
        ap.error("--chapter must be one project-local filename stem")
    root=Path(a.root).resolve(); query=a.query+" "+a.chapter; entities,always=registry_terms(root,query)
    anchors, anchor_reports, anchor_files, anchor_budget = load_anchors(root, a.writing_anchors, chapter=a.chapter, pov=a.pov, scene=a.scene)
    query+=" "+" ".join(n for e in entities for n in [e.get("canonical","")]+e.get("aliases",[]))
    paths=[p for p in root.rglob("*.md") if not any(x in SKIP for x in p.parts) and p.relative_to(root).as_posix() not in anchor_files]
    docs=[]
    for p in paths: docs.extend(chunks(p,root))
    qt=Counter(toks(query)); df=Counter()
    for d in docs:
        d["tokens"]=Counter(toks(d["text"])); df.update(d["tokens"].keys())
    N=max(1,len(docs)); structural=("story-bible","continuity-ledger","timeline","reader-ledger","world-rules","style-sheet")
    source_boost={e.get("source_file") for e in entities+always if e.get("source_file")}
    for d in docs:
        score=0.0
        for t,qf in qt.items():
            if t in d["tokens"]: score+=qf*d["tokens"][t]*math.log((N+1)/(df[t]+1)+1)
        if any(x in d["file"] for x in structural): score+=0.25
        if d["file"] in source_boost: score+=4.0
        d["score"]=round(score,4)
    ranked=sorted((d for d in docs if d["score"]>0),key=lambda x:(-x["score"],x["file"],x["start"]))
    chosen=[]; used=0
    report_by_id={item["id"]:item for item in anchor_reports}
    for d in anchors:
        cost=len(d["text"])
        if used+cost > min(anchor_budget, max(0, a.budget)):
            report_by_id[d["anchor_id"]]["reason"]="anchor_character_budget"
            continue
        chosen.append(d); used+=cost
    anchor_selected_count=len(chosen)
    for d in ranked:
        cost=len(d["text"])
        if chosen and (len(chosen)-anchor_selected_count>=a.top_k or used+cost>a.budget): continue
        chosen.append(d); used+=cost
    ranked=anchors+ranked
    sources=[]
    for i,d in enumerate(chosen):
        tier="CORE" if "anchor_id" in d or any(x in d["file"] for x in structural) else ("ACTIVE" if d["file"] in source_boost else "EVIDENCE")
        sources.append({"source_id":source_id(d),"preserve_text":"anchor_id" in d,"tier":tier,"priority":1000000-i if "anchor_id" in d else 100 if tier=="CORE" else (80 if tier=="ACTIVE" else round(d["score"]*10)),"text":d["text"],"provenance":{"file":d["file"],"start":d["start"],"end":d["end"],"score":d["score"]}})
    policy=context_policy_for_window(a.context_window, a.context_policy)
    admission=admit_sources(sources,profile=a.profile,context_window=a.context_window,context_policy=policy)
    allowed=set(admission.get("selected_sources",[]))
    inline=[d for d in chosen if source_id(d) in allowed]
    overflow=[]
    if policy=="lossless-addressable":
        overflow=[source_record(d) for d in chosen if source_id(d) not in allowed]
        overflow += [source_record(d) for d in ranked if d not in chosen][:80]
    for d in anchors:
        report=report_by_id[d["anchor_id"]]
        if source_id(d) in allowed:
            report.update(status="inline", reason="selected")
        elif report["reason"]=="pending_budget":
            report["reason"]="input_token_budget"
    selection_summary={"ranked_chunks":len(ranked), "inline_chunks":len(inline), "addressable_overflow_chunks":len(overflow), "unlisted_ranked_chunks":len(ranked)-len(inline)-len(overflow), "scope":"ranked_chunks_only_not_semantic_coverage"}
    chosen=inline
    used_chars=sum(len(d["text"]) for d in chosen)
    out=source_path(root,f"context-packs/{a.chapter}.md"); source_path(root,f"context-packs/{a.chapter}.json"); out.parent.mkdir(exist_ok=True)
    head=f"# Context Pack｜{a.chapter}\n\n- evidence_schema: {SCHEMA}\n- query: `{a.query}`\n- context_window: {a.context_window}\n- context_policy: {policy}\n- profile: {a.profile}\n- input_budget_tokens: {admission.get('input_budget')}\n- estimated_tokens: {admission.get('estimated_tokens', 0)}\n- used_characters: {used_chars}\n- admission: {admission.get('admission')}\n- forgotten_sources: {len(admission.get('forgotten_sources') or [])}\n- addressable_overflow: {len(overflow)}\n- selected entities: {', '.join(e.get('id','') for e in entities+always) or 'none'}\n- 注意：這是衍生檢索結果；寫作前回讀關鍵來源，不能取代正典與時間切片。lossless-addressable 不會把未內嵌來源摘要掉，只保留可回讀位址。\n"
    if anchor_reports:
        head+="\n## Writing anchor decisions (character inclusion only)\n\n"
        for report in anchor_reports:
            head+=f"- {report['id']} ({report['role']}, order {report['order']}): {report['status']} / {report['reason']}\n"
    body=[]; records=[]; position=len(head)
    for d in chosen:
        heading=f"\n## {d['file']}:{d['start']}-{d['end']}｜score {d['score']}\n\n"
        if "anchor_id" in d:
            heading=f"\n## Writing anchor {d['anchor_id']} ({d['anchor_role']}, order {d['anchor_order']})｜{d['file']}:{d['start']}-{d['end']}\n\n"
        record=source_record(d)
        record.update(pack_start=position+len(heading), pack_end=position+len(heading)+len(d["text"]))
        part=heading+d["text"]+"\n"
        body.append(part); records.append(record); position+=len(part)
    if overflow:
        body.append("\n## Addressable overflow（原文未摘要）\n\n")
        for d in overflow: body.append(f"- `{d['file']}:{d['start']}-{d['end']}` score {d['score']}\n")
    pack_text=head+"".join(body)
    out.write_text(pack_text,encoding="utf-8",newline="\n"); manifest=out.with_suffix(".json"); manifest.write_text(json.dumps({"schema":SCHEMA,"writing_anchors":{"schema":"minis.writing-anchors.v1","budget_characters":anchor_budget,"render_order":[d["anchor_id"] for d in chosen if "anchor_id" in d],"pov":a.pov,"scene":a.scene,"anchors":anchor_reports},"pack_sha256":text_hash(pack_text),"offset_unit":"unicode_characters_half_open","selection_summary":selection_summary,"chapter":a.chapter,"query":a.query,"budget_characters":a.budget,"top_k":a.top_k,"context_window":a.context_window,"context_policy":policy,"profile":a.profile,"used_characters":used_chars,"estimated_tokens":admission.get("estimated_tokens",0),"admission":admission,"addressable_overflow":overflow,"entities":[e.get("id") for e in entities+always],"sources":records},ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(out)
if __name__=="__main__": main()
