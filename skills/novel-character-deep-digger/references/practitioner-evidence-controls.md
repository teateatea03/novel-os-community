# 實務者證據控制：按錯誤觸發，不另造一套台帳（v1.12）

配合 `practitioner-workflow.md` 使用。以下卡片是本系統對已讀實務的改編，不冒稱官方 schema；寫入既有 review 的附記或 sidecar，回指 question／event／claim ID。新欄位不是現有 validator 已檢查的語義保證。

## A. 「沒找到」何時才構成負向證據？

依 Mills QuickLesson 13 與 NARA 的具體限制（E1／E2）：先查紀錄形成與保管制度，而非搜完三個網站就認定不存在。

觸發：要由缺載推出不存在、未參加、未任職、沒有某種行為。

`absence_assessment` 最少交代：
1. 精確命題與最窄結論（哪份名冊／哪段期間／哪個版本）。
2. 理應記錄的機制及來源：強制登記？自願填寫？選編？
3. 同系列正控制：已知理應存在的項目是否可找回？只證明找得到，不能單獨證明全集完整。
4. 形成單位、保管單位、移交或制度斷點、涵蓋時空與對象。
5. 保存、索引、數位化、缺頁與 OCR 品質；實際查過的範圍和別名。
6. 替代漏失原因與會推翻推論的新材料。

少了必要前提就保留 `search_nonresult`／查無，不用 `mode:negative` 冒充反證。NARA 官方「本館查無」也不能推出全世界不存在。自願名單、缺頁、只搜 OCR 或錯誤管轄皆不能證明未發生。

實際案例依據：NARA 自稱不能出具紀錄不存在證明；其 negative search letter 只限所管館藏。這個制度事實不能外推到所有國家；可借用的是「查無必有範圍」。

## B. 假獨立：出版者、提供者、觀測與記憶分開

依 GIJN 的 The Wire 撤稿案例、Buttry 的第一手回顧（E3／E4）。重大佐證附：

- `claimed_origin`：材料自稱來自誰。
- `supplied_by`：實際從哪個來源或中介拿到。
- `independently_retrieved`：是否透過不依賴該提供者的適當公開路徑取得；未知就 unknown。
- `observation_basis`：親歷、同期原件、回憶、轉述、未知。
- `dependence_notes`：共同新聞稿／同一提供者／共同討論或回憶的已知依賴；有證據才標，不猜串供。

三張不同署名截圖若全由同一中介提供，不等於三位專家獨立驗證。數位檔 hash 一致或獨特都不保證內容真實。另一方面，多位誠實親歷者也可能共同記錯：保留「他們如此回憶」與「可核對的事件」兩層，不用多數決。

遇口述矛盾再加 `recollection_comparison`：兩段原句與 locator、錄製時間、事件時間精度、問題句／上下文、親歷或轉述、剪輯版本、同期記錄與尚存解釋。後訪談不自動覆蓋前訪談，矛盾不證明撒謊或臨床問題。OHA 要求查核事實陳述、保留訪談情境（E5），不是把受訪者確認當成所有事件都真實。

不主動聯絡來源、使用私人信箱或擴大調查個人生活；本規則不增加資料取得權限。

## C. 當時知道什麼，決定哪個舊搜尋值得重跑

依 Mills 的實際 John Watts 研究工作例與 Bellingcat／GLAN 手冊（E6／E7）。不用第二套日誌；在研究 block 或非顯然 pivot 旁記：

`knowledge_at_search`（當時已知別名／候選／有效時期／版本）＋ `why_this_query`（哪條材料觸發改詞）＋ `resume_from`（下一個可執行起點）。

後來發現公開曾用名、職務或另一版本，建立 `revisit_trigger` 指向受影響的舊 zero 與新路由。只重查會改變問題答案的部分，不重跑整張清單。不可把後來才知道的線索回填舊事件；只有事後補寫過去決策才標 retrospective，現在發生的新搜尋與新知識應記本輪當下時間，不可誤標為回溯事件。

同名辨識比較 A／B 候選的有日期事件束與可靠 credit：哪些線索只「相容」，哪些能「區分」？保留第三候選可能性。Mills 的歷史報告示範同名、同遷移目的地仍不足以合併（E8）；不是授權追查當代真人鄰居或以簽名／人臉自動認人。

## D. 最終報告也要查：摘要會偷偷增加事實

依 Hanson／SVT 的逐項核對及整體選材審查（E9）。台帳通過之後，另抽查**最後要交付的文字**：

