---
name: novel-character-deep-digger
version: 1.10.0
description: 當使用者提供角色姓名、作品名、URL、草稿或 Instagram 帳號，或要求「深挖人設」「研究這個人／角色」「建立角色人設」「徹底分析人物」「測試角色是否寫得活」時使用。遇到可核對的 Instagram 或 X／Twitter 帳號時，自動擷取 profile／posts 納入 evidence run，不要求使用者自行整理。蒐集以取得可核對原文為先：環境已登入則用既有 session，未登入則用公開／匿名路由，不因登入狀態封殺搜尋方法。第一步先判定 real／novel／anime／film／other、角色重要度、人物模型深度與研究深度。真人採 Evidence Run v2；非真人另先建立 Work／Expression／Manifestation／Item witness、continuity map 與媒介 locator，再按小說、漫畫、影視、遊戲、舞台、神話或原創路由研究。新 R1／R2 必須保存 protocol、append-only 事件、候選篩選、raw／derived 證據、主張／競爭假說、版本矛盾與計算式飽和，最後才建模與場景驗證。
---

# Novel Character Deep Digger

把零散資料轉化為「可持續驅動長篇情節」的人物模型，而不是形容詞清單。

## 名稱本地化

名稱本地化採固定優先序：有可靠來源的官方中文譯名就使用官方譯名；沒有官方中文譯名時，不自行意譯，改依原文可靠讀音建立台灣繁體中文音譯，必要時在音譯後括註原名或型號。研究對象與引用節點的原始名稱保留不改；`name_zh` 是查詢輔助，不取代原名、ID 或別名，也不代表官方譯名；保存 `name_zh_language`、`name_zh_provenance`、`name_zh_source_label`。只有在原文讀音也無法可靠判讀時才標 `UNKNOWN`／【待定】，不得以自行意譯代替。後續交給角色資料庫建立時，將同一欄位寫入 `properties.name_zh`。

1. **第一步必須分類**：先判定研究主體是 `real`（真實／真人）、`novel`（小說）、`anime`（動漫／漫畫／動畫）、`film`（電影版本／電影原創）或 `other`（遊戲、舞台、神話、原創、跨媒體或尚未消歧）。不得在未分類的情況下直接套用真人或虛構角色流程。
2. **辨識任務**：區分真人／歷史人物研究、既有小說角色、動漫角色、電影版本角色、原創角色與舊人設修補。
3. **證據與創作分流**：全程使用四種標籤：
   - **【明示】**來源直接支持的資訊。
   - **【推論】**由行為或脈絡導出的解讀；附理由與信心（高／中／低）。
   - **【提案】**為小說可用性新增的設定；不得偽裝成事實。
   - **【待定】**資訊不足或互相矛盾，需作者決定。
4. **可追溯的私人背景、關係與未證實線索，不捏造隱私**：真人研究先讀 `references/real-person-research-protocol.md`。為貼近史實或作者指定寫實度，可保存本人公開或可靠媒體明確報導的個人背景、教育、公開關係、家庭／合作網與敏感公開主張（P1／P2／P3）；必須附 URL／短引文／日期／來源類型／信心／時間範圍。查到八卦、匿名爆料、搜尋摘要、失效頁、外流或 doxxing 等資料時，也要保存其**線索存在與來源**為 U 類／`claim`，明標 `UNVERIFIED`／風險／不可作事實使用，且不複製高度敏感內容或可識別細節。S 類（帳密、憑證、精確住址、私人聯絡、醫療紀錄、性私密素材）只記「發現但未擷取／未使用」的稽核標記。關係必須寫成可核對的圖譜邊；不做臨床診斷，也不把個人或 U 類資料直接推導成性格。
5. **能力不可只存名稱**：研究每項可用技能、職能、戰力、特殊能力或社會能力時，必須建立可引用能力卡：可觀察效果、作用／操作方式、前提、資源或訓練、限制／代價／失敗模式、反制（適用時）、版本範圍與來源。未知欄位一律標【待定】／`UNKNOWN` 與原因；不得用同類角色常識、形容詞或粉絲印象補完。
6. **以行為證明性格**：每項核心特質至少對應一種可觀察行為、觸發條件或代價。
7. **保留矛盾**：立體人物應有價值衝突、場合差異、自我敘事與真實需求的落差。
8. **服務故事**：所有設定都要能影響選擇、關係、衝突、情節或人物弧。
9. **角色檔是可修訂模型，不是填表競賽**：問卷、訪談、人格詞彙與完整背景只作探索工具；未經場景選擇、聲音或反例檢驗的欄位，不得因寫得多就視為已成立。
10. **故事相關性決定深度**：不要求每個角色完成同樣長度。主 POV／主要對手做完整模型；關鍵配角做關係與決策模型；功能角色只做最低可引用卡與局部約束。未改變下一步選擇、關係、能力、風險或讀者辨識的細節預設不擴寫。
11. **禁止過早單解收斂**：外在目標、需求、恐懼、錯誤信念與弧線先視為候選假說。證據稀少時保留 2–3 個競爭版本與推翻條件；真人不得把小說工藝的「核心創傷／錯誤信念」當成已發現的心理事實。

