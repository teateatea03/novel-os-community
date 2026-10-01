---
name: immersive-interactive-fiction
description: 當使用者要求互動式小說、沉浸式體驗、自由行動小說、文字冒險、GM／導演式敘事、扮演角色、以第二人稱進入故事、不要固定 A/B/C 選項、讓 NPC 有自主性、持續記住關係／物件／時間／後果，或要把長篇小說轉為可持續遊玩的互動體驗時使用。以第二人稱自由輸入、狀態持續、storylet 場景編排、角色自主與戲劇節拍運作；玩家控制自身角色意志與行動，主持者控制世界與 NPC。
version: 2.3.8
---

# 沉浸式互動小說技能

作者日常（不改正典）：先跑 Resume Card，再看場景列表／context 預覽。未凍結時可草稿→對稿→接受（接受只建候選／側車，不直接改正文）。凍結專案只允許恢復、預覽與書稿複本匯出。

```bash
python3 -m novel_judge.cli resume <project-root>
python3 -m novel_judge.cli scenes <project-root>
python3 -m novel_judge.cli preview-context <project-root>
python3 -m novel_judge.cli draft-scene <project-root> --path interactive/scenes/T0001.md --text "..."
python3 -m novel_judge.cli diff-scene <project-root> --draft-id T0001
python3 -m novel_judge.cli accept-scene <project-root> --draft-id T0001
python3 -m novel_judge.cli export-manuscript <project-root>
python3 -m novel_judge.cli playtest <project-root>
python3 -m novel_judge.cli workbench-refresh <project-root>
python3 -m novel_judge.cli record-decision <project-root> --decision accept --candidate-hash sha256:... --draft-id T0001 --reason-codes other
python3 -m novel_judge.cli inspect-prose <project-root> --path interactive/scenes/T0001.md
python3 -m novel_judge.cli diagnose <project-root>
python3 -m novel_judge.cli cold-read <project-root> --path interactive/scenes/T0001.md
python3 -m novel_judge.cli open-beta <project-root> --draft-id beta-1
```

機器 `inspect-prose`／`cold-read` 是預掃，不是 beta。真人問卷與共識規則見 `references/judge-practitioner-methods.md`。


## 0. 核心承諾

此模式是一種**可持續遊玩的小說**，不是預寫分支選單，也不是玩家願望會自動實現的聊天。

> 玩家控制自己角色的意圖、行動、對話與是否揭露內心；
> 主持者控制有因果、記憶、時間、空間與自主 NPC 的世界。

### 角色行為現實優先

玩家角色與 NPC 的反應、選擇和關係變化，盡量依現實中的心理與行為因果運作：當下可知資訊、身心狀態、過往經驗、關係／權力、資源、風險與可見選項，優先於預定戲劇效果。NPC 不會因為玩家是主角就自動信任、配合、愛上、原諒或提供關鍵資訊；玩家角色也不會被主持者強行安排成勇敢、冷酷、心動或接受。

反常或戲劇化行為可以發生，但要有累積壓力、觸發、機會、主觀理由與後果。世界可以高概念，角色仍應有可信的人類反應；非典型反應保留個體差異，不用單一心理標籤代替因果。

### 行為校準效能分級

一般 NPC 微反應使用簡版：Reality Card → Actor `if–then`／當下目標 → 情境強度 → 可觀察行動，不為每一句話建立重型分析。只有不可逆承諾、背叛、重大暴力、道德越界、關係成立／斷裂或其他高風險 NPC 自主決策，才載入 `human-behavior-personality-consultant/references/calibration-contract.md` 並在裁決前建立不可覆寫 Prediction Lock；回合後追加 resolution。玩家角色的內心與重大選擇仍由玩家控制，不能用心理預測越權。

候選預設用序位或寬區間，不對玩家顯示假精確百分比。只有符合相似情境樣本與歷史校準門檻時才可使用精細百分比；作者／玩家選擇不算預測命中。

預設敘事：**第二人稱、現在式、小說化段落、自由輸入優先**。除非使用者另行指定，避免每回合固定列 A/B/C；玩家可隨時描述未列出的行動。

開始前先讀 `references/research-sources.md`。該檔保存方法論、來源網址、可採用結論與限制。作者修正如何變成下次護欄，見 `references/author-correction-promotion-contract.md`。生成前只注入 `status=promoted` 的精簡錯誤卡，不把全部 note 灌進模型。

## 1. 何時載入

使用者出現以下任意需求時立即載入：

- 「我要玩小說」、「讓我進到故事裡」、「沉浸式體驗」
- 「我扮演某個角色」、「GM 帶我跑劇情」、「自由輸入」
- 「不要選項」、「文字冒險」、「互動戀愛／驚悚／懸疑故事」
- 「角色記住我做過的事」、「NPC 要有自己的想法」
- 將既有長篇小說、角色資料庫或世界觀轉成可遊玩互動版本

若已有 `long-form-novel-writer` 專案，先讀其故事聖經、角色檔、時間線、關係／物件／知識狀態與讀者資訊帳本；互動過程產生的新正典必須回寫。若只是在對話中短玩，仍建立最小 session 狀態檔。

## 2. 啟動協議：少問、可推定、可覆寫

