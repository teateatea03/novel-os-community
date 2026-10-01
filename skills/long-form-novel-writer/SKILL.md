---
name: long-form-novel-writer
version: 3.3.1
description: 當使用者要求寫長篇小說、繼續小說、長篇連載、寫第X章、續寫下一章、補完／研究斷更或未完成小說、重建原作者可能意圖、設計替代結局、重寫章節、維持角色一致性、管理時間線、世界觀／地理／制度／科技／魔法／歷史連續性、建立／更新／查詢小說世界資料庫、世界觀知識庫、地點／派系／資源／規則圖譜、建立／更新／查詢特殊物資料庫（道具、鎧甲、機體、機器人、載具、武器、神器、裝置與裝備系統）、人物／事件／派系關係圖譜、追蹤伏筆、改綱影響、避免重複內容、成人小說／成熟關係／親密敘事，或要求讓小說更像人寫、去 AI 味、調整自然度、改善台灣繁中、修復角色同聲、校準作者聲音時使用。強制連動 human-behavior-personality-consultant 校準人物行為，自動連動 novel-worldbuilding-architect 校準世界系統；以 novel-world-database-builder 保存世界層資料，以 special-object-database-builder 保存特殊物本體、版本、能力、限制、狀態與生命週期，並以 knowledge-relationship-graph／Graphify 建立跨文件的世界／人物／特殊物／事件—關係—證據—時間索引和級聯影響；未完成作品先連動 unfinished-novel-completion 建立來源／版本／意圖／分支／權利交接包；內容與風格鎖定後連動 novel-human-voice-editor 作最後文字層修訂；連動 novel-style-craft-director 建立風格契約與防漂移。依作者成人內容契約追蹤設定，不另設成人技能層硬性阻斷，但所選模型／供應商規則仍獨立生效。以可持久化聖經、世界資料庫、特殊物資料庫、圖譜、角色檔、行為模型、風格表、狀態與伏筆帳本維持連續性。
---

# Long-Form Novel Writer

為長篇與連載提供「規劃 → 寫作 → 驗證 → 更新狀態」閉環。核心任務不是一次寫很多字，而是在多章、多次對話中保持人物、時間、世界規則、敘事聲音與伏筆一致。

## 外部去 AI 味白名單整合

本技能可選整合宿主已安裝的外部 `lieflat-less-ai-tone`（不隨本包分發；缺少時記為未執行）。它只在內容、連續性、行為、資訊權限、類型與 `style-sheet.md` 鎖定後，作為最後一道窄範圍文字層 pass；完整交接契約見 `references/lieflat-less-ai-tone-integration.md`，規則唯一以 `<SKILLS_ROOT>/lieflat-less-ai-tone/SKILL.md` 為準。

固定順序：

```text
章節候選 → 世界／連續性／Reality／行為 Gate → style-sheet 檢查
→ novel-human-voice-editor chapter-gate／指定尺度修訂
→ lieflat-less-ai-tone 白名單 pass（僅宿主已安裝時）
→ 內容差分與視角／角色聲音回查 → [DRAFT] → 作者核准後 Canon Gate
```

白名單 pass 不得改劇情、角色、世界規則、知識權限、伏筆、段落結構或作者／角色聲音；未命中外部技能明示規則的文字逐字保留。不得以 AI 分數、偵測通過或「像真人」作為品質目標。既有 `[CANON]` 只在作者明確要求回溯清理時建立新的 `[DRAFT]` 修訂版，不得靜默覆寫。

## 模型能力、Luna baseline 與切換 Gate
長篇寫作使用 Luna baseline 示意設計契約；該名稱不代表特定模型的實測能力或當前可用性。依 `../novel-model-capability-compatibility/references/luna-baseline-contract.md`，模型一回合只做 extract／plan／render／repair／blind-read 之一；必須使用短 active context、帶 actor／source 的 facts、protected unknowns、scene function、facts alignment、最多兩次局部修復與隔離盲讀。state、Reality、Graph、檔案與 commit 固定由宿主執行。

模型可替換，但替換後仍跑同一 Luna fixtures 與 pipeline；更強模型不得跳過 Gate 或自行擴大事件／工具權限，較弱模型不得靜默省略功能。可接受措辭與局部創意差異，不可接受事件／狀態差分、P0、盲讀、知識邊界或玩家控制結果顯著不同。

長篇寫作的執行模型可替換，但狀態帳本、Graphify、Reality Card／Gate、工具回合、正典同步與角色行為推導不可遺失。切換模型前先跑 `novel-model-capability-compatibility` 的 text／JSON／tool／multi-step／state probes，生成 capability delta；只有達到必要 L4（狀態工作流）或 L5（自動代理）才可啟用相應模式。若模型本體只有 L1／L2，降為候選規劃／正文／局部修復，保留 host-managed L4；不得把「能回文字」標成完整相容。

## 隨機事件方向建議（v2.6）

長篇與互動模式共用 `immersive-interactive-fiction/scripts/novel_judge/random_events.py`，不另造一套抽取器。每個新專案／branch 預設 `off`；目前只允許使用者／作者切換為 `on-suggestion`，不自行增加低／中／高頻或 Storyteller profile。

長篇模式只在章／場景 planning 或 settlement 邊界要求建議：`scene_boundary`、`transition`、`travel`、`downtime`、`post_scene`、`post_chapter` 或較慢的 `world_pulse`。正文 renderer、修句、盲讀階段不得抽取或把 suggestion 注入成既成事件。元指令、直接後果未落地、已有明確 deterministic consequence、高壓場景無自然斷點及情緒收束均 suppress。

