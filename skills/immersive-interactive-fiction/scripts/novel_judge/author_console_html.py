from __future__ import annotations

"""Self-contained HTML author console generated from deterministic report data."""

from pathlib import Path
from typing import Any
import html
import json

from .author_console import author_console_report


def render_author_console_html(report: dict[str, Any]) -> str:
    data = html.escape(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    blockers = report.get("blockers", [])
    cards = [
        ("狀態", report.get("status")), ("Revision", report.get("head", {}).get("revision")),
        ("Event log", report.get("event_log", {}).get("status")), ("Random events", report.get("random_events", {}).get("mode")),
        ("Suggestions", report.get("random_events", {}).get("noncanonical_audit_records")), ("Projection", report.get("projection", {}).get("status")),
        ("Pending journal", report.get("journal", {}).get("pending")), ("Blockers", len(blockers)),
    ]
    card_html = "".join(f'<div class="card"><b>{html.escape(str(k))}</b><span>{html.escape(str(v))}</span></div>' for k, v in cards)
    blocker_html = "".join(f"<li>{html.escape(str(x))}</li>" for x in blockers) or "<li>無</li>"
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Novel OS Author Console</title><style>
:root{{--bg:#101319;--panel:#1a202b;--text:#edf2f7;--muted:#9ba8b7;--ok:#66d9a6;--bad:#ff7b7b;--line:#2a3342}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Noto Sans TC",sans-serif}}main{{max-width:980px;margin:auto;padding:24px}}h1{{font-size:24px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}.card,section{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}}.card{{display:flex;flex-direction:column;gap:8px}}.card span{{font-size:20px}}section{{margin-top:16px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted);font-size:12px}}.pass{{color:var(--ok)}}.blocked{{color:var(--bad)}}</style></head><body><main><h1>Novel OS Author Console</h1><p>Project <code>{html.escape(str(report.get("project_id")))}</code> · Branch <code>{html.escape(str(report.get("branch_id")))}</code></p><div class="grid">{card_html}</div><section><h2>Blockers</h2><ul>{blocker_html}</ul></section><section><details><summary>完整 JSON 報告</summary><pre>{data}</pre></details></section></main></body></html>'''


def write_author_console_html(store: Any, output: str | Path, *, parent_store: Any | None = None,
                              project_root: str | Path | None = None) -> dict[str, Any]:
    report = author_console_report(store, parent_store=parent_store, project_root=project_root)
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(render_author_console_html(report), encoding="utf-8")
    return {"status": report["status"], "path": str(path), "blockers": report["blockers"]}
