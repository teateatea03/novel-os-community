# 品質回歸基準

回歸測試驗證工具能否抓到**已知植入問題**，不聲稱量化整體文學價值。

## Fixture 規格
每個案例放在 `benchmarks/cases/<id>/`：
- `project/`：最小小說專案。
- `expected.json`：預期 issue category／severity／關鍵詞；可有 allowed false positives。
- `notes.md`：植入問題與為何成立。

## 指標
- detector recall：預期問題有多少被找出。
- unexpected FAIL/P0：未預期的阻斷數。
- deterministic drift：同版本腳本重跑結果是否一致。
- reviewer agreement：跨模型只比較分類與證據命中，不把多數票當真相。

- 新增行為校準案例：重大節點有 Lock 通過、缺 Lock 阻斷、篡改 hash 阻斷、無樣本精細百分比阻斷、序位／寬區間通過、章後 Resolution 可追加且不可覆寫。

先建立時間、知識、物件／數量、世界規則、POV/meta、正常無錯六類最小案例。任何門禁規則新增前先加 fixture；沒有案例證明的規則只能是 WARN。