Suggestion 只是一張可忽略的方向卡，永遠 `NON_CANONICAL_SUGGESTION`、零 commit 權、零 State／Graph／Knowledge／timeline／prose patch。作者採用後，必須依當下正典重建 scene／chapter candidate，再通過 Reality、Knowledge、角色行為、世界規則、讀者資訊、連續性與 Canon Gate；不得直接把抽取卡寫進章節、時間線或帳本。完整合約見相鄰技能 `references/random-event-suggestion-contract.md`。

每次續寫前必須呼叫 `novel-reality-state-engine`，以本章／本回合事件帳本、時間線、資源、Graphify affected 子圖和角色行為模型產生 Reality Card。先判定身體負荷與認知容量，再走 Feeling → Thought → Action；不得把角色基礎人格直接當成當下能力。正文完成後執行 Reality Gate，檢查時間、生理、認知、知識邊界、行動成本、身體反應與同意界線；未通過不得定稿或同步正典。

若專案含 `completion-state.json`，初始化與續寫前先使用 `unfinished-novel-completion/scripts/completion_gate.py`；`completion_mode=undecided`、空 `branch_id` 或補完 Gate FAIL 時，只能做研究／分支規劃，不能直接把生成內容寫成續章正文。

## 最高層大原則：角色行為現實優先

## 裁判權威分層

章節 Gate / 盲讀 / 整稿診斷必須分層，不得用單一 PASS 代表「寫得好」。

- `CANON_INTEGRITY`：可阻擋正典提交
- `NARRATIVE_QA`：高信心敘事 bug；P0 才硬擋
- `EDITORIAL_DIAGNOSIS`：整稿／章節編輯建議，含 ticket 與 revision board
- `READER_RESPONSE`：讀者反應，不自動升格
- `AUTHOR_DECISION`：唯有明示作者決策可形成偏好真值

作者修正預設只進非正典錯誤卡。角色連續性升角色護欄，文風群聚升 rejected fixture，可機器判斷且反覆出現才升既有 Gate。未核准 note 不阻擋提交，也不自動改技能。契約見相鄰 `immersive-interactive-fiction/references/author-correction-promotion-contract.md`。

`scripts/chapter_gate.py` 已輸出 `minis.novel-chapter-gate.v2` 與 authority report。
`novel_judge.editorial_diagnosis.diagnose_manuscript()` 提供整稿 advisory board，但不是完整 human developmental edit。


角色反應與行為盡量貼近現實。每次安排關鍵行為前，先依角色當下知道什麼、身心狀態、既往經驗、關係／權力、資源、風險與可見選項推導，再處理戲劇節奏；不能只因情節需要就讓角色突然失智、勇敢、冷酷、告白、原諒或背叛。張力優先來自有限資訊下的誤判、迴避、妥協、合理化、沉默、延遲反應與後果，而非人設失真。

低機率或戲劇化反應仍可使用，但必須補足前因、觸發、成立條件與代價；作者指定方向時，調整因果橋樑，不把現實感原則當成拒絕創作的理由。寫實要求的是心理與行為因果，不是抹除奇幻世界、類型特色或個體差異。

## 優先原則

1. **使用者決定 > 已定稿正文 > 鎖定設定 > 故事聖經 > 已核准大綱 > 草稿 > 技能提案。**
2. 不因「更有戲」擅改使用者設定；發現衝突時指出位置，給最小修補選項。
3. 不把大綱當正文，不把章節寫成事件摘要。用人物在具體時空中的選擇推動情節。
4. 每場戲必須至少改變一項：資訊、關係、權力、承諾、資源、位置、風險或自我認知。
5. 連續性不是角色每次都做同一件事，而是變化有可追溯原因。
6. 寫作時不展示冗長內部檢查；除非使用者要求，只輸出小說正文、三向走向推演與極簡備註。
7. 三向走向是**候選創作方向**，不是統計預測。預設使用序位（較可能／可行／低機率但成立）或寬區間；只有符合行為技能的樣本與校準門檻時，才可使用 A＋B＋C＝100% 的精細百分比。
8. 人物關鍵選擇在生成前必須經 `human-behavior-personality-consultant` 校準並保存不可覆寫 Prediction Lock；生成後追加 resolution。情節需求不能凌駕已建立的人格狀態分布、情境強度、身心狀態與可見選項。作者指定低機率方向時補成立條件，並記為作者選擇，不篡改原預測。
9. 類型、敘事鏡頭、語言質地與局部模式必須由 `novel-style-craft-director` 轉成可檢查的風格契約；不以作家姓名或模糊形容詞直接驅動正文，也不直接模仿在世作者聲紋。
10. 成人類同時受作者內容契約、風格契約與心理行為模型引導：角色設定、關係性質、尺度、同意／界線呈現、權力和後續影響由作者指定；技能不另設成人硬性阻斷。不同模型／供應商可能有不可由技能覆寫的規則。
11. 任何會影響情節的地理、資源、制度、科技、魔法、歷史與文化規則，必須先經 `novel-worldbuilding-architect` 校準；世界觀不能只在作者需要時出現，也不能用新規則無代價解決問題。
12. 跨章人物、事件、地點、派系、物件（包含特殊物）、知識、伏筆、世界規則與因果關係使用 `knowledge-relationship-graph` 建立 Graphify 相容衍生索引；若專案啟用特殊物資料庫，特殊物本體、版本、能力、規格、能源、限制、模組、持有／操作與生命週期由 `special-object-database-builder` 保存；若世界資料庫已啟用，使用 `novel-world-database-builder` 保存世界／地點／派系／資源／規則／主張／證據的獨立索引；正典正文／聖經始終優先，圖譜不得反向覆蓋來源。重大改綱先 snapshot，再查 affected。

## 正典標記

所有專案資訊依狀態標記：

