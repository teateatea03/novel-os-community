#!/usr/bin/env python3
"""Regression tests for unfinished-novel completion tooling."""
from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(argv):
    return subprocess.run([sys.executable, *map(str, argv)], text=True, capture_output=True)


def main() -> int:
    here = Path(__file__).resolve().parent
    skill = here.parent
    init = here / "init_completion_project.py"
    gate = here / "completion_gate.py"
    ingest = here / "source_ingest.py"
    compare = here / "compare_source_versions.py"
    provenance = here / "provenance_report.py"
    feasibility = here / "feasibility_report.py"
    results = []
    with tempfile.TemporaryDirectory(prefix="unfinished-completion-regression-") as td:
        base = Path(td); projects = base / "projects"
        r = run([init, "--title", "Completion Regression", "--slug", "fixture", "--root", projects])
        results.append({"case": "initialize", "pass": r.returncode == 0})
        if r.returncode:
            print(json.dumps({"ok": False, "results": results, "error": r.stderr or r.stdout}, ensure_ascii=False, indent=2)); return 1
        project = projects / "fixture"

        r = run([gate, "--root", project, "--phase", "intake"])
        results.append({"case": "clean-intake-gate", "pass": r.returncode == 0})

        intent = project / "author-intent-ledger.md"
        original = intent.read_text(encoding="utf-8")
        intent.write_text(original + "\n作者一定會採用唯一原意。\n", encoding="utf-8")
        r = run([gate, "--root", project, "--phase", "evidence"])
        results.append({"case": "reject-author-intent-overclaim", "pass": r.returncode != 0})
        intent.write_text(original, encoding="utf-8")

        state_path = project / "completion-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update({"completion_mode": "textual-continuation", "branch_id": "branch-text", "phase": "branch"})
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        hypo = project / "hypothesis-ledger.md"
        hypo.write_text(hypo.read_text(encoding="utf-8") + "\n| branch-text | textual-continuation | 依正文推演 | E01 | 無 | 無 | 觀察橋樑 | 回收F01 | 保留角色弧 | MEDIUM | [PROPOSAL] |\n", encoding="utf-8")
        r = run([gate, "--root", project, "--phase", "draft"])
        results.append({"case": "selected-branch-draft-gate", "pass": r.returncode == 0})

        state["purpose"] = "public-noncommercial"; state["rights_status"] = "unknown"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        r = run([gate, "--root", project, "--phase", "publication"])
        results.append({"case": "reject-unknown-rights-publication", "pass": r.returncode != 0})
        state["purpose"] = "private-only"; state["rights_status"] = "private-only"
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        src_a = base / "source-a.txt"; src_b = base / "source-b.txt"
        src_a.write_text("chapter one\nold ending\n", encoding="utf-8")
        src_b.write_text("chapter one\nnew ending\n", encoding="utf-8")
        for sid, src in (("source-a", src_a), ("source-b", src_b)):
            r = run([ingest, "--root", project, "register", "--source-id", sid, "--source-path", src, "--type", "unfinished-manuscript", "--permission-status", "provided-by-user", "--completeness", "complete", "--provided-by-user"])
            results.append({"case": f"register-{sid}", "pass": r.returncode == 0})
        r = run([ingest, "--root", project, "validate"])
        results.append({"case": "validate-source-manifest", "pass": r.returncode == 0})
        r = run([compare, "--root", project, "--source-a", "source-a", "--source-b", "source-b"])
        results.append({"case": "compare-source-versions", "pass": r.returncode == 0})
        r = run([provenance, "--root", project])
        results.append({"case": "empty-provenance-report", "pass": r.returncode == 0})
        r = run([feasibility, "--root", project])
        results.append({"case": "generate-feasibility-report", "pass": r.returncode == 0})
        r = run([init, "--title", "Completion Regression", "--slug", "fixture-graph", "--root", projects])
        graph_project = projects / "fixture-graph"
        results.append({"case": "initialize-graph-fixture", "pass": r.returncode == 0})
        if r.returncode == 0:
            r = run([ingest, "--root", graph_project, "register", "--source-id", "source-graph", "--source-url", "https://example.invalid/source", "--permission-status", "provided-by-user", "--completeness", "excerpt"])
            results.append({"case": "register-graph-source", "pass": r.returncode == 0})
            evidence = graph_project / "evidence-ledger.md"
            evidence.write_text(evidence.read_text(encoding="utf-8") + "\n| E01 | 核心主張 | AUTHOR-NOTE | source-graph | notes | 支持 | 無 | branch | MEDIUM | [DRAFT] |\n", encoding="utf-8")
            sync = here / "sync_graph.py"
            r = run([sync, "--root", graph_project])
            results.append({"case": "sync-completion-graph", "pass": r.returncode == 0})

    summary = {"schema": "minis.unfinished-completion-regression.v1", "passed": sum(x["pass"] for x in results), "total": len(results), "results": results}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
