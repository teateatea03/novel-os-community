# 實務者工作法：把找到資料變成經得起推翻的理解（v1.12）

這是對 v1.11 的增量協定，不是新增填表門檻。R1／R2 只為高影響問題使用；簡單身份定位不必全部展開。外部方法是借鏡，不表示本系統完成了正式社會科學研究或知道真人內心。

另按觸發讀 `practitioner-evidence-controls.md`：缺載推論→A；多來源印證或口述矛盾→B；續挖／同名→C；最終報告→D；重大反證→E。這些審查附記回指既有台帳，不建立另一套互不相通的資料庫。

## 1. 問題矩陣：保留原句脈絡與空白格

借鏡 Gale 等的 Framework Method（來源 P1）。在既有行為卡上建立小矩陣，不再重新填一次人物問卷：

| 材料／情境 ID | 時期／版本 | 核心問題／行為 | 原句及 locator | 情境與限制 | 支持哪種解釋／反例 | 缺失類別 |
|---|---|---|---|---|---|---|

- 先讀可得的完整語段或相關場景，再抽取；別讓搜尋關鍵句取代上下文。
- 相同主題才跨情境比較；時期、題材、工作角色差異仍保留。故事角色跨 continuity 不合併成一列。
- 空白格分 `not_observed`（未觀察）、`not_asked`（材料未涉及）、`unavailable`（取得受阻）、`not_applicable`（不適用），不能一律當成「沒有」。
- 保留 `other/unexpected` 放不符合舊框架的片段；不是每項新材料都必須塞回主模型。
- 摘要仍回連 artifact／頁行／timecode。抽樣不是代表性母體，不把「20篇中13篇」換算為65%人格傾向。
- 框架軟體只組織資料，不替研究者完成解釋；一張漂亮矩陣不代表理解深入。

## 2. 每個核心解釋都留下「改變軌跡」

借鏡 Gale 的 analytic memo 與 Hennink 等的 meaning-saturation trajectory（P1／P3）。先寫目前預測，再檢查新材料：

```text
問題／模型 ID：
原預期與競爭解釋：
新材料＋精確定位：
增量：新觸發／新代價／新例外／時期改變／推翻／純重複
哪些解釋變強、變弱，為什麼：
下個有區分力的材料或測試：
仍不知道、不能用於正文的部分：
```

不需要替每則貼文寫長 memo；只記會改變模型或使用限制的材料。反例若被解釋為情境差異，必須有情境證據；禁止每個反例都補一個沒來源的理由以保住原模型。

## 3. 三種停止理由分開，不靠單一飽和分數

借鏡 Guest 等的窗口／新資訊操作化與 Hennink 等區分 code/meaning saturation（P2／P3）。這裡的三軸是**本系統的改編**，不是原文已驗證的量表：

1. **發現層 discovery**：新來源家族、路由與候選是否仍增加？
2. **解釋層 explanation**：各 P0 是否仍有新條件、反例、代價、時間／版本差異？同一家族的未讀段落也可能有解釋增量。
3. **核驗層 verification**：主張是否有原文支持，矛盾、身份與高價值 defer 是否已處理？

停止備忘按問題列：窗口／資料範圍、新增什麼、剩餘盲點、下一份原文能改變什麼、停止原因（有界充分／來源受阻／時間預算／使用者限制）。能有理由停下，不等於全網窮盡；受阻不是飽和，沒有新 family 不是人物模型已成熟。

- 最後窗口不能用同一 route 反覆重查湊數，也不可跳過不利事件挑選有利窗口。
- v1.12 validator 將 event 宣告與可回溯 artifact family 合併保守檢查；這只補發現層的結構漏洞。語義新資訊與真正來源獨立性仍需查原文。
- 質性訪談研究中的 9／16–24 份或5%門檻，不可外推成社群篇數、查詢數或完整人格的固定標準。
- 不為滿足新門檻回寫舊 run、重排事件或修改歷史 source family；舊包不過時另存稽核與必要的新一輪研究。

## 4. 結論遮蔽重抽：不是看過答案再說同意

重大 P0 或有爭議主張，讓 reviewer 在未看舊 claim 結論時重抽原文。若已看過結論，誠實標一般複核；隔離 context 也不自動等於獨立專家。

```bash
python3 scripts/build_claim_review_packet.py <run-dir> \
  --claim-id C1 --output <new-review-packet.json>
```

- 工具只取中性問題與正反兩邊的 artifact locator／hash，不傳 claim text、status、假說排名或 weight_reason；同一證據去重，不標哪份支持舊結論。
- 有本地檔案時核對 hash 與路徑；未存本地的舊資料標未核驗。所有檔案只能讀，輸出拒絕覆蓋。
- reviewer 要自己開啟原文、判斷問題是否誘導、記錄最窄可支持答案與未知，**先保存重抽結果，再比對舊 claim**。
- 問題措辭、選材、檔名仍可能透露答案；不是完美盲測，也不會消除選樣偏誤。若資料集中或缺少反方，必須另找反證。
- 工具產生 packet 不代表已完成 CLAIM_AUDIT，不自動更改 status、寫入 reviews 或授予 SCENE_TESTED。

## 方法來源（本輪實際取得原文）

- **P1** Gale et al. (2013), *Using the framework method for the analysis of qualitative data in multi-disciplinary health research*. DOI 10.1186/1471-2288-13-117。定位：Stages 2–7、Discussion 的矩陣與 pitfalls。https://pmc.ncbi.nlm.nih.gov/articles/PMC3848812/
- **P2** Guest, Namey & Chen (2020), *A simple method to assess and report thematic saturation in qualitative research*. DOI 10.1371/journal.pone.0232076。定位：Base size／Run length／Discussion／Conclusion。https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0232076
- **P3** Hennink, Kaiser & Marconi (2017卷期), *Code Saturation Versus Meaning Saturation: How Many Interviews Are Enough?*. DOI 10.1177/1049732316665344。定位：Data for Assessing Meaning Saturation、Table 2、Figure 5、Discussion。https://pmc.ncbi.nlm.nih.gov/articles/PMC9359070/

完整擷取、方法差距與採用／不採用理由保留在維護者的非公開稽核紀錄，不隨本技能分發。公開技能只保留上面可獨立查核的文獻定位。
