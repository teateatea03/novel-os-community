from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def deep_copy(value: Any) -> Any:
    return copy.deepcopy(value)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_json(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def state_hash(state: dict[str, Any]) -> str:
    value = deep_copy(state)
    value.pop("state_hash", None)
    return sha256_json(value)


def stable_id(prefix: str, *parts: Any) -> str:
    raw = "\x1f".join(canonical_json(x) for x in parts)
    return f"{prefix}-{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def refresh_state_hash(state: dict[str, Any]) -> dict[str, Any]:
    state["state_hash"] = state_hash(state)
    return state
