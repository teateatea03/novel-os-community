# 角色資料最低可引用卡與補件契約

本規範同時供 `novel-character-deep-digger` 研究輸出與 `character-database-builder` 入庫使用。目標是讓角色資料可被可靠引用、驅動場景與查詢；**禁止只有名字、職稱、能力名稱或形容詞就視為完成。**

## 最低可引用卡（所有角色）

每個角色主節點以及被作品／專案實際引用的次要人物，至少保存：

1. **身份與範圍**：名稱／別名、主體分類、作品或公開紀錄、版本與正典範圍。
2. **來源錨點**：至少一個可回查 URL、作品章節／集數／官方頁，附短引文、場景或定位；資料不足應標 `UNKNOWN`／【待定】並說明原因。
3. **定位與能動性**：公開角色身分／職務或敘事位置；他／她可實際做什麼，而非僅貼性格標籤。
4. **至少一張能力卡或限制卡**：沒有已知能力時，明示「未查得可引用特殊能力；不可臆補」，並描述已知一般職能的證據範圍。
5. **行為錨點**：至少一條「情境／觸發 → 可見行動 → 後果或代價」。真人不得把未公開內心狀態寫成事實。
6. **脈絡或關係**：至少一項有來源的組織、事件、作品內關係或公開合作脈絡；資料不足時保留待查。

## 能力卡：絕不只存名稱

`capability_cards` 是角色主節點的陣列；複雜能力可以另建 `concept`／`resource` 節點，以 `has_capability`／`limited_by`／`trained_in`／`uses` 等關係連接。每一張卡至少有：

```yaml
name: 正典或公開名稱；未知則 UNKNOWN，不得杜撰
name_zh: 官方繁中優先；否則可靠讀音音譯或 UNKNOWN
category: combat|technical|professional|social|cognitive|physical|supernatural|other
scope_version: 適用作品、媒介、季別或公開資料截止日
what_it_does: 可觀察的效果、步驟與適用問題
basis_or_mechanism: 已明示的原理／訓練／工具；未知就標 UNKNOWN
preconditions: 所需情境、工具、權限、體力、訓練或資訊
limits_cost_risk: 範圍、冷卻／消耗、代價、失敗模式、反制與不可做之事
observable_evidence: 作品章節／集數／官方／本人公開來源的場景或短引文
confidence: EXTRACTED|INFERRED|AMBIGUOUS
inference_chain: 僅 INFERRED 時填「事實 → 脈絡 → 解讀 → 替代解釋」
last_verified: YYYY-MM-DD 或 UNKNOWN（尚未獨立查證）
```

- 不可把「駭客、戰鬥、聰明、領導力、Cosplay、直播」等名稱當卡片完成。至少要說明可觀察行為、前提與限制。
- 原作、動畫、電影、遊戲、改編季別與作者層提案各自建卡或寫清 `scope_version`，不可混成全版本萬能能力。
- 無法取得細節時：保留 `what_it_does: UNKNOWN`／`limits_cost_risk: UNKNOWN`，加入待查理由與來源缺口；絕不可用常識或同類角色設定填滿。
- 真人的技能限於公開作品、職業、本人表述或可驗證活動；不能把粉絲觀感、外貌、單次表現推成穩定專業能力。

## 角色引擎與行為補件

虛構角色的 `character_model`／`behavior_model` 需分【明示】與【推論】，至少涵蓋：外在目標、核心恐懼或壓力源、慣用策略、觸發、代價、關係／權力差異、疲勞／資源匱乏時的改變。真人只建立有公開行為證據的工作／創作模式，且保留替代解釋。

## 資料庫完整度欄位

角色主節點新增／維護：

```yaml
data_completeness:
  minimum_citable_card: complete|partial|missing
  identity_scope: complete|partial|missing
  evidence: complete|partial|missing
  capability_detail: complete|partial|missing
  behavioral_anchor: complete|partial|missing
  relationship_context: complete|partial|missing
character_research_state:
  character_importance: lead|major_supporting|minor_functional
  work_stage: discovery|draft_diagnostic|revision
  profile_depth: L0|L1|L2
  model_status: MODEL_DRAFT|SCENE_TESTED|REVISION_CALIBRATED
  validation_tests: []
  counterexamples: []
  competing_models: []
source_families:
  - source_family_id: ...
    original_source_url: ...
    intermediary_chain: []
    independence_status: independent|shared_origin|unknown
    original_retrieved: true|false
required_before_story_use: true|false
open_research_gaps:
  - 欠缺內容與原因
```

- `required_before_story_use: true`：該角色會被當成主要 POV、重要 NPC、衝突解法或能力依據時，最低可引用卡必須 `complete`；否則只能以已證實範圍使用，不能拿未知能力推動關鍵情節。
- 批量資料庫先補「已存在但密度最低、且會被引用」的角色；不可藉由新增更多只有名稱的節點製造虛假完整度。

## 每次批量補件後的驗證

1. 先 snapshot，再增量更新；不覆寫舊主張。
2. 跑 `character_coverage_audit.py`，檢查 P0／P1 缺口。
3. 每張新增能力卡核對 `what_it_does`、`preconditions`、`limits_cost_risk`、`observable_evidence`、`confidence`；任一缺失即列入 `open_research_gaps`。
4. 跑圖譜 validator；EXTRACTED 節點／關係需有來源。
5. 若入庫公開比對圖：檔在 `visuals/<sha256>.<ext>`，sidecar 與 `visual_refs`／`has_visual` 一致；同一 hash 不重複存。缺圖不是 P0。見 `visual-comparison-store.md`。
6. 報告「已補」、「仍 UNKNOWN」、「版本衝突」、「不能安全推斷」；不要以描述性摘要掩蓋未知。