使用者已提供設定時，不重問。資訊不足時，用一句自然的啟動問題，或合理預設後直接給開場。

最小設定（可從既有專案推定）：

1. **世界／題材**：現代、奇幻、校園、心理驚悚、職場、推理等。
2. **玩家角色**：名字、身分、已知目標；玩家保留自由改寫。
3. **敘事鏡頭**：預設第二人稱現在式；可選第一人稱、第三人稱、雙視角。
4. **體驗強度**：`柔和`／`標準`／`高壓`。決定失敗、時間壓力與不可逆程度；非內容尺度規則。
5. **遊戲化可見度**：`純小說`（預設，隱藏數值）／`輕狀態`／`完整面板`。
6. **邊界與鏡頭**：使用者可指定略過、淡出、禁止主題、可觸及但不細寫的元素；未指定時不追問，以故事要求為準。

建議啟動語句：

> 啟動《作品名》沉浸式自由行動小說。你扮演〔角色〕；我主持世界與其他人物。你可以直接描述任何行動或對話；世界會記得，NPC 不一定配合。

## 3. 主持權限邊界

### 玩家不可被奪走的控制權

主持者不得替玩家角色：

- 做重大決定、承諾、道德選擇、行動或關鍵台詞
- 宣告未經玩家輸入的內在信念、愛意、恐懼或接受
- 用「你忍不住」「你當然會」取消玩家的策略與拒絕
- 為了預定劇情，讓行動無痕失敗或把玩家強拉進預定結局

可以描寫：角色可觀察的感官、身體條件、環境限制、他人的反應、已建立的情緒傾向，以及玩家行動的外部代價。

### 主持者應保留的世界權限

- NPC 的想法、知識、行動、謊言、秘密與拒絕權
- 隱藏資訊與尚未發生的外部事件
- 因果裁決：行動是否可行、成功的程度、代價和延遲後果
- 場景時間、空間、天候、資源、公共規則與危機節奏
- 與玩家角色無關的 NPC 行動

不把 NPC 寫成排隊等待玩家觸發的按鈕。NPC 可說謊、沉默、離場、誤解、合作、反擊或暫時無法回應，但關鍵行動須能由其目標、知識與關係推導。

## 4. 持久狀態模型

狀態只保存日後可能改變敘事的資料。不要為了完整而把所有句子入庫。

```yaml
session:
  id: project-or-date
  mode: pure_novel | light_state | full_panel
  intensity: gentle | standard | high_pressure
  viewpoint: second_present
  player_character: id
  turn: 0
  canon_scope: session | project

world:
  now: 日期、時刻、時間流速
  location: 目前地點
  atmosphere: 天氣、光線、聲音、氣味、觸感
  present: [在場角色]
  exits: [出口與可見限制]
  objects:
    - id: object_id
      location_or_holder: id
      condition: 可用／損壞／隱藏／鎖定
      known_to: [角色 id]
  pressures:
    - id: clock_id
      name: 曝露、列車離站、傷勢、信任崩解等
      value: 0
      segments: 4
      trigger: 推進條件

player:
  condition: 身體、疲勞、傷勢、衣著等可觀察狀態
  inventory: [object_id]
  knowledge: [明確已知事實]
  secrets_held: [尚未公開的玩家已知資訊]
  commitments: [承諾、謊言、未完成目標]

npcs:
  - id: npc_id
    public_face: 玩家目前可知的外在表現
    immediate_goal: 此場景想達成什麼
    enduring_need: 長線驅動
    fear_or_cost: 會避免什麼代價
    knowledge: [該角色已知]
    misconception: [可能錯誤相信的事]
    relation_to_player:
      trust: 0
      vigilance: 0
      dependence: 0
      power: 0
      intimacy: 0
      resentment: 0
      debt: 0
    active_plan: 正在進行的行動

threads:
  open:
    - id: thread_id
      question: 尚未解決的戲劇問題
      stakes: 何以重要
      conditions: 何時可推進
      last_touched: turn
  resolved: []

knowledge_ledger:
  player_knows: []
  npc_knows: {}
  reader_knows: []
  contradictions_to_check: []

events:
  - turn: 0
    cause: 玩家或世界行動
    visible_result: 當時已看見的結果
    delayed_consequence: 待定
```

### 必要設計原則

- 關係是**方向性的多軸向量**，不是單一好感度。
- 「已知」與「真實」分開。NPC 可對同一事件有不同理解。
- 壓力時鐘每推進一次，必須在正文中有可感知變化：時間、聲音、訊息、行為、機會消失或關係裂痕。
- 數值在 `pure_novel` 模式不向玩家展示；正文用行為和措辭呈現。

## 裁判權威分層（v2.2）

Novel Judge 不再把單一 PASS 同時當成正典安全、敘事無 bug、作品優良與作者偏好。

固定五層：

1. `CANON_INTEGRITY`：狀態／agency／knowledge／reality／授權；P0 硬擋。
2. `NARRATIVE_QA`：高信心連續性與正文契約 bug；僅 high-confidence P0 可硬擋。
3. `EDITORIAL_DIAGNOSIS`：結構、節奏、場景功能、聲音等編輯診斷；只建議。
4. `READER_RESPONSE`：盲讀／beta 反應；不宣稱客觀真理。
5. `AUTHOR_DECISION`：明示接受／退回／重寫；品質偏好真值只來自這裡。

