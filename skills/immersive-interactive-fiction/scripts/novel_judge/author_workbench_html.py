from __future__ import annotations
import html
import json


def render_workbench_html(r):
    def esc(value): return html.escape(str(value))
    head = r.get("head", {}); inv = r.get("semantic_invariants", {}); quality = r.get("quality", {})
    metrics = quality.get("metrics", {}); readiness = r.get("readiness", {})
    timeline = "".join(
        f"<tr><td>{esc(x.get('turn_id'))}</td><td>{esc(x.get('scene_id'))}</td>"
        f"<td>{esc(x.get('action_type'))}</td><td>{'✓' if x.get('gate_authorized') else '—'}</td>"
        f"<td><code>{esc(str(x.get('state_hash',''))[-12:])}</code></td></tr>"
        for x in reversed(r.get("timeline", []))
    )
    actors = "".join(f"<div class=entity><b>{esc(x.get('id'))}</b><span>{esc(x.get('location'))}</span></div>" for x in r.get("actors", []))
    threads = "".join(f"<li><b>{esc(x.get('id'))}</b> · {esc(x.get('status'))}<br><small>{esc(x.get('question'))}</small></li>" for x in r.get("threads", {}).get("open", []))
    gates = "".join(f"<span class=chip>{esc(x.get('gate_type'))} {esc(x.get('verdict'))}</span>" for x in r.get("gates", []))
    issues = "".join(f"<li class={esc(str(x.get('severity')).lower())}><b>{esc(x.get('code'))}</b> · {esc(x.get('path'))}<br><small>{esc(x.get('minimal_repair'))}</small></li>" for x in inv.get("issues", []))
    generation = ", ".join(readiness.get("generation_blockers", [])) or "無"
    commands = ", ".join(readiness.get("command_blockers", [])) or "無"
    warnings = ", ".join(readiness.get("warnings", [])) or "無"
    embedded = json.dumps(r, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
    full = html.escape(json.dumps(r, ensure_ascii=False, sort_keys=True, indent=2))
    command_enabled = bool(r.get("actions", {}).get("enabled"))
    resume = r.get("resume") or {}
    now = resume.get("now") or {}
    freeze_label = "已凍結" if resume.get("frozen") else "進行中"
    next_action = resume.get("next_action") or "尚未建立恢復卡"
    last_summary = now.get("last_summary") or "—"
    studio = r.get("scene_studio") or {}
    preview = studio.get("context_preview") or {}
    used = preview.get("used_source_ids") or []
    selected = preview.get("selected_source_ids") or []
    used_label = ", ".join(esc(x) for x in used[:8]) or "尚無 used sources"
    selected_label = ", ".join(esc(x) for x in selected[:8]) or "尚無 selected sources"
    scene_rows = "".join(
        f"<tr><td>{esc(x.get('id'))}</td><td>{esc(x.get('kind'))}</td>"
        f"<td>{'HEAD' if x.get('is_head') else '—'}</td>"
        f"<td>{esc(x.get('chars'))}</td><td><code>{esc(x.get('path'))}</code></td></tr>"
        for x in (studio.get("scenes") or [])[:12]
    ) or "<tr><td colspan=5>尚無場景檔</td></tr>"
    draft_rows = "".join(
        f"<li><b>{esc(x.get('draft_id'))}</b> · {esc(x.get('status'))}"
        f"<br><small>{esc(x.get('path'))} · {esc(x.get('updated_at'))}</small></li>"
        for x in (studio.get("drafts") or [])[:8]
    ) or "<li>沒有未決草稿</li>"
    accepted_rows = "".join(
        f"<li><b>{esc(x.get('draft_id'))}</b> · 候選 {esc(x.get('command_id') or 'sidecar')}"
        f"<br><small>{esc(x.get('accepted_at'))}</small></li>"
        for x in (studio.get("accepted") or [])[:8]
    ) or "<li>沒有已接受側車</li>"
    studio_class = "blocked" if studio.get("frozen") or not studio.get("accept_enabled") else ""
    studio_policy = "凍結：只可預覽，草稿與接受已停用" if studio.get("frozen") else "未凍結：草稿→對稿→接受只建候選／側車，不改正典"
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Novel OS 作者工作台</title>
<style>:root{{--bg:#0c111b;--p:#151d2b;--p2:#1b2638;--tx:#edf4ff;--mu:#9fb0c7;--ac:#7dd3fc;--ok:#6ee7b7;--bad:#fb7185;--warn:#fbbf24}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font-family:-apple-system,"Noto Sans TC",sans-serif}}header{{padding:26px 5vw;background:linear-gradient(135deg,#15223a,#0e1726);border-bottom:1px solid #263750}}main{{padding:20px 5vw 60px;max-width:1400px;margin:auto}}h1{{margin:0 0 7px}}.sub,small{{color:var(--mu)}}#freshness{{padding:13px 5vw;font-weight:700}}.fresh{{background:#10352d;color:var(--ok)}}.stale{{background:#4a1821;color:#ffd8de}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:18px 0}}.card,section{{background:var(--p);border:1px solid #263750;border-radius:14px;padding:15px}}.card b{{display:block;color:var(--mu);font-size:12px}}.card strong{{font-size:22px}}section{{margin:14px 0}}.cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;padding:9px;border-bottom:1px solid #263750;font-size:13px}}.entity{{display:flex;justify-content:space-between;background:var(--p2);padding:10px;border-radius:9px;margin:7px 0}}.chip{{display:inline-block;padding:6px 9px;margin:3px;border-radius:999px;background:#17324a;color:var(--ac);font-size:12px}}li{{margin:9px 0}}.p0{{color:var(--bad)}}.p1{{color:var(--warn)}}code{{color:var(--ac)}}details pre{{white-space:pre-wrap;color:var(--mu);font-size:11px}}.blocked{{border-color:var(--bad)}}@media(max-width:760px){{.cols{{grid-template-columns:1fr}}}}</style></head>
<body><header><h1>Novel OS 作者工作台</h1><div class=sub>唯讀投影 · 所有控制動作只建立 command request，不直接修改正典</div></header>
<div id="freshness" class="fresh">正在核對 live HEAD…</div><main>
<section id="resume"><h2>恢復卡</h2><p><b>狀態：</b>{esc(freeze_label)} · HEAD {esc(now.get('head_turn') or head.get('last_turn_id'))}</p><p><b>上次摘要：</b>{esc(last_summary)}</p><p><b>下一步：</b>{esc(next_action)}</p></section>
<section id="scene-studio" class="{studio_class}"><h2>Scene Studio</h2><p><b>政策：</b>{esc(studio_policy)}</p><p><b>場景數：</b>{esc(studio.get('scene_count') or 0)} · <b>草稿：</b>{esc(studio.get('draft_count') or 0)} · <b>已接受側車：</b>{esc(studio.get('accepted_count') or 0)}</p><p><b>Context 預覽：</b>{esc(preview.get('status') or 'unavailable')} · actor {esc(preview.get('actor_id'))} · used sources {used_label}</p><p><b>selected sources：</b>{selected_label}</p><table><thead><tr><th>場景</th><th>類型</th><th>HEAD</th><th>字數</th><th>路徑</th></tr></thead><tbody>{scene_rows}</tbody></table><div class=cols><section><h3>草稿</h3><ul>{draft_rows}</ul></section><section><h3>已接受（非正典）</h3><ul>{accepted_rows}</ul></section></div><p class=sub>接受不會改正文。凍結專案請用 CLI 預覽／書稿複本；未凍結才可 draft-scene／diff-scene／accept-scene。</p></section>
<div class=grid><div class=card><b>HEAD</b><strong>{esc(head.get('scene_id') or head.get('last_turn_id'))}</strong></div><div class=card><b>Revision</b><strong>{esc(head.get('revision'))}</strong></div><div class=card><b>Events</b><strong>{esc(r.get('source',{}).get('event_count'))}</strong></div><div class=card><b>Kernel</b><strong>{esc(r.get('health',{}).get('status'))}</strong></div><div class=card><b>Readiness</b><strong>{esc(readiness.get('status'))}</strong></div><div class=card><b>Invariant debt</b><strong>{len(inv.get('issues',[]))}</strong></div></div>
<section class="{'blocked' if readiness.get('status') != 'ready' else ''}"><h2>Project Readiness</h2><p><b>生成阻擋：</b>{esc(generation)}</p><p><b>命令阻擋：</b>{esc(commands)}</p><p><b>警告：</b>{esc(warnings)}</p></section>
<section><h2>最新 Gate</h2>{gates}</section><div class=cols><section><h2>角色位置</h2>{actors}</section><section><h2>Open Threads</h2><ul>{threads}</ul></section></div><section><h2>事件時間線</h2><table><thead><tr><th>Turn</th><th>Scene</th><th>事件</th><th>Gate</th><th>State</th></tr></thead><tbody>{timeline}</tbody></table></section><section><h2>Semantic invariant migration debt</h2><ul>{issues}</ul></section>
<section id="commands" class="{'blocked' if not command_enabled else ''}"><h2>受控命令</h2><p>狀態：<b>{'可建立 request' if command_enabled else '已停用'}</b>。工作台只寫 command request；執行器仍須重新核對 source state 並走 Gate／adapter。</p></section><section><details><summary>完整投影 JSON</summary><pre>{full}</pre></details></section></main>
<script id="embedded" type="application/json">{embedded}</script><script>(async()=>{{const embedded=JSON.parse(document.getElementById('embedded').textContent);const bar=document.getElementById('freshness');try{{const live=await (await fetch('../runtime-head.json',{{cache:'no-store'}})).json();const src=embedded.source||{{}};const ok=src.state_hash===live.state_hash&&src.event_head===live.event_head&&src.runtime_head_hash===live.head_hash;if(ok){{bar.className='fresh';bar.textContent='FRESH · 工作台與 live HEAD '+String(live.last_turn_id||'')+' 一致';}}else{{bar.className='stale';bar.textContent='STALE · 工作台來源已落後 live HEAD；所有命令必須停用並先重建投影';document.getElementById('commands').className='blocked';}}}}catch(e){{bar.className='stale';bar.textContent='UNVERIFIED · 無法讀取 live runtime HEAD；不得從此工作台建立命令';document.getElementById('commands').className='blocked';}}}})();</script></body></html>'''
