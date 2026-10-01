---
name: character-database-builder
version: 1.10.0
description: 當使用者要求「建立角色資料庫」「把搜尋到的人物資料存起來」「建立人物知識庫」「更新角色資料」「查詢角色資料庫」或要把真人／小說／動漫／電影／其他媒介角色的公開資料、來源、事件、人物關係、時間線、公開圖比對與創作推論持久化時使用。第一步依 `minis.character-profile.v2` 判定 `real`、`novel`、`anime`、`film` 或 `other`，再以本地 Graphify 相容 property graph 儲存分類、版本、正典範圍、節點、證據、事件、關係、別名、信心與衝突；公開圖另存 visuals／hash，圖譜只留路徑與來源以便比對。適合真人、歷史人物、小說角色、動漫角色、電影角色、遊戲角色、原創角色與真人原型。與 `novel-character-deep-digger` 搭配：前者研究與分析，後者負責分類一致的可追溯資料庫建立、匯入、查詢與版本更新。
---

# Character Database Builder

## 目的

把搜尋或使用者提供的角色資訊建立成可搜尋、可更新、可追溯的本地資料庫。資料庫正本放在 `<CHARACTER_DATABASE_ROOT>/<slug>/graphify-out/graph.json`；Minis 預設為 `<CHARACTER_DATABASE_ROOT>/<slug>/graphify-out/graph.json`。其他 AI 框架必須把 `<CHARACTER_DATABASE_ROOT>` 映射至可持久寫入的 workspace／volume，並以實際路徑傳給圖譜工具；匯出 HTML、Mermaid、GraphML、Cypher 都是衍生檔，不得反向取代正本。

## 硬性原則

