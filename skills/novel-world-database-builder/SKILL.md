---
name: novel-world-database-builder
version: 1.2.0
description: 當使用者要求建立／保存／更新／查詢小說世界資料庫、世界觀知識庫、世界設定圖譜、地點／派系／資源／規則資料庫、世界時間線與因果網，或要把 world bible、world rules、地點檔、派系檔與研究資料轉成可持久化 Graphify 圖譜時使用。建立前必須先完成世界資料庫分類，至少保存 `subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`genre`、`classification_basis` 與 `classification_confidence`；分類不明確時標 `AMBIGUOUS`，不得無分類匯入。將原創或研究型小說世界拆成可追溯的世界、地點、派系、人物、資源、物件、科技／魔法、法律／規則、文化／物種、事件、主張與證據節點，支援認知版本、正典狀態、雙時間、衝突保留、快照、級聯影響、查詢與匯出；與 novel-worldbuilding-architect 分工：前者設計與檢查世界系統，本技能負責分類、持久化、版本化、查詢與同步，不把圖譜反向當成正典。
---

# Novel World Database Builder

## 目的與分工

把小說世界從散落的 `world-bible.md`、`world-rules.md`、地點／派系檔、時間線、研究筆記與章後差分，建立成可搜尋、可追溯、可更新的 Graphify 相容 property graph。它是**世界觀的結構索引與版本帳本**，不是替作者自動發明世界的工具。

- `novel-worldbuilding-architect`：提出世界設計、因果後果、量級估算與合理性檢查。
- `novel-world-database-builder`：保存世界層地點／派系／資源／規則／事件與主張；特殊物本體、版本、能力、規格、能源／限制、持有／操作與生命週期交給 `special-object-database-builder`。世界圖譜只引用穩定 object ID，不建立第二份特殊物正本。
- `knowledge-relationship-graph`：提供底層 schema、CLI、時間／證據／級聯能力。
- `long-form-novel-writer`：章前取得世界交接包，章後把已核准差分回寫。

正典優先順序：使用者明確決策／`[LOCKED]` > 定稿正文／`[CANON]` > 核准世界檔 > `[PLAN]` > `[DRAFT]` > 技能推論／`[PROPOSAL]`。圖譜永遠是衍生索引，不得反向覆寫世界聖經、規則帳本或正文。

## 硬性原則

1. **範圍先行**：先問世界資料庫要支援哪種查詢或哪一卷；只建故事會使用的深度，不為完整而建立百科。
2. **分類先行（硬性）**：每個世界資料庫都必須先填寫世界分類契約；至少保存 `subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`genre`、`classification_basis`、`classification_confidence`。缺欄位不得進入正式資料庫；無法消歧時保存 `AMBIGUOUS`，不可靜默猜測。
3. **資料庫分開**：不同作品、媒體版本、宇宙／時間線或正典範圍原則上建立不同 `world_id`／slug；只有使用者明確指定共享世界或跨版本比較時才建立 `contains`／`derived_from`／`variant_of` 連結，不把改編版設定混成同一正典。
4. **穩定 ID**：使用 `world:<slug>`、`place:<slug>`、`faction:<slug>`、`rule:<slug>`、`resource:<slug>`、`event:<slug>`、`claim:<slug>` 等 canonical ID；改名放 `aliases`，不要以新名稱重建同一實體。
5. **來源可追溯**：重要節點／關係附 `source_file`、`source_location`、`source_url` 或 `evidence`。作者提供的原創設定也要標明來自哪份檔案或決策。
6. **特殊物引用不重建正本**：若世界規則／資源／派系／事件涉及道具、鎧甲、機體、載具、武器或裝置，世界資料庫只建立穩定 object ID 的引用與世界層關係；特殊物本體、版本、能力、規格、能源／限制、持有／操作、模組與生命週期由 `special-object-database-builder` 保存。兩個資料庫的分類、來源、快照與同步狀態分開管理。
7. **分開事實與推論**：`EXTRACTED` 僅表示來源明示；`INFERRED` 表示因果／心理／社會推論；`AMBIGUOUS` 表示衝突或未定。`FICTIONAL_PROPOSAL` 不當作 confidence 值，放在 `properties.provenance_class`，且保持 `[PROPOSAL]`。
8. **不覆蓋衝突**：新規則、改名、政權更換、資源枯竭與不同歷史版本先 snapshot；新增主張或版本，舊 edge 標 `superseded`／`disputed` 並保留 valid time 與 audit。
9. **多方事件建事件節點**：戰爭、政變、災害、條約、發明、遷徙與章節事件使用 `event` 節點，不把參與者全部兩兩亂連。
10. **規則必須可查**：世界規則、法律、科技／魔法不只寫在長段落中；至少有條件、能力、成本、執行者／機制、例外與首次建立欄位。
11. **名稱本地化與查詢**：`label` 保留原始／正典名稱，不因翻譯改 ID 或原名；凡含非中文文字，或中文與日文／韓文／英文混合，建立 `properties.name_zh`（台灣繁體中文查詢名稱），並保存 `name_zh_language: "zh-Hant-TW"`、`name_zh_provenance`、`name_zh_source_label`。這是輔助名稱，不代表官方譯名；無法可靠翻譯時填 `UNKNOWN`／`[UNKNOWN]`，不得硬猜。列表、搜尋、消歧與跨資料庫引用要同時比對原名、別名與 `name_zh`。
12. **真相不偷渡**：角色查詢只可回傳其 `knows`／`believes`／`misbelieves` 權限內的版本；作者層查詢才可看 `[TRUTH]`。
12. **不存機密**：不把 API key、密碼、token 或與故事無關的私人敏感資料寫入圖譜、批次檔或匯出檔。

