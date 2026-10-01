---
name: knowledge-relationship-graph
version: 1.3.0
description: 當使用者要求建立知識圖譜、關係圖、人物關係網、家族／派系／組織圖、事件因果圖、時間圖譜、專案依賴圖、特殊物／道具／鎧甲／機體／載具／武器的關係圖、誰與誰有什麼牽連、修改某事會影響什麼，或需要從文件／小說／研究資料中抽取實體與關係並視覺化、查詢、追蹤版本與證據時使用。以 Graphify-Labs/graphify 為底層基準，建立 Graphify 相容的本地 property graph，支援實體、事件、typed relations、hyperedges、來源證據、別名消歧、雙時間、信心、衝突、快照、最短路徑、鄰居、級聯影響、社群分析與 HTML／Mermaid／GraphML／Cypher 輸出。可作小說、特殊物、研究、專案與一般複雜關係的共用基礎設施。
---

# Knowledge Relationship Graph

把「散落資訊」轉成可查詢、可追溯、可更新且一目瞭然的關係網。底層採指定的 [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)；本技能增加時間、事件、證據和跨領域語意，不把 Graphify fork 進技能。

## 核心原則

1. **先定義用途**：要回答最短路徑、時間狀態、級聯影響、群體結構還是證據衝突？Schema 服務查詢，不為完整而建百科。
2. **關係必須有方向與動詞**：優先 `A --works_for--> B`，避免一律 `related_to`。
3. **多方事件建事件節點**：交易、會議、戰爭、章節事件等，不把所有參與者兩兩亂連。
4. **來源與推論分開**：EXTRACTED／INFERRED／AMBIGUOUS，每條關係可附來源、位置、短引文和信心。
5. **時間不覆寫**：保存 valid time 和 transaction time；舊事實標 superseded，不直接刪除。
6. **同名不等於同一人**：別名先消歧，再合併；自動合併需保守。
7. **屬性不能吞掉實體**：人物、組織、事件、政策等應成節點，才可搜尋與連線。
8. **正本機器可讀**：`graphify-out/graph.json` 是正本；HTML、Mermaid、GraphML、Cypher 是衍生輸出。
9. **修改先快照，後查 affected**：不靜默覆蓋會造成連鎖影響的資料。
10. **名稱本地化與查詢**：節點 `label` 保留原始／正典名稱；凡含非中文文字，或中文與日文／韓文／英文混合，建立 `properties.name_zh`（台灣繁體中文查詢名稱）。翻譯優先序固定為：有可靠來源的官方中文譯名就使用官方譯名；沒有官方中文譯名時，不自行意譯，改依原文可靠讀音採台灣繁體中文音譯，必要時括註原名或型號。並保存 `name_zh_language: "zh-Hant-TW"`、`name_zh_provenance`、`name_zh_source_label`。`name_zh` 只作查詢輔助，不取代 ID、`label` 或 `aliases`，也不自動代表官方譯名；只有在原文讀音也無法可靠判讀時才填 `UNKNOWN`／`[UNKNOWN]`。搜尋、列表、消歧與跨資料庫引用必須同時比對原名、別名與 `name_zh`。
11. **機密不入圖譜**：API key、密碼、token 不寫入 graph.json 或視覺化。

## 使用 Graphify

整合、版本、授權與來源見 `references/graphify-integration.md`。

- 若現有專案已有 `graphify-out/graph.json`，自然語言查詢優先使用：
  - `graphify query "問題"`
  - `graphify path "A" "B"`
  - `graphify explain "節點"`
  - `graphify affected "節點"`
- 本技能的時間／領域命令使用 `scripts/relationship_graph.py`。
- Graphify 可掃描 code/docs/papers/images/video；一般文字關係抽取可由當前模型產生批次 JSON，再由本地腳本 import、validate、export。

### 特殊物與物件生命週期

特殊物資料庫可將 `object`、`system`、`concept`、`resource`、`event`、`claim` 與角色／組織節點放入同一個 Graphify 子圖。常用關係包括 `model_of`、`variant_of`、`loadout_of`、`component_of`、`contains_system`、`equipped_with`、`provides_capability`、`requires`、`powered_by`、`consumes`、`limits`、`vulnerable_to`、`countered_by`、`designed_by`、`manufactured_by`、`owned_by`、`possessed_by`、`operated_by`、`located_in`、`deployed_in`、`damaged_in`、`repaired_in`、`upgraded_in`、`transferred_in`、`destroyed_in`、`appears_in`、`documented_in`、`supports`、`contradicts`、`revealed_in`、`affects` 與 `requires_update`。

