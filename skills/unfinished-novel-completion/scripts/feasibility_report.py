#!/usr/bin/env python3
"""Generate a conservative feasibility assessment for unfinished-novel projects."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def table_rows(path: Path) -> list[list[str]]:
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if cells[0] in {"ID", "分支 ID", "問題", "線索／承諾", "主張", "日期", "實體", "面向"}:
            continue
        rows.append(cells)
    return rows


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def classify_intent(root: Path, source_count: int, intent_rows: int, evidence_text: str) -> tuple[str, str]:
    direct = sum(evidence_text.count(x) for x in ("AUTHOR-NOTE", "AUTHOR-STATEMENT", "EDITORIAL"))
    if intent_rows >= 2 and direct >= 2 and source_count >= 1:
        return "HIGH", "有作者材料或編輯／遺產資料，且已有多條意圖假說；仍需保留版本衝突。"
    if intent_rows >= 1 and direct >= 1:
        return "MEDIUM", "有部分作者方向證據，但來源數量、時期或正文相容性仍不足以鎖定唯一原意。"
    if intent_rows >= 1 or "AUTHOR-" in evidence_text:
        return "LOW", "存在意圖線索，但缺少足夠直接來源或獨立交叉支持。"
    return "UNKNOWN", "目前沒有足夠的作者意圖證據；不要把文本推演寫成原作者意圖。"


def classify_textual(root: Path, canon_rows: int, thread_rows: int, chapter_count: int) -> tuple[str, str]:
    if canon_rows >= 5 and thread_rows >= 3 and chapter_count >= 1:
        return "HIGH", "正文狀態、未完成線索與既有章節足以支撐正典約束續作。"
    if canon_rows >= 1 or chapter_count >= 1:
        return "MEDIUM", "已有部分文本或章節材料；需要補齊狀態、伏筆與版本整理。"
    return "LOW", "尚無可供正典約束的文本資料，先做來源匯入與研究。"


def classify_creative(root: Path, canon_rows: int, chapter_count: int) -> tuple[str, str]:
    if canon_rows >= 2 or chapter_count >= 1:
        return "HIGH", "即使原作者意圖不可知，已有材料可以設計清楚標示的非官方替代補完。"
    if root.is_dir():
        return "MEDIUM", "可建立創作性補完骨架，但目前缺少足夠原作材料來維持角色與主題連續性。"
    return "LOW", "缺少作品材料。"


def main() -> int:
    ap = argparse.ArgumentParser(description="Assess unfinished-novel completion feasibility")
    ap.add_argument("--root", required=True)
    ap.add_argument("--output")
    ap.add_argument("--write", action="store_true", help="also replace the project feasibility-report.md")
    args = ap.parse_args()
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Project not found: {root}")

    try:
        state = json.loads(read(root / "completion-state.json") or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid completion-state.json: {exc}")
    try:
        manifest = json.loads(read(root / "source-manifest.json") or "{}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid source-manifest.json: {exc}")

    sources = manifest.get("sources", []) if isinstance(manifest, dict) else []
    source_types = Counter(str(x.get("type", "unknown")) for x in sources)
    source_count = len(sources)
    local_sources = sum(bool(x.get("source_path")) for x in sources)
    url_sources = sum(bool(x.get("source_url")) for x in sources)
    canon_rows = len(table_rows(root / "textual-canon.md"))
    intent_rows = len(table_rows(root / "author-intent-ledger.md"))
    evidence_rows = len(table_rows(root / "evidence-ledger.md"))
    hypothesis_rows = len(table_rows(root / "hypothesis-ledger.md"))
    thread_rows = len(table_rows(root / "unfinished-thread-ledger.md"))
    conflict_rows = len(table_rows(root / "version-conflicts.md"))
    chapter_count = len(list((root / "chapters").glob("chapter-*.md"))) if (root / "chapters").is_dir() else 0
    intent_level, intent_reason = classify_intent(root, source_count, intent_rows, read(root / "evidence-ledger.md") + read(root / "author-intent-ledger.md"))
    textual_level, textual_reason = classify_textual(root, canon_rows, thread_rows, chapter_count)
    creative_level, creative_reason = classify_creative(root, canon_rows, chapter_count)
    rights_status = state.get("rights_status", "unknown")
    purpose = state.get("purpose", "private-only")
    rights_level = "LOW" if rights_status in {"own-work", "licensed", "public-domain"} else "HIGH"
    rights_reason = "權利狀態已標示為可創作／發布前仍須核對範圍。" if rights_level == "LOW" else "權利未知或未授權；預設限私人研究，不能直接公開或商業發布。"

    report = {
        "schema": "minis.unfinished-feasibility.v1",
        "project": root.name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "completion_mode": state.get("completion_mode", "undecided"),
        "branch_id": state.get("branch_id"),
        "purpose": purpose,
        "rights_status": rights_status,
        "counts": {"sources": source_count, "local_sources": local_sources, "url_sources": url_sources,
                   "textual_canon_rows": canon_rows, "evidence_rows": evidence_rows, "author_intent_rows": intent_rows,
                   "hypothesis_rows": hypothesis_rows, "unfinished_thread_rows": thread_rows, "version_conflict_rows": conflict_rows,
                   "chapters": chapter_count},
        "source_types": dict(source_types),
        "assessments": {
            "intent_reconstruction": {"level": intent_level, "reason": intent_reason},
            "textual_continuation": {"level": textual_level, "reason": textual_reason},
            "creative_completion": {"level": creative_level, "reason": creative_reason},
            "rights_and_publication": {"level": rights_level, "reason": rights_reason},
        },
        "recommendation": (
            "先完成來源／正典／證據整理，再決定模式。"
            if state.get("completion_mode", "undecided") == "undecided" else
            "交給長篇技能前，確認 branch_id、補完 Gate 與權利邊界。"
        ),
    }
    md = ["# Feasibility Report｜補完可行性評估", "", f"- project: `{root.name}`", f"- generated_at: {report['generated_at']}", f"- completion_mode: `{report['completion_mode']}`", f"- branch_id: `{report.get('branch_id') or 'none'}`", "", "## 評估", "", "| 面向 | 等級 | 理由 |", "|---|---|---|"]
    for key, label in (("intent_reconstruction", "原作者意圖重建"), ("textual_continuation", "正典約束續作"), ("creative_completion", "創作性替代補完"), ("rights_and_publication", "權利／發布")):
        item = report["assessments"][key]
        md.append(f"| {label} | **{item['level']}** | {item['reason']} |")
    md += ["", "## 材料統計", "", "```json", json.dumps(report["counts"], ensure_ascii=False, indent=2), "```", "", f"> 建議：{report['recommendation']}", "", "> 本報告是條件式創作研究，不是原作者意圖鑑定、法律意見或成功率統計。"]
    output = Path(args.output).expanduser().resolve() if args.output else root / "research" / "feasibility-generated.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(md) + "\n", encoding="utf-8")
    if args.write:
        (root / "feasibility-report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "written_template": bool(args.write), **report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
