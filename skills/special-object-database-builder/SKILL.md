---
name: special-object-database-builder
version: 1.0.0
description: 當使用者要求建立／保存／更新／查詢／比較小說、漫畫、動畫、電影、遊戲或原創作品中的特殊物資料庫時使用，包含小叮噹／哆啦A夢道具、鋼鐵人各代鎧甲、鋼彈／機動戰士／機體、機器人、載具、武器、神器、裝置、裝備系統與具人格的機械生命體。以 Graphify 相容 property graph 持久化特殊物、版本／變體、模組、能力、規格量測、能源與消耗、資格與限制、弱點與反制、製造／設計、持有／操作者、位置、損傷／維修／升級、事件、章節與來源證據；強制分離作品、媒體、季別、宇宙、時間線與正典，不把同名改編物靜默合併。支援特殊物比較、依賴／影響查詢、小說章前物件交接、章後狀態同步、快照、衝突版本、驗證與 HTML／Mermaid／GraphML／Cypher 匯出。與 novel-world-database-builder 分工：世界資料庫保存世界層資源／規則／制度，special-object-database-builder 保存物件本體與生命週期；需要設計或合理性檢查時搭配 novel-worldbuilding-architect，跨章索引搭配 knowledge-relationship-graph 與 long-form-novel-writer。
---

# Special Object Database Builder

## 目的與分工

把「某件特殊物能做什麼、需要什麼、為何不能無限使用、誰能操作、目前在哪裡、經歷過哪些改裝與損壞」變成可搜尋、可追溯、可更新的 Graphify 相容資料庫。它不是百科抄錄器，也不替作者把沒有來源的能力升格成正典。

- `novel-worldbuilding-architect`：設計特殊物的世界功能、成本、制度後果、物流與合理性。
- `novel-world-database-builder`：保存世界／地點／派系／資源／規則／事件；特殊物可作為被引用的物件節點，但不吞掉本技能的本體資料。
- `special-object-database-builder`：保存特殊物本體、版本、變體、系統、規格、能力、限制、持有與生命週期。
- `knowledge-relationship-graph`：提供時間、證據、版本、級聯與視覺化底層。
- `long-form-novel-writer`：章前取得物件交接包，章後回寫已核准的物件狀態差分。

## 硬性原則

1. **先鎖定範圍與版本**：一個資料庫預設只對應一個作品／媒體／宇宙／正典範圍。未指定版本不得把漫畫、動畫、電影、遊戲或不同宇宙的設定混成一件物；若確實要比較，建立 `cross_adaptation` 目錄並讓每個物件節點各自保存版本。
2. **物件身分與變體分開**：系列、型號、具名個體、改裝、武裝配置、複製品、同型量產機不可只靠長段落區分。使用 `model_of`、`variant_of`、`loadout_of`、`copy_of`、`adaptation_of`、`component_of` 連接，保留穩定 ID。
3. **特殊物與角色分開**：有自主意識的機械可作 `object` 與 `character_record` 的雙重索引，但人格、知識與行為資料另建角色節點／角色資料庫，以 `instantiates`、`inhabits` 或 `embodied_as` 連接；不能因機體有人駕駛就把駕駛者與機體合成一個人。
4. **能力必須帶條件與代價**：每個可重複使用的能力都要記錄啟動條件、消耗、冷卻／持續時間、射程／作用範圍、失效方式、已知反制與例外。能力不能只寫「很強」「全能」。
5. **規格不可假精確**：保留數值、單位、測量方式、版本、來源與不確定性；不同媒體或不同設定口徑的重量、速度、能源、火力不可直接覆蓋。需要換算時標 `CALCULATED` 並保存原始量測與假設。
6. **正典與認知分開**：`[LOCKED]`／`[CANON]`／`[PLAN]`／`[DRAFT]`／`[PROPOSAL]`／`[UNKNOWN]` 是狀態；`[TRUTH]`／`[OFFICIAL]`／`[BELIEF:<group>]`／`[RUMOR]`／`[KNOWN:<character>]` 是認知層，不能互相取代。
7. **來源與推論分層**：明示資料標 `EXTRACTED`；換算與模型推導放 `properties.provenance_class: CALCULATED`；合理推論標 `INFERRED`；來源衝突或身分不明標 `AMBIGUOUS`；作者尚未核准的原創設計標 `FICTIONAL_PROPOSAL` 且保持 `[PROPOSAL]`。
8. **所有權、持有、操作、控制分開**：`owned_by`、`possessed_by`、`operated_by`、`assigned_to`、`controls` 不是同義詞，均可有不同時間區間與條件。
9. **名稱本地化與查詢**：`label` 永遠保留原始／正典名稱；凡含非中文文字，或中文與日文／韓文／英文混合，建立台灣繁體中文查詢欄位 `properties.name_zh`。翻譯優先序固定為：**有可靠來源的官方中文譯名優先；沒有官方中文譯名時，依原文可靠讀音採台灣繁體中文音譯，不自行意譯**；必要時音譯後括註原名或型號。另保存 `name_zh_language: "zh-Hant-TW"`、`name_zh_provenance` 與 `name_zh_source_label`。`name_zh` 是輔助名稱，不取代 ID、`label` 或 `aliases`，不代表官方譯名；只有在原文讀音也無法可靠判讀時才填 `UNKNOWN`／`[UNKNOWN]` 並待核對。查詢與比較必須同時比對原名、別名與 `name_zh`。
10. **不存不必要的敏感資料**：真人／公開人物相關內容只保存與物件建模必要的公開資料；不寫入私人地址、聯絡方式、密碼、token、API key 或無關私生活。

