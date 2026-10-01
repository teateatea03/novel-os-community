## Summary / 摘要

Describe the change and why it belongs in the reusable Novel OS source.
說明修改內容，以及它為何屬於可重複使用的 Novel OS 原始碼。

## Validation / 驗證

- [ ] `python3 scripts/privacy_scan.py .`
- [ ] `python3 scripts/validate_json.py .`
- [ ] `python3 -m compileall -q skills scripts`
- [ ] `python3 scripts/run_tests.py`

## Privacy and rights / 隱私與權利

- [ ] No manuscript, live session, story state, personal/research database, private endpoint, credential, memory, log, or backup is included. / 未包含原稿、真實工作階段、故事狀態、個人／研究資料庫、私人端點、憑證、記憶、日誌或備份。
- [ ] Fixtures are synthetic and do not merely rename private data. / 測試資料為合成資料，並非僅將私人資料改名。
- [ ] I have the right to contribute all code, text, and assets in this change. / 我有權貢獻此修改中的所有程式碼、文字與資產。
- [ ] New dependencies or adapted third-party material are identified with source and license. / 新相依套件或改作的第三方材料已標示來源與授權。

## Compatibility / 相容性

List affected skills, platforms, migrations, and fallback behavior.
列出受影響的技能、平台、遷移與降級行為。
