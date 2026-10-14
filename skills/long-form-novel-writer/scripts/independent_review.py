#!/usr/bin/env python3
import argparse, json, math, re, subprocess, tempfile, uuid
from datetime import datetime
from pathlib import Path

from context_evidence import assess_context, context_source_spans
from review_evidence import (SCHEMA as REVIEW_SCHEMA, capture_source, check_binding, consolidate_binding,
                             make_report, recheck_report, source_binding, source_path)

ROLES={
"continuity":"只找可定位的時間、事實、知識、動機、POV、世界規則矛盾。不要評論個人喜好。",
"beta-reader":"以讀者角度描述理解、困惑、期待、情緒與承諾是否得到公平回應。不要改寫全文。",
"style-editor":"依風格契約找敘事距離、角色聲音、節奏、意象與重複漂移。不要把個人文風強加給文本。"
}
SCHEMA='''只輸出 JSON：{"summary":"...","issues":[{"category":"time|fact|knowledge|motivation|pov|world|reader|style","severity":"P0|P1|P2","claim":"...","evidence_a":{"file":"...","line":1,"quote":"..."},"evidence_b":{"file":"...","line":1,"quote":"..."},"minimal_fix":"...","confidence":0.0}],"questions":[]}。沒有雙證據的矛盾放 questions，不可判 P0。'''

