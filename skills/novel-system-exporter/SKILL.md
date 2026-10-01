---
name: novel-system-exporter
version: 2.10.1
description: 當使用者要求匯出／分享／移植整套小說系統、把小說寫作工作流交給其他 AI、建立可安裝的小說技能包、在新環境自動部署長篇小說／斷更小說補完／角色研究／世界觀／行為校準／關係圖譜／互動小說能力，或要求「小說系統匯出技能」「novel OS export」「portable novel skill」時使用。將已驗證的小說系統封裝為可攜 Skill bundle，安裝後以 novel-operating-system 作為單一入口，自動佈置其餘協作技能與本地專案骨架；匯出時必須先說明目標 AI 框架所需的 Skills runtime、檔案／shell／Python、圖譜、持久儲存、模型審稿與研究工具依賴，並給出可執行的 adapter／降級步驟；不匯出使用者私人小說內容，除非另行明確要求。
---

# 小說作業系統匯出器

將本機的小說能力封裝為**可安裝、可驗證、可離線使用**的「Novel OS」。匯出的不是某個專案的故事資料，而是可重複使用的工作流、模板、檢查器與狀態架構。

## 匯出範圍

核心入口為 `novel-operating-system`；它會協調 16 個專業能力，連同入口共 **17 個 Skill**：`public-web-research` 負責安全、可恢復、可稽核的公開 HTTP(S) acquisition、raw／Markdown／candidate staging 與 browser/Crawl4AI 可選升級；`novel-reality-state-engine` 負責跨作品事件、時間、資源、生理／認知容量、心理機制與正文 Reality Gate；`novel-model-capability-compatibility` 負責模型／供應商／endpoint 的能力契約、probe、adapter、fallback 與切換後回歸；`novel-sensory-sound-prose` 負責可重用的聽感、狀聲詞與五感文筆層。

1. `long-form-novel-writer`：長篇規劃、正文、連續性帳本、章後 gate、快照與改綱級聯。
2. `novel-character-deep-digger`：先分類 `real`／`novel`／`anime`／`film`／`other`，再做角色／公開原型研究，分離明示、推論與提案。
3. `human-behavior-personality-consultant`：依主體分類與版本正典進行 Evidence E1–E6、Actor 狀態分布／Agent／Author、多時間尺度、情境強度、保護／抑制、Prediction Lock、反事實與章後校準；可攜包必須包含可執行校準工具與測試。
4. `novel-worldbuilding-architect`：世界規則、制度、資源、認知矩陣與二階後果。
5. `novel-style-craft-director`：可執行風格契約、類型承諾與漂移檢查。
6. `novel-human-voice-editor`：內容鎖定後的人味、台灣繁中、角色聲音與節奏文字修訂；可選用 Humanizer-zh 31 檢查點，但不能冒充未隨本包分發的 `lieflat-less-ai-tone` 白名單 pass；缺少時記為未執行。
7. `knowledge-relationship-graph`：Graphify 相容的時間化、可追溯關係圖譜與角色主體分類欄位，並以 `properties.name_zh` 支援中文查詢而不覆蓋原始名稱；官方中文譯名優先，無官方譯名採原文讀音音譯。
8. `character-database-builder`：按主體分類保存真人／小說／動漫／電影／其他角色與來源證據，並在必要時建立 `properties.name_zh` 中文查詢欄位；官方中文譯名優先，無官方譯名採原文讀音音譯。
9. `immersive-interactive-fiction`：第二人稱自由輸入、NPC 自主、狀態持續的互動小說；含作者糾錯升格契約與非正典 `author-corrections` 帳本，不另開技能。
10. `unfinished-novel-completion`：斷更／未完成作品的來源、版本、文本正典、作者意圖、可行性、補完分支、權利與 AI 溯源。
11. `novel-world-database-builder`：小說世界／地點／派系／資源／規則／事件／主張的 Graphify 資料庫、來源、認知層、版本與章節同步；所有含非中文名稱的節點另保存 `properties.name_zh` 查詢欄位，原始 `label` 不變；官方中文譯名優先，無官方譯名採原文讀音音譯。
12. `special-object-database-builder`：道具／鎧甲／機體／載具／武器／神器／裝置的版本、能力、規格、能源、限制、持有／操作與生命週期 Graphify 資料庫；所有含非中文名稱的節點另保存 `properties.name_zh` 查詢欄位，原始 `label` 不變；官方中文譯名優先，無官方譯名採原文讀音音譯。
13. `novel-reality-state-engine`：跨作品的事件→時間／資源→生理負荷→認知容量→Feeling／Thought／Action→可行為動作→正文 Reality Gate；把世界狀態、角色當下能力與圖譜連動成硬約束。
14. `novel-model-capability-compatibility`：模型／供應商／endpoint 的能力契約、text／JSON／tool／multi-step／state probes、L0–L5 能力分級、adapter、fallback 與切換後回歸；保證換本地模型時不靜默遺失 Novel OS 功能。
15. `novel-sensory-sound-prose`：跨作品聲音分層、狀聲詞紀律、環境音／人聲／動作聲與五感 prose contract；只處理文筆感官層，不取代角色聲線、事件正典或 Reality Gate。
16. `public-web-research`：只處理公開、免登入 HTTP(S)，提供 SSRF／redirect／robots 安全閘門、raw／safe Markdown、BFS／best-first、event hash chain、checkpoint／resume、candidate staging 與 browser/Crawl4AI 可選升級；不把 crawler 結果直接當 claim 或寫入 Graphify。

