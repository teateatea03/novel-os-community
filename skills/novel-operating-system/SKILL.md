---
name: novel-operating-system
version: 2.15.9
description: 當使用者要求寫長篇小說、續寫／重寫章節、建立小說專案、補完／研究斷更或未完成小說、推演原作者意圖與替代結局、打造故事世界、建立／保存／更新／查詢小說世界資料庫、世界觀知識庫、世界設定圖譜、地點／派系／資源／規則資料庫、建立／保存／更新／查詢／比較特殊物資料庫（道具、鎧甲、機體、機器人、載具、武器、神器、裝置與裝備系統）、深挖角色、分析人物行為、設計文風、管理時間線與伏筆、建立角色資料庫或關係圖譜、或要求讓小說文字更像人寫、去除 AI 味、校準台灣繁中與角色聲音時使用。這是整套 Novel OS 的單一入口：先協調角色主體分類（real／novel／anime／film／other）與版本正典，再自動協調特殊物版本／能力／限制／生命週期、未完成作品證據與分支、長篇連續性、角色研究、行為心理、世界觀設計、世界資料庫持久化、風格、人味編輯、Graphify 關係圖譜、可追溯角色資料庫與持久互動狀態；正文、正典、世界資料、特殊物狀態、作者意圖證據、權利狀態與作者決策以可驗證的專案檔案持續管理。
---

# Novel Operating System

此技能是小說系統的**唯一入口與調度層**。依需求呼叫相鄰專業技能；不需要每個任務都啟用全部模組，但任何會改變正典的工作都必須維持狀態、來源與可追溯性。

## 現實狀態與連續性強制層
每次章節或互動回合，先載入 `novel-reality-state-engine`：從事件帳本與 Graphify 影響子圖計算時間／資源／生理負荷／認知容量，生成 Reality Card，依 Feeling → Thought → Action 推導角色的可行反應，再生成正文。生成後必須跑 Reality Gate；Gate 未通過時不得把草稿寫入正典。記憶摘要不能取代狀態計算，角色的身體反應不等於慾望、信任或同意。



所有由 Novel OS 新建或更新的角色、特殊物、世界、地點、事件、組織與關係圖譜節點，都必須保留原始 `label`，並在名稱含非中文文字或中外文混合時建立 `properties.name_zh`（台灣繁體中文查詢名稱）。名稱處理優先序固定為：**有可靠來源的官方中文譯名優先；沒有官方中文譯名時，依原文可靠讀音採台灣繁體中文音譯，不自行意譯**；必要時可括註原名或型號。同步保存 `name_zh_language`、`name_zh_provenance`、`name_zh_source_label`。查詢、列表、消歧要比對原名、aliases 與 `name_zh`；只有在原文讀音也無法可靠判讀時才填 `UNKNOWN`，不能硬猜或以自行意譯代替。`name_zh` 是輔助查詢欄位，不取代正典名稱、ID 或原始來源。

任何角色研究、行為分析、角色資料庫寫入或長篇專案建立，先建立 `minis.character-profile.v2` 分類卡：`subject_category` 只能為 `real`、`novel`、`anime`、`film`、`other`；另記 `subject_subcategory`、`subject_kind`、`source_medium`、`canon_scope`、`version_scope`、`franchise`、`classification_basis` 與 `classification_confidence`。分類規範由 `novel-character-deep-digger/references/character-category-taxonomy.md` 統一管理，資料庫欄位由 `character-database-builder/references/character-category-schema.md` 對應。

角色研究由 `novel-character-deep-digger` v1.9+ 分開決定人物模型 L0／L1／L2 與研究作業 R0／R1／R2。所有新 R1／R2 使用 `minis.character-research-run.v2`。若非真人，再強制建立 target character instance、Work／Expression／Manifestation／Item witness、continuity map 與媒介 locator；官方摘要／Wiki 不能代理 primary story text，跨版本人格需 VERSION_CONTRADICTION_AUDIT。