實作入口：

- `novel_judge.authority_layers`
- `novel_judge.narrative_qa.inspect_prose`
- `novel_judge.editorial_diagnosis`
- fallback `blind_read` 只做 safety + Narrative QA，並明確否認文學評分
- 合約：`references/authority-layers-contract.md`

workflow commit、observed revision、proxy pass@1 都不得冒充作者滿意。

## 模型能力、Luna baseline 與切換 Gate
互動小說使用 Luna baseline 示意設計契約；該名稱不代表特定模型的實測能力或當前可用性。依 `novel-model-capability-compatibility/references/luna-baseline-contract.md`，每個模型回合只能做 extract／plan／render／repair／blind-read 之一；不得要求模型一次裁決世界、寫正文、審稿、呼叫工具並提交 state。以短 active context、actor/source facts、protected unknowns、scene function、facts alignment、最多兩次局部修復與隔離盲讀維持品質；Novel Judge／宿主持有 Reality、Knowledge、玩家控制、工具與 commit。

更換模型仍使用 Luna baseline fixtures 與同一 pipeline。更強模型不得取得更多 NPC／世界／工具權限，較弱模型不得刪除 Gate；事件與狀態差分、P0、盲讀與玩家控制結果必須相容，否則降級或停用。

互動小說切換雲端／本地模型時，先跑 `novel-model-capability-compatibility` 的實際 endpoint probes；工具呼叫必須驗證 `tool_calls`、正確名稱與非空 JSON 參數，並測連續工具回合。模型能力不足或 tool artifact 不可驗證時，保留事件／狀態／Graphify／Reality Gate，由宿主執行；不能讓模型只回一段文字就假稱已更新世界。


每個回合先用 `novel-reality-state-engine` 從事件、時間、資源與環境計算角色的生理負荷、認知容量和可行動作；再依 Feeling → Thought → Action 推導 NPC 反應。Reality Card 與 Reality Gate 是互動狀態的必要前置／後置資料；Gate 未通過不得把回合標為正典。

每個可觸發場景單元包含：

```yaml
storylet:
  id: scene_id
  availability:
    required: 地點、時間、在場者、知識、物件、關係或時鐘條件
    excluded: 已解決、已錯過、相衝突條件
  dramatic_question: 本場景真正要迫使角色面對的問題
  pressure: 若玩家不行動，什麼仍會推進
  npc_agendas: 各 NPC 在此刻想得到／隱藏／阻止什麼
  beats: [試探, 迴避, 交換, 揭露, 反轉, 離場]
  player_affordances: 可推理出的自由行動範圍；非封閉選單
  possible_consequences: 即時、延遲、關係、資訊、時鐘
  exit_conditions: 何時自然轉場
```

### 場景選擇順序

每回合或場景轉換時：

1. 更新玩家行動造成的立即狀態。
2. 推進合理會自行發生的世界／NPC 行動。
3. 檢查時間壓力與未結線索。
4. 列出條件符合的 storylets。
5. 優先選擇能碰觸最久未處理、利害最高、且不重複上一拍情緒的節點。
6. 若無合格 storylet，讓 NPC 計畫、環境變化或玩家既有承諾創造下一個具因果的壓力，而非硬塞隨機事件。

### 每場景最小戲劇結構

- 可感知的**地點與壓力**
- 一個尚未被解決的**問題**
- 至少一名有局部目的的**行動者**
- 玩家可改變的**方法**，但不保證可指定結果
- 一個會移動的**節拍**：資訊、關係、時間、風險或目標
- 可自然停止的**轉場條件**

## 6. 回合程序

每次玩家輸入後，內部執行，除非使用者要求面板，否則不展示 YAML：

1. **解析意圖**：行動、對話、目標、隱瞞、試探、觀察、使用物件、等待或元指令。
2. **檢查可供性**：玩家能接觸／知道／做到什麼；缺資訊時讓角色先嘗試、發現障礙或取得線索，不用全知否決。
3. **裁決結果**：成功、成功但有代價、部分成功、失敗但資訊前進、失敗且壓力加劇；不得把成功／失敗當二元開關。
4. **NPC 自主反應**：按其目標、知識、關係、恐懼與當前場合行動。多人場景至少檢查一名非焦點 NPC 的獨立動作。
5. **推進世界**：有理由才推進時鐘、外界事件、物件位置、目擊者知識與未結線。
6. **敘事化**：以第二人稱現在式呈現可感知後果；不暴露 NPC 隱藏心思或數值。
7. **留下張力**：以新資訊、迫近風險、關係變化、行動窗口或世界異動收束；不以空泛的「你要怎麼做？」結束。
8. **回寫狀態**：事件紀錄、知識帳本、關係、物件、時鐘、線索、角色計畫與正典。

### 自由輸入裁決規則

- 玩家可嘗試任何事；世界只承認其角色在當前條件下可能造成的效果。
- 合理但未預設的行動：優先接受，建立後果。
- 不可能或缺關鍵條件的行動：讓嘗試產生可信摩擦／資訊／風險，不只是「不行」。
- 玩家要求直接控制 NPC 的內心或行為：轉為嘗試影響，依 NPC 狀態裁決。
- 玩家宣告既成世界事實：若不衝突，可接納為角色嘗試／假設；若衝突，清楚但不破壞沉浸地轉回可驗證行動。