## 最高層大原則：角色反應必須有現實因果

角色反應與行為盡量貼近現實，不把性格形容詞當成行為答案。每個重要反應都要能從角色當下知道的資訊、身心狀態、過往經驗、關係／權力、資源、風險與可見選項推導出來；不同關係、不同壓力和不同資訊可以產生不同反應，但不能只為了戲劇效果突然改變人格。

若安排反常、低機率或類型化反應，必須提供足夠前因、觸發、機會、主觀合理化與代價。研究資料不足時要保留多個解釋，不把「他應該會這樣」寫成確定事實。

## 工作流程

### 0. 分類閘門（最先完成）

在任何任務簡報、搜尋、人物心理推論或資料庫寫入前，先建立分類卡：

```yaml
subject_category: real | novel | anime | film | other
subject_subcategory: ...
subject_kind: real_person | historical_person | fictional_character | original_character | unknown
source_medium: [...]
canon_scope: public_record | novel_canon | anime_canon | film_canon | cross_adaptation | user_created | unknown
version_scope: ...
franchise: ...
classification_basis: ...
classification_confidence: EXTRACTED | INFERRED | AMBIGUOUS
```

分類規則與次分類見 `references/character-category-taxonomy.md`。分類不確定時先用 `other`／`unknown`／`AMBIGUOUS`，並記下需要查證的項目；不能因角色有動畫改編，就把原作小說或真人原型直接歸為動漫。

不同主類別採不同研究重點：

- **`real`**：公開紀錄、本人／官方資料、歷史檔案；不得推定未公開私生活或做遠端診斷。
- **`novel`**：文字正典、敘事者可靠性、角色認知與作者／版本差異。
- **`anime`**：漫畫原作、動畫改編、動畫原創、季別、重製與劇場版分開記錄。
- **`film`**：電影文本與官方設定；演員本人資料不可混入角色節點。
- **`other`**：先確認媒介、正典與權利狀態；完成消歧後才遷移分類。

分類卡完成後，報告第 0 節與角色資料庫主節點都必須保存同一組欄位。真人原型與其小說／動漫化身要分開建檔，使用 `derived_from`／`inspired_by` 連接。

**非真人追加閘門**：若 `subject_category != real`，先讀 `references/fictional-character-research-operations.md`。建立 `target_character_instance`、Work／Expression／Manifestation／Item witness cards、continuity map、translation／localization policy 與媒介 locator。不能用同名把不同 continuity 無聲合併，也不能用官方摘要、Wiki 或設定頁代理小說章節、漫畫頁格、影視時間碼、遊戲路線／patch 或舞台場次的 primary story evidence。

### 1. 建立任務簡報與深度預算（分類完成後）

從使用者輸入提取：
- 角色／人物、作品或時空背景
- 研究對象是否為真人、歷史人物、既有虛構人物或原創人物
- 寫作類型、篇幅、敘事視角、目標讀者、尺度
- 需要忠於原作／史實，還是可自由改編
- 已確定設定與不可更動項目
- 角色重要度：`lead`／`major_supporting`／`minor_functional`
- 工作階段：`discovery`（無正文探索）／`draft_diagnostic`（已有場景診斷）／`revision`（依讀者或作者回饋修訂）
- 人物模型深度：L0／L1／L2；另行決定研究作業深度 `R0`（身份／版本定位）、`R1`（場景可用研究）、`R2`（核心人物深度研究）。兩者不可互相冒充。
- 這次最需要回答的 1–3 個故事問題，以及可用時間／來源／篇幅預算

依風險分層，不機械填滿整份模板：

| 層級 | 必做內容 | 何時升級 |
|---|---|---|
| **L0 最低可用角色** | 身份／版本、故事位置、當前目標、可見阻力、能動性、至少一個行為錨點或作者設定 | 將成為衝突解法、POV 或長期角色 |
| **L1 場景可寫** | 慣用策略與代價、關係差異、聲音線索、2–3 個條件式反應、能力／限制 | 多場出現、需要辨識度或連續性 |
| **L2 長篇可持續** | 競爭角色引擎、狀態分布、形成史、人物弧候選、關係網、驗證場景與反例 | 主角、主要對手、重大真人／既有角色改編 |

若名稱有多個可能對象、URL 無法判讀，或「忠於原作」與「自由改編」會導致完全不同結果，只問最少量的澄清問題。其餘缺口可先標為【待定】並提出選項，不要用連續提問阻塞工作。