涉及公開 HTTP(S) 網頁擷取、站內探索、sitemap／RSS、LLM-ready Markdown 或可恢復 acquisition 時，載入 `public-web-research` v1.0+：先走安全 HTTP 基線，必要時升級到 Minis `browser_use` 公開檢視，Crawl4AI 只作相容環境的可選 backend。任何 crawler 產出只能是 raw／derived artifact 與 unreviewed candidate；不得跳過 Evidence Run v2 的 include／exclude／defer、source genealogy、claim audit、反證與 validator，也不得直接寫 Graphify。Facebook／Instagram 仍由專用技能路由，不以通用 crawler 取代或繞過平台限制。

若合理研究後仍為 `CANON_UNKNOWN`，但續寫／改編必須讓角色行動，路由至 `human-behavior-personality-consultant` v1.4+ 的 canon-gap completion。先做 HUMAN_BASELINE／HUMAN_DERIVED／ANTHROPOMORPHIC_ANALOGY／NONHUMAN_MODEL／SYMBOLIC_OR_FLAT Gate，再按正典窄延伸→scene objective／playable action→人類先驗→競爭 formulation→最小 backstory 生成候選。心理學只能補可寫性；HUMAN_PRIOR／PERFORMANCE_HYPOTHESIS／ADAPTATION_PROPOSAL 不得回升原作 canon，作者核准後只成為本專案 AUTHOR_CANON。重大候選需 Scene Lab、Prediction Lock 與章後 resolution。

- 真人／歷史人物：公開資料與隱私邊界。
- 小說角色：文字正典、敘事者與版本。
- 動漫角色：漫畫、動畫、動畫原創、季別、重製、劇場版。
- 電影角色：電影版本與演員本人分離。
- 其他：遊戲、舞台、神話、原創、跨媒體或未消歧。

未完成分類不可直接把推論升格為資料事實；版本改變先 snapshot，真人原型與改編角色分開建檔。


小說中的角色反應與行為，原則上盡量貼近現實。先依角色在設定世界中當下可知的資訊、身心狀態、過往學習、關係／權力、資源／制度與可預見風險推導反應，再考慮戲劇效果。不得為了推動情節，讓角色無鋪墊地突然失智、失控、勇敢、冷酷、告白、原諒、背叛，或做出違反既有人格與利益結構的選擇。

### 行為校準強制閉環

Novel OS 必須實際載入 `human-behavior-personality-consultant` v1.3+，不可只引用其名稱。流程固定為：Reality Card 限制可用能力 → Evidence E1–E6 → Actor 狀態分布／Agent／Author → 強中弱情境 → 維持／保護／抑制 → 候選與反事實 → 重大節點 Prediction Lock → 正文／互動裁決 → Resolution → 更新 if–then 模型。

長篇新專案必須建立 `behavior-calibration/predictions.jsonl` 與 `resolutions.jsonl`；重大節點缺 Lock、Lock hash 失配、已知結果回填舊 Lock，或未達門檻卻輸出精細百分比時，Character Behavior Gate 必須 FAIL，不能升為正典。候選預設使用序位或寬區間；只有同角色相似情境至少 5 筆、已解決預測至少 10 筆且有校準紀錄時，才可使用合計 100% 的精細百分比。作者選擇另記 `author_override`／`selected`，不算預測命中。

互動模式不必為每個微反應建 Lock；只有 NPC 的不可逆承諾、背叛、重大暴力、道德越界、關係斷裂或其他高風險自主決策才強制使用。一般回合使用簡版 if–then 與 Reality Gate，避免分析流程拖慢敘事。

戲劇張力應主要來自真實人物在有限資訊與壓力下的誤判、迴避、妥協、合理化、沉默、延遲反應與累積後果。現實優先不等於所有人反應相同，也不禁止奇幻、荒誕或低機率事件；但非典型／戲劇化行為必須有足夠前因、當下條件、可見選項與代價。若作者指定低機率方向，補足其成立條件，不直接用「不合理」拒絕創作。

### v2.7 production closure

v2.7 完成 production writing loop 與泛化驗證：Project Readiness 聚合 kernel／projection／memory／context／storylet／command／quality；lease-fenced author commands 只有 approval 可跨 canonical boundary；Quality Eval v2 將 explicit author feedback、observed revision 與 workflow proxy 完全分離；新 canonical events 強制 `minis.event-semantic-delta.v1`，以 operations hash 綁定 typed effects 與非空摘要。新建傳統長篇從 active `ProjectRuntimeAdapter` authority 起步，舊專案則必須來源化 migration。隔離第二專案 contract probe 與 40 章、133,600 字、40 typed events、中段知識反轉／cascade pilot 已通過 conformance、integrity 與 replay。

