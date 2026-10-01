---
name: novel-model-capability-compatibility
version: 1.4.2
description: 當使用者切換 AI／本地模型、比較模型、部署 Novel OS 到新框架、遇到工具呼叫／結構化輸出／記憶／圖譜／現實狀態功能遺失，或要求模型可替換但小說功能不能降級時使用。建立模型能力契約、探測矩陣、adapter、fallback、能力差異報告與切換後回歸驗證；不把純文字可回覆誤判成完整小說系統相容。
---

# Novel Model Capability Compatibility

模型是可替換執行層，不是 Novel OS 的功能定義。換雲端、本地、不同供應商或不同 API endpoint 時，必須維持 Novel OS 的**能力契約**；若不能維持，必須明確標記降級、提供 adapter 或切回相容模型，不能靜默遺失功能。

## Luna 最低模型基準

Novel OS 的通用工作流使用保留名稱為 Luna baseline 的**示意設計契約**，詳細要求見 `references/luna-baseline-contract.md`。此名稱不是實測報告、模型可用性或當前能力保證；任何模型都只能在同一外部腳手架內工作，且必須通過相同 fixtures。更強模型不得跳過規劃、Reality、Knowledge、Prose、盲讀與 host commit；較弱模型不得靜默刪除功能。

Luna baseline 固定把模型視為候選生成器：一回合只做 extract／plan／render／repair／blind-read 其中一項。state、Graphify、Reality、工具、檔案與正典提交由宿主持有。未取得可驗證原生 `tool_calls` artifact 時，模型本體最高只標 L2；宿主可在外部維持 L4。

跨模型相容的目標不是句子完全相同，而是：事件／狀態差分一致、零 P0、兩次局部修復內 prose Gate PASS、隔離盲讀 PASS、玩家控制與知識邊界一致。切換模型只允許局部措辭與創意差異，不能造成系統能力或權限差異。

## 核心原則

1. **能力先於模型名稱**：不以模型品牌、參數量或「能回文字」判定相容；以實際 probe 結果判定。
2. **功能契約不可被模型改寫**：事件帳本、持久檔案、Graphify、Reality Card／Gate、Feeling → Thought → Action、章後同步、玩家控制邊界與正典分層屬 Novel OS 契約。
3. **Chat／Responses／原生本地端點分開測試**：不要假設一個 endpoint 的成功代表另一個 endpoint 的工具格式也成功。
4. **工具成功不等於文字成功，文字成功也不等於工具成功**：至少分開測試純文字、結構化 JSON、原生 tool call、工具參數、連續工具回合與錯誤恢復。
5. **能力降級必須可見**：輸出 `capability-report.json`、記錄模型／供應商／endpoint／參數／日期／測試結果；失敗不可被標成 PASS。
6. **狀態與模型解耦**：模型不能成為唯一記憶；正典、事件、Graphify、Reality state 和 gate 必須由外部持久層保存。
7. **替換前後要做同一組回歸**：切換模型後重新跑小說狀態、圖譜、Reality Gate、工具、JSON 與長篇連續性 smoke test。
8. **本地模型可用性要分層**：loaded、text-ready、json-ready、tool-ready、agent-loop-ready；`Model is unloaded` 或空工具參數不能算可用。
9. **安全 fallback**：工具回合失敗時，優先切到同能力模型或停在可恢復狀態；不要把未執行的工具結果、未更新的圖譜或未通過的 Gate 假裝完成。
10. **最弱模型優先編譯**：互動與長篇宿主先把工作編譯成單一 `intent_extract`／`npc_plan`／`scene_manifest`／`render`／`repair`／`blind_read` 任務包；模型只填固定欄位。能力越低，任務越窄、context 越短、可選值越少；不因 JSON 不穩就把 state／memory／Graph 權限交給自然語言輸出。
11. **實測能力可否決理論等級**：模型即使能產生 schema-valid JSON，只要語義 probe 失敗，就不得標 L2 或取得 `intent_extract`；若純文字／render 連續空輸出或 reasoning 吃滿額度，該 endpoint 對 Novel OS 任務標 L0。宿主仍可維持模型外 L4，不得為了「用得上模型」放寬權限。
12. **同一個模型的 task-specific routing**：capability report 必須逐項記 `intent_extract`、`npc_plan`、`scene_manifest`、`render`、`repair`、`blind_read`，不能以單一總分讓通過 JSON 的模型自動取得正文或規劃權。

