"""Independent synthetic equipment-audit cases for speaker identity gates."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from all_npc_drift_firewall import validate
from extract_scene_speakers import extract, infer


REGISTRY = {
    'player_id': 'visitor',
    'actors': {'technician': {'kind': 'npc', 'contract': 'voice-contracts/technician.json'}},
    'speaker_aliases': {'技術員': 'technician', '你': 'visitor'},
}


class SpeakerRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.scene = self.root / 'scene.md'
        self.scene.write_text('技術員說：「鏡頭蓋在第二格。」\n你問：「編號相符嗎？」', encoding='utf-8')
        self.interactive = self.root / 'interactive'
        (self.interactive / 'voice-contracts').mkdir(parents=True)
        self.write_registry(REGISTRY)
        (self.interactive / 'voice-contracts/technician.json').write_text(json.dumps({
            'allowed_dialogue_acts': ['equipment_answer'], 'max_sentences': 2,
        }), encoding='utf-8')

    def write_registry(self, registry):
        (self.interactive / 'npc-registry.json').write_text(json.dumps(registry), encoding='utf-8')

    def manifest(self, *, approved=True):
        report = extract(self.scene, REGISTRY)
        if approved:
            report['dialogues'][0]['manifest'] = {'dialogue_act': 'equipment_answer'}
        path = self.root / 'manifest.json'
        path.write_text(json.dumps(report), encoding='utf-8')
        return path

    def test_aliases_resolve_explicit_custom_player_id(self):
        result = extract(self.scene, REGISTRY)
        self.assertTrue(result['parse_ok'])
        self.assertEqual([d['speaker'] for d in result['dialogues']], ['technician', 'visitor'])
        self.assertIsNone(result['dialogues'][1]['manifest'])
        self.assertEqual(result['dialogues'][0]['manifest'], {})

    def test_unconfigured_and_ambiguous_speakers_are_not_guessed(self):
        aliases = REGISTRY['speaker_aliases']
        self.assertIsNone(infer('訪客說：', aliases))
        self.assertIsNone(infer('技術員和你說：', aliases))
        self.assertIsNone(infer('技術員說：「第一格。」\n', aliases))
        self.assertEqual(infer('技術員：', aliases), 'technician')
        self.scene.write_text('訪客說：「先核對標籤。」', encoding='utf-8')
        self.assertFalse(extract(self.scene, REGISTRY)['parse_ok'])

    def test_missing_or_invalid_configuration_fails_closed(self):
        for bad in ({}, {'player_id': 'visitor', 'actors': {}},
                    {'player_id': 'visitor', 'actors': {}, 'speaker_aliases': {'技術員': 'missing'}}):
            with self.subTest(registry=bad):
                result = extract(self.scene, bad)
                self.assertFalse(result['parse_ok'])
                self.assertTrue(result['errors'])
                self.assertTrue(all(d['speaker'] is None for d in result['dialogues']))

    def test_cli_requires_registry(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('extract_scene_speakers.py')),
                                 '--scene', str(self.scene), '--out', str(self.root / 'out.json')], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / 'out.json').exists())

    def test_firewall_keeps_npc_and_semantic_review_gates(self):
        result = validate(self.root, self.scene, self.manifest(), None, False)
        self.assertTrue(result['ok'])
        result = validate(self.root, self.scene, self.manifest(approved=False), None, False)
        self.assertIn('MISSING_MANIFEST', {i['code'] for i in result['findings']})
        result = validate(self.root, self.scene, self.manifest(), None, True)
        self.assertIn('SEMANTIC_REVIEW_MISSING', {i['code'] for i in result['findings']})

    def test_missing_player_id_never_bypasses_firewall(self):
        registry = copy.deepcopy(REGISTRY)
        del registry['player_id']
        self.write_registry(registry)
        result = validate(self.root, self.scene, self.manifest(), None, False)
        codes = {item['code'] for item in result['findings']}
        self.assertFalse(result['ok'])
        self.assertIn('INVALID_SPEAKER_REGISTRY', codes)
        self.assertIn('UNREGISTERED_NPC', codes)

    def test_long_known_quote_is_fully_retained_and_checked(self):
        quote = '鏡頭蓋編號' * 120
        self.assertGreater(len(quote), 500)
        self.scene.write_text('技術員說：「' + quote + '」', encoding='utf-8')
        report = extract(self.scene, REGISTRY)
        self.assertTrue(report['parse_ok'])
        self.assertEqual(report['quotation_status'], 'present')
        self.assertEqual(report['dialogues'][0]['quote'], quote)
        result = validate(self.root, self.scene, self.manifest(), None, False)
        self.assertTrue(result['ok'])
        self.assertEqual(result['actual_quotes'], 1)
        manifest = self.manifest()
        data = json.loads(manifest.read_text(encoding='utf-8'))
        data['dialogues'] = []
        manifest.write_text(json.dumps(data), encoding='utf-8')
        result = validate(self.root, self.scene, manifest, None, False)
        self.assertIn('SPEAKER_COVERAGE', {item['code'] for item in result['findings']})

    def test_long_unknown_quote_is_not_silently_ignored(self):
        quote = '需要核對的標籤' * 100
        self.assertGreater(len(quote), 500)
        self.scene.write_text('未登記訪客說：「' + quote + '」', encoding='utf-8')
        report = extract(self.scene, REGISTRY)
        self.assertFalse(report['parse_ok'])
        self.assertEqual(len(report['dialogues']), 1)
        self.assertIsNone(report['dialogues'][0]['speaker'])
        result = validate(self.root, self.scene, self.manifest(approved=False), None, False)
        self.assertFalse(result['ok'])
        self.assertEqual(result['actual_quotes'], 1)
        self.assertIn('UNREGISTERED_NPC', {item['code'] for item in result['findings']})

    def test_malformed_quotes_fail_extraction_and_firewall(self):
        for text in ('技術員說：「鏡頭蓋還在箱裡。', '鏡頭蓋還在箱裡。」',
                     '技術員說：「標籤「待核對」尚未移除。」', '技術員說：「」'):
            with self.subTest(text=text):
                self.scene.write_text(text, encoding='utf-8')
                report = extract(self.scene, REGISTRY)
                self.assertFalse(report['parse_ok'])
                self.assertEqual(report['quotation_status'], 'invalid')
                self.assertTrue(report['errors'])
                result = validate(self.root, self.scene, self.manifest(approved=False), None, False)
                self.assertFalse(result['ok'])
                self.assertIn('QUOTATION_PARSE_FAILURE', {item['code'] for item in result['findings']})

    def test_narration_without_dialogue_is_explicitly_valid(self):
        self.scene.write_text('圓頂緩慢合攏，器材清單留在桌上。', encoding='utf-8')
        report = extract(self.scene, REGISTRY)
        self.assertTrue(report['parse_ok'])
        self.assertEqual(report['quotation_status'], 'none')
        self.assertEqual(report['dialogues'], [])
        result = validate(self.root, self.scene, self.manifest(approved=False), None, False)
        self.assertTrue(result['ok'])
        self.assertEqual(result['actual_quotes'], 0)
        self.assertEqual(result['checked_dialogues'], 0)

    def test_changed_scene_hash_is_rejected(self):
        manifest = self.manifest()
        self.scene.write_text(self.scene.read_text(encoding='utf-8') + '\n箱子已扣緊。', encoding='utf-8')
        result = validate(self.root, self.scene, manifest, None, False)
        self.assertIn('SCENE_HASH_MISMATCH', {i['code'] for i in result['findings']})


if __name__ == '__main__':
    unittest.main()
