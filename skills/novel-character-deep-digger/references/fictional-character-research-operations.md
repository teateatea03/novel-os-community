# 非真人角色研究作業：作品見證本、版本與媒介證據

本規範適用 `novel`、`anime`、`film` 及 `other` 中的 game／stage／myth／mixed-media／original。它延伸 `research-evidence-run-v2.md`：真人以「來源是否可信、人物身份是否同一」為中心；非真人首先要回答的是**哪一個作品、哪一個版本、哪一個載體實例、哪一條 continuity 中的角色**。

## 1. 基本觀念：角色不是獨立於文本的單一人

非真人角色主張必須先綁定 `witness_id`。借用 IFLA LRM 的 Work／Expression／Manifestation／Item 層次，但按敘事研究擴充：

- **Work**：抽象作品／故事創作，例如《攻殼機動隊》原作漫畫這個作品。
- **Expression**：具體實現，如日文漫畫文本、英譯本、1995 電影剪輯、TV 動畫一季、舞台演出版本。
- **Manifestation**：特定出版／發行載體，如某出版社某版、Blu-ray cut、Steam build、串流平台字幕版。
- **Item／Instance**：研究者實際看的那一本、檔案、光碟、串流播放、遊戲安裝或演出場次。
- **Witness**：本研究可定位與引用的具體見證本；可能是一個 expression，也可能只能精確到 manifestation／instance。

不能只寫「官方資料」或「原作」。最低 witness card：

```json
{
  "witness_id":"W1",
  "work_id":"work:gits-manga",
  "expression_id":"expr:gits-manga-ja-serialized",
  "manifestation_id":"mani:kodansha-edition-x",
  "instance_id":"item:research-copy-or-stream-session",
  "medium":"novel|manga|anime|film|game|stage|myth|other",
  "title":"...",
  "creator_roles":[{"name":"...","role":"author|artist|director|writer|developer|translator"}],
  "language":"...",
  "publication_or_release":"...",
  "platform":"...",
  "region":"...",
  "edition_cut_build_patch":"...",
  "continuity_id":"...",
  "canon_authority":"primary_text|official_paratext|licensed_adaptation|commentary|fan_navigation",
  "access_mode":"owned|library|licensed_stream|official_web|archive|user_supplied",
  "completeness":"complete|excerpt|summary_only|unknown"
}
```

`summary_only` witness 不能支撐逐場行為、聲音、反例或「從不／總是」主張。

## 2. 先建 Canon／Continuity Map，再搜尋角色

每個 franchise 先畫版本樹，不先合成人格：

```text
source work
├── same-continuity sequel/prequel/side story
├── adaptation / retelling
├── transmedia extension
├── reboot / remake
├── parallel universe / multiplicity
├── localization / translation / censorship variant
└── fan / unofficial / promotional non-story material
```

關係類型：

- `SAME_CONTINUITY`
- `PREQUEL_OF`／`SEQUEL_OF`／`SIDE_STORY_OF`
- `ADAPTS`：重述另一作品，預設不共享全部事件。
- `EXTENDS`：在同故事世界增加材料，但需官方 continuity 依據。
- `REBOOTS`／`REMAKES`
- `PARALLEL_TO`
- `LOCALIZES`／`TRANSLATES`
- `CENSORS_OR_REEDITS`
- `INSPIRED_BY`
- `NON_CANON_PROMOTION`
- `UNKNOWN_RELATION`

「官方製作」不等於同一 continuity；「同名角色」也不等於同一角色實例。若官方沒有宣布 canon hierarchy，研究者不得自行發明唯一正史；只能按 witness／continuity 報告。

## 3. 證據角色：文本、旁文本、解讀分開

### A. Primary story text

作品本身可直接支撐：角色說了／做了什麼、敘事者怎麼描述、畫面／聲音如何呈現、遊戲在某路線／狀態發生什麼。

### B. Official paratext

封面文案、官方網站、設定集、角色頁、press kit、片尾 credits、patch notes、導演／作者 commentary。可支撐創作意圖、職稱、設定、版本與製作背景，但**不能自動覆蓋成片／出版文本的相反呈現**。角色簡介是摘要，不代理完整正文。

### C. Production witness

