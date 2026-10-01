from __future__ import annotations

"""Indexed, repairable append-only JSONL event storage helpers."""

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .canonical import canonical_json, now_iso, sha256_json

INDEX_SCHEMA = "minis.event-index.v1"
MANIFEST_SCHEMA = "minis.event-log-manifest.v1"


def _sha_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _manifest_path(store: Any) -> Path:
    return store.events_dir / "event-log-manifest.json"


def _index_path(store: Any) -> Path:
    return store.events_dir / "event-index.json"


def _atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data); fh.flush(); os.fsync(fh.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)


def _maintenance_journal_path(store: Any) -> Path:
    return store.events_dir / "event-maintenance.json"


def recover_event_maintenance(store: Any) -> dict[str, Any]:
    path = _maintenance_journal_path(store)
    if not path.exists(): return {"status": "clean", "recovered": False}
    journal = json.loads(path.read_text(encoding="utf-8")); backup = Path(journal["active_backup"])
    if not backup.exists(): raise ValueError("event maintenance backup is missing")
    _atomic_bytes(store.events_path, backup.read_bytes())
    manifest_path = _manifest_path(store); previous = journal.get("previous_manifest")
    if previous is None:
        if manifest_path.exists(): manifest_path.unlink()
    else: store._atomic_json(manifest_path, previous)
    archive = journal.get("new_archive")
    if archive and Path(archive).exists(): Path(archive).unlink()
    refresh_active_segment_manifest(store)
    path.unlink(); build_event_index(store)
    return {"status": "rolled_back_event_maintenance", "recovered": True, "operation": journal.get("operation"), "backup": str(backup)}


def load_log_manifest(store: Any) -> dict[str, Any]:
    path = _manifest_path(store)
    if path.exists():
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != MANIFEST_SCHEMA: raise ValueError("unsupported event log manifest")
        return value
    return {"schema": MANIFEST_SCHEMA, "archives": [], "active": store.events_path.name, "updated_at": now_iso()}


def _active_meta(manifest: dict[str, Any]) -> dict[str, Any] | None:
    value = manifest.get("active_segment")
    return value if isinstance(value, dict) else None


def _active_metadata(path: Path) -> dict[str, Any]:
    raw = path.read_bytes() if path.exists() else b""
    report = inspect_jsonl(path)
    if report["status"] != "clean":
        raise ValueError(f"active event log is not clean: {report['status']}")
    return {"file": path.name, "bytes": len(raw), "sha256": _sha_bytes(raw),
            "event_count": len(report["records"]), "updated_at": now_iso()}


def refresh_active_segment_manifest(store: Any) -> dict[str, Any]:
    """Persist the trusted active-segment head after an authorized append."""
    manifest = load_log_manifest(store)
    manifest["active_segment"] = _active_metadata(store.events_path)
    manifest["updated_at"] = now_iso()
    store._atomic_json(_manifest_path(store), manifest)
    return manifest


