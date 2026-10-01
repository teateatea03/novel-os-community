---
name: unfinished-novel-completion
version: 1.1.0
description: 當使用者要求補完、續寫、復原、推演或研究斷更／太監／未完成小說、作者中止的長篇、作者去世後未完手稿、讀者替代結局、AI續寫未完作品，或需要判斷原作者意圖、文本正典、版本衝突、補完可行性、版權倫理與非官方發布方式時使用。將未完成作品視為有來源證據、版本、不確定性、分支與權利邊界的研究型創作專案，再交接給 Novel OS 長篇寫作；不把推測冒充原作者意圖，也不把斷更視為放棄著作權。
---

# Unfinished Novel Completion

把「斷更小說補完」與普通續章分開處理。目標不是聲稱恢復作者腦中的唯一結局，而是建立可追溯、可分支、可修正的三種結果：原作者意圖重建、正典約束續作、創作性替代補完。

## 核心界線

1. **文本正典 ≠ 作者意圖 ≠ 讀者理論 ≠ 補完提案**。每個主張都要標示來源層級、信心與範圍。
2. 原作者筆記、訪談或遺產資料也可能是早期版本；若與已發表正文衝突，保存衝突，不靜默選邊。
3. 「最可能」只表示目前證據下的條件式推演；不得寫成「作者一定會如此結局」。
4. 斷更、失聯或作者死亡不等於作品進入公有領域。公開分享、改作與商業利用另做權利評估。
5. 原作作者仍在世時，不擅自把作品包裝成官方續作；有明確禁止二創或要求撤下時，尊重其要求。
6. 可私下推演不代表可以公開發布或營利；`rights-and-publication.md` 必須在交付前更新。
7. AI 產出、人工修改、研究資料與最終正文都要可追溯；不把模型生成當成作者證據。

## 三種補完模式

- **`intent-reconstruction`｜原作者意圖重建**：只有在有作者大綱、手稿、本人說法、編輯／遺產資料或多重文本證據時使用。輸出「證據支持的可能方向」，保留替代解釋。
- **`textual-continuation`｜正典約束續作**：依已寫正文、人物選擇、世界規則、伏筆與類型承諾推演；不宣稱知道作者原意。這是沒有作者後續資料時的預設正式模式。
- **`creative-completion`｜創作性替代補完**：證據不足、版本衝突無法消解，或作者明確要自由結局時使用。標為非官方、依原作材料／精神發展的創作版本。

模式未經作者選擇前保持 `undecided`，不得把 `PROPOSAL` 升為 `CANON`。

## 標籤與證據層

### 作品狀態

沿用 `[LOCKED]`／`[CANON]`／`[PLAN]`／`[DRAFT]`／`[PROPOSAL]`／`[UNKNOWN]`，另加：

- `[TEXT-CANON]`：已發表或作者已定稿的正文／版本。
- `[AUTHOR-NOTE]`：作者筆記、提綱、手稿中的方向。
- `[AUTHOR-STATEMENT]`：作者本人可核對的公開說法。
- `[EDITORIAL]`：編輯、出版方、遺產管理人或授權方資料。
- `[ADAPTATION]`：改編版本，不自動回填原作正典。
- `[FAN-THEORY]`：讀者／社群假說，只作線索。
- `[INFERENCE]`：由文本與脈絡推導的假說。
- `[PROPOSAL]`：補完者新增的創作方案。
- `[CONFLICTED]`：證據互相衝突。
- `[UNKNOWN]`：目前不可合理判定。

### 信心

`HIGH` 只表示來源明確且範圍相符，不表示原作者必然會採用；`MEDIUM` 表示有多項間接支持；`LOW` 只能當候選假說。競爭假說不得因「看起來有戲」提高信心。

## 標準工作流

### 1. Intake

先建立 `completion-brief.md`、`source-manifest.json`、`rights-and-publication.md` 與 `completion-provenance.md`。記錄作品、作者、斷更點、來源範圍、用途、權利狀態與模式；不確定就填 `UNKNOWN`，不要先寫結局。