草稿、手稿、分鏡、劇本、shooting script、prompt book、設計稿、刪除場景、cut content。它可證明創作過程或替代方案；只有進入發布作品或被官方明定 canon，才是角色已發生事實。

### D. Reception／navigation

學術評論、專業評論、百科、粉絲 Wiki、攻略、逐集摘要、論壇。適合導航、術語、集數與爭議地圖；仍需回 primary witness。粉絲共識可以是 reception claim，不能變 canon claim。

### E. Creator statement

作者／導演／編劇／演員／聲優訪談依角色權責分級。作者對自己的意圖有高價值，但「意圖」與「文本實際呈現」分開；演員或聲優的理解是 performance interpretation，不是其他版本角色傳記。

## 4. 各媒介怎麼挖

## 4.1 小說、網路小說、輕小說

### 證據單位

- 卷／冊、章、節、頁、段落；電子版用章節＋段落首句／location，不只用可漂移頁碼。
- 記 POV、敘事層、說話者、引語範圍、時間位置。
- 區分 narrator assertion、character belief、quoted document、dream／vision、rumor、free indirect discourse。

### 工具與路線

- 出版社／作者頁、圖書館目錄、ISBN、版權頁、目次。
- 合法取得的 EPUB/PDF/純文字：先 hash；建立章節索引、角色提及 concordance、引語定位；OCR 只用於掃描本並人工核對核心引文。
- TEI／critical apparatus 思路保存不同 witness 的 variant readings；不要把初版、修訂版、譯本句子混成一條。
- 搜索時除了姓名，加入作品原名、卷章標題、獨特短句、敘事事件、別名與譯名。

### 特有陷阱

- 譯者新增語氣被誤認為原角色聲音。
- 第一人稱／不可靠敘事者的自述被當客觀世界事實。
- 網路連載、實體修訂、文庫版新增段落未分版。
- 搜尋 snippet／讀者整理取代付費正文；不能取得正文就降級 `summary_only`。

## 4.2 漫畫、圖像小說、Webtoon

### 證據單位

`volume/chapter/page-or-scroll-anchor/tier/panel/balloon`，並保存閱讀方向。角色行為不是只讀台詞：需同時記構圖、視線、姿勢、表情、panel sequence、gutter、頁跨／scroll pacing 與誰的 speech balloon。

### 工具與路線

- 出版者、作者、單行本 ISBN、連載期號、官方數位平台。
- 對合法研究頁面建立 page/panel log；OCR 只協助找字，必須回看圖像與 balloon attribution。
- 版本比較：連載版→單行本修訂、黑白→彩色、本地化翻轉、審查、重排、Webtoon scroll 轉頁版。
- 動畫不是漫畫的「影音證明」；另建 adaptation witness。

### 特有陷阱

- 只抽台詞而漏掉畫面反例。
- panel reading order 判錯。
- fan scanlation／嵌字改寫角色語氣。
- 封面、四格附錄、作者塗鴉、宣傳圖的 canon 狀態未標。

## 4.3 動畫、電影、影集

### 證據單位

`season/episode/cut_or_release/timecode-range/shot`；必要時建立 shot-sequence log：鏡號、起訖時間碼、景別、動作、剪接、畫面資訊、對白、聲音／音樂。時間碼須綁定 cut、framerate 或串流版本；不同片頭／廣告插入會漂移。

### 工具與路線

- 正式發行／授權串流／影碟、官方 episode guide、credits、production notes。
- 合法本地檔可用 ffprobe 記 duration/codec、ffmpeg 抽關鍵幀／音訊；字幕作導航，核心引文回聽原語音並記 speaker。
- screenplay、shooting script、storyboard、deleted scene 與 final cut 分開；final film 優先描述實際成片，劇本支持製作見證。
- 比較 theatrical/director’s/TV/international cut、dub/sub、審查剪輯、重製與不同 framerate。

### 特有陷阱

- 字幕把含混語氣明確化；配音版重寫口吻。
- 演員訪談混入角色事實。
- production order、broadcast order、故事時間順序混淆。
- 官方角色頁摘要被拿來支撐未展示的心理。

## 4.4 遊戲、互動小說、Visual Novel

### 證據單位

`title/platform/region/build-or-patch/DLC/save-state/route/quest/node/dialogue-choice/outcome`。同一句台詞可能只在特定好感、隊伍、旗標、難度或過往選項出現。

