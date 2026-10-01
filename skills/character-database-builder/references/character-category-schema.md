# 角色分類標準

角色資料庫採用 `minis.character-profile.v2` 分類契約；完整規範見：
`../novel-character-deep-digger/references/character-category-taxonomy.md`

## 主分類

- `real`：真實／真人（含歷史人物）
- `novel`：小說角色
- `anime`：動漫／漫畫／動畫角色
- `film`：電影版本或電影原創角色
- `other`：遊戲、舞台、神話、原創、跨媒體或尚未消歧

## 角色主節點必填欄位

每個 `entity_type: person` 的角色主節點，`properties` 必須包含：

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
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS"
}
```

## 名稱本地化欄位

若角色原始名稱含非中文文字或中外文混合，主節點 `properties` 必須包含：

```json
{
  "name_zh": "官方中文譯名；若無官方譯名則依原文讀音的台灣繁中音譯",
  "name_zh_language": "zh-Hant-TW",
  "name_zh_provenance": "OFFICIAL_ZH|MODEL_TRANSLITERATION_ASSISTED|UNKNOWN",
  "name_zh_source_label": "原始 label"
}
```

規則：官方中文譯名優先；查不到官方中文譯名時採音譯，不自行意譯。只有原文文字或讀音無法可靠判讀時才填 `UNKNOWN`。`label`、ID 與 `aliases` 保留原樣。

## 建檔規則

1. 一開始先判斷主分類；分類不明先用 `other` + `unknown` + `AMBIGUOUS`，不可硬猜。
2. 使用者指定的版本優先。例如「電影版角色」歸 `film`；「漫畫原作角色」歸 `anime`／`manga_character`。
3. 原作與改編版不得無聲合併；在 `version_scope`、`canon_scope` 或版本節點保存差異。
4. 真人原型與小說化／動漫化角色必須分開建立，再用 `derived_from`／`inspired_by` 連接。
5. 列表與查詢結果按 `subject_category` 分組，並顯示次分類、作品／系列與版本範圍。

## 分類研究邊界

- `real`：只研究公開可查證資料，不推定未公開私生活或診斷。
- `novel`：以文字正典和作者資料為主，區分敘事者、角色認知與情節事實。
- `anime`：漫畫、動畫、動畫原創、季別、重製與劇場版分開。
- `film`：只把電影版本設定歸角色，不把演員本人資料混入。
- `other`：記錄媒介和待查原因，完成消歧後再遷移分類。