### 2. 來源與版本

使用 `scripts/source_ingest.py` 登記使用者提供或公開可核對的來源，保存 SHA-256、版本、章節範圍、取得時間與完整度。原文、連載版、出版版、預告、訪談、粉絲整理與改編分開；可用 `compare_source_versions.py` 產生差異報告。

### 3. 正典與意圖分離

先整理 `textual-canon.md`，再填 `evidence-ledger.md`、`author-intent-ledger.md`、`version-conflicts.md`。正文說明「故事已發生什麼」；意圖帳本只說「證據支持作者可能想做什麼」。把粉絲理論列為假說，不當作作者資料。

### 4. 可行性評估

使用 `scripts/feasibility_report.py --root <project> --write` 評估來源完整度、結構完整度、伏筆回收度、人物／世界穩定度、意圖可推測度、版本衝突與權利風險。使用 `scripts/sync_graph.py --root <project>` 把來源、主張、版本／分支與專案節點同步到既有 Graphify 圖譜。至少分別評估三種模式，不用一個總分掩蓋「原意不可知但合理續作可行」的差異。

### 5. 建立分支

在 `hypothesis-ledger.md` 與 `unfinished-thread-ledger.md` 中保存 A／B／C 分支。每個分支都要列證據、假設、反證、必要橋樑、伏筆處理、人物弧影響與分歧點。用 `scripts/branch_diff.py` 比較分支，不把低機率分支刪掉；作者選定前保持 `[PROPOSAL]`。

### 6. 交接長篇寫作

作者選定模式與分支後，將 `textual-canon.md`、`evidence-ledger.md`、`author-intent-ledger.md`、`unfinished-thread-ledger.md`、`feasibility-report.md` 和權利狀態交給 `long-form-novel-writer`。每章仍遵循世界觀、行為、風格、圖譜與讀者資訊帳本；正文新增內容標為該補完分支的 `[DRAFT]`，核准後才成為專案 `[CANON]`。

### 7. 補完 Gate 與溯源

在分析、分支、正文與發布前執行 `scripts/completion_gate.py --root <project> --phase ...`；使用 `scripts/feasibility_report.py` 生成可行性報告，完成證據整理後使用 `scripts/sync_graph.py --root <project>` 把來源、主張與分支同步到既有 Graphify 圖譜。圖譜是衍生索引，不反向覆蓋正文正典。它檢查必要檔案、JSON、模式、證據／意圖分層、未完成線、權利狀態、AI 揭露與過度宣稱。`provenance_report.py` 彙整 AI 草稿、人類決策、修改與最終正文來源。

## 跨技能路由

- `long-form-novel-writer`：章節計畫、正文、狀態更新、改綱級聯與章後 gate。
- `novel-character-deep-digger`：既有角色與作者公開資料；只把可核對材料放入證據層。
- `human-behavior-personality-consultant`：檢查「作者可能安排的行為」是否有角色與情境橋樑。
- `novel-worldbuilding-architect`：檢查補完方向是否符合資源、制度、物流與世界規則。
- `novel-style-craft-director`：提煉可泛化工藝，不直接複製作者聲紋或原文。
- `knowledge-relationship-graph`：把來源、主張、版本、伏筆、人物與分支建立可追溯子圖。
- `novel-human-voice-editor`：只在內容與正典鎖定後做文字層修訂，不掩飾補完性質。

## 交付格式

每次交付至少說明：

1. 補完模式與分支 ID；
2. 原作者意圖可推測度與正典續作可行性，分開評估；
3. 使用的來源與主要未知／衝突；
4. 哪些是 `[TEXT-CANON]`、`[INFERENCE]`、`[PROPOSAL]`；
5. 已執行與未執行的 Gate；
6. 是否非官方、AI 是否參與，以及目前發布／權利限制。

minis_url: <MINIS_RESOURCE_URL>
