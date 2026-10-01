# 語言節奏工具：採用來源、實作邊界與調整原則

更新：2026-08-24。這是 `novel-human-voice-editor` 的按需參考；處理的是**中文小說的句子／段落／對話節奏**，不是情節速度，也不是 AI 作者偵測。

## 已驗證且採用的外部輪子

### 1. Writhm：先把讀者感到「不對」的節奏看出來

- 來源：[Writhm](https://writhm.io/)
- 產品作法：依句長與複雜度標色，讓作者一眼看見全頁句長分布、重複與單調區；門檻可依作品自訂。
- 本系統採用：產生句子長度條圖和 short／medium／long 三帶；**不採用**它暗示的「多變就必定更好」。場景的壓力、視角、人物聲音可合理地造成重複。

### 2. Cadence（MIT）：透明、可重跑的診斷，而非黑箱分數

- 來源：[wuisabel-gif/Cadence](https://github.com/wuisabel-gif/Cadence)（MIT；2026-08-24 核對）
- 產品作法：以句長變異（CV）及明示的結構／語彙訊號報告原因；其規則與權重公開，強調固定文字應得到固定結果。
- 本系統採用：deterministic 的句長 CV、重複句首、短句連發等「定位訊號」；**不採用**其 0–100 等級、AI／人類語氣判分、英文禁詞表或任何作者歸屬主張。

### 3. Musical Text（MIT）：編輯器內的低干擾句長標記

- 來源：[tynanpurdy/musical-text](https://github.com/tynanpurdy/musical-text)（MIT；2026-08-24 核對）
- 產品作法：實時斷句、按字數標色、允許使用者調整 short／medium／long 門檻；把句長可視化當作寫作中的鏡子。
- 本系統採用：每句的單位長度和可跳轉位置。繁中不沿用其英文單字正則：本系統以 CJK 字元加連續拉丁詞作**視覺節奏單位**。

### 4. AutoCrit／ProWritingAid：統計圖用來發現位置，不替作者決策

- [AutoCrit Pacing](https://www.autocrit.com/editing/support/pacing/)：以段落／章節長度、慢段和類型比較協助定位；需登入才能取得完整產品細節。
- [ProWritingAid Sentence Length Report](https://help.prowritingaid.com/article/49-how-to-use-the-sentence-length-report)：用句長圖指出過多長句造成單調、過多短句造成斷裂。
- 本系統採用：在 HTML 報告呈現可定位句子地圖；**不採用**類型常模、預設理想平均值或「統計偏離＝壞文」的結論。

### 5. 小說 line-editing 的人工補層：朗讀才有最終裁決

- [Fiction University：The Benefits of Reading Your Work Out Loud](http://blog.janicehardy.com/2010/03/re-write-wednesday-speaking-out.html)
- [Fiction University：Give Me a Beat: Rhythm in Dialogue](http://blog.janicehardy.com/2011/02/give-me-beat-rhythm-in-dialog.html)
- [Write With Seth：Find Your Prose Rhythm](https://writewithseth.com/finding-your-prose-rhythm-the-musical-beats-of-great-description/)
- 共同實務：朗讀可抓靜讀跳過的卡口、標點假停頓與木質對話；描述要讓讀者按可處理順序接收行動／觀察；台詞、tag、動作與 POV 內化共同形成節拍。

## Novel OS 的可執行採用法

在事件、正典、角色／世界／行為檢查完成後，於 `novel-human-voice-editor` 的 `light`、`deep` 或 `chapter-gate` 修訂中執行：

```sh
python3 scripts/prose_rhythm_audit.py \
  --file <draft.md> --format html --output <rhythm-report.html>
```

按報告只做必要的局部複核：

| 訊號 | 人工複核問題 | 可用修法 |
|---|---|---|
| `ACTION_STACK` | 讀者能否依真實順序看見所有動作？ | 拆成 2–3 個 beat，或刪掉未承擔功能的觀察 |
| `POSSIBLE_FALSE_SIMULTANEITY` | 是否把先後行動硬寫成同時？ | 調換動詞、拆句、明示先後 |
| `MONOTONE_LENGTH_RUN` | 等速是否就是本段需要的麻木／壓迫／儀式感？ | 若不是，改變資訊密度或句法，不隨機切句 |
| `REPEATED_OPENER_RUN` | 重複是刻意聲音還是生成模板？ | 改變焦點／起句；角色慣用法可保留 |
| `SHORT_BEAT_RUN` | 每個短拍是否有壓力、焦點或認知功能？ | 合併無功能短句，或讓一拍真正落地 |
| `DIALOGUE_TAG_STUTTER` | tag 是否把台詞切成停走？ | 改 tag 位置，或用 POV／有功能的動作維持說話者辨識 |

## 朗讀標記（不可由靜態工具取代）

以正常對話速度念，或用 TTS 播放；只在草稿副本上做四種標記：

- `／`：自然呼吸或轉折；
- `×`：嘴巴／耳朵卡住；
- `↻`：必須回頭才理解指涉、動作或說話者；
- `?`：標點讓語勢錯停或缺停。

先改 `×` 和 `↻`，再看統計訊號。修完後重跑 audit，確認變動是因為句法／節拍真的改了，而不是同義詞替換。

## 授權與不可採用的輪子

- `prose-rhythm-detector` 是 GPL-3.0，且重心是英／俄／法／西的文體學節律與作者研究；不拷貝或嵌入，僅作研究線索。
- `text-rhythm-analyzer` 是 MIT，但它需要作者手標劇情張力；可用於卷／場景曲線，不能取代本工具的語言層診斷。
- 所有自動訊號皆屬 `EDITORIAL_DIAGNOSIS`。不得成為正典 Gate、AI 偵測器、作者品質分數或強迫文風規格。