## 模型執行層相容性
模型可替換，但 Novel OS 的事件帳本、Graphify、Reality Card／Gate、Feeling → Thought → Action、長篇連續性與正典同步不可因模型切換而消失。每次切換模型、供應商或 endpoint，先載入 `novel-model-capability-compatibility`，執行能力探測與切換前後回歸；純文字成功不代表工具／狀態／agent loop 成功。若新模型低於必要 L4／L5，必須明示降級、保留外部狀態並啟用相容 fallback，不得靜默成為 active model。

## Host-first 通用 runtime（v2.3）

所有模型一律只接收由宿主編譯的單一微任務；自由輸入解析、狀態轉移、Reality／Knowledge、storylet availability、角色 episodic memory／reflection evidence、Graph projection、branch lock、journal recovery 與正典提交均由 deterministic runtime 執行。L1 本地模型只能渲染已核准 manifest 或做局部修句；L2 可提出結構化候選；工具能力不增加正典權限。

v2.2 已加入事件 log 的 hash-verified offset index、corrupt-tail 備份修復、archive manifest compaction 與維護崩潰回滾、typed temporal Graph、長篇 projector 與作者 runtime console。v2.3 再加入 Temporal 類 replay contract／runtime build 相容驗證與 golden-history fixture、外部模型微任務的 durable activity lifecycle（schedule／lease／retry／cancel／stale result／restart recovery）、Yarn Story Solver 類 bounded storylet model checking（不可達內容、broken target、soft lock），以及獨立於 index 的完整 archive manifest hash／count／duplicate integrity gate。舊事件以明示 legacy-v1 相容路徑重播；未知事件或 transition contract 一律 fail closed。作者控制台會阻斷不相容重播、全歷史損壞及 pending model activity。

schema 後語義驗證適用全部六類模型任務：NPC actor ID 與核准 handoff owner 必須精確匹配；render 會拒絕空正文、task hash 洩漏與負面安全播報；repair／blind read／manifest 有非空與 enum 限制。能力仍逐 task 評級：單一模型可同時是 intent／repair／blind-read candidate，卻對 plan／manifest／render 為 L0。

### 隨機事件建議層（v2.4）

Novel OS 現提供顯式、branch-scoped 的隨機事件開關，且目前只批准 `off` 與 `on-suggestion`。所有新專案與 branch 預設 `off`；關閉時不得抽取、寫 suggestion audit、建立 agenda 或以其他名稱背景提示。只有使用者／作者可切換模式。

啟用後仍只在語意窗口檢查：action resolution 僅限 deterministic consequence 不明確時；一般機會在 scene boundary／transition／travel／downtime；fallout 在 post-scene／post-chapter；背景世界在較慢 world pulse；重大負面方向必須先 telegraph。元指令／澄清、直接後果未完成、明確因果已存在、高壓場景無自然斷點、情緒收束皆 suppress。

抽取結果是 `NON_CANONICAL_SUGGESTION` 方向卡，不是事件：不直接宣告發生、不修改 State／Graph／Knowledge／關係／傷勢／物件／時鐘／時間線／正文，不替玩家行動或寫內心，不寫死死亡、婚育、背叛、永久傷勢、關係成立／破裂、派系滅亡或世界規則改變。使用者／作者選擇採用後，才依當下 state 重新建立正式候選並走 Reality、Knowledge、Player Agency、Character Behavior、World Rules 與 Canon Gate。

Runtime 必須保存 algorithm version、seed、pool hash、eligible set、urgency tier、weights、roll、selected／no-event；required roles 先綁定再入池；no-event 是正式結果。Suggestion audit 與 canonical event log 分離，重播已記錄方向不得重新抽取。權威合約與 starter pool 位於 `immersive-interactive-fiction/references/random-event-*`，author console 只顯示模式與非正典 audit 健康度。

