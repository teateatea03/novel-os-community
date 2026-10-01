# 角色深挖研究作業手冊（Research Operations）

本手冊只處理「怎麼挖、用什麼挖、去哪裡挖、何時停止」，不替代人物模型與心理分析。核心順序是：**問題化 → 消歧 → 地形圖 → 探索 → 定向取得原文 → 鄰接擴展 → 核驗 → 保存 → 飽和停止**。

> **v1.8 執行規則**：本文件保留來源地形與工具路由；新 R1／R2 的完成證據改由 `research-evidence-run-v2.md` 與 `scripts/validate_research_run.py` 管理。下文 `minis.character-research-manifest.v1` 僅供舊研究相容與 R0 輕量定位，不可用來宣稱新 R1／R2 完成。

## 1. 研究層級與最低產物

| 層級 | 用途 | 必做來源面 | 最低可重現產物 |
|---|---|---|---|
| **R0 定位** | 功能角色、單一事實／版本問題 | 1 個權威入口＋必要正典 | 身份卡、1 個查詢紀錄、來源清單、未解缺口 |
| **R1 場景研究** | 主要配角、關係／能力／時間線 | 至少 3 種來源面；包含原始／官方或正典 | 查詢矩陣、來源地形圖、證據包、負向查核紀錄 |
| **R2 深度研究** | 主角、核心對手、真人／歷史改編、爭議版本 | 至少 5 種相關來源面；原始資料、鄰接網、反證面必含 | 完整 research manifest、查詢日誌、來源譜系、原始快照／精確定位、飽和報告與盲點 |

R0/R1/R2 是**研究作業深度**，與人物模型 L0/L1/L2 分開。資料已由使用者完整提供時可降低外搜層級，但要記錄 `scope_exception`，不能假裝執行過搜尋。

## 2. R0：先做身份與版本消歧

建立 `identity-resolution`：

```yaml
canonical_label: ...
aliases: [藝名, 本名候選, 舊名, 帳號, 原文名, 羅馬字, 官方譯名]
language_variants: [zh-Hant, zh-Hans, ja, ko, en, ...]
disambiguators: [作品, 職業, 組織, 地區, 年代, 合作者]
anti_disambiguators: [已知同名者與排除條件]
identity_keys: [官方帳號, DOI/ISBN/IMDb/Wikidata/ORCID 等公開識別碼]
version_scope: ...
confidence: EXTRACTED | INFERRED | AMBIGUOUS
```

至少用兩個不只重複姓名的公開屬性綁定身份，例如「帳號＋官方作品頁」、「姓名＋組織＋活動日期」。同名者未排除前，不合併來源。

### 查詢字詞桶

先建詞桶，再組查詢，不靠臨場想到什麼搜什麼：

- `N` 名稱：精確姓名、別名、原文、舊帳號、常見錯拼與音譯。
- `C` 脈絡：作品、公司、學校、地區、年代、合作人。
- `E` 事件：訪談、得獎、加入、退出、爭議、發表、角色初登場。
- `D` 文件：訪談、逐字稿、履歷、設定集、press kit、論文、檔案、判決／公告（限合法公開）。
- `X` 排除：同名者、錯誤作品、無關國家或職業。

代表查詢：`"N" C D`、`site:domain "N"`、`"N" E before:YYYY-MM-DD`、`"N" filetype:pdf`、原文名與當地語言詞。搜尋運算子依平台實際支援調整，不能把 Google 語法原封不動假設所有站都支援。

## 3. 先畫來源地形圖：去哪裡挖

不要只用一般搜尋引擎。依主體選擇相關來源面，並記錄「查過但無結果」：

### 共通來源面

