<!-- language-navigation -->

[繁體中文](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/zh-TW.md) | **English** | [日本語](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/ja.md) | [한국어](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/ko.md) | [Español](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/es.md) | [Français](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/fr.md) | [Deutsch](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/de.md) | [Português](https://github.com/teateatea03/novel-os-community/blob/main/.github/PULL_REQUEST_TEMPLATE/pt.md)

## Summary

Describe the change and why it belongs in the reusable Novel OS source.

## Validation

- [ ] `python3 scripts/privacy_scan.py .`
- [ ] `python3 scripts/validate_json.py .`
- [ ] `python3 -m compileall -q skills scripts`
- [ ] `python3 scripts/run_tests.py`

## Privacy and rights

- [ ] No manuscript, live session, story state, personal/research database, private endpoint, credential, memory, log, or backup is included.
- [ ] Fixtures are synthetic and do not merely rename private data.
- [ ] I have the right to contribute all code, text, and assets in this change.
- [ ] New dependencies or adapted third-party material are identified with source and license.

## Compatibility

List affected skills, platforms, migrations, and fallback behavior.