- 每個可驗句或子句能回到 claim／artifact locator，或明標分析／未知／創作。P0 深查之外，其餘實質事實也不能游離證據。
- 抽取時鎖定主體—動詞—客體／數量／否定範圍：一位來源否認自己的參與，不等於所有署名者都否認；中介未獨立核驗，不等於每個人的身份已證偽。摘要不得把局部更正擴成全體主張。
- 尤其看關係動詞、確定日期、數量、因果與意圖詞：合作≠受僱；邀請≠到場；沒遵守≠故意無視；記不清≠失智。
- 用簡短 `output_audit`：report 段落 → 可驗命題 → claim／locator → 原文是否支持「同樣強度」的措辭 → 修正。不是把所有修辭拆成欄位。
- 檢查最可能改變整體印象的已取得反例：若排除，理由是範圍、版本或品質，而不是不合預設故事。
- 「三次準時→責任感強」需展示推論橋梁、其他解釋及情境限制；文末三個腳註不能把人格推論升格成事實。

不要求每個小事兩個來源，也不製造正反各半的假平衡。結構一致不等於語義支持，此步目前仍為人工／代理查核，不能宣稱程式自動辨識所有誤導。

## E. 重大反證：重開及下游影響，而不只改一行

觸發：有可檢查的材料動搖關鍵證據身份、真實性或適用範圍；單純否認不是自動撤回指令。

1. 保存反證原文，暫停將受影響 claim 當確定事實輸出。
2. 經適當獨立路徑查原件，保留更正／不變及原因。
3. 列依賴它的時間線、關係邊、能力卡、人物解釋、正文使用點；檢查各項是否有其他證據仍可支持，不盲目連坐刪除。
4. 另存修訂和影響清單，依資料庫技能授權與 snapshot 流程增量更新；不擦掉原研究歷史。
5. 明列可恢復信心的證據條件，保留 CONTESTED／AMBIGUOUS／REFUTED 等現有 status。

例如「活動完成→加入組織→重視承諾」的原頁其實只是預告：三層都要重新檢查；不能只改活動日而保留依賴它的人格結論。借鏡 The Wire 案例的修復教訓（E3），不移植報警、懲罰或強制公開道歉作本技能操作。

## 來源與實際查閱範圍

- **E1** Elizabeth Shown Mills, *QuickLesson 13: Classes of Evidence—Direct, Indirect & Negative*；正文無日期。https://www.evidenceexplained.com/content/quicklesson-13-classes-evidence%E2%80%94direct-indirect-negative
- **E2** NARA, *Naturalization Records*；頁面審閱2025-09-10。FAQ negative search letter。https://www.archives.gov/research/immigration/naturalization
- **E3** Rowan Philp／GIJN (2023-01-30), *Lessons from a Retracted Investigation in India: How to Avoid Fabricated Evidence*。二手案例報導，未取得撤稿內部文件，不裁判責任。https://gijn.org/stories/lessons-from-a-retracted-investigation-in-india-how-to-avoid-fabricated-evidence/
- **E4** Steve Buttry, *Verification Fundamentals: Rules to Live By*；章頁日期unknown；開頭1996年回查冠軍賽的第一手回顧。https://datajournalism.com/read/handbook/verification-1/verification-fundamentals-rules-to-live-by/2-verification-fundamentals-rules-to-live-by
- **E5** Oral History Association, *Oral History Best Practices*；正文日期unknown。https://oralhistory.org/best-practices/
- **E6** Mills, *QuickLesson 20: Research Reports for Research Success*；正文日期unknown。https://www.evidenceexplained.com/content/quicklesson-20-research-reports-research-success
- **E7** Bellingcat／GLAN (last updated 14.12.2022), *Methodology for Online Open Source Investigations into Incidents Taking Place in Ukraine Since 24 February 2022*，PDF p.14。https://www.bellingcat.com/app/uploads/2022/12/JA-Manual-for-PUBLICATION.pdf
- **E8** Mills (2014-11-02), *Revolutionary War Capt. John Watts…*；29頁取得，精讀p.1–3、7–11，同名辨識方法。https://www.historicpathways.com/download/RWCaptJohnWatts.pdf
- **E9** Nils Hanson／GIJN (2021-11-03), *A Guide to Fact-Checking Investigative Stories*；SVT實際編務工作流。https://gijn.org/resource/guide-to-fact-checking-investigative-stories/

詳盡短引、定位、來源雜湊與不採用理由，見本輪稽核資料夾的 `journalism.md`／`archives.md`；方法改編不等於原作者為本系統背書。