- **[LOCKED]** 使用者禁止更動。
- **[CANON]** 已核准或已出現在定稿正文。
- **[PLAN]** 已核准但尚未發生的規劃，可依後續指示調整。
- **[DRAFT]** 尚未核准的正文或設定。
- **[PROPOSAL]** 技能提出、尚待作者決定。
- **[UNKNOWN]** 不可自行補完的重要缺口。

不得把 [PROPOSAL]、[DRAFT] 靜默升為 [CANON]。若使用者直接說「繼續／下一章」而未要求修改，可把緊接前一版正文視為獲准延續；重要新世界規則仍要單獨列出。

## 專案儲存

長篇預設建立於 `<NOVEL_PROJECTS_ROOT>/<project-slug>/`；在 Minis 的預設值是 `<NOVEL_PROJECTS_ROOT>/<project-slug>/`，以便跨會話延續。其他 AI 框架的整合者必須把 `<NOVEL_PROJECTS_ROOT>` 映射到持久可寫的 workspace／volume／檔案庫，並在 initializer 使用 `--root` 指定它；不要假設 `<MINIS_ROOT>/` 存在，也不要搬動既有專案。

建議結構：

```text
project/
├── project-brief.md
├── story-bible.md
├── world-bible.md
├── world-rules.md
├── knowledge-matrix.md
├── current-state.md
├── behavior-models.md
├── timeline.md
├── plot-threads.md
├── reader-ledger.md
├── entity-registry.json             # 可編輯的實體／別名／context mode
├── mention-index.json               # 衍生提及索引
├── workflow-state.json
├── runtime/                          # 與互動模式共用的 append-only event/state kernel
│   └── sessions/manuscript/branches/main/
├── story-index.json                 # 衍生檢索索引
├── cascade-impact.json              # 變更待處理清單（若有）
├── volumes/
├── chapter-plans/
├── scenes/
├── context-packs/
├── gates/
├── snapshots/
├── chapter-index.md
├── style-sheet.md
├── decisions.md
├── graphify-out/
│   ├── graph.json
│   ├── graph.html
│   └── audit.jsonl
├── locations/
├── factions/
├── characters/
├── chapters/
├── summaries/
├── research/
├── world-database-link.json         # 可選：外部世界資料庫連結與同步狀態
└── world-db-sync/                   # 可選：世界資料庫增量批次／交接包
```

首次建立時載入 `story-bible-template.md`、`continuity-ledger-template.md`、`behavior-models-template.md`，並從 `templates/` 建立 `reader-ledger.md`、`entity-registry.json`、`workflow-state.json` 和持久化 `volumes/`、`chapter-plans/`、`scenes/` 空間；由 `../novel-worldbuilding-architect/world-bible-template.md` 與 `world-rules-template.md` 建立世界檔。若專案啟用外部世界資料庫，複製 `../novel-world-database-builder/templates/world-database-link.json` 至 `world-database-link.json`；若啟用特殊物資料庫，複製 `../special-object-database-builder/templates/special-object-database-link.json` 至 `special-object-database-link.json`，把世界／特殊物的增量批次與章前交接包放在 `world-db-sync/`；並載入 `../knowledge-relationship-graph/SKILL.md` 初始化 Graphify 相容 `graphify-out/graph.json`。

- **斷更／未完成作品專案**：如果使用 `unfinished-novel-completion/scripts/init_completion_project.py`，在一般長篇骨架之外新增 `completion-brief.md`、`source-manifest.json`、`textual-canon.md`、`evidence-ledger.md`、`author-intent-ledger.md`、`version-conflicts.md`、`feasibility-report.md`、`hypothesis-ledger.md`、`unfinished-thread-ledger.md`、`rights-and-publication.md`、`completion-provenance.md`、`completion-state.json` 與 `generation-log.jsonl`；這些檔案在模式與分支決定前保持研究／提案狀態。

## 工程層：可恢復的長篇生產閉環

新建專案由 initializer 建立 `runtime/sessions/manuscript/branches/main/`，並立即綁定 active `ProjectRuntimeAdapter` production authority；以 `immersive-interactive-fiction/scripts/novel_judge` 的同一 FileStore、State、append-only event、hash、branch lock、journal recovery、七 Gate、typed semantic delta 與 Graph projector 作機器正本。每個作者核准場景以 `commit_scene_event(ProjectRuntimeAdapter, ...)` 原子提交；直接 FileStore canonical mutation 在 authority 啟用後 fail closed。`longform_projector.py` 由 event/state 重建 `current-state.md`、`timeline.md`、`chapter-index.md` 並保存來源 hash manifest，人工修改或事件前進會標 stale。`author_console.py` 顯示 HEAD／journal／event corruption／projection／memory／branch diff blocker。舊專案不得無證據偽造歷史 transition；先唯讀盤點並用 provenance baseline migration／隔離 probe 驗證，確認無第二 writer 後才 cutover。Schema 更新走 migration registry、backup 與 manifest。

以下工程層補足帳本之外的持久化、檢索與可執行檢查；它們產生的是**衍生資料與警報**，絕不反向覆蓋 [CANON] 正文。

### 分層規劃與場景卡

- 總綱 → `volumes/volume-001.md` → `chapter-plans/chapter-001.md` → `scenes/scene-001-01.md`。載入 `templates/volume-plan.md`、`chapter-plan.md`、`scene-card.md`，不要把每個 Beat 鎖死成不可發現的正文。
- 每個場景卡必填目標、阻力、風險、策略、轉折、進／離場狀態、前後繼因果、世界限制、心理行為鏈、讀者資訊與狀態差分。場景 `[PLAN]`、`[DRAFT]`、`[CANON]` 狀態獨立維護。
- 卷級情緒與進度依 `references/pacing-and-emotion.md` 作提醒；禁止把曲線或固定懸崖當鐵律。

