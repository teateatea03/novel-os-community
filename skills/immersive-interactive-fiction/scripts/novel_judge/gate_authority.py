from __future__ import annotations

"""Deterministic, state-bound Gate authorization for production commits."""

import re
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json, stable_id
from .errors import GATE_AUTHORIZATION_FAILED, GATE_ENVELOPE_INVALID, GATE_OVERRIDE_INVALID, JudgeError

GATE_ENVELOPE_SCHEMA = "minis.gate-envelope.v1"
GATE_RESULT_SCHEMA = "minis.gate-result.v1"
GATE_OVERRIDE_SCHEMA = "minis.gate-override.v1"
GATE_AUTHORIZATION_SCHEMA = "minis.gate-authorization.v1"
GATE_POLICY_VERSION = "gate-policy/1.0"

DEFAULT_REQUIRED_GATES = (
    "turn_contract", "reality", "scene_progression", "prose",
    "fact_agency", "interactive_agency", "blind_read",
)
DEFAULT_RUNNERS = {
    gate: {"id": f"novel-judge.{gate.replace('_', '-')}", "versions": ["1"]}
    for gate in DEFAULT_REQUIRED_GATES
}
NON_OVERRIDABLE_GATES = {"turn_contract", "reality", "fact_agency", "interactive_agency"}
VALID_VERDICTS = {"PASS", "WARN", "FAIL"}
VALID_SEVERITIES = {"OK", "P2", "P1", "P0"}


