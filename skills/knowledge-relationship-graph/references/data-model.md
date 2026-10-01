# 通用關係圖譜資料模型

本模型是 Graphify 相容的 property graph 擴充。`graphify-out/graph.json` 是正本；節點使用 `nodes`，關係使用 `links`，多人／多物件共同事件可使用事件節點或 `hyperedges`。

## 角色分類欄位

角色主節點（`entity_type: person` 且 `properties.character_record: true`）除通用欄位外，必須保存：

- `subject_category`：`real`／`novel`／`anime`／`film`／`other`
- `subject_subcategory`、`subject_kind`
- `source_medium`、`canon_scope`、`version_scope`、`franchise`
- `classification_basis`、`classification_confidence`

分類說明：`real` 含歷史人物；`novel` 是小說角色；`anime` 是漫畫／動畫／動漫角色；`film` 是電影版本／電影原創角色；`other` 是遊戲、舞台、神話、原創、跨媒體或尚未消歧。分類描述對象來源，不能取代 `EXTRACTED`／`INFERRED`／`AMBIGUOUS` 證據強度。版本改變先 snapshot；真人原型與改編角色分開建檔。

## 節點

必要：
- `id`：穩定 canonical ID，如 `person:lin-mei`、`event:2026-merger`
- `label`：人類可讀的原始／正典名稱，不能因本地化覆蓋
- `entity_type`：person／organization／group／place／event／object／document／concept／project／task／decision／claim／resource／system／role／other

建議：
- `aliases`：別名、舊稱、翻譯名、代號
- `properties`：領域屬性，不把應獨立成節點的實體塞進屬性
- 名稱含非中文文字時，`properties` 必須保存 `name_zh`、`name_zh_language: "zh-Hant-TW"`、`name_zh_provenance` 與 `name_zh_source_label`；原始 `label`、ID 與 `aliases` 保留不改。翻譯優先序是官方中文譯名，其次是依原文可靠讀音的台灣繁中音譯；不得自行意譯。`name_zh` 為查詢輔助，不等同官方譯名；只有原文文字或讀音也無法判讀才填 `UNKNOWN`。
- `status`：active／planned／disputed／superseded／deleted
- `valid_from`／`valid_to`：此實體狀態在領域世界有效的時間
- `confidence`／`confidence_score`
- `source_file`／`source_location`／`source_url`／`evidence`
- `captured_at`：系統何時取得

## 關係

必要：
- `id`／`key`
- `source`／`target`
- `relation`：小寫 snake_case 動詞，如 `works_for`、`parent_of`、`causes`

建議：
- `relation_category`：kinship／social／authority／membership／ownership／dependency／causal／temporal／spatial／knowledge／conflict／support／workflow／general
- `inverse_relation`
- `directed`
- `polarity`：positive／negative／neutral／mixed
- `properties`：角色、強度、數量、條件
- `status`
- `valid_from`／`valid_to`：事實何時成立（valid time）
- `transaction_from`／`transaction_to`：系統何時知道／何時被取代（transaction time）
- `confidence`：EXTRACTED／INFERRED／AMBIGUOUS
- `confidence_score`：0–1
- `evidence`：每條證據的來源、位置、網址、短引文、擷取時間

關係不可只用無語義的 `related_to`，除非目前真的無法分類；不確定要標 AMBIGUOUS，而非裝作確定。

## 事件節點

涉及三方以上、角色不同、時間地點和後果的事件，使用事件節點：

```text
Person A --participated_in {role:buyer}--> Event
Person B --participated_in {role:seller}--> Event
Object X --subject_of--> Event
Event --occurred_at--> Place
Event --causes--> Event Y
```

這比把所有參與者兩兩相連更準確。事件可保存 `event_time`／`event_end`、狀態、條件和證據。

## Hyperedge

Graphify 支援 hyperedges。只在「群體共同形成某事」且事件節點不自然時使用，例如多個概念共同構成一個框架。需要時間、角色、後果或可查詢屬性時，優先事件節點。

## 證據與來源

參考 Graphify 的 EXTRACTED／INFERRED／AMBIGUOUS 與 W3C PROV 的 provenance 精神：
- EXTRACTED：來源明示；分數預設 1.0。
- INFERRED：合理推論；列推論鏈或依據。
- AMBIGUOUS：來源歧義／互相衝突；保留待審。

不同來源可支持互斥主張。不要覆蓋；建立 `claim` 節點、`supports`／`contradicts` 關係，或讓關係標 disputed。

## 雙時間

- Valid time：關係在故事／現實中何時為真。
- Transaction time：系統何時得知、何時更正。

舊關係失效時標 `superseded` 並關閉時間，不直接刪除。這讓圖譜能回答「當時真相是什麼」與「我們當時以為什麼」。

## 別名與消歧

- 同一實體多名稱：合併到 canonical node，名稱放 aliases。
- 同名不同實體：使用不同 ID，不共用模糊 alias；加 disambiguation 屬性。
- 自動抽取先標候選，不可因字串相似就直接合併。

## 版本與級聯

修改節點／關係前先 snapshot。刪除、取代或改綱時執行 `affected`：
- `depends_on`
- `causes`
- `contains`
- `member_of`
- `knows`
- `located_in`
- `appears_in`
- `supports`／`contradicts`

將受影響節點標 `stale`／`cascade_pending`，由使用者或上層技能確認後更新。