1. **來源優先**：每項重要公開事實附 `source_url`、來源名稱、位置或短引文；沒有來源不可標記為 EXTRACTED。
2. **分層儲存**：明示資料用 `EXTRACTED`；根據多個線索的分析用 `INFERRED`；來源互相矛盾、身份未核實或只有二手說法用 `AMBIGUOUS`。
3. **可追溯的個人資料、關係與未證實線索，不把推論冒充真人事實**：先讀 `../novel-character-deep-digger/references/real-person-research-protocol.md`。可保存 P2 個人背景與 P3 敏感公開主張，並保存查到的八卦、匿名爆料、搜尋摘要、失效頁、外流或 doxxing 的**線索存在**為 U 類 `claim`；每筆需有來源／最小識別、日期、級別、信心、時間範圍、`UNVERIFIED`／風險與不可作事實使用標籤。不得把 U 類升格或用作人格推論；不複製高度敏感內容或可識別細節。帳密、憑證、私人聯絡、精確住址、醫療紀錄與性私密素材屬 S 類，只存「發現但未擷取／未使用」的稽核標記。心理、私生活與關係的推論要標 `INFERRED`／`FICTIONAL_PROPOSAL`，與真人事實分開。
4. **保留衝突**：新資料與舊資料不一致時，先 snapshot，再新增新主張或事件；不要直接刪改舊事實。
5. **名稱本地化**：`label` 是不可改動的原始／正典名稱；只要節點名稱含有非中文文字，或名稱為中文與日文／韓文／英文混合，必須在 `properties.name_zh` 保存台灣繁體中文可搜尋名稱。翻譯優先序固定為：**(1) 有可靠來源的官方中文譯名，使用官方譯名；(2) 沒有官方中文譯名時，不自行意譯，改採依原文讀音建立的台灣繁體中文音譯**。必要時可在音譯後以括號保留原名或型號以便消歧。`name_zh` 是查詢輔助欄位，不取代 `label`、ID 或 `aliases`，也不代表來源已公布該中文譯名。另保存 `name_zh_language: "zh-Hant-TW"`、`name_zh_provenance` 與 `name_zh_source_label`；無法可靠判讀原文讀音時才填 `UNKNOWN` 並標記待人工核對，不得改用自行意譯。查詢、列表與消歧必須同時比對 `label`、`aliases`、`properties.name_zh`。
6. **多方事件建事件節點**：漫展、捐助、直播、爭議等建立 event 節點，再用 `participated_in`、`occurred_at`、`reported_by` 等關係連接。
7. **最低可引用卡、禁止名稱佔位**：建立、匯入或補件任何角色前，必讀 `references/minimum-citable-character-card.md`。角色、技能／能力、職稱、人格標籤不能只存名稱；每個會被引用的角色都要有身份／範圍、來源錨點、可觀察行為、至少一張詳盡能力或限制卡、脈絡關係與 `data_completeness`。未知應標 `UNKNOWN` 與待查原因，不得臆補。先補既有低密度節點，不以新增更多名稱節點取代補件。
8. **敏感資料最小化與關係完整性**：對故事或研究必要的公開背景／關係，不因它較私人就省略：依 P 級、來源、時間範圍、信心與用途保存為節點／具方向關係／claim；不以同框、互追或八卦補全。查到八卦／外流／doxxing 時要以 U 類受限 claim 保存查核線索與風險，不能當事實或重述細節；S 類只記已發現未擷取／未使用。
9. **保存角色模型成熟度，不把研究量冒充驗證**：接收 `novel-character-deep-digger` v1.6+ 交付時，主節點保存 `character_importance`、`work_stage`、`profile_depth`、`model_status`（`MODEL_DRAFT|SCENE_TESTED|REVISION_CALIBRATED`）、`validation_tests`、`counterexamples`、`competing_models` 與 `required_before_story_use`。未通過場景測試的豐富分析仍是 `MODEL_DRAFT`。
10. **來源家族去重**：證據／claim 保存 `source_family_id`、`original_source_url`、`intermediary_chain`、`independence_status` 與 `original_retrieved`；同一貼文、採訪、影片、新聞稿或匿名說法的轉載不得計為多個獨立來源。
11. **保存研究 evidence run，不信任手填完整度**：接收 deep-digger v1.8+ 新 R1／R2 時，保存 `run_id`、protocol/events/candidates/artifacts/claims/reviews/run-summary 的路徑與 SHA-256、研究深度、P0 closure、benchmark misses、must-route coverage、checkpoint、defer／blocked 與 `RESEARCH_COMPLETE|RESEARCH_INCOMPLETE|SCOPE_LIMITED`。Graph 節點／關係的每筆證據回指 `claim_id`、`artifact_id`、locator 與 source family；raw／derived lineage 不塞進敘事 properties。舊 manifest 標 `LEGACY_V1`，不得自動宣稱 v2 完成。
12. **非真人以角色實例與作品見證本入庫**：接收 deep-digger v1.9+ 時，保存 work／expression／manifestation／item（witness）、continuity 與 adaptation／translation／reboot 關係；claim 另存 `witness_ids`、`continuity_ids`、`canon_status`、`narrative_level`、`version_portability`。同名角色跨 continuity 不合併為同一人格正本。只有 official paratext／summary 的資料庫標 `summary_only`／`RESEARCH_INCOMPLETE_FOR_BEHAVIOR`；跨版本 stable claim 必須保留各版 claim 與 contradiction audit。

## 角色主體分類（必填）

正式建立或匯入角色前，先讀 `references/character-category-schema.md`，完成分類卡。主分類只能是：

- `real`：真實／真人，含歷史人物
- `novel`：小說／網路小說／輕小說角色
- `anime`：漫畫／動畫／動漫角色
- `film`：電影版本或電影原創角色
- `other`：遊戲、舞台、神話、原創、跨媒體或尚未消歧

每個角色主節點的 `properties` 必須至少保存：

```json
{
  "subject_category": "real|novel|anime|film|other",
  "subject_subcategory": "...",
  "subject_kind": "real_person|historical_person|fictional_character|original_character|unknown",
  "source_medium": ["..."],
  "canon_scope": "public_record|novel_canon|anime_canon|film_canon|cross_adaptation|user_created|unknown",
  "version_scope": "...",
  "franchise": "...",
  "classification_basis": "...",
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS",
  "character_importance": "lead|major_supporting|minor_functional",
  "work_stage": "discovery|draft_diagnostic|revision",
  "profile_depth": "L0|L1|L2",
  "model_status": "MODEL_DRAFT|SCENE_TESTED|REVISION_CALIBRATED",
  "validation_tests": [],
  "counterexamples": [],
  "competing_models": [],
  "required_before_story_use": false
}
```

