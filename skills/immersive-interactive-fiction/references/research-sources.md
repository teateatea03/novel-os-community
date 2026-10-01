# 沉浸式互動小說：研究來源與設計轉譯

> 研究日期：2026-08-01。此文件保存方法論來源、能支持的設計結論、限制，供 `immersive-interactive-fiction` 技能引用。連結均為公開頁面；搜尋摘要只作線索，重要結論優先由一手作品、開發者文件或學術論文支持。

## 2026-08-09 第四輪補充：durable workflow 與敘事模型檢查

### Temporal Workflow Execution／Worker Versioning
- 來源：Temporal 官方文件，https://docs.temporal.io/workflow-execution ；官方搜尋索引中的〈Safely deploying changes to Workflow code〉與各 SDK Versioning 文件。
- 方法：durable workflow 以 event history 重播恢復；外部工作是可等待、重試、取消的 activity；工作流程式升級前用歷史 replay 測試，舊執行可由相容 build／patch 路徑承接。
- 轉譯：Novel OS 除 state migration 外，事件必須帶 producer runtime build 與 transition contract；未知 contract fail closed。外部模型微任務以持久 activity 保存 scheduled／running／completed／failed／cancelled／stale、worker lease、attempt 與 max attempts。升級前用 golden-history fixture 重播到相同 state hash。
- 限制：Novel OS 是本地檔案 runtime，不宣稱具備 Temporal 叢集的全球擴展、服務端排程或 exactly-once 網路傳輸；採用的是 replay safety 與 durable activity 工程原則。

### Yarn Spinner Story Solver
- 來源：Yarn Spinner 官方，https://www.yarnspinner.dev/story-solver ；Yarn Spinner 文件首頁 https://docs.yarnspinner.dev/ 。官方說明其以自動 theorem prover 檢查故事邏輯、不可達內容、soft lock 與 broken quest state。
- 轉譯：對具有明示 conditions／effects／exits 的 storylets 做 bounded state exploration，回報 unreachable、broken target、open-thread soft lock 與截斷界線；發佈前將這份報告視為結構 Gate。
- 限制：自由輸入小說的行動空間不可完整枚舉；求解器只涵蓋顯式 storylet 子圖，不把有限探索 PASS 誇大成整部作品的數學完備證明。

### Novelcrafter Codex／Series Codex
- 來源：Novelcrafter 官方 Help 的 Codex、Series Codex、Codex Entry／Relations 文件，https://www.novelcrafter.com/help/docs/category/codex 。
- 方法：集中管理人物、地點、物件、lore、關係與 book／series scope，並按進度更新條目。
- 評估：Novel OS 的角色／世界／特殊物 Graphify、時間化 relation、source evidence 與 knowledge scope 已更嚴格；Codex 的優勢在作者 UX 與低摩擦整理，不需要另建平行正本。本輪維持 author console 為 projection，優先補 runtime 安全而非複製商用 UI。

### ink／Twine 再確認
- 來源：ink GitHub https://github.com/inkle/ink ；Twine Story Formats https://twinery.org/reference/en/story-formats/ 。
- 評估：ink 的 story-format／save-format 版本分離與可編譯 JSON runtime，再次支持 Novel OS 將內容格式、狀態格式與 runtime transition contract 分離；Twine 可替換 story format 支持 renderer／runtime adapter 與正典資料解耦。Novel OS 不改成預寫分支語言，保留自由輸入與 deterministic host 裁決。

---

## 結論摘要

本技能採用的形式是「第二人稱、自由輸入、GM／導演式、狀態持續型互動小說」。它不是預寫分支樹：玩家掌控一名角色的意圖、行動與發言；主持者模擬世界、時間、NPC 的目的與後果；每回合從持久世界狀態選出當下可發生的場景節點（storylet），再以小說語言呈現。

沉浸的來源不是大量文字或無限選項，而是：1) 行動被世界具體承認，2) NPC 有獨立目的，3) 時間與資訊不會倒流，4) 空間、物件、關係與未結事件能持續影響後文，5) 玩家可改變方法但不能任意控制結果。

