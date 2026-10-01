# 實體、別名與提及索引

`entity-registry.json` 是可編輯來源；`mention-index.json` 與 heatmap 是衍生資料。

## 欄位
每個 entity：`id`、`canonical`、`type`、`aliases[]`、`context_mode`、`source_file`、`status`。

`context_mode`：
- `always`：只給極少數核心契約；即使 query 未命中也加入來源首個片段。
- `detected`：query、章綱、scene card 或本文命中 canonical／alias 時加入。
- `never`：不自動送入 context pack；仍可人工讀取。

## 規則
1. 單一漢字或過短別名預設不統計，避免普通詞誤命中。
2. 同 alias 指向多實體時列為 ambiguous，不自動合併。
3. 未登記專名只列候選，不升正典。
4. mention 次數只是可見度提示，不等於戲份、敘事重要性或真正參與事件。
5. 更名保留舊 alias 與 valid time；不可用全域字串取代歷史正文。