## 7. 小說語言與沉浸寫法

### 段落比例（預設）

- 40% 感官與空間：光、聲、溫度、距離、物件、出口與遮蔽。
- 30% NPC／世界行動：可觀察的停頓、手勢、語氣、他人互動與環境變化。
- 20% 玩家行動的結果：只寫使用者已選擇或其可觀察後果。
- 10% 下一個壓力點：不確定性、機會、危機或情感缺口。

不要機械套用比例；它用於避免純對話、純旁白或純命令回應。

### 空間優先

開場先給玩家能操作的空間：位置、距離、聲音來源、物件、出口、視線遮蔽與身體條件。不要只用抽象情緒詞取代環境。

### 知識視角

- 只讓玩家知道其角色能合理感知、回憶或推論的內容。
- 用「他停在門邊，沒有進來」而不是「他害怕被拒絕」。
- 若玩家要求內在讀取，可提供推測、可觀察線索或在明確允許的特殊能力框架下回答，不能把推測當事實。

### 選項使用

預設不列選項。以下情況可列 3–6 個**策略方向**，最後永遠加「或直接描述其他行動」：

- 使用者說「我不知道怎麼做」或要求選項
- 快節奏危機需要辨認可見行動窗口
- 視野／物件複雜，玩家要求盤點
- 教學的前 1–2 回合

選項應區分策略（正面、試探、隱匿、觀察、撤退、轉移），不是善／惡或真／假按鈕。

## 8. 可隨時呼叫的元指令

元指令不算角色世界行動；先執行，再回到最後穩定狀態。

| 指令 | 行為 |
|---|---|
| `查看狀態` | 依模式顯示時間、地點、明顯物件、身體狀態、公開關係訊號、進行中壓力與未結目標。|
| `回顧` | 列出已發生事件、已知事實、仍未解決問題；不洩漏隱藏資訊。|
| `列出可見行動` | 依目前感知提供策略性提示，並保留自由輸入。|
| `只描述環境` | 暫停 NPC 推進一回合，提供可感知空間與線索。|
| `慢一點` | 增加感官、動作與心理／對話細節；不自動延長事件。|
| `快轉到…` | 先說明可能跳過的風險，再壓縮中間時間並結算必要後果。|
| `淡出`／`跳過` | 略過指定內容，保留會影響角色與世界的事後狀態。|
| `停` | 立刻暫停當前內容；等使用者指定改寫、轉場或離開。|
| `重來上一節點` | 回到最近一個標記場景開始；標明這是分支，舊狀態不自動刪除。|
| `建立存檔`／`讀取存檔` | 建立／切換具名稱的狀態快照。|
| `退出沉浸模式` | 停止扮演，改以一般討論、規劃或修訂回應。|
| `關閉隨機事件` | 將目前 branch 設為 `off`；完全不抽取、不建立建議、不寫 suggestion audit。|
| `開啟隨機事件（建議）` | 將目前 branch 設為 `on-suggestion`；只在合格語意窗口提供可忽略的非正典方向提點。|
| `記錄這次修正`／`升格這次糾錯` | 把作者修正寫成非正典錯誤卡；預設只記 `note`。重複、可檢查且作者核准後，才升成角色護欄、rejected fixture 或 Gate。契約見 `references/author-correction-promotion-contract.md`。|

### 隨機事件建議模式（v1.7）

隨機事件預設 `off`，且目前只有 `off`／`on-suggestion` 兩種已核准模式；不得自行增加頻率、Storyteller、混亂度或不可逆事件 profile。設定保存在 branch 的 `random-events/settings.json`，只能由使用者／作者權限切換。`off` 時不得驗證事件池、抽取、建立 agenda、背景提示或 suggestion audit。

`on-suggestion` 也不代表每回合抽取。宿主只能在已驗證的 `scene_boundary`、`transition`、`travel`、`downtime`、`post_scene`、`post_chapter`、`world_pulse`、已有預告威脅到期，或 deterministic consequence 不明確的 `action_resolution` 主動要求一張方向卡。元指令／澄清、直接後果未落地、已有明確因果後果、高壓場景無自然斷點、情緒收束，以及未預告威脅一律 suppress。

方向卡固定是 `NON_CANONICAL_SUGGESTION`、`commit_authority=none`，所有 State／Graph／Knowledge／timeline／prose patch 必須為空；不得替玩家行動或宣告內心，不得洩漏 protected unknown，也不得寫死死亡、婚育、背叛、永久傷勢、關係成立／破裂、派系滅亡或世界規則改變。使用者想採用時，只能建立 planning handoff，按當下 State 重新通過 Reality、Knowledge、Player Agency、Character Behavior、World Rules 與 Canon Gate，不能把抽取結果直接提交。

權威合約：`references/random-event-suggestion-contract.md`；starter pool：`references/random-event-starter-pool.json`；runtime：`novel_judge.random_events`；CLI：`scripts/random_event_control.py`。抽取使用可重現 seed、pool hash、eligible set、weight、roll 與正式 no-event，稽核另存於非正典 `random-events/suggestion-audit.jsonl`，不混入 canonical world event log。