分類欄位與 `confidence` 分工不同：分類描述對象屬於哪一種主體；`confidence` 描述該節點或主張的證據強度。分類不明時使用 `other`／`unknown`／`AMBIGUOUS`，不可硬猜。真人原型與改編後的虛構角色須分開建檔，使用 `derived_from` 或 `inspired_by` 連結。

### 版本對應規則

- 使用者明確指定某版本時，以指定媒介為主：例如「電影版」→ `film`；「漫畫原作」→ `anime`／`manga_character`。
- 未指定版本時，以主要正典來源為主；有改編的其他媒介列入 `source_medium`，不覆寫主分類。
- 漫畫、動畫、動畫原創、季別、重製、劇場版要在 `version_scope`／`canon_scope` 分開。
- 電影角色不能混入演員本人資料。
- 列表與查詢按 `subject_category` 分組，顯示次分類、系列／作品與版本範圍。


```text
<database>/
├── graphify-out/
│   ├── graph.json       # 正本（不含圖 bytes）
│   ├── graph.json.bak
│   ├── audit.jsonl
│   ├── snapshots/
│   ├── graph.html
│   ├── graph.mmd.md
│   ├── GRAPH_REPORT.md
│   ├── graph.graphml
│   └── cypher.txt
└── visuals/             # 公開比對圖；sidecar JSON + 圖檔。見 references/visual-comparison-store.md
```

## 節點類型

- `person`：人物及角色原型
- `organization`：學校、公司、平台、主辦方
- `place`：城市、場館、地區；不存私人地址
- `event`：漫展、公開宣布、公益、作品發布、爭議
- `document`：報導、訪談、官方公告、影片頁面
- `resource`：官方帳號、平台個人空間、作品頁、公開比對圖（`kind: public_visual`，檔在 `visuals/`）
- `claim`：有爭議或需單獨標記的公開說法
- `concept`：職業、內容風格、教育背景等可被關聯的概念

## 建立流程

### 1. 定義範圍、分類與非真人版本實例