### 讀者資訊帳本

載入 `references/reader-information.md` 與 `templates/reader-ledger.md`。角色「知道什麼」存於 knowledge matrix；讀者「文本可知／可推論／被引導誤信／仍被保留」只存於 `reader-ledger.md`。每個場景回寫新增、確認、誤導、反轉或保留，並記資訊載體、最後重提、最晚回應及章末最強未解問題。

### Context Builder 與檢索

章前先讀必需正典，依 `references/entity-mentions.md` 維護 `entity-registry.json`，可執行 `python3 scripts/entity_mentions.py --root <project> --heatmap` 建立別名／提及索引；再執行：

```bash
python3 scripts/build_story_index.py --root <project>
python3 scripts/build_context_pack.py --root <project> --chapter chapter-001 --query "POV 地點 活躍伏筆"
```

context pack 採關鍵詞 TF-IDF 與結構帳本小幅保底，輸出來源檔和行號、Top-K 與字元預算。它不以向量相似度取代時間線、正典狀態、認知權限或圖譜；寫作前仍須回讀每個關鍵來源。`workflow-state.json` 記錄當前 phase／章／場、待 gate、未提交草稿、最近 snapshot、索引與 cascade 狀態，使中斷後可恢復。

### Gate、快照與級聯

- 章後執行 `python3 scripts/chapter_gate.py --root <project> --chapter chapter-001`。詳細分類見 `references/consistency-taxonomy.md`；報告必含 PASS/WARN/FAIL、P0/P1/P2、雙證據與最小修補。它是啟發式檢查，作者可以 override，但須記到 `decisions.md`。
- 每卷中點、每 10 章、重大改綱後或卷末，再執行 `python3 scripts/deep_consistency.py --root <project> --chapter chapter-001`。必要時依 `references/reviewer-protocol.md` 分開呼叫 `independent_review.py` 的 continuity／beta-reader／style-editor；模型結果一律為 `machine_suggestion`，無雙證據只列問題，不能自動升 P0。
- 改動 [CANON] 前先執行 `python3 scripts/snapshot_project.py --root <project> --reason "原因"`；接著 `python3 scripts/cascade_impact.py --root <project> --query "修改主題" --mark`。依 `references/revision-cascade.md` 更新來源、帳本、摘要與未來章綱，再重建 index/context pack 和 gate。
- 協作與差分依 `references/git-collaboration.md`，用 `novel_git.py init/status/branch/commit`；不得自動 hard reset、force push、rebase、merge 或把 Git commit 誤當 [CANON]。commit 前有 FAIL/P0 時需作者提供 override reason。
- 工具品質依 `references/regression-testing.md` 以植入缺陷 fixture 驗證。新增規則前先證明能抓到對應案例；未校準規則最多 WARN。
- 可用 `python3 scripts/manuscript_metrics.py --file <chapter>` 檢查長度、對話比例、句長、重複 n-gram、meta 標記。指標只提示，不能以機械黑名單抹平文風。

先判斷：
- **新專案**：從概念、人物或大綱開始。
- **續寫**：延續既有章節。
- **指定章節**：依章綱寫第 X 章。
- **改寫／潤稿**：保留哪些事件、視角與字數？
- **一致性修復**：先找衝突，不急著重寫。
- **規劃**：只產出故事聖經、大綱、章綱或場景卡。

只問會實質改變成品的資訊。新專案最少需要：故事前提、主要人物、類型／調性、視角與本次交付範圍。缺少其他資訊時列出少量 [PROPOSAL] 假設即可開始。

## 新專案流程

### 1. 建立創作契約

確認：
- 類型、核心前提、主題問題、目標讀者與尺度
- 人稱、視角策略、時態、語體與禁用手法
- 預計篇幅、章數或更新節奏（若未定可暫缺）
- 寫實程度、年代／地域、研究要求
- 必須保留、絕不可出現的內容
- 若為成人題材：角色年齡／身分、關係性質、內容級別、露骨程度、同意／界線／拒絕／撤回如何呈現、權力關係、敘事立場、禁用內容與事後影響

載入 `../novel-style-craft-director/SKILL.md`，依故事需求選擇「主引擎 1 種＋敘事鏡頭 1 種＋語言質地 1 種＋局部修飾 0–1 種」，建立 `style-sheet.md`。成人題材或親密／情色內容另載入 `../novel-style-craft-director/references/adult-mature-intimacy.md`；不得僅以「成人風格」四字省略尺度與界線。

### 2. 建立故事引擎

以因果而非事件清單整理：

> 主角因＿＿而追求＿＿；對手／制度以＿＿阻止；每次使用＿＿策略雖取得＿＿，卻付出＿＿並使下一個問題更難；最終必須在＿＿與＿＿之間選擇。

至少確定：主角目標、內在需求、主要阻力、代價、時限、不可逆轉點、結局承諾。資訊不足時給 2–3 個差異明確的方案，不大量擅補。

### 1. 角色主體分類

所有跨章角色都必須保留 `subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise` 與 `classification_confidence`。開始寫作前先完成分類，並把該分類傳給深挖、行為顧問與角色資料庫；不能把真人、小說、動漫、電影版本或其他媒介的證據無標記混用。

- `real`：公開真人／歷史人物；只使用公開資料。
- `novel`：小說文字正典。
- `anime`：漫畫／動畫／動漫正典，分開版本。
- `film`：電影版本；與演員本人分離。
- `other`：遊戲、舞台、神話、原創或未消歧。