互動事件是可重播正本，State 是 checkpoint，Graph／context／摘要是可重建衍生物。角色記憶分 episodic、evidence-backed reflection、retrieval context；不得把摘要當事件正本。Novel OS 對所有模型預設 `lossless-addressable`：宿主自己做不壓縮記憶，窗口只限制當次內嵌量；塞不下的來源列 overflow id／hash，不摘要、不忘掉。`lossy-admission` 必須明示才可啟用。任何寫入都必須帶 source state hash、branch、event／turn provenance，並在 branch 級跨程序鎖內完成。

### 單一 Production Authority（v2.7 production）

所有 production project adapter 的唯一 canonical mutation API 是 `ProjectRuntimeAdapter.commit()`；它在通用 `FileStore` event kernel 上統一 lock、recovery、stale check、event append、state、branch manifest、runtime HEAD 與 project pointer。綁定 `production-authority.json` 後，直接 FileStore 寫入與 project-specific canonical writer 一律 fail closed。既有小說必須以來源化歷史 migration／cutover 接管，不得覆寫未知歷史；真正新建的互動或傳統長篇專案可由 `initialize_new_project()`／`initialize_longform_production()` 直接建立 active authority，從空 append-only history 開始。契約見 `immersive-interactive-fiction/references/production-authority-contract.md`。

### 第五輪 runtime hardening（v2.5）

在 v2.4 建議模式產品邊界不變的前提下，v2.5 補強模型外權威：active event segment manifest hash／count、activity lease fencing token 與 lock-scoped schedule／recovery、檔案型 ID 單一安全 segment、random request 冪等重播與 audit hash chain、suggestion source-state binding。這些是完整性與競爭修復，不新增頻率、Storyteller profile 或自動事件投放。

### v2.6 durability closure

v2.6 不新增小說功能；它把 v2.5 的新完整性階段收斂為可崩潰恢復的單機 durability baseline。Random suggestion audit 使用 journal→fsync append→manifest→journal cleanup 交易，重啟只能完成 journal 證明的單筆 suffix；request ID 同時綁定 source state、algorithm、pool、trigger、seed 與 window fingerprint，同 ID 不同請求一律 idempotency conflict。Model activity v1 透過明示 registry 遷移至 v2，舊 running lease 必須失效並重新 claim，complete 無 token 永遠拒絕。Event integrity 驗證改為純讀記憶體解析，不建立暫存檔。Audit、active event manifest 與 activity schedule／claim／complete／migration 均有真實 subprocess SIGKILL matrix。

作者控制台固定標示 `local-integrity`：可偵測意外損壞、截斷與相對既有 head 的未授權改動，但沒有外部 anchor 時不宣稱能抵抗具完整檔案寫入權的攻擊者。需要惡意全寫入抵抗時，宿主必須另接專案目錄外簽章、WORM 或遠端 append-only checkpoint。

### 裁判權威分層（v2.14）

Novel Judge `0.13.8+` 將評估拆成 `CANON_INTEGRITY`／`NARRATIVE_QA`／`EDITORIAL_DIAGNOSIS`／`READER_RESPONSE`／`AUTHOR_DECISION`。機器預掃不是 beta；真人共識也不是作者決定。  
正典提交只看 canon 與高信心 Narrative QA P0；編輯診斷與讀者反應不得單獨授權或冒充品質真值。  
細節見 `immersive-interactive-fiction/references/authority-layers-contract.md`。

### 不可繞過的 Gate 授權（v2.7 production）

每個 production candidate 的 Gate 必須使用 `minis.gate-envelope.v1`，由固定 CommitPolicy 驗證 runner、payload、turn、scene SHA-256、source state hash、verdict、severity、artifact 與 override。approve 只產生 state-bound authorization；`ProjectRuntimeAdapter.commit()` 必須在 branch lock 內完整重驗，並把 authorization hash 寫進 canonical event、runtime HEAD 與 project pointer。FAIL／P0 永不可 override；玩家控制、Reality、fact agency 等 authority Gate 也永不可 override。檔案存在或 hash 正確不再等於授權。此契約適用互動小說、傳統長篇與隔離測試專案；模型、工作台與專案專用工具都不得旁路。契約見 `immersive-interactive-fiction/references/gate-authority-contract.md`。

