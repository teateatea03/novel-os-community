# Character Research Evidence Run v2

本規範把角色研究從「完成一張 manifest」改成「可重播、可挑戰的研究執行」。適用新 R1／R2；舊 `minis.character-research-manifest.v1` 只保留 legacy provenance，不自動升級。

## 1. 為何 v1 不夠

v1 能要求 exact query、來源面與 artifact，卻仍可能被事後補表欺騙：手填五個 `searched`、三條近義查詢與一句飽和理由，就能假裝完成。v2 不再相信自述欄位；coverage、query diversity、claim closure 與 saturation 都由實際 event／candidate／artifact／review 關聯計算。

## 2. 專業實務轉譯

- **GIJN／SVT 三 checkpoint**：啟動時挑戰假說；中段檢查遺漏與黑白化；交付前逐主張查核。角色研究對應 `START_CHALLENGE → MIDPOINT_REVIEW → CLAIM_AUDIT`。
- **PRISMA-S／PRESS**：保存每個平台原樣查詢、日期、filters、raw hit count、dedup 方法；用 known items 測試主查詢，而非只評語法好看。
- **Genealogical Proof Standard**：合理窮盡、完整引用、證據關聯、衝突解決、書面結論；負向證據必須先證明「該紀錄理應存在且該資料集覆蓋相關時空」。
- **AHA／檔案研究者**：查前讀 finding aid 並排優先級；查中以一致標籤連接照片與 box/folder；每日回顧、備份、補洞；線上目錄不等於完整館藏。
- **Bellingcat／Berkeley Protocol／WITNESS**：識別→蒐集→處理→審閱→分析→產出；原始檔與衍生檔分離、擷取即 hash、保存 provenance／處理步驟／限制；高風險研究先做安全與最小化評估。
- **專業 fact-checker lateral reading**：不要在陌生網站內垂直讀到相信；先離站查作者、機構、資助、聲譽與原始主張。
- **OCCRP／Aleph 類 casefile**：以人物、組織、事件、識別碼為 pivot；原始資料、候選紀錄、實體關係與分析分層，不把全文共現直接升格為關係。
- **Hunchly 類 capture**：瀏覽與擷取同步留下 URL、時間、hash、note；但 hash 只能證明「擷取後未變」，不能證明擷取前內容真實。
- **研究資料 provenance**：raw immutable、derived 可重建；每次 OCR、轉寫、翻譯、裁切、摘要都記 input hash、工具／版本、參數與人工校對。

## 3. Evidence run 目錄

```text
research-run/
├── protocol.json                 # 搜尋前鎖定，修改須新 revision
├── events.jsonl                  # append-only hash chain
├── candidates.jsonl              # 每筆候選 include/exclude/defer
├── artifacts/
│   ├── raw/                      # 原始擷取，不覆寫
│   └── derived/                  # OCR/字幕/翻譯/摘要
├── artifacts.jsonl               # URL、hash、locator、衍生鏈
├── claims.jsonl                  # 主張—證據—反證—假說
├── reviews.jsonl                 # start/midpoint/claim audit
├── run-summary.json              # 由工具計算，不手填 coverage/saturation
└── report.md
```

## 4. 研究前契約 `protocol.json`

最低欄位：

```json
{
  "schema":"minis.character-research-run.v2",
  "run_id":"...",
  "subject":{"label":"...","category":"real|novel|anime|film|other","identity_keys":[]},
  "depth":"R0|R1|R2",
  "started_at":"ISO-8601",
  "questions":[{
    "id":"Q1","text":"中性、可回答問題","priority":"P0|P1|P2",
    "decision_use":"答案會改變哪個場景／版本／能力／關係",
    "candidate_answers":["H1","H2","UNKNOWN"],
    "required_source_roles":["primary","independent_secondary"],
    "negative_evidence_expectation":"若不存在，應在哪個完整資料集看到什麼"
  }],
  "identity_resolution":{"aliases":[],"language_variants":[],"disambiguators":[],"excluded_homonyms":[],"identity_keys":[]},
  "source_plan":[{"id":"SP1","question_ids":["Q1"],"surface":"official|canon|archive|library|scholarly|news|adjacent|web_archive|av|public_record","method":"query|browse|citation|contact|request|inspection","priority":"must|should|could","expected_yield":"..."}],
  "benchmark_items":[{"id":"B1","question_ids":["Q1"],"locator":"URL/ID","holdout":true}],
  "risks":{"subject_harm":"low|medium|high","investigator_risk":"low|medium|high","sensitive_data":[],"mitigations":[]},
  "stop_policy":{"min_distinct_routes":3,"no_new_family_window":3,"p0_must_close":true}
}
```

