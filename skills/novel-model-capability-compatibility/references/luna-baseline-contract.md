# Luna Baseline Contract｜Novel OS 最低模型基準

版本：1.1.0
契約識別：`novel-os-candidate-baseline-v1`
目的：定義模型候選生成器與宿主權限之間的最低設計契約；換模型不能改變工作流、權限或正典結果。

「Luna」是既有檔名與介面保留的契約代號。本文不是實測 benchmark，不宣稱任何真實模型、供應商或 endpoint 的當前能力或可用性。所有實際等級與 task 授權都必須由部署者重新執行 probe、保存可驗證 artifact 後判定。

## 核心定義

「以 Luna 為基礎」不是要求永遠只呼叫 Luna，而是：

1. Novel OS 的 prompt 粒度、JSON schema、context pack、修復回合與 Gate 都須符合這份窄任務契約，並由部署測試驗證。
2. 其他模型不得因更強而跳過規劃、Reality、Knowledge、Prose、盲讀或提交流程。
3. 其他模型不得因更弱而靜默省略功能；未通過 Luna baseline 就降級或停止。
4. 正典、state、Graphify、Reality、檔案與 commit 由宿主持有；任何模型都只是候選生成器。

## 驗證要求（非實測結果）

以下是部署者必須執行的檢查；表內沒有預先通過的結果。

| Probe | 驗收要求 | 未驗證時的邊界 |
|---|---|---|
| 固定目標語言短文字 | 精確遵循指定輸出 | 不授予 text-ready |
| JSON object | 可解析且符合 schema | 不授予 structured-ready |
| 原生 tool call | 保存原生 tool_calls 與參數 artifact | 不授予 tool-ready |
| 資訊抽取與長上下文取用 | 在明示 envelope 與來源下核對已知答案 | 不從單一針測推導完整小說能力 |
| NPC plan | actor、knowledge、Reality 與核准行動一致 | 不授予自主提交權 |
| scene manifest | 核對 facts、protected unknowns 與 handoff | 不接受只有合法 JSON 的候選 |
| manifest→正文 | 非空、無事實錯接且通過 prose Gate | 不將流暢度當成正確性 |
| facts＋issues→局部修復 | 最多兩次內通過要求的 Gate | 未通過即停止或 fallback |
| 隔離盲讀 | 與生成回合隔離且保存結果 | 同模型審稿不宣稱獨立模型審稿 |

能力判定必須依實際驗證 artifact；本文件不給任何模型預設 L1–L5 等級。宿主可在通過自己的檔案、Graph、Reality 與 Gate 測試後維持 host-managed L4；這不提高模型本體的工具或正典權限。

## Luna-safe 任務粒度

禁止把以下工作合成一個 prompt：

```text
讀全部小說 → 自己規劃 → 自己寫正文 → 自己檢查 → 自己更新正典
```

標準拆分：

```text
Host 取 active context
→ Luna 產 scene manifest JSON
→ Host 驗證人物／事實／知識／Reality／玩家邊界
→ Luna 依核准 manifest render 正文
→ Host fact alignment＋deterministic prose Gate
→ Luna 只按 issues 做局部修復（最多 2 次）
→ 隔離 Luna run 做 scene-only blind read
→ Host 驗證 hash／delta
→ Host 原子 commit
```

每個 Luna 回合只能有一個主要工作：extract、plan、render、repair、blind-read 其一。

## Prompt 契約

每個 Luna prompt 使用明確區塊：

- `<canon>`：本場唯一可用事實；
- `<facts>`：actor、source、valid time；
- `<unknowns>`：必須保留的未知；
- `<player_boundary>`：不得替玩家做什麼；
- `<scene_function>`：六類之一；
- `<output_schema>` 或 `<requirements>`；
- `<forbidden_prose>`：只放本場高風險模式，不灌整庫反例。

避免：