### 2. 研究作業：先建立可重現搜尋，再蒐集與校驗

任何需要外部研究的任務先讀 `references/research-operations.md`、`references/session-access-policy.md` 與 `references/research-evidence-run-v2.md`。依 R0／R1／R2 完成身份消歧、N/C/E/D/X 查詢詞桶、來源地形圖與四輪搜尋：探索 seed → 定向取得原文 → 引文／credits／FAN 鄰接擴展 → 反證與負向查核。工具依證據問題選擇。蒐集以拿到可核對原文為先：有登入就用登入，沒登入就用公開／匿名方法，一條路失敗就換下一條；不向使用者索取帳密，不把憑證寫進研究檔，不破解存取控制。

**新 R1／R2 不再以手填 manifest 作完成證明。**先建立 `minis.character-research-run.v2` 的 `protocol.json`，再以 hash-chained `events.jsonl` 保存實際 QUERY／BROWSE／CITATION／PIVOT／CONTACT／CAPTURE／TRANSFORM／REVIEW；搜尋結果先進 candidates ledger，經 include／exclude／defer 才能擷取。raw evidence 與 OCR／轉寫／翻譯等 derived artifact 分開，衍生物必有 input hash、工具版本與人工核對狀態。核心主張需連到精確 locator、source family、反證與競爭假說。

R1 必做 `START_CHALLENGE`＋`CLAIM_AUDIT`；R2 再加 `MIDPOINT_REVIEW`、known-item holdout 或獨立 search-strategy review。coverage、query diversity、P0 closure 與 saturation 由 event/candidate/artifact/claim/review 關聯計算，不接受一句手填「已飽和」。執行：

```bash
python3 scripts/validate_research_run.py <research-run-directory> --summary <research-run-directory>/run-summary.json
```

validator FAIL 時只能標 `RESEARCH_INCOMPLETE`；使用者限制外搜時標 `SCOPE_LIMITED`。舊 `minis.character-research-manifest.v1` 可保存 legacy provenance，但不得自動升為 v2／R2，也不可偽造查詢事件。

非真人 R1／R2 在通用 run validator 後再執行：

```bash
python3 scripts/validate_fictional_research.py <research-run-directory>
```

小說 claim 定位到版／卷／章／節／頁或段落；漫畫定位到卷／話／頁或 scroll anchor／panel／balloon；影視定位到 season／episode／cut／timecode／shot；遊戲定位到 platform／region／build／patch／DLC／save／route／quest／node／choice；舞台定位到 script／production／venue／date／cast／act／scene／cue；神話民俗定位到具體採集文本／講述者／地點／日期／variant。`CROSS_VERSION_STABLE` 必須每個納入 continuity 都有 primary story witness，並通過 `VERSION_CONTRADICTION_AUDIT`；只有 official paratext／summary 時只能交付版本摘要，不能建立完整跨版本人格。

### 2.1 公開網頁擷取與站內探索路由

外部研究需要取得公開 HTTP(S) 原文、站內連結、sitemap／RSS，或要將網頁保存成 raw＋Markdown＋candidate 時，先讀 `../public-web-research/SKILL.md`，使用其安全 HTTP 基線。它提供 Crawl4AI 式 LLM-ready Markdown、BFS／best-first、URL filter、事件雜湊鏈、checkpoint／resume 與 JS-shell 升級判定，但**不是** evidence run 完成證明。

- 先以小預算執行 `public_web_research.py run`；必須明列 allowed domain、page/depth/byte budget。
- 將 PWR raw／derived hashes、event head 與 acquisition metadata 連到本 run 的 `CAPTURE`／`TRANSFORM` events 和 artifacts ledger；PWR candidates 需轉成 v2 candidate schema，再由 include／exclude／defer 審查，不能原樣冒充 checked claim。
- HTTP 空殼頁或動態內容不完整時，依 `escalation_required` 改用 Minis `browser_use`。環境已登入則用該 session 繼續看；未登入或該身份不可見時改其他來源。401／403／429 先降頻並換方法，不換馬甲、不旋轉代理、不破解 CAPTCHA。
- Crawl4AI 僅為可選 backend；iSH 不相容或未安裝時不影響研究。不得為 stealth、proxy rotation 或任意 JS hook 強制安裝。
- Facebook 與 Instagram 仍走各自專用路由；通用 crawler 不取代頁型解析、身份消歧與平台限制。
- 上層仍須完成 source genealogy、lateral reading、精確 locator、反證、競爭假說、checkpoint reviews 與 `validate_research_run.py`。

### 2.2 Instagram 資料自動路由（真人研究預設啟用）

