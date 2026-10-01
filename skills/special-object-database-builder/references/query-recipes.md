# 特殊物資料庫查詢配方

以下命令以 `GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py`、`DB=<SPECIAL_OBJECT_DATABASE_ROOT>/<slug>` 為例。

## 物件總覽

```bash
python3 "$GRAPH" search --root "$DB" "鎧甲"
python3 "$GRAPH" search --root "$DB" "機體"
python3 "$GRAPH" neighbors --root "$DB" "object:<slug>"
```

## 能力與限制

沿物件的 `provides_capability`、`requires`、`consumes`、`limits`、`vulnerable_to`、`countered_by` 關係查詢；能力 edge 的 `properties` 讀取啟動條件、成本、持續時間、範圍、失效與反制。

## 版本／變體比較

先按 `properties.version_scope`、`properties.canon_scope`、`identity_mode` 分組，再比對 `measurements`、能力 edge、能源、操作資格與限制。跨版本不得把最大數值合併成共同規格。

## 生命週期與狀態

```bash
python3 "$GRAPH" timeline --root "$DB"
python3 "$GRAPH" neighbors --root "$DB" "event:<slug>"
python3 "$GRAPH" affected --root "$DB" "resource:<slug>" --depth 3
```

物件持有、操作、位置與可用性要回讀事件節點及 valid time；不能只看最新一條 edge。

## 小說交接

章前查詢物件、目前位置、持有者、操作員、能源／彈藥／冷卻、損傷、模組與角色已知版本；章後只將核准差分新增為事件／狀態，不直接覆蓋歷史。
