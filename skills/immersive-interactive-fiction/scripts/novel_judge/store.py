from __future__ import annotations

import json
import errno
import os
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

try:
    import fcntl
except ImportError:  # pragma: no cover - non-POSIX host adapter must replace this
    fcntl = None

from .canonical import canonical_json, now_iso, refresh_state_hash, sha256_json
from .durability import crash_failpoint, fsync_directory
from .errors import DUPLICATE_EVENT, JudgeError, PRODUCTION_AUTHORITY_REQUIRED
from .state import normalize_state


class FileStore:
    """Atomic, branch-scoped file store for the judge runtime.

    It is deliberately boring: JSON state is replaced atomically; events and
    turns are append-only records with idempotency checks; journal files make
    interrupted commits inspectable and recoverable.
    """

    @staticmethod
    def _safe_segment(value: Any, label: str) -> str:
        text = str(value)
        if not text or text in {".", ".."} or any(x in text for x in ("/", "\\", "\x00")):
            raise ValueError(f"{label} must be one safe path segment")
        return text

    def __init__(self, root: str | Path, project_id: str, session_id: str, branch_id: str = "main", *, namespace: str = "interactive") -> None:
        self.root = Path(root)
        self.project_id = str(project_id)
        self.session_id = self._safe_segment(session_id, "session_id")
        self.branch_id = self._safe_segment(branch_id, "branch_id")
        self.namespace = self._safe_segment(namespace, "namespace")
        self.base = self.root / self.namespace / "sessions" / self.session_id / "branches" / self.branch_id
        self.state_dir = self.base / "state"
        self.events_dir = self.base / "events"
        self.turns_dir = self.base / "turns"
        self.audit_dir = self.base / "audit"
        self.patch_dir = self.base / "graph-patches"
        self.journal_dir = self.base / "journal"
        self._production_token: object | None = None
        self._ensure()

    def _ensure(self) -> None:
        for p in (self.state_dir, self.state_dir / "checkpoints", self.events_dir, self.turns_dir,
                  self.audit_dir, self.patch_dir, self.journal_dir):
            p.mkdir(parents=True, exist_ok=True)

    @property
    def current_path(self) -> Path:
        return self.state_dir / "current.json"

    @property
    def events_path(self) -> Path:
        return self.events_dir / "events.jsonl"

    @property
    def events_index_path(self) -> Path:
        return self.events_dir / "event-index.json"

    @property
    def manifest_path(self) -> Path:
        return self.base / "branch-manifest.json"

    @property
    def workflow_path(self) -> Path:
        return self.base / "workflow.json"

    @property
    def journal_path(self) -> Path:
        return self.journal_dir / "transaction.json"

    @property
    def authority_path(self) -> Path:
        return self.base / "production-authority.json"

    @property
    def lock_path(self) -> Path:
        return self.journal_dir / "branch.lock"

    @contextmanager
    def transaction_lock(self, *, timeout: float = 10.0):
        """Serialize writers for one branch across processes.

        POSIX hosts use flock. Other hosts must provide an equivalent adapter;
        silently running without a real lock is forbidden for production use.
        """
        if fcntl is None:
            raise RuntimeError("cross-process file locking is unavailable; install a host lock adapter")
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as fh:
            deadline = time.monotonic() + max(0.0, float(timeout))
            while True:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if exc.errno not in {errno.EACCES, errno.EAGAIN, errno.EPERM}:
                        raise
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"branch transaction lock timeout: {self.branch_id}")
                    time.sleep(0.025)
            try:
                yield
            finally:
                fcntl.flock(fh.fileno(), fcntl.LOCK_UN)

    def _read_json(self, path: Path, default: Any = None) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _atomic_json(self, path: Path, value: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(value, fh, ensure_ascii=False, sort_keys=True, indent=2)
                fh.write("\n")
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
            fsync_directory(path.parent)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)

    def bind_production_authority(self, token: object) -> None:
        """Require a private adapter token for canonical mutation methods."""
        if self._production_token is not None and self._production_token is not token:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED, "production store is already bound to another authority")
        self._production_token = token

    def _require_production_token(self, token: object | None) -> None:
        if self._production_token is not None:
            if token is not self._production_token:
                raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                                 "direct canonical mutation is forbidden; use ProjectRuntimeAdapter.commit")
        elif self.authority_path.exists():
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                             "production branch is authority-bound; construct ProjectRuntimeAdapter")

    def save_state(self, state: dict[str, Any], *, _authority_token: object | None = None) -> dict[str, Any]:
        self._require_production_token(_authority_token)
        state = normalize_state(state, verify_hash=False)
        self._atomic_json(self.current_path, state)
        return state

    def load_state(self) -> dict[str, Any] | None:
        state = self._read_json(self.current_path)
        return normalize_state(state) if state is not None else None

    def write_checkpoint(self, checkpoint_id: str, state: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        state = normalize_state(state, verify_hash=False)
        checkpoint_id = self._safe_segment(checkpoint_id, "checkpoint_id")
        path = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        self._atomic_json(path, state)
        return path

    def load_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        checkpoint_id = self._safe_segment(checkpoint_id, "checkpoint_id")
        path = self.state_dir / "checkpoints" / f"{checkpoint_id}.json"
        value = self._read_json(path)
        if value is None:
            raise FileNotFoundError(path)
        return normalize_state(value)

    def read_events(self, *, tolerate_corrupt_tail: bool = False) -> list[dict[str, Any]]:
        from .event_log import read_event_records
        return read_event_records(self, tolerate_corrupt_tail=tolerate_corrupt_tail)

    def repair_events(self, *, _authority_token: object | None = None) -> dict[str, Any]:
        self._require_production_token(_authority_token)
        from .event_log import repair_corrupt_tail
        with self.transaction_lock():
            from .event_log import recover_event_maintenance
            recover_event_maintenance(self)
            return repair_corrupt_tail(self)

    def compact_events(self, *, retain_active: int = 200, _authority_token: object | None = None) -> dict[str, Any]:
        self._require_production_token(_authority_token)
        from .event_log import compact_event_log
        with self.transaction_lock():
            from .event_log import recover_event_maintenance
            recover_event_maintenance(self)
            return compact_event_log(self, retain_active=retain_active)

    def find_event(self, *, event_id: str | None = None, idempotency_key: str | None = None) -> dict[str, Any] | None:
        from .event_log import find_indexed_event
        return find_indexed_event(self, event_id=event_id, idempotency_key=idempotency_key)

    def append_event(self, event: dict[str, Any], *, _authority_token: object | None = None) -> dict[str, Any]:
        self._require_production_token(_authority_token)
        existing = self.find_event(event_id=event.get("event_id"), idempotency_key=event.get("idempotency_key"))
        if existing:
            if existing.get("after_state_hash") == event.get("after_state_hash"):
                return existing
            raise JudgeError(DUPLICATE_EVENT, "event or idempotency key already exists with different result", details={"event_id": event.get("event_id")})
        self.events_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as fh:
            fh.write(canonical_json(event) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        crash_failpoint("event_after_append")
        from .event_log import refresh_active_segment_manifest, build_event_index
        refresh_active_segment_manifest(self)
        crash_failpoint("event_after_active_manifest")
        build_event_index(self)
        crash_failpoint("event_after_index")
        return event

    def save_turn(self, turn: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        turn_id = self._safe_segment(turn["turn_id"], "turn_id")
        path = self.turns_dir / f"{turn_id}.json"
        self._atomic_json(path, turn)
        return path

    def save_audit(self, turn_id: str, audit: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        turn_id = self._safe_segment(turn_id, "turn_id")
        path = self.audit_dir / f"{turn_id}.json"
        self._atomic_json(path, audit)
        return path

    def save_graph_patch(self, turn_id: str, patch: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        turn_id = self._safe_segment(turn_id, "turn_id")
        path = self.patch_dir / f"{turn_id}.json"
        self._atomic_json(path, patch)
        return path

    def save_manifest(self, manifest: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        self._atomic_json(self.manifest_path, manifest)
        return self.manifest_path

    def update_head(self, event: dict[str, Any], state: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        manifest = self.load_manifest() or {"schema": "minis.interactive-branch-manifest.v1", "branch_id": self.branch_id}
        manifest.update({"head_event_id": event.get("event_id"), "head_state_hash": state.get("state_hash"), "updated_at": now_iso()})
        return self.save_manifest(manifest, _authority_token=_authority_token)

    def load_manifest(self) -> dict[str, Any] | None:
        return self._read_json(self.manifest_path)

    def write_journal(self, journal: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        journal = dict(journal)
        journal.setdefault("updated_at", now_iso())
        self._atomic_json(self.journal_path, journal)
        return self.journal_path

    def load_journal(self) -> dict[str, Any] | None:
        return self._read_json(self.journal_path)

    def clear_journal(self, *, _authority_token: object | None = None) -> None:
        self._require_production_token(_authority_token)
        if self.journal_path.exists():
            self.journal_path.unlink()
            fsync_directory(self.journal_path.parent)

    def save_workflow(self, workflow: dict[str, Any], *, _authority_token: object | None = None) -> Path:
        self._require_production_token(_authority_token)
        return self._atomic_json(self.workflow_path, workflow)  # type: ignore[return-value]

    def load_workflow(self) -> dict[str, Any] | None:
        return self._read_json(self.workflow_path)

    def clone_branch_files(self, target: "FileStore") -> None:
        if self._production_token is not None or target._production_token is not None:
            raise JudgeError(PRODUCTION_AUTHORITY_REQUIRED,
                             "bound production branches require an explicit migration or fork adapter")
        if target.base.exists():
            shutil.rmtree(target.base)
        target._ensure()
        if self.current_path.exists():
            target.save_state(self.load_state())
        for name, src_dir, dst_dir in (("events", self.events_dir, target.events_dir), ("turns", self.turns_dir, target.turns_dir),
                                       ("audit", self.audit_dir, target.audit_dir), ("patches", self.patch_dir, target.patch_dir)):
            if src_dir.exists():
                for src in src_dir.glob("*"):
                    if src.is_file():
                        shutil.copy2(src, dst_dir / src.name)