### 工具與路線

- 官方遊戲／patch notes／manual／codex／credits／developer commentary。
- 研究 protocol 記研究者熟悉度、平台、版本、遊玩邊界、route selection、play time、save files 與選項；符合 DiGAP 的反身性與透明度。
- 保存 gameplay capture、save hash／state description、quest log、node IDs（若遊戲公開）、選項與結果。
- wiki／攻略導航 missable content；需回遊戲內重現，或標 `secondary_only`。
- Datamine／解包只在合法、授權與安全範圍；分 `shipped_reachable`、`shipped_unreachable`、`cut_or_unused`、`developer_tooling`。存在檔案中不代表玩家正典。
- Live-service 必須記 server、season、patch、活動期限與伺服器關閉風險。

### 特有陷阱

- 玩家選擇／avatar 行為誤當固定角色性格。
- gameplay mechanic 與 diegetic 能力混淆。
- patch 後台詞／能力改動覆蓋舊版本。
- 把 datamine、beta、leak、unused voice 當已發生劇情。
- 影片 walkthrough 沒記 uploader 的 route、mods 或剪輯。

## 4.5 舞台、音樂劇、廣播劇

### 證據單位

劇本版本＋production＋場次。舞台角色存在於每一製作與每場演出；同一劇本的 blocking、節奏與表演解讀可不同。

### 工具與路線

- published script、prompt book、stage manager cues、導演本、節目冊、cast list、服裝／佈景稿、正式錄影、照片、評論與口述史。
- 記 venue、date、cast、understudy、production、act/scene/page/cue/timecode。
- Prompt book 是某製作的重要工作見證，不自動代表所有演出。
- 廣播劇記 episode／track／timecode、script、聲音與 narrator 層。

### 特有陷阱

- 劇本角色與某演員詮釋無聲合併。
- bootleg 片段缺場次／上下文。
- live performance 的短暫變化被當永久正典。

## 4.6 神話、傳說、民俗、公版角色

這類通常沒有單一作者與唯一 canon。研究單位是 **attested variant／recorded telling**，不是現代百科合成人物。

### 工具與路線

- 最早／重要文本、田野筆記、錄音、直接逐字稿、地方語言版本、採集者／講述者／地點／日期。
- ATU 用於 tale type、Motif-Index 用於敘事元素導航；分類號不是原始證據，也不表示所有 variant 共享特徵。
- 分開古典文獻、宗教文本、地方口傳、後世文學改寫、現代影視／遊戲。
- 翻譯與殖民採集脈絡需要記錄；不要把不同文化的「相似神」合成同一人。

### 特有陷阱

- 把後世最流行版本倒灌成古代信仰。
- 用 archetype／motif 取代具體文本。
- 把不同地域、時代、講述者 variant 排成虛假的唯一時間線。

## 4.7 原創角色

原創角色沒有外部 canon 要「挖」。研究分成兩條：

1. **作者正典稽核**：作者設定、草稿、已寫場景、刪稿、決策與 retcon；以專案版本和 canon status 管理。
2. **外部 plausibility research**：職業、制度、文化、年代、地理、身體與 lived experience；這些只約束角色可行選項，不會自動生成角色內心。

不要搜尋「某類人通常怎樣」後把群體平均貼成角色人格。敏感經驗需要多份 lived-experience／專業來源與 sensitivity review，但仍是創作參考。

## 5. 非真人 Canon Matrix

每個 R1／R2 `protocol.json` 增加：

```json
{
  "fictional_scope": {
    "target_character_instance":"char:motoko@sac",
    "primary_continuity_ids":["gits-sac"],
    "excluded_continuity_ids":["gits-1995","gits-arise"],
    "allowed_relation_types":["SAME_CONTINUITY","SEQUEL_OF"],
    "languages":["ja","zh-Hant"],
    "translation_policy":"原文優先；譯文作導航；差異建 variant claim",
    "spoiler_boundary":"...",
    "rights_access_boundary":"..."
  },
  "witnesses": [],
  "canon_matrix": []
}
```

每個 claim 增加：

