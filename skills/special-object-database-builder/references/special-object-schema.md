# 特殊物分類與欄位契約

特殊物資料庫採用 `minis.special-object.v1`。資料庫級 `classification` 必須和批次、`graph.classification`、manifest 一致；每個特殊物主節點另保存 object-level 分類。

## 資料庫級 classification

必填欄位：

```json
{
  "subject_category": "real|novel|anime|film|game|comic|stage|myth|original|other",
  "subject_subcategory": "anime_gadget|film_powered_armor|anime_mecha|...",
  "subject_kind": "fictional_object_catalog|real_technology_catalog|original_object_catalog|cross_media_catalog|unknown",
  "source_medium": ["manga", "tv_anime", "official_guide"],
  "canon_scope": "manga_canon|anime_canon|film_canon|game_canon|cross_adaptation|user_created|unknown",
  "version_scope": "具體作品／媒體／宇宙／季別／版本；不得只寫系列名",
  "franchise": "作品或系列；無系列可為 null",
  "genre": ["mecha", "science_fiction"],
  "classification_basis": "可回溯的分類理由",
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS"
}
```

## 物件主節點 properties

`entity_type: object` 且 `special_object_record: true` 時，至少需要：

```json
{
  "special_object_record": true,
  "object_category": "gadget|powered_armor|mecha|mobile_suit|vehicle|weapon|tool|artifact|device|robot|sentient_machine|equipment_system|other",
  "object_subcategory": "細分類",
  "object_kind": "fictional_object|real_technology|original_object|hybrid|unknown",
  "identity_mode": "singleton|model_line|variant|loadout|component|copy|prototype|unknown",
  "version_scope": "具體版本",
  "canon_scope": "anime_canon",
  "franchise": "作品／系列",
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS",
  "canon_status": "[CANON]",
  "epistemic_layer": "[TRUTH]",
  "provenance_class": "EXTRACTED"
}
```

## 物件分類提示

- `gadget`：可攜式或單一用途道具、裝置。
- `powered_armor`：穿戴式動力鎧甲或外骨骼。
- `mecha`／`mobile_suit`：大型機器人、機動兵器、機體。
- `vehicle`：交通、戰鬥或宇宙載具。
- `weapon`：主要功能是攻擊或防禦的武器。
- `artifact`：具有特殊規則、歷史或超自然性質的物件。
- `sentient_machine`：具有自主意識；人格與角色資料另建。

## 規格 measurements

每一筆可比較量測保存：

```json
{
  "metric": "重量",
  "value": 63.0,
  "unit": "kg",
  "qualifier": "裝備後／設定值",
  "version_scope": "具體版本",
  "source": "設定集頁碼或 URL",
  "provenance_class": "EXTRACTED|CALCULATED|AMBIGUOUS",
  "assumptions": []
}
```

`CALCULATED` 必須有原始值與計算假設；衝突數值不能互相覆蓋。

## 生命週期事件

推薦事件類型：`designed`、`manufactured`、`activated`、`assigned`、`deployed`、`damaged`、`repaired`、`modified`、`upgraded`、`transferred`、`stolen`、`lost`、`destroyed`、`retired`。

物件狀態要能回答：當時在哪裡、誰持有、誰操作、是否可用、能源／彈藥／冷卻、裝了哪些模組、有哪些已知損傷。不要用一個 current_status 取代歷史事件。

## 版本規則

原作漫畫、電視動畫、動畫電影、真人電影、遊戲、重製與跨宇宙版本分開。跨版本比較可在同一 catalog 中並列，但每個物件節點必須保留自己的 `version_scope` 與 `canon_scope`；不能因同名、同外觀或同型號自動合併。