## 儲存位置與結構

資料庫正本是 `<WORLD_DATABASE_ROOT>/<slug>/graphify-out/graph.json`；匯出檔不可取代正本。特殊物本體資料庫不使用這個路徑，改由 `special-object-database-builder` 的 `SPECIAL_OBJECT_DATABASE_ROOT` 保存。

Minis 預設：

```text
WORLD_DATABASE_ROOT=<WORLD_DATABASE_ROOT>
WORLD_DATABASE_WORK_ROOT=<WORKSPACE_ROOT>
DB=<WORLD_DATABASE_ROOT>/<slug>
WORK=<WORKSPACE_ROOT>/<slug>-world-db
```

建議結構：

```text
<world-db>/
└── graphify-out/
    ├── graph.json          # 唯一正本
    ├── graph.json.bak      # 最近寫入前備份
    ├── audit.jsonl         # 操作紀錄
    ├── snapshots/          # 重大更新前快照
    ├── graph.html          # 衍生視覺化
    ├── graph.mmd.md       # 衍生 Mermaid
    ├── graph.graphml      # 選用匯出
    ├── cypher.txt         # 選用匯出
    └── GRAPH_REPORT.md    # 衍生報告
```

若資料庫服務單一小說專案，可把同一 `graphify-out/` 放在專案根目錄；必須在 `world-database-link.json` 或專案說明中記錄 `world_id`、資料庫路徑、來源正典與最後同步時間，避免孤立圖譜。

## 世界分類契約（建立前必填）

`world_id`、資料庫 manifest、catalog 項目與世界根節點的 `properties` 必須一致保存以下欄位；這是世界資料庫級分類，不等同節點的 `world_category`：

- `subject_category`：`real`（現實／歷史）、`novel`（小說）、`anime`（漫畫／動畫／動漫）、`film`（電影版本／電影原創）、`game`、`stage`、`myth`、`original`、`other`。
- `subject_subcategory`：更細的類型，例如 `manga_cyberpunk`、`anime_original`、`film_adaptation`、`original_fantasy`、`real_historical`。
- `subject_kind`：`real_world`、`fictional_world`、`adapted_world`、`shared_world`、`unknown`。
- `source_medium`：來源媒體陣列，例如 `manga`、`tv_anime`、`anime_film`、`film`、`novel`、`official_website`、`author_decision`。
- `canon_scope`：`real_record`、`novel_canon`、`manga_canon`、`anime_canon`、`film_canon`、`cross_adaptation`、`user_created`、`unknown`。
- `version_scope`：具體作品、卷／期、播映／出版版本或「未鎖定版本」；不得只寫「攻殼機動隊」等模糊名稱。
- `franchise`：系列／作品名；無系列填 `null`。
- `genre`：可複選的題材標籤，例如 `cyberpunk`、`posthuman_science_fiction`、`political_thriller`。
- `classification_basis`：一句可回溯的分類理由，附 `source_file`／`source_url`／`evidence`。
- `classification_confidence`：`EXTRACTED`、`INFERRED` 或 `AMBIGUOUS`；分類信心與世界內容的證據信心分開保存。

### 分類決策規則