---

## 資料來源與驗證層級

- **A 級（一手／官方）**：Inform、Twine、ink、Choice of Games、80 Days、Ironsworn、Punchdrunk 與作者／開發者官方頁。用於確認系統實際功能與作品設計聲明。
- **B 級（同行評審／正式論文與專書）**：Mateas & Stern、McCoy et al.、Riedl & Young、Machon、Alston。用於支持一般化設計推論。
- **C 級（開發者訪談、技術演講、歷史專案介紹）**：Versu、Façade 的補充脈絡。可用於工藝線索；若和一手／學術資料衝突，以 A／B 為準。
- **研究限制**：本技能不從搜尋摘要推導獨立結論；搜尋只用來定位來源。歷史網頁可能失效，保留作品、作者、出版年份與 DOI／官方頁便於後續復核。

## A. 文字冒險與世界模型

### Inform 7／Interactive Fiction Technology Foundation
- 來源：Inform 官方網站，https://inform7.com/ ；Interactive Fiction Technology Foundation，https://iftechfoundation.org/
- 方法：以場所、方向、容器、物件、角色、可行動性及規則維護一致的可互動世界模型。解析器遊戲的價值不在命令格式，而在「玩家能嘗試非預列動作，世界仍有可推理反應」。
- 轉譯：每個場景必須記錄地點、在場人物、可見出口、顯著物件、物件位置／持有者、阻礙與時間壓力。玩家輸入不在清單內，先依世界狀態裁決可行性，再敘事化。
- 限制：不要假裝完整物理模擬。只對故事有影響的物件與規則進入狀態；不重要動作以簡短但可信的回應處理。

### Emily Short：World Models Rendered in Text
- 來源：Emily Short，〈World Models Rendered in Text〉，2018，https://emshort.blog/2018/06/19/world-models-rendered-in-text/
- 方法：文字敘事中的世界模型可以包含多個互動層，將物件、場所、人物狀態與文字輸出連結；文字不是單純裝飾，而是模型的可見表面。
- 轉譯：狀態紀錄與正文必須互相校驗；「門鎖上」「杯子在桌上」「某角色不知道某事」不可只存在其中一邊。玩家看見的是有選擇性的感官輸出，而非資料庫全知清單。

---

## B. 動態敘事、Storylet 與品質狀態

### Emily Short：Storylet 脈絡
- 來源：Emily Short，〈An Introduction to Storylets〉，2019（原網址已可能改版），可由作者站內與 Google Scholar／IF 社群索引核對；另見 Tanya X. Short，〈Storylets: You Want Them〉，GDC 2017，https://www.gdcvault.com/play/1024390/Storylets-You-Want-Them
- 方法：storylet 是帶有出現條件與結果的短敘事單元，不依賴單一、脆弱的分支樹。當玩家狀態符合條件，相關事件可在合適時機浮現。
- 轉譯：使用「可用條件 → 場景壓力 → 玩家自由反應 → 狀態結果 → 未結鉤子」五段式。條件可包含：場所、時間、角色在場、信任／戒心、已知秘密、持有物、時鐘與前置事件。不要把每個行動預寫成固定頁面。
- 限制：storylet 不是隨機事件清單。每個節點必須服務人物目標、關係或主線壓力，且避免重複同一情緒節拍。

### Failbetter／Fallen London 的 quality-based narrative
- 來源：Failbetter Games，Fallen London 官方頁，https://www.fallenlondon.com/ ；官方 Help／wiki 對 qualities 與 storylets 的公開說明。
- 方法：以可見或隱藏的 qualities（品質／狀態）決定事件可用性、結果與文字差異；玩家歷史成為未來內容的條件。
- 轉譯：關係不可壓成單一「好感度」。至少分開信任、戒心、依賴、權力、親密、怨懟、債務與已知資訊；只追蹤會改變決策或場景的軸。讓少量文字差異反映玩家歷史。

