#!/usr/bin/env python3
import argparse, json, re
from collections import Counter, defaultdict
from pathlib import Path

SKIP={".git","snapshots","context-packs","gates","reviews","benchmarks"}

def files(root):
    for base in ("chapters","summaries","chapter-plans","scenes"):
        d=root/base
        if d.exists():
            for p in d.rglob("*.md"):
                if not any(x in SKIP for x in p.parts): yield p

def load_registry(root):
    p=root/"entity-registry.json"
    if not p.exists(): raise SystemExit("missing entity-registry.json")
    return json.loads(p.read_text(encoding="utf-8"))

def pattern(term):
    if len(term.strip())<2: return None
    if re.fullmatch(r"[A-Za-z0-9 _-]+",term):
        return re.compile(r"(?<![A-Za-z0-9])"+re.escape(term)+r"(?![A-Za-z0-9])",re.I)
    return re.compile(re.escape(term))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True)
    ap.add_argument("--heatmap",action="store_true")
    a=ap.parse_args(); root=Path(a.root).resolve(); reg=load_registry(root)
    alias_to_ids=defaultdict(list)
    for e in reg.get("entities",[]):
        for name in [e.get("canonical","")]+e.get("aliases",[]):
            if pattern(name): alias_to_ids[name].append(e.get("id"))
    ambiguous={k:v for k,v in alias_to_ids.items() if len(set(v))>1}
    records=[]; totals=Counter()
    for p in files(root):
        text=p.read_text(encoding="utf-8",errors="ignore")
        for e in reg.get("entities",[]):
            aliases=[]; count=0
            for name in [e.get("canonical","")]+e.get("aliases",[]):
                if name in ambiguous: continue
                rx=pattern(name)
                if rx:
                    n=len(rx.findall(text))
                    if n: aliases.append({"name":name,"count":n}); count+=n
            if count:
                eid=e.get("id"); totals[eid]+=count
                records.append({"entity_id":eid,"file":str(p.relative_to(root)),"count":count,"aliases":aliases})
    out={"schema":"minis.novel-mentions.v1","ambiguous_aliases":ambiguous,"totals":dict(totals),"records":records}
    dest=root/"mention-index.json"; dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if a.heatmap:
        print("entity\tmentions\tfiles")
        for eid,n in totals.most_common():
            print(f"{eid}\t{n}\t{sum(1 for r in records if r['entity_id']==eid)}")
    else: print(dest)
if __name__=="__main__": main()