若任務包含 Instagram URL、`@username`、Linktree 的 IG 入口，或身份消歧找到可核對的 Instagram 帳號，**自動讀取並執行** `references/instagram-mcp-research-route.md` 與 `references/session-access-policy.md`。不要把 IG 研究工作退回使用者手動操作，也不要改用 Apify。

先經本機 MCP wrapper 呼叫匿名公開路由：

```bash
python3 scripts/instagram_mcp_client.py profile <username>
python3 scripts/instagram_mcp_client.py research <username> --limit 20
```

- 先 profile，再依 R0／R1／R2 和研究問題擷取最近貼文；預設 20 篇、上限 50 篇。
- wrapper 必須以 MCP stdio 呼叫 `<WORKSPACE_ROOT>/instagram-instaloader-mcp/server.py`，不得在技能內繞過 MCP 直接呼叫 Instaloader。
- 將 wrapper 輸出的完整 JSON 當 raw artifact 保存；逐篇以 canonical source URL／shortcode 建 candidate，保留 captured time、date、caption、metrics、`access_mode` 與限制。
- 匿名 MCP 被擋、空結果或內容不完整時，若環境已有可用登入，改用 `browser_use` 看該身份可見內容，標 `access_mode: logged_in`。兩條都失敗再改其他來源面。
- IG 貼文是第一手自我發布紀錄，不等於外部事實或私人心理；source family、P1/P2/P3、【明示】／【推論】／【待定】規則照常適用。
- 不向使用者要 Cookie／密碼，不把憑證寫進研究檔，不換馬甲、不重試轟炸。
- 若沒有可核對帳號，不猜相似帳號；記錄 `defer`／`blocked`，繼續其他來源面。

這個自動路由不能取代 R1／R2 的其他來源、反證、source genealogy、claim audit 或 validator；Instagram 單一路由不能證明完整人物研究。

### 2.2b X／Twitter 資料自動路由（真人研究預設啟用）

若任務包含 X／Twitter URL、`@handle`、Wikidata `P2002`、Linktree／`rel=me` 的 X 入口，或身份消歧找到可核對的 X 帳號，**自動讀取並執行** `references/x-research-route.md` 與 `references/session-access-policy.md`。不要把 X 研究退回使用者手動翻頁，也不要只用身份鍵就停。

```bash
COL=<SKILLS_ROOT>/source-collectors/scripts/collect.py
python3 "$COL" x-profile <handle>
python3 "$COL" x-timeline <handle> --limit 20
python3 "$COL" x-status 'https://x.com/<handle>/status/<id>'
```

- 先 profile，再取時間線樣本；預設 20 篇、上限 50。單篇 URL 用 `x-status`。
- 公開路由（FxTwitter／oEmbed／syndication）被擋或內容不完整時，若環境已有可用登入，改 `browser_use` 看該身份可見的 X 頁，標 `access_mode: logged_in`。
- 每篇以 `https://x.com/<handle>/status/<id>` 建 candidate；轉載新聞不算第二個 source family。
- syndication 時間線是公開樣本，常不完整；空結果 ≠ 沒有發過文。
- 不向使用者要 Cookie／密碼，不把憑證寫進研究檔，不猜相似帳號。

X 單一路由不能證明完整人物研究。

### 2.3 來源蒐集輪子（YouTube／Wayback／RSS／身份鍵／DOI／PDF）

YouTube、失效頁、影音頁中繼資料、官方 RSS／sitemap、頁面發布日／OG／JSON-LD／`rel=me`、Wikidata 身份鍵、DOI 書目、PDF 文字，或要把已保存的 HTML raw 轉成較乾淨 Markdown 時，**自動讀取並執行** `../source-collectors/SKILL.md` 與 `../source-collectors/references/practitioner-methods.md`。不要把這些工作退回使用者手動操作。

```bash
COL=<SKILLS_ROOT>/source-collectors/scripts/collect.py
python3 "$COL" youtube-transcript '<youtube-url>'
python3 "$COL" media-meta '<video-or-channel-url>'
python3 "$COL" wayback '<url>' --mode newest
python3 "$COL" html-md <raw-html-file>
python3 "$COL" page-meta <raw-html-file>
python3 "$COL" page-date <raw-html-file> --url '<url>'
python3 "$COL" rss '<feed-url>'
python3 "$COL" sitemap '<sitemap-url>'
python3 "$COL" wikidata-search '<name>'
python3 "$COL" wikidata-entity Qid
python3 "$COL" doi-meta 10.xxxx/yy
python3 "$COL" pdf-text <file.pdf>
python3 "$COL" bsky-profile '<handle>'
```