1. 建立或匯入前先分類；先做作品／媒體／版本消歧，再抽取世界內容。
2. `real`、`novel`、`anime`、`film` 等分類是互斥的主分類；跨媒體作品依本資料庫實際鎖定的正典版本分類，不因同一系列有其他改編而混合。
3. 原作漫畫世界歸 `subject_category: anime`、`subject_subcategory: manga_<genre>`、`subject_kind: fictional_world`、`canon_scope: manga_canon`；漫畫／動畫在此欄位模型中共用 `anime` 主類，`source_medium` 必須寫明 `manga`。
4. 「初版／原作」沒有唯一指向時，先建立分類主張或列 `[AMBIGUOUS]`，不得擅自選電影、動畫或漫畫；使用者指定後才鎖定。
5. 每個資料庫的 catalog 與 manifest 都必須可按 `subject_category`、`subject_subcategory`、`subject_kind`、`franchise`、`version_scope` 篩選；交付時列出分類結果與排除的版本。
6. 已存在但缺少分類契約的資料庫，更新時先 snapshot，再補分類；若資料來源不足，補齊欄位並標 `AMBIGUOUS`，不得假裝已核實。

### 最小分類範例

```json
{
  "subject_category": "anime",
  "subject_subcategory": "manga_cyberpunk",
  "subject_kind": "fictional_world",
  "source_medium": ["manga", "official_website"],
  "canon_scope": "manga_canon",
  "version_scope": "士郎正宗《攻殼機動隊 THE GHOST IN THE SHELL》初版原作漫畫（1989–1990）；不含1995電影、S.A.C.與其他改編",
  "franchise": "攻殼機動隊／THE GHOST IN THE SHELL",
  "genre": ["cyberpunk", "posthuman_science_fiction", "political_thriller"],
  "classification_basis": "本資料庫鎖定士郎正宗原作漫畫，不把後續動畫與電影改編設定併入",
  "classification_confidence": "EXTRACTED"
}
```

## 名稱本地化

研究、建立、匯入與更新任何節點時，保留原始／正典 `label`；凡名稱含非中文文字，或中文與日文／韓文／英文混合，建立台灣繁體中文 `properties.name_zh` 以便無法輸入原文時查詢與指名。翻譯優先序固定為：有可靠來源的官方中文譯名就使用官方譯名；沒有官方中文譯名時，不自行意譯，改依原文可靠讀音採台灣繁體中文音譯，必要時在音譯後括註原名或型號。保存 `name_zh_language: "zh-Hant-TW"`、`name_zh_provenance`、`name_zh_source_label`。原名、ID、aliases 不被翻譯覆蓋；`name_zh` 不自動宣稱是官方譯名。只有在原文讀音也無法可靠判讀時才填 `UNKNOWN`／【待定】，不得捏造或以自行意譯代替。搜尋與消歧同時比對 `label`、`aliases`、`properties.name_zh`。

### 節點類型

使用 Graphify 通用 `entity_type`，再用 `properties.world_category` 細分，避免自訂類型造成工具不相容：

| 世界概念 | 建議 entity_type | `world_category` |
|---|---|---|
| 世界／宇宙／行星 | `system` | `world`／`universe`／`planet` |
| 地區／城市／聚落／地標 | `place` | `region`／`city`／`settlement`／`landmark` |
| 派系／政府／宗教／公司 | `group` 或 `organization` | `faction`／`government`／`religion`／`company` |
| 世界規則／法律／科技／魔法 | `system` | `world_rule`／`law`／`technology`／`magic` |
| 資源／能源／貨幣／服務 | `resource` | `material`／`energy`／`currency`／`service` |
| 文化／語言／階級／規範 | `concept` | `culture`／`language`／`class`／`norm` |
| 物種／族群／人口群 | `group` | `species`／`population` |
| 歷史／政治／災害／發明事件 | `event` | `historical`／`political`／`disaster`／`discovery` |
| 角色、物件、來源、爭議主張 | `person`／`object`／`document`／`claim` | 依領域填寫 |

核心節點至少包含：`id`、`label`、`entity_type`、`aliases`、`status`、`confidence`、`confidence_score`；世界特有欄位放 `properties`。名稱含非中文文字時，另必須在 `properties` 保存 `name_zh`、`name_zh_language`、`name_zh_provenance` 與 `name_zh_source_label`；`label` 與 ID 不得被翻譯覆蓋。建議加入 `canon_status`、`epistemic_layer`、`scope`、`valid_from`／`valid_to`、`first_established`、`story_function`、`cost`、`constraints`、`exceptions`、`evidence`。

### 關係詞彙

關係使用小寫 snake_case 動詞並保持方向；優先使用：