物件版本、能力、規格、能源、限制與持有／操作狀態都要保留 valid time、transaction time、來源和證據；不同作品媒體／宇宙／季別不靜默合併。特殊物的 Graphify 正本由 `special-object-database-builder` 保存，本技能可建立跨專案引用與級聯索引，但不反向覆蓋特殊物正本或作品正典。



```text
project/
└── graphify-out/
    ├── graph.json          # 正本，Graphify node-link JSON
    ├── graph.json.bak      # 最近寫入前備份
    ├── audit.jsonl         # 操作紀錄
    ├── snapshots/
    ├── graph.html          # Graphify 互動視覺化
    ├── graph.mmd.md        # Mermaid
    ├── graph.graphml       # Gephi／yEd（選用）
    ├── cypher.txt          # Neo4j（選用）
    └── GRAPH_REPORT.md
```

## 特殊物資料庫的核心模型見 `../special-object-database-builder/SKILL.md`。當查詢物件能力、版本差異、依賴、持有／操作、損傷／維修或修改影響時，使用專用 schema 和 validator；`knowledge-relationship-graph` 只提供通用 Graphify 執行、跨物件／角色／世界子圖、時間與證據查詢，不把 object 節點當普通無狀態道具。

當圖譜承載角色資料庫時，`entity_type: person` 的角色主節點應在 `properties` 保存 `minis.character-profile.v2` 欄位：

- `character_record: true`
- 可選 `visual_refs`／`primary_visual_id`：公開比對圖指標（檔在角色庫 `visuals/`，不把圖 bytes 寫進 graph.json）
- `subject_category`: `real`／`novel`／`anime`／`film`／`other`
- `subject_subcategory`
- `subject_kind`
- `source_medium`
- `canon_scope`
- `version_scope`
- `franchise`
- `classification_basis`
- `classification_confidence`

`subject_category` 是資料主體分類，不取代 `EXTRACTED`／`INFERRED`／`AMBIGUOUS` 證據信心。真人原型與小說／動漫化身要分開節點，以 `derived_from`／`inspired_by` 連接；漫畫、動畫、動畫原創、重製與電影版本不可無聲合併。查詢角色資料時按主分類分組，再按次分類、作品與版本範圍篩選。完整欄位定義見 `references/data-model.md` 與角色資料庫技能的分類契約。


## 角色主體分類與版本閘門

角色、人物或角色資料庫進入圖譜前，先保存 `minis.character-profile.v2` 分類欄位：`subject_category`（`real`／`novel`／`anime`／`film`／`other`）、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`classification_basis`、`classification_confidence`。分類不是證據信心；兩者都要保存。真人原型、小說／動漫化身、不同電影或動畫版本分開節點，使用 `derived_from`／`inspired_by` 或版本關係連接。
- `valid_from`／`valid_to`
- `confidence`／`confidence_score`
- `evidence` 與來源位置

### 關係

- `source`、`target`、`relation`
- `relation_category`、`inverse_relation`、`polarity`
- `valid_from`／`valid_to`
- `transaction_from`／`transaction_to`
- `status`、`confidence`、`evidence`

### 事件

事件是節點；參與者用 `participated_in` 並在 properties 記 role，地點用 `occurred_at`，因果用 `causes`／`contributes_to`。

## 工作流程

### 1. 定義圖譜契約

確認：
- 範圍與用途
- 核心 entity types
- 核心 relation vocabulary
- 時間粒度
- 哪些來源可信
- 要輸出哪種圖
- 是否需要增量更新／級聯分析

不必先建立完整 ontology。先從使用案例出發，後續再擴充 organizing principles。

### 2. 初始化

```bash
python3 scripts/relationship_graph.py init --root <project> --title "圖譜名稱"
```

不得覆寫既有圖，除非使用者明確要求 `--force`。

### 3. 切分來源並抽取

對每份資料：
1. 列出候選實體、別名與類型。
2. 列明示關係和證據。
3. 列推論關係、推論鏈與替代解釋。
4. 列事件、時間、地點、角色與後果。
5. 找跨文件同一實體與同名不同實體。
6. 產生批次 JSON，先 validate 再 import。

來源大時沿用 Graphify：detect → extract → build → cluster → analyze → report → export。

### 4. 新增節點／關係／事件

```bash
python3 scripts/relationship_graph.py add-node \
  --root <project> --id person:alice --label Alice --type person \
  --alias 艾莉絲 --properties '{"role":"editor"}' \
  --source-file notes.md --source-location L12-L20

python3 scripts/relationship_graph.py add-edge \
  --root <project> --source person:alice --target org:acme \
  --relation works_for --category membership --valid-from 2026-01-01 \
  --confidence EXTRACTED --source-file contract.md --source-location L8

python3 scripts/relationship_graph.py add-event \
  --root <project> --id event:meeting-001 --label "專案會議" \
  --time 2026-07-31 --place place:office \
  --participant person:alice:chair --participant person:bob:attendee
```

