# 世界資料庫查詢指南

## 建立／匯入前分類檢查

正式執行 `init` 或 `import` 前，批次檔頂層必須有 `classification`，且包含：

```text
subject_category, subject_subcategory, subject_kind, source_medium,
canon_scope, version_scope, franchise, genre,
classification_basis, classification_confidence
```

`version_scope` 必須指向具體作品／版本，不得只填系列名；分類未定時使用 `classification_confidence: AMBIGUOUS` 並停在提案／待確認階段。匯入後，世界根節點 `properties`、manifest 與 catalog 必須複製同一份分類契約，供分類篩選與版本消歧。

先執行分類驗證器，再執行 Graphify 匯入：

```bash
python3 "$SKILL_ROOT/scripts/validate_world_classification.py" --batch "$BATCH"
python3 "$GRAPH" init --root "$DB" --title "世界資料庫"
python3 "$GRAPH" import --root "$DB" --file "$BATCH" --strict
python3 "$GRAPH" validate --root "$DB"
python3 "$GRAPH" export --root "$DB" --graphml --cypher
```

### 分類與版本索引

分類契約應同時保存於資料庫根圖的 `graph.classification`、世界根節點 `properties`、`database-manifest.json` 與 `<WORLD_DATABASE_ROOT>/catalog.json`。catalog 項目至少保留：

```text
subject_category, subject_subcategory, subject_kind,
canon_scope, version_scope, franchise, genre
```

查詢世界時先按分類與版本篩選，再讀節點與關係；同系列不同媒體不得只靠標題合併。

```bash
python3 "$GRAPH" search --root "$DB" "關鍵詞"
python3 "$GRAPH" neighbors --root "$DB" "rule:example"
python3 "$GRAPH" path --root "$DB" "faction:a" "resource:water"
python3 "$GRAPH" affected --root "$DB" "rule:example" --depth 3
python3 "$GRAPH" timeline --root "$DB"
```

## 更新
```bash
python3 "$GRAPH" snapshot --root "$DB"
python3 "$GRAPH" close-edge --root "$DB" --id edge:old --status superseded --valid-to 2026-01-01
python3 "$GRAPH" validate --root "$DB"
```

圖譜只保存結構與證據；`world-bible.md`、`world-rules.md` 和定稿正文仍是正典。