1. **發現層**：一般搜尋、新聞搜尋、百科、粉絲維基、論壇、社群；只負責別名、關鍵事件與原始來源線索。
2. **原始／權威層**：官方網站、本人公開帳號、原作、正式劇本、出版者、製作委員會、機構公告、原始訪談／影片／逐字稿。
3. **圖書與學術層**：國家／大學圖書館目錄、WorldCat、Google Books、出版社頁、Google Scholar、Crossref、PubMed／JSTOR 等相關領域資料庫；用 ISBN／DOI 等識別碼去重。
4. **新聞與期刊層**：具編輯流程媒體、報刊資料庫、產業刊物；分清原訪、通稿、綜合稿與轉載。
5. **檔案與歷史層**：國家／地方／校史／企業／專門檔案館、博物館、finding aid、館藏目錄、口述史庫；先由 collection → series → box/folder → item 定位，必要時詢問館員。
6. **鄰接網層**：家人、朋友、合作人、同事、競爭者、組織、作品 credit、活動名單、同一事件參與者。直接人物資料斷裂時，用 FAN／cluster research 從關係人的紀錄反照主體。
7. **網頁歷史層**：Internet Archive／Memento／Archive.today 等公開網頁典藏、舊版 sitemap、RSS。失效頁先查 canonical URL、標題精確句，再用 `source-collectors` 的 `wayback` 取 snapshot URL；不把快照日期當原發布日。
8. **視覺影音層**：原影片／音訊頁、字幕／逐字稿、圖片原頁。YouTube 先用 `source-collectors` 的 `youtube-transcript`；沒有字幕再用 `media-meta`（yt-dlp 不下載）。必要時抽關鍵幀、反向圖片搜尋、OCR、metadata／upload context。EXIF 可缺失或被修改，只是線索。
9. **公共紀錄與專業登錄層**：依法公開且與任務必要的公司／法人、作品權利、選舉、法院、政府 open data、專業登錄；不同司法區各用官方入口。環境已有可用登入則用該身份取得可見內容；沒有則用公開入口。不索取帳密、不破解付費牆。取得方式見 `session-access-policy.md`。

### Instagram MCP source route

在共通來源面新增一個 **公開社群一手層**：

9. **Instagram 社群層（自動）**：若存在可核對的本人／官方帳號，先用本機 `instagram-instaloader-mcp`；匿名被擋或內容不完整時，改用環境已有的已登入瀏覽器或其他可見來源。保存 raw JSON／頁面擷取、canonical URL、shortcode、發布日、擷取日、caption、metrics、`access_mode` 與錯誤／限流紀錄。它是自我發布證據，不是私人生活資料庫；不向使用者要 Cookie／密碼，不把憑證寫進研究檔。
10. **X／Twitter 社群層（自動）**：若存在可核對的本人／官方 handle，走 `source-collectors` 的 `x-profile`／`x-timeline`／`x-status`；公開路由被擋改已登入瀏覽器。保存 status URL、text、created_at、`access_mode`。時間線是樣本不是完整檔。完整規則見 `x-research-route.md`。

### Instagram route 整合規則

- 真人／公開人物：本人／官方 Instagram 可作 P1 公開職業、作品、活動與自我敘事來源；涉及 P2/P3、敏感關係或心理，只能建立有來源的 claim，不能由 caption 或照片直接推導。
- 非真人：Instagram 只在研究媒介或作者明確要求的公開宣傳材料範圍內使用，不可把真人帳號與虛構角色 witness 混合。
- 相同貼文被新聞／其他平台轉載時，先做 source genealogy，原貼文與轉載不自動算兩個獨立 family。
- 每次 route 的 raw capture 進 candidate／artifact ledger；tool failure 不等於 zero result，rate limit 不等於不存在。
- 完整操作、schema、fallback 與固定指令見 `references/instagram-mcp-research-route.md`。

### 媒介路由

- **真人／歷史人物**：本人／機構 → 原訪與同期紀錄 → 圖書／報刊／檔案 → 鄰接網 → 公共紀錄；敏感資料依 P/U/S 協定。
- **小說角色**：指定版本正文 → 章節／頁碼索引 → 作者／編輯訪談 → 版本校勘、學術評論 → wiki 作導航。
- **動漫／電影**：漫畫卷話／動畫集數／影片 timecode → credits／設定集／官方站 → 編劇導演聲優訪談 → 版本差異；角色與演員分開。
- **遊戲／互動作品**：遊戲版本、任務／對話／codex、patch notes、官方資料 → datamine 僅在合法公開且標非正典／版本限制時作線索。
- **原創角色**：不做無目的外搜；只研究角色所需職業、年代、文化、制度與 lived-experience 盲點，並與角色事實分層。

## 4. 四輪搜尋，而非一條直線

### Round A：探索（高召回）

用所有名稱／語言變體與 2–4 個消歧詞找 seed sources。此輪只建立：別名、時間線骨架、機構、作品、重要關係、候選來源。搜尋摘要只能成為 lead。

