#!/usr/bin/env python3
"""Create a persistent long-form novel project without overwriting existing work."""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def clean_slug(value: str) -> str:
    value = value.strip().lower().replace(" ", "-")
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-.")
    if not value or value in {".", ".."}:
        raise ValueError("slug must contain ASCII letters or numbers")
    return value


def write_new(path: Path, content: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a long-form novel project")
    parser.add_argument("--title", required=True)
    parser.add_argument("--slug", required=True, help="ASCII project folder name")
    parser.add_argument("--root", default=os.environ.get("NOVEL_PROJECTS_ROOT", "~/.novel-os/novels"))
    args = parser.parse_args()

    slug = clean_slug(args.slug)
    root = Path(args.root).expanduser().resolve()
    project = root / slug
    if project.exists():
        raise SystemExit(f"Project already exists; no files changed: {project}")

    skill_dir = Path(__file__).resolve().parent.parent
    project.mkdir(parents=True)
    for name in ("characters", "locations", "factions", "chapters", "summaries", "research", "volumes", "chapter-plans", "scenes", "context-packs", "gates", "reviews", "snapshots", "benchmarks", "behavior-calibration"):
        (project / name).mkdir()

    try:
        shutil.copyfile(skill_dir / "story-bible-template.md", project / "story-bible.md")
        shutil.copyfile(skill_dir / "behavior-models-template.md", project / "behavior-models.md")
        behavior_tool = skill_dir.parent / "human-behavior-personality-consultant" / "scripts" / "behavior_calibration.py"
        if behavior_tool.exists():
            import subprocess
            subprocess.run([sys.executable, str(behavior_tool), "init", "--root", str(project)], check=True, capture_output=True, text=True)
        else:
            raise FileNotFoundError(f"missing behavior calibration runtime: {behavior_tool}")
        world_skill = skill_dir.parent / "novel-worldbuilding-architect"
        world_bible_template = world_skill / "world-bible-template.md"
        world_rules_template = world_skill / "world-rules-template.md"
        if world_bible_template.exists():
            shutil.copyfile(world_bible_template, project / "world-bible.md")
        else:
            write_new(project / "world-bible.md", "# World Bible\n\n- 核心世界前提：\n- [LOCKED] 規則：\n")
        if world_rules_template.exists():
            shutil.copyfile(world_rules_template, project / "world-rules.md")
        else:
            write_new(project / "world-rules.md", "# World Rules\n\n| ID | 規則 | 成本／限制 | 狀態 |\n|---|---|---|---|\n")
        write_new(project / "knowledge-matrix.md", "# Knowledge Matrix\n\n| ID | [TRUTH] | [OFFICIAL] | [BELIEF]／[RUMOR] | [KNOWN:character] | 證據／途徑 |\n|---|---|---|---|---|---|\n")
        style_template = skill_dir.parent / "novel-style-craft-director" / "style-contract-template.md"
        if style_template.exists():
            shutil.copyfile(style_template, project / "style-sheet.md")
        else:
            write_new(project / "style-sheet.md", "# Style Sheet\n\n- 主引擎：\n- 敘事鏡頭：\n- 語言質地：\n- 成人內容契約（若適用）：\n")
        sections = {
            "current-state.md": "# Current State｜當前狀態\n\n- 最後定稿章節：\n- 故事日期／時刻：\n- 當前地點：\n- 上章不可逆變化：\n- 下一章直接壓力：\n\n## 世界觀／公共狀態（依 world-rules 與 knowledge-matrix）\n- 本章相關世界規則：\n- 地點／基礎設施狀態：\n- 派系權力／策略：\n- 資源／物流：\n- 科技／魔法可用性與成本：\n- [TRUTH]／[OFFICIAL]／[BELIEF]／[RUMOR]／[KNOWN] 變化：\n- 公共事件與待發生二階後果：\n\n## 人物狀態\n| 人物 | 位置 | 身體／傷勢 | 情緒／壓力 | 目標 | 持有物 | 下一步意圖 |\n|---|---|---|---|---|---|---|\n\n## 關係狀態\n| A ↔ B | 信任 | 權力 | 未說出口 | 最近變化 |\n|---|---|---|---|---|\n\n## 資訊與物件\n| ID | 內容／物件 | 知道者／持有人 | 誤信者／位置 | 最近變化 |\n|---|---|---|---|---|\n",
            "timeline.md": "# Timeline｜時間線\n\n| 日期／時間 | 章節 | 事件 | 地點 | 參與者 | 所需時長 | 連續性註記 |\n|---|---|---|---|---|---|---|\n",
            "plot-threads.md": "# Plot Threads｜情節、伏筆與走向預測\n\n| ID | 線索／承諾 | 首次埋設 | 最近推進 | 狀態 | 最晚再出現 | 預計回收 |\n|---|---|---|---|---|---|---|\n\n狀態：Seeded／Active／Complicated／Resolved／Dropped（需作者同意）\n\n## 候選走向與 Prediction Lock\n| 預測 ID／節點 | A 方向／信心／心理等級 | B 方向／信心／心理等級 | C 方向／信心／心理等級 | 表示法 | 世界＋行為校準 | 成立／推翻條件 | 作者選擇／狀態 |\n|---|---|---|---|---|---|---|---|\n\n> 先校準世界可行性，再建立不可覆寫 Prediction Lock。預設使用序位（較可能／可行／低機率但成立）或寬區間；只有同角色相似情境至少 5 筆、已解決預測至少 10 筆且有校準紀錄時，才可使用合計 100% 的精細百分比。作者選擇不等於預測命中。權威 lock／resolution 在 `behavior-calibration/*.jsonl`。\n\n## 預測變動\n| Prediction ID／版本 | 原表示 | 新表示 | 新證據／變動原因 | Supersedes | 更新章節／時間 |\n|---|---|---|---|---|---|\n",
            "chapter-index.md": "# Chapter Index｜章節索引\n\n| 章 | 日期／地點 | 視角 | 場景目標 | 主要轉折 | 結尾狀態 | 摘要檔 | 正典狀態 |\n|---|---|---|---|---|---|---|---|\n",
            "decisions.md": "# Decisions｜作者決策紀錄\n\n| 日期 | 決策 | 覆寫了什麼 | 理由 | 影響檔案／章節 | 狀態 |\n|---|---|---|---|---|---|\n",
        }
        write_new(project / "project-brief.md", f"# {args.title}\n\n- 專案代號：`{slug}`\n- 狀態：[DRAFT]\n- 建立時間：{datetime.now().astimezone().isoformat(timespec='seconds')}\n- 核心前提：\n- 本次目標：\n- [LOCKED] 設定：\n")
        templates = skill_dir / "templates"
        for source, target in (("reader-ledger.md", "reader-ledger.md"), ("workflow-state.json", "workflow-state.json"), ("entity-registry.json", "entity-registry.json")):
            template = templates / source
            if template.exists():
                shutil.copyfile(template, project / target)
        (project / "volumes" / "README.md").write_text("# 卷計畫\n\n以 `templates/volume-plan.md` 建立 `volume-001.md` 等檔案。\n", encoding="utf-8")
        (project / "chapter-plans" / "README.md").write_text("# 章節計畫\n\n以 `templates/chapter-plan.md` 建立穩定章號檔案。\n", encoding="utf-8")
        (project / "scenes" / "README.md").write_text("# 場景卡\n\n以 `templates/scene-card.md` 建立 `scene-001-01.md` 等可持久化場景單位。\n", encoding="utf-8")
        for filename, content in sections.items():
            write_new(project / filename, content)
        graph_script = skill_dir.parent / "knowledge-relationship-graph" / "scripts" / "relationship_graph.py"
        if graph_script.exists():
            import subprocess
            subprocess.run(
                [sys.executable, str(graph_script), "init", "--root", str(project), "--title", f"{args.title} 關係圖譜"],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            (project / "graphify-out").mkdir()
            write_new(project / "graphify-out" / "graph.json", json.dumps({"directed": True, "multigraph": True, "graph": {"schema": "minis.relationship-graph.v1", "title": f"{args.title} 關係圖譜"}, "nodes": [], "links": [], "hyperedges": []}, ensure_ascii=False, indent=2) + "\n")
        # Long-form and interactive modes share the same deterministic event
        # kernel. Markdown ledgers remain human-readable projections, not a
        # second silent source of truth.
        judge_scripts = skill_dir.parent / "immersive-interactive-fiction" / "scripts"
        if judge_scripts.exists():
            sys.path.insert(0, str(judge_scripts))
            from novel_judge.longform import initialize_longform_production
            initialize_longform_production(str(project), slug, provenance={"initializer": "init_novel_project.py"})
        manifest = {
            "schema": "minis.long-form-novel.v2.0",
            "title": args.title,
            "slug": slug,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "canon_through": None,
            "latest_draft": None,
        }
        project_path = project / "project.json"
        if project_path.exists():
            existing = json.loads(project_path.read_text(encoding="utf-8"))
            authority_pointer = existing.get("production_authority")
            manifest.update({"production_authority": authority_pointer} if authority_pointer else {})
            project_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            write_new(project_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    except Exception:
        shutil.rmtree(project, ignore_errors=True)
        raise

    print(json.dumps({"ok": True, "project": str(project)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
