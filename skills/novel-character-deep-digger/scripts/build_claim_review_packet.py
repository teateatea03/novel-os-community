#!/usr/bin/env python3
"""Build a conclusion-blind re-extraction packet; never alter a research run."""
import argparse
import hashlib
import json
from pathlib import Path
from research_gap_planner import read_file, records, indexed


def packet(run_dir, claim_id):
    root = Path(run_dir).resolve()
    p = read_file(root, 'protocol.json')
    if p.get('schema') != 'minis.character-research-run.v2':
        raise ValueError('unsupported_schema')
    questions = indexed(records(p.get('questions', []), 'questions'), 'id')
    claims = indexed(read_file(root, 'claims.jsonl', True), 'claim_id')
    artifacts = indexed(read_file(root, 'artifacts.jsonl', True), 'artifact_id')
    c = claims.get(claim_id)
    if not c or c.get('question_id') not in questions:
        raise ValueError('missing_claim_or_question')
    question = questions[c['question_id']]
    if not isinstance(question.get('text'), str) or not question['text'].strip():
        raise ValueError('missing_question_text')
    refs = records(c.get('evidence', []), 'evidence') + records(c.get('counterevidence', []), 'counterevidence')
    materials = {}
    for ref in refs:
        aid = ref.get('artifact_id')
        if aid not in artifacts:
            raise ValueError('missing_artifact')
        a = artifacts[aid]
        locator = ref.get('locator')
        if not locator:
            raise ValueError('missing_locator')
        key = (aid, json.dumps(locator, ensure_ascii=False, sort_keys=True))
        if key in materials:
            continue
        item = {'artifact_id': aid, 'locator': locator, 'registered_sha256': a.get('sha256'),
                'raw_or_derived': a.get('raw_or_derived', 'unknown'),
                'capture_status': a.get('capture_status', 'unknown'),
                'file_check': 'unverified_no_local_path'}
        checked = []
        for field in ('local_path', 'path'):
            if not a.get(field):
                continue
            if not isinstance(a[field], str):
                raise ValueError('invalid_path')
            path = Path(a[field])
            path = (path if path.is_absolute() else root / path).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError('missing_or_external_artifact')
            digest = hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda: f.read(1024 * 1024), b''):
                    digest.update(block)
            if digest.hexdigest() != a.get('sha256'):
                raise ValueError('artifact_hash_mismatch')
            checked.append(str(path.relative_to(root)))
        if checked:
            item.update(local_paths=sorted(set(checked)), file_check='hash_verified')
        # Explicit allowlist. Never include text/status/hypotheses/weight_reason or review results.
        materials[key] = item
    inputs = ['protocol.json', 'claims.jsonl', 'artifacts.jsonl']
    return {'schema': 'minis.character-claim-review-packet.v1',
            'run_id': p.get('run_id'), 'claim_id': claim_id,
            'question_id': c['question_id'], 'question': question['text'],
            'recorded_conclusion_omitted': True, 'independent_review_established': False,
            'input_hashes': {n: hashlib.sha256((root/n).read_bytes()).hexdigest() for n in inputs},
            'materials': [materials[k] for k in sorted(materials)],
            'review_prompts': [
                '先重述問題；若問題或選材本身暗示答案，記錄偏誤。',
                '開啟原始材料及定位前後文；重新抽出誰說了什麼、何時、對哪個對象。',
                '分開自述、親歷、轉述、表演與推論；記錄可支持的最窄答案。',
                '列矛盾、負向證據的可觀測性限制、需補原文與未知。',
                '先保存自己的抽取結果，再與舊 claim 比對並記錄分歧；禁止把本 packet 當已完成審查。'],
            'limitations': [
                '只隱去 ledger 結論；問題措辭、來源選擇、檔名與原文仍可能洩漏結論。',
                '不會自動匿名化材料，不證明 reviewer 獨立或已閱讀原文。',
                '無證據材料時只能列缺口，不可判為通過。',
                '未執行完整 run validator，亦未判定語義正確、來源獨立或研究完成。']}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('run_dir')
    ap.add_argument('--claim-id', required=True)
    ap.add_argument('--output', required=True, help='New output file only')
    args = ap.parse_args()
    try:
        result = packet(args.run_dir, args.claim_id)
        with Path(args.output).open('x', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(json.dumps({'created': True, 'materials': len(result['materials']),
                          'review_completed': False}, ensure_ascii=False))
        return 0
    except (ValueError, TypeError, OSError, KeyError, AttributeError, RuntimeError):
        print(json.dumps({'created': False, 'error': 'invalid_input_or_existing_output'}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