- 完整 current.yaml／全部 open_pressure；
- 幾十回合原文；
- 一次要求兼顧十多個抽象原則；
- 「自然一點／有文學感」等無法驗證指令；
- 要 Luna 自己宣稱已通過 Gate。

## 必要外部防護

以下通用失敗模式必須由宿主檢查；並非某個模型的實測傾向：

1. **過度保守／玩家 ping**：manifest 必須要求至少一個由正典支持的 NPC 低風險自主行動；若合理上真的無行動，場景標 `rest／transition`，不假造進展。
2. **模板填充**：取消最低字數；禁止香氣、微微、熱氣、視線、等待安排只為收尾。
3. **事實錯接**：每個 facts item 帶 `actor` 與 `source`；render 後逐條對齊。
4. **重複事實**：同一 focal change 正文通常只寫一次；重複必須有新功能。
5. **模糊指涉**：關鍵「兩人／兩位／有關／那條線」需唯一前件或標記刻意未知。
6. **自評偏誤**：blind reader 使用隔離 run，不給 state、manifest、作者意圖或前一 Gate 結論；作者回饋是最高校準來源。

## 跨模型等價契約

換用任何其他模型時，仍必須跑同一組 Luna baseline fixtures。可接受差異：措辭、節奏、局部創意；不可接受差異：

- 事件、知識、時間、人物或物件 delta 不一致；
- 模型跳過或合併 pipeline；
- 更強模型自行使用工具、寫檔、改 state 或擴大 NPC 行動；
- 更弱模型刪除 Reality、Graph、盲讀或正典同步；
- scaffolded prose 在兩次修復後仍有 P0 或 blind-reader fail；
- 同一 fixture 的功能結果與預期契約顯著不同。

模型更換驗收：

```text
P1 text exact
P2 JSON schema
P3 tool artifact（可選能力，不影響 baseline；未驗證則 host-only）
P4 host Reality／Graph／state regression
P5 scene manifest facts／unknowns／player boundary
P6 scaffolded prose deterministic gate
P7 fact alignment
P8 isolated blind read
P9 reopen project continuity
```

只有 P1、P2、P4–P9 通過，才可標記為「Luna-baseline compatible」。工具能力較強不會提高小說權限；工具能力較弱也不影響 host-managed L4，但不能自行 agent commit。

## 品質差異上限

不同模型文句不必完全相同；相容性依契約測試判定，不能用模型名稱保證能力。切換後需符合：

- 同一事件與狀態差分；
- 零新增 P0；
- 兩次局部修復內 deterministic prose Gate PASS；
- 隔離盲讀 PASS；
- 人物／Reality／Knowledge／玩家控制 Gate PASS；
- 作者抽查若連續兩次判明顯退化，該模型停用於正文生成。

## 退化策略

- JSON 不穩：只作 prose render，不作 plan／state proposal。
- Facts alignment 不穩：縮短 context、逐 actor 分開 render；仍失敗則停用。
- Prose Gate 連續失敗：降低到局部改句，不生成整場。
- Blind read 不穩：blind reader 改由宿主規則＋作者抽查；不得虛稱獨立審稿。
- 工具不可驗證：固定 host-only，模型無提交權。

## 回歸資產

倉庫內 `fixtures/synthetic-reasoning-budget-example.json` 與 `fixtures/synthetic-task-capability-example.json` 是獨立編寫的示意資料，明示 `synthetic: true`，不可當作驗收結果。

部署者應把實際 probe 輸出保存在來源 checkout 以外的私有 `capability-reports/` 目錄，並記錄 endpoint、模型、日期、設定與來源 artifact。每次更換模型、endpoint、prompt contract 或重大 Gate 後，重跑同一 fixtures，保存 capability delta。

`luna_baseline_gate.py` 為相容既有 report，保留 `isolated_luna_blind_read` probe 欄位名稱；該欄位表示按本契約完成的隔離盲讀，不能由名稱推定真實模型通過測試。