## 小模型與 64K Context Phase 0／Phase 1

本版本新增 `references/small-model-compatibility-contract.md` 與 `fixtures/host-function-availability.json`。宿主功能與模型能力分離：即使模型為 L0，event／state／Graph／Reality／memory／storylet／Gate／commit 仍由宿主完整維持；只有失敗的候選任務降級或進入 fallback，不得偽稱完成。

`immersive-interactive-fiction/scripts/novel_judge/context_budget.py` 提供 deterministic token-aware admission：支援 CORE／ACTIVE／EVIDENCE／ARCHIVE 來源層、64K envelope、system／output／safety 預留、保守 tokenizer 估算、required source fail-closed。所有模型預設 `lossless-addressable`：宿主自己保存可定址原文，窗口只限制當次內嵌量，overflow 只留 id／hash，不摘要、不忘掉。`lossy-admission` 必須明示才可啟用。`compile_model_task()` 已把 admission record 與 `context_policy` 綁入 task packet／task hash；長篇 context pack 亦支援 `--context-window`、`--context-policy` 與 task profile，並將 admission manifest 落盤。

目前仍不宣稱任何 9B 模型可自主完成所有正文任務；下一階段要用實際 endpoint 做 8K／16K／32K／48K／64K 階梯與逐 task benchmark。

### 本地 reasoning endpoint 規則

對具 reasoning 功能的本地 OpenAI-compatible endpoint，若 probe 顯示 reasoning tokens 佔滿 output budget、正文為空或 `finish_reason=length`，不得把它當正文模型失敗後盲目重試。adapter 必須查明該 endpoint 支援的 reasoning／thinking 設定，明示採用的參數（例如端點確實支援時的 `reasoning_effort: "none"`），並重新測試；`enable_thinking=false`／`chat_template_kwargs` 不是通用等價物，只有 provider 回報實際生效才可採用。

本地 renderer 預設 contract：host renderer-only packet、temperature 0.2–0.5、保留足夠 output budget、重複 Gate、最多兩次局部修復；不能直接把普通 chat／長歷史對話當 production prose path。`fixtures/synthetic-reasoning-budget-example.json` 以完全虛構的數值示範空正文與 output budget 的診斷格式；`fixtures/synthetic-task-capability-example.json` 示範 retrieval、schema、semantic 與逐 task 授權的區別。兩者都不是實測、能力背書或設定根因證據，不能據以啟用真實模型。


| 能力 | 最低可接受結果 | 測試要求 | 失敗時 |
|---|---|---|---|
| 純文字生成 | 能產生繁中／目標語言正文 | deterministic short response | 可作文件模式，不能宣稱完整 agent |
| 結構化 JSON | 回傳可解析且符合 schema | state／Reality Card／event fixture | 使用外部 parser、修復回合或標 `json_unavailable` |
| 原生工具呼叫 | `tool_calls` 有正確名稱與非空參數 | required tool probe + schema validation | 改 Chat／Responses adapter、換模型或停用 agent tools |
| 連續工具回合 | 工具結果能放回對話並繼續 | 2-step tool loop | 降為單步工具或人工執行，不可假稱完成 |
| 檔案讀寫 | 可回讀同一 project root | write→new run→read | 使用外部 host adapter；不能靠 context 宣稱持久化 |
| Python／process runner | 能跑 state／graph／gate scripts | fixture command + exit code | 手動 checklist，標記未執行 |
| Graphify | 可 validate、affected、timeline、snapshot | graph fixture regression | 保存 JSON，禁止宣稱查詢／匯出完成 |
| Reality engine | 能產生 Reality Card 並跑 Reality Gate | hungry/cold/capacity fixture | 不得生成未校準正文；切換到相容執行器 |
| 長期連續性 | 可讀事件、時間、知識與分支 | reopen project continuation | 只能文件模式，必須明示無自動連續性 |
| 第二模型審稿 | adapter 回傳明確 success／unavailable | review schema probe | 人工／同模型 gate，不能偽稱獨立審稿 |