- 結構／空間：`contains`、`located_in`、`borders`、`connected_to`、`precedes`、`follows`、`occurred_at`
- 權力／制度：`controls`、`governs`、`regulates`、`enforces`、`member_of`、`leads`、`allied_with`、`opposes`
- 資源／能力：`produces`、`consumes`、`uses`、`requires`、`depends_on`、`enables`、`limits`、`blocks_access_to`、`trades_in`
- 世界因果：`causes`、`contributes_to`、`triggers`、`responds_to`、`changes_state_of`、`violates_rule`、`bound_by_rule`
- 知識／版本：`knows`、`believes`、`misbelieves`、`supports`、`contradicts`、`documented_in`、`derived_from`、`revealed_in`
- 小說交接：`appears_in`、`pov_of`、`foreshadows`、`resolves`、`affects`、`requires_update`

`properties` 可保存角色、數量、強度、條件、合法性、運輸時間、普及率與失靈方式；不要用 `related_to` 取代可辨識的語意。

## 建立流程

### 1. 定義資料庫契約

先填寫並驗證世界分類契約：`world_id`、slug、`subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`genre`、`classification_basis`、`classification_confidence`。再確認世界／作品 slug、資料截止日、來源正典、要回答的問題、時間粒度、是否包含 `[PLAN]`／`[DRAFT]`、要不要匯出 HTML／GraphML／Cypher，以及世界資料庫與小說專案的連結方式。分類不明時建立 `[AMBIGUOUS]` 分類主張，不得直接初始化或正式匯入。缺口只列 2–3 個有實質差異的 `[PROPOSAL]`，不要靜默補成 `[CANON]`。

### 2. 準備來源與盤點

優先讀取：`project-brief.md`、`story-bible.md`、`world-bible.md`、`world-rules.md`、`locations/`、`factions/`、`timeline.md`、`knowledge-matrix.md`、研究檔與章後世界差分。列出：

- 實體、別名、類型與消歧結果；
- 規則句、成本、資格、執行者、例外；
- 地點的出入口、資源、控制者、交通與危險；
- 派系的公開目標、實際利益、資源、合法性、執行力與分裂；
- 資源流、生產／運輸／分配／消耗與黑市；
- 歷史事件、因果、時間、地點、參與者與版本；
- `[TRUTH]`／`[OFFICIAL]`／群體信念／流言／角色已知版本；
- 一階／二階／三階後果及尚未決定事項。

把多方行動建成事件節點；把互相衝突的說法建成 `claim` 節點，由來源以 `supports`／`contradicts` 連接。

### 3. 產生批次 JSON

先寫入 `<WORLD_DATABASE_WORK_ROOT>/<slug>-world-db/extraction-batch.json`，使用本技能的 `templates/world-extraction-batch.json` 作骨架；不能直接手改正本。節點與關係的 `source_file`、`source_location`、`source_url` 和 `evidence` 使用相對路徑或可回讀 URL。原創設定可用 `source_file: "world-bible.md"`、`evidence.quote` 和 `properties.source_kind: "author_decision"`。

### 4. 初始化／匯入

```bash
GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py
DB=<WORLD_DATABASE_ROOT>/<slug>
BATCH=<WORLD_DATABASE_WORK_ROOT>/<slug>-world-db/extraction-batch.json