## 儲存位置與結構

正本是 `<SPECIAL_OBJECT_DATABASE_ROOT>/<slug>/graphify-out/graph.json`；HTML、Mermaid、GraphML、Cypher 與報告都是衍生檔，不可取代正本。

Minis 預設：

```text
SPECIAL_OBJECT_DATABASE_ROOT=<SPECIAL_OBJECT_DATABASE_ROOT>
SPECIAL_OBJECT_DATABASE_WORK_ROOT=<WORKSPACE_ROOT>
DB=<SPECIAL_OBJECT_DATABASE_ROOT>/<slug>
WORK=<WORKSPACE_ROOT>/<slug>-special-object-db
```

建議結構：

```text
<special-object-db>/
├── database-manifest.json
├── source-register.md
├── object-catalog.md                 # 可讀索引，圖譜仍是正本
└── graphify-out/
    ├── graph.json                    # 唯一機器正本
    ├── graph.json.bak
    ├── audit.jsonl
    ├── snapshots/
    ├── graph.html
    ├── graph.mmd.md
    ├── graph.graphml
    ├── cypher.txt
    └── GRAPH_REPORT.md
```

可攜／小說專案若要連結資料庫，使用 `templates/special-object-database-link.json`，不要把外部資料庫悄悄複製成專案內另一份正本。

## 特殊物分類契約（建立前必填）

資料庫批次的頂層 `classification`、manifest 與資料庫的 `graph.classification` 必須一致保存：

- `subject_category`：`real`、`novel`、`anime`、`film`、`game`、`comic`、`stage`、`myth`、`original` 或 `other`。
- `subject_subcategory`：例如 `anime_gadget`、`film_powered_armor`、`anime_mecha`、`game_vehicle`、`original_artifact`。
- `subject_kind`：`fictional_object_catalog`、`real_technology_catalog`、`original_object_catalog`、`cross_media_catalog` 或 `unknown`。
- `source_medium`：`manga`、`tv_anime`、`anime_film`、`film`、`novel`、`game`、`official_guide`、`author_decision` 等陣列。
- `canon_scope`：`real_record`、`manga_canon`、`anime_canon`、`film_canon`、`novel_canon`、`game_canon`、`cross_adaptation`、`user_created` 或 `unknown`。
- `version_scope`：具體媒體、作品版本、宇宙、季別／劇場版／遊戲版本或資料截止範圍；不得只寫系列名。
- `franchise`：系列／作品名，無系列填 `null`。
- `genre`：`science_fiction`、`superhero`、`mecha`、`fantasy`、`gadget_comedy` 等題材陣列。
- `classification_basis`：可回溯的分類理由，帶來源檔／URL／使用者決策。
- `classification_confidence`：`EXTRACTED`、`INFERRED` 或 `AMBIGUOUS`。

每一個特殊物主節點（`entity_type: object` 且 `properties.special_object_record: true`）另外必須保存：

