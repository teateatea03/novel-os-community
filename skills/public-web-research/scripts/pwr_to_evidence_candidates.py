#!/usr/bin/env python3
"""Convert PWR acquisition candidates into Evidence Run v2 candidate drafts.

The output is deliberately `defer`/`needs_review`; it cannot create checked claims.
"""
import argparse, hashlib, json, sys
from pathlib import Path

def load_json(path):
    with open(path,encoding="utf-8") as f: return json.load(f)
def iter_jsonl(path):
    with open(path,encoding="utf-8") as f:
        for n,line in enumerate(f,1):
            if line.strip():
                try: yield json.loads(line)
                except Exception as e: raise ValueError(f"{path}:{n}: {e}")
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--pwr-run",required=True); ap.add_argument("--discovered-by",required=True,help="existing Evidence Run v2 event_id"); ap.add_argument("--prefix",default="PWRK"); ap.add_argument("--source-role",choices=["primary","first_person","contemporaneous","independent_secondary","tertiary","lead"],default="lead"); ap.add_argument("--output",required=True); a=ap.parse_args()
    root=Path(a.pwr_run).resolve(); protocol=load_json(root/"protocol.json"); cp=load_json(root/"checkpoint.json")
    source=root/"derived/candidates/candidates.jsonl"
    if not source.exists(): raise ValueError("PWR candidates file missing")
    out=[]
    for i,c in enumerate(iter_jsonl(source),1):
        if c.get("review_status")!="unreviewed" or c.get("disposition")!="defer": raise ValueError("adapter accepts only unreviewed/defer PWR candidates")
        out.append({"candidate_id":f"{a.prefix}{i:04d}","discovered_by":a.discovered_by,"canonical_locator":c["canonical_url"],"title":c.get("title") or "UNKNOWN","creator":Path(root).name,"published_at":"UNKNOWN","source_role":a.source_role,"source_family_hint":"UNASSESSED:PWR:"+hashlib.sha256(c["canonical_url"].encode()).hexdigest()[:16],"disposition":"defer","reason_code":"needs_review","screened_by":"UNSCREENED","screened_at":"PENDING","priority":"normal","acquisition_provenance":{"pwr_run_id":protocol["run_id"],"pwr_event_head":cp["last_event_hash"],"pwr_candidate_id":c["candidate_id"],"raw_sha256":c["raw_sha256"],"derived":c.get("derived",{}),"captured_at":c.get("captured_at"),"security_flags":c.get("security_flags",[]),"escalation_required":c.get("escalation_required",False)},"adapter_warning":"Must be screened and rewritten before include; this is not a claim or source-family decision."})
    dest=Path(a.output); dest.parent.mkdir(parents=True,exist_ok=True)
    with open(dest,"w",encoding="utf-8") as f:
        for x in out: f.write(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n")
    print(json.dumps({"written":len(out),"output":str(dest),"forced_disposition":"defer","event_binding":a.discovered_by},ensure_ascii=False,indent=2))
    return 0
if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as e: print(f"error: {e}",file=sys.stderr); raise SystemExit(4)
