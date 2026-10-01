from __future__ import annotations

"""Deterministic high-signal Narrative QA checks.

These checks intentionally stay conservative. They catch a small set of
high-confidence prose/contract bugs that previously slipped through when the
model did not self-report structured violations. They are not a full editor.
"""

import re
from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import sha256_json
from .repetition import detect_repetition, split_units

SCHEMA = "minis.narrative-qa-report.v1"

_SENT_SPLIT = re.compile(r"(?<=[。！？!?；;\n])")
_DEAD = re.compile(r"(已經死了|早已死了|當場死亡|斷氣了|沒了呼吸|停止呼吸|被殺死|死去了|死亡了)")
_RESUME = re.compile(r"(起身|站起來|坐起來|睜開眼|開口|說話|走去|走開|煮咖啡|繼續說|點了點頭|笑了)")
_EXPLAIN = re.compile(r"(因為|原來|其實|卻是|原來是|復生|復活|假裝|裝死|假死|沒死|並未死|沒有死|醒來|蘇醒|被救)")
_POV_1 = re.compile(r"(?<![A-Za-z])(我|我們|我的|我們的)(?![A-Za-z])")
_POV_2 = re.compile(r"(?<![A-Za-z])(你|你們|你的|你們的)(?![A-Za-z])")
_POV_3 = re.compile(r"(?<![A-Za-z])(他|她|它|他們|她們|它們|其)(?![A-Za-z])")
_SUMMARY = re.compile(r"(他們談了很多|之後發生了很多事|關係因此改變|事情也往前推進|一段時間後|總而言之|簡單來說|就這樣)")
_CLICHE = re.compile(r"(命運的齒輪|時間彷彿靜止|空氣彷彿凝固|不禁感嘆|一切都將不再一樣|淚水奪眶而出|心中五味雜陳|仿佛被雷擊中|宛如一盆冷水)")
_DIALOGUE = re.compile(r"[「\"“]([^」\"”]{4,80})[」\"”]")
_SAID = re.compile(r"([^\s「」\"“”]{1,12})(?:說|道|問|答|回)[：:]?\s*[「\"“]")


def _sentences(text: str) -> list[str]:
    parts = []
    for chunk in re.split(r"\n+", str(text or "")):
        chunk = chunk.strip()
        if not chunk:
            continue
        pieces = [x.strip() for x in _SENT_SPLIT.split(chunk) if x and x.strip()]
        parts.extend(pieces or [chunk])
    return parts


def _span(text: str, needle: str) -> dict[str, Any] | None:
    idx = text.find(needle)
    if idx < 0:
        return None
    return {"start": idx, "end": idx + len(needle), "quote": needle[:180]}


def _finding(code: str, severity: str, claim: str, *, confidence: str = "high",
             evidence: list[Any] | None = None, span: dict[str, Any] | None = None,
             repair: str | None = None, blocks_commit: bool | None = None) -> dict[str, Any]:
    return normalize_finding({
        "layer": "NARRATIVE_QA",
        "code": code,
        "severity": severity,
        "confidence": confidence,
        "claim": claim,
        "evidence": evidence or [],
        "span": span,
        "minimal_fix": repair,
        "blocks_commit": True if blocks_commit is None and severity == "P0" and confidence == "high" else bool(blocks_commit),
        "author_overridable": severity != "P0",
    })


def detect_unexplained_death_resume(text: str) -> list[dict[str, Any]]:
    sents = _sentences(text)
    out = []
    for i, sent in enumerate(sents):
        if not _DEAD.search(sent):
            continue
        window = sents[i:i + 3]
        joined = "".join(window)
        if _RESUME.search(joined) and not _EXPLAIN.search(joined):
            quote = "".join(window)[:180]
            out.append(_finding(
                "UNEXPLAINED_DEATH_RESUME", "P0",
                "正文出現死亡／斷氣後，隨即恢復行動，且同一視窗未提供假死、復活或誤判解釋",
                evidence=[{"window": window}],
                span=_span(text, quote) or {"quote": quote},
                repair="補上可觀察解釋，或刪除未授權的復行動作，或把超自然／醫療例外寫入正典後再描寫",
            ))
            break
    return out


