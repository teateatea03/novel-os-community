# Novel OS Host Adapter Contract

語言：[English](host-adapter-contract.en.md) | **繁體中文**

**原文一致性註記：**下方 Skill router 列仍寫「十五個專業技能」，但第 C 節及現行套件清單為 1 個總入口＋16 個專業技能（合計 17 個）。雙語版本保留原文措辭並明示差異，待原契約審查時統一，不以翻譯逕改契約。

這份契約給「不是 Minis」的 AI 框架整合者。Novel OS 不是把 ZIP 上傳後就能自行取得檔案權限、模型權限或跨對話記憶的插件；宿主必須提供下列能力，才能稱為自動化部署。

## A. 宿主應提供的最小介面

| 能力 | 最小操作 | Novel OS 用途 | 缺少時 |
|---|---|---|---|
| Skill router | `load_skill(name)`／讀取資源檔 | 由總入口按意圖載入十五個專業技能 | 改為手動把對應 Skill 放入 prompt |

| 持久儲存 | `read(path)`、`write(path)`、`list(path)`、`mkdir(path)` | 專案聖經、章節、帳本、state、圖譜與快照 | 僅文件模式，不能承諾跨 run 連續性 |
| Process runner | `run(argv, cwd)` | 執行 Python initializer、gate、state、graph 工具 | 手工使用模板與 checklist，不可聲稱驗證已跑 |
| Project identity | 穩定的 `project_id` → storage root | 讓同一本小說在新對話／worker 回讀同一份狀態 | 使用者每次手動提供檔案／摘要 |
| Branch writer lock | `lock(project,session,branch)`／交易鎖 | 串行化 recovery、stale-hash、event、state、manifest commit | 僅允許 single-writer；不得宣稱多 worker 安全 |
| Model task adapter | 接收 `minis.model-task.v1`，先持久 schedule，worker 以 lease claim，回傳固定 schema | 讓 L1/L2 模型只做單一 extract／plan／render／repair 任務，支援 retry／cancel／stale／restart recovery | 文件模式或人工填表；模型無 state 權限 |
| Runtime／event versioning | runtime build、event schema、transition contract、golden replay fixture | 升級後重播舊歷史仍得到相同 state hash；未知 contract fail closed | 凍結舊 runtime，只能人工遷移後升級 |
| Story solver | bounded storylet state exploration | 找 unreachable、broken target、soft lock 並揭露探索上限 | 人工路徑審查，不可宣稱全路徑驗證 |
| Random-event suggestion control | branch-scoped `off`／`on-suggestion`、semantic window、seeded pool、non-canonical audit | 只在合格窗口提供可忽略方向卡，保留 no-event 與可重現 provenance | 固定 `off`；不得用 prompt 偷抽或把建議當正典 |
| Memory／Graph projector | event → episodic memory；events → Graphify projection | 記憶可追溯、圖譜可重建 | 保存 events；標記衍生索引未更新 |
| Graphify 補完索引 | `sync_graph.py` 將來源、主張、分支同步到既有 `graph.json` | 來源、證據、版本與補完假說可查詢 | 圖譜是衍生索引，不得反向覆蓋正文／正典 |
Process runner 應優先採 **argv 陣列而非拼接 shell 字串**，限制在專案／技能工作區，並保留 stdout、stderr、exit code 作為 gate artifact。

## B. 路徑映射

