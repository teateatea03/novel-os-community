#!/usr/bin/env python3
"""Synthetic regression tests for the publication gates; no real user data."""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import privacy_scan
import run_tests
import validate_json


class RepositoryChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        self.root.mkdir()

    def write(self, name, content='public synthetic example'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding='utf-8')
        return path

    def call(self, entrypoint):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = entrypoint([str(self.root)])
        return status, output.getvalue()

    def assert_failed(self, entrypoint, reason):
        status, output = self.call(entrypoint)
        self.assertEqual(status, 1, output)
        self.assertIn(reason, output)
        return output

    def init_git(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def track(self, name):
        subprocess.run(['git', '-C', str(self.root), 'add', '-f', '--', name],
                       check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_plain_source_and_unicode_json_pass(self):
        self.write('README.md', 'Synthetic source')
        self.write('fixture.json', '{"example": "虚构"}')
        self.assertEqual(self.call(privacy_scan.main)[0], 0)
        status, output = self.call(validate_json.main)
        self.assertEqual(status, 0, output)
        self.assertIn('1 files', output)

    def test_credentials_detected_without_echoing_content(self):
        synthetic = 'gh' + 'p_' + 'A' * 24
        self.write('config.txt', synthetic + '\nSYNTHETIC_STORY_MARKER')
        output = self.assert_failed(privacy_scan.main, 'GitHub token')
        self.assertNotIn(synthetic, output)
        self.assertNotIn('SYNTHETIC_STORY_MARKER', output)

    def test_scanner_source_is_not_exempt(self):
        self.write('scripts/privacy_scan.py', 'gh' + 'p_' + 'A' * 24)
        self.assert_failed(privacy_scan.main, 'GitHub token')

    def test_secret_in_filename_is_redacted(self):
        synthetic = 'gh' + 'p_' + 'A' * 24
        self.write('secret_' + synthetic + '.txt')
        output = self.assert_failed(privacy_scan.main, '[redacted]')
        self.assertNotIn(synthetic, output)

    def test_invalid_utf8_fails_both_gates_without_content(self):
        self.write('sample.json', b'\xffSYNTHETIC_STORY_MARKER')
        for entrypoint in (privacy_scan.main, validate_json.main):
            with self.subTest(entrypoint=entrypoint.__module__):
                output = self.assert_failed(entrypoint, 'not valid UTF-8')
                self.assertNotIn('SYNTHETIC_STORY_MARKER', output)

    def test_unreadable_file_fails_both_gates(self):
        self.write('sample.json', '{}')
        with patch.object(Path, 'open', side_effect=PermissionError('PRIVATE_ERROR_DETAIL')):
            for entrypoint in (privacy_scan.main, validate_json.main):
                output = self.assert_failed(entrypoint, 'cannot read file')
                self.assertNotIn('PRIVATE_ERROR_DETAIL', output)

    def test_directory_error_fails_both_gates(self):
        def broken_walk(root, **kwargs):
            kwargs['onerror'](PermissionError(13, 'PRIVATE_ERROR_DETAIL', str(root / 'data')))
            return iter(())
        with patch.object(privacy_scan.os, 'walk', side_effect=broken_walk):
            for entrypoint in (privacy_scan.main, validate_json.main):
                output = self.assert_failed(entrypoint, 'cannot read directory')
                self.assertNotIn('PRIVATE_ERROR_DETAIL', output)

    def test_oversize_file_requires_review(self):
        self.write('large.json', b' ' * (privacy_scan.MAX_BYTES + 1))
        for entrypoint in (privacy_scan.main, validate_json.main):
            self.assert_failed(entrypoint, 'file exceeds 5 MB')

    def test_bad_json_reports_location_without_source(self):
        self.write('broken.json', '{"SYNTHETIC_STORY_MARKER": }')
        output = self.assert_failed(validate_json.main, 'line 1, column')
        self.assertNotIn('SYNTHETIC_STORY_MARKER', output)

    def test_missing_or_file_root_fails(self):
        for root in (self.root / 'missing', self.write('file.txt')):
            for entrypoint in (privacy_scan.main, validate_json.main):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(entrypoint([str(root)]), 1)

    def test_confirmed_local_environments_excluded(self):
        for name in ('.venv', 'venv', 'env'):
            self.write(name + '/pyvenv.cfg', 'home = /example/python')
            self.write(name + '/lib/package/sample.json', 'not json')
            self.write(name + '/lib/package/example.txt', 'gh' + 'p_' + 'A' * 24)
        self.write('data.json', '{}')
        self.assertEqual(self.call(privacy_scan.main)[0], 0)
        status, output = self.call(validate_json.main)
        self.assertEqual(status, 0, output)
        self.assertIn('1 files', output)

    def test_unconfirmed_environment_not_hidden(self):
        self.write('.venv/example.txt', 'gh' + 'p_' + 'A' * 24)
        self.assert_failed(privacy_scan.main, 'GitHub token')

    def test_nested_environment_not_hidden(self):
        self.write('examples/.venv/pyvenv.cfg', '')
        self.write('examples/.venv/example.txt', 'gh' + 'p_' + 'A' * 24)
        self.assert_failed(privacy_scan.main, 'GitHub token')

    def test_generated_caches_excluded(self):
        self.write('__pycache__/module.pyc', b'\xff')
        self.write('.pytest_cache/example.json', 'not json')
        self.assertEqual(self.call(privacy_scan.main)[0], 0)
        self.assertEqual(self.call(validate_json.main)[0], 0)

    def test_private_roots_not_hidden_by_cache_names(self):
        for name in sorted(privacy_scan.PRIVATE_PARTS):
            self.write(name + '/__pycache__/data.txt')
        findings = privacy_scan.scan(self.root)
        self.assertEqual(len(findings), len(privacy_scan.PRIVATE_PARTS))
        self.assertTrue(all('private data path' in reason for _, reason in findings))

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_file_directory_and_broken_symlinks_rejected_without_read(self):
        outside = self.root.parent / 'outside'
        outside.mkdir()
        (outside / 'data.json').write_text('{}', encoding='utf-8')
        for name, target, is_dir in (
            ('linked.json', outside / 'data.json', False),
            ('linked_dir', outside, True),
            ('broken.json', outside / 'missing', False),
        ):
            try:
                (self.root / name).symlink_to(target, target_is_directory=is_dir)
            except OSError as exc:
                self.skipTest(f'Cannot create symlink on this platform: {exc.__class__.__name__}')
        with patch.object(privacy_scan, 'read_source', side_effect=AssertionError('followed link')):
            self.assert_failed(privacy_scan.main, 'symlink is not reviewable')
        with patch.object(validate_json, 'read_source', side_effect=AssertionError('followed link')):
            self.assert_failed(validate_json.main, 'symlink is not reviewable')

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_named_as_local_environment_rejected(self):
        try:
            (self.root / '.venv').symlink_to(self.root.parent, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f'Cannot create symlink on this platform: {exc.__class__.__name__}')
        self.assert_failed(privacy_scan.main, 'symlink is not reviewable')

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFOs unavailable')
    def test_special_file_rejected_without_blocking(self):
        os.mkfifo(self.root / 'pipe')
        self.assert_failed(privacy_scan.main, 'not a regular file')

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_gitignored_private_data_still_scanned(self):
        self.init_git()
        self.write('.gitignore', 'novels/\n')
        self.write('novels/story.txt')
        self.assert_failed(privacy_scan.main, 'private data path')

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_tracked_environment_and_cache_content_not_hidden(self):
        self.init_git()
        self.write('.venv/pyvenv.cfg', '')
        for name in ('.venv/lib/data.json', '__pycache__/data.json'):
            self.write(name, 'not json')
            self.track(name)
        output = self.assert_failed(validate_json.main, 'invalid JSON')
        self.assertIn('.venv/lib/data.json', output)
        self.assertIn('__pycache__/data.json', output)
        self.write('.venv/lib/leak.txt', 'gh' + 'p_' + 'A' * 24)
        self.assert_failed(privacy_scan.main, 'GitHub token')

    @unittest.skipUnless(shutil.which('git'), 'Git not installed')
    def test_missing_tracked_content_fails_closed(self):
        self.init_git()
        path = self.write('data.json', '{}')
        self.track('data.json')
        path.unlink()
        self.assert_failed(privacy_scan.main, 'tracked file could not be reviewed')

    def test_git_failure_fails_closed(self):
        (self.root / '.git').mkdir()
        with patch.object(privacy_scan.subprocess, 'run', side_effect=FileNotFoundError):
            for entrypoint in (privacy_scan.main, validate_json.main):
                self.assert_failed(entrypoint, 'cannot enumerate tracked files')

    def test_runner_includes_gate_tests_and_keeps_judge_package_discovery(self):
        self.write('skills/example/test_example.py', '')
        self.write('skills/immersive-interactive-fiction/scripts/novel_judge/test_example.py', '')
        with patch.object(run_tests, 'ROOT', self.root), patch.object(run_tests, 'run') as run:
            with contextlib.redirect_stdout(io.StringIO()):
                run_tests.main()
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(len(commands), 3)
        self.assertIn('scripts', commands[0])
        self.assertIn('discover', commands[0])
        self.assertIn('novel_judge', commands[1])
        self.assertIn('-t', commands[1])
        self.assertEqual(commands[2][-1], 'test_example.py')

    def test_runner_propagates_failure(self):
        with patch.object(run_tests.subprocess, 'run') as run:
            run.return_value.returncode = 7
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as raised:
                run_tests.run(['synthetic-command'])
        self.assertEqual(raised.exception.code, 7)


if __name__ == '__main__':
    unittest.main()
