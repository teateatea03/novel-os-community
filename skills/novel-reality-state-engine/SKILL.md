---
name: novel-reality-state-engine
version: 1.8.0
description: 當使用者要求讓小說角色更貼近現實、檢查人物反應是否受飢餓／疼痛／疲勞／寒冷／睡眠／藥物／壓力影響、修復長篇角色狀態漂移、建立生理與認知狀態模型、讓世界事件真正改變角色可行為能力、驗證互動小說時間／資源／心理連續性、建立 Reality Card／Reality Gate，或要求把心理學、行為學、事件帳本、Graphify 與正文生成連動時使用。它是跨作品的小說狀態引擎，不只服務單一角色或單一本小說。
---

# Novel Reality State Engine

把「事件記憶」編譯成「角色此刻能做什麼、知道什麼、說得出什麼」，再讓正文生成受到這些條件約束。

## 模型執行層契約
現實狀態引擎不得假設任何模型能可靠呼叫工具或產生 JSON。模型切換由 `novel-model-capability-compatibility` 探測；L1／L2 模型只可作文字／文件模式，Reality Card／Reality Gate 必須由宿主執行；L4／L5 才可依部署契約啟用狀態工具或自動 agent loop。

## 核心原則

1. **事件先於解釋**：先讀取時間、資源、環境、睡眠、傷勢、藥物、關係／權力與知識帳本；不能只從上一段文字猜狀態。
2. **穩定人格不等於當前容量**：Actor／Agent／Author 是長期層；飢餓、疲勞、寒冷、疼痛、恐懼和睡眠破碎會折損注意力、工作記憶、語言完整度、規劃時間和執行力。
3. **Feeling → Thought → Action**：每個關鍵反應都要經過身體感受／注意力、內在評估、第一衝動、抑制／妥協、實際行動、短期回報與延遲代價。
4. **配合不自動等於同意**：吃飯、喝水、接受照顧、沉默、靠近、服從或身體反應不得自動改寫成信任、慾望、親密或同意。
5. **不要求角色永遠漂亮地抵抗**：角色可以犯錯、說錯、先答應後悔、做無效行動、誤判、重複思考或因身體需求先行動後補理由。
6. **不把心理標籤當因果**：使用條件式、競爭假說和可觀察預測；不做精神診斷，不把單一理論當命運。
7. **Graphify 是依賴圖，不是裝飾**：事件節點、資源、狀態、知識、伏筆與因果邊必須能被章前 context pack 查詢；圖譜不得覆寫正典正文。
8. **時間不假裝精確**：資訊不足時保存最小／最大區間與來源，不把「約一天」寫成確定的 27 小時。
9. **生成前後雙 Gate**：生成前建立 Reality Card；生成後檢查時間、生理、認知、知識權限、行為成本、角色控制權與後果。

## 跨技能路由

- 長篇／章節／重寫：先載入本技能，再連動 `long-form-novel-writer`、`human-behavior-personality-consultant`、`knowledge-relationship-graph`。
- 自由輸入互動小說：每回合在世界裁決前載入本技能；玩家角色與 NPC 都要有當前容量，但不得奪取玩家控制權。
- 人物行為分析：用本技能提供事件／狀態／能力層，交給行為顧問分析 Actor／Agent／Author。
- 圖譜查詢／受影響分析：用 `event → state → capacity → affordance → consequence` 邊；不要只建人物關係。
- 世界觀／世界資料庫：資源、制度、環境和規則事件若會改變角色能力，必須產生 state delta。

## 每回合必做流程

```text
讀取正典與 state
→ 讀取最新事件及 valid time
→ 更新時間／資源／環境／身體負荷
→ 計算 cognitive capacity 與可行動集合
→ 建立 Reality Card
→ 行為顧問推導 Feeling → Thought → Action
→ 生成場景／回應
→ Reality Gate 稽核正文
→ 寫回事件、state、knowledge、Graphify、timeline、context pack
```