先確認研究對象、資料截止日、用途、資料來源範圍與主體分類。建立分類卡：`subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`classification_basis`、`classification_confidence`。若分類不明，先以 `other`／`unknown`／`AMBIGUOUS` 保存，不猜測身份或媒介。

若非真人，先讀 `../novel-character-deep-digger/references/fictional-character-research-operations.md`；先建 work／expression／manifestation／item witness 與 continuity/adaptation edges，再建角色 instance。研究的是「某角色在某 continuity／witness 中的版本」，不是先假設整個 franchise 只有一個人。



### 2. 搜尋、擷取與研究譜系

先讀 `../novel-character-deep-digger/references/research-operations.md` 與 `research-evidence-run-v2.md`。新 R1／R2 只接受通過 `validate_research_run.py` 的 `minis.character-research-run.v2`；需保存 protocol hash、append-only event head、candidate dispositions、raw/derived artifact hashes、claim/review IDs 與 run-summary。只有來源清單或 v1 manifest 時標 `LEGACY_V1`／`RESEARCH_INCOMPLETE`；使用者限制外搜時標 `SCOPE_LIMITED`。執行：

```bash
python3 ../novel-character-deep-digger/scripts/validate_research_run.py <research-run-directory> --summary <research-run-directory>/run-summary.json
```

圖譜匯入只接收已 include 的 candidate 與已核查 claim；搜尋 hit、全文共現或 deferred lead 不得直接升格為人物／關係事實。

若來源由 `public-web-research` 擷取，PWR 的 candidate ledger 只算 acquisition staging，不算 deep-digger v2 已審查 candidate，更不算 claim。匯入前必須由 evidence run adapter／研究者完成以下轉換與核對：

- PWR canonical URL → v2 `canonical_locator`；PWR event／artifact ID → `discovered_by` 與 artifact provenance。
- `review_status=unreviewed`／`disposition=defer` 不可直接改成 include；必須保存 `screened_by`、`screened_at`、source role、reason code 與 identity/version 判定。
- raw SHA-256、derived input/output hash、capture method 與 locator 寫入 artifacts ledger；清理後 Markdown 不可取代 raw。
- 只有 claim audit 後的 `include && checked` claim 可進 Graphify；schema validator 或 dry-run 必須拒絕 crawler candidate、搜尋 snippet 與未核查 source-family hint。
- PWR `security_flags`／`escalation_required` 是安全與完整性訊號，不是人物事實；不得寫入人物性格或關係邊。

公開頭像／作品視覺若要入庫比對，讀 `references/visual-comparison-store.md`，用 `scripts/ingest_public_visual.py` 寫入 `visuals/`（hash 去重）；圖譜只存 `visual_refs`、`has_visual` 與來源 URL，不把圖 bytes 寫進 `graph.json`。不整批下載社群原圖；S 類圖不存。

優先順序：本人／官方帳號與原始影片或公告 → 可靠媒體專訪 → 多家媒體交叉報導 → 搜尋摘要與百科僅作線索。保存：

- URL、標題、發布日期、抓取日期
- 明示內容及短引文
- 涉及的人物、組織、地點、事件，以及「主體—關係—客體」的方向與時間範圍
- 來源是否一手、二手、轉載或 U 線索；真人資料的 P1／P2／P3／U／S 分級、查核狀態與風險
- 可確認、矛盾、未確認項與待查節點

### 3. 產生批次 JSON

**入庫前先完成最低可引用卡。**讀取 `references/minimum-citable-character-card.md`，為角色主節點保存 `data_completeness`、`required_before_story_use`、`open_research_gaps`；能力採 `capability_cards` 詳細卡或獨立能力節點＋關係。若只有名稱或無法取得細節，保留 `UNKNOWN`／待查，不可把常識或粉絲印象填成資料。先對既有低密度角色做補件，再考慮新增角色。

用 `knowledge-relationship-graph` 的 schema 產生 `extraction-batch.json`，先放在 `<CHARACTER_DATABASE_WORK_ROOT>/<slug>-character-db/`，不能直接手改正本。Minis 的預設 work root 是 `<WORKSPACE_ROOT>/`；其他框架將它映射至暫存但可由同一 agent run 存取的 workspace。重要欄位：

```json
{
  "nodes": [{
    "id": "person:example",
    "label": "公開名稱",
    "entity_type": "person",
    "aliases": ["別名"],
    "properties": {
      "subject_category": "real|novel|anime|film|other",
      "subject_subcategory": "...",
      "subject_kind": "real_person|historical_person|fictional_character|original_character|unknown",
      "source_medium": ["..."],
      "canon_scope": "public_record|novel_canon|anime_canon|film_canon|cross_adaptation|user_created|unknown",
      "version_scope": "...",
      "franchise": "...",
      "classification_basis": "...",
      "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS"
    },
    "status": "active",
    "confidence": "EXTRACTED",
    "confidence_score": 0.9,
    "source_file": "來源名稱",
    "source_url": "https://example.com",
    "evidence": [{"quote": "短引文"}]
  }],
  "links": [{
    "id": "edge:example",
    "source": "person:example",
    "target": "event:one",
    "relation": "participated_in",
    "relation_category": "event",
    "status": "active",
    "confidence": "EXTRACTED",
    "confidence_score": 0.8,
    "evidence": [{"source_url": "https://example.com", "quote": "..."}]
  }],
  "hyperedges": []
}
```

### 4. 初始化與匯入

使用技能內的腳本：

```bash
# 先由整合者設定可攜路徑；Minis 範例：
# GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py
# DB=<CHARACTER_DATABASE_ROOT>/<slug>
# BATCH=<WORKSPACE_ROOT>/<slug>-character-db/extraction-batch.json
GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py
DB=<CHARACTER_DATABASE_ROOT>/<slug>
BATCH=<CHARACTER_DATABASE_WORK_ROOT>/<slug>-character-db/extraction-batch.json
python3 "$GRAPH" init --root "$DB" --title "<名稱>角色資料庫"
python3 "$GRAPH" import --root "$DB" --file "$BATCH" --strict
python3 "$GRAPH" validate --root "$DB"
python3 "$GRAPH" export --root "$DB" --graphml --cypher
```

若資料庫已存在，不使用 `--force`。先執行 `snapshot`，再以增量批次匯入；若是明確要求重建才可 `init --force`。

### 5. 分類與資料密度驗證

除了圖譜的一般驗證，必須檢查：

- 每個角色主節點是否有合法 `subject_category`。
- 是否同時有 `subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope` 與 `classification_basis`。
- 每個會被引用角色是否通過 `references/minimum-citable-character-card.md` 的最低可引用卡；能力不能只有名稱，必須有可觀察效果、前提、限制／代價與證據或推論鏈。
- `data_completeness`、`required_before_story_use` 與 `open_research_gaps` 是否誠實反映缺口；UNKNOWN 不可被靜默略過。
- 對整體根目錄使用 `scripts/character_coverage_audit.py --root <CHARACTER_DATABASE_ROOT> --output <report.md>`；先處理 P0（身份／能力／來源缺失）再處理 P1（行為引擎缺失）。
- 每個重要關係是否以具體動詞、方向、時間、證據與信心保存；未知但結構必要的人／組織是否已作待查節點，而非被靜默遺漏。
- `real` 的 P2／P3 是否有必要性、來源、日期與範圍；U 類是否被正確保留為 `UNVERIFIED` claim 而沒有升格、複製敏感細節或拿去做診斷；S 類是否僅有發現／隔離稽核。
- `novel`／`anime`／`film` 是否有作品與正典／版本範圍。
- 真人原型與改編角色是否分開。
- `other`／`unknown` 是否有待查原因。

交付時按主分類分組，告知資料庫路徑、節點／關係數、分類、版本範圍、驗證結果、來源與不確定項，並提供正本及視覺化檔案連結。不要只給摘要而不保存檔案。


```bash
$GRAPH search --root "$DB" "關鍵詞"
$GRAPH neighbors --root "$DB" "person:<slug>"
$GRAPH timeline --root "$DB"
```

交付時告知：資料庫路徑、節點／關係數、驗證結果、來源與不確定項，並提供正本及視覺化檔案連結。不要只給摘要而不保存檔案。

## 更新流程

1. 搜尋新資料並建立來源文件節點或更新來源證據。
2. `snapshot --root <DB>`。
3. 只新增新節點／關係；舊資料若失效用 `close-edge`，保留歷史與 audit。
4. 若同一事實出現矛盾，建立 `claim` 或 `disputed` 關係，記錄雙方來源。
5. `validate`、`search`、`timeline`、`export`。
6. 需要回答「改動會影響哪些角色／事件」時，使用 `affected`；不要默默覆寫相關資料。

## 與角色深挖技能的分工

- `novel-character-deep-digger`：研究公開資料、建立人物檔案、提出可標記的性格推論與小說化方案。
- `character-database-builder`：把研究結果拆成節點／關係／事件／來源證據，持久化、查詢、版本化、驗證與匯出。
- `knowledge-relationship-graph`：提供底層 schema 與本地圖譜工具。
- 公開比對圖：`references/visual-comparison-store.md` 與 `scripts/ingest_public_visual.py`；`apple-vision similarity` 只作輔助，不作生物辨識。

完整的心理分析、行為因果與小說寫法不可直接塞進真人事實節點；可另存為 `analysis`／`fictional_proposal` 文件節點，並在 properties 中標示 `not_public_fact: true`。

## 快速回應範例

使用者：「把剛才搜尋的兔娘資訊建立資料庫。」

執行：建立 `person:tu-niang`、平台 resource、教育／地點、公開事件、來源 document 與證據；將姓名、教師任職說法、官方帳號等未完全核實項標為 `AMBIGUOUS`；驗證後交付正本與 graph.html。

使用者：「更新她最近的活動。」

執行：先 snapshot，搜尋日期與來源，新增 event／document；不覆蓋原時間線。

使用者：「查她和教育背景有什麼關聯？」

執行：對資料庫做 search／neighbors／path，回答每項結果的來源與信心，不把 inferred 關係說成 extracted。