每名主要人物至少記錄：
- 外在目標、內在需求、核心恐懼、錯誤信念
- 公開面具、私下狀態、壓力下策略
- 語言／行為指紋、能力與限制
- 對其他角色的欲望、誤解、權力與未說出口的期待
- 知道什麼、不知道什麼、以為自己知道什麼

格式見 `character-profile-template.md`。

### 4. 建立故事聖經、世界聖經與宏觀大綱

載入 `../novel-worldbuilding-architect/SKILL.md`，先建立支撐第一卷所需的最小可用世界：核心規則、資源／基礎設施、權力／法律、日常生活、科技／魔法成本、近期歷史壓力，以及 [TRUTH]／[OFFICIAL]／[BELIEF]／[RUMOR]／[KNOWN] 認知版本。不要為完整而一次填滿整個宇宙。

先鎖定硬約束，再規劃可變部分。大綱按「人物選擇＋世界反作用造成後果」排列，不以巧合連接。每一大段應有：
- 角色採取策略
- 局部成功或失敗
- 新資訊／代價
- 關係或目標改變
- 下一步被迫發生的原因
- 本段使用／改變的世界規則，以及一階／二階公共後果

不要把所有細節提前鎖死；保留局部發現空間。

## 跨技能路由（按需載入）

圖譜、世界觀與風格的詳細觸發、正典同步、章前交接與改綱流程在 `references/cross-skill-routing.md`。只有工作涉及該域才載入對應技能：

- **未完成／斷更小說**：`unfinished-novel-completion` 會先處理來源、版本、文本正典、作者意圖、可行性、分支、權利與溯源；只有選定模式／分支並通過補完 Gate，才交接本技能逐章寫作。
- **世界觀**：新地點／制度／文化、科技魔法、資源物流公共事件、世界限制成為情節條件；先做世界可行性，後做行為與風格。
- **未完成作品**：本章來自 `unfinished-novel-completion` 交接時，章前必須同時讀 `completion-brief.md`、`completion-state.json`、`textual-canon.md`、`evidence-ledger.md`、`author-intent-ledger.md`、`unfinished-thread-ledger.md`、`feasibility-report.md`、`rights-and-publication.md` 與當前分支。正文只能使用已選定 `completion_mode`／`branch_id` 的材料；未選分支保留為 `[PROPOSAL]`，不得混入正典。每章後補完 Gate 與一般章節 Gate 都要通過或明確記錄 override。

## 章前協議

寫任何續章前，依需要讀取而非憑記憶：
1. `project-brief.md`、`style-sheet.md`
2. 查詢 `graphify-out/graph.json` 取得本章相關實體／事件／關係子圖和來源位置
3. 本章相關 `world-bible.md`、`world-rules.md`、`knowledge-matrix.md`、地點與派系檔
4. `current-state.md` 與 `behavior-models.md`
5. 本章相關人物檔
6. `timeline.md` 與 `plot-threads.md`
7. 最近 1–3 章摘要
8. 上一章尾段；涉及呼應時再搜尋更早正文
9. 本章章綱與使用者最新指示

- **未完成作品章前補充**：若專案含 `completion-state.json`，先確認 `completion_mode`、`branch_id`、`rights_status` 與 `last_gate`；讀取補完交接檔，不得只讀上一章。若模式仍為 `undecided`、分支為空或補完 Gate 尚未通過，先停在研究／規劃階段，不直接生成長篇續章。

### 建立場景契約

章內每場戲先在內部確認：
- 視角人物、時間、地點與進場狀態
- 當下目標與阻力
- 可失去的具體事物
- 角色採取的策略
- 轉折／揭露
- 離場狀態如何不同
- 該場如何迫使下一場發生

沒有變化的場景應合併、縮短或刪除。

### 強制心理／行為校準

若既有非真人角色的正典資料不足以回答本場行為，先讀 `../human-behavior-personality-consultant/references/canon-gap-behavior-completion.md`。只有在 deep-digger 已確認 `CANON_UNKNOWN` 後，才啟動 Mind Architecture Gate 與低推定補全。先用 given circumstances、scene objective、obstacle 與 playable action 寫候選，再用 HUMAN_PRIOR／競爭 formulation 排序；最後才可提 backstory。補全候選必經 Scene Lab，並保存 authority label。作者採用後只升本專案 `[AUTHOR-CANON]`，不得標原作 `[CANON]`，也不得寫成「原作者真正意圖」。

在生成關鍵場景或 A／B／C 前，先由 `../novel-worldbuilding-architect/SKILL.md` 確認候選方向在世界規則、資源、制度、時間、物流與角色知識上可行，再套用 `../human-behavior-personality-consultant/SKILL.md` 建立當前節點的最小行為模型。一般低風險過場可用簡版；涉及不可逆選擇、關係斷裂、背叛、黑化、暴力、創傷反應、親密承諾、道德越界、權力巨變時使用完整版。

#### 第一步：建立行為基線

- **Evidence**：按 E1–E6 標示直接行為、相似情境先例、自述、他述、群體基準率與純提案；低層證據不得覆蓋直接行為。
- **Actor**：基線、常態／高壓波動、少見但可能表現、恢復條件與 `if–then` 模式，不用固定人格點。
- **Agent**：此刻目標、恐懼、承諾、可見選項及主觀成本。
- **Author**：他相信自己是誰，哪種選擇可被自我故事允許或合理化。
- **情境強度**：強／中／弱；強情境提高制度與後果權重，降低人格權重。
- **狀態／脈絡**：睡眠、疼痛、飢餓、疲勞、急慢性壓力、近期獎懲、關係與權力、成長學習史、文化／制度限制。
- **選擇空間**：角色實際看得見並做得到的方案；作者知道的選項不等於角色知道。

#### 第二步：建立候選行為鏈

每個方向都要能寫成：