```json
{
  "object_category": "gadget|powered_armor|mecha|mobile_suit|vehicle|weapon|tool|artifact|device|robot|sentient_machine|equipment_system|other",
  "object_subcategory": "可查詢的細分類",
  "object_kind": "fictional_object|real_technology|original_object|hybrid|unknown",
  "identity_mode": "singleton|model_line|variant|loadout|component|copy|prototype|unknown",
  "version_scope": "具體版本，不得只寫系列名",
  "canon_scope": "anime_canon",
  "franchise": "作品／系列",
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS"
}
```

`object_category` 描述物件本身，不取代來源分類；例如電影版鋼鐵人鎧甲可為 `film` + `powered_armor`，動畫版鋼彈可為 `anime` + `mobile_suit`，小叮噹／哆啦A夢道具可為 `anime` + `gadget`。原作漫畫、電視動畫、劇場版、重製版與遊戲機體要用不同 `version_scope`，除非使用者明確要求跨版本比較。

## 圖譜資料模型

### 主要節點

- `object`：具名道具、鎧甲、機體、載具、武器、神器、機械個體或裝備系統。
- `system`：反應爐、推進器、感測器、AI、特殊裝甲、武器模組、操作介面等可重複查詢的子系統。
- `concept`：能力、技術、材料、標準、模式或戰術概念。
- `resource`：能源、彈藥、燃料、稀有材料、維修資源或服務。
- `person`／`organization`／`group`：設計者、製造者、駕駛者、所有者、軍隊、公司或派系；角色資料要遵守角色分類技能。
- `place`：工廠、基地、倉庫、戰場、博物館或可公開定位的故事場所。
- `event`：製造、啟用、交接、戰鬥、損傷、維修、改裝、升級、轉移、報廢或出場事件。
- `document`／`claim`：官方設定集、百科、訪談、章節、爭議規格或互斥說法。

主物件節點至少有：`id`、`label`、`entity_type`、`aliases`、`status`、`confidence`、`confidence_score`、`properties`、來源與證據。建議的 `properties` 包含：

```json
{
  "special_object_record": true,
  "canon_status": "[CANON]",
  "epistemic_layer": "[TRUTH]",
  "function": "物件在故事／世界中的主要功能",
  "form_factor": "道具／鎧甲／機體／載具……",
  "operator_model": "單人／多人／遠端／自主／資格限制",
  "power_source": [],
  "capabilities": [],
  "measurements": [],
  "requirements": [],
  "costs": [],
  "constraints": [],
  "failure_modes": [],
  "known_counters": [],
  "maintenance": [],
  "availability": "prototype|limited|mass_produced|unique|unknown",
  "story_function": [],
  "provenance_class": "EXTRACTED"
}
```

### 能力與規格

- 可被問「哪些物件有這個能力」的能力，建議建成 `concept:capability-*` 節點，以 `provides_capability` 連接物件；條件、消耗、冷卻、範圍、失效與反制放在 edge `properties`。
- 可被比較的數值使用 `measurements` 陣列，每筆至少含 `metric`、`value`、`unit`、`qualifier`、`version_scope`、`source`；同一物件有衝突數值時建立不同 measurement／claim，不覆寫。
- 能源、彈藥、材料與維修工具若影響劇情，建成 `resource` 節點並用 `requires`、`consumes`、`refuels_with`、`maintained_by` 連線。
- 外觀／配色可放簡短 `appearance`；若造型差異影響辨識、功能或版本，另建 `variant`／`loadout` 節點，不用一段文字混過。
- 具有自主意識的物件要把 `agency_level`、`knowledge_scope`、`decision_rights` 與角色資料分開；「可對話」不自動等於完整角色正典。

### 關係詞彙

優先使用有方向的 snake_case 關係：

- 身分／版本：`model_of`、`variant_of`、`loadout_of`、`copy_of`、`adaptation_of`、`succeeded_by`、`upgraded_from`、`transforms_into`。
- 結構／模組：`component_of`、`contains_system`、`equipped_with`、`compatible_with`、`incompatible_with`、`integrates_with`。
- 能力／資源：`provides_capability`、`enables`、`requires`、`depends_on`、`powered_by`、`consumes`、`produces`、`refuels_with`、`limits`、`vulnerable_to`、`countered_by`。
- 人物／組織：`designed_by`、`manufactured_by`、`owned_by`、`possessed_by`、`operated_by`、`assigned_to`、`controls`、`licensed_to`。
- 空間／事件：`located_in`、`stored_in`、`deployed_in`、`appears_in`、`used_in`、`participated_in`、`damaged_in`、`repaired_in`、`upgraded_in`、`destroyed_in`、`transferred_in`。
- 證據／敘事：`documented_in`、`supports`、`contradicts`、`derived_from`、`revealed_in`、`foreshadows`、`affects`、`requires_update`。