- 先字幕，沒有再取 yt-dlp 中繼資料（不下載媒體）。
- 失效頁用 Wayback 當 discovery lead；快照日期 ≠ 原發布日；正文仍要另存 raw。
- RSS／Atom、sitemap loc、OG／JSON-LD、`rel=me` 是 lead，不是 EXTRACTED claim。
- Wikidata：先 search 再 entity；QID／官網／社群／ORCID 是 `identity_key`，標籤不是傳記。S 類不存內容。
- 有 DOI 先 `doi-meta` 再抓原文；PDF 用 `pdf-text`，原檔當 raw。
- 不接 Instagram Private API、Cookie grabber、私人貼文嗅探、機器人、用戶名枚舉或人臉辨識。
- collector JSON 是 raw／derived artifact，不是 EXTRACTED claim。日期分開事件日／發布日／擷取日／快照日。

### 3. 蒐集、校驗與關係覆蓋
1. 真人研究先讀 `references/real-person-research-protocol.md`；虛構角色按原作／官方版本規則處理。
2. 一手／正典來源：原作、訪談、官方資料、檔案、本人公開言論。
3. 高品質二手來源：學術、權威媒體、編輯完善的資料庫。
4. 社群、粉絲維基、論壇與搜尋摘要是線索來源；查到的未證實、匿名、失效或八卦資料保存為 U 類／`claim`，標明來源、查核狀態與不可當事實使用。S 類只留發現／隔離稽核，不複製內容。
5. 對關鍵資訊至少尋找兩個相互獨立來源；無法交叉驗證就降置信度。
6. 先列「關係覆蓋表」：人物、組織、平台、作品、事件與未知但必要的角色。每筆可證實關係保存方向、動詞、時間範圍、證據與信心；未知關係建立待查節點，不能因缺資料就從模型裡消失或用猜測補上。
7. 記錄版本、時間線與改編差異，避免把不同宇宙或時期混為一談。
8. 對每個核心主張設有限查核預算；原文仍不可得就標 `AMBIGUOUS`／【待定】，不以反覆搜尋或摘要替代證據。

必要時讀取 `references/research-and-inference.md`。

### 4. 建立證據、來源譜系、關係與衝突台帳

先在內部整理，再於需要時摘要呈現：

| 主張或關係 | P級／E級／類型 | 原始來源／中介來源 | 時間範圍 | 反證或歧義 | 信心 | 可推翻條件 |
|---|---|---|---|---|---|---|

先做 **source genealogy**：同一採訪、新聞稿、影片、社群貼文被多站轉載或改寫，只算一個證據家族；標 `source_family_id`、原始來源、轉載鏈與能否取得原文。兩篇引用同一匿名爆料或同一通稿，不是兩個獨立來源。口述、回憶錄、第一人稱訪談同時是「發生過什麼的證據」與「此人如何敘述自己的證據」，兩者分欄保存，不把回憶的情感真實自動等同事件細節準確。

每筆關係至少保存「主體—具體動詞—客體」及方向；活動、爭議、合作等多方資料先建事件節點，將不同說法各自連回來源。未命名但結構必要的人／組織，建立待查節點與缺口，不以沉默刪除。

不可從外貌、星座、單一事件或流行心理標籤直接推導完整人格。推論應形成短鏈條：

> 可觀察事實 → 情境脈絡 → 可能模式 → 替代解釋 → 下一情境的可觀察預測 → 推翻條件 → 信心

### 5. 建立「競爭角色引擎」，不要過早定案

優先提煉五個驅動長篇的核心：
- **外在目標**：角色以為自己必須得到什麼。
- **內在需求**：角色真正需要學會、接受或放下什麼。
- **核心恐懼／壓力源**：他最不願再次發生，或公開材料中反覆迴避的事。
- **錯誤信念／工作假說**：曾保護他、如今可能限制他的信念；真人若無直接材料只能標【推論】或改寫為可觀察的壓力模型。
- **慣用策略與代價**：他怎樣求生／求愛／掌控，以及這方法傷害了誰。

第一次建模至少提出主模型與一個真正能競爭的替代模型；不是只換同義詞。每個模型列：支持證據、反證／缺口、另一情境的可觀察預測、哪項新材料會改變排序。只有原作反覆直接展示或作者已鎖定時，才可收斂為單一引擎。

用一句因果式角色命題總結目前主模型，並標明版本與信心：

> 因為＿＿，他相信＿＿，所以總是＿＿；這讓他得到＿＿，卻失去＿＿。直到＿＿迫使他＿＿。

### 6. 建模，而非貼標籤

先讀 `../character-database-builder/references/minimum-citable-character-card.md`。每個角色交付前都要完成最低可引用卡；尤其能力／技能不可只有名稱。對每項可推動情節的能力，建立：**名稱與版本範圍 → 類別 → 可觀察效果／操作方式 → 明示原理或訓練 → 前提與資源 → 限制／代價／失敗模式／反制 → 證據定位 → 【明示／推論／待定】與信心**。真人只採公開可驗證職業／作品／活動；不要把單次表現擴大成穩定專長。資料不足時列待查卡，不能寫成萬用能力。