### Production 歷史與 legacy cutover

既有專案必須由已驗證的 reconciliation baseline 重建 append-only canonical history；active segment manifest、offset index、point-in-time replay、Graph／timeline projector 都必須可重建。legacy candidate、turn、audit、scene revision 與 state checkpoint 保留來源 hash；缺少原 event payload 時只標 `RECONSTRUCTED_CHECKPOINT`，不補造 transition。cutover 後 legacy writer／candidate lifecycle／HEAD builder 必須降為 migration read-only 並 fail closed；唯一 mutation API 是 `ProjectRuntimeAdapter.commit()`。歷史正本與版本契約不同的專案只可先唯讀盤點或在隔離複本驗證，不得宣稱未經驗證的 production cutover。完整契約見 `immersive-interactive-fiction/references/production-history-migration-contract.md`。

### v2.7 Production writing closure

v2.7 將 Project Readiness、Graph／long-form／workbench freshness、command executor、event-derived memory／context／storylet、semantic debt、Quality Eval v2 與 typed semantic events 接上同一 production authority。`explicit_author_pass_at_1`、observed revision 與 workflow proxy 必須分欄；沒有明示 feedback 時保持 `null`。新 canonical events 必帶 `minis.event-semantic-delta.v1`，以 operations hash 綁定 typed effects 與非空摘要；legacy history 不回填猜測。新建傳統長篇使用 active authority＋七 Gate＋typed event；100k+ pilot 與隔離第二專案 contract probe 是 release smoke 的必要證據。



所有小說生成、規劃、修訂與盲讀流程使用 Luna baseline 示意設計契約，這不是實測能力或模型可用性保證，依 `novel-model-capability-compatibility/references/luna-baseline-contract.md` 執行。這不是永久鎖定單一模型；任何替換模型都必須使用同一 active-context、scene manifest、facts alignment、局部修復、deterministic Gate、隔離盲讀與 host commit 流程。更強模型不得取得額外正典／工具權限，較弱模型不得省略功能；事件與狀態差分、P0、盲讀與玩家控制結果必須與 Luna baseline 相容。

## 能力路由

| 使用者目標 | 必用模組 | 視需要加入 |
|---|---|---|
| 建立／續寫長篇、章節重寫 | `long-form-novel-writer` | style、world、behavior、graph |
| 公開 HTTP(S) 網頁擷取、Markdown、站內探索、可恢復 acquisition | `public-web-research` | deep-digger、browser_use；Facebook／Instagram 改走專用技能 |
| 真人／小說／動漫／電影角色研究與立體人設 | `novel-character-deep-digger` | public-web-research、behavior、character-db、graph、版本正典 |
| 公開人物／小說／動漫／電影角色資料持久化／查詢 | `character-database-builder` | knowledge-relationship-graph、分類驗證 |
| 人物動機、反應、弧線合理性 | `human-behavior-personality-consultant` | deep-digger、long-form |
| 世界規則、城市、制度、魔法／科技 | `novel-worldbuilding-architect` | `novel-world-database-builder`、graph、long-form |
| 特殊物資料庫建立／更新／查詢／比較／匯出 | `special-object-database-builder` | `novel-worldbuilding-architect`、`knowledge-relationship-graph`、`long-form-novel-writer`；涉及駕駛者／人格時加 character-db／behavior |
| 文風、敘事距離、類型工藝 | `novel-style-craft-director` | long-form |
| 文句自然化、去 AI 味、台灣繁中校準、角色聲音修訂 | `novel-human-voice-editor`（必要時用 Humanizer-zh 31 檢查點）→ `lieflat-less-ai-tone`（窄範圍白名單 pass） | long-form、style、behavior |
| 聲音描寫、狀聲詞、五感／聽感、場景太安靜或動作清單無聲 | `novel-sensory-sound-prose` | style、human-voice、intimacy craft、long-form |
| 關係網、事件因果、時間圖譜 | `knowledge-relationship-graph` | character-db、long-form |
| 未完成／斷更小說研究、補完、原作者意圖推演、替代結局 | `unfinished-novel-completion` | long-form、graph、style、behavior、world；必要時 web／character-db |