## 能力等級

```text
L0 unavailable       endpoint／模型不可用
L1 text-ready         純文字可回覆
L2 structured-ready   JSON／schema 可解析
L3 tool-ready         原生工具呼叫與非空參數通過
L4 state-ready        可讀寫 project、跑 state／graph／reality gate
L5 agent-ready        連續工具回合、錯誤恢復、狀態同步、正典 gate 全通過
```

Novel OS 的完整互動／長篇 agent 模式至少需要 **L4**；需要自動工具代理時需要 **L5**。L1／L2 只能作文件或人工輔助模式。

## 模型切換流程

```text
保存目前 active model + capability report
→ 讀取 project state／graph／Reality state
→ 停止未完成工具回合，保存可恢復 checkpoint
→ 探測新模型 endpoint
→ 執行 text／JSON／tool／multi-step／state probes
→ 比對必要能力契約
→ 建立 adapter 或選 fallback
→ 重跑 Novel OS regression
→ 只有 Gate 通過才切換為 active
→ 輸出 capability delta + degraded capabilities
```

## 必測 probe

### P1 純文字
要求固定短句，驗證 endpoint、編碼、延遲與錯誤格式。

### P2 JSON
要求回傳指定 state schema；檢查 JSON 是否可解析、欄位是否完整、是否混入 markdown。

### P3 工具名稱與參數
提供 `local_health_check(status)`，要求 `tool_choice=required`；檢查：

- 是否真正回傳 `tool_calls`，不是把 JSON 寫成普通文字；
- function name 是否正確；
- arguments 是否非空；
- arguments 是否符合 JSON schema；
- `finish_reason` 是否因 reasoning／length 提前結束。

### P4 連續工具回合
第一次呼叫工具，注入結果，再要求第二次工具或最終回覆；測試 message role、tool_call_id 和 adapter 格式。

### P5 Reality／Graph fixture
給定已知事件：飢餓、冷、沒有食物、可取得水；要求模型先讀 Reality Card，再產生短反應。模型不能把狀態引擎本身交給模型臨時猜；宿主必須能執行外部 Reality script。

### P6 長篇重開
寫入 event T001、關閉 run、重新開啟，要求讀取並產生 T002；檢查不是靠上下文殘留。

## Endpoint／adapter 規則

- OpenAI-compatible Chat Completions：使用 `messages`、`tools`、`tool_choice`，保存 raw response。
- Responses API：使用宿主原生 input／tool item schema；不得把 Chat message 直接當 Responses body。
- 本地 OpenAI-compatible server：先 `GET /v1/models`，再以實際 model ID 測 Chat、JSON、tool；模型 loaded 狀態單獨記錄。
- reasoning model：工具 probe 必須給足 output budget，並記錄 reasoning 是否佔用額度；必要時把 thinking level 降為 off／low，但不能假裝工具格式因此一定正確。
- 不同模型的 system／developer／tool role 行為不得靠猜測；adapter 要保存原始錯誤、轉換後 body 摘要與 applied extras。
- API key、OAuth token 和 cookie 不寫入 capability report。

## 降級矩陣

```text
L5 → L4：停用自動連續工具回合，保留外部狀態與人工／單步工具
L4 → L2：保留 JSON／Reality Card／Graph scripts，由宿主人工執行工具
L2 → L1：文件模式；模型不得聲稱已更新 state、graph 或 gate
L1 → L0：停止生成，要求修復 endpoint／切換 fallback
```

降級報告至少包含：`active_model`、`previous_model`、`endpoint_kind`、`level_before`、`level_after`、`passed`、`failed`、`disabled_features`、`fallback_model`、`report_path`、`timestamp`。

## 交付前檢查

- 是否測試過實際 endpoint，而非只看模型清單？
- 是否分開測純文字、JSON、工具、連續工具與 state？
- 是否驗證工具參數不是空物件？
- 是否保留原始錯誤與 capability delta？
- 是否確認 Reality／Graph／長篇 state 不依賴模型上下文？
- 是否測試切換後重新開 run？
- 是否清楚列出降級功能與 fallback？
- 是否避免輸出秘密、API key、OAuth token 或 cookie？