不包含：任何使用者私人專案、角色資料庫、聊天紀錄、API key、token 或外部模型設定。若使用者需要**連同某部小說移交**，先另做專案快照、審查敏感資料，再使用封包內的 project handoff 工具。

## Host-first runtime v2.6 匯出要求
可攜包必須包含 Novel Judge 的 branch 級跨程序鎖、transaction journal／sidecar recovery、正式 schema migration registry、模糊輸入 fail-closed router、NPC plan lifecycle、episodic memory／evidence-backed reflection／retention、單一微任務 `model_tasks` 編譯器、local model JSON Schema／GBNF adapter contract、task-specific capability routing、durable model activity 的 schedule／lease／retry／cancel／stale／restart recovery、runtime build／event transition contract replay compatibility、golden-history fixture、bounded storylet solver、hash-verified event index、corrupt-tail repair、archive compaction／maintenance rollback、index-independent archive manifest integrity gate、temporal typed Graph projector、長篇 Markdown projector、author console、隨機事件 `off`／`on-suggestion` branch 開關、非正典 suggestion runtime／starter pool／audit／統計校準，以及長篇／互動共用 event kernel。Host adapter 若不能提供可靠跨程序鎖，必須明示 single-writer 降級；不得宣稱可安全多會話提交。L1 模型只允許通過實測的 render／局部 repair，L2 才可做通過語義 probe 的候選結構，所有級別都沒有 state／Graph／檔案 commit 權限。

- model-activity v2 fencing token：claim 每次產生新的 lease token，complete 必須同時匹配 owner／token 且 lease 未過期；schedule／recovery 都在 branch lock 內。
- active event segment 也由 manifest 保存 hash／bytes／count；刪除 index 後竄改 active log 不得重建為新基線，僅接受 transaction journal 可證明的單筆 fsync 後崩潰 suffix。
- `session_id`／`branch_id`／`checkpoint_id`／`turn_id` 等檔案型識別碼只能是單一安全 segment，禁止 `/`、反斜線、NUL、`.` 與 `..`。
- random-event request 具 branch-scoped request ID 冪等性，重試重播已記錄方向而不重抽；audit 有 manifest＋hash chain，suggestion 綁定 source state，過期方向不可直接產生 adoption handoff。

- random-event request 除 branch-scoped request ID 外必須保存 request fingerprint；同 ID／同 fingerprint 才能重播，同 ID／不同 source state、algorithm、pool、trigger、seed 或 window 必須回 idempotency conflict。Suggestion audit append 與 manifest 更新須由可恢復 journal 連成交易。
- model-activity v1 必須經明示 migration registry 升 v2；舊 running lease 一律失效並重新 claim，無 token complete 永遠拒絕。
- event integrity verification 必須純讀，不建立健康檢查暫存檔。Portable smoke 必須執行 audit、active manifest、activity schedule／claim／complete／migration 的真實 subprocess SIGKILL matrix。
- 完整性聲明預設只能是 `local-integrity`；沒有專案目錄外的簽章、WORM 或遠端 append-only checkpoint 時，不得宣稱抵抗具完整檔案寫入權的攻擊者。