`protocol.json` 必須在主要搜尋前建立。修訂時保留舊版 hash，事件記 `PROTOCOL_REVISION` 與理由；不得直接覆寫後假裝一開始就知道。

## 5. Append-only `events.jsonl`

每個實際動作一列：

```json
{"event_id":"E0001","type":"QUERY|BROWSE|CITATION_BACKWARD|CITATION_FORWARD|PIVOT|CONTACT|ARCHIVE_REQUEST|CAPTURE|TRANSFORM|REVIEW","question_ids":["Q1"],"plan_id":"SP1","started_at":"...","ended_at":"...","actor":"agent|human|tool","platform":"Google Web","input":{"exact_query":"...","filters":{}},"result":{"status":"success|zero|noise|blocked|error","raw_hit_count":null,"new_candidate_ids":["K1"]},"tool":{"name":"...","version":"..."},"prev_hash":"...","event_hash":"..."}
```

事件 hash 以移除 `event_hash` 後的 canonical JSON 計算 SHA-256；第一筆 `prev_hash` 為 64 個 `0`。`searched` coverage 只能由成功／zero／noise 的實際事件推導。Blocked/error 不算已查完，但可證明嘗試過。

## 6. Candidate ledger：結果與證據之間不能跳級

搜尋結果、腳註、同框人物、新聞、影片先進 `candidates.jsonl`：

```json
{"candidate_id":"K1","discovered_by":"E0001","canonical_locator":"...","title":"...","creator":"...","published_at":"...","source_role":"primary|first_person|contemporaneous|independent_secondary|tertiary|lead","source_family_hint":"...","disposition":"include|exclude|defer","reason_code":"answers_question|duplicate_family|wrong_identity|wrong_version|no_original|irrelevant|unsafe|unavailable|needs_review","screened_by":"...","screened_at":"..."}
```

必須保存排除與 defer；否則無法區分「沒看見」與「看見後合理排除」。同一 URL canonicalization、DOI/ISBN、標題＋作者＋日期及 source genealogy 用於去重；不能只用 URL 字串去重。

## 7. Raw／derived 證據與 provenance

Artifact 最低欄位：`artifact_id`、`candidate_id`、`kind`、`raw_or_derived`、original/canonical/archive URL、retrieved_at、content SHA-256、MIME、size、capture method、精確 locator、rights/access restriction。

衍生物另記：`derived_from`、input hash、operation（OCR/transcribe/translate/extract/frame）、tool/version/model、parameters、output hash、human_checked、known_error。原始檔不可被 OCR 文字或摘要取代。截圖只能證明畫面；有可能時另存 HTML／PDF／原始媒體與 metadata。

## 8. Source evaluation：內容與載體分開

每個納入來源評估：

- **身份**：作者／帳號／機構是否真的是聲稱者。
- **來源角色**：第一手、同期、獨立二手、通稿、轉載、線索。
- **資訊者知情條件**：親歷、職務可知、轉述、回憶、未知。
- **時間距離**：事件當時或多年後回憶。
- **獨立性**：是否同 source family、共同通稿、同一匿名來源。
- **動機與限制**：宣傳、辯護、商業、粉絲整理、節錄、翻譯。
- **lateral reading**：至少一個站外來源檢查陌生發布者；官方自述不能自行證明機構獨立可信。

## 9. Claim／hypothesis matrix

核心主張不得只有「有來源」：

```json
{"claim_id":"C1","question_id":"Q1","text":"...","claim_type":"fact|relationship|timeline|capability|self_narrative|inference","status":"SUPPORTED|CONTESTED|AMBIGUOUS|UNAVAILABLE|REFUTED","hypotheses":[{"id":"H1","fit":"supports|contradicts|neutral"},{"id":"H2","fit":"..."}],"evidence":[{"artifact_id":"A1","locator":"p.4/para.7/00:03:12","mode":"direct|indirect|negative","source_family_id":"SF1","weight_reason":"..."}],"counterevidence":[],"conflict_resolution":"...","sensitivity":"若移除哪筆證據，結論是否改變","required_before_story_use":false}
```