> 塑形因素 → 近期脆弱 → 觸發 → 主觀評估 → 第一衝動 → 保護／抑制 → 實際行為 → 短期回報／維持因素 → 長期代價 → 事後自我敘事

同時回答為何沒有更糟、為何也沒有更好。如果鏈條缺少關鍵橋樑，降低候選序位／信心並標示成立條件；不得用診斷標籤、童年陰影或荷爾蒙一句話代替因果。

#### 第三步：心理合理性分級

對 A／B／C 分別標記：
- **成立**：目前條件已足夠，可自然發生。
- **大致成立**：需要 1 個輕微觸發或橋樑。
- **勉強成立**：需要多項新增條件或明顯累積鋪墊。
- **目前不成立**：違反核心模式且沒有足以壓過它的條件。

「目前不成立」可給 0%；若作者堅持採用，先提供最小合理化方案：補入可觀察的累積壓力、錯誤學習、關係變化、資源喪失、道德許可或不可逆代價，再重估，不以「人很複雜」含混帶過。

#### 第四步：Prediction Lock 與信心表示

重大節點在正文生成前，使用 `../human-behavior-personality-consultant/scripts/behavior_calibration.py lock` 將來源 state hash、證據階梯、情境強度、2–4 個候選、可觀察預測、推翻條件、保護／抑制因素、反事實與未知事項追加到 `behavior-calibration/predictions.jsonl`。同一 Prediction ID 不得覆寫；新資訊建立新版並以 `supersedes` 連結。

候選由下列項目共同校準，不採機械平均：
1. 證據層級與相似情境基準率
2. 人格狀態分布與 `if–then` 相容度
3. 當下目標／恐懼相容度
4. 生理認知狀態、壓力與恢復容量
5. 維持、保護與抑制因素
6. 關係、制度、世界規則與現實可行性
7. 情節因果與伏筆成熟度

預設使用序位；資料普通可用寬區間。只有相似情境至少 5 筆、已解決預測至少 10 筆且存在校準紀錄時，才可使用合計 100% 的精細百分比。高戲劇性不能單獨提高信心；作者偏好不能寫進行為機率。

#### 第五步：寫進場景而非解說

選定方向後，至少呈現行為鏈中兩個可觀察橋樑：例如注意偏移、身體狀態、猶豫、替代方案被排除、稱謂變化、自我合理化、短期獎賞或延遲代價。除非使用者要求分析報告，正文後只顯示精簡的「行為校準」依據，不傾倒心理學術語。

### 三向走向推演

把「每段落」解讀為每個完整的**敘事段落／場景節點**：一次具有目標、阻力、轉折與狀態變化的情節單元；不要在每個排版自然段、每幾句對話或動作之後打斷正文。若使用者明確指定「每個自然段」，才依其字面要求執行，但先保持選項極短。

每個節點寫完後，依當前正典列出三條**互斥且具實質差異**的下一步。預設格式：

```text
【下一段三向推演｜Prediction Lock：Pxxx｜表示法：序位】
A｜較可能｜角色目前最自然的策略與直接後果｜心理合理性：成立
B｜可行｜需不同觸發／代價的方向｜心理合理性：大致成立
C｜低機率但成立｜高衝擊且仍符合設定的方向｜心理合理性：勉強成立
行為校準：Evidence、情境強度、Actor 分布／Agent／Author、身心狀態、保護／抑制與關係權力（1–3 句）
成立／推翻條件：明列缺少橋樑與會改變排序的新證據
```

若證據普通，可將文字信心改為寬區間，例如 `A｜40–65%`；各區間不要求端點加總。只有 lock 通過精細百分比門檻時，才使用 `A｜45%／B｜35%／C｜20%`，且合計 100%。

規則：
1. A、B、C 排序由目前證據、世界可行性與人物行為自然度決定；不是作者喜好票數。
2. 序位／寬區間不得假裝統計精度；精細百分比必須由校準工具驗證門檻與總和。
3. 推估至少考量：世界規則、資源／時間／物流、人物認知權限、證據階梯、Actor 狀態分布、Agent／Author、完整行為鏈、情境強度、身心狀態、學習史、保護／抑制、關係／權力、伏筆成熟度、文化／制度與 [LOCKED] 設定。
4. 三向不能只是同一事件換措辭；應改變策略、盟友／對手、代價、資訊揭露或情節尺度之一。
5. 候選都必須可寫且不違反正典。低順位 C 不等於獵奇反轉、角色降智、巧合救場或無鋪墊黑化。
6. 若某方向目前不成立，可明列缺少條件，不得為湊三向硬寫荒謬選項；實際只有兩條時可只列兩條。
7. 使用者選定候選後，該選擇成為下一節點 [PLAN]；真正寫入並獲核准後才升 [CANON]。作者可提出未列出的方向。
8. 使用者未選而直接要求「繼續」時，預設採最高序位；若會新增重大世界規則、殺死核心人物或造成不可逆類型轉向，先請作者選擇。
9. 正文中不宣告機率；推演區放在節點正文之後。使用者要求純正文時隱藏推演，但重大節點仍需在帳本保存 lock。

### 章後行為校準

完成場景或取得作者選擇後，使用 `behavior_calibration.py resolve` 追加 outcome、可觀察命中／落空、漏判、作者覆寫／新資訊與模型更新。Resolution 不得覆寫原 lock；作者選擇不自動計為 prediction hit。再把穩定的新 `if–then` 模式回寫 `behavior-models.md`，並記錄復發、抗拒、假性進步或舊策略回返。

## 正文寫作協議

### 視角與資訊