隨機事件建議層仍必須預設 `off`；關閉時不抽取、不提示、不寫 audit。`on-suggestion` 只可產生 `NON_CANONICAL_SUGGESTION`，所有 State／Graph／Knowledge／timeline／prose patch 為空，採用後仍須走正常 Reality／Knowledge／Agency／Behavior／World／Canon Gates。匯出器與 smoke test 必須包含 `novel_judge.test_runtime_v08`、`novel_judge.test_runtime_v09`、`novel_judge.test_runtime_v10` 與 `novel_judge.test_upgrade_v25`；不得把 suggestion audit 混入 canonical event log，也不得自動增加尚未核准的頻率或 Storyteller profile。

## 現實狀態引擎匯出要求
可攜包必須包含 `novel-reality-state-engine`、其 schema／研究規劃／測試夾具與可執行 Reality Card／Reality Gate 工具。匯出器需將它列為 Novel OS 核心協作技能，並驗證每個長篇／互動宿主適配契約都宣告事件帳本、狀態計算、Feeling → Thought → Action 與生成前後 Reality Gate；不能只匯出說明文件而漏掉計算器。

## 模型能力相容性匯出要求
可攜包必須包含 `novel-model-capability-compatibility`、capability report schema／fixture、probe script 與 L0–L5／fallback 規則。宿主適配契約必須宣告實際 endpoint 的 text／JSON／tool／multi-step／state probes；若目標模型未通過必要能力，匯出包只能標示降級模式，不能宣稱完整 Novel OS 相容。



在匯出、交付或教導安裝前，先讀 `references/platform-compatibility.md`，並依目標框架明確交付以下內容：

1. **系統成分**：本包是 `SKILL.md` 規約、Markdown／JSON 模板、Python 檢查器與 Graphify 相容 JSON 圖譜；它不是自帶模型、資料庫、雲端帳號或搜尋服務。
2. **最低完整模式依賴**：Python **3.10+**（建議 3.11+）、可執行 process 的 shell、可持久讀寫的 UTF-8 檔案系統、可安裝／載入多技能的 agent framework；ZIP 分發另需解壓能力。
3. **選用依賴與功能邊界**：
   - 核心 17 個 Skill（1 個入口＋16 個協作技能）：內部相對路徑協作，需整包同層保留；其中 `novel-reality-state-engine` 不能只以 prompt 取代，至少需要事件／狀態 JSON 與可執行 Reality Gate；`novel-model-capability-compatibility` 不能只以模型名稱或純文字測試取代，必須跑實際 text／JSON／tool／state probes。
   - `networkx`：圖譜 path／affected 與 GraphML；
   - `graphifyy` + `networkx`：HTML、社群、Cypher 匯出；
   - Git：受 gate 保護的 commit（快照腳本仍可不用 Git）；
   - web/browser：公開資料研究；
   - 第二模型／sub-agent：獨立審稿；原 `minis-model-use` adapter 必須在其他框架替換。
4. **目標框架分類**：判定它是 A 原生 Skills+shell、B 自訂 agent+adapter、C 只支援知識檔，還是 D 僅 system prompt；不可把 C／D 宣傳為全自動部署。
5. **適配與驗收**：依 `host-adapter-contract.md` 逐項指定 skill router、檔案工具／持久 storage、Python runner、web tool、模型 review adapter，以及 `NOVEL_PROJECTS_ROOT`、`CHARACTER_DATABASE_ROOT`、`CHARACTER_DATABASE_WORK_ROOT`、`WORLD_DATABASE_ROOT`、`WORLD_DATABASE_WORK_ROOT`、`SPECIAL_OBJECT_DATABASE_ROOT`、`SPECIAL_OBJECT_DATABASE_WORK_ROOT`、`INTERACTIVE_PROJECTS_ROOT` 等路徑映射；再使用 `platform-compatibility.md` 的框架對照與驗收清單。
6. **驗收與降級**：列出可跑的 smoke test；不能跑時列出停用項、人工替代流程與不可聲稱已完成的功能。

沒有指定目標 AI 時，交付 ZIP 的同時必須附上 `platform-compatibility.md`，並先問或建議使用者提供：框架／版本、Skills 或 system-prompt 入口、shell/Python 權限、持久儲存、是否可掛 web／第二模型工具。

## 快速執行

### 1. 更新後封裝

當原始技能有修改，先刷新 payload，再建立 ZIP：