先讀被路由技能的 `SKILL.md`，依其完整流程和資源執行。涉及斷更／未完成作品時，**先讀 `unfinished-novel-completion/SKILL.md`，在初始化與續寫前完成來源、文本正典、作者意圖、可行性、分支與權利邊界檔案**；不得直接把未完成作品當普通續章處理。若宿主未實作技能自動載入，從本目錄向上找到 `skills/<name>/SKILL.md` 後手動讀取。

## 特殊物資料庫工作流

當輸入要求建立、保存、更新、查詢、比較或匯出道具、鎧甲、機體、機器人、載具、武器、神器、裝置或裝備系統資料庫時，先讀 `special-object-database-builder/SKILL.md`，並按需讀 `novel-worldbuilding-architect` 與 `knowledge-relationship-graph`。先鎖定作品／媒體／宇宙／版本／正典範圍，再把特殊物拆成物件、版本／變體、模組、能力、規格、能源／彈藥、限制／反制、操作資格、持有／控制、位置、生命週期事件與來源證據；不同漫畫、動畫、電影、遊戲、季別、重製或宇宙不得無聲合併。特殊物技能負責物件本體與生命週期，世界資料庫負責世界層規則／資源／制度；需要跨章同步時交給 `long-form-novel-writer`，需要人物駕駛／自主意識／知識時加載角色與行為技能。

特殊物的能力查詢必須同時回傳啟動條件、能源／彈藥／材料、消耗、持續／冷卻、範圍、失效方式、已知反制與版本來源；不能只回一個戰力排名。規格比較按 `version_scope`、`canon_scope`、`identity_mode` 分組，衝突以 claim／measurement 保留，不以最新資料覆蓋舊版本。小說章前提供物件目前位置、持有／操作、完整度／損傷、能源／彈藥／冷卻、模組與角色可知版本；章後只回寫已核准差分。

## 世界資料庫工作流

當輸入要求建立、保存、更新、查詢或匯出小說世界資料庫，或把 world bible、world rules、地點／派系／資源／規則與研究資料轉成可追溯圖譜時，先讀 `novel-world-database-builder/SKILL.md`，並按需讀 `novel-worldbuilding-architect` 與 `knowledge-relationship-graph`。世界觀設計技能負責最小可用世界、因果後果與合理性；世界資料庫技能負責 Graphify 正本、來源證據、認知層、正典狀態、快照、版本、查詢、匯出與長篇同步。若世界資料中引用特殊物，保留本技能的穩定 object ID，特殊物本體與生命週期交給 `special-object-database-builder`，不可把兩份正本靜默合併。先建立資料庫契約與來源盤點，再以批次 JSON 匯入；不可用圖譜反向覆寫 world bible 或正文。

世界資料庫查詢必須遵守兩層標記：`[LOCKED]／[CANON]／[PLAN]／[DRAFT]／[PROPOSAL]／[UNKNOWN]` 是正典狀態；`[TRUTH]／[OFFICIAL]／[BELIEF:<group>]／[RUMOR]／[KNOWN:<character>]` 是認知版本。角色視角只可使用其已取得的版本。重大規則、資源、控制權、歷史或認知改動先 snapshot，再做 affected，章後只回寫已核准差分。



當輸入涉及斷更、太監、作者中止、作者去世後未完手稿、讀者替代結局或 AI 續寫未完成作品，先交給 `unfinished-novel-completion`：

1. 初始化 completion brief、source manifest、textual canon、evidence／author-intent ledger、version conflicts、feasibility、hypothesis、unfinished-thread、rights、provenance 與 completion state。
2. 把 `TEXT-CANON`、`AUTHOR-NOTE`、`AUTHOR-STATEMENT`、`EDITORIAL`、`ADAPTATION`、`FAN-THEORY`、`INFERENCE`、`PROPOSAL`、`UNKNOWN` 分開；不把推測冒充原作者意圖。
3. 分別評估 `intent-reconstruction`、`textual-continuation`、`creative-completion` 的可行性。沒有作者後續材料時，預設是正典約束續作，不宣稱恢復原意。
4. 保留至少兩條合理分支，記錄證據、假設、反證、未完成線處理與分歧點；作者選擇前不得升為 `[CANON]`。
5. 先檢查 `rights-and-publication.md`。斷更、失聯或死亡不等於著作權消失；未知／未授權作品預設只做私人研究與分析，不包裝官方續作。
6. 通過補完 Gate 後，才把交接包交給 `long-form-novel-writer` 逐章規劃、寫作、驗證與更新狀態。