def verify_event_log_integrity(store: Any) -> dict[str, Any]:
    """Verify the complete active+archive history independently of the index.

    A deleted index must never turn an altered or missing immutable archive
    into an accepted new baseline.
    """
    manifest = load_log_manifest(store); errors = []; event_ids = set(); idempotency = set(); count = 0
    declared = {str(x.get("file")): x for x in manifest.get("archives", [])}
    for name, meta in declared.items():
        path = store.events_dir / name
        if not path.is_file():
            errors.append({"code": "EVENT_ARCHIVE_MISSING", "file": name}); continue
        raw = path.read_bytes(); actual_hash = _sha_bytes(raw)
        if actual_hash != meta.get("sha256"):
            errors.append({"code": "EVENT_ARCHIVE_HASH_MISMATCH", "file": name, "expected": meta.get("sha256"), "actual": actual_hash})
        report = inspect_jsonl(path)
        if report["status"] != "clean": errors.append({"code": "EVENT_ARCHIVE_CORRUPT", "file": name, "status": report["status"]})
        if int(meta.get("event_count", -1)) != len(report["records"]):
            errors.append({"code": "EVENT_ARCHIVE_COUNT_MISMATCH", "file": name, "expected": meta.get("event_count"), "actual": len(report["records"])})
        for rec in report["records"]:
            value = rec["value"]; eid = value.get("event_id"); ikey = value.get("idempotency_key")
            if eid and eid in event_ids: errors.append({"code": "DUPLICATE_EVENT_ID", "event_id": eid})
            if ikey and ikey in idempotency: errors.append({"code": "DUPLICATE_IDEMPOTENCY_KEY", "idempotency_key": ikey})
            if eid: event_ids.add(eid)
            if ikey: idempotency.add(ikey)
            count += 1
    active = inspect_jsonl(store.events_path)
    active_meta = _active_meta(manifest)
    authorized_extension = False
    if active_meta is None:
        # Upgrade bridge for v2.4 stores: the old authoritative index already
        # recorded exact file bytes/hash. Accept only a present, schema-valid,
        # fully fresh index; deleting it must not create a new trust baseline.
        legacy_index = None
        index_path = _index_path(store)
        if active["records"] and index_path.exists():
            try:
                candidate = json.loads(index_path.read_text(encoding="utf-8"))
                if candidate.get("schema") == INDEX_SCHEMA and _index_fresh(store, candidate):
                    legacy_index = candidate
            except Exception:
                legacy_index = None
        if active["records"] and legacy_index is None:
            # First append may be fsynced before the first active manifest is
            # installed.  Only the branch transaction journal may authorize
            # exactly that one initial record; no journal means no baseline.
            journal = store.load_journal() if hasattr(store, "load_journal") else None
            if not declared and len(active["records"]) == 1 and isinstance(journal, dict):
                value = active["records"][0]["value"]
                authorized_extension = value.get("event_id") == journal.get("event_id") and value.get("idempotency_key") == journal.get("idempotency_key")
            if not authorized_extension:
                errors.append({"code": "ACTIVE_SEGMENT_BASELINE_MISSING", "file": store.events_path.name})
    else:
        raw = store.events_path.read_bytes() if store.events_path.exists() else b""
        expected_bytes = int(active_meta.get("bytes", -1))
        expected_hash = active_meta.get("sha256")
        # A crash can occur after the fsynced append but before the active
        # manifest replacement. Accept exactly the journal-proven single-record
        # suffix so recovery can finish; arbitrary appended bytes stay blocked.
        journal = store.load_journal() if hasattr(store, "load_journal") else None
        if expected_bytes >= 0 and len(raw) > expected_bytes and _sha_bytes(raw[:expected_bytes]) == expected_hash and isinstance(journal, dict):
            suffix = inspect_jsonl_bytes(raw[expected_bytes:])
            if suffix["status"] == "clean" and len(suffix["records"]) == 1:
                value = suffix["records"][0]["value"]
                authorized_extension = value.get("event_id") == journal.get("event_id") and value.get("idempotency_key") == journal.get("idempotency_key")
        if active_meta.get("file") != store.events_path.name:
            errors.append({"code": "ACTIVE_SEGMENT_FILE_MISMATCH", "expected": active_meta.get("file"), "actual": store.events_path.name})
        if not authorized_extension and expected_bytes != len(raw):
            errors.append({"code": "ACTIVE_SEGMENT_SIZE_MISMATCH", "expected": active_meta.get("bytes"), "actual": len(raw)})
        if not authorized_extension and expected_hash != _sha_bytes(raw):
            errors.append({"code": "ACTIVE_SEGMENT_HASH_MISMATCH", "expected": active_meta.get("sha256"), "actual": _sha_bytes(raw)})
        expected_count = int(active_meta.get("event_count", -1)) + (1 if authorized_extension else 0)
        if expected_count != len(active["records"]):
            errors.append({"code": "ACTIVE_SEGMENT_COUNT_MISMATCH", "expected": expected_count, "actual": len(active["records"])})
    if active["status"] != "clean": errors.append({"code": "ACTIVE_EVENT_LOG_CORRUPT", "status": active["status"]})
    for rec in active["records"]:
        value = rec["value"]; eid = value.get("event_id"); ikey = value.get("idempotency_key")
        if eid and eid in event_ids: errors.append({"code": "DUPLICATE_EVENT_ID", "event_id": eid})
        if ikey and ikey in idempotency: errors.append({"code": "DUPLICATE_IDEMPOTENCY_KEY", "idempotency_key": ikey})
        if eid: event_ids.add(eid)
        if ikey: idempotency.add(ikey)
        count += 1
    report = {"schema": "minis.event-log-integrity.v1", "status": "pass" if not errors else "blocked",
              "event_count": count, "archive_count": len(declared), "errors": errors}
    report["report_hash"] = sha256_json(report); return report


def event_files(store: Any) -> list[Path]:
    manifest = load_log_manifest(store)
    paths = [store.events_dir / str(x["file"]) for x in manifest.get("archives", [])]
    paths.append(store.events_path)
    return [x for x in paths if x.exists()]


