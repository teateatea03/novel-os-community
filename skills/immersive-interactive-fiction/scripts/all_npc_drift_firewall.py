#!/usr/bin/env python3
"""All-NPC drift firewall: validates final scene artifacts before commit.

This is deliberately conservative: regex catches only deterministic shapes;
semantic judgments must be supplied as a hash-bound review artifact.
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

from dialogue_quotes import parse_dialogue_quotes
from speaker_registry import registry_errors

P0 = {"QUOTATION_PARSE_FAILURE", "INVALID_SPEAKER_REGISTRY", "UNREGISTERED_NPC", "MISSING_CONTRACT", "MISSING_MANIFEST", "SCENE_HASH_MISMATCH", "SPEAKER_COVERAGE", "SEMANTIC_REVIEW_MISSING", "SEMANTIC_REVIEW_MISMATCH", "SEMANTIC_DRIFT"}
SENTENCE = re.compile(r"[。！？!?]+")
TECH = re.compile(r"轉播|收音|組件|訊號|接入|硬體|設備|權限|風險|偵測|狀態")
REPORT = re.compile(r"不代表|目前|對方|原因|因此|狀態|組件|轉播鏈|現場")
HOST = re.compile(r"先把.*講完|先讓.*自己|不要替.*|輪到.*|現在最需要|你.*先")
THERAPIST = re.compile(r"以前.*現在|不是要.*帳|自己說|界線|同意|你想要|雙方|關係")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))

def quote_data(scene: Path) -> tuple[list[str], list[str]]:
    text = scene.read_text(encoding="utf-8")
    body = text.split("## 正文", 1)[-1]
    quotes, errors = parse_dialogue_quotes(body)
    return [quote for _, quote in quotes], errors

def sentences(text: str) -> int:
    return len([x for x in SENTENCE.split(text) if x.strip()]) or (1 if text.strip() else 0)

def issue(code, severity, actor, text, message):
    return {"code": code, "severity": severity, "actor": actor, "text": text, "message": message}

def taxonomy(actor: str, text: str, contract: dict) -> list[dict]:
    out = []
    n = sentences(text)
    forbid = set(contract.get("forbidden_dialogue_acts", []))
    max_s = int(contract.get("max_sentences", 99))
    max_i = int(contract.get("max_information_units", max_s))
    tech_report = bool(TECH.search(text) and REPORT.search(text) and n >= 2)
    if tech_report and "analyst_report" in forbid:
        out.append(issue("ANALYST_REPORT_VOICE", "P0", actor, text, "technical fact chain functions as a report"))
    if HOST.search(text) and "host_direction" in forbid:
        out.append(issue("HOST_DIRECTOR_VOICE", "P0", actor, text, "assigns scene priority or another actor's next step"))
    if THERAPIST.search(text) and "relationship_mediation" in forbid:
        out.append(issue("THERAPIST_RELATIONSHIP_MEDIATOR", "P0", actor, text, "packages history, intent, or agreement for both parties"))
    if n > max_s:
        out.append(issue("OVER_RESPONSE", "P1", actor, text, f"{n} sentences exceeds contract max_sentences={max_s}"))
    # Information units are clauses separated by causal/report markers.
    units = 1 + len(re.findall(r"[；，]|但是|不代表|目前|對方|因此|至於", text))
    if units > max_i * 3:
        out.append(issue("OVER_RESPONSE", "P1", actor, text, f"dense clause count {units} exceeds information budget"))
    return out

def validate(root: Path, scene: Path, manifest_p: Path, review_p: Path | None, require_review: bool) -> dict:
    registry = load(root / "interactive" / "npc-registry.json")
    manifest = load(manifest_p)
    findings = [issue("INVALID_SPEAKER_REGISTRY", "P0", None, "", message)
                for message in registry_errors(registry)]
    if manifest.get("scene_sha256") != sha(scene):
        findings.append(issue("SCENE_HASH_MISMATCH", "P0", None, "", "manifest does not bind to final scene bytes"))
    actors = registry.get("actors", {}) if isinstance(registry, dict) else {}
    if not isinstance(actors, dict):
        actors = {}
    player_id = registry.get("player_id") if isinstance(registry, dict) else None
    entries = manifest.get("dialogues", [])
    declared = []
    for e in entries:
        actor, text = e.get("speaker"), e.get("quote", "")
        declared.append(text)
        if isinstance(player_id, str) and player_id.strip() and actor == player_id:
            continue
        if actor not in actors:
            findings.append(issue("UNREGISTERED_NPC", "P0", actor, text, "speaker absent from dynamic registry")); continue
        config = actors[actor]
        contract_path = config.get("contract") if isinstance(config, dict) else None
        if not isinstance(contract_path, str) or not contract_path:
            findings.append(issue("MISSING_CONTRACT", "P0", actor, text, "registered NPC has no contract path")); continue
        cp = root / "interactive" / contract_path
        if not cp.is_file():
            findings.append(issue("MISSING_CONTRACT", "P0", actor, text, str(cp))); continue
        contract = load(cp)
        if not e.get("manifest"):
            findings.append(issue("MISSING_MANIFEST", "P0", actor, text, "dialogue lacks per-turn manifest")); continue
        act = e["manifest"].get("dialogue_act")
        if act not in contract.get("allowed_dialogue_acts", []):
            findings.append(issue("FORBIDDEN_ACT_EXECUTION", "P0", actor, text, f"act {act!r} not allowed"))
        findings.extend(taxonomy(actor, text, contract))
    actual, quote_errors = quote_data(scene)
    findings.extend(issue("QUOTATION_PARSE_FAILURE", "P0", None, "", message) for message in quote_errors)
    missing = list((Counter(actual) - Counter(declared)).elements())
    extra = list((Counter(declared) - Counter(actual)).elements())
    if missing or extra:
        findings.append(issue("SPEAKER_COVERAGE", "P0", None, "", f"unbound_quotes={missing}; declared_not_in_scene={extra}"))
    if require_review:
        if not review_p or not review_p.exists():
            findings.append(issue("SEMANTIC_REVIEW_MISSING", "P0", None, "", "hash-bound semantic review required"))
        else:
            review = load(review_p)
            if review.get("scene_sha256") != sha(scene):
                findings.append(issue("SEMANTIC_REVIEW_MISMATCH", "P0", None, "", "semantic review targets different scene bytes"))
            elif review.get("verdict") != "pass":
                findings.append(issue("SEMANTIC_DRIFT", "P0", None, "", "semantic review did not pass"))
    severity = "P0" if any(x["severity"] == "P0" for x in findings) else ("P1" if findings else "OK")
    return {"ok": not findings, "severity": severity, "scene": str(scene), "scene_sha256": sha(scene), "findings": findings, "checked_dialogues": len(entries), "actual_quotes": len(actual)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--scene", required=True)
    ap.add_argument("--manifest", required=True); ap.add_argument("--semantic-review")
    ap.add_argument("--allow-no-semantic-review", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(); r = validate(Path(a.root), Path(a.scene), Path(a.manifest), Path(a.semantic_review) if a.semantic_review else None, not a.allow_no_semantic_review)
    raw = json.dumps(r, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).write_text(raw + "\n", encoding="utf-8")
    print(raw)
    raise SystemExit(0 if r["ok"] else 2)
if __name__ == "__main__": main()
