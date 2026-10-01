from __future__ import annotations

"""Editorial diagnosis layer: advisory only, never canon truth.

This is a scaffold for whole-manuscript / multi-scene developmental review.
It produces evidence-oriented tickets and a strengths-first memo outline.
It does not block commit by itself.
"""

import re
from pathlib import Path
from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json
from .narrative_qa import inspect_prose
from .scene_goals import inspect_scene_goals

SCHEMA = "minis.editorial-diagnosis.v1"
TICKET_SCHEMA = "minis.narrative-bug-ticket.v1"

_SCENE_SPLIT = re.compile(r"\n\s*---\s*\n|\n#{1,3}\s+")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def make_ticket(
    *,
    code: str,
    claim: str,
    severity: str = "P2",
    confidence: str = "medium",
    layer: str = "EDITORIAL_DIAGNOSIS",
    locus: dict[str, Any] | None = None,
    evidence: list[Any] | None = None,
    expected_contract: str | None = None,
    reproduction: str | None = None,
    reader_impact: str | None = None,
    minimal_repair: str | None = None,
    duplicate_of: str | None = None,
) -> dict[str, Any]:
    ticket = {
        "schema": TICKET_SCHEMA,
        "ticket_id": sha256_json({"code": code, "claim": claim, "locus": locus or {}})[:16],
        "code": code,
        "layer": layer,
        "severity": severity,
        "confidence": confidence,
        "claim": claim,
        "locus": locus or {},
        "evidence": evidence or [],
        "expected_contract": expected_contract,
        "reproduction": reproduction,
        "reader_impact": reader_impact,
        "minimal_repair": minimal_repair,
        "duplicate_of": duplicate_of,
        "status": "open",
        "blocks_commit": False,
        "author_overridable": True,
        "created_at": now_iso(),
    }
    return ticket


