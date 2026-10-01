from __future__ import annotations

from typing import Any

from .authority_layers import build_authority_report, normalize_finding
from .canonical import canonical_json, sha256_json
from .delta import validate_delta_paths
from .errors import GATE_FAILED, PLAYER_SOVEREIGNTY
from .narrative_qa import inspect_prose
from .repetition import detect_repetition


def _facts_for(state: dict[str, Any], audience: str, actor_id: str | None) -> set[str]:
    truth = state.get("knowledge", {}).get("truth", {})
    result = {k for k, v in truth.items() if isinstance(v, dict) and v.get("visibility") == "public"}
    k = state.get("knowledge", {})
    if audience == "player" and actor_id:
        result.update(k.get("player", {}).get(actor_id, []))
    elif audience == "npc" and actor_id:
        result.update(k.get("npcs", {}).get(actor_id, []))
    elif audience == "reader":
        result.update(k.get("reader", []))
    return set(result)


def validate_generated_output(output: dict[str, Any], state: dict[str, Any], *, audience: str = "reader", actor_id: str | None = None) -> dict[str, Any]:
    """Validate a model envelope.

    Canon/agency/knowledge issues remain hard errors. High-confidence Narrative
    QA P0 findings also fail the gate. Editorial smells stay warnings and never
    alone prove literary quality.
    """
    if not isinstance(output, dict):
        return {"status": "fail", "errors": [{"code": GATE_FAILED, "message": "model output must be an object"}], "warnings": [], "authority": None}
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    layered: list[dict[str, Any]] = []

    if not isinstance(output.get("text", ""), str):
        errors.append({"code": GATE_FAILED, "message": "text must be a string"})
        layered.append(normalize_finding({
            "layer": "CANON_INTEGRITY", "code": GATE_FAILED, "severity": "P0", "confidence": "high",
            "claim": "text must be a string", "blocks_commit": True, "author_overridable": False,
        }))
    else:
        # Keep legacy repetition path for compatibility, then run broader QA.
        repetition = detect_repetition(output.get("text", ""))
        if repetition["status"] == "fail":
            for x in repetition["findings"]:
                if x["severity"] == "P0":
                    errors.append({"code": x["code"], "message": "generated prose contains repeated content", "details": x["evidence"]})
        elif repetition["status"] == "warn":
            warnings.append({"code": "REPETITION_WARNING", "message": "generated prose may contain repeated content", "details": repetition["findings"]})
        qa = inspect_prose(output.get("text", ""), include_repetition=False)
        for item in qa.get("findings") or []:
            layered.append(item)
            if item.get("severity") == "P0" and item.get("confidence") == "high":
                errors.append({
                    "code": item.get("code"),
                    "message": item.get("claim"),
                    "details": {"evidence": item.get("evidence"), "span": item.get("span"), "layer": item.get("layer")},
                })
            else:
                warnings.append({
                    "code": item.get("code"),
                    "message": item.get("claim"),
                    "details": {"evidence": item.get("evidence"), "span": item.get("span"), "layer": item.get("layer"), "severity": item.get("severity")},
                })

    if output.get("player_actions"):
        errors.append({"code": PLAYER_SOVEREIGNTY, "message": "model output claims an action for the player", "details": {"actions": output["player_actions"]}})
        layered.append(normalize_finding({
            "layer": "CANON_INTEGRITY", "code": PLAYER_SOVEREIGNTY, "severity": "P0", "confidence": "high",
            "claim": "model output claims an action for the player", "blocks_commit": True, "author_overridable": False,
            "details": {"actions": output["player_actions"]},
        }))
    if output.get("player_commitments"):
        errors.append({"code": PLAYER_SOVEREIGNTY, "message": "model output creates player commitments"})
        layered.append(normalize_finding({
            "layer": "CANON_INTEGRITY", "code": PLAYER_SOVEREIGNTY, "severity": "P0", "confidence": "high",
            "claim": "model output creates player commitments", "blocks_commit": True, "author_overridable": False,
        }))
    delta = output.get("state_delta")
    if delta:
        try:
            validate_delta_paths(delta, source="model")
        except Exception as exc:
            errors.append({"code": getattr(exc, "code", GATE_FAILED), "message": str(exc)})
            layered.append(normalize_finding({
                "layer": "CANON_INTEGRITY", "code": getattr(exc, "code", GATE_FAILED), "severity": "P0", "confidence": "high",
                "claim": str(exc), "blocks_commit": True, "author_overridable": False,
            }))
    visible = _facts_for(state, audience, actor_id)
    for fact in output.get("claimed_facts", []) or []:
        if fact not in visible:
            errors.append({"code": "KNOWLEDGE_LEAK", "message": "claimed fact is outside audience knowledge", "details": {"fact": fact}})
            layered.append(normalize_finding({
                "layer": "CANON_INTEGRITY", "code": "KNOWLEDGE_LEAK", "severity": "P0", "confidence": "high",
                "claim": "claimed fact is outside audience knowledge", "blocks_commit": True, "author_overridable": False,
                "details": {"fact": fact},
            }))
    if output.get("unstructured_state_claims"):
        warnings.append({"code": "UNVERIFIED_STATE_CLAIM", "message": "unstructured claims are not state changes and require author review"})
        layered.append(normalize_finding({
            "layer": "NARRATIVE_QA", "code": "UNVERIFIED_STATE_CLAIM", "severity": "P2", "confidence": "medium",
            "claim": "unstructured claims are not state changes and require author review", "blocks_commit": False,
        }))

    authority = build_authority_report(
        findings=layered,
        source="narrative_gate",
        subject={"audience": audience, "actor_id": actor_id, "state_hash": state.get("state_hash")},
    )
    status = "fail" if errors else "pass"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "audience": audience,
        "context_fingerprint": sha256_json(sorted(visible)),
        "authority": authority,
        "may_commit": authority["commit"]["may_commit"] and status == "pass",
    }


def require_narrative_gate(output: dict[str, Any], state: dict[str, Any], *, audience: str = "reader", actor_id: str | None = None) -> dict[str, Any]:
    report = validate_generated_output(output, state, audience=audience, actor_id=actor_id)
    if report["status"] != "pass":
        raise ValueError(canonical_json(report))
    return report