def inspect_jsonl_bytes(data: bytes) -> dict[str, Any]:
    """Parse JSONL bytes without creating or modifying any filesystem entry."""
    records = []; offset = 0; valid_bytes = 0; corrupt = None
    lines = data.splitlines(keepends=True)
    for index, raw in enumerate(lines):
        start = offset; offset += len(raw)
        content = raw.rstrip(b"\r\n")
        if not content: valid_bytes = offset; continue
        try:
            value = json.loads(content.decode("utf-8"))
            if not isinstance(value, dict): raise ValueError("event record is not an object")
            records.append({"value": value, "offset": start, "length": len(raw), "line_hash": _sha_bytes(raw)})
            valid_bytes = offset
        except Exception as exc:
            is_tail = index == len(lines) - 1
            corrupt = {"offset": start, "bytes": len(data) - start, "error": f"{type(exc).__name__}: {exc}", "is_tail": is_tail}
            if not is_tail: return {"status": "corrupt_middle", "records": records, "valid_bytes": valid_bytes, "size": len(data), "corrupt_tail": corrupt}
            break
    return {"status": "corrupt_tail" if corrupt else "clean", "records": records, "valid_bytes": valid_bytes, "size": len(data), "corrupt_tail": corrupt}


def inspect_jsonl(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists(): return inspect_jsonl_bytes(b"")
    return inspect_jsonl_bytes(p.read_bytes())


def read_event_records(store: Any, *, tolerate_corrupt_tail: bool = False) -> list[dict[str, Any]]:
    integrity = verify_event_log_integrity(store)
    if integrity["errors"]:
        # Tail repair remains an explicit opt-in and applies only to active log.
        tail_only = all(x.get("code") == "ACTIVE_EVENT_LOG_CORRUPT" and x.get("status") == "corrupt_tail" for x in integrity["errors"])
        if not (tolerate_corrupt_tail and tail_only):
            raise ValueError(f"event history integrity failure: {integrity['errors']}")
    out = []
    for path in event_files(store):
        report = inspect_jsonl(path)
        if report["status"] != "clean" and not (tolerate_corrupt_tail and report["status"] == "corrupt_tail" and path == store.events_path):
            raise ValueError(f"event log {report['status']}: {path}: {report.get('corrupt_tail')}")
        out.extend(x["value"] for x in report["records"])
    return out


def build_event_index(store: Any) -> dict[str, Any]:
    integrity = verify_event_log_integrity(store)
    if integrity["errors"]: raise ValueError(f"event history integrity failure: {integrity['errors']}")
    entries = {}; idempotency = {}; files = []
    for path in event_files(store):
        report = inspect_jsonl(path)
        if report["status"] != "clean": raise ValueError(f"cannot index {report['status']}: {path}")
        rel = path.relative_to(store.events_dir).as_posix()
        raw = path.read_bytes(); files.append({"file": rel, "bytes": len(raw), "sha256": _sha_bytes(raw)})
        for record in report["records"]:
            value = record["value"]; eid = value.get("event_id"); ikey = value.get("idempotency_key")
            loc = {"file": rel, "offset": record["offset"], "length": record["length"], "line_hash": record["line_hash"]}
            if eid:
                if eid in entries: raise ValueError(f"duplicate event id in log: {eid}")
                entries[str(eid)] = loc
            if ikey:
                if ikey in idempotency: raise ValueError(f"duplicate idempotency key in log: {ikey}")
                idempotency[str(ikey)] = str(eid)
    index = {"schema": INDEX_SCHEMA, "files": files, "events": entries, "idempotency": idempotency,
             "event_count": len(entries), "built_at": now_iso()}
    store._atomic_json(_index_path(store), index)
    return index


def _index_fresh(store: Any, index: dict[str, Any]) -> bool:
    expected = {x["file"]: x for x in index.get("files", [])}
    actual = event_files(store)
    actual_names = {x.relative_to(store.events_dir).as_posix() for x in actual}
    if set(expected) != actual_names: return False
    for p in actual:
        name = p.relative_to(store.events_dir).as_posix(); meta = expected[name]; size = p.stat().st_size; digest = _sha_bytes(p.read_bytes())
        if size == meta.get("bytes") and digest != meta.get("sha256"):
            raise ValueError(f"event log changed without append: {name}")
        if name != store.events_path.name and (size != meta.get("bytes") or digest != meta.get("sha256")):
            raise ValueError(f"immutable event archive changed: {name}")
        if size < int(meta.get("bytes", 0)):
            raise ValueError(f"event log was truncated without maintenance journal: {name}")
        if size != meta.get("bytes") or digest != meta.get("sha256"): return False
    return True


def find_indexed_event(store: Any, *, event_id: str | None = None, idempotency_key: str | None = None) -> dict[str, Any] | None:
    path = _index_path(store); index = None
    if path.exists():
        try:
            candidate = json.loads(path.read_text(encoding="utf-8"))
            if candidate.get("schema") == INDEX_SCHEMA and _index_fresh(store, candidate): index = candidate
        except (OSError, json.JSONDecodeError): index = None
    if index is None: index = build_event_index(store)
    eid = event_id or index.get("idempotency", {}).get(str(idempotency_key))
    loc = index.get("events", {}).get(str(eid)) if eid else None
    if not loc: return None
    source = store.events_dir / loc["file"]
    with source.open("rb") as fh: fh.seek(int(loc["offset"])); raw = fh.read(int(loc["length"]))
    if _sha_bytes(raw) != loc["line_hash"]: raise ValueError("event index line hash mismatch")
    value = json.loads(raw.decode("utf-8"))
    if event_id and value.get("event_id") != event_id: raise ValueError("event index id mismatch")
    if idempotency_key and value.get("idempotency_key") != idempotency_key: raise ValueError("event index idempotency mismatch")
    return value


def repair_corrupt_tail(store: Any) -> dict[str, Any]:
    report = inspect_jsonl(store.events_path)
    if report["status"] == "clean": return {"status": "clean", "repaired": False}
    if report["status"] != "corrupt_tail": raise ValueError("refusing to repair non-tail event corruption")
    backup = store.events_dir / f"events-corrupt-{sha256_json(store.events_path.read_bytes()).split(':')[-1][:16]}.bak"
    shutil.copy2(store.events_path, backup)
    journal = {"schema": "minis.event-maintenance.v1", "operation": "repair_tail", "active_backup": str(backup),
               "previous_manifest": load_log_manifest(store) if _manifest_path(store).exists() else None,
               "new_archive": None, "started_at": now_iso()}
    store._atomic_json(_maintenance_journal_path(store), journal)
    _atomic_bytes(store.events_path, store.events_path.read_bytes()[:int(report["valid_bytes"])])
    refresh_active_segment_manifest(store)
    index = build_event_index(store); _maintenance_journal_path(store).unlink()
    return {"status": "repaired_corrupt_tail", "repaired": True, "backup": str(backup),
            "removed_bytes": int(report["size"]) - int(report["valid_bytes"]), "event_count": index["event_count"]}


def compact_event_log(store: Any, *, retain_active: int = 200) -> dict[str, Any]:
    retain_active = max(1, int(retain_active)); active_report = inspect_jsonl(store.events_path)
    if active_report["status"] != "clean": raise ValueError("repair event log before compaction")
    records = active_report["records"]
    if len(records) <= retain_active: return {"status": "not_needed", "archived": 0, "active": len(records)}
    cut = len(records) - retain_active; prefix = b"".join(store.events_path.read_bytes()[x["offset"]:x["offset"] + x["length"]] for x in records[:cut])
    suffix = b"".join(store.events_path.read_bytes()[x["offset"]:x["offset"] + x["length"]] for x in records[cut:])
    manifest = load_log_manifest(store); seq = len(manifest.get("archives", [])) + 1
    name = f"archive-{seq:06d}-{_sha_bytes(prefix).split(':')[-1][:16]}.jsonl"; archive = store.events_dir / name
    backup = store.events_dir / f"events-precompact-{_sha_bytes(store.events_path.read_bytes()).split(':')[-1][:16]}.bak"
    shutil.copy2(store.events_path, backup)
    store._atomic_json(_maintenance_journal_path(store), {"schema": "minis.event-maintenance.v1", "operation": "compact",
                       "active_backup": str(backup), "previous_manifest": manifest, "new_archive": str(archive), "started_at": now_iso()})
    _atomic_bytes(archive, prefix); _atomic_bytes(store.events_path, suffix)
    manifest.setdefault("archives", []).append({"file": name, "event_count": cut, "sha256": _sha_bytes(prefix), "created_at": now_iso()})
    manifest["active_segment"] = _active_metadata(store.events_path)
    manifest["updated_at"] = now_iso(); store._atomic_json(_manifest_path(store), manifest)
    index = build_event_index(store); _maintenance_journal_path(store).unlink()
    return {"status": "compacted", "archive": str(archive), "archived": cut, "active": retain_active,
            "total": index["event_count"], "archive_hash": _sha_bytes(prefix)}
