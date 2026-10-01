#!/usr/bin/env python3
"""Evidence-oriented chapter gate with authority layers.

Legacy lint checks remain. High-confidence Narrative QA is added. Editorial
smells are warnings only. This still does not claim a full developmental edit.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

# Allow importing novel_judge from the interactive skill package.
ROOT = Path(__file__).resolve().parents[2]
NJ = ROOT / 'immersive-interactive-fiction' / 'scripts'
if str(NJ) not in sys.path:
    sys.path.insert(0, str(NJ))

from novel_judge.authority_layers import build_authority_report, normalize_finding  # type: ignore
from novel_judge.narrative_qa import inspect_prose  # type: ignore


def issue(out, severity, cat, claim, a, b, fix, *, code=None, layer='EDITORIAL_DIAGNOSIS', confidence='medium', blocks=False):
    item = {
        'severity': severity,
        'category': cat,
        'claim': claim,
        'evidence_a': a,
        'evidence_b': b,
        'minimal_fix': fix,
        'code': code or cat.upper().replace(' ', '_')[:40],
        'layer': layer,
        'confidence': confidence,
        'blocks_commit': blocks,
    }
    out.append(item)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--chapter', required=True)
    a = p.parse_args()
    root = Path(a.root)
    path = root / 'chapters' / f'{a.chapter}.md'
    if not path.exists():
        raise SystemExit(f'chapter not found: {path}')
    text = path.read_text(encoding='utf-8', errors='replace')
    out = []
    if re.search(r'\[(?:TODO|TBD|INSERT|META)\]', text, re.I):
        issue(out, 'P1', 'Narrative & Style', '未清除 meta 標記', str(path), 'chapter text', '刪除或移入計畫檔', code='META_MARK', layer='NARRATIVE_QA', confidence='high')
    if len(text.strip()) < 400:
        issue(out, 'P2', 'Narrative & Style', '章節過短；可能不是完整場景單元', str(path), f'{len(text)} chars', '確認是片段或補足場景', code='CHAPTER_TOO_SHORT')
    style = (root / 'style-sheet.md').read_text(encoding='utf-8', errors='ignore') if (root / 'style-sheet.md').exists() else ''
    if re.search(r'\b(I|we|my|our)\b', text) and 'POV' not in style:
        issue(out, 'P2', 'Narrative & Style', '可能出現未登記第一人稱 POV', str(path), 'style-sheet.md', '核對 POV 契約', code='POV_CONTRACT_HINT', confidence='low')
    ledger = root / 'reader-ledger.md'
    if not ledger.exists():
        issue(out, 'P1', 'Timeline & Plot Logic', '缺少讀者資訊帳本', str(path), 'reader-ledger.md absent', '建立帳本並回寫本章資訊投放', code='MISSING_READER_LEDGER')
    for required, cat in [('timeline.md', 'Timeline & Plot Logic'), ('current-state.md', 'Factual & Detail'), ('knowledge-matrix.md', 'Characterization')]:
        if not (root / required).exists():
            issue(out, 'P1', cat, f'缺少核心帳本：{required}', str(path), required, '初始化或補回帳本', code='MISSING_LEDGER')
    s = [x.strip() for x in re.split(r'[。！？!?]\s*', text) if len(x.strip()) > 12]
    for x, y in zip(s, s[1:]):
        if x == y:
            issue(out, 'P2', 'Narrative & Style', '相鄰句重複', x, y, '刪除或改變功能', code='ADJACENT_DUP', layer='NARRATIVE_QA', confidence='high')
            break

    qa = inspect_prose(text)
    for item in qa.get('findings') or []:
        out.append({
            'severity': item.get('severity'),
            'category': 'Narrative QA',
            'claim': item.get('claim'),
            'evidence_a': item.get('span') or item.get('evidence'),
            'evidence_b': item.get('minimal_fix'),
            'minimal_fix': item.get('minimal_fix'),
            'code': item.get('code'),
            'layer': item.get('layer') or 'NARRATIVE_QA',
            'confidence': item.get('confidence'),
            'blocks_commit': item.get('blocks_commit'),
        })

    findings = [normalize_finding({
        'layer': i.get('layer') or 'EDITORIAL_DIAGNOSIS',
        'code': i.get('code'),
        'severity': i.get('severity'),
        'confidence': i.get('confidence') or 'medium',
        'claim': i.get('claim'),
        'evidence': [i.get('evidence_a'), i.get('evidence_b')],
        'minimal_fix': i.get('minimal_fix'),
        'blocks_commit': i.get('blocks_commit', False),
    }) for i in out]
    authority = build_authority_report(findings=findings, source='chapter_gate', subject={'chapter': a.chapter, 'path': str(path)})
    status = 'FAIL' if any(x.get('severity') == 'P0' for x in out) else ('WARN' if out else 'PASS')
    report = {
        'schema': 'minis.novel-chapter-gate.v2',
        'chapter': a.chapter,
        'status': status,
        'issues': out,
        'authority': authority,
        'may_commit': authority['commit']['may_commit'],
        'note': 'Heuristic + Narrative QA. Not a full developmental edit. Author may override non-P0 with recorded decision. Behavior Prediction Lock remains separate.',
        'claims': {
            'literary_quality_judged': False,
            'whole_manuscript_edit': False,
            'reader_preference_judged': False,
        },
    }
    d = root / 'gates'
    d.mkdir(exist_ok=True)
    dest = d / f'{a.chapter}-gate.json'
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok': True, 'status': status, 'issues': len(out), 'may_commit': report['may_commit'], 'output': str(dest)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
