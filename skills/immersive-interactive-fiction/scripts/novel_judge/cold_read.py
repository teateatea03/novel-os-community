from __future__ import annotations

"""Cold-read / beta-reader workflow artifacts.

These capture *human* reader experience. They never become canon and never
alone block commit. AUTHOR_DECISION remains separate.

Machine Narrative QA is a prescan only. Practitioner sources (Jane Friedman /
Barbara Linn Probst survey of 92 authors; Andrew Noakes / The Niche Reader;
Dabble beta-feedback practice) agree: beta readers are proxies for future
readers, not editors, not copyeditors, and not a vote the author must obey.
"""

from pathlib import Path
from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import now_iso, sha256_json
from .editorial_diagnosis import make_ticket
from .scene_review import review_scene_text

SCHEMA = "minis.cold-read-report.v1"
SESSION_SCHEMA = "minis.beta-read-session.v1"
CONSENSUS_SCHEMA = "minis.reader-consensus.v1"

# Core questions: always ask. Kept short for volunteer readers.
CORE_QUESTIONS = [
    "整體印象如何？",
    "最喜歡什麼？",
    "有沒有不喜歡的地方？是什麼？",
    "開頭有沒有抓住你？",
    "哪裡開始失趣、略讀或停讀？",
    "故事好不好跟？哪裡困惑？困惑是好奇還是失去方向？",
    "有沒有覺得不合理、難以置信、或不一致？",
    "主角或其他角色有沒有讓你在意？誰最記得、誰最模糊？",
    "結局滿不滿意？",
]

# Optional / craft. Do not dump these as required homework on volunteers.
OPTIONAL_QUESTIONS = [
    "轉折是否 earned？",
    "哪裡感到作者在強推？",
    "類型預期有沒有被滿足、被耍、或被破壞？",
]

PROMPT_QUESTIONS = list(CORE_QUESTIONS)

HUMAN_ROLES = {"beta_reader", "cold_read_human", "alpha_reader", "critique_partner"}


def build_beta_questionnaire(*, genre: str | None = None) -> dict[str, Any]:
    return {
        "schema": "minis.beta-questionnaire.v1",
        "genre": genre,
        "questions": list(CORE_QUESTIONS),
        "optional_questions": list(OPTIONAL_QUESTIONS),
        "instructions": [
            "以讀者經驗回答，不做免費 copyedit／校對",
            "標出具體章節／段落，不要只給總分",
            "區分『看不懂』與『不喜歡』",
            "不必當編輯：不用評三幕、市場或『該怎麼改』",
            "義工讀者以核心題為主；選答可略過",
            "機器預掃不是 beta，也不是作者必須接受的票",
        ],
        "created_at": now_iso(),
    }


