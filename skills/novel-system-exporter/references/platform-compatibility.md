# Novel OS 平台相容性與依賴矩陣

本文件必須和 ZIP 一起交付。Novel OS 是一組**技能說明＋本地模板／Python 驗證器**，不是獨立模型、聊天平台、向量資料庫或雲端服務。它能否「自動佈置」取決於目標 AI 框架是否允許：讀取多檔技能、寫入檔案、執行命令，以及（選用）呼叫模型／網路。

```text
- 1 個總入口＋16 個協作技能，合計 17 個 runtime Skill（原始碼另含匯出器）
- 模型能力相容專用：`novel-model-capability-compatibility`，負責實際 endpoint probe、L0–L5、adapter、fallback 與切換後回歸
- 現實狀態專用：`novel-reality-state-engine`，提供事件→狀態→能力→行為→正文驗證鏈
- 世界資料庫專用：`novel-world-database-builder`
- 特殊物資料庫專用：`special-object-database-builder`，正本路徑為 `SPECIAL_OBJECT_DATABASE_ROOT`
- 斷更補完專用：unfinished-novel-completion
```

## 1. 核心元件與它們依賴什麼

| 元件／功能 | 使用的系統／格式 | 最低依賴 | 選用依賴 | 沒有時的降級方式 |
|---|---|---|---|---|
| 技能調度 | `SKILL.md` YAML frontmatter + Markdown；`novel-operating-system` | 可載入多個文字檔的 AI／Agent | 能依 description 自動觸發的 Skills runtime | 將總入口作為 system prompt／project instruction，人工附上其餘 skills |
| 專案持久化 | Markdown、JSON、普通資料夾 | 可讀寫 UTF-8 檔案 | Git | 在對話／Canvas／雲端文件維護同名檔；明說無跨回合保證 |
| 長篇初始化與本地 gate | Python CLI，標準函式庫 | **Python 3.10+**、shell、可寫磁碟 | Git | 手工複製模板與檢查清單；不可聲稱已跑 gate／快照 |
| 關係圖正本 | Graphify 相容 node-link JSON | Python 3.10+（初始化、JSON validate） | `networkx`：path／affected；`graphifyy` + `networkx`：HTML、社群、Cypher export | 保存／閱讀 graph.json；人工查詢關係，不宣稱產生視覺化或最短路徑 |
| 世界資料庫 | Graphify 相容 JSON、世界／地點／派系／資源／規則／事件／主張節點、來源證據與增量批次 | Python 3.10+、持久 UTF-8 檔案 | `networkx`／`graphifyy`：path、affected、HTML、GraphML、Cypher | 保存 graph.json 與 Markdown 帳本；人工執行版本／認知檢查，不宣稱完成視覺化匯出 |
| 特殊物資料庫 | Graphify 相容 JSON、物件／版本／變體／模組／能力／規格／能源／限制／持有／操作／生命週期節點與來源證據 | Python 3.10+、持久 UTF-8 檔案 | `networkx`／`graphifyy`：path、affected、HTML、GraphML、Cypher | 保存 graph.json 與物件帳本；人工執行版本／規格衝突檢查，不宣稱完成視覺化匯出 |
| 互動小說 | JSON-compatible state、Markdown turn log | 檔案讀寫；Python 3.10+ 可驗證／checkpoint | 長期記憶／資料庫 | 每回合回顧貼在聊天中的 state；不可保證重開對話後留存 |
| 補完來源研究與驗證 | 未完成作品 | `unfinished-novel-completion`；研究／附件工具可選 | `source_ingest.py` 登記 hash、版本、完整度、權利狀態；`completion_gate.py` 檢查意圖過度宣稱與發布邊界 |
| 獨立模型審稿 | 宿主的模型呼叫 CLI／API | 無，非必要 | 可呼叫第二模型或子 agent | 改為人工／同模型 checklist；不可稱「獨立模型已審」 |

### 來源研究與未完成作品工具

`unfinished-novel-completion` 的基礎工具只使用 Python 標準庫：`init_completion_project.py`、`source_ingest.py`、`compare_source_versions.py`、`branch_diff.py`、`feasibility_report.py`、`sync_graph.py`、`completion_gate.py`、`provenance_report.py` 與 `run_regression.py`。網路、OCR、PDF、瀏覽器與第二模型均為選用；沒有它們時，仍可處理使用者提供的檔案，但必須標示來源範圍與未知，不得假裝查證。



### 最低「完整自動化」環境

- **Python 3.10 以上**：目前核心腳本使用 `X | None` 型別聯集語法；建議 Python 3.11+。
- **POSIX shell 或等價 process runner**：執行 Python CLI。
- **可寫入的持久檔案系統**：安裝技能與保存小說專案；至少需要一個可寫入 skills 目錄和 projects 目錄。
- **UTF-8 檔案支援**：故事、模板、JSON 及繁中內容均採 UTF-8。
- **ZIP 解壓能力**：僅在以 ZIP 分發時需要；可改由 Git／資料夾上傳。
- **本機標準庫**：核心 initializer、帳本、gate、state 與 bundle scripts 只依 Python 標準庫；不需 `pip install` 才能跑基本 smoke test。

