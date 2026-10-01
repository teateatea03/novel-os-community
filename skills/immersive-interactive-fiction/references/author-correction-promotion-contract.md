# 作者糾錯升格契約 v1

狀態：`[CANON WORKFLOW]`  
用途：把作者修正從對話／daily log，升成下次會讀到的護欄、rejected fixture 或 Gate。  
權威：只產生非正典品質證據與生成前護欄；**不得**自行提交正典、改 state、或讓模型自動改規則。

## 為什麼需要

作者回饋帳本記錄 `accept / revise / reject`，但不保證下次生成會讀到那條教訓。  
單次口味不該變技能；反覆、可檢查、且已有作者核准的錯誤，才可升格。

## 預設：先不要建新技能

不確定時，只記錯誤卡，不新建 `SKILL.md`。  
一個新技能必須證明現有角色檔、voice contract、人味編輯、rejected fixture 或 Gate 都裝不下。

## 輸出類型

| 類型 | 何時使用 | 寫入哪裡 | 下次如何生效 |
|---|---|---|---|
| `note` | 單次口味、證據不足 | `quality/author-corrections.jsonl` | 不自動注入 |
| `character_guard` | 同一角色會再犯的連續性／聲線 | 角色檔「一致性護欄」與／或 `voice-contracts/*.json` | 生成該角色前必讀 |
| `rejected_fixture` | 可重現的壞稿模式 | `interactive/prose-fixtures/rejected/` | prompt 改版與人味／散文 Gate 回歸 |
| `gate` | 可用固定字串／狀態差分機器判斷 | 既有 Gate 或新增 error code | 提交前硬擋 |
| `workflow_change` | 問題在流程，不在一句規則 | 互動／長篇技能的回合程序 | 改宿主步驟，不加規則堆 |
| `reject` | 一次性、無法泛化 | 只留 feedback | 不升格 |

## 升格條件

同時滿足才可從 `note` 往上走：

1. 作者明示修正，不是模型自己後悔。
2. 能寫成「若條件 X，不得寫成 Y；應寫成 Z」。
3. 至少有一份壞摘錄與一份已接受修訂。
4. 不與現有正典、voice contract、Gate 衝突。
5. 最好能刪掉或合併舊規則，而不是只加新的。

角色連續性預設升 `character_guard`。  
文風群聚預設升 `rejected_fixture`。  
可機器判斷且會反覆出現，才升 `gate`。

## 生命週期

```text
作者修正
→ 寫 minis.author-correction.v1 錯誤卡（status=note）
→ 建議 recommended_action
→ 作者核准升格
→ 寫入目標護欄／fixture／Gate
→ 記錄 promotion
```

未核准不得改角色正典護欄，也不得把 note 當 Gate。

## 生成前必讀

寫含該角色的候選前，宿主應讀：

1. 該角色 `characters/*.md` 的一致性護欄
2. `interactive/voice-contracts/<id>.json`
3. 與本場同類的 `prose-fixtures/rejected/`（最多 3 張，只取 error code 與 expected detection）
4. 本專案 `quality/author-corrections.jsonl` 裡 `status=promoted` 且 `applies_when` 命中的卡片

不要把整個 rejected 庫或全部 note 灌進模型。

## 禁止

- 一次修正就開一個新技能
- 用模型自動改 `SKILL.md` 或 Gate
- 把未核准 note 寫進正典
- 為了「防 AI」把文字故意改粗糙
