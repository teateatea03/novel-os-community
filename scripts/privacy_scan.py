#!/usr/bin/env python3
"""Fail closed on credentials, local artifacts, and private-project material.

Review working-tree files, including untracked and gitignored files. Exclude Git
metadata, generated Python caches, and confirmed root Python virtualenvs. Tracked
files override cache/virtualenv exclusions. This is not a staged-index scan.
"""
from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
from pathlib import Path

MAX_BYTES = 5_000_000
CACHE_DIRS = {'__pycache__', '.pytest_cache'}
VENV_DIRS = {'.venv', 'venv', 'env'}
PRIVATE_PARTS = {
    'novels', 'interactive-fiction', 'novel-character-database',
    'novel-character-research', 'novel-world-database',
    'novel-special-object-database', 'memory', 'attachments', 'offloads', 'backups',
}
NAME_BAD = re.compile(
    r'(^|[._-])(env|credential|secret|token|cookie|private|id_rsa|id_ed25519)([._-]|$)',
    re.I,
)
PATTERNS = {
    'private key': re.compile(r'BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY'),
    'GitHub token': re.compile(r'(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})'),
    'AWS key': re.compile(r'AKIA[0-9A-Z]{16}'),
    'Slack token': re.compile(r'xox[baprs]-[A-Za-z0-9-]{10,}'),
    'Google API key': re.compile(r'AIza[0-9A-Za-z_-]{30,}'),
    'credential assignment': re.compile(r'\b(?:api[_ -]?key|password|access[_ -]?token)\s*[:=]\s*["\']?(?!<|\{|\[|YOUR_|EXAMPLE|REDACTED|None\b|null\b)[A-Za-z0-9_./+=-]{12,}', re.I),
    # Split the literal so this scanner can scan its own source without a bypass.
    'Minis resource URL': re.compile(r'mini' r's://'),
    'private workspace path': re.compile(r'/var/minis/(?:shared/(?:novels|interactive-fiction|novel-(?:character|world|special-object)-(?:database|research))|memory|attachments|offloads)(?:/|\b)'),
    'private IPv4 endpoint': re.compile(r'https?://(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?::\d+)?'),
}
Finding = tuple[str, str]


def reviewed_files(root: Path) -> tuple[list[Path], list[Finding]]:
    """Return in-scope regular files and fail-closed traversal diagnostics.

    Do not use .gitignore for exclusions: it deliberately lists private data that
    the privacy gate must catch. Symlinks are never followed or silently omitted.
    Git is required only for a checkout with its own .git metadata.
    """
    findings: list[Finding] = []
    if not root.is_dir():
        return [], [('.', 'scan root is not an accessible directory')]
    tracked: set[str] = set()
    if os.path.lexists(root / '.git'):
        try:
            result = subprocess.run(
                ['git', '-C', str(root), '-c', 'core.fsmonitor=false',
                 'ls-files', '--cached', '-z'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True,
            )
            tracked = {os.fsdecode(p) for p in result.stdout.split(b'\0') if p}
        except (OSError, subprocess.CalledProcessError):
            return [], [('.', 'cannot enumerate tracked files; Git review required')]
    tracked_dirs = {
        parent.as_posix()
        for filename in tracked
        for parent in Path(filename).parents
        if parent != Path('.')
    }
    files: list[Path] = []
    seen: set[str] = set()

    def walk_error(exc: OSError) -> None:
        try:
            rel = Path(exc.filename).relative_to(root).as_posix()
        except (TypeError, ValueError):
            rel = '.'
        findings.append((rel, 'cannot read directory; manual review required'))

    for base, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        base_path = Path(base)
        retained = []
        for name in sorted(dirs + names):
            path = base_path / name
            rel = path.relative_to(root).as_posix()
            if name == '.git':
                continue  # Git metadata is never publication source.
            try:
                mode = path.lstat().st_mode
            except OSError:
                findings.append((rel, 'cannot inspect file; manual review required'))
                continue
            if stat.S_ISLNK(mode):
                findings.append((rel, 'symlink is not reviewable; replace with source file'))
                continue
            if stat.S_ISDIR(mode):
                private_path = bool(set(path.relative_to(root).parts) & PRIVATE_PARTS)
                exclude = name in CACHE_DIRS and not private_path
                if base_path == root and name in VENV_DIRS:
                    try:
                        exclude = stat.S_ISREG((path / 'pyvenv.cfg').lstat().st_mode)
                    except FileNotFoundError:
                        exclude = False
                    except OSError:
                        findings.append((rel, 'cannot inspect virtualenv marker'))
                        exclude = False
                if not exclude or rel in tracked_dirs:
                    retained.append(name)
            elif stat.S_ISREG(mode):
                files.append(path)
                seen.add(rel)
            else:
                findings.append((rel, 'not a regular file; manual review required'))
        dirs[:] = retained
    for rel in tracked - seen:
        findings.append((rel, 'tracked file could not be reviewed'))
    return sorted(files), findings


def read_source(path: Path) -> tuple[str | None, str | None]:
    """Bound reads and never include file contents or raw exceptions in errors."""
    try:
        with path.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            return None, 'file exceeds 5 MB; manual review required'
        return data.decode('utf-8'), None
    except UnicodeDecodeError:
        return None, 'not valid UTF-8; manual review required'
    except OSError:
        return None, 'cannot read file; manual review required'


def scan(root: Path) -> list[Finding]:
    files, findings = reviewed_files(root)
    for path in files:
        rel = path.relative_to(root).as_posix()
        if set(path.relative_to(root).parts) & PRIVATE_PARTS or NAME_BAD.search(path.name):
            findings.append((rel, 'sensitive filename/private data path'))
            continue
        text, error = read_source(path)
        if error:
            findings.append((rel, error))
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append((rel, label))
    return sorted(set(findings))


def display_path(rel: str) -> str:
    # Escape control characters and redact credential matches even in filenames.
    for pattern in PATTERNS.values():
        rel = pattern.sub('[redacted]', rel)
    return repr(rel)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        findings = scan(Path(args[0] if args else '.').resolve())
    except (OSError, RuntimeError):
        findings = [('.', 'cannot resolve scan root; manual review required')]
    if findings:
        print('PRIVACY SCAN FAILED:')
        for path, why in findings:
            print(f'- {display_path(path)}: {why}')
        return 1
    print('Privacy scan passed: no configured credential, private endpoint, or private-project indicators found.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