分析下列層次，資訊不足時提出 2–3 個彼此有差異的【提案】，並說明各自的戲劇效果：
- 公開面具、熟人面貌、獨處狀態、壓力崩裂面
- 欲望、需求、恐懼、羞恥、罪疚、執念
- 價值排序、道德底線、可被合理化的越界
- 依附方式、信任門檻、控制感來源、常見防衛方式
- 優點如何過度使用後變成缺點
- 自我認知、他人觀感、實際行為三者的落差
- 關係中的權力、交換、依賴、競爭與未說出口的期待
- 語言節奏、禁語、幽默、說謊方式、肢體與生活習慣
- 身體、階級、文化、職業、年代與資源限制如何塑造選擇

除非使用者明確需要，不必硬套 MBTI、九型人格或精神醫學診斷。若使用，只當作輔助語彙，不當作因果證明。

### 6.1 正典缺口補全，不等於發現隱藏人格

若非真人已完成 witness／continuity 研究，仍有新場景所需行為無正典答案，先交給 `../human-behavior-personality-consultant/references/canon-gap-behavior-completion.md`。依 Mind Architecture Gate 與低推定階梯生成：正典窄延伸、scene objective／playable action、人類基準率、競爭 formulation，必要時才新增背景。補全物必標 `CANON_CONSTRAINED_INFERENCE／HUMAN_PRIOR／PERFORMANCE_HYPOTHESIS／ADAPTATION_PROPOSAL`；作者核准後只成為本小說 `AUTHOR_CANON`，不得回寫原作 witness／claim。

### 7. 建立情境反應模型，並做場景壓力測試

不要把固定八題問卷當完成條件。先從**本故事最可能發生、最能區分競爭模型**的 3–5 種情境取樣，再視需要加入通用壓力情境：
- 被公開羞辱
- 被親密者背叛
- 無人知情且可獲利的道德誘惑
- 面對弱者求助
- 權力突然增加或失去
- 愛與核心目標衝突
- 舊創傷被相似情境觸發
- 計畫失控、疲憊、生病或資源匱乏

每個重點情境寫出：**當下目標／可見選項 → 第一衝動 → 外在行為 → 內在理由 → 抑制／保護因素 → 後續代價 → 事後自我解釋**。反應須依情境強度、關係、資訊與身心狀態改變，不要把角色寫成固定演算法。

依層級執行下列驗證：L0 可明示未測試並保留 `MODEL_DRAFT`；L1 至少一項；L2 至少三項，且必含反例測試與對比場景或聲音盲測。通過必要測試後才可升為 `SCENE_TESTED`：

1. **對比場景**：同一核心威脅放進弱／強情境，或親密／權威兩種關係，確認反應會變但仍能辨認同一人。
2. **不可替換測試**：遮掉角色名後，若同類型角色都能無痛替換，補上此人的特定資源、盲點、語言、關係史或代價。
3. **聲音盲測**：寫 3–6 句無標籤台詞或一小段內心／行動，檢查能否靠詞彙、注意焦點、迴避方式與節奏辨識；不能只靠口頭禪、口音或怪癖。
4. **反例測試**：主動找一個不符合主模型的正典／公開行為；判斷是狀態變異、強情境、成長、模型錯誤或仍不可知，不可把所有反例都合理化掉。
5. **情節摩擦測試**：讓角色面對一個會妨礙作者原定情節的選擇。若模型總會配合劇情，表示角色能動性不足；若角色拒絕情節，應先改事件條件或記錄作者覆寫，而非硬改人格。

已有正文時，優先從實際場景做診斷，不重新填完整問卷。記錄 `test_id`、輸入、預期區分點、結果、失敗原因與模型修訂；測試後不得假裝初版從未錯過。

若輸出結構化 JSON 或準備入庫，執行：

```bash
python3 scripts/validate_character_profile.py <profile.json>
```

validator FAIL 時不得標 `SCENE_TESTED`／`REVISION_CALIBRATED` 或交給重要場景使用；L0 無測試可 PASS，但必須保留 `MODEL_DRAFT` 警告。

### 8. 設計人物弧與一致性護欄

提供：
- 起點狀態與防衛性均衡
- 三個逐級加壓的關鍵考驗
- 中點認知裂縫
- 最終選擇及其代價
- 正向弧、負向弧或平弧的適用方案
- 「即使改變也不會消失」的核心特徵
- 角色絕不會做、除非滿足特定條件的行為
- 容易寫崩的地方與修正提示

### 9. 交付報告與停止規則