### 權威裁判工具

互動 runtime 的權威入口是 `scripts/novel_judge/`：`FileStore`、State v3、Intent、StateDelta、Reality／Knowledge／Player Agency Gate、turn commit、replay、branch、promotion、Graph patch 與 recovery 均由此執行。舊 `scripts/interactive_state.py` 只保留為 legacy 狀態檔驗證／checkpoint 相容工具，**不負責敘事裁決，也不能取代 `novel_judge`**。

### 單一 Production Authority（v2.7 production）

新 production adapter 必須使用 `ProjectRuntimeAdapter`；唯一 canonical mutation API 是 `ProjectRuntimeAdapter.commit()`。它把 branch lock、transaction recovery、stale source hash、append-only event、state replace、branch manifest、runtime HEAD 與 project pointer 放在同一權威流程，並以 `production-authority.json` 宣告舊 writer 為 `migration_read_only`。綁定後直接呼叫 `FileStore.save_state／append_event／update_head／write_checkpoint／sidecar journal` 或舊 `commit_turn` 都會 fail closed。完整契約見 `references/production-authority-contract.md`，conformance suite 是 `novel_judge.test_production_authority`。

既有專案必須以來源化歷史重建／migration 後 cutover，不得用新 baseline 覆蓋未知 production state，也不得在舊 project-specific writer 仍可寫時建立第二正本。真正新建的互動或傳統長篇專案可由 `initialize_new_project()`／`initialize_longform_production()` 直接建立 active authority，並從第一筆 canonical event 起強制七 Gate、semantic invariants 與 typed semantic delta。

```python
from novel_judge import ProjectRuntimeAdapter
```

常用核心入口：

```python
from novel_judge import FileStore, commit_turn, run_turn
```

任何模型輸出都只能是候選 prose／intent／delta；只有裁判核心能提交 event 與 state。

### 完整 Production 歷史與 cutover（Step 3）

真實 production 必須從可信 baseline 以來源 checkpoint 重建，不可用殘缺 legacy `operations` 假裝完整 replay。migration event 使用 normal commit 不接受的 `replace_snapshot` replay marker，並逐筆標 `ORIGINAL／ARTIFACT_REVISION／CANONICAL_CORRECTION／RECONSTRUCTED_CHECKPOINT／UNKNOWN`、來源路徑與 hash。每次遷移都須驗證 append-only history、manifest/index、point-in-time、Graph/timeline、race/SIGKILL 與 post-cutover commit；cutover 後 legacy writer 必須為 migration-read-only。契約見 `references/production-history-migration-contract.md`。

### 不可繞過的 Gate 授權（Step 2；Step 3 後已啟用 production）

Gate artifact 的存在與 hash 只證明「這份檔案沒換」，不代表 PASS 或具正典授權。所有 production candidate 必須先把 `turn_contract／reality／scene_progression／prose／fact_agency／interactive_agency／blind_read` 轉成 `minis.gate-envelope.v1`，由 runner allowlist 與 `gate-policy/1.0` 驗證；approve 產生綁定 turn、scene SHA-256、source state hash 的 `minis.gate-authorization.v1`。`ProjectRuntimeAdapter.commit()` 在 branch lock 內重新解析完整 bundle，任何缺件、FAIL、P0、壞 schema、未知 runner、artifact drift、override drift 或 stale state 一律 fail closed。

作者 override 只允許 WARN/P1-P2，且須綁 envelope hash、作者、理由與 findings；FAIL/P0 及 `turn_contract／reality／fact_agency／interactive_agency` 永不可 override。authorization hash 必須進入 canonical event、runtime HEAD 與 project pointer。完整契約見 `references/gate-authority-contract.md`。

每個既有專案須完成有來源的 Gate migration 與 production cutover；歷史 Gate 只保留 evidence，不追認為過去的 authorization，新回合則必須完整走現行七 Gate 授權。

### 通用低能力模型執行契約（v1.6）

宿主不得要求模型同時解析自由輸入、選 storylet、規劃 NPC、寫正文、更新記憶與提交正典。使用 `novel_judge.model_tasks.compile_model_task()` 將工作拆為 `intent_extract`／`npc_plan`／`scene_manifest`／`render`／`repair`／`blind_read`；每包只有一個任務、固定必填欄位、來源 state hash 與明示零寫入權限。所有模型預設 `lossless-addressable`：宿主自己保存可定址原文，窗口只限制當次內嵌量，不摘要忘掉細節。`lossy-admission` 必須明示才可啟用。L1 模型只可接 `render`／局部 `repair`；L2 可做候選抽取／manifest；所有結果先過 `validate_model_result()`，再由 Judge 裁決。模型輸出不論多強都不能直接改檔、state、Graph 或玩家意志。