- `witness_ids`
- `continuity_ids`
- `canon_status`: `TEXT_CANON|OFFICIAL_PARATEXT|PRODUCTION_WITNESS|ADAPTATION_ONLY|LOCALIZATION_VARIANT|CUT_UNUSED|RECEPTION|FAN_NAVIGATION|AUTHOR_CANON|PROPOSAL`
- `narrative_level`: `diegetic_fact|narrator_assertion|character_belief|rumor|dream_vision|performance_choice|gameplay_state`
- `version_portability`: `SINGLE_WITNESS|SAME_CONTINUITY|CROSS_VERSION_STABLE|CONFLICTING|UNKNOWN`

## 6. 跨版本穩定核心 Gate

只有符合以下條件，才能標 `CROSS_VERSION_STABLE`：

1. protocol 明列比較哪些 continuity／witness，不以「主要版本」含混帶過；
2. 每個被比較 continuity 至少一份足以支持該 claim 的 primary story witness；官方摘要不能代替正文；
3. 沒有已知明確反例，或反例已使 claim 改為條件式；
4. 用最小共同命題，不把一版的形成史／戀情／能力原因外推；
5. 至少做一個 `VERSION_CONTRADICTION_AUDIT`，主動搜尋相反呈現；
6. 報告同時保存 per-version claims；跨版本 claim 是衍生比較，不覆蓋它們。

例如：「多版素子皆為高能力義體／cyberbrain 行動者」可能穩定；「她因出生即無自然身體而恐懼失去自主」只屬 ARISE 或創作推論，不能跨版。

## 7. 非真人 Evidence Run 必要 route

### R1

- 至少一個完整 primary witness route；
- 一個版本／書目／release metadata route；
- `START_CHALLENGE`、`CLAIM_AUDIT`；
- 每個 P0 claim 有精確媒介 locator。

### R2 單版本

- 完整 primary corpus 或明示 sampling frame；
- paratext／production／creator route 至少一種；
- counterexample search；
- `CANON_SCOPE_REVIEW`＋原有三 checkpoint。

### R2 跨版本

- continuity map；
- 每個納入版本的 primary witness；
- adaptation／translation／release comparison；
- `VERSION_CONTRADICTION_AUDIT`；
- per-version claim coverage 與 stable-core derivation。

## 8. 搜尋與工具的合理降級

- 受版權保護正文不可取得：保存書目與 access attempts，標 `summary_only/UNAVAILABLE`；不以盜版全文或模型記憶補原文。
- 使用者提供合法片段：hash、記 edition／context／頁前後界線；片段不能支撐全作「總是」。
- 字幕／OCR／fan transcript：作 derived/navigation；核心引文回 primary audio/image/text。
- Wiki API／Fandom：可批次找 episode、quest、aliases、citations；不可把 infobox 當 canon。
- 網路搜尋適合找官方頁、版本、訪談與書目；不適合替代作品觀看／閱讀／遊玩。

## 9. 非真人研究停止條件

除了 evidence run v2 的 P0 closure：

- 每個納入 continuity／witness 的 sampling frame 已完成或明示缺口；
- 版本矩陣中沒有未處理的 identity merge；
- primary evidence 密度足以支撐交付深度；若只有摘要，模型深度必須降級；
- adaptation、translation、cut／patch、route 差異已處理；
- 跨版本 stable claims 通過 contradiction audit；
- 新資料只增加同一場景轉述／粉絲整理，而不改變版本、行為、能力、關係或聲音時停止。

## 10. 實作依據

- IFLA Library Reference Model：Work／Expression／Manifestation／Item 分層。
- TEI Critical Apparatus：witness、lemma、variant reading 與 canonical reference 思路。
- Textual criticism／scholarly editing：版本見證本與異文，不把「最舊」自動當唯一正確。
- Comics studies：page／spread／panel sequence、gutter、閱讀路徑與圖文共同 close reading。
- Film studies sequence analysis：shot-by-shot、timecode、mise-en-scène、editing、sound。
- Digital Game Analysis Protocol (DiGAP)：研究者位置、選本、版本／平台、遊玩邊界、coding 與透明報告。
- Game preservation／citation practice：platform、build/patch、DLC、save state、server 與 emulation 狀態。
- Theatre archives：script、prompt book、production files、cast、venue、performance recording。
- Folklore studies：ATU tale type、Motif-Index 與 primary collected variants。
- Transmedia／adaptation studies：continuity、multiplicity、adaptation 與 extension 分流。