def extract_json(s):
    s=re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.S)
    def reject_constant(value):
        raise ValueError("non-finite JSON number: " + value)
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("non-finite JSON number")
        return number
    try:
        return json.loads(s, parse_constant=reject_constant, parse_float=finite_float)
    except json.JSONDecodeError:
        a=s.find("{"); b=s.rfind("}")
        if a>=0 and b>a:
            return json.loads(s[a:b+1], parse_constant=reject_constant, parse_float=finite_float)
        raise


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--chapter")
    ap.add_argument("--role", choices=ROLES, default="continuity")
    ap.add_argument("--model")
    ap.add_argument("--context-pack")
    ap.add_argument("--max-tokens", type=int, default=2500)
    ap.add_argument("--check-review", help="Read-only source freshness check; never applies revisions")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    if a.check_review:
        try:
            report = json.loads(Path(a.check_review).read_text(encoding="utf-8"))
            check = recheck_report(root, report)
        except (OSError, ValueError) as error:
            check = {"status": "unverified", "problems": [str(error)]}
        print(json.dumps(check, ensure_ascii=True))
        raise SystemExit(0 if check["status"] == "current" else 2)
    if not a.chapter or not a.model:
        ap.error("--chapter and --model are required unless --check-review is used")
    if "/" in a.chapter or "\\" in a.chapter or a.chapter in {".", ".."}:
        ap.error("--chapter must be a single chapter identifier")
    draft_file = f"chapters/{a.chapter}.md"
    try:
        draft = capture_source(root, draft_file, normalize=True)
        chapter = source_path(root, draft_file)
        cp = Path(a.context_pack) if a.context_pack else root / "context-packs" / f"{a.chapter}.md"
        cp_name = cp.absolute().relative_to(root).as_posix()
        cp = source_path(root, cp_name)
        sources = {draft_file: draft}
        style = ""
        if (root / "style-sheet.md").exists():
            sources["style-sheet.md"] = capture_source(root, "style-sheet.md", 12000, normalize=True)
            style = sources["style-sheet.md"]["text"]
        context = "（無 context pack）"
        bound_inputs = []
        for path in (cp, cp.with_suffix(".json")):
            if path.exists():
                item = capture_source(root, path.relative_to(root).as_posix(), 0)
                bound_inputs.extend(source_binding({item["file"]: item}))
                if path == cp:
                    context = item["text"]
        receipt = assess_context(root, cp, context, min(len(context), 30000))
        if receipt["status"] == "verified":
            context_sources = context_source_spans(root, receipt)
            # Full chapter/style snapshots already reflect their actual prompt prefix.
            for name, source in context_sources.items():
                if name not in sources:
                    sources[name] = source
                else:
                    if sources[name]["sha256"] != source["sha256"]:
                        raise ValueError("source changed during preparation: " + name)
                    sources[name]["ranges"].extend(source["ranges"])
            for item in receipt["sources"]:
                bound_inputs.append({"file": item["file"], "sha256": item["source_sha256"], "ranges": []})
    except (OSError, UnicodeError, ValueError) as error:
        raise SystemExit(f"review inputs unavailable: {error}")
    prompt = f"你是獨立小說審稿者。角色：{a.role}。{ROLES[a.role]}\n{SCHEMA}\n以下引用可能不完整，正典以來源檔為準。行號以來源檔 1 起算；引用必須是唯一且連續的原文。\n\n# STYLE file=style-sheet.md\n{style[:12000]}\n# CONTEXT\n{context[:30000]}\n# CHAPTER file={draft_file}\n{draft['text']}"
    reviews = source_path(root, "reviews")
    reviews.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    base = reviews / f"{a.chapter}-{a.role}-{stamp}-{uuid.uuid4().hex[:8]}"
    raw = Path(str(base) + ".raw.txt")
    binding = consolidate_binding(source_binding(sources) + bound_inputs)
    def save_error(status, error, payload=None):
        result = {"schema": REVIEW_SCHEMA, "role": a.role, "model": a.model,
                  "status": status, "error": error, "context_receipt": receipt,
                  "source_binding": binding,
                  "raw_file": str(raw.relative_to(root)) if raw.exists() else None}
        if payload is not None:
            result["machine_suggestion"] = payload
        fail = Path(str(base) + ".error.json")
        fail.write_text(json.dumps(result, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print(fail)
        return fail
    if receipt["status"] in {"stale", "invalid"}:
        save_error(receipt["status"], "context pack requires rebuilding before review")
        raise SystemExit(2)
    before = check_binding(root, binding)
    if before["status"] != "current":
        save_error("stale", "review inputs changed during prompt preparation")
        raise SystemExit(2)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False, newline="\n") as f:
        f.write(prompt)
        prompt_path = f.name
    cmd = ["minis-model-use", "run", "--model", a.model, "--prompt-file", prompt_path,
           "--max-tokens", str(a.max_tokens), "--temperature", "0", "--output", str(raw)]
    try:
        r = subprocess.run(cmd, text=True, capture_output=True)
    except OSError as error:
        save_error("unavailable", str(error))
        raise SystemExit(2)
    finally:
        Path(prompt_path).unlink(missing_ok=True)
    if r.returncode:
        save_error("unavailable", (r.stderr or r.stdout).strip())
        raise SystemExit(2)
    try:
        data = extract_json(raw.read_text(encoding="utf-8"))
        # JSON permits escaped lone surrogates; UTF-8 source/report files do not.
        json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (OSError, ValueError) as error:
        save_error("unverified", f"review JSON invalid: {error}")
        raise SystemExit(2)
    try:
        report = make_report(data, sources, draft_file, a.role, a.model,
                             str(raw.relative_to(root)), prompt, receipt)
    except (ValueError, TypeError, OverflowError) as error:
        save_error("unverified", f"review validation failed: {error}")
        raise SystemExit(2)
    report["source_binding"] = binding
    report["source_text_normalization"] = "splitlines_join_lf; source hashes bind original bytes"
    report["prompt_sections"] = {
        "chapter": {"characters": len(draft["text"]), "included_characters": len(draft["text"]), "omitted_characters": 0},
        "style": {"characters": len(style), "included_characters": min(len(style), 12000), "omitted_characters": max(0, len(style) - 12000)},
        "context": {"characters": len(context), "included_characters": min(len(context), 30000), "omitted_characters": max(0, len(context) - 30000)}}
    report["freshness"] = check_binding(root, binding)
    if report["freshness"]["status"] != "current":
        for finding in report["validation"]["findings"]:
            finding["status"] = "stale"
    dest = Path(str(base) + ".json")
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(dest)
    if report["validation"]["status"] == "unverified" or report["freshness"]["status"] != "current":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