優先找能區分假說的 diagnostic evidence，而不是累積大量兩邊都相容的履歷。負向證據只有在資料集覆蓋範圍、建立慣例、索引品質與搜尋方法足以期待該紀錄出現時才可使用；一般 Google 沒搜到只能是 `search_nonresult`。

## 10. 三個 checkpoint

1. **START_CHALLENGE**：主要搜尋前，由 devil’s advocate 檢查問題是否預設答案、同名風險、反方假說、來源盲區、傷害／安全風險。
2. **MIDPOINT_REVIEW**：至少一個 P0 有初步證據後，檢查是否只累積支持材料、哪些 known item 沒被主查詢找回、哪些 source family 過度集中、是否需改 query／source plan。修訂要留事件。
3. **CLAIM_AUDIT**：交付前逐個 P0 claim 重抽原文與 locator；核對名稱、日期、數字、引文、版本、關係動詞；對敏感／重大結論使用第二 reviewer。第二 reviewer 可以是另一人、另一模型的隔離 context，或同一執行者在不看分析結論下從原始證據重抽；必須明標，不能把普通重讀冒充獨立。

R2 最少三 checkpoint；R1 最少 START_CHALLENGE＋CLAIM_AUDIT。高風險真人敏感主張必須有獨立 reviewer 或保持 `AMBIGUOUS`。

## 11. Known-item 與查詢品質測試

若已有可靠 seed，建立 benchmark；至少一筆設 `holdout:true`，不能用它的完整標題／獨特引文直接組主查詢。記錄每個 benchmark 是否由哪個 query 找回。漏掉的 seed 要：擴詞／換平台／改 route，或解釋索引與範圍限制。

Known-item 測試只證明「能找回已知材料」，不證明未知材料完整；仍需 citation、adjacent、archive 等不同 route。沒有 benchmark 時，protocol 寫理由，R2 改以第二 reviewer 做 search-strategy review，不能空白略過。

## 12. 由證據計算 coverage 與 saturation

工具從 event log 計算，不接受手填：

- `planned_route_coverage`：must route 中有有效事件的比例及缺口。
- `query_diversity`：不同語言、平台、surface、method 與實質不同概念組合；三條只加「專業／著名」的近義查詢算一個 route。
- `family_yield_curve`：依事件序列新增獨立 source family。
- `candidate_flow`：raw hits（可得時）→ candidates → include/exclude/defer → artifacts → claims。
- `benchmark_recall`：找到／未找到的 known items，只作診斷，不單獨當完整度分數。
- `p0_closure`：每個 P0 為 SUPPORTED/CONTESTED/AMBIGUOUS/UNAVAILABLE/REFUTED，且有證據或完整 attempts；不得刪除不利問題。
- `review_closure`：checkpoint 與 P0 claim audit 完成。

可以停止：must routes 已執行或有可辯護的 blocked／revision；最後 `no_new_family_window` 個**不同 route**沒有新增獨立 family；P0 全部閉合；defer 沒有未處理的高價值候選；claim audit 通過。新增來源只重複同一家族時停止，不為湊數繼續。

## 13. 工具失敗不是研究失敗，但必須可見

- 動態頁抓不到：保存 capture error，改 reader／print／官方 API／公開 archive；不可用摘要假裝原文。
- 搜尋結果個人化／漂移：保存時間、語言、地區／登入狀態（不存敏感 cookie）、raw result capture；結論不依賴排名。
- OCR／轉寫錯：保存原檔、信心／known error、人工核對核心引文。
- archive 缺頁：記 collection coverage 與 missingness；不要把缺檔當事件未發生。
- 社群內容刪除：快照是「某時曾被擷取」；先驗帳號身份、上下文與是否為重貼。
- 工具供應商失效：protocol 記工具類別與 fallback，不把品牌寫成唯一方法。

## 14. 實作驗收基準

每次修改本規範至少跑：

1. **false-complete adversarial fixture**：五個手填 surface、三條近義 query、一個空洞 artifact，必須 FAIL。
2. **broken-chain fixture**：改一筆舊 event 或衍生物缺 input hash，必須 FAIL。
3. **unresolved-P0 fixture**：P0 被從 claims 漏掉，必須 FAIL。
4. **same-family cross-check fixture**：兩篇轉載冒充獨立，必須 FAIL／警告且不能滿足獨立核對。
5. **real benchmark run**：使用既有研究對象重跑；報告 known items 找回、漏失、candidate dispositions、source families、checkpoint 修訂與最終差異，不只測 schema。