### ink／inkle
- 來源：inkle，ink 官方文件，https://www.inklestudios.com/ink/ ；ink GitHub，https://github.com/inkle/ink
- 方法：文字優先、節點與選項可交錯，支援變數、條件、標籤、執行測試。ink 的重點是作者掌握敘事節奏，而非無限制支線。
- 轉譯：每回合都要有一個可感知的「場景問題」，而非無邊界閒談；用標記管理場景目的、知識揭露、角色在場與後果。必要時提供策略性提示，但不得把提示偽裝成唯一可行動作。

### 80 Days／inkle
- 來源：inkle，80 Days 官方頁，https://www.inklestudios.com/80days/ ；GDC Vault 與開發者訪談可檢索其動態旅行敘事設計。
- 方法：時間、資源、路徑、世界事件與人物邂逅互相限制；可重玩性來自狀態組合與視角，不是大量互斥結局。
- 轉譯：對長篇互動小說使用「有限壓力」：時鐘、日程、資源、外部風險、錯過成本。玩家有能動性，但任何選擇都可能關閉其他機會。

---

## C. 角色自主、社會模擬與戲劇管理

### Façade：Interactive Drama Architecture
- 來源：Michael Mateas & Andrew Stern，Façade 官方／研究頁，https://www.interactivestory.net/ ；〈Architecture, Authorial Idioms and Early Observations of the Interactive Drama Façade〉，2005，可於 ACM Digital Library 檢索。
- 方法：結合戲劇管理（drama management）、角色行為與玩家輸入解讀，讓系統在維持戲劇張力時允許自由輸入；以 beats（戲劇節拍）安排局部場景目標。
- 轉譯：每場景定義「壓力問題」與 1–3 個可能節拍，例如試探、迴避、揭露、反轉、離場；NPC 可追求自己的局部目標。主持者不強推預定結果，而是保持衝突仍活著。
- 限制：不可為了劇情把玩家行動抹除或替玩家角色決定情緒。戲劇管理只控制世界如何回應、何時施壓、何時揭露。

### Prom Week／Comme il Faut
- 來源：McCoy, Treanor, Samuel, Reed, Mateas & Wardrip-Fruin，〈Prom Week: Social Physics as Gameplay〉，FDG 2011，https://users.soe.ucsc.edu/~michaelm/publications/McCoy2011PromWeek.pdf
- 方法：Comme il Faut（CiF）以社會規範、關係網與角色偏好推動互動；人物會判斷行為在當前關係與場合下是否合宜。
- 轉譯：NPC 行動需由「欲望／恐懼、知識、關係、地位、正在保護的事、當前場景規範」推導。記錄關係的方向性：A 信任 B，不代表 B 信任 A。
- 限制：數值不能取代人物。每次 NPC 關鍵行動要能用一句角色內在理由說明。

### Versu
- 來源：Richard Evans & Emily Short，Versu 介紹與技術文章，http://www.versu.com/ （歷史專案）；Short 的專題文章與 GDC 談話可檢索。
- 方法：以社會實踐（social practices）和角色可供性模擬一組人物在同一情境中各自能做、想做與認為合宜的行為。
- 轉譯：在多人場景中，不把所有 NPC 排隊等玩家。每回合至少檢查誰可能插話、離開、觀察、結盟、掩飾或採取與玩家無關的行動。

### Narrative Planning：平衡劇情與角色
- 來源：Mark O. Riedl & R. Michael Young，〈Narrative Planning: Balancing Plot and Character〉，JAIR 39 (2010), 551–585，https://doi.org/10.1613/jair.2989
- 方法：敘事規劃試圖使角色行為在其目標與故事事件間保持因果合理，避免「角色為了劇情突然做不會做的事」。
- 轉譯：每個重大轉折都必須同時通過兩項檢查：它是否由既有世界因果觸發？它是否符合涉及角色當下掌握的資訊與目標？若不通過，改為鋪墊、誤解、代價或另一條世界反應。