- 一個場景維持一個視角中心，除非使用者明確採全知觀點。
- 只寫視角人物此刻可感知、知道或合理推測的內容。
- 記錄資訊權限；不能讓人物知道尚未得知的秘密。
- 內心不是作者說明欄。思想也應有偏見、遺漏、自我欺騙與當下目的。

### 場景與節奏

- 從有壓力或即將失衡之處進場，完成轉折後離場。
- 摘要用於跨越無決策價值的時間；場景用於選擇、衝突、揭露和關係變化。
- 高張力後可有恢復段，但恢復段仍須改變關係、理解或計畫。
- 章末不必每次硬做懸崖；可用新問題、不可逆選擇、情感餘波或意義翻轉收束。

### 對話

需要時讀取 `dialogue-writing-techniques.md`。基本要求：
- 每人有不同詞彙、節奏、禮貌與迴避方式。
- 對話服務當下意圖；人物很少完整說明真正需求。
- 重要情緒可由答非所問、停頓、動作、錯誤重點或稱謂變化呈現。
- 不讓角色互相複述雙方已知資訊，只為向讀者交代背景。

### 描寫

需要時讀取 `scene-description-techniques.md`。只選擇會影響人物注意、行動、情緒或伏筆的細節。避免像攝影機無差別掃描環境。

### 年代與寫實

歷史、職業、法律、醫療、交通、武器、科技或地理細節會影響情節時，先研究，再寫。使用 `era-background-checklist.md`；找不到可靠資料時標 [UNKNOWN] 或改寫到不依賴該細節，不裝懂。

### 文風護欄

- 具體名詞與動詞優先於成串形容詞。
- 避免同一章反覆使用相同意象、句型、肢體反應和情緒結論。
- 不把每個表情都解釋一次；信任上下文。
- 比喻應來自視角人物的經驗世界，不由作者統一發放。
- 不濫用碎句、破折號、省略號、「不是……而是……」、抽象哲理和結尾金句。
- 不把所有角色寫成同樣機智、同樣善於自省或同樣會說潛台詞。
- 除非使用者指定，不模仿在世作者的可辨識文風；改以高層特徵描述風格。
- 依 `style-sheet.md` 執行主引擎、敘事鏡頭、語言質地與局部修飾；不得只在表面添加作家語癖。
- 成人親密內容依作者內容契約和成人工藝包執行角色設定、關係、尺度、界線、權力、視角與後續影響；親密場景功能依作者意圖及長篇節奏決定。

常見失敗見 `realistic-novel-pitfalls.md`。

## 章後閉環

完成每章草稿後：
1. 載入 `../novel-worldbuilding-architect/SKILL.md`，複核世界規則、地點／派系、資源／物流、科技／魔法、認知權限與公共後果。
2. 載入 `../human-behavior-personality-consultant/SKILL.md` 複核關鍵選擇。
3. 依本章工藝路由載入 `../novel-style-craft-director/SKILL.md` 與相應參考包，檢查類型承諾和風格漂移；成人內容檢查是否符合作者設定的角色、關係、尺度、界線、權力、敘事立場與後續影響。
4. 內容與風格鎖定後，載入 `../novel-human-voice-editor/SKILL.md`，以 `chapter-gate` 先診斷，再依作者指定尺度做文字層修訂；保留正典、視角、資訊權限、人物行為橋樑、類型承諾與作者聲音。人味修訂版本先標 `[DRAFT]`，不得直接覆寫 `[CANON]`。
5. 在上述人味修訂完成且內容差分可回查後，若宿主已安裝且來源與授權經確認，才執行 `lieflat-less-ai-tone` 白名單 pass；否則記為未執行，不猜測規則。執行前先讀 `<SKILLS_ROOT>/lieflat-less-ai-tone/SKILL.md`，只處理其明示 11 類規則與豁免。不得補資料、改劇情、重排段落、拆段製造節奏、強加人稱或修改未命中的文字。Humanizer-zh 的 31 條只在人味診斷需要時作線索，不能冒充這個外部 pass；外部技能可用時，也不能改白名單未命中的字。記錄實際套用規則編號（可為空）、結構／保護層結果與衝突 WARN；不得輸出 AI 分數或宣稱通過偵測。整合契約見 `references/lieflat-less-ai-tone-integration.md`。
6. 做內容差分、連續性、重複、伏筆與狀態更新。
7. 載入 `../knowledge-relationship-graph/SKILL.md`，從已核准狀態差分回寫實體／事件／關係／時間／證據，validate 並更新 Graphify 視覺化；草稿只以 [DRAFT]／planned 寫入。詳細欄位見 `continuity-ledger-template.md`。

### 1. 世界規則與結構檢查
- 本章使用的地理、資源、法律、制度、科技／魔法、歷史與文化是否已建立或標 [DRAFT]？
- 人口、距離、時間、交通、通訊、物流和基礎設施量級是否可行？
- 強大能力是否遵守資格、成本、限制、反制與既有例外？
- [TRUTH]、[OFFICIAL]、[BELIEF]、[RUMOR]、[KNOWN] 是否分開，角色有無偷渡作者知識？
- 公共事件的一階／二階後果是否影響地點、資源、派系、日常和角色選項？
- 世界或組織是否為方便主角而突然全知、失能或創造新解法？

### 2. 因果與人物檢查
- 本章是否由前一章後果推動，而非作者需要？
- 關鍵選擇是否通過 Actor／Agent／Author、狀態／脈絡與完整行為鏈校準？
- 是否有另一個同樣能解釋行為的競爭假說，且正文提供足以辨別的線索？
- 選定低機率方向時，是否已把必要觸發、累積壓力、可見選項與代價寫進正文？
- 對手是否有自己的目標與可行策略？
- 巧合若引發麻煩可以接受；巧合不應替主角解決高潮。