def record_reader_reaction(
    *,
    reader_id: str,
    source: str,
    reactions: list[dict[str, Any]],
    overall: dict[str, Any] | None = None,
    role: str = "beta_reader",
) -> dict[str, Any]:
    """Record a *human* reader. Machine prescan must not use this path."""
    if role not in HUMAN_ROLES:
        role = "beta_reader"
    findings = []
    tickets = []
    for item in reactions or []:
        if str(item.get("origin") or "") == "deterministic_pre_scan":
            continue
        severity = str(item.get("severity") or "P2").upper()
        if severity not in {"P0", "P1", "P2"}:
            severity = "P2"
        claim = str(item.get("claim") or item.get("note") or "reader reaction")
        finding = normalize_finding({
            "layer": "READER_RESPONSE",
            "code": str(item.get("code") or "READER_REACTION"),
            "severity": severity if severity != "P0" else "P1",
            "confidence": str(item.get("confidence") or "medium"),
            "claim": claim,
            "blocks_commit": False,
            "details": {"locus": item.get("locus"), "emotion": item.get("emotion"), "origin": "human"},
        })
        findings.append(finding)
        tickets.append(make_ticket(
            code=finding["code"],
            claim=claim,
            severity=finding["severity"],
            confidence=finding["confidence"],
            layer="READER_RESPONSE",
            locus={"source": source, **dict(item.get("locus") or {})},
            evidence=[item],
            reader_impact=item.get("emotion") or item.get("impact"),
            minimal_repair=item.get("suggested_repair"),
        ))
    authority = build_authority_report(
        findings=findings, source="cold_read.human",
        subject={"reader_id": reader_id, "source": source, "role": role},
    )
    report = {
        "schema": SCHEMA,
        "role": role,
        "reader_id": reader_id,
        "source": source,
        "questionnaire": build_beta_questionnaire(),
        "reactions": [x for x in (reactions or []) if str(x.get("origin") or "") != "deterministic_pre_scan"],
        "overall": overall or {},
        "tickets": tickets,
        "authority": authority,
        "claims": {
            "is_objective_quality": False,
            "is_author_decision": False,
            "is_human_reader": True,
            "is_beta_reader": role == "beta_reader",
            "is_literary_score": False,
            "blocks_commit": False,
            "author_must_accept": False,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def cold_read_text(text: str, *, source: str = "text", reader_id: str = "host-cold-read") -> dict[str, Any]:
    """Host packet: machine prescan + empty human slots. Prescan is not a reader."""
    review = review_scene_text(text, source=source, scene_id=source)
    authority = build_authority_report(
        findings=[],
        source="cold_read.host_packet",
        subject={"reader_id": reader_id, "source": source},
        extras={"prescan_hash": review.get("report_hash")},
    )
    report = {
        "schema": SCHEMA,
        "role": "cold_read_prescan",
        "reader_id": reader_id,
        "source": source,
        "questionnaire": build_beta_questionnaire(),
        "reactions": [],
        "tickets": [],
        "authority": authority,
        "prescan": review,
        "human_slots": {
            "status": "pending",
            "questions": list(CORE_QUESTIONS),
            "optional_questions": list(OPTIONAL_QUESTIONS),
            "note": "fill with real human cold-read answers; machine prescan is not a beta reader",
        },
        "claims": {
            "is_objective_quality": False,
            "is_author_decision": False,
            "is_human_reader": False,
            "is_beta_reader": False,
            "is_literary_score": False,
            "machine_prescan_only": True,
            "blocks_commit": False,
            "author_must_accept": False,
        },
        "created_at": now_iso(),
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def summarize_reader_consensus(reports: list[dict[str, Any]] | None) -> dict[str, Any]:
    """One reader is anecdote; two+ independent humans on the same code/locus is a candidate.

    Never becomes AUTHOR_DECISION. Author may reject consensus.
    """
    human = []
    for report in reports or []:
        if not isinstance(report, dict):
            continue
        claims = report.get("claims") if isinstance(report.get("claims"), dict) else {}
        if claims.get("is_human_reader") or report.get("role") in HUMAN_ROLES:
            human.append(report)
    buckets: dict[str, dict[str, Any]] = {}
    for report in human:
        rid = str(report.get("reader_id") or "unknown")
        items = list(report.get("tickets") or []) + list(report.get("reactions") or [])
        for item in items:
            if not isinstance(item, dict):
                continue
            code = str(item.get("code") or "READER_REACTION")
            locus = item.get("locus") if isinstance(item.get("locus"), dict) else {}
            loc = str(locus.get("chapter") or locus.get("scene_id") or locus.get("source") or "")
            key = f"{code}|{loc}"
            row = buckets.setdefault(key, {"code": code, "locus": loc, "readers": set(), "claims": []})
            row["readers"].add(rid)
            claim = str(item.get("claim") or item.get("note") or "")
            if claim:
                row["claims"].append(claim)
    rows = []
    for row in buckets.values():
        n = len(row["readers"])
        rows.append({
            "code": row["code"],
            "locus": row["locus"],
            "independent_reader_count": n,
            "readers": sorted(row["readers"]),
            "status": "consensus_candidate" if n >= 2 else "anecdote",
            "claims": row["claims"][:8],
        })
    rows.sort(key=lambda x: (-x["independent_reader_count"], x["code"], x["locus"]))
    out = {
        "schema": CONSENSUS_SCHEMA,
        "human_report_count": len(human),
        "anecdote_count": sum(1 for r in rows if r["status"] == "anecdote"),
        "consensus_candidate_count": sum(1 for r in rows if r["status"] == "consensus_candidate"),
        "rows": rows,
        "claims": {
            "is_author_decision": False,
            "author_must_accept_all": False,
            "one_reader_is_anecdote": True,
            "consensus_is_not_canon": True,
        },
        "created_at": now_iso(),
    }
    out["report_hash"] = sha256_json({k: v for k, v in out.items() if k != "report_hash"})
    return out


def open_beta_session(project_root: str | Path, *, session_id: str, readers: list[str] | None = None) -> dict[str, Any]:
    root = Path(project_root)
    out_dir = root / "reviews" / "beta" / session_id
    out_dir.mkdir(parents=True, exist_ok=True)
    questionnaire = build_beta_questionnaire()
    session = {
        "schema": SESSION_SCHEMA,
        "session_id": session_id,
        "project_root": str(root),
        "readers": list(readers or []),
        "questionnaire": questionnaire,
        "status": "open",
        "path": str(out_dir),
        "practice": {
            "beta_is_not_editor": True,
            "machine_prescan_is_not_beta": True,
            "author_must_not_accept_all": True,
        },
        "created_at": now_iso(),
    }
    session["session_hash"] = sha256_json({k: v for k, v in session.items() if k != "session_hash"})
    import json
    (out_dir / "session.json").write_text(json.dumps(session, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Beta Reader Questionnaire",
        "",
        "以讀者經驗回答。不必當編輯、不必校對、不必說該怎麼改。",
        "標出章節／段落。區分「看不懂」與「不喜歡」。義工以核心題為主。",
        "",
        "## 核心題",
        "",
    ]
    lines.extend(f"- {q}" for q in CORE_QUESTIONS)
    lines.extend(["", "## 選答", ""])
    lines.extend(f"- {q}" for q in OPTIONAL_QUESTIONS)
    lines.append("")
    (out_dir / "questionnaire.md").write_text("\n".join(lines), encoding="utf-8")
    return session
