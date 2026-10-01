# 正典缺口行為補全：用人類行為與心理學生成可寫候選

適用情境：非真人角色已完成版本／witness 研究，但某個新場景沒有正典答案，而小說仍需要角色選擇、台詞、反應或關係發展。

核心原則：**補可寫性，不補成原作事實。** 心理學提供基準率、因果語彙與候選生成；它不能發現角色「其實」有某種創傷、依附型、診斷或秘密童年。

## 1. 外部實務的共同答案

### 演員／導演

Stanislavski 類 given circumstances、objective、obstacle、action／beat，以及 Practical Aesthetics 的 literal→want→essential action→as-if，都先從劇本事實與可玩的動作出發。演員常需補 subtext，但補的是**此場可演假說**，並在排練中比較，不是宣告隱藏傳記真相。情緒不是命令；先做可觀察 action，情緒由情境產生。

### 編劇／改編作者／授權 tie-in 作者

既有角色寫作會研究 canon、語音節奏與 continuity，利用小說內心視角深化角色，但新增內容必須能嵌入既有／未來正典。常見做法是從外在 desire、scene objective、obstacle、既有弱點／界線與 subtext 推導；新增 backstory 是可撤回的工作假說。Tie-in 寫作的困難正是「能更親密地進入角色」也更容易超出授權／正典。

### 專業小說作者

Foxwell 等 181 位專業作家研究顯示，許多作家會感到角色有聲音與自主性。這可理解為作者內化角色後的社會模擬／agency tracking；適合測「角色會不會拒絕情節」，但不產生 canon authority。

### 臨床心理 formulation／人格心理

資料不足時用可修訂工作假說、競爭模型、觸發／維持／保護因素、基準率與推翻條件。人格描述的是分布與 if–then，不是單次行為腳本；診斷與童年因果不能無證據回填。

### 可信 NPC／believable agents

Oz／believable-agent 傳統與遊戲 NPC 實務重視目標、自主動機、情緒 appraisal、反應式行為、社會記憶與跨語言／動作一致的強人格。其目的不是完整模擬大腦，而是以足夠廣度、清楚藝術選擇創造「生命感」。

### 心理師兼小說家

Bev Thomas 強調 why now、說與不說、過去如何留在現在、改變會反覆；Jonathan Kellerman 的實務提醒：心理學找規則，小說也關心越過規則的人。基準率是起點，例外需要條件，不是禁止例外。

## 2. 何時可以啟動

只有同時成立才啟動 `CANON_GAP_BEHAVIOR_COMPLETION`：

1. 已鎖定 target character instance、continuity 與當前場景時間；
2. 已完成合理的 primary witness 搜尋／sampling，缺口仍為 `CANON_UNKNOWN`；
3. 使用者要續寫、改編、互動或補完，確實需要角色現在行動；
4. 新行為不會被誤包裝成原作、作者意圖或跨版本事實；
5. 有可撤回／比較的創作分支，且作者選擇前不升 canon。

若缺口其實可由尚未查的正典回答，先研究，不用心理學偷填。

## 3. Mind Architecture Gate

先判定角色能多大程度套用人類心理：

| 模式 | 適用 | 心理學使用方式 |
|---|---|---|
| `HUMAN_BASELINE` | 虛構人類，作品未改寫基本心智 | 可用人類基準率，但受文化／年代／制度調節 |
| `HUMAN_DERIVED` | 義體人、長生種、變種人等，仍有明確人類發展／社會化 | 人類模型為骨架；逐項修改身體、壽命、記憶、風險、文化 |
| `ANTHROPOMORPHIC_ANALOGY` | AI、機器、神祇、外星／非人，作品呈現類人目標情緒 | 只在已展示功能上類比；不得預設荷爾蒙、依附、睡眠、死亡焦慮、童年 |
| `NONHUMAN_MODEL` | 蜂群、集體意識、異質認知、規則型存在 | 先建作品內 perception／memory／utility／identity／time 模型；人類心理只作對照 |
| `SYMBOLIC_OR_FLAT` | 寓言、喜劇吉祥物、功能型角色 | 優先類型／象徵／節奏一致，不強迫完整臨床深度 |
| `UNKNOWN` | 證據不足 | 只做最低行動候選，不發明深層內在 |

