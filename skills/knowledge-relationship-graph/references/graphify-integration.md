# Graphify 整合與來源

## 指定上游

- 專案：[Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)
- Python 套件：`graphifyy`
- 本次確認版本：0.9.45
- 本次確認 commit：`0738af373af9cf5c95f862cc5f3327fd96b4ea23`（2026-08-16）
- 上次技能紀錄：0.9.31／`4fe11092ccbe9f543608f140c790f68d5d83cae4`（2026-07-30）
- 本次更新重點：修正 `graphify install` 的平台版本戳記、增量重建的 `.graphify_root` 錨定判斷、Go 大小寫相撞符號 ID、以及無 `id` hyperedge 在增量重抽時造成的崩潰。
- 授權：專案標示 Apache-2.0，另包含 `LICENSE-MIT` 的 MIT 授權內容；若分發上游程式或衍生碼，保留授權與 NOTICE 要求。

本技能使用 Graphify 公開 Python API／CLI 作底層引擎，不修改上游套件：
- `cluster()`：Leiden／Louvain 社群偵測
- `label_communities_by_hub()`：無 LLM 社群命名
- `god_nodes()`：高連接樞紐
- `to_html()`：互動圖
- `to_cypher()`：Neo4j 匯入
- CLI `graphify query/path/explain/affected`

## Graphify 原始流程

```text
detect → extract → build graph → cluster → analyze → report → export
```

原始資料格式重要欄位：
- nodes：id、label、file_type、source_file、source_location
- links：source、target、relation、confidence、confidence_score、source_file、source_location
- hyperedges：nodes、relation、confidence
- confidence：EXTRACTED／INFERRED／AMBIGUOUS

## 本技能新增的領域層

Graphify 的強項是從程式碼、文件、論文、圖片與影音抽取架構關係。本技能補充：
- 通用 entity_type
- event 節點與參與角色
- relation_category／inverse／polarity
- valid time＋transaction time
- 多證據陣列與 claim 衝突
- 別名消歧
- 版本快照和級聯影響
- 小說、家族、組織、專案等領域詞彙

正本仍是 Graphify 相容 `graphify-out/graph.json`，讓上游 CLI 可直接 query/path/explain。

## 來源與標準

- [W3C PROV-O](https://www.w3.org/TR/prov-o/)：可交換、可擴充的來源證據模型；本技能採其 Entity／Activity／Agent 與 provenance 精神，但不強迫完整 OWL。
- [Neo4j — What is a knowledge graph?](https://neo4j.com/blog/knowledge-graph/what-is-knowledge-graph/)：節點、關係、properties 與 organizing principles；也強調知識圖譜可先從小範圍使用案例開始。
- [Mermaid Flowchart](https://mermaid.js.org/syntax/flowchart.html) 及 [ER Diagram](https://mermaid.js.org/syntax/entityRelationshipDiagram.html)：可讀、可攜的 Markdown 視覺化。
- Graphify 自身 extraction spec：來源位置、信心標籤、hyperedge 和增量更新。

## iSH／Alpine 說明

完整 Graphify 預設依賴大量 tree-sitter 語言套件，較適合程式碼抽取。通用關係圖譜層主要需要：
- `py3-networkx`
- `py3-numpy`
- `py3-rapidfuzz`
- `graphifyy`（本次以 `--no-deps` 安裝，因通用圖譜不需所有 AST extractor）

若日後要用 Graphify 掃描多語言程式碼，再安裝相應 tree-sitter 套件或完整 graphifyy 依賴。文件／小說的語意抽取可由當前模型產生批次 JSON，再交給本地腳本驗證與匯入，不要求額外 API key。
