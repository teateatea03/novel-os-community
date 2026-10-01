# Novel Judge 實務方法（2026-09-06）

採公開編輯／beta 經驗與 LLM-as-judge 研究，接到既有五層權威。不新增 Gate，不把機器分數當品質真值。

## 採用

### 小說實務（人）

- Jane Friedman／Barbara Linn Probst（92 位作者實際用法，2019／2025）：beta 是未來讀者的代理人，不是編輯；不同階段用不同讀者；問題清單避免空讚／空罵，但過度引導會讓人只看你問的花色；**不要照單全收**，多人（尤其作家＋非作家）指出同一弱點才較認真；太多廚師會毀掉意圖。
- Jane Friedman／Andrew Noakes（The Niche Reader，管理過數百件）：beta ≠ 專業編輯，不問三幕、內在衝突、市場能不能賣；固定問整體印象、喜歡／不喜歡、開頭、失趣、能不能跟、困惑、不合理、不一致、角色好不好跟、結局滿不滿意；故事特問放最後，看它有沒有在前面自發出現。義工問卷宜短。
- Dabble／Abi Wurdeman：beta 在自己改到當下最好之後；不當校對；要的是情節破洞、節奏、失趣、角色感受、情緒有沒有發生。

接到本系統：

- `READER_RESPONSE` 只收人類冷讀／beta。機器 `inspect_prose` 是 prescan，origin 必須標明，不進 pass@1。
- 一位讀者＝軼事；兩位以上獨立提到同一 code／locus＝共識票；採納仍是 `AUTHOR_DECISION`。
- 問卷分核心／可選；不做免費 copyedit。

### LLM-as-judge 研究（機器）

- Zheng et al., MT-Bench／Chatbot Arena（arXiv:2306.05685）：position bias、verbosity bias、self-enhancement；pairwise 要換位。
- Shi et al., Judging the Judges（arXiv:2406.07791）：位置偏差不是隨機，換位一致性要量。
- Dubois et al., Length-Controlled AlpacaEval（arXiv:2404.04475）：自動評審偏愛長答案；長度是已知干擾。
- Park et al., OffsetBias（arXiv:2407.06551）：評審偏誤有多型，需 meta-evaluation 集，不能假設「有打分就準」。
- Kim et al., Prometheus（arXiv:2310.08491）：沒有 rubric／reference 的分數不可靠。
- G-Eval（arXiv:2303.16634）：LLM 分數仍低於與人類中等相關；創造性任務尤其不能用 BLEU 類指標。

接到本系統：

- pairwise 必須換位、揭露長度比；heuristic issue-weight **不是**人類偏好真值。
- `quality_improved` 維持 False，直到有未見過的人類／hidden 證據。
- 不把 LLM 文青分接到 CANON 或 pass@1。
- NARRATIVE_QA 維持保守、有 span／evidence 的規則；P0 只留給高信心契約破壞。

## 不採用

- 用單一 LLM PASS 同時代表可提交、沒有敘事 bug、編輯夠強、讀者會喜歡、作者比較喜歡。
- 把機器冷讀當成 beta。
- 把編輯診斷或讀者層改成硬擋提交。
- 為了「看起來有在評」放寬 P0 或新開 Gate。
- 義工 beta 丟 20 題以上當必答。
- 作者必須接受所有 beta 意見。
