<!-- language-navigation --> [繁體中文](zh-TW.md) | **English** | [日本語](ja.md) | [한국어](ko.md) | [Español](es.md) | [Français](fr.md) | [Deutsch](de.md) | [Português](pt.md)

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
