#!/usr/bin/env python3
import argparse, json, re
from collections import Counter
from pathlib import Path

CANON_PATTERNS={
 "age":re.compile(r"((?:(?![一二三四五六七八九十百兩〇零])[\u4e00-\u9fffA-Za-z·]){2,12})[：:，,、是為年齡 ]{0,8}([一二三四五六七八九十百兩〇零0-9]{1,3})\s*歲"),
 "count":re.compile(r"((?:(?![一二三四五六七八九十百兩〇零])[\u4e00-\u9fffA-Za-z·]){2,12})[：:，,、有持共計 ]{0,8}([0-9一二三四五六七八九十兩]{1,4})\s*(?:枚|把|人|封|顆|瓶|天|年|小時)"),
}
META=("身為AI","作為AI","以下是本章","這個場景","根據你的要求","我不能繼續")

def loc(text,start): return text.count("\n",0,start)+1

def collect(root):
    paths=[]
    for name in ("story-bible.md","continuity-ledger.md","timeline.md","world-rules.md","world-bible.md","object-state.md"):
        p=root/name
        if p.exists(): paths.append(p)
    for d in ("characters","locations","factions","chapters"):
        p=root/d
        if p.exists(): paths.extend(sorted(p.rglob("*.md")))
    return paths

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--chapter")
    a=ap.parse_args(); root=Path(a.root).resolve(); files=collect(root); claims={}; issues=[]
    for p in files:
        text=p.read_text(encoding="utf-8",errors="ignore")
        for kind,rx in CANON_PATTERNS.items():
            for m in rx.finditer(text):
                key=(kind,m.group(1)); val=m.group(2); ev={"file":str(p.relative_to(root)),"line":loc(text,m.start()),"text":m.group(0)[:160]}
                if key in claims and claims[key][0]!=val:
                    issues.append({"category":"fact","severity":"P1","claim":f"{key[1]} 的 {kind} 值可能衝突：{claims[key][0]} vs {val}","evidence_a":claims[key][1],"evidence_b":ev,"minimal_fix":"核對時間切片、計量語境與正典來源；若非同一事實，改寫以消歧。","confidence":"low"})
                else: claims[key]=(val,ev)
    chapter=root/"chapters"/f"{a.chapter}.md" if a.chapter else None
    if chapter and chapter.exists():
        text=chapter.read_text(encoding="utf-8",errors="ignore")
        for term in META:
            for m in re.finditer(re.escape(term),text):
                ev={"file":str(chapter.relative_to(root)),"line":loc(text,m.start()),"text":term}
                issues.append({"category":"style","severity":"P0","claim":"正文出現 meta/拒絕語句","evidence_a":ev,"evidence_b":ev,"minimal_fix":"刪除正文外說明並恢復小說敘事。","confidence":"high"})
    out={"schema":"minis.deep-consistency.v1","scope":{"chapter":a.chapter,"files":len(files)},"result":"FAIL" if any(i["severity"]=="P0" for i in issues) else ("WARN" if issues else "PASS"),"issues":issues,"limitations":["規則式數值抽取可能把不同語境混為同一事實；所有 P1 必須人工核對。","無法單獨推斷角色知識、隱含時間與世界規則語意。"]}
    d=root/"gates"; d.mkdir(exist_ok=True); dest=d/f"deep-{a.chapter or 'project'}.json"; dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(dest); print(out["result"])
if __name__=="__main__": main()
