#!/usr/bin/env python3
"""Create hash-bound speaker manifests using explicit project registry aliases.

Only a direct alias label (``name:``) or simple attribution (``name說：``)
immediately before a quotation is recognized. Missing configuration, ambiguous
attribution, pronouns without an alias, and unattributed quotes fail closed.
An extracted NPC entry is a placeholder, not an approved per-turn manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from dialogue_quotes import parse_dialogue_quotes
from speaker_registry import registry_errors

ATTRIBUTION = r'(?:說|問|回答|回|傳|表示|道|喊|補了)'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer(prefix: str, aliases: dict[str, str]) -> str | None:
    # Do not reuse a speaker from an earlier sentence or quotation.
    clause = re.split(r'[。！？!?\n」]', prefix)[-1].strip()
    matches = {
        actor for label, actor in aliases.items()
        if re.fullmatch(re.escape(label) + rf'(?:\s*{ATTRIBUTION}\s*[:：]?|\s*[:：])\s*', clause)
    }
    return next(iter(matches)) if len(matches) == 1 else None


def extract(scene: Path, registry: dict, scene_id: str | None = None) -> dict:
    config_errors = registry_errors(registry, require_aliases=True)
    body = scene.read_text(encoding='utf-8').split('## 正文', 1)[-1]
    quotes, quote_errors = parse_dialogue_quotes(body)
    errors = config_errors + quote_errors
    aliases = registry.get('speaker_aliases', {}) if not config_errors else {}
    player_id = registry.get('player_id') if not config_errors else None
    dialogues = []
    for opening, quote in quotes:
        actor = infer(body[:opening], aliases)
        dialogues.append({
            'speaker': actor,
            'quote': quote,
            'manifest': None if actor is None or actor == player_id else {},
        })
    return {
        'schema': 'minis.npc-scene-manifest.v1',
        'scene_id': scene_id or scene.stem,
        'scene_sha256': digest(scene),
        'dialogues': dialogues,
        'quotation_status': 'invalid' if quote_errors else ('present' if quotes else 'none'),
        'parse_ok': not errors and all(item['speaker'] for item in dialogues),
        'errors': errors,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', required=True)
    parser.add_argument('--registry', required=True, help='Project npc-registry.json with player_id, actors, and speaker_aliases')
    parser.add_argument('--out', required=True)
    parser.add_argument('--scene-id')
    args = parser.parse_args()
    try:
        registry = json.loads(Path(args.registry).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        parser.error(f'cannot read speaker registry: {exc}')
    output = extract(Path(args.scene), registry, args.scene_id)
    raw = json.dumps(output, ensure_ascii=False, indent=2)
    Path(args.out).write_text(raw + '\n', encoding='utf-8')
    print(raw)
    raise SystemExit(0 if output['parse_ok'] else 2)


if __name__ == '__main__':
    main()
