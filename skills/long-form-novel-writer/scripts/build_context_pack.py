#!/usr/bin/env python3
import argparse, json, math, re, sys
from collections import Counter
from pathlib import Path

# Reuse the same token-aware admission contract as interactive runtime.
SKILLS_ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_ROOT / "immersive-interactive-fiction" / "scripts"))
from novel_judge.context_budget import admit_sources, context_policy_for_window, estimate_tokens

SKIP={".git","snapshots","context-packs","gates","reviews","benchmarks"}
TOKEN=re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+")
def toks(s): return [x.lower() for x in TOKEN.findall(s)]
def chunks(path,root,size=1200):
    text=path.read_text(encoding="utf-8",errors="ignore"); lines=text.splitlines(); out=[]; buf=[]; start=1; n=0
    for i,line in enumerate(lines,1):
        if buf and (n+len(line)>size or re.match(r"^#{1,3} ",line)):
            out.append({"file":str(path.relative_to(root)),"start":start,"end":i-1,"text":"\n".join(buf)}); buf=[]; start=i; n=0
        buf.append(line); n+=len(line)+1
    if buf: out.append({"file":str(path.relative_to(root)),"start":start,"end":len(lines),"text":"\n".join(buf)})
    return out
def registry_terms(root,query):
    p=root/"entity-registry.json"; selected=[]; always=[]
    if not p.exists(): return selected,always
    data=json.loads(p.read_text(encoding="utf-8")); hay=query.lower()
    for e in data.get("entities",[]):
        names=[e.get("canonical","")]+e.get("aliases",[]); mode=e.get("context_mode","detected")
        if mode=="always": always.append(e)
        elif mode=="detected" and any(n and n.lower() in hay for n in names): selected.append(e)
    return selected,always
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--chapter",required=True); ap.add_argument("--query",default=""); ap.add_argument("--top-k",type=int,default=14); ap.add_argument("--budget",type=int,default=18000, help="legacy character budget; used as a soft prefilter"); ap.add_argument("--context-window",type=int,default=65536); ap.add_argument("--context-policy",choices=["lossy-admission","lossless-addressable","lossy","lossless","astra"],default=None); ap.add_argument("--profile",choices=["interactive","plan","render","research","blind_read"],default="research")
    a=ap.parse_args(); root=Path(a.root).resolve(); query=a.query+" "+a.chapter; entities,always=registry_terms(root,query)
    query+=" "+" ".join(n for e in entities for n in [e.get("canonical","")]+e.get("aliases",[]))
    paths=[p for p in root.rglob("*.md") if not any(x in SKIP for x in p.parts)]
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
    for d in ranked:
        cost=len(d["text"])
        if chosen and (len(chosen)>=a.top_k or used+cost>a.budget): continue
        chosen.append(d); used+=cost
    sources=[]
    for i,d in enumerate(chosen):
        tier="CORE" if any(x in d["file"] for x in structural) else ("ACTIVE" if d["file"] in source_boost else "EVIDENCE")
        sources.append({"source_id":f"{d['file']}:{d['start']}-{d['end']}","tier":tier,"priority":100 if tier=="CORE" else (80 if tier=="ACTIVE" else round(d["score"]*10)),"text":d["text"],"provenance":{"file":d["file"],"start":d["start"],"end":d["end"],"score":d["score"]}})
    policy=context_policy_for_window(a.context_window, a.context_policy)
    admission=admit_sources(sources,profile=a.profile,context_window=a.context_window,context_policy=policy)
    allowed=set(admission.get("selected_sources",[]))
    inline=[d for d in chosen if f"{d['file']}:{d['start']}-{d['end']}" in allowed]
    overflow=[]
    if policy=="lossless-addressable":
        overflow=[{"file":d["file"],"start":d["start"],"end":d["end"],"score":d["score"]} for d in chosen if f"{d['file']}:{d['start']}-{d['end']}" not in allowed]
        overflow += [{"file":d["file"],"start":d["start"],"end":d["end"],"score":d["score"]} for d in ranked if d not in chosen][:80]
    chosen=inline
    used_chars=sum(len(d["text"]) for d in chosen)
    out=root/"context-packs"/f"{a.chapter}.md"; out.parent.mkdir(exist_ok=True)
    head=f"# Context Pack｜{a.chapter}\n\n- query: `{a.query}`\n- context_window: {a.context_window}\n- context_policy: {policy}\n- profile: {a.profile}\n- input_budget_tokens: {admission.get('input_budget')}\n- estimated_tokens: {admission.get('estimated_tokens', 0)}\n- used_characters: {used_chars}\n- admission: {admission.get('admission')}\n- forgotten_sources: {len(admission.get('forgotten_sources') or [])}\n- addressable_overflow: {len(admission.get('addressable_overflow') or overflow)}\n- selected entities: {', '.join(e.get('id','') for e in entities+always) or 'none'}\n- 注意：這是衍生檢索結果；寫作前回讀關鍵來源，不能取代正典與時間切片。lossless-addressable 不會把未內嵌來源摘要掉，只保留可回讀位址。\n"
    body=[]
    for d in chosen: body.append(f"\n## {d['file']}:{d['start']}-{d['end']}｜score {d['score']}\n\n{d['text']}\n")
    if overflow:
        body.append("\n## Addressable overflow（原文未摘要）\n\n")
        for d in overflow: body.append(f"- `{d['file']}:{d['start']}-{d['end']}` score {d['score']}\n")
    out.write_text(head+"".join(body),encoding="utf-8"); manifest=out.with_suffix(".json"); manifest.write_text(json.dumps({"schema":"minis.context-pack.v4","chapter":a.chapter,"query":a.query,"budget_characters":a.budget,"context_window":a.context_window,"context_policy":policy,"profile":a.profile,"used_characters":used_chars,"estimated_tokens":admission.get("estimated_tokens",0),"admission":admission,"addressable_overflow":overflow,"entities":[e.get("id") for e in entities+always],"sources":[{k:d[k] for k in ("file","start","end","score")} for d in chosen]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(out)
if __name__=="__main__": main()