```bash
python3 scripts/build_novel_os_bundle.py refresh \
  --source-root <SKILLS_ROOT> \
  --bundle-root .
```

目前封包版本：`v2.10.1`。

若目前就在本技能資料夾，`--bundle-root .` 即可。不可從輸出 ZIP 反向覆蓋來源技能。

### 2. 交付到新 AI／新環境

交付完整 ZIP **及** `references/platform-compatibility.md`。先判定目標框架的能力等級，不能假定「匯入 ZIP」等於對方已安裝或已能自動協作：

- **A｜原生 Skills + shell + 持久檔案**：以安裝器安裝，保留 **17 個**技能（總入口＋十六個協作技能）的同層資料夾，註冊 `novel-operating-system` 作主入口；可跑 smoke test。
- **B｜自訂 Agent／工具框架**：整合者須把入口轉為 system/developer instruction 或 router，將讀寫檔、Python process、web、持久 storage 和第二模型審稿逐一映射；`independent_review.py` 的 `minis-model-use` 必須改成該框架 adapter。
- **C｜知識檔／Project instruction 平台**：匯入整個 `skills/` 子樹；系統可提供流程與模板，但無法承諾安裝、CLI gate、圖譜匯出或跨聊天持久化。
- **D｜單一 system prompt**：只移植總入口與必要規則；由整合者手動保存狀態與挑選專業模組，明確標為手動降級。

完整的依賴、套件安裝、框架對照與驗收清單見 `references/platform-compatibility.md`。

### 3. 驗證匯出

每次發佈前必須：

```bash
python3 scripts/build_novel_os_bundle.py verify --bundle-root .
python3 scripts/verify_novel_os.py --profile full --bundle-root .
python3 scripts/install_novel_os.py --target /tmp/novel-os-test --smoke-test
```

驗證內容：payload manifest／SHA-256、Python 編譯、長篇專案初始化、關係圖譜驗證、互動狀態 fixture 與長篇回歸測試。任何 FAIL 不交付 ZIP。

- **補完工具**：`unfinished-novel-completion` 提供來源 hash／版本差異／作者意圖分層／可行性與分支帳本／權利邊界／溯源報告／補完 Gate；所有未完成作品工作都必須保留這些檔案，不能只交付一段續寫正文。
- 安裝器拒絕覆寫同名技能；更新必須加 `--upgrade`，且會先建立 `backups/`。
- `novel-operating-system` 是唯一推薦的觸發入口；其他技能仍可被單獨呼叫。
- 安裝後使用 `novel-operating-system/INSTALLATION.json` 確認版本、來源 hash、安裝日期與完整性。
- 主機技能目錄可任意指定；所有核心內部路由依相對路徑，Python 初始化器依 `__file__` 尋找相鄰技能。
- 主機若要執行完整工作流，必須有 Python 3.10+、可寫檔案系統和 process runner；圖譜視覺化另需要 `networkx` 與 `graphifyy`，Git／web／第二模型均為選用增強。
- `independent_review.py` 目前依賴 Minis 的 `minis-model-use`；在任何其他 AI 框架都必須改寫成其模型／sub-agent adapter，或停用並記錄為未執行，不能偽稱獨立審稿完成。
- 若目標 AI 沒有 shell／檔案權限，交付單一入口 Skill 和所有資源檔；它可遵循流程，但無法自動建立本地檔案、執行 gate 或保證持久狀態。

## 品質與安全門檻

1. 匯出前不能默默略過任一核心技能。
2. 檢查 manifest 是否只有 allowlist 中的檔案；拒絕 `.git`、`__pycache__`、`.env`、私有專案、憑證與二進位暫存。
3. 不把推論、真人公開資料與虛構提案混成正典；保留來源／信心分層規則。
4. 不把 Git commit、圖譜索引或機器審核當作正典；作者指示與已定稿正文優先。
5. 清楚告知受限於目標模型／供應商的獨立政策；本技能無法覆寫對方的平台規則。

詳細的跨平台匯入與「僅文件模式」說明見 `references/portable-install.md`；目標框架的依賴矩陣、套件、adapter、能力等級、框架對照與驗收清單見 `references/platform-compatibility.md`；給 LangGraph／MCP／OpenAI／Claude／Gemini／Dify 等外部宿主的逐項實作責任見 `references/host-adapter-contract.md`；封裝與完整性驗證規格見 `references/bundle-contract.md`。