---

## D. 主持、自由輸入與安全協商

### 單人／GM-less 角色扮演與 Oracle
- 來源：Ironsworn 官方 SRD，https://www.ironswornrpg.com/ ；The Solo Adventurer’s Toolbox（Paul Bimler）；Mythic Game Master Emulator（Word Mill Games）。
- 方法：用場景問題、角色目標、隨機／不確定性 oracle、事件焦點與進度軌道，在沒有固定主持人的狀況下保持意外與節奏。
- 轉譯：主持者在不確定結果時不要暗中偏袒預設劇情，可明示成功／部分成功／失敗／代價四種可能；以「時鐘」追蹤接近、暴露、危機、信任崩解等進程。小說模式不必骰骰子，但必須保留真正的不確定性。

### TTRPG 安全工具：Lines、Veils、X-Card、Script Change
- 來源：John Stavropoulos，X-Card，http://tinyurl.com/x-card-rpg ；Beau Jágr Sheldon，Lines and Veils（多個公開整理）；Brie Sheldon，Script Change RPG Toolbox，https://briebeau.com/thoughty/2019/02/script-change-rpg-toolbox/ 
- 方法：在開始前協商禁止元素（lines）、可存在但淡出處理的元素（veils），進行中允許跳過、倒帶、暫停、慢鏡與快速前進。
- 轉譯：把它做成玩家隨時可用的敘事控制語：`停`、`淡出`、`跳過`、`回到上一節點`、`慢一點`、`快轉`、`只寫外部`、`切換視角`。這些是體驗調節工具，不是角色世界中的行動。

---

## E. 沉浸、空間與觀眾能動性

### 沉浸式劇場與 Sleep No More 脈絡
- 來源：Josephine Machon，《Immersive Theatres: Intimacy and Immediacy in Contemporary Performance》，2013；Punchdrunk，《Sleep No More》官方檔案，https://www.punchdrunk.com/ ；Adam Alston，《Beyond Immersive Theatre》，2016。
- 方法：觀眾用移動、注意力與路徑形成個人經驗；空間、物件、聲音、遮蔽與「同時發生但無法全看」創造臨場感。
- 轉譯：場景以可行走、可觸摸、可躲藏、可聽見的空間寫成，而非只有人物對話背景。讓玩家選擇關注哪個線索；保留看不見的外部事件與錯過感，但不能用隱藏資訊否定已給出的事實。

---

## 交叉設計原則

1. **自由輸入 + 有界世界**：接受任何角色行動意圖，但以場所、人物、時間與能力決定結果。
2. **作者／主持者不是玩家角色的操縱者**：不替玩家做重大情緒、道德或行動決定；可以描寫可觀察的身體反應與世界後果。
3. **狀態最小化**：只記錄日後能造成敘事差異的資料，避免「每句話都入庫」。
4. **NPC 是行動者**：每一主要 NPC 都有近期目標、長期需求、恐懼、秘密／未知與可接受代價。
5. **節拍不是鐵軌**：每一場景保留壓力與可變的節拍，不預定玩家必達某結局。
6. **後果可見、但可延遲**：玩家要能理解因果，不必立刻知道所有後果。
7. **每回合結於張力**：新資訊、選擇、威脅、關係變化或時間推進至少一項；不要用空泛「你要怎麼做？」結束。
8. **持久性優先**：正文、狀態檔、事件紀錄與讀者已知資訊保持一致；重大反轉要檢查前文。

## 不採用的模式

- 純分支樹：很快組合爆炸，且玩家常覺得選擇是假的。
- 單一好感度：抹平信任、恐懼、慾望、依賴與權力。
- 無摩擦許願機：玩家每句話都讓世界與 NPC 屈服，沒有代價與自主性。
- 純隨機事件：沒有角色與主題因果。
- 不可逆硬鎖：除非玩家明確要求高風險模式，否則每個重大節點保留可見的替代策略或回顧點。