部署設定應提供以下值；不要把 Minis 路徑硬編進別的環境：

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` 可讀 `NOVEL_PROJECTS_ROOT`，也可明確傳入 `--root`。
- `SPECIAL_OBJECT_DATABASE_ROOT` 保存特殊物資料庫正本 `graphify-out/graph.json`；`SPECIAL_OBJECT_DATABASE_WORK_ROOT` 保存批次 JSON 與交接包，不能取代正本。
- `WORLD_DATABASE_ROOT` 保存世界資料庫正本 `graphify-out/graph.json`；`WORLD_DATABASE_WORK_ROOT` 保存世界批次 JSON 與交接包，不能取代正本。
- 其他 root 是 router／framework adapter 的設定值；將相關 Skill 中的 `<..._ROOT>` placeholder 替換為真實持久路徑。
- 同一本小說的所有檔案必須位於同一可回讀 project root；不可只把最後一章留在短暫聊天上下文。

## C. 必要部署流程

1. 解壓 bundle，先執行：

   ```bash
   # 先確認 Python、hash 與完整 smoke test 都可用：
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. 註冊 **17 個** Skill（總入口＋16 個專業 Skill），其中 `novel-reality-state-engine` 必須提供事件／狀態 JSON、Reality Card 與可執行 Reality Gate；`novel-model-capability-compatibility` 必須提供實際 endpoint 的 text／JSON／tool／state probes、能力等級與 fallback；`novel-sensory-sound-prose` 必須保留聲音／五感 prose contract；並保留同層相對路徑。
3. 設定 `project_id` 對應以上持久根目錄，並授權 agent 讀寫該 project 的檔案。
4. 對新專案執行 initializer，確認 Markdown／JSON／`graphify-out/graph.json` 都成功建立。
5. 關閉並重新開一個 agent run，要求它讀取狀態再續寫，以驗證不是依賴暫時上下文。
6. 以兩個 worker 對同一 source state hash 同時提交：必須恰好一個成功，另一個得到 stale-hash／conflict；再以 events replay 驗證 current state hash。
7. 建立兩筆 episodic memory，驗證 reflection 至少引用兩個存在的 evidence IDs；編譯 L1 render task，確認封包不含 hidden truth 且 `may_commit_state=false`。
8. 從 events 重建互動 Graphify projection，刪除後重建應得到相同 source hash。
9. 保存至少一份 golden-history fixture；用新 runtime 重播必須得到 expected state hash，未知 transition contract 必須被拒絕。
10. 建立一個 model activity，驗證 lease 過期後可 recovery、state 前進後舊結果標 stale、pending activity 會阻斷 author console。
11. 建立含 unreachable／broken target／soft lock 的 storylet fixture，確認 solver 都能檢出並明示 max depth／max states。
12. compact events 後刪除 index 並竄改 archive；重建 index 前必須由 manifest integrity gate 拒絕。
13. 驗證新 branch 預設 `off` 且不抽取／不寫 audit；由 user 開啟 `on-suggestion` 後，在 scene boundary 以固定 seed 取得相同 suggestion／no-event，確認 canonical event log、State、Graph、Knowledge 與 prose 均未改變。
14. 對 meta input、pending direct consequence、高壓無 natural break、已有 deterministic consequence 與未預告 threat 執行 request，全部必須 suppress；採用 suggestion 只能產生 planning handoff 並列出 Reality／Knowledge／Agency／Behavior／World／Canon Gates。
15. 驗證 active segment 的 manifest hash／bytes／count：刪除 event index 後竄改 active log 必須 fail closed；activity claim 回傳 fencing token，舊 token／缺 token／過期 lease 均不得 complete；所有檔案型 ID 拒絕 path traversal；同一 random-event `request_id` 重試不得重抽或新增第二筆 audit，audit hash chain 竄改後不得重播，過期 suggestion 不得建立 adoption handoff。

## D. 選用工具 adapter

### 網頁研究

若宿主提供 browser/search，router 要把搜尋結果、URL、出版者、日期和短引文寫入 research／圖譜證據欄位。沒有 browser 時，只能處理使用者提供材料，並使用 `【待定】`／`【提案】`，不能假裝查證。

### 第二模型／sub-agent 審稿

`long-form-novel-writer/scripts/independent_review.py` 目前呼叫 Minis 的 `minis-model-use`。非 Minis 框架要採下列其中一種做法：

1. 寫一個 framework adapter，接收 `role`、`prompt`、`max_tokens`，呼叫另一個模型／sub-agent，將原始文字與解析後 JSON 存到 `reviews/`；或
2. 停用獨立審稿，改跑本地 gate／人工 checklist，並在交付中標示「第二模型未執行」。

無論哪種，輸出保持：`machine_suggestion` 不可直接升為 `[CANON]`；沒有雙證據的問題只列入 `questions`；失敗要產出 `unavailable` artifact，不得靜默當作通過。

### 圖譜與版本控制

- `networkx`：開啟 path、affected、GraphML 等功能。
- `graphifyy` + `networkx`：開啟 Graphify HTML、社群與 Cypher export。
- Git：只用於 commit／branch；沒有 Git 時仍可使用檔案 snapshot。

這些都是增強，不是啟動小說寫作的前置條件。

## E. Router 最小邏輯

```text
if request 是特殊物資料庫建立／更新／查詢／比較／匯出:
    load special-object-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add character-db + behavior when operator/autonomous-machine/personality matters
    add long-form when linked to a novel project or chapter state
elif request 是世界資料庫建立／更新／查詢／匯出:
    load novel-world-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add long-form when linked to a novel project or chapter state
elif request 是跨章寫作／續寫／改綱:
    load long-form + behavior
    add world/style/graph only when the story state needs them
elif request 是角色研究:
    load character-deep-digger
    add behavior + character-db/graph when evidence or persistence is needed
elif request 是人味／台灣繁中／角色聲音修訂:
    load human-voice-editor after content/continuity/style checks
elif request 是斷更／未完成小說補完、原作者意圖或替代結局:
    load unfinished-novel-completion
    add long-form + evidence/source tools + world/behavior/style/graph as needed
elif request 是自由輸入互動小說:
    load immersive-interactive-fiction
    add world/behavior/style/graph by scene complexity
```

總入口應先處理這個 router；不要每回合盲目把所有 Skill 全塞進模型 context。

## F. 不能由 bundle 自動完成的事

- 在未授權的雲端帳號安裝 Skill、設定 API key、開啟工具權限或建立資料庫。
- 讓純聊天模型獲得 shell、檔案系統、永久記憶或多模型能力。
- 覆寫目標模型／平台的內容政策、token 上限、隱私規則或網路限制。

若任何條件缺失，採用 `platform-compatibility.md` 的 B／C／D 級降級模式，並在部署報告中逐條列出未啟用功能。