def diagnose_text(text: str, *, source: str = "text", scene_id: str | None = None) -> dict[str, Any]:
    qa = inspect_prose(text)
    goals = inspect_scene_goals(text, scene_id=scene_id)
    tickets: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for item in goals.get("findings") or []:
        findings.append(normalize_finding(item))
        tickets.append(make_ticket(
            code=str(item.get("code")), claim=str(item.get("claim")), severity=str(item.get("severity")),
            confidence=str(item.get("confidence") or "medium"), layer=str(item.get("layer") or "EDITORIAL_DIAGNOSIS"),
            locus={"source": source, "scene_id": scene_id}, evidence=list(item.get("evidence") or []),
            expected_contract="scene has goal, opposition and exit-state change",
            minimal_repair=item.get("minimal_fix"),
        ))
    for item in qa.get("findings") or []:
        # Promote prose QA into tickets; keep severity, but editorial layer remains advisory unless already P0 QA.
        layer = "NARRATIVE_QA" if item.get("severity") == "P0" else "EDITORIAL_DIAGNOSIS"
        if item.get("code") in {"UNEXPLAINED_DEATH_RESUME", "META_LEAK", "REPETITION_LOOP"}:
            layer = "NARRATIVE_QA"
        finding = normalize_finding({**item, "layer": layer, "blocks_commit": layer == "NARRATIVE_QA" and item.get("severity") == "P0"})
        findings.append(finding)
        tickets.append(make_ticket(
            code=str(finding.get("code")),
            claim=str(finding.get("claim")),
            severity=str(finding.get("severity")),
            confidence=str(finding.get("confidence")),
            layer=layer,
            locus={"source": source, "scene_id": scene_id, "span": finding.get("span")},
            evidence=list(finding.get("evidence") or []),
            expected_contract="scene remains continuous, voiced, and free of unearned state breaks",
            reproduction=f"read {source}" + (f" scene {scene_id}" if scene_id else ""),
            reader_impact="may break immersion, trust, or clarity",
            minimal_repair=finding.get("minimal_fix"),
        ))

    # Lightweight craft signals: no dialogue + many abstract relation claims.
    if len(text.strip()) >= 400 and "「" not in text and '"' not in text and text.count("。") >= 6:
        if re.search(r"(關係|感情|信任|成長|命運|意義)", text) and not re.search(r"(走|門|手|聲|看|說|坐|站)", text):
            claim = "較長段落缺少對白與具體動作，卻大量談論關係／意義，可能是摘要壓過場景"
            tickets.append(make_ticket(
                code="SCENE_FUNCTION_WEAK",
                claim=claim,
                severity="P2",
                confidence="low",
                locus={"source": source, "scene_id": scene_id},
                expected_contract="scene should pursue a concrete objective under pressure",
                reader_impact="reader may skim or fail to feel change",
                minimal_repair="為場景設定目標、阻力與至少一個可觀察選擇",
            ))
            findings.append(normalize_finding({
                "layer": "EDITORIAL_DIAGNOSIS", "code": "SCENE_FUNCTION_WEAK", "severity": "P2",
                "confidence": "low", "claim": claim, "blocks_commit": False,
            }))

    authority = build_authority_report(findings=findings, source="editorial_diagnosis", subject={"source": source, "scene_id": scene_id})
    strengths = []
    if "「" in text or '"' in text:
        strengths.append("含對白，具備場面潛力")
    if re.search(r"(因為|可是|然而|如果不|只好)", text):
        strengths.append("出現因果或權衡語言，可能已有選擇壓力")
    if not tickets:
        strengths.append("未觸發高信心敘事 QA 規則；仍需人類整稿閱讀")

    report = {
        "schema": SCHEMA,
        "status": authority["layers"]["NARRATIVE_QA"]["status"] if authority["layers"]["NARRATIVE_QA"]["finding_count"] else (
            "WARN" if tickets else "PASS"
        ),
        "source": source,
        "scene_id": scene_id,
        "strengths": strengths,
        "tickets": tickets,
        "authority": authority,
        "editorial_letter_outline": {
            "what_work_is_trying_to_be": "UNKNOWN — author/genre contract required",
            "strengths": strengths,
            "highest_leverage_problems": [t["claim"] for t in tickets[:5]],
            "revision_roadmap": [
                "先處理 NARRATIVE_QA P0/P1",
                "再處理場景目標／代價／轉折",
                "再統一角色聲音與資訊權限",
                "最後才做句級人味與潤飾",
            ],
            "claims": {
                "is_developmental_edit": False,
                "is_complete_manuscript_read": False,
                "blocks_commit": False,
            },
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def diagnose_chapter_file(path: str | Path, *, chapter: str | None = None) -> dict[str, Any]:
    p = Path(path)
    text = _read_text(p)
    report = diagnose_text(text, source=str(p), scene_id=chapter or p.stem)
    report["chapter"] = chapter or p.stem
    return report


def diagnose_manuscript(root: str | Path, *, limit: int = 50) -> dict[str, Any]:
    """Whole-project advisory diagnosis over chapter files.

    This is still not a substitute for a human cold read. It aggregates local
    tickets and produces a revision board skeleton.
    """
    base = Path(root)
    chapters_dir = base / "chapters"
    files = sorted(chapters_dir.glob("*.md")) if chapters_dir.is_dir() else []
    if not files:
        # interactive scenes fallback
        scenes = base / "interactive" / "scenes"
        files = sorted(scenes.glob("T*.md")) if scenes.is_dir() else []
    files = files[: max(1, int(limit))]
    chapter_reports = []
    all_tickets: list[dict[str, Any]] = []
    for f in files:
        r = diagnose_chapter_file(f, chapter=f.stem)
        chapter_reports.append({"chapter": f.stem, "path": str(f), "status": r["status"], "ticket_count": len(r["tickets"]), "report_hash": r["report_hash"]})
        all_tickets.extend(r["tickets"])

    # Simple absence / concentration metrics
    by_code: dict[str, int] = {}
    for t in all_tickets:
        by_code[t["code"]] = by_code.get(t["code"], 0) + 1
    findings = [
        normalize_finding({
            "layer": "EDITORIAL_DIAGNOSIS",
            "code": code,
            "severity": "P2",
            "confidence": "low",
            "claim": f"全稿聚合出現 {count} 次 {code}",
            "blocks_commit": False,
        })
        for code, count in sorted(by_code.items(), key=lambda x: (-x[1], x[0]))[:12]
    ]
    authority = build_authority_report(findings=findings + [
        # carry any narrative QA tickets upward
        normalize_finding({
            "layer": t.get("layer") or "EDITORIAL_DIAGNOSIS",
            "code": t.get("code"),
            "severity": t.get("severity"),
            "confidence": t.get("confidence"),
            "claim": t.get("claim"),
            "blocks_commit": t.get("layer") == "NARRATIVE_QA" and t.get("severity") == "P0",
            "evidence": t.get("evidence"),
        })
        for t in all_tickets if t.get("layer") == "NARRATIVE_QA"
    ], source="editorial_diagnosis.manuscript", subject={"root": str(base), "chapter_count": len(files)})

    board = {
        "schema": "minis.revision-board.v1",
        "phases": [
            {"id": "cold_read", "status": "pending", "goal": "完整冷讀並記錄停讀／困惑／情緒點"},
            {"id": "structure", "status": "pending", "goal": "情節／支線／場景功能圖"},
            {"id": "character_arcs", "status": "pending", "goal": "人物與關係弧檢查"},
            {"id": "continuity", "status": "pending", "goal": "時間／物件／知識／承諾"},
            {"id": "prose_voice", "status": "pending", "goal": "聲音、節奏、感官與人味"},
            {"id": "second_read", "status": "pending", "goal": "修訂後二次驗收"},
        ],
        "open_tickets": len(all_tickets),
        "top_codes": by_code,
    }
    report = {
        "schema": "minis.manuscript-diagnosis.v1",
        "root": str(base),
        "chapter_count": len(files),
        "chapters": chapter_reports,
        "ticket_count": len(all_tickets),
        "tickets": all_tickets[:500],
        "revision_board": board,
        "authority": authority,
        "limitations": [
            "not a full human developmental edit",
            "does not score reader enjoyment",
            "does not replace explicit author decisions",
        ],
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report