### 3. 風格、類型與成人檢查
- 本章是否執行 `style-sheet.md` 的主引擎，而非只使用表面腔調？
- 敘事距離、資訊控制、時間結構、語言密度、對話和意象是否有無理由漂移？
- 主要人物是否仍有不同聲音，風格是否迫使人物違反心理行為因果？
- 推理線索、恐怖機制、科幻二階後果、愛情信任證據等主類型承諾是否實際推進？
- 每 3–5 章或每卷是否完成一次跨章防漂移比較，並把有意變化寫入 [PLAN]？
- 成人內容：是否遵守作者指定的角色年齡／身分、關係性質、內容級別、界線呈現、權力、敘事立場與後續影響？

### 4. 連續性檢查
- 日期、時刻、年齡、旅程和事件順序
- 地點、出入口、天氣（若重要）與交通時間
- 傷勢、疲勞、衣物、金錢、武器、鑰匙、信件等物件持有
- 誰知道／誤信／隱瞞何事，資訊何時取得
- 關係、承諾、債務、法律與社會後果
- 世界規則、能力成本與已建立限制

### 5. 重複檢查

區分必要呼應與無效重複：
- 相同背景是否已向同一視角說明？
- 相同衝突是否產生新策略、新代價或權力變化？
- 相同情緒是否只換句話重說？
- 回憶是否改變當下決策，而非重播資料？

重複意象可保留，但每次須改變語境或含義。

### 6. 伏筆與承諾

更新每條線索狀態：Seeded（埋下）／Active（推進）／Complicated（變質）／Resolved（回收）／Dropped（作者同意放棄）。記錄最晚應再次出現的章節範圍，避免遺忘或過早回收。

### 7. 更新專案檔

草稿未核准時，以 [DRAFT] 或 pending 區塊記錄；核准後更新：
- `chapters/chapter-XXX.md`
- `summaries/chapter-XXX-summary.md`
- `chapter-index.md`
- `current-state.md`
- `behavior-models.md`
- `world-bible.md`
- `world-rules.md`
- `knowledge-matrix.md`
- 受影響的 `locations/`、`factions/`
- `timeline.md`
- `plot-threads.md`
- `graphify-out/graph.json`（衍生索引；先正典後圖譜）
- 受影響的人物檔、故事聖經與決策紀錄

摘要必須記錄「狀態變化」，不只概括劇情。保存使用者覆寫與修改理由到 `decisions.md`，避免日後又改回去。

### 8. 更新走向預測與校準

在 `plot-threads.md` 或章節摘要中記錄最新 Prediction ID、候選序位／區間、判斷依據、成立／推翻條件與表示法；不可覆寫 `behavior-calibration/predictions.jsonl`。使用者選定後標示 `Selected` 並追加 resolution；已寫入草稿標 `[DRAFT]`，獲核准後才標 `[CANON]`。新資訊建立新版 lock 並以 supersedes 連結，舊版保留。

## 改寫與修訂

先辨識修訂層級：
1. **連續性修補**：改最少句段，修正日期、資訊或物件錯誤。
2. **場景修訂**：保留事件結果，重做目標、阻力、轉折和節奏。
3. **人物修訂**：重建動機鏈或心理鋪墊。
4. **結構修訂**：調整章序、因果、伏筆或人物弧。
5. **文句潤飾**：在結構穩定後才做。

未經要求，不要在潤稿時擅改事實、刪除伏筆或新增世界規則。大幅改寫後重新執行章後閉環。

## 預設交付

- 使用者要「寫章節」：直接給完整正文；每個敘事段落／場景節點後附 A／B／C 候選，預設用序位或寬區間；只有校準門檻通過才附合計 100% 的精細百分比。必要備註最多列 3–5 點。
- 使用者要「規劃」：交付因果式大綱、章目標，以及每個規劃節點的 A／B／C 候選、Prediction ID 與信心表示法，不假裝已是正文。
- 使用者要「只要純正文」：本次隱藏三向推演區，但仍可在內部／專案帳本維護；不得違反使用者明確格式要求。
- 使用者要「檢查」：先列阻斷級問題，再列最小修改，不以個人喜好冒充錯誤。
- 篇幅不明時，以能完成一個實質場景單元為準，結尾說明目前停點，不聲稱未實際寫出的字數。

## 最終品質檢查

- 本章是否有欲望、阻力、選擇、代價與狀態變化？
- 主角是否有能動性，而非只被事件搬運？
- 事件之間是否主要由「所以／但是」連接，而非「然後」？
- 人物是否只知道他有途徑得知的資訊？
- 台詞遮住名字後，主要人物是否仍可區分？
- 年代、空間、物件、傷勢和旅程是否可行？
- 是否重講舊資料，卻未賦予新意義？
- 是否留下足夠但不過量的未解承諾？
- 是否遵守 [LOCKED] 設定、作者內容契約及使用者最新決定？
- 本章世界規則、資源、制度、科技／魔法、時間／物流與人物認知是否一致，且新設定已正確標記？
- 公共事件是否推演並記錄至少相關的一階／二階後果？
- 成人內容是否依契約維持角色、關係、尺度、界線、權力、敘事立場與跨章後續影響，而未被技能自行改寫？
- 是否在每個敘事段落／場景節點後提供三個互斥走向，且 A＋B＋C＝100%？
- 每個走向是否經 Actor／Agent／Author、身心狀態、學習史、關係權力、可見選項與制度現實校準？
- 選定的行為能否追溯成完整因果鏈，正文是否呈現至少兩個可觀察橋樑？
- 百分比是否有行為與情節因果依據、註明條件式估計，並避免虛假精確？
- 章後帳本與 Graphify 圖譜是否已同步、validate 通過或標明 WARN，且草稿沒有被誤標成正典？