python3 "$GRAPH" init --root "$DB" --title "<世界名>世界資料庫"
python3 "$GRAPH" import --root "$DB" --file "$BATCH" --strict
python3 "$GRAPH" validate --root "$DB"
python3 "$GRAPH" export --root "$DB" --graphml --cypher
```

若 `graph.json` 已存在，禁止重跑 `init --force`；先 `snapshot`，再建立只含新增／變更內容的增量批次。只有作者明確要求重建且已保存舊版時才能 force。

### 5. 驗證與交付

至少檢查：先以 `classification` 區塊驗證世界分類契約完整且與世界根節點／manifest／catalog 一致；缺任何必填欄位或版本範圍只有模糊系列名時，拒絕正式匯入。再檢查零 dangling edge、零重複節點 ID、零無效時間區間、重要 `EXTRACTED` 資料有來源、別名衝突已消歧或記為警告、規則／資源／派系節點有必要關係。用三種查詢 smoke test：

```bash
python3 "$GRAPH" search --root "$DB" "關鍵世界名詞"
python3 "$GRAPH" neighbors --root "$DB" "world:<slug>"
python3 "$GRAPH" timeline --root "$DB"
```

交付時說明資料庫正本路徑、節點／關係數、驗證結果、包含／排除的正典層、未決衝突、最後 snapshot，以及正本與衍生檔案連結。不可只交摘要而不保存可回讀資料。

## 更新、衝突與級聯

1. 讀取新章後差分、作者決策或修訂來源；先判斷是新增、狀態變化、別名、時間版本還是互斥主張。
2. 重大變更前：`snapshot --root "$DB"`；若改規則／資源／地點控制／歷史因果，再以 `affected --node ... --depth 3` 查級聯。
3. 只新增新節點／edge；失效關係用 `close-edge --status superseded --valid-to ...`，保留舊版與 audit。
4. 互斥版本建立 `claim`，由來源 `supports`／`contradicts`；不能以最新筆記直接刪除舊歷史。
5. 變更後重新 `validate`、`search`、`neighbors`、`timeline`、`export`；必要時將受影響節點標 `cascade_pending`，交由作者決定是否同步回世界聖經、章綱、角色認知與正文。

## 查詢與長篇交接

### 常用問題

- 「這項魔法依賴哪些資源、誰控制入口？」：`neighbors`／`path`／`affected`。
- 「城市斷糧會影響哪些派系與角色？」：從 `resource` 或 `event` 做 `affected`，再按時間切片。
- 「這段歷史有哪些互相衝突的版本？」：搜尋 `claim`，檢查 `supports`／`contradicts` 與來源。
- 「角色能不能知道這個真相？」：查 `knows`／`believes`／`misbelieves`、`revealed_in`，不可只看 `[TRUTH]`。
- 「修改規則會改到哪些章？」：查 `affected`，再回讀 `appears_in`／`bound_by_rule`／`depends_on`。

### 章前世界交接包

交給 `long-form-novel-writer`：

1. 本章相關 `[CANON]`／`[LOCKED]` 規則、地點、派系、資源與事件；
2. 地點可行動空間、出入口、交通／通訊、風險與當前狀態；
3. 組織的正式權限、實際控制、合法性、資訊與失靈點；
4. 科技／魔法的資格、成本、冷卻、反制與已知例外；
5. 角色可知／誤信版本與不能偷用的 `[TRUTH]`；
6. 物流、時間、資源量級與延遲後果；
7. 本章可能觸發的一階／二階公共後果；
8. 不可臨時新增的解法與待作者決策項。

### 章後回寫

只把已核准的狀態差分寫入圖譜：新地點／派系／資源／事件、控制權與物件轉移、規則使用／違反／例外、角色與讀者的資訊變化、伏筆／回收、公共後果。即興描寫若未核准，標 `[DRAFT]` 或 `[PROPOSAL]`，不得升成目前世界真相。

## 品質檢查

- [ ] **世界資料庫分類契約完整**：manifest、catalog、world root 與批次 `classification` 的 `subject_category`、`subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`genre`、`classification_basis`、`classification_confidence` 均存在且一致；分類不明確時為 `AMBIGUOUS`。
- [ ] 圖譜能回答本次定義的問題，而不是只有節點清單。
- [ ] 每個重要實體可搜尋，關係有方向、動詞、時間與狀態。
- [ ] 世界、規則、地點、派系、資源、事件、主張與來源沒有被塞成不可查的長文字。
- [ ] `[LOCKED]`／`[CANON]`／`[PLAN]`／`[DRAFT]` 與 `[TRUTH]`／官方／信念／角色認知分開。
- [ ] 重要 `EXTRACTED` 主張能回到來源；推論、提案與歧義不冒充事實。
- [ ] 資源流、資格、執行、黑市、物流與失靈至少在相關設定中有橋樑。
- [ ] 歷史事件使用時間、地點、參與者與因果關係，不只是一串年份。
- [ ] 修改前有 snapshot，修改後有 validate、affected 或明確記錄不需要級聯。
- [ ] 角色查詢遵守知識權限，圖譜不取代世界聖經與正文。
- [ ] 交付包含正本、衍生檔、驗證結果、未知項與下一個同步點。

## 與其他技能協作

需要設計或合理性檢查時先載入 `../novel-worldbuilding-architect/SKILL.md`；需要長篇章前／章後同步時載入 `../long-form-novel-writer/SKILL.md`；需要人物知識與角色資料庫時搭配 `../character-database-builder/SKILL.md`；需要改綱影響、最短路徑或通用圖譜能力時載入 `../knowledge-relationship-graph/SKILL.md`。本技能只負責世界資料的持久化與結構化，不把自己的推論升格成作者正典。