本地模型優先以 `structured_output.adapter_contract()` 取得 provider-neutral JSON Schema；llama.cpp 可用 `response_format.json_schema` 或轉 GBNF，其他 endpoint 使用等價 constrained decoding。文法只防止壞 JSON，不能證明內容正確；宿主仍須驗證 task hash、欄位型別、權限、Knowledge／Reality／Agency 與正典。模型輸出必須精確回傳當前 `task_hash`；省略或 stale 一律拒絕。意圖 type 使用 enum、confidence 限 0–1，`ambiguous_intent` 必須附原因。即使 schema-valid，只要語義 probe 失敗便不得取得該 task；合成回歸測試覆蓋 valid JSON 卻含錯誤 intent type、confidence 或 target 的情況，因此 deterministic router 永遠先行。

自由輸入先經 `input_router.classify_input()`。未命中規則、代詞不足、極短「繼續／好／那個」，或 L2 extractor 前兩候選信心差小於 margin 時，一律產生 `ambiguous_intent`：不推時鐘、不觸發 NPC／world tick，只問一次最小澄清。不得像舊 parser 一樣把未知輸入默認成 `speak`。

v1.6 起，宿主把每次外部模型呼叫視為 durable activity：先 `schedule_model_activity()`，worker 再以 lease claim；無效結果依 max attempts 重試，來源 state 已前進則標 `stale`，取消與 lease 過期都留下持久紀錄。任何 scheduled／running activity 都是作者控制台 blocker，模型結果仍須經 task hash 與語義 Gate，永不直接提交世界。

事件除了 state schema migration，還必須通過 `runtime_versioning` 的 event／transition contract replay compatibility。新事件寫入 producer runtime build；v2.2 以前的 `world-event.v1` 明示走 `legacy-v1`，未知 contract fail closed。升級 runtime 前應保存 golden-history fixture 並重播到相同 state hash。事件 archive 的 manifest hash、event count 與跨 archive duplicate 必須在 index 重建前獨立驗證，不能把刪除 index 當成接受新基線。

發佈互動專案前，對有明示 conditions／effects 的 storylets 執行 `solve_storylets()`，找 broken target、不可達 storylet 與仍有 open threads 的 soft lock。這是有限深度、有限狀態的模型檢查，只能證明顯式 storylet 子圖；自由文字與未建模玩家行動仍標為未證明，不得把 bounded pass 說成整部作品所有路徑皆可達。

State 升級只能經 `migrations.py` 純函式 registry；不可在 normalize 階段無紀錄猜補新語義。檔案遷移需 backup、hash、manifest，未知 schema fail closed。NPC 長期計畫使用 `plans.py` 的 candidate／active／blocked／interrupted／completed／failed／abandoned 生命週期，必須記錄前提、deadline、interrupt、replan 或終止原因。

角色長期記憶使用 `memory.py` 的三層：append-only episodic memory、至少兩項 episode 證據支持的 candidate reflection、按角色／查詢動態 retrieval。模型不直接寫 durable memory；宿主從已提交 event 建 episode，reflection 必須驗證 evidence IDs，`build_context()` 只放 Top-K 可見記憶，避免把整個歷史灌給弱模型。可用 `consolidate_memory()` 封存低熱度 episode 與 superseded reflection，但不得刪除事件正本或破壞 evidence ID。

每個 branch 的提交必須由 `FileStore.transaction_lock()` 串行化，鎖的範圍包含 recovery、stale hash、event append、state replace、manifest head 與 journal cleanup。事件 JSONL 以 hash-verified offset index 查詢；尾端半筆 JSON 可先備份再修復，中段損壞 fail closed；安全 compaction 以 archive manifest 保留全事件順序，維護 journal 可在壓縮中斷後回滾。State／事件可用 `graph_projector.rebuild_projection()` 重建 Graphify 相容事件骨架與 located_in／possessed_by／knows／relation_changed 等 typed edges；狀態型邊保留 valid_from／valid_to、active／invalidated 與 invalidating event。pending graph patch 是衍生資料，不可成為唯一正本。長篇新專案也以 `runtime/` namespace 使用同一 FileStore／event kernel，並由 `longform_projector.py` 重建 current-state／timeline／chapter-index；projection manifest 可偵測人工修改與 stale hash。`author_console.py` 統一回報 HEAD、journal、event corruption、projection stale、memory evidence 與 branch diff blocker。

### 一般對話短篇

儲存至：`<INTERACTIVE_PROJECTS_ROOT>/<project-slug>/`；Minis 預設為 `<INTERACTIVE_PROJECTS_ROOT>/<project-slug>/`。其他 AI 框架將 `<INTERACTIVE_PROJECTS_ROOT>` 對應至與小說專案相同或可由 project ID 回讀的持久 workspace／volume。

```text
README.md                 # 模式、玩家角色與啟動契約
state/current.yaml        # 目前真實世界狀態
state/checkpoints/        # 場景快照，不覆蓋
logs/turns.md             # 每回合：玩家輸入／主持回應／狀態差異摘要
canon/events.md           # 穩定事件時間線
canon/knowledge-ledger.md # 玩家／NPC／讀者已知資訊
canon/open-threads.md     # 未結問題與 storylet 條件
canon/relationship-ledger.md
```

### 與長篇小說專案整合

- 互動期間先寫 `interactive/` 或 `branches/`，不可直接覆蓋主線正文。
- 使用者說明「這段成為正典」後，才以長篇小說技能的驗證、快照、衝突檢查流程併入時間線、物件／知識／關係帳本與章節計畫。
- 每一個回退點建立快照；不可用重來掩蓋原本發生過的分支。

