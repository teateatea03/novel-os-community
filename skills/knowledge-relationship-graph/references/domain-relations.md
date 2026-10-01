# 領域關係詞彙與建模規則

圖譜可跨領域，但每個 relation 必須保持方向和語意清楚。

## 人物／家族／社會

- `parent_of`／`child_of`
- `sibling_of`（可標 undirected）
- `partner_of`／`married_to`／`ex_partner_of`
- `friend_of`／`rival_of`／`enemy_of`
- `mentor_of`／`student_of`
- `trusts`／`distrusts`／`owes`
- `supports`／`opposes`／`betrayed`

關係強度、公開／私密、互惠／單向、開始／結束時間放在 edge properties；不要把「A 愛 B」自動推成「B 愛 A」。

## 組織／權力／商業

- `member_of`／`leads`／`reports_to`
- `works_for`／`employs`
- `owns`／`controls`／`funds`
- `contracts_with`／`supplies`
- `regulates`／`investigates`／`sanctions`
- `allied_with`／`competes_with`

正式權力與實際控制可分成不同 edge。組織不是一個人；重大行動用事件節點連接決策者、執行者和受影響者。

## 事件／時間／因果

- `participated_in`（properties.role）
- `occurred_at`
- `precedes`／`follows`
- `causes`／`contributes_to`／`prevents`
- `part_of_event`
- `triggers`／`responds_to`

相關不等於因果。只因時間相鄰不可標 `causes`；證據不足用 `correlated_with` 或 AMBIGUOUS。

## 知識／證據／主張

- `knows`／`believes`／`suspects`
- `reveals_to`／`conceals_from`
- `claims`
- `supports`／`contradicts`
- `derived_from`／`cites`
- `documented_in`

主張有爭議時建立 claim 節點，不把主張直接當實體屬性。

## 地點／物件／資源

- `located_in`／`originates_from`
- `travels_to`
- `owns`／`possesses`／`transfers_to`
- `uses`／`consumes`／`produces`
- `depends_on`／`blocks_access_to`

持有、所有、控制不同；時間關係要標 valid interval。

## 專案／工作流／文件

- `depends_on`／`blocks`／`enables`
- `assigned_to`／`approved_by`
- `implements`／`supersedes`
- `references`／`generated_from`
- `affects`／`requires_update`
- `version_of`

## 小說領域

- `appears_in`（角色／物件→章／場景）
- `pov_of`（場景→角色）
- `knows`／`misbelieves`／`conceals_from`
- `foreshadows`／`resolves`
- `injures`／`heals`
- `located_in`／`travels_to`
- `bound_by_rule`／`violates_rule`
- `causes`／`motivates`

將章、卷、場景、伏筆、世界規則、角色、事件都視為節點，才能做改綱級聯和上下文檢索。

## 通用查詢

- 最短關係路徑：A 如何牽連到 B？
- 鄰居：某人直接涉及哪些人、事件、組織？
- 時間切片：某日期有哪些有效關係？
- 級聯：改動某規則／事件會影響什麼？
- 衝突：哪些來源支持互斥主張？
- 中心性：誰／哪項資源是高依賴樞紐？
- 社群：哪些節點形成自然群集？
- 孤點：哪些資料未與其他項目建立關係？