任何一項關鍵來源缺失，標記 `STATE_UNCERTAIN`；不能用文學流暢度掩蓋缺資料。

## Reality Card 最小內容

```yaml
as_of: current valid time or range
last_events: [event ids]
physical:
  hunger: none | rising | high | critical | unknown
  thirst: none | rising | high | critical | unknown
  fatigue: low | moderate | high | severe | unknown
  thermal_load: neutral | cold | hot | wet_cold | unknown
  pain_or_drug_effect: none | present | uncertain
  physical_capacity: normal | strained | limited | minimal | unknown
cognition:
  clarity: clear | narrowed | fragmented_clear | confused | impaired | unknown
  working_memory: normal | reduced | poor | unknown
  planning_horizon: days | hours | minutes | immediate | unknown
  speech: full | shorter | fragments | minimal | unknown
  long_analysis_allowed: true | false | uncertain
psychology:
  dominant_need: ...
  dominant_threat: ...
  approach_avoidance_conflict: ...
  active_self_story: ...
affordances: [what the character can plausibly do now]
likely_errors: [realistic mistakes or omissions]
knowledge_boundary: [known / inferred / unknown]
state_confidence: high | medium | low
```

## 寫作約束

- 身體先於作者解釋：先寫刺激、身體和注意力，再寫她如何理解。
- 長篇完整分析必須有容量條件；`fragmented_clear` 或 `confused` 時，改用片段、重複、忘記、被需求打斷的思考。
- 保留競爭解釋：角色未取得的其他角色意圖不可直接寫成事實。
- 每個大行動記錄至少一項成本：熱量、體力、寒冷、暴露、關係、資訊、羞恥、談判籌碼或延遲後果。
- 每回合允許 0–2 個合理錯誤；不是強制失誤，而是禁止每回合都出現完美心理勝利。
- 作者可以指定低機率結果，但必須補成立條件與代價，並在狀態與圖譜留下來源。

## 禁止的連續性捷徑

- 把角色檔的「聰明／敏銳」直接當成當下能長篇分析。
- 把一句「很餓」當成完整生理模擬。
- 用模糊的「隔天」消除進食、睡眠和溫度後果。
- 用最新摘要覆蓋歷史事件而不標記 superseded／branch。
- 讓角色知道作者、讀者或 Graphify 裡但尚未取得的資訊。
- 把天候、設備故障或未到貨的物件誤寫成某個角色當下的內心意圖。

## 驗收

至少執行：

```bash
python3 scripts/reality_state.py validate --state <state.json>
python3 scripts/reality_state.py card --state <state.json> --out <reality-card.json>
python3 scripts/reality_state.py gate --state <state.json> --text <draft.md>
```

本技能的腳本是標準庫實作；完整工程仍需持久檔案、事件帳本與宿主 process runner。它是創作校準工具，不是醫療、法醫或臨床預測器。


## Executable cognitive capacity compiler

Reality Card 的 `capacity` 不只是供模型閱讀的描述。當角色處於高飢餓／高寒冷／高疲勞、破碎睡眠、`fragmented_clear`、工作記憶降低或 `planning_horizon=minutes`，宿主必須編譯並持久化：`max_major_actions_per_turn=1`、`max_minor_actions_per_turn=2`、`max_new_entities_attended=2`、`max_explicit_plan_steps=1`、`max_zones=1`、`must_reanchor_after_actions=1`、`requires_action_manifest=true`、`action_granularity=micro`。這些預算由 deterministic Novel Judge 與 prose Gate 執行，不由 LLM 自行解釋或放寬。

宏觀意圖如 `explore_house` 必須拆成 micro-turn；`observe` 只允許局部觀察，不授權跨區、清點、拿取、讀圖或完整安全判斷。每個 micro-turn 獨立重算 Reality Card、提交 StateDelta、生成 bounded prose 並通過 capacity Gate。超過行動數、區域數、計畫步驟或新實體注意上限時，保存 rejected attempt，不修改 authoritative state。
