# 一致性分類與章節 Gate

Gate 輸出 `PASS`、`WARN` 或 `FAIL`，每一項附來源證據與最小修補。作者可 override；override 必須記錄理由，不靜默刪除警告。

## 分類
1. **Timeline & Plot Logic**：絕對／相對時間、時長、同時性、無因之果、因果違反、棄置情節。
2. **Characterization**：記憶、知識、技能、能力或已建立行為模式無橋樑波動。
3. **World-building & Setting**：規則、制度／社會規範、地理／空間／物流。
4. **Factual & Detail**：名稱、外貌、數字、物件、傷勢、位置。
5. **Narrative & Style**：POV 越權、語調或風格契約漂移、meta 標記殘留。

## 嚴重度
- **P0**：與 [LOCKED]/[CANON] 直接矛盾，或破壞因果；通常 FAIL。
- **P1**：證據不足、可能讀者誤解或跨章風險；WARN。
- **P2**：品質、重複或待核對；WARN。

每筆：`ID｜嚴重度／分類｜主張｜證據 A／B｜最小修補｜是否 override`。