不要用 `related_to` 取代可辨識語意；暫時無法分類時才使用並標 `AMBIGUOUS`。

## 建立流程

### 1. 建立資料庫契約

先填 `classification`，確認作品／媒體／宇宙／版本、資料截止日、資料來源、比較目的、要回答的問題與是否包含草稿。若使用者只說「鋼彈機體」或「鋼鐵人鎧甲」而沒有指定版本，先建立 `AMBIGUOUS` 分類或提出 2–3 個版本選項，不直接把所有改編設定合併。

### 2. 來源盤點與消歧

優先讀取官方設定集、作品正文本身、製作／作者資料、官方網站與使用者提供的聖經；百科與粉絲資料作線索，除非交叉核實不可標作 EXTRACTED。盤點：

- 具名物件、別名、代號、系列／型號與個體／量產關係；
- 媒體、宇宙、季別、劇場版、遊戲版本、出版版本與正典範圍；
- 外形／配置、功能、能力條件、能源、彈藥、消耗、冷卻、資格與限制；
- 尺寸、重量、速度、射程、續航、裝甲、火力、感測、乘員等量測與口徑；
- 設計者、製造者、駕駛者、所有者、派系、基地與轉移事件；
- 生產、啟用、出場、戰鬥、損傷、維修、改裝、升級、失竊、轉讓與報廢時間線；
- 互相衝突的規格、不同角色／機構知道的版本與未決主張。

### 3. 產生批次 JSON

先寫入 `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>/<slug>-special-object-db/extraction-batch.json`，使用 `templates/special-object-extraction-batch.json`。批次不可直接手改 `graph.json`；每個重要節點與 edge 都要帶 `source_file`／`source_url`／`evidence` 或標為 `INFERRED`／`AMBIGUOUS`。

### 4. 驗證、初始化與匯入

```bash
GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py
OBJECT_VALIDATE=<SKILLS_ROOT>/special-object-database-builder/scripts/validate_special_object_classification.py
DB=<SPECIAL_OBJECT_DATABASE_ROOT>/<slug>
BATCH=<SPECIAL_OBJECT_DATABASE_WORK_ROOT>/<slug>-special-object-db/extraction-batch.json

python3 "$OBJECT_VALIDATE" --batch "$BATCH"
python3 "$GRAPH" init --root "$DB" --title "<作品／版本>特殊物資料庫"
python3 "$GRAPH" import --root "$DB" --file "$BATCH" --strict
python3 "$GRAPH" validate --root "$DB"
python3 "$OBJECT_VALIDATE" --batch "$BATCH" --graph "$DB/graphify-out/graph.json"
python3 "$GRAPH" export --root "$DB" --graphml --cypher
```

若資料庫已存在，禁止 `init --force`；先 `snapshot`，再用只含新增／變更內容的增量批次。專用驗證器與 Graphify 一般驗證都要跑，前者檢查特殊物分類／欄位，後者檢查節點、edge、來源與 dangling 關係。

### 5. 完整度稽核、交付與「禁止只有名稱」規則

**名稱目錄不是完成的特殊物資料庫。** 匯入後必須對每個 `object` 執行欄位級稽核；不能因批次很多就把「只知道名稱」交付為可引用資料。

每個物件都要有 `properties.data_completeness`，至少逐欄標出 `COMPLETE`、`PARTIAL` 或 `UNKNOWN`：

```json
{
  "data_completeness": {
    "identity_version": "COMPLETE",
    "function_and_constraints": "COMPLETE",
    "source_traceability": "COMPLETE",
    "technical_specs": "PARTIAL",
    "weapons": "PARTIAL",
    "operators": "UNKNOWN",
    "manufacturer": "PARTIAL",
    "lifecycle_events": "UNKNOWN"
  },
  "required_before_story_use": [
    "確認 version_scope",
    "UNKNOWN 不得自動補寫",
    "情節若依賴規格或狀態，先補來源或標 DRAFT"
  ]
}
```