### Round B：定向取原文（高精確）

對每個核心問題建立 exact query；追到原始頁、原作段落、完整訪談、影片 timecode、檔案 item。二手文有引文時，以「獨特短句精確搜尋＋作者／日期／標題」追源；找不到原文就保留中介鏈與 `original_retrieved:false`。

### Round C：雪球與鄰接擴展

- 向後追：腳註、書目、credits、訪談提及的文件與人物。
- 向前追：誰引用、回應、修正或重新發布該 seed。
- 橫向追：同事件其他參與者、同組織、同地點、同時期新聞、FAN 網絡。
- 查不合模型的詞：`criticism`、`correction`、`denied`、`retrospective`、`版本差異`、當地語言同義詞。

每擴展一層要記錄「這條邊預期回答哪個問題」。超過 2 hops 仍未改變核心問題時，停止網絡漂移。

### Round D：反證與缺口搜尋

把核心主張改寫成可被否定的問題；搜尋相反日期、其他版本、否認／更正、同名者、同期沉默的替代原因。至少記錄一個**未找到也有意義的負向查核**，但「沒有搜到」不是「不存在」。

## 5. 用什麼工具：按證據問題選，不按工具名炫技

| 問題 | 首選方法／工具類型 | 必留產物 |
|---|---|---|
| 找頁面／限定站點與日期 | 搜尋引擎、站內搜尋、`site:`、精確片語、日期／檔案類型 | exact query、平台、日期、結果數或篩選理由 |
| 找書／論文／版本 | 圖書館目錄、WorldCat、Scholar、Crossref、領域資料庫 | ISBN/DOI、版次、頁碼／章節 |
| 找舊頁／刪改頁 | Wayback/Memento/Archive.today、RSS、canonical URL | 原 URL、snapshot URL、capture time、原發布日（若可知） |
| 讀 PDF／掃描 | 原生文字抽取；無文字層才 OCR | 檔案 hash、頁碼、OCR 語言、人工校對狀態 |
| 讀影音 | 官方字幕／逐字稿優先；下載合法可得媒體後用 ffmpeg 抽音訊／關鍵幀、語音轉寫 | timecode、檔案／頁面、轉寫是否人工校對 |
| 驗圖片／影片 | Google Lens／TinEye／InVID 類反搜、關鍵幀、地標／時間線比對 | 原檔或 URL、關鍵幀、最早可見版本、限制 |
| 管來源與快照 | Zotero 類書目工具、WARC／網頁快照、結構化 CSV/JSONL | metadata、accessed_at、local path、SHA-256 |
| Instagram 帳號／貼文 | 本機 `scripts/instagram_mcp_client.py`（MCP stdio → Instaloader）；匿名被擋改已登入瀏覽器 | profile／posts／post／raw capture JSON、canonical URL、shortcode、captured_at、`access_mode`、錯誤／限流紀錄 |
| X／Twitter 帳號／貼文 | `collect.py x-profile`／`x-timeline`／`x-status`；公開被擋改已登入瀏覽器 | handle、status URL、text、created_at、`access_mode`；時間線標樣本 |
| YouTube 字幕／自動字幕 | `../source-collectors/scripts/collect.py youtube-transcript <url>`（jdepoix/youtube-transcript-api） | video_id、language、is_generated、snippets、source_url |
| 影音頁中繼資料 | `../source-collectors/scripts/collect.py media-meta <url>`（yt-dlp `--skip-download -J`） | title／description／upload_date／channel／subtitle_languages；不下載媒體 |
| 失效／舊網頁 | `../source-collectors/scripts/collect.py wayback <url>`（akamhy/waybackpy） | archive_url、snapshot timestamp；快照日期 ≠ 原發布日 |
| HTML→較乾淨 Markdown | `../source-collectors/scripts/collect.py html-md <file>`（Alir3z4/html2text）；raw 仍由 PWR 保存 | derived Markdown，回指 raw hash |
| RSS／Atom 發現 | `../source-collectors/scripts/collect.py rss <feed-url>`（kurtmckee/feedparser） | feed title、entry link／published；條目是 lead |
| 頁面發布日候選 | `../source-collectors/scripts/collect.py page-date <html>`（adbar/htmldate） | publication_date；不可代替 captured_at／snapshot |
| 頁面 OG／JSON-LD | `../source-collectors/scripts/collect.py page-meta <html>` | canonical、og、jsonld；是 lead 不是事實 |
| Wikidata 身份鍵 | `wikidata-search` 再 `wikidata-entity Qid` | QID、官網、社群帳號、ORCID／VIAF；標籤不是傳記 |
| IndieWeb `rel=me` | `page-meta` 的 `rel_me` | 本人站聲明的帳號 URL；需第二屬性綁定 |
| DOI 書目 | `doi-meta 10.xxxx/yy`（Crossref） | 標題、作者、ORCID、期刊、issued；再抓原文 |
| PDF 文字層 | `pdf-text <file.pdf>`（pdftotext） | derived 文字；原 PDF 當 raw |
| sitemap 發現 | `sitemap <url>` | loc 列表；是 lead |
| Bluesky 公開檔 | `bsky-profile <handle>` | did／handle／displayName／description |
| 批次處理 | `curl/wget`、`pdftotext`、OCR、ffmpeg、hash 工具 | 指令或工具版本、輸入輸出、失敗紀錄 |