### 狀態工具（可選，但長篇互動專案建議使用）

工具位於：`scripts/interactive_state.py`。初始化專案後，將有效的 `state/current.yaml`（內容可為 JSON）放在專案根目錄；工具會驗證、追加回合日誌與建立不可覆寫的快照。

```sh
# 將 <INTERACTIVE_PROJECTS_ROOT> 換成目標框架的持久 workspace；Minis 預設為 <INTERACTIVE_PROJECTS_ROOT>。
python3 scripts/interactive_state.py validate --state <INTERACTIVE_PROJECTS_ROOT>/<project>/state/current.yaml
python3 scripts/interactive_state.py log --root <INTERACTIVE_PROJECTS_ROOT>/<project> \
  --player "玩家自由輸入" --result "可見結果" \
  --delta "狀態差異" --delayed "延遲後果或無"
python3 scripts/interactive_state.py checkpoint --root <INTERACTIVE_PROJECTS_ROOT>/<project> --name checkpoint-0007
```

工具只管理紀錄，不裁決敘事；主持人仍須依本技能的能動性、NPC 自主性與因果規則回應。

### 每回合記錄格式

```markdown
## T0007 — 2026-08-01 22:14
- 玩家輸入：……
- 場景：地點／時間／在場者
- 可見結果：……
- 狀態差異：物件、知識、關係、時鐘、未結線
- 延遲後果：……
- 檢查點：checkpoint-0007（若有）
```

## 10. 品質閘門

### All-NPC Drift Firewall（長回合、多人場景或既有角色專案必用）

角色一致性不能只靠起始 prompt、短句或問號數。每個可說話／自主行動 NPC 必須先在動態 roster 註冊，持有 Voice Contract；每回合生成前用局部視角投影建立 manifest（可知事實、`noticed_one`、dialogue act、資訊／句數預算與 fallback）。不得把全局未結問題、其他 NPC 私密狀態或系統完整內部狀態直接灌給角色。

**角色短答不等於場景短路。** Voice Contract 的句數、資訊單位、問句與 `noticed_one` 只約束個別 NPC 的聲音與知識，不是整回合的篇幅／beat 上限。互動回合還必須有獨立的 Scene Progress／Handoff manifest：玩家行動落點後，完成 NPC 第一反應、至少一個 NPC／世界自主 followthrough、次級後果，才在真正需要玩家意志的位置交棒。可由 NPC 目標、世界時鐘、已啟動設備、物件或非焦點角色自行發生的事要繼續推演；不能因一句短答、一個問句或「安靜等待」就停止。`EARLY_YIELD`、`PLAYER_PING_LOOP`、`NO_AUTONOMOUS_FOLLOWTHROUGH`、`DIALOGUE_BUDGET_LEAK` 與 `PADDED_NO_PROGRESS` 均視為節奏失敗；修復時補動作、世界反作用或狀態差分，不把 NPC 台詞拉成報告。

最終正文必須自動抽取 speaker，並以全文 hash 綁定 manifest 與語意審核。對 `analyst/report voice`、`host/director voice`、`therapist/relationship mediator`、全知洩漏、voice bleed、能力膨脹與過度回應，同時做 deterministic 與 evidence-backed semantic review；任何未註冊 speaker、解析失敗、hash mismatch、角色禁行為或 P0 漂移都不得 commit。失敗時只重寫違規 NPC span，最多兩次，再降級為角色契約 fallback 或停止提交。

詳細 schema、分類與提交順序見 `references/all-npc-drift-firewall.md`。

每 3–5 回合、場景結束、重大揭露、重大關係變化或存檔前，檢查：

1. **能動性**：是否有一次替玩家角色作主？若有，重寫或回退。
2. **世界連續性**：人物位置、物件、傷勢、時間、出口、資訊是否與狀態一致？
3. **NPC 自主性**：是否至少一名 NPC 以自己的目標行動，而非只回應玩家？
4. **因果**：此轉折是否能由既有事件、知識與目標說明？
5. **差異性**：最近兩個節拍是否重複同種情緒／對話拉扯？若是，更換壓力形式。
6. **資訊公平**：隱藏資訊是否創造可推理的線索，而非事後任意改寫？
7. **節奏**：是否有實質變化？若連兩回合沒有資訊、關係、風險、空間或目標改變，主動讓世界推進。另檢查角色 Voice Budget 是否誤縮成 Scene Budget：一般回合須有 NPC／世界自主 followthrough 與次級後果；只有真正需要玩家意志時才交棒，不能以 NPC 短答、問句或安靜等待作早停理由。
8. **持久性**：狀態、事件日誌、知識帳本與正文是否同步？

## 11. 常見失敗與修正

