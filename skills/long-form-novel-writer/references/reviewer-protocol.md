# 獨立審稿與深度一致性稽核

獨立 reviewer 用於補盲，不是作者、正典或 gate 的替代品。優先角色：

- **continuity**：只找可由雙證據支持的矛盾；不評論喜好。
- **beta-reader**：描述讀者理解、困惑、期待與情緒效果；不重寫成自己的風格。
- **style-editor**：依 `style-sheet.md` 查可定位漂移、角色同聲與無效重複。

## 證據契約
每個 issue 必須有 category、severity、claim、evidence_a、evidence_b、minimal_fix、confidence。無法提供兩個可定位證據時只能列 `question`，不能判 P0。模型輸出永遠標 `machine_suggestion`；合併進 gate 前由主流程複核原文。

## 深度 sweep 時機
每卷中點、每 10 章、重大改綱後、卷末。輸入以 context pack、最近章節、帳本和風格契約為主，避免無差別塞全稿。不同 reviewer 應分開呼叫，避免一個模型同時扮演作者、讀者與裁判造成角色污染。

## 成本與失敗
模型不可用、JSON 不合法或超時時，保留原始回傳與 WARN；不阻止正文保存。除非作者設定 fail-closed，深度 reviewer 不自動把草稿標 FAIL。