最低可引用卡（不分機體、船艦、道具或裝甲）必須具備：

1. **身分**：名稱／型號、版本範圍、正典範圍、類型與可查詢中文名；
2. **用途**：故事／世界內的具體功能，而非「戰鬥用」等空泛標籤；
3. **能力與邊界**：至少一項能力、啟動或適用條件、成本／依賴、限制／失效或反制；
4. **運用資訊**：能源或供給、操作模型；武裝／模組、製造／所屬、操作員／持有者能查則分開建欄與關係；
5. **可追溯性**：每項主張有一手來源，或清楚標為 `INFERRED`／`AMBIGUOUS`／`UNKNOWN`，不得把百科摘要升格為官方正典；
6. **場景狀態**：若要供小說引用，另需已知的完整度／損傷、位置、持有／操作、能源／彈藥／冷卻。沒有就明標 `UNKNOWN`，不可捏造。

### 建立／補全的強制順序

1. 先從官方資料建立身份、媒體範圍和具名名錄；若只取得名錄，狀態只能是 `catalog_only`，不可宣稱完成。
2. 對**每一筆**物件逐項收集：型號與身分、功能、系統／能力、武裝／模組、能源／消耗、限制、規格、製造／所屬、操作／持有、關鍵生命週期事件與來源。
3. 一手資料不足時，可用可靠二級資料補作「參考卡」，但每個技術欄位、量測與關係皆標 `INFERRED`，並保留原始 URL／頁面／條目；不得以此把空白填成看似確定的數據。
4. 對查不到的欄位填 `UNKNOWN` + 具體待查項（例如「艦載 MS 數量 UNKNOWN；待官方設定集」），不可留空陣列或用泛稱掩蓋缺口。
5. 產生 `REFERENCE_COVERAGE.md`：列出總物件數、各欄位有資料／PARTIAL／UNKNOWN 的數量、重要缺口、來源層級與可安全引用範圍；再跑抽樣 `neighbors` smoke test。
6. 只有資料卡和驗證都完成後才交付。若使用者要求「盡量補齊」，優先補全既有物件的資訊密度，**不要為了擴充清單再新增一批只有名稱的節點**。

交付時列出：正本路徑、資料庫分類與版本範圍、物件／模組／能力／事件節點與關係數、各欄位完整度、驗證結果、包含／排除的媒體、規格衝突、`UNKNOWN`／待補清單、最後 snapshot，以及正本與衍生檔連結。若只是跨作品比較，不要宣稱已建立單一正典；應說明每個物件的版本隔離方式。

## 查詢與比較

常用問題及查法：

- 「這件鎧甲能做什麼、代價是什麼？」：主物件 `neighbors`，沿 `provides_capability`、`requires`、`consumes`、`limits` 查能力與成本。
- 「哪些道具可以瞬間移動？有何限制？」：`search` 能力節點，再反查 `provides_capability`，按版本／正典分組。
- 「這台機體有哪些改裝與前身？」：`neighbors`／`path` 查 `variant_of`、`upgraded_from`、`component_of`。
- 「誰曾經駕駛／持有它？何時轉移？」：按時間查 `operated_by`、`possessed_by`、`transferred_in` 與事件節點；不把一次使用說成永久所有權。
- 「它依賴哪些資源？能源斷供會影響什麼？」：`affected` 從 `resource`／`system` 沿 `requires`、`depends_on`、`enables` 查級聯。
- 「不同版本的規格哪裡不同？」：先按 `version_scope` 分組，再比對 `measurements` 與 `claim`；不直接取最大值當共同正典。
- 「它在小說哪一章出現、目前狀況？」：查 `appears_in`、`located_in`、`damaged_in`、`repaired_in`、`possessed_by`，回讀章後狀態與正文。

需要批量比較時，輸出比較矩陣至少包含：版本、身分模式、能力、啟動條件、能源／消耗、限制／反制、操作資格、量測及來源，而不是只排一個戰力排名。

## 更新、衝突與級聯

