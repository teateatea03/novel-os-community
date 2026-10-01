# 跨技能自動路由（詳細規格）

本文件從主技能拆出，以保持核心 SKILL.md 可快速載入。涉及圖譜、世界觀或風格時才讀取相關段落。

## 關係圖譜

載入 `../knowledge-relationship-graph/SKILL.md` 和 `../knowledge-relationship-graph/references/novel-domain-profile.md`。圖譜是正典文件的**衍生索引、上下文檢索與影響分析層**；定稿正文、故事／世界聖經和使用者決定仍是來源真相。

### 啟動與同步

在新專案初始化、章前組裝人物／地點／事件／祕密／伏筆子圖、章後改變人物關係／知識／物件／位置／派系／規則／因果／伏筆、改綱或修改關鍵身分／事件，以及使用者詢問牽連／影響／知情時載入。每 3–5 章或每卷做孤點、別名、過期關係、未回收伏筆和高風險樞紐檢查。

- [CANON]／[LOCKED] 關係可作 active；[PLAN]／[DRAFT] 必須有 status，不混進「目前真相」。
- 每條重要 edge 附 source_file、source_location／章節與證據；EXTRACTED 無來源要警告。
- 變更關閉 valid time，不刪舊 edge。圖譜與來源衝突時修圖，不修正典。

### 章前／後

章前用 `graphify query/path`、`relationship_graph.py neighbors/timeline --as-of/affected` 找子圖和來源，再回讀來源檔。章後先更新正典帳本，回寫章／場景、POV、事件參與者／因果、關係 valid interval、knows／believes／misbelieves／conceals_from、物件轉移、伏筆與世界規則；最後 validate/export。圖譜失敗標 WARN，不得阻止正文保存。

改綱：先 snapshot，再從修改節點沿 causes／depends_on／appears_in／knows／foreshadows 深度 2–4 查 affected，標 stale／cascade_pending；作者確認後更新正典、摘要、帳本與圖譜，重建輸出與 context pack。

## 世界觀

載入 `../novel-worldbuilding-architect/SKILL.md`。它決定世界允許、限制和回應什麼；心理行為技能決定人物／組織在可見選項中較可能如何行動；風格技能決定讀者如何得知。若既有非真人正典沒有回答新場景行為，先由 deep-digger 確認 `CANON_UNKNOWN`，再讀 behavior consultant 的 `references/canon-gap-behavior-completion.md`；先判定 human/nonhuman mind architecture，不能把人類心理默認套給 AI、神祇、蜂群或異質心智。

### 啟動與章前包

在建立世界、進入新地點／國家／階級／文化、首次使用或改變科技／魔法／種族／宇宙規則、情節涉及法律政治經濟戰爭犯罪災難交通通訊疾病資源、世界規則將成反轉／高潮條件、發現地理物流權力史或認知版本衝突時載入。每章後有新設定，及每 3–5 章／每卷檢查二階後果。

章前只讀相關：[CANON]/[LOCKED] 規則；空間、出入口、交通通訊與資源；派系合法性／執行力／策略；科技魔法的資格成本反制例外；[TRUTH] vs [OFFICIAL]/[BELIEF]/[RUMOR]/[KNOWN]；人口物流法律時間文化對選項的限制；及可能公共後果。

A/B/C 先檢查世界結構（資源時間制度技術資訊）是否成立，再以行為技能建立 Evidence、Actor 狀態分布、情境強度、保護／抑制與不可覆寫 Prediction Lock，然後檢查伏筆成熟度，最後只用類型風格決定呈現。候選預設用序位／寬區間；未達校準門檻不得強制湊成 100% 的精細百分比。世界設定透過程序、價格、路線、工作、稱謂與後果進場；即興細節先標 [DRAFT]。

`special-object-database-builder` 的特殊物本體、版本、能力、規格、能源／彈藥、限制／反制、模組、持有／操作、損傷／維修／升級與事件時間線可由本技能章前查詢並於章後回寫；其正本另存於 `SPECIAL_OBJECT_DATABASE_ROOT`，小說圖譜只保存交接所需的穩定 object ID 與章節／場景關係。

## 特殊物交接

特殊物不是一次性道具描寫。需要物件本體、版本、能力、規格、能源／彈藥、限制／反制、模組、持有／操作、損傷／維修／升級、事件時間線、來源證據或跨版本比較時，先讀 `../special-object-database-builder/SKILL.md`。章前交接至少要取得：object ID 與版本正典、目前位置、持有者／操作員、可用性／損傷、能源／彈藥／冷卻、已裝模組、能力啟動條件與代價、角色可知版本、下一個補給／維修／失效時鐘，以及不可臨時新增的解法。

章後只回寫已核准的物件差分：取得／交接、位置、持有／操作、能力使用與消耗、能源／彈藥、損傷／維修、模組裝卸、改裝／升級、曝光、派系反應、伏筆與延遲後果。若正文即興出現新能力、新版本規格或新物件來源，先標 `[DRAFT]`／`[PROPOSAL]`，不得靜默升為 `[CANON]`。

## 風格工藝

載入 `../novel-style-craft-director/SKILL.md`，不得憑記憶模糊套用。衝突優先序：使用者 [LOCKED]／內容契約 → 正典／資訊權限 → 心理行為因果 → 主類型讀者承諾 → 風格契約 → 局部修飾。

### 啟動與路由

在新專案／style sheet 不可檢查、使用者指定類型作家流派讀感換文風、特殊場景模式、故事類型／視角／時間轉換、每 3–5 章或每卷防漂移、角色同聲／節奏失衡／解說過量／意象句型重複／類型感不足，以及成人題材與同意權力界線時載入。

- 寫實／心理／現代主義／極簡／日本近代內省：`references/literary-psychological.md`
- 推理／黑色犯罪／間諜驚悚／恐怖哥德：`references/suspense-crime-horror.md`
- 科幻／奇幻／魔幻寫實／反烏托邦／諷刺：`references/speculative-and-satirical.md`
- 歷史／武俠／古典群像／愛情／家族史詩：`references/historical-wuxia-relationship.md`
- 成人題材／成熟關係／親密情色／同意權力：`references/adult-mature-intimacy.md`
- 混合類型：`references/style-blending.md`

只讀本章需要包，不做聲紋拼貼。章前從 style sheet 讀八軸、主引擎、鏡頭、語言質地、局部規則、禁用手法與漂移警報；先決定可見選項和行為，再以類型組織阻力資訊轉折代價，以鏡頭控制資訊，最後才套語言。漂亮句不能改變因果或角色聲音。

成人題材不等於露骨：讀取作者指定年齡／身分、關係、級別、界線、權力、立場、露骨程度與禁用內容；心理技能處理行為條件、風格技能處理距離與詞彙、長篇技能追蹤後果。模型或供應商的限制獨立適用，技能不得覆寫。
