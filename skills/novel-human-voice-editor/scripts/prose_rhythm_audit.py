#!/usr/bin/env python3
"""Chinese-aware prose rhythm audit.

A deterministic editorial diagnostic inspired by sentence-length visualizers
(Writhm, Cadence, Musical Text) and line-editing read-aloud practice. It marks
patterns for review; it never assigns quality, authorship, or commit verdicts.
"""
from __future__ import annotations
import argparse, html, json, math, re
from collections import Counter
from pathlib import Path

SCHEMA = "minis.prose-rhythm-audit.v1"
END = re.compile(r"(?<=[。！？!?…])(?:[」』）】]*)(?:\s+|$)")
CJK = re.compile(r"[\u3400-\u9fff]")
WORD = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?|[\u3400-\u9fff]")
DIALOGUE = re.compile(r"[「『][^」』]{1,120}[」』]")
TAG = re.compile(r"(?:他|她|我|你|[\u3400-\u9fff]{1,4})(?:說|問|答|回|道|喊|叫|低聲說|開口)")
ACTION = re.compile(r"(?:走|跑|轉|抬|伸|拿|放|坐|站|看|聽|摸|拉|推|關|開|靠|躲|停|退|進|出|咬|抓|笑|哭|嘆|點頭|搖頭|望|盯|彎|起身|回頭|抬頭|低頭)")
SIMULTANEOUS = re.compile(r"(?:一邊.{0,25}一邊|(?:走|跑|轉|抬|伸|拿|放|坐|站|看|聽|摸|拉|推|關|開|靠|躲|停|退|進|出|咬|抓|笑|哭|嘆|點頭|搖頭|望|盯|彎|起身|回頭|抬頭|低頭)著.{0,28}(?:走|跑|轉|抬|伸|拿|放|坐|站|看|聽|摸|拉|推|關|開|靠|躲|停|退|進|出|咬|抓|笑|哭|嘆|點頭|搖頭|望|盯|彎|起身|回頭|抬頭|低頭))")