Gate 維度：身體／生理、感知、記憶、情緒、依附／社會、時間感、死亡／損失、能動性、語言、自我連續性。每個維度標 `humanlike|modified|nonhuman|unknown`。

## 4. 補全階梯：低推定優先

### Tier 0｜正典直接延伸

從相似場景 E1/E2、明示目標、關係與能力，做最窄延伸。例：角色多次在危機先封鎖通道；新危機仍可把「先控制資訊／出口」列高順位。這是 `CANON_CONSTRAINED_INFERENCE`，不是新心理背景。

### Tier 1｜場景行動補全

用演員方法，不先發明童年：

1. Literal：場上客觀發生什麼？
2. Given circumstances：時間、空間、關係、權力、身心／機體狀態、剛發生什麼。
3. Scene objective：他要對方／世界在本場結束前做什麼？
4. Obstacle／stakes：什麼阻擋，失敗失去什麼？
5. Playable actions：2–4 個及物動詞策略，如試探、拖延、逼迫、安撫、轉移、結盟、撤離。
6. Beat change：收到何種新資訊時改策略？

輸出 `PERFORMANCE_HYPOTHESIS`。它足以寫場景，通常不需要完整人格學說。

### Tier 2｜人類行為基準率

當 Tier 0/1 仍無法排序，以 E5 心理／行為研究提供先驗：威脅評估、損失規避、地位／羞恥、認知負荷、依附／互惠、強情境、疲勞疼痛、群體規範等。只回答「一般人在這些條件下哪些反應較常見」，不能決定角色一定如此。

每個 prior 必須寫：適用人群／情境、對此角色可遷移性、世界差異、可觀察預測、失效條件。

### Tier 3｜競爭 psychological formulations

只為解決跨多場的反覆缺口，建立 2–3 個競爭模型：

- M1 最小正典模型；
- M2 同樣符合正典的替代模型；
- M3 戲劇性較高、需新增條件的方案。

每個模型有：正典支持、human prior、反證、會預測的下一行為、不能解釋什麼、最小新增設定、可撤回性。不得把 attachment／trauma／core belief 當預設答案。

### Tier 4｜新增形成史／背景

只有當多個未來場景都需要、Tier 0–3 無法穩定驅動，才提出 backstory。新增設定遵守：

- 最小充分：只加能改變選擇的部分；
- 多方案：至少兩個不同形成史能產生相近現在；
- 非診斷：不用疾病名稱代理角色；
- 世界相容：年代、文化、物種、制度與技術成立；
- 明示代價：新增背景會關閉哪些情節可能；
- 作者核准：採用前 `ADAPTATION_PROPOSAL`，核准後只成為本小說 `AUTHOR_CANON`，不回寫原作。

## 5. 六層標籤，禁止倒灌

- `SOURCE_CANON`：primary witness 直接支持。
- `CANON_UNKNOWN`：合理研究後仍未交代。
- `CANON_CONSTRAINED_INFERENCE`：由同版本行為與條件窄推。
- `HUMAN_PRIOR`：心理學／行為學群體基準率。
- `PERFORMANCE_HYPOTHESIS`：演員／導演式可演方案。
- `ADAPTATION_PROPOSAL`：為本小說新增。
- `AUTHOR_CANON`：作者核准後，只對本專案有效。
- `REFUTED_BY_CANON`：與正典衝突，不得採用，除非明示 AU／retcon。

下游輸出不得把後五者寫成「原作其實暗示」。

## 6. Canon Constraint Envelope

補全前建立不可侵犯包：

```yaml
character_instance: ...
continuity: ...
scene_time: ...
source_state_hash: ...
known_facts: [...]
observed_behavior_anchors: [...]
known_voice_constraints: [...]
knowledge_limits: [...]
relationship_state: [...]
world_and_body_constraints: [...]
explicit_unknowns: [...]
forbidden_inferences: [...]
future_continuity_constraints: [...]
```

