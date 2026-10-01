# 角色主體分類標準

版本：`minis.character-profile.v2`

這份分類標準供 `novel-character-deep-digger`、`character-database-builder`、Novel OS 與長篇寫作共用。分類描述的是「研究對象的主體來源／現實性」，不是角色在作品中的職業。

## 一、必填主分類

`subject_category` 只能使用以下五種值：

| 值 | 中文 | 判定範圍 |
|---|---|---|
| `real` | 真實／真人 | 現實中的公開人物、歷史人物、創作者、運動員、政治人物、Coser、演員等。歷史人物也歸此類，不因已逝而變成虛構角色。 |
| `novel` | 小說 | 主要正典來自小說、網路小說、輕小說、散文敘事或其他文字虛構作品的角色。 |
| `anime` | 動漫 | 主要正典來自漫畫、動畫、動漫影集、動畫原創、日漫／韓漫／中國動畫等。以漫畫與動畫的版本差異放在 `version_scope`，不混成單一事實。 |
| `film` | 電影 | 研究對象是電影版本、電影原創角色，或使用者明確指定的真人／動畫電影版本。即使電影改編自小說或動漫，只要本次研究鎖定電影版本，就歸 `film`。 |
| `other` | 其他 | 遊戲、舞台劇、廣播劇、神話傳說、原創角色、跨媒體無法判定、未完成消歧等。應用 `subject_subcategory` 說明原因，不把未知硬猜成小說或動漫。 |

## 二、必填次分類

`subject_subcategory` 使用下列建議值；若不適用可用 `unknown`，但要記錄原因：

- `real_public_figure`：現代公開真人
- `real_historical_person`：歷史人物
- `novel_character`、`web_novel_character`、`light_novel_character`
- `manga_character`、`anime_tv_character`、`anime_film_character`、`donghua_character`、`animation_character`
- `film_live_action_character`、`film_animated_character`、`film_original_character`、`film_adaptation_character`
- `game_character`、`stage_character`、`myth_folklore_character`、`original_character`、`mixed_media_character`、`unknown`

## 三、必填身份與正典欄位

所有角色主節點（通常是 `entity_type: person`）都要有：

```json
{
  "subject_category": "real|novel|anime|film|other",
  "subject_subcategory": "...",
  "subject_kind": "real_person|historical_person|fictional_character|original_character|unknown",
  "source_medium": ["..."],
  "canon_scope": "public_record|novel_canon|anime_canon|film_canon|cross_adaptation|user_created|unknown",
  "version_scope": "研究採用的作品／動畫季／電影／時間版本",
  "franchise": "作品系列；真人可為 null",
  "classification_basis": "為何歸入此類",
  "classification_confidence": "EXTRACTED|INFERRED|AMBIGUOUS"
}
```

## 四、版本與改編規則

1. **使用者明確指定版本優先**：例如「某角色的電影版」歸 `film`；「某角色漫畫原作」歸 `anime` 並以 `manga_character` 作次分類。
2. **未指定版本採主要正典來源**：原作小說角色即使有動畫，預設歸 `novel`；原作漫畫角色即使有電影，預設歸 `anime`。
3. **同一角色的不同版本不可無聲合併**：可共用別名，但要在 `version_scope`、`canon_scope` 或獨立版本節點保存差異。
4. **跨媒體研究**：主分類採本次研究的主版本，`source_medium` 填完整媒介，`canon_scope` 用 `cross_adaptation`，並列出版本衝突。
5. **真人原型與小說化角色分離**：真人歸 `real`；由真人改寫出的虛構角色應另建 `fictional_character` 節點，以 `derived_from` 或 `inspired_by` 連接，不能覆寫真人節點。
6. **分類不確定時**：先用 `other`／`unknown`／`AMBIGUOUS`，保留待查問題；完成來源確認後再 snapshot 更新，不直接猜測。

## 五、不同類別的研究邊界

- `real`：只用公開可查證資料，不推定未公開私生活、疾病、創傷、收入、合約或心理診斷。
- `novel`：以文字正典、作者資料與版本為主；區分敘事者說法、角色認知與客觀情節。
- `anime`：分開漫畫／動畫／動畫原創、季別、重製與劇場版；粉絲推測不升格為正典。
- `film`：記錄電影中的明示設定、鏡頭可見行為、劇本／官方設定與改編差異；不把演員本人資料混入角色。
- `other`：先確認媒介與權利／正典狀態，再決定是否轉入其他主類別。

## 六、查詢與顯示

資料庫列表以 `subject_category` 分組；列表顯示中文名稱、英文值、次分類、作品／系列與資料庫 slug。任何回答「有哪些角色」時，不能只按資料夾排序，也要顯示主分類與版本範圍。