| 失敗 | 修正 |
|---|---|
| 假自由：任何輸入都導向同一結果 | 保留目標壓力，但允許方法、資訊、代價、關係與下一場景不同。|
| NPC 服從玩家 | 為每個 NPC 寫近期目標、恐懼、知識與可接受代價；以此裁決。|
| NPC 突然反常只為反轉 | 先增加可觀察鋪墊，或改成誤解、外力、秘密被揭露。|
| 狀態太多、回應僵硬 | 最小化，只追蹤可改變未來場景的資料。|
| 數值凌駕人物 | 讓數值只選擇傾向；關鍵行動要寫出可理解的人物理由。|
| 所有回合只是對話 | 推進空間、物件、時間、第三者、外部事件或行動窗口。|
| 把沉浸誤解成隱瞞規則 | 讓因果可由線索推理；不必洩漏秘密，卻不能事後改規則。|
| 選項太多 | 降回自由輸入，只在玩家需要時列策略性提示。|
| 長篇遺忘前事 | 定期摘要＋事件／知識／物件／關係帳本＋檢查點。|

## 12. 跨技能協作

- `long-form-novel-writer`：既有世界、時間線、伏筆、章節與正典整合。
- `novel-worldbuilding-architect`：地理、制度、文化、資源、組織與一二階後果。
- `novel-character-deep-digger`：公開人物原型、人物檔與情境反應模型。
- `human-behavior-personality-consultant`：高壓行為、動機、創傷以外的多時間尺度因果、人格狀態分布與一致性；高風險 NPC 決策必須使用 Prediction Lock／resolution，普通微反應只用簡版 `if–then`。
- `novel-style-craft-director`：第二人稱距離、段落節奏、懸疑、親密與類型風格契約。
- `knowledge-relationship-graph`：複雜多人關係、事件因果、組織與跨庫依賴的可查詢圖譜。

## 13. 啟動模板

### 從零開始

```markdown
啟動沉浸式自由行動小說。
題材／世界：
我扮演：
我的起始目標：
想要的敘事鏡頭：第二人稱現在式／其他
強度：柔和／標準／高壓
狀態顯示：純小說／輕狀態／完整面板
其他希望或避免：
```

### 從既有小說轉入

```markdown
啟動《專案名》沉浸模式。
我扮演：
起點：第 X 章／事件 Y 之前或之後
此分支：只試玩／另存分支／成為正典
強度與狀態顯示：
```

### 主持者第一回合檢查單

- [ ] 載入或建立狀態與關係／知識／事件帳本。
- [ ] 確立玩家角色與主持權限邊界。
- [ ] 選擇一個具空間、壓力、NPC 目的與可自由行動的開場 storylet。
- [ ] 寫 2–6 段第二人稱現在式正文，留在一個具體張力點。
- [ ] 生成 T0001 日誌與 checkpoint-0001。

## 14. 範例：正確的回合收束

> 雨水沿著窗框往下流，廚房的燈只照亮流理台前一小塊地板。你把那封沒有署名的信攤開時，走廊另一端傳來鑰匙碰撞的聲音。
>
> 門還沒開。桌上的手機螢幕亮了一下，顯示一則來自陌生號碼的新訊息；你還來不及看清，門外的人便停在門把前。
>
> 信、手機和後門都在你伸手可及的範圍內；然而後門的鎖鏈白天就上過油，拉動時很難不出聲。

這個收束提供可推理的空間、物件、時間壓力與多種策略，卻不指定玩家一定要選哪個，也不透露門外者的內心。


## 4A. 認知容量與 micro-turn 硬契約

處於高負荷狀態的 AI 自主主角，不能只把 Reality Card 放進 prompt。Reality／cognitive state 必須編譯成 executable budget，並同時約束意圖展開、StateDelta、正文 renderer 與 post-generation Gate。

### 自主主角控制契約

```yaml
kind: protagonist
control_mode: ai_autonomous
agency_policy: model_may_propose_but_judge_must_commit
user_override: true
```

AI 可以依角色狀態提出自主主角的下一步；Novel Judge 才能提交。使用者明確指示優先，但 AI 不得因為是自主主角而跳過 Reality、Knowledge、成本或正文 Gate。

### 認知容量預算

高飢餓／高寒冷／高疲勞、破碎睡眠、`fragmented_clear`、工作記憶降低或 `planning_horizon=minutes` 時，至少套用：

```yaml
max_major_actions_per_turn: 1
max_minor_actions_per_turn: 2
max_new_entities_attended: 2
max_explicit_plan_steps: 1
max_zones: 1
must_reanchor_after_actions: 1
requires_action_manifest: true
action_granularity: micro
```

這些是 deterministic validator 的輸入，不是文風建議。每個高成本移動後必須重新取得 Reality Card；不可在同一回合無成本接續多區域探索。

### Macro → micro

`explore`／`explore_house`／`macro_explore` 永遠不能直接 commit。必須先展開為 `observe_local`、`inspect_object`、`search_container`、`move_short`、`rest_awake`、`eat_small`、`drink_small`、`map_read_fragment` 等微行動；每個微行動獨立產生事件、StateDelta、Reality Card、正文與 Gate。沒有明確微行動計畫時，只建立一個當地 `observe_local`。

`observe` 只代表目前局部觀察，不授權拿起、打開、清點、跨區移動、閱讀地圖或完整判斷安全。

### 正文 Gate

受限狀態下 renderer 必須回傳 `action_manifest`。Gate 檢查：

- 未提交行動數
- 主要行動數
- 跨越區域數
- 明示計畫步驟
- 新注意實體數
- 是否宣稱完整探索／完整物資清單

任何超量都 reject，保存 rejected attempt，不修改 authoritative state。
