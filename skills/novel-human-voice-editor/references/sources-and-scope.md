# 研究來源與轉譯範圍

本技能吸收的是可泛化的編輯原則，不複製任何專案的完整指令、例句或作者聲紋。

## 主要來源

- [blader/humanizer](https://github.com/blader/humanizer)：英文 Humanizer skill；其 README 與 `SKILL.md` 將 AI 寫作痕跡拆成內容、句法、詞彙、語氣與聲音層，並強調保留事實、校準作者聲音與避免誤殺。
- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh) commit `f4518a8`（2026-09-23）：中文 31 個檢查點與保留邊界。本技能只吸收觸發條件，不複製例句；執行時讀 `humanizer-zh-checkpoints.md`，不把模式命中當成作者身份證據。
- [nagameTW/humanizer-zh-tw](https://github.com/nagameTW/humanizer-zh-tw)：台灣繁中在地化版本；提供中文用語、全形標點、語域、Markdown 結構和「不捏造事實」護欄。
- [aeopress/writing-skills.TW](https://github.com/aeopress/writing-skills.TW)：將繁中去 AI 味與節奏修訂分成兩層；`good-writing-tw` 的氣口、句長錯落和避免短句連發，轉譯為本技能的小說節奏護欄。
- [Aboudjem/humanizer-skill](https://github.com/Aboudjem/humanizer-skill)：提供群聚診斷、不同聲音設定、引用／程式碼保護和「不要把真正的人聲洗平」的誤判原則。
- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)：外部模式觀察的參考入口；本技能不把該頁的詞彙直接當成中文禁詞表。

## 本技能的小說化轉譯

外部通用技能通常處理文章、README 或社群貼文；本技能另加：

- 正典、視角與角色知識權限優先於文句自然度；
- 角色聲音卡、答非所問、迴避能力與壓力下語言變化；
- 把「情緒說破」「台詞資料包」「所有人都會自省」「機械完美場景」列為小說專用診斷類別；
- 將自動工具限制為定位提醒，不計算 AI 機率、不保證規避偵測；
- 先完成世界、行為、連續性與風格檢查，最後才做文字層修訂；
- 修訂版本維持 `[DRAFT]`／`[CANON]` 分層，避免漂亮句覆蓋正典。

Humanizer-zh 對照截至 2026-09-23，commit `f4518a8`。其餘研究資料截至 2026-08-01。來源可能變動，使用時以原專案最新文件為準。
