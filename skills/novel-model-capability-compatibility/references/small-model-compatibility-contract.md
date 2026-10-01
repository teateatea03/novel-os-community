# Small-Model Compatibility Contract

版本：1.1.0（host-owned lossless default）

## 目的

9B 以下本地模型是可替換的候選生成器，不是 Novel OS 的權威執行層。模型能力不足時，宿主仍必須維持事件、狀態、Graphify、Reality、記憶、Storylet、Gate、分支與 commit 的可用性；不可把模型失敗偽裝成成功。

## 能力與功能分離

- `model-capability-report.json`：記錄實際 endpoint／模型各 task 的測試結果。
- `host-function-availability.json`：記錄不論模型等級，宿主功能與 fallback 是否可用。
- 模型的 L0–L5 不等於 Novel OS 的功能等級。
- state、event、Graph、Reality、Knowledge、Agency、Gate、commit 永遠由宿主驗證與執行。

## 受控任務

模型一次只執行一個微任務：`intent_extract`、`npc_plan`、`scene_manifest`、`render`、`repair`、`blind_read`。每個結果必須帶當前 task hash；schema 合法不代表語意、權限、正典或品質通過。

## L0–L2 fallback

| 模型任務 | L0 | L1 | L2 | L2 + host |
|---|---|---|---|---|
| intent | deterministic router／作者澄清 | 純文字候選，host parse | constrained JSON＋semantic validation | 可進 production candidate |
| NPC plan | storylet／規則候選 | 只提供理由或排序 | 有限 enum JSON candidate | host 檢查 actor／knowledge／Reality |
| scene manifest | host skeleton | 小模型填單欄 | constrained manifest | host 檢查 handoff／unknowns |
| render | deterministic skeleton／作者／fallback model | 窄場景純文字或片段 | facts-bound structured render | host prose／continuity／Reality Gate |
| repair | deterministic issue patch／作者 | 指定句局部修復 | issue-bound JSON repair | 最多兩次，否則升級 |
| blind read | deterministic checks | 規則＋弱模型提示 | schema reviewer | 不能單獨批准正文 |
| commit／state／Graph／Reality／Gate | host full | host full | host full | host full |

## fallback ladder

1. 同模型縮短 context。
2. 將任務拆成更小欄位。
3. 改成局部 render／repair。
4. 使用 host deterministic skeleton 或 storylet。
5. 要作者補最小決策。
6. 切換已驗證 fallback model。
7. fail closed，保存 activity、輸入 hash、失敗原因，不寫 canonical。

## 64K context 原則

`context_window=65536` 是 endpoint envelope，不是每次都把 65536 token 當輸入。每個 request 必須保留 system／schema、輸出預留與 tokenizer 不確定性；Admission Controller 必須記錄估算、選取、淘汰、壓縮、來源 hash 與 admission 結果。

上下文層級固定為：`CORE`（任務契約與權限）、`ACTIVE`（當前場景與 Reality）、`EVIDENCE`（時間線／記憶／規則／圖譜）、`ARCHIVE`（按需查詢）。超額時只能依 deterministic priority 淘汰，不能靜默尾端截斷。

## Host-owned lossless-addressable 原則

Novel OS 自己實作 Astra 那種「不摘要、不忘掉」的上下文，**不依賴任何特定模型**。9B／64K 與百萬級窗口走同一條政策；窗口只決定這次能內嵌多少原文。

- `lossless-addressable`（**所有模型的預設**）：原文原樣內嵌；塞不進當次 prompt 的來源改列 `addressable_overflow`（id／hash／provenance），**不得摘要、不得標成忘掉**。模型或宿主下一回合可依 id 回讀原文。
- `lossy-admission`：必須明示 `context_policy=lossy` 或 `NOVEL_OS_CONTEXT_POLICY=lossy` 才可啟用。可壓空白、可淘汰 ARCHIVE／低優先來源；`forgotten_sources` 等於被淘汰來源。這是實驗路徑，不是 Novel OS 預設。
- 正典仍是事件帳本，不是模型窗口。窗口再大也不能讓模型寫 state／Graph／commit。
- 更強模型不得合併 extract／plan／render／repair／blind-read，也不得跳過 Reality／Knowledge／Gate。
- 不能把「64K 可接受」誤報成「64K 全部被模型有效理解」；未內嵌來源必須仍可定址。

## 禁止事項

- 不能因模型回傳普通文字就宣稱 tool call 已執行。
- 不能因 JSON valid 就讓模型寫檔、改 state、改 Graph 或提交正典。
- 不能把 reject、stale、未驗證 projection 或模型自述當角色記憶。
- 不能把「64K 可接受」誤報成「64K 全部被模型有效理解」。