def default_gate_policy(required_gate_types: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    required = sorted(set(required_gate_types or DEFAULT_REQUIRED_GATES))
    runners = {}
    for gate in required:
        runners[gate] = DEFAULT_RUNNERS.get(gate, {"id": f"novel-judge.{gate.replace('_', '-')}", "versions": ["1"]})
    return {
        "schema": "minis.commit-gate-policy.v1",
        "version": GATE_POLICY_VERSION,
        "required_gate_types": required,
        "allowed_runners": runners,
        "non_overridable_gate_types": sorted(set(NON_OVERRIDABLE_GATES) & set(required)),
        "author_override_scope": "WARN_ONLY",
        "fail_is_overridable": False,
        "p0_is_overridable": False,
    }


def _hash_without(value: dict[str, Any], key: str) -> str:
    return sha256_json({k: v for k, v in value.items() if k != key})


def make_gate_envelope(*, gate_type: str, turn_id: str, scene_sha256: str,
                       source_state_hash: str, verdict: str = "PASS", severity: str = "OK",
                       findings: list[dict[str, Any]] | None = None,
                       runner_id: str | None = None, runner_version: str = "1",
                       policy_version: str = GATE_POLICY_VERSION,
                       details: dict[str, Any] | None = None,
                       artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "schema": GATE_RESULT_SCHEMA,
        "gate_type": str(gate_type),
        "turn_id": str(turn_id),
        "scene_sha256": str(scene_sha256),
        "source_state_hash": str(source_state_hash),
        "verdict": str(verdict).upper(),
        "severity": str(severity).upper(),
        "findings": list(findings or []),
        "details": dict(details or {}),
    }
    envelope = {
        "schema": GATE_ENVELOPE_SCHEMA,
        "policy_version": policy_version,
        "runner": {"id": runner_id or f"novel-judge.{gate_type.replace('_', '-')}", "version": str(runner_version)},
        "payload": payload,
        "payload_hash": sha256_json(payload),
        "artifact": artifact,
        "issued_at": now_iso(),
    }
    envelope["envelope_hash"] = _hash_without(envelope, "envelope_hash")
    return envelope


def make_trusted_gate_envelope(*, candidate_binding: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Emit a host-executor receipt for an already compiled candidate.

    Plain ``make_gate_envelope`` remains a fixture constructor; active
    production accepts only this receipt-bearing form.
    """
    envelope = make_gate_envelope(**kwargs)
    receipt_core = {"schema": "minis.gate-attestation.v1", "executor": "novel-judge.builtin-gate-executor",
                    "executor_version": "1", "gate_type": envelope["payload"]["gate_type"],
                    "payload_hash": envelope["payload_hash"], "candidate_binding": dict(candidate_binding)}
    receipt = dict(receipt_core); receipt["receipt_hash"] = sha256_json(receipt_core)
    envelope["attestation"] = receipt
    envelope["envelope_hash"] = _hash_without(envelope, "envelope_hash")
    return envelope
def make_author_override(*, envelope: dict[str, Any], author_id: str, reason: str,
                         finding_codes: list[str] | None = None) -> dict[str, Any]:
    payload = envelope.get("payload", {})
    codes = sorted(set(str(code) for code in (finding_codes or []) if str(code).strip()))
    value = {
        "schema": GATE_OVERRIDE_SCHEMA,
        "authority": "author",
        "author_id": str(author_id),
        "reason": str(reason),
        "scope": "gate_findings",
        "turn_id": payload.get("turn_id"),
        "scene_sha256": payload.get("scene_sha256"),
        "source_state_hash": payload.get("source_state_hash"),
        "gate_type": payload.get("gate_type"),
        "gate_envelope_hash": envelope.get("envelope_hash"),
        "finding_codes": codes,
        "issued_at": now_iso(),
    }
    value["override_id"] = stable_id(
        "gate-override", value["author_id"], value["gate_envelope_hash"],
        value["reason"], *codes,
    )
    value["override_hash"] = _hash_without(value, "override_hash")
    return value


def _invalid(code: str, message: str, **details: Any) -> JudgeError:
    return JudgeError(code, message, details=details)


def validate_gate_envelope(envelope: dict[str, Any], *, policy: dict[str, Any],
                           turn_id: str, scene_sha256: str, source_state_hash: str,
                           project_root: str | Path | None = None,
                           candidate_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(envelope, dict) or envelope.get("schema") != GATE_ENVELOPE_SCHEMA:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate envelope schema is invalid")
    required = {"policy_version", "runner", "payload", "payload_hash", "issued_at", "envelope_hash"}
    missing = sorted(required - set(envelope))
    if missing: raise _invalid(GATE_ENVELOPE_INVALID, "gate envelope missing fields", missing=missing)
    if envelope.get("policy_version") != policy.get("version"):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate policy version mismatch")
    if envelope.get("envelope_hash") != _hash_without(envelope, "envelope_hash"):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate envelope hash mismatch")
    payload = envelope.get("payload")
    if not isinstance(payload, dict) or payload.get("schema") != GATE_RESULT_SCHEMA:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate result payload schema is invalid")
    payload_required = {"gate_type", "turn_id", "scene_sha256", "source_state_hash", "verdict", "severity", "findings", "details"}
    payload_missing = sorted(payload_required - set(payload))
    if payload_missing: raise _invalid(GATE_ENVELOPE_INVALID, "gate payload missing fields", missing=payload_missing)
    if envelope.get("payload_hash") != sha256_json(payload):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate payload hash mismatch")
    gate_type = str(payload.get("gate_type"))
    if gate_type not in set(policy.get("required_gate_types", [])):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate type is not allowed by policy", gate_type=gate_type)
    runner = envelope.get("runner")
    expected_runner = policy.get("allowed_runners", {}).get(gate_type, {})
    if not isinstance(runner, dict) or runner.get("id") != expected_runner.get("id") or str(runner.get("version")) not in {str(x) for x in expected_runner.get("versions", [])}:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate runner is not authorized", gate_type=gate_type, runner=runner)
    if payload.get("turn_id") != turn_id:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate turn binding mismatch", gate_type=gate_type)
    if not re.fullmatch(r"[0-9a-f]{64}", str(scene_sha256)) or not re.fullmatch(r"sha256:[0-9a-f]{64}", str(source_state_hash)):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate authority binding hashes are malformed", gate_type=gate_type)
    if payload.get("scene_sha256") != scene_sha256:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate scene hash binding mismatch", gate_type=gate_type)
    if payload.get("source_state_hash") != source_state_hash:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate source state is stale", gate_type=gate_type)
    raw_verdict = payload.get("verdict"); raw_severity = payload.get("severity")
    if raw_verdict not in VALID_VERDICTS or raw_severity not in VALID_SEVERITIES:
        raise _invalid(GATE_ENVELOPE_INVALID, "gate verdict or severity must use canonical enum values", gate_type=gate_type)
    verdict = str(raw_verdict); severity = str(raw_severity)
    if not isinstance(payload.get("details"), dict):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate details must be an object", gate_type=gate_type)
    if not isinstance(payload.get("findings"), list) or not all(isinstance(x, dict) and str(x.get("code", "")).strip() for x in payload["findings"]):
        raise _invalid(GATE_ENVELOPE_INVALID, "gate findings must contain coded objects", gate_type=gate_type)
    if verdict == "PASS" and severity != "OK":
        raise _invalid(GATE_ENVELOPE_INVALID, "PASS gate must have OK severity", gate_type=gate_type)
    if verdict == "WARN" and severity not in {"P1", "P2"}:
        raise _invalid(GATE_ENVELOPE_INVALID, "WARN gate must have P1 or P2 severity", gate_type=gate_type)
    if severity == "P0" and verdict != "FAIL":
        raise _invalid(GATE_ENVELOPE_INVALID, "P0 gate must be FAIL", gate_type=gate_type)
    if candidate_binding is not None:
        attestation = envelope.get("attestation")
        if not isinstance(attestation, dict) or attestation.get("candidate_binding") != candidate_binding:
            raise _invalid(GATE_ENVELOPE_INVALID, "active Gate requires executor attestation")
        receipt_core = {k: attestation.get(k) for k in ("schema", "executor", "executor_version", "gate_type", "payload_hash", "candidate_binding")}
        if receipt_core.get("schema") != "minis.gate-attestation.v1" or receipt_core.get("executor") != "novel-judge.builtin-gate-executor" or attestation.get("receipt_hash") != sha256_json(receipt_core):
            raise _invalid(GATE_ENVELOPE_INVALID, "Gate executor attestation is invalid")
    artifact = envelope.get("artifact")
    if artifact is not None:
        if not isinstance(artifact, dict) or not artifact.get("path") or not artifact.get("sha256") or project_root is None:
            raise _invalid(GATE_ENVELOPE_INVALID, "gate artifact binding is invalid", gate_type=gate_type)
        path = (Path(project_root) / str(artifact["path"])).resolve(); root = Path(project_root).resolve()
        try: path.relative_to(root)
        except ValueError: raise _invalid(GATE_ENVELOPE_INVALID, "gate artifact escapes project root", gate_type=gate_type)
        if not path.is_file(): raise _invalid(GATE_ENVELOPE_INVALID, "gate artifact is missing", gate_type=gate_type)
        import hashlib
        if hashlib.sha256(path.read_bytes()).hexdigest() != artifact.get("sha256"):
            raise _invalid(GATE_ENVELOPE_INVALID, "gate artifact hash mismatch", gate_type=gate_type)
    return payload


def validate_author_override(override: dict[str, Any], *, envelope: dict[str, Any],
                             policy: dict[str, Any]) -> dict[str, Any]:
    payload = envelope["payload"]; gate_type = payload["gate_type"]
    if not isinstance(override, dict) or override.get("schema") != GATE_OVERRIDE_SCHEMA:
        raise _invalid(GATE_OVERRIDE_INVALID, "gate override schema is invalid", gate_type=gate_type)
    if override.get("override_hash") != _hash_without(override, "override_hash"):
        raise _invalid(GATE_OVERRIDE_INVALID, "gate override hash mismatch", gate_type=gate_type)
    if override.get("authority") != "author" or not str(override.get("author_id", "")).strip() or not str(override.get("reason", "")).strip():
        raise _invalid(GATE_OVERRIDE_INVALID, "override requires identified author and reason", gate_type=gate_type)
    if override.get("scope") != "gate_findings":
        raise _invalid(GATE_OVERRIDE_INVALID, "override scope must be gate_findings", gate_type=gate_type)
    for key in ("turn_id", "scene_sha256", "source_state_hash", "gate_type"):
        if override.get(key) != payload.get(key):
            raise _invalid(GATE_OVERRIDE_INVALID, "gate override binding mismatch", gate_type=gate_type, field=key)
    if override.get("gate_envelope_hash") != envelope.get("envelope_hash"):
        raise _invalid(GATE_OVERRIDE_INVALID, "gate override envelope binding mismatch", gate_type=gate_type)
    if payload.get("verdict") != "WARN" or payload.get("severity") not in {"P1", "P2"}:
        raise _invalid(GATE_OVERRIDE_INVALID, "only WARN/P1-P2 may be overridden", gate_type=gate_type)
    if gate_type in set(policy.get("non_overridable_gate_types", [])):
        raise _invalid(GATE_OVERRIDE_INVALID, "this gate type is non-overridable", gate_type=gate_type)
    finding_codes = {str(x.get("code")) for x in payload.get("findings", [])}
    requested = override.get("finding_codes")
    if not isinstance(requested, list) or not requested or len(requested) != len(set(requested)):
        raise _invalid(GATE_OVERRIDE_INVALID, "override must name a non-empty unique finding scope", gate_type=gate_type)
    if set(requested) != finding_codes:
        raise _invalid(GATE_OVERRIDE_INVALID, "override scope must name every current gate finding", gate_type=gate_type)
    expected_id = stable_id(
        "gate-override", str(override["author_id"]), str(override["gate_envelope_hash"]),
        str(override["reason"]), *sorted(set(requested)),
    )
    if override.get("override_id") != expected_id:
        raise _invalid(GATE_OVERRIDE_INVALID, "gate override id mismatch", gate_type=gate_type)
    return override


def evaluate_gate_bundle(envelopes: list[dict[str, Any]], *, overrides: list[dict[str, Any]] | None,
                         policy: dict[str, Any], turn_id: str, scene_sha256: str,
                         source_state_hash: str, project_root: str | Path | None = None,
                         candidate_binding: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(envelopes, list):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate bundle must be a list")
    by_type: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    for envelope in envelopes:
        payload = validate_gate_envelope(envelope, policy=policy, turn_id=turn_id,
                                         scene_sha256=scene_sha256, source_state_hash=source_state_hash,
                                         project_root=project_root)
        gate_type = payload["gate_type"]
        if gate_type in by_type:
            raise _invalid(GATE_AUTHORIZATION_FAILED, "duplicate gate type", gate_type=gate_type)
        by_type[gate_type] = (envelope, payload)
    required = set(policy.get("required_gate_types", [])); missing = sorted(required - set(by_type))
    if missing: raise _invalid(GATE_AUTHORIZATION_FAILED, "required gates are missing", missing=missing)
    override_by_gate: dict[str, dict[str, Any]] = {}
    for override in overrides or []:
        gate_type = str(override.get("gate_type", ""))
        if gate_type in override_by_gate: raise _invalid(GATE_OVERRIDE_INVALID, "duplicate override", gate_type=gate_type)
        if gate_type not in by_type: raise _invalid(GATE_OVERRIDE_INVALID, "override has no matching gate", gate_type=gate_type)
        validate_author_override(override, envelope=by_type[gate_type][0], policy=policy)
        override_by_gate[gate_type] = override
    blockers = []
    for gate_type, (_, payload) in by_type.items():
        verdict, severity = payload["verdict"], payload["severity"]
        if verdict == "FAIL" or severity == "P0":
            blockers.append({"gate_type": gate_type, "reason": "fail_or_p0", "verdict": verdict, "severity": severity})
        elif verdict == "WARN" and gate_type not in override_by_gate:
            blockers.append({"gate_type": gate_type, "reason": "warn_requires_author_override", "verdict": verdict, "severity": severity})
    if blockers: raise _invalid(GATE_AUTHORIZATION_FAILED, "gate bundle is not authorized", blockers=blockers)
    binding = dict(candidate_binding or {})
    binding_required = {"candidate_hash", "operations_hash", "actor_id", "action_type", "semantic_hash"}
    if binding and not binding_required.issubset(binding):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "candidate binding is incomplete", missing=sorted(binding_required-set(binding)))
    envelope_hashes = {gate: by_type[gate][0]["envelope_hash"] for gate in sorted(required)}
    override_hashes = {gate: override_by_gate[gate]["override_hash"] for gate in sorted(override_by_gate)}
    gate_evidence = []
    for gate in sorted(required):
        envelope, payload = by_type[gate]
        artifact = envelope.get("artifact")
        override = override_by_gate.get(gate)
        override_evidence = None
        if override:
            override_evidence = {
                "schema": override.get("schema"),
                "authority": override.get("authority"),
                "author_id": override.get("author_id"),
                "reason": override.get("reason"),
                "scope": override.get("scope"),
                "finding_codes": list(override.get("finding_codes", [])),
                "override_hash": override.get("override_hash"),
            }
        gate_evidence.append({
            "gate_type": gate,
            "envelope_schema": envelope.get("schema"),
            "payload_schema": payload.get("schema"),
            "runner": dict(envelope["runner"]),
            "verdict": payload["verdict"],
            "severity": payload["severity"],
            "finding_codes": sorted(str(x["code"]) for x in payload.get("findings", [])),
            "payload_hash": envelope["payload_hash"],
            "envelope_hash": envelope["envelope_hash"],
            "artifact": dict(artifact) if isinstance(artifact, dict) else None,
            "override": override_evidence,
            "override_hash": (override or {}).get("override_hash"),
        })
    core = {
        "policy_version": policy["version"], "turn_id": turn_id,
        "scene_sha256": scene_sha256, "source_state_hash": source_state_hash,
        "required_gate_types": sorted(required), "candidate_binding": binding or {},
        "envelope_hashes": envelope_hashes,
        "override_hashes": override_hashes, "gate_evidence": gate_evidence,
    }
    authorization_hash = sha256_json(core)
    record = {
        "schema": GATE_AUTHORIZATION_SCHEMA,
        "authorization_id": stable_id("gate-authorization", authorization_hash),
        "authorization_hash": authorization_hash,
        "decision": "AUTHORIZED",
        **core,
        "issued_at": now_iso(),
    }
    record["record_hash"] = _hash_without(record, "record_hash")
    return record


def validate_authorization_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict) or record.get("schema") != GATE_AUTHORIZATION_SCHEMA or record.get("decision") != "AUTHORIZED":
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization record is invalid")
    if record.get("record_hash") != _hash_without(record, "record_hash"):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization record hash mismatch")
    core = {k: record.get(k) for k in (
        "policy_version", "turn_id", "scene_sha256", "source_state_hash",
        "required_gate_types", "candidate_binding", "envelope_hashes", "override_hashes", "gate_evidence",
    )}
    if record.get("authorization_hash") != sha256_json(core):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization semantic hash mismatch")
    if record.get("authorization_id") != stable_id("gate-authorization", record["authorization_hash"]):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization id mismatch")
    binding = record.get("candidate_binding") or {}
    required_binding = {"candidate_hash", "operations_hash", "actor_id", "action_type", "semantic_hash"}
    if binding and not required_binding.issubset(binding):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "candidate authorization binding is incomplete")
    evidence = record.get("gate_evidence")
    required = record.get("required_gate_types")
    if not isinstance(evidence, list) or not isinstance(required, list):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization evidence is invalid")
    evidence_types = [entry.get("gate_type") for entry in evidence if isinstance(entry, dict)]
    if evidence_types != sorted(required) or len(evidence_types) != len(set(evidence_types)):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization evidence is incomplete")
    if set(record.get("envelope_hashes", {})) != set(required):
        raise _invalid(GATE_AUTHORIZATION_FAILED, "gate authorization envelope set is incomplete")
    for entry in evidence:
        gate = entry["gate_type"]
        if not isinstance(entry.get("runner"), dict) or not entry.get("payload_hash"):
            raise _invalid(GATE_AUTHORIZATION_FAILED, "gate evidence runner or payload is incomplete", gate_type=gate)
        if entry.get("envelope_schema") != GATE_ENVELOPE_SCHEMA or entry.get("payload_schema") != GATE_RESULT_SCHEMA:
            raise _invalid(GATE_AUTHORIZATION_FAILED, "gate evidence schema is invalid", gate_type=gate)
        if entry.get("envelope_hash") != record["envelope_hashes"].get(gate):
            raise _invalid(GATE_AUTHORIZATION_FAILED, "gate evidence envelope hash mismatch", gate_type=gate)
        override_hash = record.get("override_hashes", {}).get(gate)
        if entry.get("override_hash") != override_hash:
            raise _invalid(GATE_AUTHORIZATION_FAILED, "gate evidence override hash mismatch", gate_type=gate)
        if override_hash and (entry.get("override") or {}).get("override_hash") != override_hash:
            raise _invalid(GATE_AUTHORIZATION_FAILED, "gate override evidence is incomplete", gate_type=gate)
    return record