這些功能不需要 API key、不需要資料庫、不需要 Node.js，也不需要網路。

### 選用依賴（功能增強，而非基礎工作流）

```bash
# 圖譜路徑、級聯查詢、GraphML
python -m pip install networkx

# Graphify HTML／社群／Cypher 匯出；上游套件名稱是 graphifyy
python -m pip install graphifyy networkx

# Git 版本快照與受 gate 保護的 commit
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` 可只用 Python 標準函式庫；`path`／部分 cycle 檢查需要 `networkx`。
- `relationship_graph.py export` 需要 **`networkx` + `graphifyy`**。沒有這兩項時保留 `graph.json`，不要假稱 HTML／GraphML／Cypher 已輸出。
- `independent_review.py` 目前是 **Minis 專用 adapter**，會呼叫 `minis-model-use`。在別的框架必須替換成該框架的第二模型／sub-agent／API adapter，或停用此選用審稿步驟。
- `novel_git.py` 是選用版本控制 layer。沒有 Git 時仍可用 `snapshot_project.py` 產生檔案快照。

## 3.2 主機綁定點與必做替換

封包本身的核心資料格式可攜，但以下是**主機／框架綁定點**，整合者必須處理：

| 綁定點 | Minis 目前用法 | 其他 AI 框架要做什麼 |
|---|---|---|
| 預設小說根目錄 | `<NOVEL_PROJECTS_ROOT>` | 設 `NOVEL_PROJECTS_ROOT` 或每次 initializer 傳 `--root <persistent-projects-root>`；勿假設 `<MINIS_ROOT>` 存在 |
| 角色資料庫根目錄 | `<CHARACTER_DATABASE_ROOT>` | 對接 `<CHARACTER_DATABASE_ROOT>`；批次暫存對接 `<CHARACTER_DATABASE_WORK_ROOT>`，兩者都須可由同一 project／agent 存取 |
| 特殊物資料庫根目錄 | `<SPECIAL_OBJECT_DATABASE_ROOT>` | 對接 `<SPECIAL_OBJECT_DATABASE_ROOT>`；批次暫存對接 `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>`，兩者都須可由同一 project／agent 存取 |
| 互動小說狀態根目錄 | `<INTERACTIVE_PROJECTS_ROOT>` | 對接 `<INTERACTIVE_PROJECTS_ROOT>`，確保 state／checkpoints／logs 可跨 run 回讀 |
| 獨立審稿 | `minis-model-use run` | 重寫 `independent_review.py` 的 command adapter，或建立同等 sub-agent function；保留 JSON schema、error artifact 和不自動升正典規則 |
| Skill 發現 | Minis skill registry + 相鄰目錄 | 註冊 **17 個** descriptions（總入口＋十六個專業技能）或建立 intent router；允許 agent 按需讀取同層 resource files |
| 長期狀態 | Minis shared directory | 對接 durable volume、資料庫、artifact store 或 framework checkpointer，依 project ID 回讀 |
| 研究工具 | Minis browser／shell | 對接 framework browser/search/file tools；沒有就限制為使用者提供資料 |

- `init_novel_project.py` 已支援 `NOVEL_PROJECTS_ROOT`；明確 `--root` 的優先級更高。角色／世界／特殊物資料庫與互動小說的 `<..._ROOT>` placeholder 必須由框架 router／部署設定替換。凡是原文件中的 `<MINIS_ROOT>/...`，在非 Minis 環境均視為**範例預設路徑**，不是硬性系統需求。

## 4. AI 框架能力分級

### A｜原生 Skills + shell + 檔案系統（完整模式）

適合具有 Skill runtime、agent tools、sandbox／terminal 的框架。可直接安裝整包，執行：

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**框架必須做的事：**

1. 將 `<SKILLS_DIR>/novel-operating-system/SKILL.md` 註冊為主要可觸發 skill。
2. 保留 **17 個**技能資料夾（總入口＋十六個協作技能）的同層關係，不可只上傳入口檔。
3. 允許 agent 讀取相鄰 skill 的 `SKILL.md`、templates、references、scripts。
4. 提供安全的命令工具或 process runner 執行 `python3`。
5. 重新索引／重啟 skill registry 後，用 smoke test 結果驗收。

**建議額外做：**網路研究工具、第二模型 adapter、Git、`networkx`、`graphifyy`。

### B｜自訂 Agent／工具呼叫框架（需 adapter）

適合有 system prompt、function calling、檔案工具，但不認識 `SKILL.md` 的框架。

**框架整合者要做：**

1. 把 `novel-operating-system/SKILL.md` 放進 agent 的 system/developer instructions；保留 YAML description 作路由規則。
2. 把其餘**十五個** skill 作為可檢索 reference 文件，或為它們建立 router：依使用者意圖載入對應 `SKILL.md`。
3. 映射工具：
   - shell → Python scripts；
   - read/write/list files → 專案檔與 state；
   - web search/browser → 公開資料研究；
   - second-model/sub-agent → `independent_review.py` 的替代 adapter。
