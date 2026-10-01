# Completion Modes｜補完模式

## 模式比較

| 模式 | 核心問題 | 可用證據 | 不可宣稱 | 預設輸出 |
|---|---|---|---|---|
| `intent-reconstruction` | 作者可能原本要怎麼寫？ | 作者大綱、手稿、本人說法、編輯／遺產資料 | 不能宣稱恢復唯一原意 | 證據排序的候選方向 |
| `textual-continuation` | 依已寫文本，下一步最合理是什麼？ | 正文、人物選擇、世界規則、伏筆、類型承諾 | 不能宣稱代表作者原意 | 正典約束續作 |
| `creative-completion` | 讀者／作者想要哪一種新結局？ | 正文精神、主題、角色與作者新指示 | 不能冒充官方或原作者版本 | 非官方替代補完 |

## 模式選擇規則

1. 有明確作者材料，但與正文衝突：可用 `intent-reconstruction`，必須同時開 `version-conflicts.md`。
2. 只有大量正文、沒有作者後續材料：以 `textual-continuation` 為預設。
3. 證據很少、版本無法核對或作者要求自由改編：使用 `creative-completion`。
4. 作者尚未決定用途或權利：模式可先 `undecided`，先做研究，不寫可發布正文。
5. 三種模式可以各自保存分支，但不可合併成一個模糊的「官方結局」。

## 可能性語言

推薦：「目前證據較支持」「若採用此假設」「這是文本約束下的合理路線」。

避免：「作者一定會」「唯一正解」「替作者完成」「這就是原本結局」。

## 交接欄位

交給長篇技能時至少帶上：`completion_mode`、`branch_id`、`canon_scope`、`confidence`、`unresolved_threads`、`rights_status`、`disclosure_status`。
