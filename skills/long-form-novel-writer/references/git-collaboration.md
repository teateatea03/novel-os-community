# Git 協作與正典版本規範

Git 是協作與差分層；`[LOCKED]/[CANON]/[PLAN]/[DRAFT]` 仍是內容狀態，兩者不可混同。

## 安全預設
1. `novel_git.py init` 只初始化 repository、`.gitignore` 與 Git attributes，不自動 commit。
2. commit 前先跑 local gate；P0/FAIL 時預設拒絕，作者可用 `--override-reason` 明確覆寫並寫入 `decisions.md`。
3. 不自動 `reset --hard`、force push、rebase、merge 或 checkout 覆蓋工作樹。
4. 分支命名：`draft/chapter-001-*`、`revise/*`、`experiment/*`；正典升級由作者確認後 commit。
5. 衍生檔（story index、context packs、gates、mentions、review raw）預設忽略；聖經、帳本、章綱、scene card、正文與摘要納入版本。

## 建議節點
- 章前：working tree 應可辨識；重大改寫另做 filesystem snapshot。
- 章草稿：`draft:` commit 可保留，但不代表 [CANON]。
- 作者核准且 gate 通過：`canon:` commit，並同步 `project.json.canon_through`。
- 改綱：新 branch + snapshot + cascade impact；人工決定如何合併。

多人協作時，衝突優先人工合併 Markdown；不得以「較新檔案」整檔覆寫較舊但含有效正典的版本。