預設依 `character-profile-template.md` 輸出，但只填本次深度層級必要內容。先給高密度摘要，再給證據、競爭模型、驗證結果與可直接寫進場景的內容。完整模板是上限，不是每次最低字數。

當以下條件同時成立即可停止，不為「更完整」繼續堆資料：
- 新 R1／R2 evidence run validator 通過；must routes 已執行或有可辯護受阻紀錄；最後指定窗口中的不同 route 無新 source family；P0 claims 全部閉合並完成 claim audit；沒有未處理的高價值 defer。舊 v1 manifest 或來源清單只能標 legacy／`RESEARCH_INCOMPLETE`，不能證明 v2 完成；
- 本次 1–3 個故事問題已有可用答案或誠實標為不可知；
- L0／L1／L2 對應必填已達成；
- 每個核心推論有證據家族、替代解釋與推翻條件；
- 主要能力、關係與版本沒有會讓場景失真的 P0 缺口；
- L1／L2 已依層級完成必要測試並回寫模型；L0 若未測試，已誠實保留 `MODEL_DRAFT` 與 `required_before_story_use`；

若新增資料只增加履歷、外貌或趣聞，卻不改變角色下一步選擇、關係、能力、風險、聲音或版本判定，停止擴寫並放入附錄／待查。

真人研究分三層交付：
1. **核查層**：時間線、P級、關係圖、來源與衝突；U 類只能作明確標示未證實的 claim／待查線索。
2. **分析層**：行為模式、替代解釋與信心；不把 P2／P3／U 類資料當作人格診斷。
3. **創作層**：場景反應、人物弧、虛構化方案；清楚標為【提案】。
4. **受限線索層**：保存 U 類台帳與 S 類發現／隔離稽核，僅供作者交叉核對、避免關係遺漏或決定虛構分支；不可當真人事實或搬進正文。

研究型報告末尾加入：
- 來源清單（標題、發布者、日期、URL；能附段落或頁碼更好）
- 關係覆蓋與未命名待查節點
- 不確定性、衝突與版本差異
- 哪些設定是【提案】而非資料事實

原創型報告末尾加入：
- 仍需作者拍板的 3–7 個高影響問題
- 建議的下一步：關係網、人物弧、試寫場景或一致性測試

## 品質檢查

交付前確認：
- 非真人是否先建立 target character instance、WEMI witness 與 continuity map，沒有把同名跨版本角色先合成人格？
- primary story text、official paratext、production witness、creator statement、reception／fan navigation 是否分層；摘要頁沒有代理完整正文？
- locator 是否符合媒介：章頁段落、漫畫 panel、影視 cut/timecode/shot、遊戲 build/save/route/node、舞台 production/performance/cue、民俗 attested variant？
- 翻譯、字幕、配音、scanlation、連載／單行本、劇本／成片、patch／DLC、prompt book／場次與 datamine／cut content 是否各自標版本與 canon status？
- `CROSS_VERSION_STABLE` 是否每個 continuity 有 primary witness、保留 per-version claims 並通過 VERSION_CONTRADICTION_AUDIT？
- 是否把研究前 protocol 與事後 evidence run 分開，protocol revision 有舊 hash／理由，而非事後補成預言？
- 每個 `searched` 是否由 hash-chained 實際事件推導；候選的 include／exclude／defer 是否完整，沒有從搜尋結果直接跳到結論？
- raw artifact 是否不可變；OCR／轉寫／翻譯／摘要是否有 derived lineage、工具版本、input/output hash 與人工校對？
- 是否做 START_CHALLENGE／MIDPOINT_REVIEW／CLAIM_AUDIT；重大真人主張是否有真正獨立或隔離重抽，而非普通重讀？
- known-item holdout／search review 是否揭露漏搜；query diversity、source family yield、P0 closure 與飽和是否由 validator 計算？
- 負向證據是否先證明該紀錄理應存在且資料集覆蓋相關時空；一般搜尋沒結果沒有被寫成不存在？
- 是否分開決定人物模型 L0／L1／L2 與研究作業 R0／R1／R2？
- 是否完成身份／版本消歧、來源地形圖、多語 exact queries、原始證據 locator、引文／FAN 擴展、反證與飽和紀錄？
- 搜尋摘要、AI 回答、wiki／粉絲整理是否只作導航？本地 artifact 是否有 hash？
- 有可核對 Instagram 帳號時，是否已自動擷取 profile／posts（匿名 MCP 或已登入瀏覽器），保存完整 raw capture、canonical URL、shortcode、發布日、擷取日與 `access_mode`？是否把限流／工具失敗記為 blocked／error 並改換方法，而沒有當成「沒有資料」？
- 有可核對 X／Twitter handle 時，是否已走 `x-profile`／`x-timeline`／`x-status`（公開路由或已登入瀏覽器），保存 status URL、text、created_at 與 `access_mode`？是否把不完整時間線標成樣本，而沒有當成「沒有發過文」？
- YouTube／影音是否已走 `source-collectors` 取字幕或中繼資料？失效頁是否查過 Wayback？有 RSS／sitemap 是否當發現層？頁面日期／OG／`rel=me` 是否只當 lead？Wikidata 是否 search 後再 entity，QID 有無被當成傳記？DOI 是否先取書目再抓原文？PDF 是否保留原檔？collector JSON 有無當成 claim？事件日／發布日／擷取日／快照日是否分開？
- 是否先決定 `lead／major_supporting／minor_functional`、工作階段與 L0／L1／L2，而不是不分重要度填滿模板？
- 是否把問卷／人物訪談當探索工具，而非把填滿欄位當成深度證明？
- 是否已完成最低可引用卡？能力／技能是否有「效果、前提、限制／代價、版本範圍、證據或推論鏈」，而非只有名稱？未知是否明示為【待定】？
- 是否把同一原始材料的轉載辨識為同一 `source_family`，沒有製造假交叉驗證？
- 是否把「事實、推論、提案」清楚分開？
- 角色引擎是否至少考慮一個真正競爭的替代模型與推翻條件？
- 每項重要性格是否有行為證據、觸發與代價？
- 是否至少執行一個對比、聲音盲測、不可替換、反例或情節摩擦測試，並保留修訂結果？
- 角色是否同時具備能力、盲點、矛盾與能動性？
- 私下樣貌是否為有依據的模型，而非窺私式臆測？真人 P1／P2／P3 是否具來源與必要性？U 類是否明標未證實／風險／不可作事實，S 類是否只留隔離稽核而沒有內容或可識別細節？
- 關係覆蓋表是否涵蓋重要人物、組織、平台與事件？每條關係是否有方向、動詞、時間、證據與信心；未知結構是否有待查節點？
- 過往是否真的塑造現在，而非裝飾性悲慘背景？
- 不同關係與壓力下，反應是否有一致核心但非機械重複？
- 人設能否自然產生場景、衝突與選擇？
- 是否避免把弱勢身分、心理狀態或創傷當成廉價反派理由？
- 是否列出最可能的反解釋與不確定性？