### 斷更補完交付

每次交付簡短說明：補完模式／分支、原意可推測度與正典續作可行性、使用來源、主要未知／衝突、證據層、已執行／未執行 Gate、非官方與 AI 揭露狀態，以及下一個作者決策點。


1. **作者主權**：使用者的明確指示大於任何模板、模型審查與既有推論。若覆寫舊正典，記錄決策與影響，不假裝不存在矛盾。
2. **正典分層**：區分已定稿、草稿、研究事實、推論、傳聞、角色認知與創作提案。不可把後三者寫成不容置疑的真相。
3. **狀態先於華麗文字**：開始新章或互動回合前，取得最小必要狀態；結束後更新人物、時間、物件、資訊、關係、伏筆、讀者資訊和延遲後果。
4. **斷更補完**：`unfinished-novel-completion` 的研究／分支／溯源層完成後，才把選定模式與 branch handoff 交給 `long-form-novel-writer`。
5. **因果可追溯**：重大轉折通過世界可行性與行為可行性；必要時入圖譜並連結來源／章節／信心。
6. **真人資料邊界**：僅使用必要的公開資料；保留來源與 EXTRACTED／INFERRED／AMBIGUOUS／FICTIONAL_PROPOSAL 分層，拒絕推定私人敏感資訊。
7. **親密與權力**：角色皆須成年。描寫親密關係時保有角色能動性、同意／權力脈絡及事後後果；不將傷害包裝為無後果的浪漫。
8. **人味修訂**：`novel-human-voice-editor` 只能在內容、連續性、行為、視角和風格檢查完成後介入文字層。文章或說明可選用 Humanizer-zh 的 31 個檢查點，但單詞、三項列表和破折號本身不是改寫理由。其後可選擇執行已安裝的 `lieflat-less-ai-tone` 白名單 pass，但只能依該技能明示規則處理可定位表層痕跡；保護正典、作者聲音、角色差異與必要的不完美。它不以「騙過 AI 偵測」為目標，不將單一用詞當成證據。
9. **不虛報工具結果**：沒有 shell／檔案權限時，說明哪些驗證、圖譜或快照不能執行，仍可提供等價文本方案。

## 長篇工作流

### A. 建立專案或取得既有正典

新專案：先讀 `long-form-novel-writer`，使用其 initializer 或等價骨架。至少建立 project brief、story bible、world bible/rules、style sheet、角色檔、behavior models、current state、timeline、plot threads、reader ledger、chapter index、decisions、entity registry、workflow state 與 graph。

既有專案：先產出 Resume Card（HEAD、凍結與否、未收線、下一步），再讀 project brief、story bible、current state、timeline、plot threads、reader ledger、entity registry、最新摘要與目標章；再判斷需要載入的角色／世界／風格／行為模組。不得只讀上一章就續寫。單人作者的成功標準是低摩擦恢復，不是先填完整設定。

作者日常入口（不改正典）：

```bash
python3 -m novel_judge.cli resume <project-root>
python3 -m novel_judge.cli scenes <project-root>
python3 -m novel_judge.cli preview-context <project-root> --actor <id>
python3 -m novel_judge.cli draft-scene <project-root> --path <scene.md> --text "..."
python3 -m novel_judge.cli diff-scene <project-root> --draft-id <id>
python3 -m novel_judge.cli accept-scene <project-root> --draft-id <id>
python3 -m novel_judge.cli export-manuscript <project-root>
```

生成入口（`compile_model_task`／`run_turn`／`run_agent_turn`）必須自己從 store／專案根找到 verified writing-inputs，不必把 `_production_project_root` 寫進正典。讀到時標 `generation_read_model=verified`，把 `used_source_ids` 寫進 packet，並寫 writing-inputs 旁的 used-sources 側車（非正典），讓 context 預覽看得到這次用了哪些記憶。所有模型預設 `context_policy=lossless-addressable`，並記 `addressable_source_ids`；未內嵌來源不得標成 forgotten。讀不到就明示 `canonical_fallback`，不得假裝已使用投影記憶。新專案 0 event 可 bootstrap 第一場；已有事件卻空記憶仍阻擋。凍結專案只允許恢復卡／預覽／匯出複本，不生成新回合。