LLM 可以：產生查詢候選、翻譯／歸納、從**已取得材料**抽取主張、找矛盾。LLM 不可以：把生成內容當來源、聲稱讀過無法存取的頁、用摘要補原文、依模型記憶填 URL／引文。重要抽取需回到原頁逐項核對。

工具失敗時用 fallback ladder：可讀原頁 → 已登入瀏覽器（若環境已有）→ reader/text view → print/PDF → 公開快照 → 書目／中介來源 → 聯絡館員／作者（若合適）→ `UNAVAILABLE`。一條路失敗就換下一條；不因「需要登入」停搜。不索取帳密、不破解 CAPTCHA／付費牆、不換馬甲。詳見 `session-access-policy.md`。

- 若研究來源含 Instagram，必須把 MCP raw capture 綁到 `artifacts.jsonl`：`raw_or_derived: raw`、`kind: instagram_mcp_capture`、`locator` 至少含 profile／post URL 或 shortcode、`sha256`、`retrieved_at`、`source_family_id`；衍生摘要不可取代 raw capture。
- 每個 Instagram MCP route 都要在 `events.jsonl` 有實際 `BROWSE`／`CAPTURE` 事件，且在 `candidates.jsonl` 留下貼文候選的 include／exclude／defer；不接受只在報告寫「已查 Instagram」。

## 6. 每次搜尋必留 research manifest

最低 schema：

```json
{
  "schema": "minis.character-research-manifest.v1",
  "research_depth": "R0|R1|R2",
  "questions": [{"id":"Q1","text":"...","priority":"P0|P1|P2"}],
  "identity_resolution": {"aliases":[],"disambiguators":[],"excluded_homonyms":[]},
  "source_map": [{"surface":"official|archive|news|scholarly|adjacent|web_archive|av|public_record","status":"searched|not_applicable|blocked","reason":"..."}],
  "queries": [{"id":"q1","question_id":"Q1","platform":"...","exact_query":"...","language":"...","searched_at":"...","filters":{},"result":"useful|zero|noise|blocked","new_source_families":0,"notes":"..."}],
  "artifacts": [{"id":"a1","url":"...","archived_url":"...","retrieved_at":"...","local_path":"...","sha256":"...","locator":"page|paragraph|timecode|box-folder-item","capture_status":"full|partial|metadata_only"}],
  "claims": [{"id":"c1","question_id":"Q1","artifact_ids":["a1"],"source_family_id":"sf1","status":"EXTRACTED|INFERRED|AMBIGUOUS|UNVERIFIED","counterevidence":[]}],
  "negative_checks": [{"question_id":"Q1","where":"...","query":"...","meaning":"not_found_not_absent"}],
  "saturation": {"last_queries":[],"new_independent_families":0,"open_p0_gaps":[],"stop_reason":"..."},
  "scope_exceptions": []
}
```

檔名使用穩定 ID，不用容易重名的標題：`<source-id>_<YYYY-MM-DD>_<short-label>.<ext>`。檔案館材料另含 repository／collection／series／box／folder／item；PDF／書籍含 edition/page；影音含 timecode；網頁含 accessed_at。若合法保存本地副本，計算 SHA-256；不能保存全文時，至少保存書目、精確 locator、短引與存取限制。