def detect_pov_drift(text: str) -> list[dict[str, Any]]:
    sents = _sentences(text)
    if len(sents) < 2:
        return []
    flags = []
    for sent in sents:
        present = []
        if _POV_1.search(sent):
            present.append("1")
        if _POV_2.search(sent):
            present.append("2")
        if _POV_3.search(sent) and not re.search(r"^[「\"“].*[」\"”]$", sent.strip()):
            # third-person mentions are common; only count as focal if sentence starts with them or has cognition verbs
            if re.search(r"^(他|她|他們|她們)", sent.strip()) or re.search(r"(心想|覺得|知道|看見自己|意識到)", sent):
                present.append("3")
        flags.append(set(present))
    used = set().union(*flags) if flags else set()
    # Drift: first person narration plus second-person address and third-person self-cognition nearby.
    joined = "\n".join(sents)
    if {"1", "2", "3"}.issubset(used) or (
        "1" in used and "2" in used and re.search(r"(他|她)看見自己", joined)
    ):
        quote = joined[:180]
        return [_finding(
            "POV_DRIFT", "P1",
            "同一短段混用第一／第二／第三人稱焦點，疑似 POV 漂移或視角越權",
            confidence="high",
            evidence=[{"personas": sorted(used), "sentences": sents[:6]}],
            span=_span(text, sents[0]) or {"quote": quote},
            repair="統一場景焦點人物與人稱；必要時切段並標明視角轉換",
            blocks_commit=False,
        )]
    # Local adjacent sentence person flip with cognition claim
    for a, b in zip(sents, sents[1:]):
        if _POV_1.search(a) and re.search(r"(他|她)看見自己|你知道", b):
            return [_finding(
                "POV_DRIFT", "P1",
                "相鄰句從第一人稱跳到他人自我觀察或第二人稱全知，疑似 POV 漂移",
                evidence=[{"a": a, "b": b}],
                span=_span(text, a),
                repair="保留單一焦點；不要同時寫『我』的行動與『他看見自己／你知道』的全知",
                blocks_commit=False,
            )]
    return []


def detect_flat_character_voice(text: str) -> list[dict[str, Any]]:
    # Look for two speakers uttering highly similar declarative templates.
    pairs = []
    for m in re.finditer(r"([^\n「」\"“”]{1,12})(?:說|道)[：:]?\s*[「\"“]([^」\"”]{6,80})[」\"”]", text):
        pairs.append((m.group(1).strip(), m.group(2).strip(), m.start()))
    if len(pairs) < 2:
        return []
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            a_name, a_line, a_pos = pairs[i]
            b_name, b_line, b_pos = pairs[j]
            if a_name == b_name:
                continue
            # Same syntactic frame: 我認為我們應該X
            na = re.sub(r"[，。！？、\s]", "", a_line)
            nb = re.sub(r"[，。！？、\s]", "", b_line)
            if not na or not nb:
                continue
            same_frame = (
                na.startswith("我認為我們應該") and nb.startswith("我認為我們應該")
            ) or (
                len(na) >= 8 and len(nb) >= 8 and na[:6] == nb[:6] and abs(len(na) - len(nb)) <= 4
            )
            if same_frame:
                return [_finding(
                    "FLAT_CHARACTER_VOICE", "P1",
                    f"角色「{a_name}」與「{b_name}」使用高度同構台詞，聲音可替換",
                    confidence="high",
                    evidence=[{"a": {"name": a_name, "line": a_line}, "b": {"name": b_name, "line": b_line}}],
                    span={"start": a_pos, "end": b_pos + len(b_line), "quote": f"{a_name}:{a_line} / {b_name}:{b_line}"},
                    repair="讓用詞、節奏、回避、目標與資訊差拉開；避免同模板對白",
                    blocks_commit=False,
                )]
    return []