### B. 章節生命週期

1. 明確化本章壓力、角色目標、場景因果、視角、讀者知道／未知資訊與退出狀態。
2. 以角色的可見資訊及當下身心／關係／資源限制做行為校準。
3. 寫完整可閱讀的正文，不以大綱取代章節，除非使用者只要大綱。
4. 執行或人工完成連續性、讀者資訊、世界規則、角色動機、風格與重複度檢查。
5. 章後更新所有被改變的狀態，產生摘要與 gate；再做 snapshot／commit。任何 FAIL 需揭露、修正或經作者明確接受。

### C. 改綱／重寫

先建立變更提案與影響範圍。修改已定稿的事件、關係、秘密、傷勢、時間、世界規則或物件時，回溯受影響章節、摘要、伏筆、讀者資訊與圖譜；更新後再驗證。不可只改一段正文而遺留錯誤帳本。

## 互動小說迴圈

開始回合前先看 Resume Card。玩家可自由輸入行動與對話；不把回合限縮為 A/B/C。每回合依序：

1. 讀取 state、先前行動與有效時鐘；確認玩家控制權只限其角色。
2. 推演 NPC 各自的目標、知識、限制與關係，不讓 NPC 因劇情需要全知或被動。
3. 描寫玩家可感知的結果，保留不確定性與合理反作用；不預先決定玩家的思想／行動。
4. 更新世界時間、位置、物件、知識、關係向量、事件、時鐘與延遲後果；記錄可見結果與隱藏變動。
5. 提出開放式感官／行動鉤子，而非強迫選項。

## 自我檢查與交付

交付小說內容時簡短附上：修改或產生的檔案、正典狀態、已執行／未能執行的檢查、尚存風險與下一個合理切入點。除非使用者要求，勿以冗長流程打斷閱讀體驗。

## 世界資料庫初始化與同步

若新長篇要啟用獨立世界資料庫，使用：

```bash
WORLD_DATABASE_ROOT=<WORLD_DATABASE_ROOT>
WORLD_DATABASE_WORK_ROOT=<WORKSPACE_ROOT>
GRAPH=<SKILLS_ROOT>/knowledge-relationship-graph/scripts/relationship_graph.py
DB="$WORLD_DATABASE_ROOT/<slug>"
BATCH="$WORLD_DATABASE_WORK_ROOT/<slug>-world-db/extraction-batch.json"
python3 "$GRAPH" init --root "$DB" --title "世界資料庫"
python3 "$GRAPH" import --root "$DB" --file "$BATCH" --strict
python3 "$GRAPH" validate --root "$DB"
```

長篇 initializer 仍只建立本地 `world-bible.md`／`world-rules.md`；外部世界資料庫必須由作者或 router 明確啟用並以 `world-database-link.json` 記錄。

作者修正不另開技能。先寫非正典錯誤卡；重複、可檢查且作者核准後，才升成角色護欄、rejected fixture 或既有 Gate。契約與 runtime 在 `immersive-interactive-fiction/references/author-correction-promotion-contract.md` 與 `novel_judge.author_corrections`。單次口味只記 note，不得自動改 `SKILL.md` 或正典。

目前 Novel OS 可攜 runtime 由 17 個 Skill 組成：1 個總入口與 16 個協作技能（另有匯出器，不安裝進 runtime），其中 `novel-reality-state-engine` 是跨作品的現實狀態與連續性核心，`novel-model-capability-compatibility` 是跨供應商／本地模型的能力契約與切換 Gate，`novel-sensory-sound-prose` 是通用聽感／狀聲詞／五感文筆層；共同確保事件、時間、資源、生理負荷、認知容量、心理機制、工具、Graphify、感官文筆與正文驗證不因模型或宿主替換而靜默消失。

詳細規則在相鄰的十六個專業技能內。系統匯出、安裝和自測請用 `novel-system-exporter`。
