from __future__ import annotations

"""Bounded narrative model checking inspired by Yarn Spinner Story Solver.

The solver explores only explicit storylet effects. It does not pretend to
prove reachability for unconstrained prose or arbitrary player free input.
"""

from collections import deque
from typing import Any

from .canonical import deep_copy, refresh_state_hash, sha256_json
from .delta import apply_operations
from .storylets import available_storylets


def _exit_targets(storylet: dict[str, Any]) -> list[str]:
    raw = storylet.get("next_storylets", storylet.get("exits", []))
    if isinstance(raw, str): return [raw]
    if isinstance(raw, list): return [str(x) for x in raw if isinstance(x, (str, int))]
    return []


def _apply_storylet(state: dict[str, Any], storylet: dict[str, Any]) -> dict[str, Any] | None:
    operations = storylet.get("effects", storylet.get("operations", []))
    if not isinstance(operations, list): return None
    try:
        next_state = apply_operations(state, operations, source="system") if operations else deep_copy(state)
    except Exception:
        return None
    sid = str(storylet.get("id")); completed = set(next_state.get("metadata", {}).get("solver_completed_storylets", [])); completed.add(sid)
    next_state.setdefault("metadata", {})["solver_completed_storylets"] = sorted(completed)
    next_state["metadata"]["solver_last_storylet"] = sid
    return refresh_state_hash(next_state)


def solve_storylets(state: dict[str, Any], *, actor_id: str | None = None, max_depth: int = 12, max_states: int = 2000) -> dict[str, Any]:
    definitions = {str(s.get("id")): s for s in state.get("storylets", {}).get("active", []) if isinstance(s, dict) and s.get("id")}
    declared_edges = [(sid, target) for sid, item in definitions.items() for target in _exit_targets(item)]
    issues: list[dict[str, Any]] = []
    for source, target in declared_edges:
        if target not in definitions: issues.append({"code": "BROKEN_STORYLET_TARGET", "storylet_id": source, "target": target})
    queue = deque([(state, 0, [])]); seen = {state.get("state_hash") or sha256_json(state)}; reachable: set[str] = set(); terminal_paths = []; soft_locks = []; truncated = False
    while queue:
        current, depth, path = queue.popleft()
        available = available_storylets(current, actor_id=actor_id)
        if not available:
            open_threads = current.get("threads", {}).get("open", [])
            terminal = not open_threads or bool(current.get("metadata", {}).get("story_complete"))
            item = {"path": path, "open_threads": [x.get("id", x) if isinstance(x, dict) else x for x in open_threads]}
            (terminal_paths if terminal else soft_locks).append(item)
            continue
        if depth >= max_depth:
            truncated = True; continue
        for storylet in available:
            sid = str(storylet["id"]); reachable.add(sid); next_state = _apply_storylet(current, storylet)
            if next_state is None:
                issues.append({"code": "INVALID_STORYLET_EFFECT", "storylet_id": sid}); continue
            digest = next_state.get("state_hash") or sha256_json(next_state)
            if digest not in seen and len(seen) < max_states:
                seen.add(digest); queue.append((next_state, depth + 1, path + [sid]))
            elif len(seen) >= max_states: truncated = True
    unreachable = sorted(set(definitions) - reachable)
    issues.extend({"code": "UNREACHABLE_STORYLET", "storylet_id": sid} for sid in unreachable)
    issues.extend({"code": "SOFT_LOCK", **item} for item in soft_locks)
    report = {"schema": "minis.story-solver-report.v1", "scope": "explicit_storylet_effects_only",
              "storylet_count": len(definitions), "reachable": sorted(reachable), "unreachable": unreachable,
              "declared_edges": [{"source": a, "target": b} for a, b in declared_edges],
              "explored_states": len(seen), "terminal_paths": terminal_paths[:50], "soft_locks": soft_locks[:50],
              "truncated": truncated, "limits": {"max_depth": max_depth, "max_states": max_states},
              "issues": issues, "status": "pass" if not issues and not truncated else ("incomplete" if truncated and not issues else "fail")}
    report["report_hash"] = sha256_json(report); return report