1. 新來源先登錄，判斷是新增物件、版本／變體、能力／模組、規格修正、持有／操作變更、生命週期事件或衝突主張。
2. 重大改動前執行 `snapshot`；改變能力、能源、限制、核心模組、操作者或物件位置後執行 `affected --depth 3`。
3. 同一版本的規格衝突建 `claim`，由來源以 `supports`／`contradicts` 連接；不同版本建不同 measurement／edge，不以新資料刪掉舊資料。
4. 物件轉移、損傷、維修、改裝、升級與報廢建立事件節點；舊 `possessed_by`／`operated_by`／`located_in` edge 關閉 valid time，再加入新狀態。
5. 重新跑專用驗證器、Graphify `validate`、查詢 smoke test 與 export；匯出失敗只能標 WARN，不覆寫來源正典。
6. 若變更影響章節、角色選項、世界資源或規則，標 `cascade_pending`，交由 `long-form-novel-writer`／`novel-worldbuilding-architect` 同步來源檔與章綱。

## 小說與互動小說交接

### 章前

交給長篇／互動系統：物件正典與版本、目前位置、持有者／操作員、完整度／損傷、能源／彈藥／冷卻、已裝模組、可用能力與限制、角色知道的版本、可見後果、不可臨時新增的解法與下一個維修／補給時鐘。玩家只能控制自己的角色；物件與 NPC 的所有權、故障與自主決策依狀態和世界規則推演。

### 章後

只回寫已核准的物件差分：首次取得／交接、位置、持有／操作、能力使用與消耗、損傷／維修、模組裝卸、能源變化、曝光、世界／派系反應、伏筆與後續時鐘。未核准的新能力標 `[DRAFT]`／`[PROPOSAL]`，不得寫進目前正典。

## 品質檢查

- [ ] 每個物件皆有 `data_completeness` 與 `required_before_story_use`；名錄／catalog-only 不可被宣稱為完成資料庫。
- [ ] 每筆都有最低可引用卡：身分、具體用途、能力＋條件／成本／限制、運用資訊、來源層級；查不到須明寫 `UNKNOWN` 與待查項，不能只有名稱或空白陣列。
- [ ] 已產生 `REFERENCE_COVERAGE.md`，量化規格、武裝、操作者、製造者、事件等欄位的 COMPLETE／PARTIAL／UNKNOWN，並說明可安全引用邊界。
- [ ] 「盡量補齊」時先提高既有節點資訊密度，不以新增無資料的名稱節點充數。
- [ ] 頂層 classification、manifest、graph metadata 與資料庫範圍一致；缺版本時為 `AMBIGUOUS`。
- [ ] 每個特殊物主節點有 `object_category`、`object_subcategory`、`object_kind`、`identity_mode` 與版本／正典欄位。
- [ ] 同名改編、型號、個體、變體、配置、模組未被靜默合併。
- [ ] 能力都能回答條件、成本、限制、失效與反制；重要依賴不是藏在一段描述裡。
- [ ] 量測保留單位、版本、來源、原始值與計算假設；沒有假精確。
- [ ] 所有權／持有／操作／控制與 valid time 分開。
- [ ] EXTRACTED 主張可回到來源；推論、計算、提案與衝突已分層。
- [ ] 損傷／維修／升級／轉移使用事件或可追溯差分，不覆蓋歷史。
- [ ] 圖譜零 dangling edge、零重複 ID、零無效時間區間；專用 validator 與通用 validator 均通過。
- [ ] 交付包含正本、衍生檔、來源／未知／排除版本與下一個同步點。

## 與其他技能協作

- 需要設計特殊物的能力、成本、能源、制度後果或「為何沒有普及」：先載入 `novel-worldbuilding-architect`。
- 需要把特殊物放入世界資源／規則／派系／地點網：搭配 `novel-world-database-builder`，由世界資料庫引用本技能的 object ID。
- 需要角色與物件的駕駛、控制、人格、知識或行為合理性：搭配 `character-database-builder`、`novel-character-deep-digger`、`human-behavior-personality-consultant`。
- 需要章前／章後跨章同步、伏筆與改綱影響：搭配 `long-form-novel-writer` 與 `knowledge-relationship-graph`。
- 需要第二人稱自由輸入、持有物與故障狀態持續：搭配 `immersive-interactive-fiction`。

特殊物資料庫是正典檔案的衍生索引；使用者決策、定稿正文與已核准設定始終優先於圖譜或模型推論。
