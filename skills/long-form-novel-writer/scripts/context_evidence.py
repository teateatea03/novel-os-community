"""Byte fingerprints and character-level inclusion evidence, never semantic coverage."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath

SCHEMA = "minis.context-pack.v5"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text_hash(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def source_path(root: Path, name: str) -> Path:
    """Validate portable project-relative identities and reject existing symlinks."""
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("invalid source path")
    relative = PurePosixPath(name)
    if relative.as_posix() != name or relative.is_absolute() or any(p in (".", "..") for p in name.split("/")):
        raise ValueError("invalid source path")
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlink source is not supported")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("source outside project")
    return path


def source_record(chunk: dict) -> dict:
    return {key: chunk[key] for key in (
        "file", "start", "end", "score", "source_sha256", "excerpt_sha256")}


def _inclusion(start: int, end: int, limit: int) -> dict:
    included = max(0, min(end, limit) - start)
    total = end - start
    return {"status": "full" if included == total else ("partial" if included else "omitted"),
            "included_characters": included, "total_characters": total}


def assess_context(root: Path, pack_path: Path, context_text: str, included_chars: int) -> dict:
    """Validate v5 evidence against current sources and the exact prompt prefix.

    v4/absent sidecars remain usable but explicitly unverified. Unknown or corrupt
    evidence is invalid; callers must not invoke a model for stale/invalid packs.
    Offsets use Python Unicode characters, [start, end), not bytes or tokens.
    """
    if type(included_chars) is not int or not 0 <= included_chars <= len(context_text):
        raise ValueError("invalid context prefix length")
    result = {"schema": "minis.context-evidence.v1", "status": "missing",
              "scope": "character_inclusion_only", "sources": [],
              "pack_characters": len(context_text), "included_characters": included_chars,
              "omitted_characters": len(context_text) - included_chars,
              "included_text_sha256": text_hash(context_text[:included_chars])}
    try:
        pack_name = pack_path.absolute().relative_to(root.absolute()).as_posix()
        pack_path = source_path(root, pack_name)
        manifest_path = source_path(root, pack_path.with_suffix(".json").relative_to(root).as_posix())
    except (OSError, ValueError) as error:
        result.update(status="invalid", reason=str(error))
        return result
    if not pack_path.exists():
        return result
    if not manifest_path.exists():
        result["status"] = "invalid" if "- evidence_schema: " + SCHEMA in context_text.splitlines() else "legacy_unverified"
        result["reason"] = "manifest_missing"
        return result
    try:
        def reject_constant(value):
            raise ValueError("non-finite manifest number")
        def finite_float(value):
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("non-finite manifest number")
            return number
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"),
                              parse_constant=reject_constant, parse_float=finite_float)
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        if manifest.get("schema") == "minis.context-pack.v4":
            if "- evidence_schema: " + SCHEMA in context_text.splitlines():
                raise ValueError("v5 pack requires v5 manifest")
            result["status"] = "legacy_unverified"
            result["reason"] = "legacy_manifest_without_fingerprints"
            return result
        if manifest.get("schema") != SCHEMA:
            raise ValueError("unsupported manifest schema")
        if manifest.get("offset_unit") != "unicode_characters_half_open":
            raise ValueError("unsupported pack offset unit")
        if manifest.get("pack_sha256") != text_hash(context_text):
            result.update(status="stale", reason="pack_hash_mismatch")
            return result
        if not isinstance(manifest.get("sources"), list) or not isinstance(manifest.get("addressable_overflow"), list):
            raise ValueError("source collections must be arrays")
        summary = manifest.get("selection_summary")
        counts = ("ranked_chunks", "inline_chunks", "addressable_overflow_chunks", "unlisted_ranked_chunks")
        if (not isinstance(summary, dict)
                or any(type(summary.get(key)) is not int or summary[key] < 0 for key in counts)
                or summary["inline_chunks"] != len(manifest["sources"])
                or summary["addressable_overflow_chunks"] != len(manifest["addressable_overflow"])
                or summary["ranked_chunks"] != sum(summary[key] for key in counts[1:])):
            raise ValueError("invalid selection summary")
        result["selection_summary"] = {key: summary[key] for key in counts}
        result["selection_summary"]["scope"] = "ranked_chunks_only_not_semantic_coverage"
        previous_end = 0
        for inline, entries in ((True, manifest["sources"]), (False, manifest["addressable_overflow"])):
            for entry in entries:
                if not isinstance(entry, dict):
                    raise ValueError("source entry must be an object")
                name, start, end = entry["file"], entry["start"], entry["end"]
                if type(start) is not int or type(end) is not int or start < 1 or end < start:
                    raise ValueError("invalid source line range")
                for key in ("source_sha256", "excerpt_sha256"):
                    digest = entry.get(key)
                    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                        raise ValueError("invalid source fingerprint")
                item = {"file": name, "start": start, "end": end,
                        "source_sha256": entry["source_sha256"], "excerpt_sha256": entry["excerpt_sha256"],
                        "status": "verified", "placement": "inline" if inline else "addressable_overflow"}
                if inline:
                    a, b = entry["pack_start"], entry["pack_end"]
                    if type(a) is not int or type(b) is not int or not previous_end <= a <= b <= len(context_text):
                        raise ValueError("invalid or overlapping pack range")
                    previous_end = b
                    if text_hash(context_text[a:b]) != entry["excerpt_sha256"]:
                        raise ValueError("embedded excerpt hash mismatch")
                    item.update(pack_start=a, pack_end=b, inclusion=_inclusion(a, b, included_chars))
                else:
                    item["inclusion"] = {"status": "omitted", "included_characters": 0,
                                         "reason": "address_only_not_source_text"}
                path = source_path(root, name)
                try:
                    raw = path.read_bytes()
                    lines = raw.decode("utf-8").splitlines()
                    if sha256_bytes(raw) != entry["source_sha256"]:
                        item.update(status="stale", reason="source_hash_mismatch")
                    elif end > len(lines) or text_hash("\n".join(lines[start - 1:end])) != entry["excerpt_sha256"]:
                        item.update(status="stale", reason="source_range_mismatch")
                except FileNotFoundError:
                    item.update(status="missing", reason="source_missing")
                except (OSError, UnicodeError):
                    item.update(status="invalid", reason="source_unreadable")
                result["sources"].append(item)
        result["status"] = "verified" if all(s["status"] == "verified" for s in result["sources"]) else "stale"
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        result.update(status="invalid", reason=str(error))
    return result


def context_source_spans(root: Path, assessment: dict) -> dict:
    """Return internal evidence snapshots only for verified, included source text.

    Text uses the pack's splitlines/join normalization. Hashes bind original file
    bytes; ranges index normalized Unicode characters. Never serialize this text
    as an incidental metadata field. A changed second read fails closed.
    """
    if assessment.get("status") != "verified":
        return {}
    snapshots = {}
    for item in assessment["sources"]:
        count = item["inclusion"]["included_characters"]
        if item["placement"] != "inline" or not count:
            continue
        name = item["file"]
        if name not in snapshots:
            raw = source_path(root, name).read_bytes()
            if sha256_bytes(raw) != item["source_sha256"]:
                raise ValueError("context source changed during preparation: " + name)
            snapshots[name] = {"text": "\n".join(raw.decode("utf-8").splitlines()),
                               "sha256": item["source_sha256"], "ranges": []}
        snapshot = snapshots[name]
        if snapshot["sha256"] != item["source_sha256"]:
            raise ValueError("inconsistent source fingerprints: " + name)
        lines = snapshot["text"].split("\n")
        start = sum(len(line) + 1 for line in lines[:item["start"] - 1])
        snapshot["ranges"].append([start, start + count])
    return snapshots
