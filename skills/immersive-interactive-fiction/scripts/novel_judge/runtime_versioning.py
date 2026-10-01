from __future__ import annotations

"""Replay-safe runtime and event-contract compatibility checks.

State migrations protect snapshots; this module protects historical event
histories from being silently interpreted by incompatible transition code.
"""

from typing import Any

from .canonical import sha256_json
from .errors import JudgeError

RUNTIME_BUILD = "novel-judge/0.13.8"
CURRENT_EVENT_SCHEMA = "minis.world-event.v1"
CURRENT_TRANSITION_CONTRACT = "minis.transition-contract.v1"
SUPPORTED_EVENT_SCHEMAS = {CURRENT_EVENT_SCHEMA}
SUPPORTED_TRANSITION_CONTRACTS = {CURRENT_TRANSITION_CONTRACT, "legacy-v1"}


def stamp_event_contract(event: dict[str, Any]) -> dict[str, Any]:
    event.setdefault("runtime_build", RUNTIME_BUILD)
    event.setdefault("transition_contract", CURRENT_TRANSITION_CONTRACT)
    return event


def event_contract(event: dict[str, Any]) -> str:
    # v2.2 and older world-event.v1 records predate explicit contract stamps;
    # their operation semantics are the legacy-v1 compatibility path.
    return str(event.get("transition_contract") or "legacy-v1")


def replay_compatibility_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    builds: set[str] = set()
    contracts: set[str] = set()
    schemas: set[str] = set()
    for index, event in enumerate(events):
        schema = str(event.get("schema") or "")
        contract = event_contract(event)
        build = str(event.get("runtime_build") or "pre-0.7")
        schemas.add(schema); contracts.add(contract); builds.add(build)
        if schema not in SUPPORTED_EVENT_SCHEMAS:
            errors.append({"code": "UNSUPPORTED_EVENT_SCHEMA", "index": index, "event_id": event.get("event_id"), "schema": schema})
        if contract not in SUPPORTED_TRANSITION_CONTRACTS:
            errors.append({"code": "UNSUPPORTED_TRANSITION_CONTRACT", "index": index, "event_id": event.get("event_id"), "contract": contract})
    report = {"schema": "minis.replay-compatibility-report.v1", "runtime_build": RUNTIME_BUILD,
              "event_count": len(events), "event_schemas": sorted(schemas),
              "transition_contracts": sorted(contracts), "producer_builds": sorted(builds),
              "errors": errors, "status": "pass" if not errors else "blocked"}
    report["report_hash"] = sha256_json(report)
    return report


def require_replay_compatible(events: list[dict[str, Any]]) -> dict[str, Any]:
    report = replay_compatibility_report(events)
    if report["errors"]:
        raise JudgeError("REPLAY_CONTRACT_INCOMPATIBLE", "event history requires an unsupported replay contract", details=report)
    return report


def make_replay_fixture(initial_state: dict[str, Any], events: list[dict[str, Any]], expected_state_hash: str) -> dict[str, Any]:
    """Create a portable golden-history fixture for upgrade replay tests."""
    return {"schema": "minis.replay-fixture.v1", "runtime_build": RUNTIME_BUILD,
            "initial_state": initial_state, "events": events,
            "expected_state_hash": expected_state_hash,
            "history_hash": sha256_json(events)}
