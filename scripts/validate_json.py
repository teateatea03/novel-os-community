#!/usr/bin/env python3
"""Validate UTF-8 JSON in the same reviewed-file scope as privacy_scan.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from privacy_scan import display_path, read_source, reviewed_files


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    try:
        root = Path(args[0] if args else '.').resolve()
        files, errors = reviewed_files(root)
    except (OSError, RuntimeError):
        root, files, errors = Path('.'), [], [('.', 'cannot resolve scan root')]
    count = 0
    for path in files:
        if path.suffix != '.json':
            continue
        count += 1
        rel = path.relative_to(root).as_posix()
        text, error = read_source(path)
        if error:
            errors.append((rel, error))
            continue
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            errors.append((rel, f'invalid JSON at line {exc.lineno}, column {exc.colno}'))
        except (ValueError, RecursionError):
            errors.append((rel, 'JSON exceeds parser limits'))
    if errors:
        print('JSON validation failed:')
        for path, why in sorted(set(errors)):
            print(f'- {display_path(path)}: {why}')
        return 1
    print(f'JSON validation passed: {count} files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