## 7. 證據擷取與核驗

每個核心主張至少回答（對齊 First Draft／GIJN 五柱：provenance／source／date／location／motivation）：

1. **Provenance**：來源真的是誰產生的？是否有原始版本，還是轉載／截圖／搜尋摘要？
2. **Date**：事件日、發布／更新日期、擷取日、快照日是否分開？不得互代。頁面日期用 `page-date` 只當候選。
3. **Source**：這是直接觀察、當事人自述、他人轉述、通稿還是推論？
4. **Location／identity**：身份／版本是否確定？地點若相關，是否有獨立材料，而非只靠檔名或字幕？
5. **Motivation**：來源為何公開這份材料（宣傳、更正、爭議、存檔）？這不自動等於謊言，但影響解讀。
6. 其他來源是否獨立，還是同一 source family？
7. 是否有更正、刪節、翻譯差異或上下文缺失？
8. 什麼新材料會推翻它？

落地工具與不採用清單見 `../source-collectors/references/practitioner-methods.md`。

網頁與新聞不要只存首頁 URL；保存標題、作者／發布者、發布／更新／抓取日、段落定位、短引與 canonical／archived URL。影音保存 timecode；原作保存卷／章／頁／集／幕；檔案保存完整館藏階層。

## 8. 搜尋飽和與停止 Gate

不以「搜很久」或「結果很多」判定完成。可以停止的條件：

- P0 問題均有答案或誠實標 `UNAVAILABLE/AMBIGUOUS`；
- 已查完該 R 層必要來源面，`not_applicable/blocked` 有理由；
- 最近至少 3 個彼此不同的定向查詢／citation/FAN 擴展沒有新增獨立 source family，或新增來源只重複已知履歷；
- 核心主張有精確 locator、來源譜系與反證搜尋；
- 仍存在的缺口不會讓版本、身份、關係、能力或重要場景失真，或已列 `required_before_story_use`。

以下情況必須繼續或降級結論：只有搜尋摘要、只有粉絲二手整理、原文不可得、同名未排除、所有交叉來源同源、關鍵日期靠推算、R2 無反證／鄰接搜尋、查詢日誌不可重現。

## 9. 外部實務依據（導航清單）

- Society of American Archivists, *Using Archives: A Guide to Effective Research*: finding aid、館藏範圍、遠端請求、限制與未處理館藏。https://www2.archivists.org/usingarchives
- GIJN, *Fact-Checking & Verification*: provenance/source/date/location/motivation、逐句查核、反搜與影音驗證資源。https://gijn.org/resource/fact-checking-verification/
- Bellingcat, *Online Investigation Toolkit*: 依 maps、image/video、people、websites、archiving、data organization 等問題選工具並保留 caveat。https://bellingcat.gitbook.io/toolkit
- 本機落地與不採用清單：`../source-collectors/references/practitioner-methods.md`（RSS、頁面日期／OG、Wikidata QID；不接用戶名枚舉、人臉辨識、GHunt）。
- McGowan et al., PRESS 2015: 研究問題翻譯、布林／鄰近運算、subject headings、text words、拼字語法、limits/filters 的搜尋式同儕審查。https://pubmed.ncbi.nlm.nih.gov/27005575/
- Elizabeth Shown Mills, *Identity Problems & the FAN Principle*: 直接紀錄缺失時研究 friends/associates/neighbors，以 cluster evidence 解身份問題。https://www.evidenceexplained.com/content/quicklesson-11-identity-problems-fan-principle
- Smithsonian Institution Archives, *How to Do Oral History*: 先背景研究、開放式問題、錄音環境、同意與保存。https://siarchives.si.edu/history/how-do-oral-history
- Zotero Documentation, *Adding Items*: 優先從出版／摘要主頁取得高品質 metadata，網頁可存 snapshot，PDF 需綁 parent item／identifier。https://www.zotero.org/support/adding_items_to_zotero
- Google Search Help, *Refine Google searches*: quotes、site、exclude、before/after、filetype 與 filters。https://support.google.com/websearch/answer/2466433?hl=en

上述指南提供方法，不代表任何單一工具永遠可用；工具清單需按地區、媒介與平台變動更新。