`forbidden_inferences` 例：沒有證據不得新增童年虐待、診斷、戀愛、性史、創傷、仇恨、秘密血緣；非人角色不得無聲加入人類生理與發展史。

## 7. 候選生成與選擇

每個缺口至少產生：

1. **最小延伸 A**：最接近已展示策略；
2. **情境變體 B**：因關係／資源／狀態而換策略；
3. **反常但成立 C**：需要明確觸發／代價的少見行為；
4. 必要時 **不可知 D**：以沉默、延遲、拒絕回答或場景結構保留空白。

對每個候選評估：

- canon compatibility
- objective fit
- mind-architecture compatibility
- human-prior fit
- relationship／knowledge fit
- voice／attention fit
- dramatic utility（只作 tie-breaker）
- added-assumption cost
- future-continuity risk
- falsifier／revision trigger

優先採「足以驅動場景、但新增假設最少」的候選。高戲劇性不能壓過正典。

## 8. Rehearsal／Scene Lab

心理模型不能只在表格裡成立。對前兩名候選各寫同一場景 150–400 字或 blocking/dialogue sketch，保持外部事件相同，只改角色策略。執行：

- name masking／voice blind test；
- interchangeability：換成同類角色是否仍完全相同；
- counterexample：哪個既有場景最反對此方案；
- audience inference：讀者能否從動作推到預期內在，而不靠解說；
- consequence test：此策略下一場留下什麼不同後果；
- actor playability：能否用動詞演，而不是「演得很焦慮」。

通過者是 `SCENE_TESTED_PROPOSAL`，仍非 source canon。

## 9. 心理學能補與不能補

### 可以補

- 在給定資訊、目標、關係、身體／機體與風險下的候選反應；
- 缺乏同類場景時的行為先驗；
- 合理的猶豫、誤判、防衛、維持、保護與代價；
- 新場景需要的 objective、action、subtext 與 beat change；
- 多個可能形成史及其不同戲劇後果。

### 不能補

- 原作者未寫的「真正內心」；
- 唯一正確童年／創傷／依附型；
- 精神診斷；
- 另一 continuity 的人格；
- 只因是類人外形就套用人類生理；
- 以群體平均覆蓋角色已展示的反例；
- 以「心理合理」宣稱某走向必然。

## 10. 與現有校準閉環

- Evidence：SOURCE_CANON 對應 E1–E4；HUMAN_PRIOR 是 E5；PERFORMANCE_HYPOTHESIS／ADAPTATION_PROPOSAL 是 E6。
- Reality Card／world rules 先限制可行行為；Mind Architecture Gate 再決定人類 prior 可遷移多少。
- 重大節點照常建立 Prediction Lock；`model_origin` 記哪一 Tier。
- 作者選擇不算預測命中；章後 resolution 若多次支持某 if–then，可提升本專案模型成熟度，但永不回升成 source canon。
- 原作日後出現新材料：重新跑 canon conflict；衝突時本專案可 retcon、分支 AU 或保留 adaptation divergence，不改寫歷史標籤。

## 11. 實務來源

- Stanislavski：given circumstances、objective、units/beats、action；以行動而非直接「演情緒」。
- Practical Aesthetics：literal、want、essential action、as-if；可演行動優先。
- Tie-in novel 實務：canon／continuity 約束、角色 voice、內心親密性與授權邊界。
- TV writers’ room：living character bible、continuity tracking、character advocate、collective story breaking。
- Adaptation screenwriting：把內在外化成行動／subtext，保留作品 heart 而非逐項複製。
- Foxwell et al. (2020)：181 位專業作家的角色聲音與自主感。
- McAdams／Fleeson／formulation／Prediction Lock：人格分布、目標、自我故事、競爭假說與校準。
- Bev Thomas：why now、說與未說、過去在現在的痕跡、非線性改變。
- Jonathan Kellerman：心理學找 predictive rules；小說也寫 transgressions。
- Bates／Oz Project／believable agents：目標、情緒、反應式規劃、強人格與藝術性簡化；不要求完整人腦模擬。