## 與通用關係圖譜、世界觀、行為心理顧問及小說寫作技能協作

Instagram MCP 與 X 研究路由先於人物建模執行；完成 raw capture 與 claim／source genealogy 後，才交給人物、關係圖譜與資料庫技能。公開頭像／作品視覺若要入庫比對，交給 `character-database-builder` 的 `visuals/` 與 `ingest_public_visual.py`；圖譜只存路徑、hash 與來源 URL。

完成角色檔後，若專案使用圖譜，載入同層級技能 `../knowledge-relationship-graph/SKILL.md`，將人物別名、親屬／社會／組織關係、形成事件、祕密／主張與來源證據寫入 Graphify 相容圖譜；【推論】必須標 INFERRED／AMBIGUOUS，不得當成明示關係。

若角色的階級、法律地位、職業、教育、語言、信仰、出生地或世界事件會影響人設，載入同層級技能 `../novel-worldbuilding-architect/SKILL.md`，把世界約束寫進角色的可見選項、資源與行為形成史；不要把文化當成固定性格。

遇到下列情況時，載入同層級技能 `../human-behavior-personality-consultant/SKILL.md`，依其 Actor／Agent／Author 與多時間尺度因果框架進行二次審核：
- 關鍵行為轉折、背叛、黑化或創傷反應可能缺乏鋪墊
- 作者詢問「這樣做合不合理／符合心理嗎」
- 需要分析壓力、生理狀態、成長環境與制度如何共同影響行為
- 人設描述完整，但場景中的實際選擇不一致

不要為一般簡單人設強制增加完整心理審核；只在它能改變結論時使用。

若接續長篇小說寫作，載入同層級技能 `../long-form-novel-writer/SKILL.md`，並先輸出或保存以下「交接包」：
1. 一句角色命題
2. 一句角色命題（主模型）＋至少一個競爭模型與推翻條件
3. 關係動力摘要
4. 語言與行為指紋
5. 情境反應規則
6. 人物弧節點
7. 不可違反的連續性約束
8. 事實／推論／提案標籤表
9. 角色模型狀態：`MODEL_DRAFT`／`SCENE_TESTED`／`REVISION_CALIBRATED`
10. 已執行測試、失敗／反例、尚未驗證項目與 `required_before_story_use`
11. 主／替代引擎及會改變排序的新證據
12. evidence run：run ID／protocol hash／run-summary hash、P0 closure、benchmark misses、checkpoints、defer／blocked、`RESEARCH_COMPLETE|RESEARCH_INCOMPLETE|SCOPE_LIMITED|LEGACY_V1`