4. 把 Minis 專用 `minis-model-use` 呼叫替換為自己的模型客戶端。必須保留原有 JSON 審稿 schema、失敗 artifact 和「machine_suggestion 不自動升正典」原則。
5. 指定 durable storage key／工作區，將同一作品的檔案在不同對話／worker 間帶回。
6. 實作或明確關閉 skill 自動觸發；不能只把**11 份 Skill 文件**塞進 context 卻聲稱會自動協作。

### C｜只支援上傳知識檔／自訂指令的聊天 AI（文件模式）

可移植寫作規約、模板、資料 schema 與檢查清單，但不具備真正自動化。

**要做：**上傳完整 `skills/` 子樹；把總入口設成 project instruction；每回合在 prompt 附上或讓 AI 查閱作品的 current state、story bible、時間線、角色檔、reader ledger 和上一章摘要。

**不能承諾：**自動建資料夾、CLI gate、hash 驗證、Git、Graphify 匯出、跨聊天記憶、背景任務、第二模型審稿。

### D｜只有單一 system prompt 的模型（手動降級）

把總入口精簡後貼入 system prompt，再把各專業技能與專案模板當知識庫。使用者／整合者須手動保存每回合產生的狀態文件；這保有思考框架，不等同完整 Novel OS。

## 5. 常見框架整合清單

| 類型 | 應放在哪裡 | 必做設定 | 特別注意 |
|---|---|---|---|
| OpenAI Assistants／Responses 類 | system instructions + vector/file search + code interpreter／自建 sandbox | 建立 router、持久 file store、Python execution adapter | 不要假設檔案跨 run 自動同步；需自行回存專案檔 |
| Claude Projects／MCP 類 | Project instructions + knowledge files；MCP filesystem／shell server | 把 skills 作資源，MCP 提供讀寫／runner／web | 沒有 MCP 時屬 C 級，不能跑 scripts |
| Gemini Gems／Vertex Agent 類 | system instruction + File Search／Code Execution／Cloud Storage | 對接 durable storage、function router、Python runner | 僅 Gem 指令通常沒有跨對話檔案工作流 |
| LangChain／LangGraph／CrewAI／AutoGen 類 | router node + file tools + subprocess tool + durable checkpointer | 依意圖載入 skills、保留 project ID、建立 review agent adapter | 需自行實作 skill discovery 與狀態 checkpoint，不是解壓即自動生效 |
| Open WebUI／AnythingLLM／Dify／Flowise 類 | Knowledge base + agent workflow／tool nodes | 上傳 skill files、接 shell/Python tool、掛載 persistent volume | 純 RAG 聊天模式屬 C 級；需 workflow 才能達 A/B |
| 世界資料庫宿主 | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | 掛載持久 world graph、批次工作區，提供 snapshot／validate／affected／export | 沒有 process runner 時只保存 JSON／Markdown，不能宣稱 Graphify CLI 已跑 |
| 特殊物資料庫宿主 | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | 掛載持久特殊物 graph、批次工作區，提供 snapshot／validate／affected／export | 沒有 process runner 時只保存 JSON／Markdown，不能宣稱特殊物驗證或匯出已跑 |
| Cursor／Claude Code／Codex CLI 等 coding agent | skills/commands directory + workspace | 安裝 **17 個**資料夾、設定 Python 和 workspace root | 對話式 model review adapter 需依其 CLI 改寫 |

這些名稱只說明整合類型；各產品版本、方案與權限不同，部署前須確認其最新文件。

## 6. 部署驗收清單

整合完成後，由宿主或整合者逐項確認：

- [ ] 能讀到 `novel-operating-system` 與十五個相鄰專業技能。
- [ ] 寫入測試檔後，新 agent run／新對話仍能讀回。
- [ ] `python3 --version` ≥ 3.10；若要跑圖譜 exporter，`networkx`／`graphifyy` 可 import。
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` 通過；或已明確記錄無法執行的項目。
- [ ] 新建一個測試小說專案，確認 story bible、state、timeline、reader ledger 與 graph.json 都建立。
- [ ] 讓 agent 寫一小段、更新狀態、開新 run 後續寫，確認連續性不是只靠上下文殘留。
- [ ] 若啟用研究，確認它能記錄 URL／來源／信心，而不是把搜尋摘要當正典。
- [ ] 若啟用第二模型審稿，確認 adapter 失敗時只產生 unavailable artifact，不阻斷或偽造結果。

## 7. 平台限制與責任邊界

- 目標模型的內容政策、工具權限、token 上限、資料保留與網路規則，均獨立於 Novel OS，不能由此 Skill 覆寫。
- 「自動佈置」指在**有安裝／檔案／shell 權限的 agent 框架**內自動安裝、建立骨架與載入路由；不是把 ZIP 丟給任意聊天模型就能永久安裝。
- 外部模型、瀏覽器與 Git 全為可選增強。缺少時要明確採用何種降級，不得以完成語氣掩蓋能力缺口。
