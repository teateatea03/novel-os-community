#!/usr/bin/env python3
"""Run the repository's portable standard-library test suites."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, cwd=None, env=None):
    shown = ' '.join(map(str, cmd))
    print(f'\n$ {shown}', flush=True)
    result = subprocess.run(list(map(str, cmd)), cwd=cwd or ROOT, env=env)
    if result.returncode:
        raise SystemExit(result.returncode)


def main():
    # Check the publication gates as well as the skill behavior.
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'scripts',
         '-p', 'test_*.py', '-q'])

    # Novel Judge tests need package discovery so relative imports resolve.
    scripts = ROOT / 'skills/immersive-interactive-fiction/scripts'
    env = os.environ.copy()
    env['PYTHONPATH'] = str(scripts)
    run([sys.executable, '-m', 'unittest', 'discover', '-s', 'novel_judge',
         '-t', '.', '-p', 'test_*.py', '-q'], cwd=scripts, env=env)

    # Remaining self-contained test scripts.
    for path in sorted(ROOT.glob('skills/**/test_*.py')):
        if 'immersive-interactive-fiction/scripts/novel_judge/' in path.as_posix():
            continue
        run([sys.executable, path.name], cwd=path.parent)
    print('\nAll portable repository tests passed.')


if __name__ == '__main__':
    main()
