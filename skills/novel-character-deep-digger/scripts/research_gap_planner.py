#!/usr/bin/env python3
"""Read-only v2 gap triage. No network, no claims of research completion."""
import argparse
import json
from pathlib import Path

SCHEMA = 'minis.character-research-gap-plan.v1'
ROUTES = {'QUERY', 'BROWSE', 'CITATION_BACKWARD', 'CITATION_FORWARD',
          'PIVOT', 'CONTACT', 'ARCHIVE_REQUEST'}
REQUIRED = ['protocol.json', 'events.jsonl', 'candidates.jsonl',
            'artifacts.jsonl', 'claims.jsonl', 'reviews.jsonl']
MAX_BYTES = 32 * 1024 * 1024


def read_file(root, name, lines=False):
    path = root / name
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError('missing_or_external:' + name)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('input_too_large:' + name)
    try:
        text = path.read_text(encoding='utf-8')
        value = [json.loads(x) for x in text.splitlines() if x.strip()] if lines else json.loads(text)
    except (ValueError, UnicodeError):
        raise ValueError('malformed_json:' + name) from None
    if lines and any(not isinstance(x, dict) for x in value):
        raise ValueError('non_object_record:' + name)
    if not lines and not isinstance(value, dict):
        raise ValueError('non_object:' + name)
    return value


def records(value, field):
    if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
        raise ValueError('invalid_list:' + field)
    return value


def indexed(rows, key):
    out = {}
    for row in rows:
        ident = row.get(key)
        if not isinstance(ident, str) or not ident.strip() or ident in out:
            raise ValueError('missing_or_duplicate_id:' + key)
        out[ident] = row
    return out


def plan(root):
    root = Path(root).resolve()
    p = read_file(root, 'protocol.json')
    if p.get('schema') != 'minis.character-research-run.v2':
        raise ValueError('unsupported_schema')
    ev, ca, ar, cl, rv = [read_file(root, n, True) for n in REQUIRED[1:]]
    questions = indexed(records(p.get('questions', []), 'questions'), 'id')
    plans = indexed(records(p.get('source_plan', []), 'source_plan'), 'id')
    events = indexed(ev, 'event_id')
    candidates = indexed(ca, 'candidate_id')
    artifacts = indexed(ar, 'artifact_id')
    claims = indexed(cl, 'claim_id')
    indexed(rv, 'review_id')
    tasks = []
    def add(rank, kind, refs, action):
        tasks.append({'rank': rank, 'kind': kind, 'refs': refs, 'next_action': action})
    audited = {cid for r in rv if r.get('checkpoint') == 'CLAIM_AUDIT'
               for cid in r.get('claim_ids', [])}
    for qid, q in questions.items():
        base = {'P0': 0, 'P1': 30, 'P2': 60}.get(q.get('priority'), 60)
        related = [c for c in cl if c.get('question_id') == qid]
        if not related:
            add(base, 'question_without_claim', [qid], '先列可回答主張與原始來源缺口；未知仍需誠實記錄。')
        for c in related:
            cid = c['claim_id']
            evidence = records(c.get('evidence', []), 'evidence')
            counter = records(c.get('counterevidence', []), 'counterevidence')
            refs = [qid, cid]
            if c.get('status') == 'CONTESTED':
                add(base + 1, 'conflicting_claim', refs, '對照相反說法的原句、日期、身份與版本；先不多數決。')
            elif c.get('status') in {'AMBIGUOUS', 'UNAVAILABLE'}:
                add(base + 6, 'unresolved_claim', refs, '尋找能區分競爭解釋的原始材料；受阻時保留未知。')
            if not evidence:
                add(base + 2, 'no_supporting_evidence', refs, '補原文或完整嘗試紀錄；不能以摘要代證據。')
            families = set()
            for x in evidence + counter:
                aid = x.get('artifact_id')
                a = artifacts.get(aid)
                if a is None:
                    add(base, 'broken_artifact_reference', refs, '先修復不存在的 artifact 引用，再研究。')
                    continue
                af, ef = a.get('source_family_id'), x.get('source_family_id')
                if af and ef and af != ef:
                    add(base, 'family_label_conflict', refs + [aid], '核對來源譜系；不以不同標籤製造獨立印證。')
                family = af or ef
                if family:
                    families.add(family)
                else:
                    add(base + 3, 'unknown_source_family', refs + [aid], '追溯資訊起源後記錄來源家族。')
                if a.get('capture_status') in {'partial', 'metadata_only'}:
                    add(base + 3, 'incomplete_capture', refs + [aid], '判斷本主張需要的上下文是否缺失；必要時取完整原文。')
                if not x.get('locator'):
                    add(base + 2, 'missing_precise_locator', refs + [aid], '補頁碼／段落／時間碼，回原文逐項核對。')
            if evidence and len(families) < 2:
                add(base + 8, 'limited_source_diversity', refs, '檢查轉載鏈；按問題需要找獨立材料，單一正典或自述不必湊數。')
            if q.get('priority') == 'P0' and cid not in audited:
                add(base + 4, 'p0_not_audited', refs, '從原始材料重新抽查主張，留下 CLAIM_AUDIT。')
            if c.get('required_before_story_use'):
                add(base + 1, 'story_use_blocker', refs, '解除已記錄的使用限制前，不交給重要場景當事實。')
    for kid, c in candidates.items():
        if c.get('disposition') == 'defer':
            high = c.get('priority') in {'P0', 'high'}
            add(5 if high else 45, 'deferred_candidate', [kid], '先篩選相關性與身份；未知優先級不等於低價值。')
        if c.get('identity_binding') in {'PROBABLE', 'UNBOUND'} and c.get('disposition') == 'include':
            add(0, 'identity_not_verified', [kid], '候選保持隔離，以官方明示互鏈或穩定 ID 查核，不能直接合併人物。')
    for pid, source in plans.items():
        attempts = [x for x in ev if x.get('plan_id') == pid and x.get('type') in ROUTES]
        effective = [x for x in attempts if x.get('result', {}).get('status') in {'success', 'zero', 'noise'}]
        if source.get('priority') == 'must' and not effective:
            add(7, 'must_route_unfinished', [pid], '查核受阻原因，換可用且合適的來源面或明示範圍限制。')
        if attempts and attempts[-1].get('result', {}).get('status') in {'blocked', 'error'}:
            add(25, 'last_attempt_blocked', [pid], '記錄重試條件；不要立即重複請求或把限制當成零結果。')
    unique = {(t['kind'], tuple(t['refs'])): t for t in tasks}
    ordered = sorted(unique.values(), key=lambda t: (t['rank'], t['kind'], t['refs']))
    return {'schema': SCHEMA, 'run_id': p.get('run_id'),
            'advisory_only': True, 'validation_performed': False,
            'completion_assessed': False, 'task_count': len(ordered), 'tasks': ordered,
            'limitations': ['rank 是工作順序，不是事實可信度。',
                           '未核對原文、hash、身份或真正來源獨立性；必須另跑 validator。',
                           '零待辦不代表研究完成；工具未執行任何搜尋。']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run_dir')
    ap.add_argument('--output', help='Create new JSON file; never overwrite')
    args = ap.parse_args()
    try:
        result = plan(args.run_dir)
        text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.output:
            with Path(args.output).open('x', encoding='utf-8') as f:
                f.write(text)
        print(text, end='')
        return 0
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as exc:
        # Do not print malformed source content or arbitrary file contents.
        print(json.dumps({'error': type(exc).__name__, 'plan_created': False,
                          'hint': '檢查輸入 schema、重複 ID、檔案路徑與輸出是否已存在。'}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
