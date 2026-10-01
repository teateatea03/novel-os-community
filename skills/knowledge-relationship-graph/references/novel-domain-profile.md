# 小說圖譜領域設定

## 節點類型

- project：小說專案
- document：故事聖經、世界聖經、風格表、角色檔、章節正文
- person：角色
- group／organization：派系、家族、機構
- place：地點
- event：情節事件、歷史事件
- object：關鍵物件、特殊物、武器、信件、證據；若是道具／鎧甲／機體／載具／裝置，另由 `special-object-database-builder` 保存版本與生命週期
- claim：真相、官方說法、群體信念、流言
- concept／system：世界規則、科技、魔法、法律、文化規範
- task／decision：待決作者問題、改綱決策
- resource：金錢、能源、稀缺資源

卷、章、場景可使用 document 節點並加 `properties.level=volume|chapter|scene`。

## 必要關係

### 結構
- project `contains` volume／chapter／document
- volume `contains` chapter
- chapter `contains` scene
- scene `precedes` scene

### 人物與場景
- character `appears_in` scene／chapter
- scene `pov_of` character
- character `participated_in` event（properties.role）
- event `occurred_at` place

### 人物關係
- `parent_of`／`partner_of`／`mentor_of`／`friend_of`／`rival_of`
- `trusts`／`distrusts`／`owes`／`betrayed`
- `member_of`／`leads`／`controls`

所有關係可有 valid_from／valid_to 和公開／私密程度。

### 資訊
- character `knows` claim
- character `believes`／`misbelieves` claim
- character `conceals_from` character（properties.claim_id）
- evidence／event `supports`／`contradicts` claim
- claim `revealed_in` scene

`[TRUTH]／[OFFICIAL]／[BELIEF]／[RUMOR]／[KNOWN]` 可放 claim properties，不把不同版本覆蓋成同一條文字。

### 因果與動機
- event `causes`／`contributes_to` event
- event／claim `motivates` character
- scene `fulfills`／`violates` plan anchor
- event `changes_state_of` character／place／faction

### 伏筆
- clue／scene `foreshadows` event／claim
- scene `resolves` foreshadow
- foreshadow `depends_on` clue／event

### 世界與資源
- character／faction `bound_by_rule` system
- event／character `violates_rule` system
- system `depends_on` resource
- faction `controls` resource／place
- object `located_in` place；特殊物狀態另查 `possessed_by`／`operated_by`／`equipped_with`／`damaged_in`／`repaired_in`／`upgraded_in`／`transferred_in`
- character `possesses` object
- event `transfers` object（角色用 participant role 表達）

## 正典同步規則

1. 定稿正文和 [CANON]／[LOCKED] 文件是主要來源；圖譜是衍生索引。
2. [PLAN]／[DRAFT] 節點和關係保留 status，不作目前有效事實回答，除非查詢明確要求規劃層。
3. 章後先更新故事帳本，再回寫圖譜；不能用模型抽取結果反向覆蓋正典。
4. 每條重要 edge 附 `source_file`、`source_location`／章節和短證據。
5. 修改定稿前 snapshot；改綱後 `affected`，標出 stale／cascade_pending。
6. 舊關係結束時關閉 valid time，不刪除。例如信任破裂、物件轉移、派系更換領袖。
7. 角色出場、POV、位置、知識、物件和傷勢等可從圖譜建立 context pack，但仍與 current-state／timeline 交叉驗證。

## 章前查詢

- POV 角色鄰居與深度 1–2 子圖
- 當前地點、派系、物件和活躍事件
- 角色 knows／believes／misbelieves
- 未回收 foreshadows 和依賴
- 世界規則的 bound_by_rule／depends_on
- 本章計畫節點與前置事件

## 章後回寫

- 新實體和別名
- 出場、POV、地點和事件參與
- 新關係／關係強度或狀態變化
- 物件、特殊物、資源、職位與控制權轉移
- 角色知識和讀者揭露
- 因果、伏筆與回收
- 世界規則使用／違反／例外
- 一階、二階公共後果

## 一致性查詢

- 已死亡／離開角色是否在非回憶場景再次 appears_in？
- 角色是否 knows 尚未 revealed／learned 的 claim？
- 同一時間人物是否位於不相容地點？
- 物件是否同時 possessed by 多人而非共享物？
- 技能／世界規則是否有無前因波動？
- 伏筆是否長期沒有後繼或回收？
- 改動某規則、事件、人物身分會 affected 哪些章節？