若 ID 含冒號，participant 的 CLI `NODE:ROLE` 會歧義；批次 JSON 可完整指定 role。簡單 CLI 可使用無冒號 alias 作參與者名稱。

### 5. 驗證

```bash
python3 scripts/relationship_graph.py validate --root <project>
```

檢查：
- 重複 ID／別名衝突
- dangling edge
- 缺 relation
- confidence 範圍
- EXTRACTED 卻無來源
- 時間區間錯誤
- causes／depends_on／parent_of／precedes 循環

警告不等於錯誤；保留歧義供人工審核。

### 6. 查詢

```bash
python3 scripts/relationship_graph.py search --root <project> "關鍵詞"
python3 scripts/relationship_graph.py neighbors --root <project> "Alice"
python3 scripts/relationship_graph.py path --root <project> "Alice" "Project X"
python3 scripts/relationship_graph.py timeline --root <project>
python3 scripts/relationship_graph.py affected --root <project> "Rule A" --depth 3
```

Graphify 的 query/path/explain 可直接讀同一 `graph.json`。時間切片可傳 `--as-of YYYY-MM-DD`。

### 7. 更新與版本

關係失效不刪除：

```bash
python3 scripts/relationship_graph.py close-edge \
  --root <project> --id edge:... --status superseded --valid-to 2026-07-31
```

重大變更先：

```bash
python3 scripts/relationship_graph.py snapshot --root <project>
```

再用 affected 查級聯。需要刪除時仍先保留 snapshot 和 audit。

### 8. 視覺化與匯出

```bash
python3 scripts/relationship_graph.py export --root <project> --graphml --cypher
```

產生 Graphify HTML、Mermaid、報告；可選 GraphML／Cypher。圖太大時先查詢子圖或依社群／類型／時間切片，不把一萬條線硬塞同一畫面。

## 視覺化策略

- 人物／組織關係：flowchart，edge 標動詞，顏色分 relation category。
- 資料 schema：Mermaid ER 圖。
- 事件演化：timeline 或事件 flowchart。
- 因果／依賴：有向圖，保留方向。
- 超大圖：Graphify HTML 社群聚合；先 overview，再 drill-down。

「一目瞭然」需要分層，不等於把所有節點一次顯示。

## 連續性狀態圖譜協作
圖譜不只保存角色與關係，也必須保存事件→狀態→能力→行為的可追溯鏈。每次小說或互動回合後，將新事件、時間、資源、生理負荷、認知容量與未解問題建成可驗證節點／關係；生成前以 `affected`、`timeline`、`path` 和知識邊界查詢子圖，供 `novel-reality-state-engine` 生成 Reality Card。圖譜缺少最新事件或驗證未通過時，不得當作連續性已完成。



小說節點至少包含：人物、地點、派系、事件、卷、章、場景、伏筆、物件、世界規則、祕密／主張。

寫章前：
- 查本章 POV 的鄰居、地點、活躍事件和最短牽連。
- 查角色 knows／misbelieves／conceals_from。
- 查世界規則與場景的 depends_on。
- 由子圖建立 context pack。

章後：
- 新人物／事件／關係／物件轉移回寫。
- 已失效關係關閉 valid time。
- 場景和出場角色連 `appears_in`，POV 連 `pov_of`。
- 伏筆連 `foreshadows`／`resolves`。
- 改綱前 snapshot＋affected，標記 cascade_pending。

圖譜提供結構與證據，不取代正文、故事聖經和時間線；它是跨檔案索引與推理骨架。

## 一般領域整合

- 家族：親屬、婚姻、繼承、事件和版本變化。
- 組織：正式匯報、實際控制、資金、合作與衝突。
- 專案：任務依賴、文件、決策、負責人與修改影響。
- 研究：論文、主張、證據、支持／反駁與引用。
- 歷史：事件、參與者、地點、因果、來源版本和時間切片。

敏感私人資料只有在使用者明確提供且確有必要時才建模；不擅自搜集或推斷。

## 最終品質檢查

- 每個重要實體是否可被搜尋，而非塞在屬性文字？
- 關係方向、動詞和時間是否明確？
- 明示、推論與歧義是否分層？
- 每項重要主張能否回到來源證據？
- 同名／別名是否消歧？
- 多方事件是否正確建成事件節點？
- 舊事實是否保留版本而非直接覆蓋？
- 圖是否可用 overview＋子圖閱讀？
- 修改是否先 snapshot 並做 affected？
- 是否能用 Graphify query/path/explain 直接回答問題？