def clean(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    return re.sub(r"(?m)^\s*>.*$", "", text)

def split_sentences(text: str):
    items=[]; start=0
    for m in re.finditer(r"[。！？!?…]+[」』）】]*", text):
        end=m.end(); raw=text[start:end]
        if raw.strip(): items.append((start,end,raw.strip()))
        start=end
    if text[start:].strip():
        lead=len(text[start:])-len(text[start:].lstrip())
        items.append((start+lead,len(text),text[start:].strip()))
    return items

def units(s: str) -> int:
    # CJK characters are usable visual rhythm units; contiguous Latin words count once.
    return len(WORD.findall(s))

def opener(s: str) -> str:
    s=re.sub(r"^[「『（(\s]+", "", s)
    m=re.search(r"[\u3400-\u9fffA-Za-z]+", s)
    return (m.group(0)[:3] if m else "")

def cv(vals):
    if len(vals)<2 or not sum(vals): return 0.0
    mean=sum(vals)/len(vals)
    return math.sqrt(sum((v-mean)**2 for v in vals)/len(vals))/mean

def cls(n, mean):
    if n <= max(5, mean*.62): return "short"
    if n >= mean*1.45: return "long"
    return "medium"

def issue(code, severity, idxs, text, note):
    return {"code":code,"severity":severity,"sentence_indices":[i+1 for i in idxs],
            "loci":[{"sentence":i+1,"excerpt":text[i][:100]} for i in idxs],"note":note}

def analyze(raw: str, source="text"):
    text=clean(raw); ss=split_sentences(text); rows=[]
    for i,(a,b,s) in enumerate(ss):
        rows.append({"index":i+1,"start":a,"end":b,"text":s,"units":units(s),
                     "opener":opener(s),"dialogue":bool(DIALOGUE.search(s)),
                     "action_hits":ACTION.findall(s),"simultaneity_candidate":bool(SIMULTANEOUS.search(s))})
    lens=[r['units'] for r in rows]; mean=(sum(lens)/len(lens)) if lens else 0
    for r in rows: r['band']=cls(r['units'],mean) if mean else 'medium'
    issues=[]
    # Runs are review flags, not instructions to randomize prose.
    for key, code, note in [('band','MONOTONE_LENGTH_RUN','連續相近長度可能形成等速；確認是否符合此處壓力與視角。'),
                            ('opener','REPEATED_OPENER_RUN','連續同起句可能是模板感；確認是否為刻意重複或角色聲音。')]:
        i=0
        while i<len(rows):
            j=i+1
            while j<len(rows) and rows[j][key] and rows[j][key]==rows[i][key]: j+=1
            if j-i>=4: issues.append(issue(code,'review',list(range(i,j)),[r['text'] for r in rows],note))
            i=j
    for i,r in enumerate(rows):
        # This does not claim grammatical impossibility; it asks for sequencing review.
        if len(r['action_hits'])>=4:
            issues.append(issue('ACTION_STACK','review',[i],[x['text'] for x in rows],
                '同一句有多個動作詞；確認讀者能按順序看見，必要時拆成 beats。'))
        if r['simultaneity_candidate']:
            issues.append(issue('POSSIBLE_FALSE_SIMULTANEITY','review',[i],[x['text'] for x in rows],
                '含可能的同時動作結構；確認不是把應先後發生的動作壓成同一拍。'))
    i=0
    while i<len(rows):
        j=i
        while j<len(rows) and rows[j]['band']=='short': j+=1
        if j-i>=4:
            issues.append(issue('SHORT_BEAT_RUN','review',list(range(i,j)),[r['text'] for r in rows],
                '短句連續出現；確認每一拍都有壓力、焦點或角色認知功能。'))
        i=max(i+1,j)
    # dialogue lines followed repeatedly by explicit speech tags can create a stutter.
    tag_idxs=[i for i,r in enumerate(rows) if r['dialogue'] and TAG.search(r['text'])]
    for a,b in zip(tag_idxs,tag_idxs[1:]):
        if b==a+1:
            chain=[a,b]; k=b+1
            while k in tag_idxs: chain.append(k);k+=1
            if len(chain)>=3:
                issues.append(issue('DIALOGUE_TAG_STUTTER','review',chain,[r['text'] for r in rows],
                    '連續對白均以顯式 tag 收束；確認是否需要改以 POV、動作或位置維持辨識。'))
            break
    band_counts=Counter(r['band'] for r in rows)
    return {"schema":SCHEMA,"source":source,"summary":{"sentences":len(rows),"mean_units":round(mean,1),"length_cv":round(cv(lens),2),"bands":dict(band_counts),"issue_count":len(issues)},"sentences":rows,"issues":issues,
            "limits":["中文以字／拉丁詞作視覺節奏單位，不等同音步或文學品質。","所有訊號需朗讀、視角、人物聲音與場景功能複核。","此為 EDITORIAL_DIAGNOSIS；不可作正典提交 Gate 或 AI 作者判定。"]}

def report_html(data):
    rows=data['sentences']; maxu=max([r['units'] for r in rows] or [1])
    colors={'short':'#9bd3ae','medium':'#f5cf78','long':'#ed9a92'}
    bars=''.join(f'<a title="{html.escape(r["text"])}" href="#s{r["index"]}" class="bar {r["band"]}" style="height:{max(12,round(r["units"]/maxu*180))}px">{r["index"]}</a>' for r in rows)
    sentence_rows=''.join(f'<li id="s{r["index"]}"><b>{r["index"]}. {r["units"]} units · {r["band"]}</b>　{html.escape(r["text"])}</li>' for r in rows)
    issue_rows=''.join(f'<li><b>{x["code"]}</b> — {html.escape(x["note"])}<br>{"; ".join("S"+str(n) for n in x["sentence_indices"])}</li>' for x in data['issues']) or '<li>沒有觸發啟發式訊號；仍應做朗讀複核。</li>'
    return f'''<!doctype html><meta charset="utf-8"><title>Prose Rhythm Audit</title><style>body{{font:16px -apple-system,system-ui;max-width:980px;margin:28px auto;padding:0 16px;line-height:1.65;color:#222}}.bars{{height:225px;border-bottom:2px solid #777;display:flex;align-items:end;gap:3px;overflow-x:auto;padding:8px}}.bar{{min-width:24px;color:#222;text-decoration:none;text-align:center;padding:2px;font-size:11px}}.short{{background:{colors['short']}}}.medium{{background:{colors['medium']}}}.long{{background:{colors['long']}}}li{{margin:8px 0}}code{{background:#eee;padding:2px 4px}}</style><h1>Prose Rhythm Audit</h1><p>句數 {data['summary']['sentences']}；平均單位 {data['summary']['mean_units']}；長度變異 CV {data['summary']['length_cv']}。綠＝短、黃＝中、紅＝長。這是視覺診斷，不是品質分數。</p><div class="bars">{bars}</div><h2>需複核的節奏位置</h2><ul>{issue_rows}</ul><h2>句子地圖</h2><ol>{sentence_rows}</ol><h2>限制</h2><ul>{''.join('<li>'+html.escape(x)+'</li>' for x in data['limits'])}</ul>'''

def main():
    p=argparse.ArgumentParser(); p.add_argument('--file',required=True);p.add_argument('--format',choices=['json','html'],default='json');p.add_argument('--output')
    a=p.parse_args(); data=analyze(Path(a.file).read_text(encoding='utf-8',errors='replace'),a.file)
    result=json.dumps(data,ensure_ascii=False,indent=2) if a.format=='json' else report_html(data)
    if a.output: Path(a.output).write_text(result,encoding='utf-8')
    else: print(result)
if __name__=='__main__': main()