def detect_summary_only_scene(text: str) -> list[dict[str, Any]]:
    body = str(text or "").strip()
    if not body:
        return []
    sents = _sentences(body)
    if not sents:
        return []
    summary_hits = [s for s in sents if _SUMMARY.search(s)]
    has_dialogue = bool(_DIALOGUE.search(body))
    has_concrete = bool(re.search(r"(走|門|手|聲|光|味道|坐下|站|看|聽|握|推|拉|笑|哭|沉默)", body))
    # Short abstract paragraph with summary templates and almost no scene work.
    if summary_hits and not has_dialogue and (len(body) < 120 or len(summary_hits) >= max(1, len(sents) // 2)) and not has_concrete:
        quote = summary_hits[0]
        return [_finding(
            "SUMMARY_ONLY_SCENE", "P1",
            "段落以抽象摘要推進情節／關係，缺少可演的場景行為與對話",
            confidence="high",
            evidence=[{"summary_sentences": summary_hits, "chars": len(body)}],
            span=_span(body, quote),
            repair="改寫成至少一個有目標、阻力與可觀察行為的場景節拍，或明確標成過場摘要",
            blocks_commit=False,
        )]
    if summary_hits and len(body) < 80 and not has_dialogue:
        return [_finding(
            "SUMMARY_ONLY_SCENE", "P1",
            "極短摘要替代場景，讀者看不到事件如何發生",
            evidence=[{"text": body}],
            span=_span(body, body[:80]),
            repair="補上具體動作、對話或感官細節，或接受為非場景過場並降低戲劇宣稱",
            blocks_commit=False,
        )]
    return []


def detect_stock_cliche(text: str) -> list[dict[str, Any]]:
    hits = []
    for m in _CLICHE.finditer(str(text or "")):
        hits.append(m.group(0))
    if not hits:
        return []
    # One cliché is a warning; stacked clichés are stronger editorial smell.
    severity = "P2" if len(hits) == 1 else "P1"
    return [_finding(
        "STOCK_CLICHE", severity,
        "正文出現高頻陳腔／說明式金句，可能取代具體場景壓力",
        confidence="medium" if len(hits) == 1 else "high",
        evidence=[{"hits": hits[:8]}],
        span=_span(text, hits[0]),
        repair="用角色特定知覺、代價或行為代替現成金句；若是角色口癖需建立聲音依據",
        blocks_commit=False,
    )]


def detect_meta_leak(text: str) -> list[dict[str, Any]]:
    patterns = [
        r"作為AI", r"身為AI", r"我不能繼續", r"根據你的要求", r"以下是本章", r"這個場景的目的",
        r"\[(?:TODO|TBD|INSERT|META)\]", r"task_hash",
    ]
    for pat in patterns:
        m = re.search(pat, str(text or ""), re.I)
        if m:
            return [_finding(
                "META_LEAK", "P0",
                "正文洩漏 meta／寫作過程／模型任務痕跡",
                evidence=[{"match": m.group(0)}],
                span={"start": m.start(), "end": m.end(), "quote": m.group(0)},
                repair="刪除正文外說明，恢復故事敘事",
            )]
    return []


def inspect_prose(text: str, *, include_repetition: bool = True) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    findings.extend(detect_meta_leak(text))
    findings.extend(detect_unexplained_death_resume(text))
    findings.extend(detect_pov_drift(text))
    findings.extend(detect_flat_character_voice(text))
    findings.extend(detect_summary_only_scene(text))
    findings.extend(detect_stock_cliche(text))
    if include_repetition:
        rep = detect_repetition(text)
        for item in rep.get("findings") or []:
            sev = item.get("severity") or "WARN"
            severity = "P0" if sev == "P0" else ("P1" if sev == "P1" else "P2")
            findings.append(_finding(
                str(item.get("code") or "REPETITION"),
                severity,
                "generated prose contains repeated content",
                confidence="high" if severity == "P0" else "medium",
                evidence=[item.get("evidence")],
                repair="刪除 decoder loop 或無功能重複",
                blocks_commit=severity == "P0",
            ))
    authority = build_authority_report(
        findings=findings,
        source="narrative_qa.inspect_prose",
        subject={"kind": "prose", "chars": len(str(text or "")), "units": len(split_units(text))},
    )
    status = "FAIL" if any(f.get("severity") == "P0" for f in findings) else ("WARN" if findings else "PASS")
    report = {
        "schema": SCHEMA,
        "status": status,
        "finding_count": len(findings),
        "findings": findings,
        "authority": authority,
        "may_commit": authority["commit"]["may_commit"],
    }
    report["report_hash"] = sha256_json({k: v for k, v in report.items() if k != "report_hash"})
    return report


def validate_generated_output_qa(output: dict[str, Any], state: dict[str, Any] | None = None) -> dict[str, Any]:
    """Narrative QA layer for model envelopes. Does not replace canon gates."""
    text = output.get("text", "") if isinstance(output, dict) else ""
    report = inspect_prose(text if isinstance(text, str) else "")
    # Structured self-reports remain authoritative for knowledge/agency; QA only adds prose layer.
    report["state_hash"] = (state or {}).get("state_hash")
    return report
