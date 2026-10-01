from __future__ import annotations

"""Single production-authority adapter over the shared FileStore kernel.

This module owns production state/event/head/project-pointer commits. Project
specific code may prepare candidates and projections, but may not install
canonical state, events, or authority pointers through a second writer.
"""

import json
from pathlib import Path
from typing import Any

from .canonical import now_iso, sha256_json
from .engine import commit_turn, recover_store, replay_events


def make_candidate_binding(*, turn_id: str, operations: list[dict[str, Any]], actor_id: str,
                           action_type: str, summary: str | None = None,
                           scene_id: str | None = None, chapter_id: str | None = None,
                           scene_sha256: str | None = None,
                           semantic_hash: str | None = None) -> dict[str, Any]:
    """Canonical transition identity shared by approval and commit."""
    ops_hash = sha256_json(operations)
    value = {"turn_id": str(turn_id), "operations": operations, "actor_id": str(actor_id),
             "action_type": str(action_type), "summary": summary, "scene_id": scene_id,
             "chapter_id": chapter_id, "scene_sha256": scene_sha256,
             "operations_hash": ops_hash, "semantic_hash": semantic_hash}
    return {"candidate_hash": sha256_json(value), "operations_hash": ops_hash,
            "actor_id": str(actor_id), "action_type": str(action_type),
            "semantic_hash": semantic_hash or ""}

from .errors import JudgeError, PRODUCTION_AUTHORITY_REQUIRED, PRODUCTION_CONFORMANCE_FAILED
from .event_log import verify_event_log_integrity
from .intent import make_intent
from .gate_authority import default_gate_policy, evaluate_gate_bundle, validate_authorization_record, make_trusted_gate_envelope
from .store import FileStore

AUTHORITY_SCHEMA = "minis.production-authority.v1"
AUTHORITY_MODE = "single_filestore_event_kernel"
COMMIT_API = "ProjectRuntimeAdapter.commit"
LEGACY_WRITER_MODE = "migration_read_only"
REQUIRED_COMMIT_EVIDENCE = ("gate_authorization_hash", "semantic_invariant_report_hash")


