#!/usr/bin/env python3
import argparse, json, re, subprocess, tempfile
from datetime import datetime
from pathlib import Path

ROLES={
"continuity":"只找可定位的時間、事實、知識、動機、POV、世界規則矛盾。不要評論個人喜好。",
"beta-reader":"以讀者角度描述理解、困惑、期待、情緒與承諾是否得到公平回應。不要改寫全文。",
"style-editor":"依風格契約找敘事距離、角色聲音、節奏、意象與重複漂移。不要把個人文風強加給文本。"
}
SCHEMA='''只輸出 JSON：{"summary":"...","issues":[{"category":"time|fact|knowledge|motivation|pov|world|reader|style","severity":"P0|P1|P2","claim":"...","evidence_a":{"file":"...","line":1,"quote":"..."},"evidence_b":{"file":"...","line":1,"quote":"..."},"minimal_fix":"...","confidence":0.0}],"questions":[]}。沒有雙證據的矛盾放 questions，不可判 P0。'''

def extract_json(s):
    s=re.sub(r"^```(?:json)?\s*|\s*```$","",s.strip(),flags=re.S)
    try:return json.loads(s)
    except Exception:
        a=s.find("{"); b=s.rfind("}")
        if a>=0 and b>a:return json.loads(s[a:b+1])
        raise

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--chapter",required=True); ap.add_argument("--role",choices=ROLES,default="continuity"); ap.add_argument("--model",required=True); ap.add_argument("--context-pack"); ap.add_argument("--max-tokens",type=int,default=2500)
    a=ap.parse_args(); root=Path(a.root).resolve(); chapter=root/"chapters"/f"{a.chapter}.md"
    if not chapter.exists(): raise SystemExit("chapter not found")
    cp=Path(a.context_pack) if a.context_pack else root/"context-packs"/f"{a.chapter}.md"
    context=cp.read_text(encoding="utf-8",errors="ignore") if cp.exists() else "（無 context pack）"
    style=(root/"style-sheet.md").read_text(encoding="utf-8",errors="ignore") if (root/"style-sheet.md").exists() else ""
    prompt=f"你是獨立小說審稿者。角色：{a.role}。{ROLES[a.role]}\n{SCHEMA}\n以下引用可能不完整，正典以來源檔為準。\n\n# STYLE\n{style[:12000]}\n# CONTEXT\n{context[:30000]}\n# CHAPTER file={chapter.relative_to(root)}\n{chapter.read_text(encoding='utf-8',errors='ignore')}"
    reviews=root/"reviews"; reviews.mkdir(exist_ok=True); stamp=datetime.now().strftime("%Y%m%d-%H%M%S"); base=reviews/f"{a.chapter}-{a.role}-{stamp}"
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",suffix=".txt",delete=False) as f: f.write(prompt); prompt_path=f.name
    raw=base.with_suffix(".raw.txt")
    cmd=["minis-model-use","run","--model",a.model,"--prompt-file",prompt_path,"--max-tokens",str(a.max_tokens),"--temperature","0","--output",str(raw)]
    r=subprocess.run(cmd,text=True,capture_output=True); Path(prompt_path).unlink(missing_ok=True)
    if r.returncode:
        error=(r.stderr or r.stdout).strip()
        fail=base.with_suffix(".error.json")
        fail.write_text(json.dumps({"schema":"minis.novel-review.v1","role":a.role,"model":a.model,"status":"unavailable","error":error,"raw_file":str(raw.relative_to(root)) if raw.exists() else None},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(fail); raise SystemExit(2)
    try: data=extract_json(raw.read_text(encoding="utf-8",errors="ignore"))
    except Exception as e: raise SystemExit(f"review JSON invalid; raw kept at {raw}: {e}")
    data.update({"schema":"minis.novel-review.v1","role":a.role,"model":a.model,"status":"machine_suggestion","raw_file":str(raw.relative_to(root))})
    dest=base.with_suffix(".json"); dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(dest)
if __name__=="__main__": main()