def _history_replay(initial_state: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay both normal runtime events and Step 3 checkpoint migrations."""
    if any(any(isinstance(op, dict) and op.get("op") == "replace_snapshot" for op in event.get("operations", [])) for event in events):
        from .history_migration import migration_replay
        return migration_replay(initial_state, events)
    return replay_events(initial_state, events)


class ProjectRuntimeAdapter:
    """Project-facing facade with one canonical commit API.

    Initial baselines and historical migrations are intentionally outside the
    normal commit path. They require an explicit migration authority record;
    callers cannot silently save a new production state.
    """

    def __init__(self, project_root: str | Path, project_id: str, session_id: str,
                 branch_id: str = "main", *, namespace: str = "interactive") -> None:
        self.project_root = Path(project_root)
        self.project_id = str(project_id)
        self.session_id = str(session_id)
        self.branch_id = str(branch_id)
        self.namespace = str(namespace)
        self.store = FileStore(self.project_root, self.project_id, self.session_id,
                               self.branch_id, namespace=self.namespace)
        self.authority_path = self.store.authority_path
        self.project_pointer_path = self.project_root / "project.json"
        self.runtime_head_path = self.project_root / "runtime-head.json"
        self.gate_dir = self.store.base / "gate-authority"
        self.gate_policy_path = self.gate_dir / "policy.json"
        self.gate_bundle_dir = self.gate_dir / "bundles"
        self.gate_authorization_dir = self.gate_dir / "authorizations"
        self._authority_token = object()
        self.store.bind_production_authority(self._authority_token)

    def authority_record(self) -> dict[str, Any] | None:
        return self.store._read_json(self.authority_path)

    def initialize(self, initial_state: dict[str, Any], *, baseline_id: str,
                   provenance: dict[str, Any], migration_authorized: bool = False) -> dict[str, Any]:
        if not migration_authorized:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                             "production baseline initialization requires explicit migration authority")
        if provenance.get("shadow") is not True:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                             "Step 1 permits shadow authority only; production cutover belongs to Step 3")
        with self.store.transaction_lock():
            if self.store.current_path.exists() or self.authority_path.exists():
                raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                                 "production authority already initialized; use commit or an explicit migration tool")
            policy = default_gate_policy()
            state = self.store.save_state(initial_state, _authority_token=self._authority_token)
            self.store.write_checkpoint(baseline_id, state, _authority_token=self._authority_token)
            manifest = {
                "schema": "minis.interactive-branch-manifest.v1",
                "project_id": self.project_id,
                "session_id": self.session_id,
                "branch_id": self.branch_id,
                "baseline_checkpoint": f"state/checkpoints/{baseline_id}.json",
                "baseline_state_hash": state["state_hash"],
                "head_event_id": state.get("events_head"),
                "head_state_hash": state["state_hash"],
                "status": "active",
                "updated_at": now_iso(),
            }
            self.store.save_manifest(manifest, _authority_token=self._authority_token)
            authority = {
                "schema": AUTHORITY_SCHEMA,
                "mode": AUTHORITY_MODE,
                "status": "shadow",
                "canonical_commit_api": COMMIT_API,
                "store_namespace": self.namespace,
                "project_id": self.project_id,
                "session_id": self.session_id,
                "branch_id": self.branch_id,
                "baseline_id": baseline_id,
                "baseline_state_hash": state["state_hash"],
                "legacy_writer_mode": LEGACY_WRITER_MODE,
                "cutover_performed": False,
                "gate_policy_path": str(self.gate_policy_path.relative_to(self.project_root)),
                "gate_policy_hash": sha256_json(policy),
                "provenance": provenance,
                "candidate_binding_required": False,
                "require_author_decision_on_scene_commit": True,
                "created_at": now_iso(),
            }
            self.store._atomic_json(self.store.authority_path, authority)
            self.configure_gate_policy(policy, _initializing=True)
            self._sync_authority_projections(state=state, event=None, status="baseline")
            return {"status": "initialized", "authority": authority, "state_hash": state["state_hash"]}

    def initialize_new_project(self, initial_state: dict[str, Any], *, baseline_id: str = "initial",
                               provenance: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create an active production authority for a genuinely new project.

        This is not a legacy cutover path: the event history starts empty at a
        source-hashed baseline and every subsequent mutation uses commit().
        """
        with self.store.transaction_lock():
            if self.store.current_path.exists() or self.authority_path.exists():
                raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                                 "new-project authority requires an empty store")
            policy = default_gate_policy()
            state = self.store.save_state(initial_state, _authority_token=self._authority_token)
            self.store.write_checkpoint(baseline_id, state, _authority_token=self._authority_token)
            manifest = {"schema": "minis.interactive-branch-manifest.v1",
                        "project_id": self.project_id, "session_id": self.session_id,
                        "branch_id": self.branch_id,
                        "baseline_checkpoint": f"state/checkpoints/{baseline_id}.json",
                        "baseline_state_hash": state["state_hash"], "head_event_id": None,
                        "head_state_hash": state["state_hash"], "scope": state.get("canon_scope", "canon"),
                        "schema_version": 1, "status": "active",
                        "updated_at": now_iso()}
            self.store.save_manifest(manifest, _authority_token=self._authority_token)
            activated = now_iso()
            authority = {"schema": AUTHORITY_SCHEMA, "mode": AUTHORITY_MODE, "status": "active",
                         "canonical_commit_api": COMMIT_API, "store_namespace": self.namespace,
                         "project_id": self.project_id, "session_id": self.session_id,
                         "branch_id": self.branch_id, "baseline_id": baseline_id,
                         "baseline_state_hash": state["state_hash"],
                         "legacy_writer_mode": LEGACY_WRITER_MODE,
                         "cutover_performed": False, "born_under_single_authority": True,
                "require_author_decision_on_scene_commit": True,
                         "gate_policy_path": str(self.gate_policy_path.relative_to(self.project_root)),
                         "gate_policy_hash": sha256_json(policy),
                         "semantic_invariants_activated_at": activated,
                         "typed_semantic_events_activated_at": activated,
                         "typed_semantic_events": {"schema": "minis.event-semantic-delta.v1",
                             "mode": "required_for_new_canonical_events",
                             "executable_authority": "operations", "binding": "operations_hash",
                             "summary_required": True, "legacy_history": "none"},
                         "candidate_binding_required": True,
                         "provenance": {"new_project": True, **dict(provenance or {})},
                         "created_at": activated}
            self.store._atomic_json(self.authority_path, authority)
            self.configure_gate_policy(policy, _initializing=True)
            self._sync_authority_projections(state=state, event=None, status="baseline")
            return {"status": "initialized_active", "authority": authority,
                    "state_hash": state["state_hash"]}

    def require_authority(self) -> dict[str, Any]:
        authority = self.authority_record()
        if not authority or authority.get("schema") != AUTHORITY_SCHEMA:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED, "production authority record missing or invalid")
        if authority.get("mode") != AUTHORITY_MODE or authority.get("canonical_commit_api") != COMMIT_API:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED, "project is not bound to the shared production commit API")
        if authority.get("status") not in {"shadow", "active"}:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED, "production authority status is not writable")
        return authority

    def configure_gate_policy(self, policy: dict[str, Any], *, _initializing: bool = False) -> dict[str, Any]:
        if not _initializing:
            self.require_authority()
        if not isinstance(policy, dict) or policy.get("schema") != "minis.commit-gate-policy.v1" or not policy.get("version"):
            from .errors import GATE_ENVELOPE_INVALID
            raise JudgeError(GATE_ENVELOPE_INVALID, "commit gate policy is invalid")
        self.gate_dir.mkdir(parents=True, exist_ok=True)
        existing = self.store._read_json(self.gate_policy_path)
        if existing and existing != policy:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate policy is immutable for this authority; migrate explicitly")
        self.store._atomic_json(self.gate_policy_path, policy)
        return policy

    def gate_policy(self) -> dict[str, Any]:
        policy = self.store._read_json(self.gate_policy_path)
        if not policy:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate policy is missing")
        authority = self.require_authority()
        if authority.get("gate_policy_hash") != sha256_json(policy):
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate policy hash differs from production authority")
        return policy

    def _authorization_record_for_turn(self, turn_id: str, *,
                                       expected_hash: str | None = None) -> dict[str, Any]:
        from .errors import GATE_AUTHORIZATION_FAILED
        safe = self.store._safe_segment(turn_id, "turn_id")
        record = self.store._read_json(self.gate_authorization_dir / f"{safe}.json")
        if not record:
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate authorization record is missing")
        validate_authorization_record(record)
        if expected_hash is not None and record.get("authorization_hash") != expected_hash:
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "canonical event gate authorization hash mismatch")
        return record

    @staticmethod
    def _gate_bundle_projection(record: dict[str, Any] | None) -> dict[str, Any] | None:
        if not record:
            return None
        return {
            "schema": "minis.head-gate-bundle.v1",
            "policy_version": record.get("policy_version"),
            "authorization_hash": record.get("authorization_hash"),
            "turn_id": record.get("turn_id"),
            "scene_sha256": record.get("scene_sha256"),
            "source_state_hash": record.get("source_state_hash"),
            "required_gate_types": list(record.get("required_gate_types", [])),
            "gates": list(record.get("gate_evidence", [])),
        }

    def approve_gate_bundle(self, *, turn_id: str, scene_sha256: str,
                            source_state_hash: str, envelopes: list[dict[str, Any]],
                            overrides: list[dict[str, Any]] | None = None,
                            candidate_binding: dict[str, Any] | None = None) -> dict[str, Any]:
        authority = self.require_authority()
        if authority.get("candidate_binding_required", True) and candidate_binding is None:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "active production requires candidate-bound Gate authorization")
        with self.store.transaction_lock():
            current = self.store.load_state()
            if not current or current.get("state_hash") != source_state_hash:
                from .errors import GATE_AUTHORIZATION_FAILED
                raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate bundle source state is stale",
                                 details={"expected": (current or {}).get("state_hash"), "actual": source_state_hash})
            authorization = evaluate_gate_bundle(
                envelopes, overrides=overrides, policy=self.gate_policy(), turn_id=turn_id,
                scene_sha256=scene_sha256, source_state_hash=source_state_hash,
                project_root=self.project_root, candidate_binding=candidate_binding,
            )
            bundle = {
                "schema": "minis.gate-bundle.v1", "turn_id": turn_id,
                "scene_sha256": scene_sha256, "source_state_hash": source_state_hash,
                "candidate_binding": candidate_binding,
                "envelopes": envelopes, "overrides": list(overrides or []),
                "authorization": authorization, "created_at": now_iso(),
            }
            bundle["bundle_hash"] = sha256_json({k: v for k, v in bundle.items() if k != "bundle_hash"})
            self.gate_bundle_dir.mkdir(parents=True, exist_ok=True)
            self.gate_authorization_dir.mkdir(parents=True, exist_ok=True)
            safe = self.store._safe_segment(turn_id, "turn_id")
            bundle_path = self.gate_bundle_dir / f"{safe}.json"
            authorization_path = self.gate_authorization_dir / f"{safe}.json"
            if bundle_path.exists() or authorization_path.exists():
                from .errors import GATE_AUTHORIZATION_FAILED
                raise JudgeError(GATE_AUTHORIZATION_FAILED, "gate bundle already approved; create a new candidate revision")
            self.store._atomic_json(bundle_path, bundle)
            self.store._atomic_json(authorization_path, authorization)
            return authorization

    def _revalidate_gate_authorization(self, *, turn_id: str, scene_sha256: str,
                                       source_state_hash: str,
                                       candidate_binding: dict[str, Any]) -> dict[str, Any]:
        safe = self.store._safe_segment(turn_id, "turn_id")
        bundle_path = self.gate_bundle_dir / f"{safe}.json"
        authorization_path = self.gate_authorization_dir / f"{safe}.json"
        if not bundle_path.is_file() or not authorization_path.is_file():
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "approved gate bundle or authorization is missing")
        bundle = self.store._read_json(bundle_path); record = self.store._read_json(authorization_path)
        if bundle.get("bundle_hash") != sha256_json({k: v for k, v in bundle.items() if k != "bundle_hash"}):
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "approved gate bundle hash mismatch")
        if bundle.get("turn_id") != turn_id or bundle.get("scene_sha256") != scene_sha256 or bundle.get("source_state_hash") != source_state_hash:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "approved gate bundle binding mismatch")
        approved_binding = record.get("candidate_binding") or bundle.get("candidate_binding") or {}
        if approved_binding and approved_binding != candidate_binding:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "approved gate candidate binding differs from commit candidate")
        if approved_binding and record.get("candidate_binding") != candidate_binding:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "authorization candidate binding differs from commit candidate")
        validate_authorization_record(record)
        embedded = bundle.get("authorization")
        validate_authorization_record(embedded)
        if embedded != record:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "bundle and standalone gate authorizations differ")
        reevaluated = evaluate_gate_bundle(
            bundle.get("envelopes"), overrides=bundle.get("overrides"), policy=self.gate_policy(),
            turn_id=turn_id, scene_sha256=scene_sha256, source_state_hash=source_state_hash,
            project_root=self.project_root, candidate_binding=(candidate_binding if approved_binding else None),
        )
        if reevaluated.get("authorization_hash") != record.get("authorization_hash"):
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "commit-time gate authorization differs from approval")
        return record

    def commit(self, *, turn_id: str, operations: list[dict[str, Any]],
               expected_state_hash: str, actor_id: str = "world",
               action_type: str = "world_tick", source: str = "author",
               summary: str | None = None, scene_id: str | None = None,
               chapter_id: str | None = None, source_artifact_hash: str | None = None,
               source_artifact_path: str | None = None,
               scene_sha256: str | None = None,
               semantic_kind: str | None = None,
               semantic_effects: list[dict[str, Any]] | None = None,
               author_decision: dict[str, Any] | None = None,
               lock_timeout: float = 10.0) -> dict[str, Any]:
        authority = self.require_authority()
        if not scene_sha256:
            from .errors import GATE_AUTHORIZATION_FAILED
            raise JudgeError(GATE_AUTHORIZATION_FAILED, "production commit requires a scene-bound gate authorization")
        from .author_decision import require_scene_author_decision, record_author_decision
        decision_payload = require_scene_author_decision(
            scene_id=scene_id,
            author_decision=author_decision,
            authority_record=authority,
            allow_system_commit=True,
        )
        from .semantic_events import compile_semantic_delta
        semantic_delta = compile_semantic_delta(
            turn_id=turn_id, actor_id=actor_id, action_type=action_type,
            operations=operations, summary=summary, scene_id=scene_id,
            declared_effects=semantic_effects, semantic_kind=semantic_kind,
        )
        candidate_binding = make_candidate_binding(turn_id=turn_id, operations=operations, actor_id=actor_id,
            action_type=action_type, summary=summary, scene_id=scene_id, chapter_id=chapter_id,
            scene_sha256=scene_sha256, semantic_hash=semantic_delta["semantic_hash"])
        parameters: dict[str, Any] = {"operations": operations, "gate_scene_sha256": scene_sha256,
                                      "semantic_delta": semantic_delta}
        if scene_id:
            if not source_artifact_path or not source_artifact_hash:
                raise ValueError("scene commits require source_artifact_path and source_artifact_hash")
            import hashlib
            artifact = (self.project_root / source_artifact_path).resolve(); root = self.project_root.resolve()
            try: artifact.relative_to(root)
            except ValueError: raise ValueError("scene artifact escapes project root")
            if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != source_artifact_hash or source_artifact_hash != scene_sha256:
                raise ValueError("scene artifact is missing or differs from scene authorization")
            parameters.update({"scene_id": scene_id, "chapter_id": chapter_id,
                               "summary": summary, "source_artifact_hash": source_artifact_hash,
                               "source_artifact_path": source_artifact_path})
        intent = make_intent(actor_id, action_type, turn_id=turn_id, source=source,
                             player_authored=True, parameters=parameters,
                             intent_id=f"production-{turn_id}")
        committed = False
        with self.store.transaction_lock(timeout=lock_timeout):
            current = self.store.load_state()
            if not current or current.get("state_hash") != expected_state_hash:
                from .errors import STATE_HASH_MISMATCH
                raise JudgeError(STATE_HASH_MISMATCH, "caller state hash is stale",
                                 details={"expected": expected_state_hash, "actual": (current or {}).get("state_hash")})
            gate_authorization = self._revalidate_gate_authorization(
                turn_id=turn_id, scene_sha256=scene_sha256,
                source_state_hash=expected_state_hash,
                candidate_binding=candidate_binding,
            )
            # Grandfather existing migration debt, but fail closed on every
            # newly introduced high-confidence semantic contradiction.
            from .semantic_invariants import enforce_transition
            invariant_report = enforce_transition(current, operations)
            parameters["semantic_invariant_report_hash"] = invariant_report["report_hash"]
            parameters["gate_authorization_hash"] = gate_authorization["authorization_hash"]
            intent["parameters"] = parameters
            from .event_log import recover_event_maintenance
            from .engine import _commit_turn_locked
            recover_event_maintenance(self.store)
            result = _commit_turn_locked(
                self.store, intent, expected_state_hash=expected_state_hash,
                source=source, authority_token=self._authority_token,
            )
            if result.get("status") == "committed":
                result["event"]["gate_authorization_hash"] = gate_authorization["authorization_hash"]
                result["gate_authorization"] = gate_authorization
                event_record = self.store.find_event(event_id=result["event"]["event_id"])
                if not event_record or event_record.get("gate_authorization_hash") != gate_authorization["authorization_hash"]:
                    from .errors import GATE_AUTHORIZATION_FAILED
                    raise JudgeError(GATE_AUTHORIZATION_FAILED, "canonical event did not preserve gate authorization")
                self._sync_authority_projections(state=self.store.load_state(), event=result.get("event"), status="committed",
                                                 gate_authorization=gate_authorization)
                committed = True
        if committed:
            # Canonical commit is already durable and the branch lock is now
            # released. Disposable projectors must never inflate lock latency.
            try:
                from .production_projections import refresh_production_projections
                result["projection_refresh"] = refresh_production_projections(self)
            except Exception as exc:
                failure = {"schema": "minis.production-projection-refresh-failure.v1",
                           "status": "failed", "turn_id": turn_id,
                           "state_hash": self.store.load_state().get("state_hash"),
                           "error_type": type(exc).__name__, "error": str(exc),
                           "created_at": now_iso()}
                self.store._atomic_json(self.store.base / "projection-refresh-failure.json", failure)
                result["projection_refresh"] = failure
            if decision_payload is not None:
                try:
                    state_after = self.store.load_state() or {}
                    result["author_decision"] = record_author_decision(
                        self.store,
                        decision=decision_payload["decision"],
                        author_id=decision_payload["author_id"],
                        candidate_hash=candidate_binding["candidate_hash"],
                        source_state_hash=expected_state_hash,
                        source_event_head=state_after.get("events_head"),
                        turn_id=turn_id,
                        scene_id=scene_id,
                        reason_codes=decision_payload.get("reason_codes") or ["other"],
                        reason=decision_payload.get("reason") or summary or "scene commit accepted",
                        changed_spans=decision_payload.get("changed_spans") or [],
                        revision_round=decision_payload.get("revision_round"),
                        gate_pass=True,
                        confidence=decision_payload.get("confidence") or "high",
                        reluctant_accept=bool(decision_payload.get("reluctant_accept")),
                        provenance={"source": "ProjectRuntimeAdapter.commit", "action_type": action_type},
                    )
                except Exception as exc:
                    # Decision ledger failure must surface: preference truth is required for scene commits.
                    raise ValueError(f"failed to record AUTHOR_DECISION after commit: {exc}") from exc
        return result

    def recover(self) -> dict[str, Any]:
        self.require_authority()
        with self.store.transaction_lock():
            report = dict(recover_store(self.store, _authority_token=self._authority_token))
            state = self.store.load_state()
            events = self.store.read_events()
            event = events[-1] if events else None
            projection_errors: list[str] = []
            if state:
                head = self.store._read_json(self.runtime_head_path)
                project = self.store._read_json(self.project_pointer_path, {})
                latest_auth = (event or {}).get("gate_authorization_hash")
                if not head or head.get("state_hash") != state.get("state_hash") or head.get("event_head") != state.get("events_head") or head.get("gate_authorization_hash") != latest_auth:
                    projection_errors.append("runtime_head_stale")
                pointer = project.get("production_authority", {})
                if pointer.get("state_hash") != state.get("state_hash") or pointer.get("event_head") != state.get("events_head") or pointer.get("gate_authorization_hash") != latest_auth:
                    projection_errors.append("project_pointer_stale")
                self._sync_authority_projections(state=state, event=event, status="recovered")
            report["core_status"] = report.get("status")
            report["projection_errors_before_recovery"] = projection_errors
            report["projection_reconciled"] = bool(projection_errors)
            report["recovered"] = bool(report.get("recovered") or projection_errors)
            if projection_errors and report.get("status") == "clean":
                report["status"] = "reconciled_projections"
            return report

    def read_state_at(self, *, sequence: int | None = None,
                      turn_id: str | None = None) -> dict[str, Any]:
        """Replay a point-in-time state from the trusted baseline."""
        authority = self.require_authority()
        events = self.store.read_events()
        if sequence is not None:
            if sequence < 0 or sequence > len(events): raise ValueError("sequence is outside event history")
            selected = events[:sequence]
        elif turn_id is not None:
            matches = [i for i,e in enumerate(events) if str(e.get("turn_id")) == str(turn_id)]
            if not matches: raise KeyError(turn_id)
            selected = events[:matches[-1]+1]
        else:
            selected = events
        return _history_replay(self.store.load_checkpoint(authority["baseline_id"]), selected)

    def status(self) -> dict[str, Any]:
        authority = self.require_authority()
        state = self.store.load_state()
        events = self.store.read_events()
        integrity = verify_event_log_integrity(self.store)
        manifest = self.store.load_manifest()
        runtime_head = self.store._read_json(self.runtime_head_path)
        project = self.store._read_json(self.project_pointer_path, {})
        canonical_events = [e for e in events if e.get("verdict") in {"allow", "allow_with_cost", "partial", "meta"}]
        latest_canonical = canonical_events[-1] if canonical_events else None
        errors: list[str] = []
        if not state:
            errors.append("missing_state")
        else:
            if (manifest or {}).get("head_state_hash") != state.get("state_hash"): errors.append("manifest_state_mismatch")
            if runtime_head and runtime_head.get("state_hash") != state.get("state_hash"): errors.append("runtime_head_state_mismatch")
            if runtime_head and runtime_head.get("event_head") != state.get("events_head"): errors.append("runtime_head_event_mismatch")
            if latest_canonical:
                latest_event = latest_canonical
                latest_auth = latest_event.get("gate_authorization_hash")
                # Authorities upgraded before Step 4 may have migration/live
                # history without invariant evidence. Only events committed
                # after semantic_invariants_activated_at are required to carry it.
                activated = authority.get("semantic_invariants_activated_at")
                if activated and str(latest_event.get("created_at") or "") >= str(activated) and not latest_event.get("semantic_invariant_report_hash"):
                    errors.append("latest_event_missing_semantic_invariant_evidence")
                typed_activated = authority.get("typed_semantic_events_activated_at")
                if typed_activated and str(latest_event.get("created_at") or "") >= str(typed_activated):
                    try:
                        from .semantic_events import validate_semantic_delta
                        validate_semantic_delta(latest_event.get("semantic_delta"), latest_event.get("operations", []))
                    except (TypeError, ValueError):
                        errors.append("latest_event_missing_or_invalid_semantic_delta")
                if not latest_auth:
                    errors.append("latest_event_missing_gate_authorization")
                else:
                    try:
                        authorization = self._authorization_record_for_turn(
                            str(latest_event.get("turn_id")), expected_hash=latest_auth,
                        )
                        expected_bundle = self._gate_bundle_projection(authorization)
                        if (runtime_head or {}).get("gate_bundle") != expected_bundle:
                            errors.append("runtime_head_gate_bundle_mismatch")
                    except JudgeError:
                        errors.append("latest_gate_authorization_invalid")
                if runtime_head and runtime_head.get("gate_authorization_hash") != latest_auth: errors.append("runtime_head_gate_authorization_mismatch")
                if project.get("production_authority", {}).get("gate_authorization_hash") != latest_auth: errors.append("project_pointer_gate_authorization_mismatch")
            if project.get("production_authority", {}).get("state_hash") != state.get("state_hash"): errors.append("project_pointer_state_mismatch")
            if latest_canonical:
                replayed = _history_replay(self.store.load_checkpoint(authority["baseline_id"]), events)
                if replayed.get("state_hash") != state.get("state_hash"): errors.append("replay_state_mismatch")
        return {
            "schema": "minis.production-conformance-report.v1",
            "status": "pass" if not errors and integrity.get("status") == "pass" else "fail",
            "errors": errors,
            "authority": authority,
            "event_count": len(events),
            "state_hash": (state or {}).get("state_hash"),
            "event_head": (state or {}).get("events_head"),
            "gate_policy_hash": sha256_json(self.gate_policy()),
            "latest_gate_authorization_hash": (latest_canonical.get("gate_authorization_hash") if latest_canonical else None),
            "integrity": integrity,
        }

    def assert_conformant(self) -> dict[str, Any]:
        report = self.status()
        if report["status"] != "pass":
            raise JudgeError(PRODUCTION_CONFORMANCE_FAILED, "production adapter conformance failed", details=report)
        return report

    def _sync_authority_projections(self, *, state: dict[str, Any], event: dict[str, Any] | None,
                                    status: str, gate_authorization: dict[str, Any] | None = None) -> None:
        """Project pointers are projections; FileStore remains the authority."""
        event_authorization_hash = (event or {}).get("gate_authorization_hash")
        if gate_authorization is None and event_authorization_hash:
            gate_authorization = self._authorization_record_for_turn(
                str((event or {}).get("turn_id") or state.get("last_turn_id")),
                expected_hash=event_authorization_hash,
            )
        gate_bundle = self._gate_bundle_projection(gate_authorization)
        head = {
            "schema": "minis.production-runtime-head.v1",
            "authority_schema": AUTHORITY_SCHEMA,
            "canonical_commit_api": COMMIT_API,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "branch_id": self.branch_id,
            "state_path": str(self.store.current_path.relative_to(self.project_root)),
            "events_path": str(self.store.events_path.relative_to(self.project_root)),
            "manifest_path": str(self.store.manifest_path.relative_to(self.project_root)),
            "state_hash": state.get("state_hash"),
            "event_head": state.get("events_head"),
            "last_turn_id": state.get("last_turn_id"),
            "scene_id": ((event or {}).get("scene") or {}).get("scene_id") or state.get("last_turn_id"),
            "scene_path": ((event or {}).get("scene") or {}).get("source_artifact_path"),
            "scene_sha256": ((event or {}).get("scene") or {}).get("source_artifact_hash"),
            "revision": state.get("revision"),
            "gate_authorization_hash": (gate_authorization or {}).get("authorization_hash") or (event or {}).get("gate_authorization_hash"),
            "gate_authorization_path": (str((self.gate_authorization_dir / f"{self.store._safe_segment(str(state.get('last_turn_id')), 'turn_id')}.json").relative_to(self.project_root)) if state.get("last_turn_id") and ((self.gate_authorization_dir / f"{self.store._safe_segment(str(state.get('last_turn_id')), 'turn_id')}.json").exists()) else None),
            "gate_bundle": gate_bundle,
            "status": status,
            "updated_at": now_iso(),
        }
        head["head_hash"] = sha256_json(head)
        self.store._atomic_json(self.runtime_head_path, head)
        if status == "committed":
            from .durability import crash_failpoint
            crash_failpoint("production_after_runtime_head")
        project = self.store._read_json(self.project_pointer_path, {})
        project.update({
            "project_id": project.get("project_id", self.project_id),
            "production_authority": {
                "schema": AUTHORITY_SCHEMA,
                "project_id": self.project_id,
                "session_id": self.session_id,
                "branch_id": self.branch_id,
                "canonical_commit_api": COMMIT_API,
                "authority_path": str(self.authority_path.relative_to(self.project_root)),
                "runtime_head_path": str(self.runtime_head_path.relative_to(self.project_root)),
                "state_hash": state.get("state_hash"),
                "event_head": state.get("events_head"),
                "last_turn_id": state.get("last_turn_id"),
                "scene_id": ((event or {}).get("scene") or {}).get("scene_id") or state.get("last_turn_id"),
                "scene_path": ((event or {}).get("scene") or {}).get("source_artifact_path"),
                "scene_sha256": ((event or {}).get("scene") or {}).get("source_artifact_hash"),
                "gate_authorization_hash": (gate_authorization or {}).get("authorization_hash") or (event or {}).get("gate_authorization_hash"),
                "updated_at": now_iso(),
            },
        })
        self.store._atomic_json(self.project_pointer_path, project)
        if status == "committed":
            from .durability import crash_failpoint
            crash_failpoint("production_after_project_pointer")


def production_store(project_root: str | Path, project_id: str, session_id: str,
                     branch_id: str = "main", *, namespace: str = "interactive") -> ProjectRuntimeAdapter:
    return ProjectRuntimeAdapter(project_root, project_id, session_id, branch_id, namespace=namespace)
