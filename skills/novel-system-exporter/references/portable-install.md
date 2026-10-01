# 匯入與部署 Novel OS

## 先做能力盤點：選擇正確部署模式

交付前先讓目標環境回答：

```text
1. 能否安裝多個 Skill／指令？入口目錄或設定位置在哪裡？
2. Agent 能否讀寫持久檔案、列目錄與執行 Python／shell？
3. Python 版本？是否允許安裝 networkx、graphifyy 和 Git？
4. 是否有 web／browser、第二模型或 sub-agent，以及怎樣由工具呼叫？
5. 專案檔在新對話、新 worker 或重啟後存在哪裡？
```

依答案選擇：**A 完整安裝**（Skills + shell + storage）、**B adapter 整合**（自訂 agent tools）、**C 知識檔模式**，或 **D 單 prompt 手動模式**。完整判定、套件與各框架的 adapter 需求在 `platform-compatibility.md`；沒有 A／B 的條件時，不能宣稱已「自動佈置」。

## 支援自訂技能目錄的 AI 平台（A：完整模式）

1. 解壓縮 ZIP。
2. 在解壓根目錄執行：

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. 讓該平台重新掃描技能，或重啟其技能索引。
4. 以「建立一個長篇小說專案」測試。它應觸發 `novel-operating-system`，依序建立專案骨架、決定是否需要研究／世界觀／行為／文風／圖譜，並在正文前先完成規劃與 gate。

**更新**：加 `--upgrade`。安裝器會把已存在的同名技能移入 `<target>/backups/novel-os-<timestamp>-<unique>/`，完成後才替換；失敗會復原原檔。

### 授權與第三方聲明

完整 ZIP 必須保留根目錄的 `LICENSE`、`THIRD_PARTY.md` 與 `docs/COMMERCIAL_TERMS.md`，以及各技能原有的第三方授權文件。安裝器將這些聲明存到 `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`，保留原相對路徑，讓文件中的授權連結繼續有效；各技能內的上游聲明也留在原位。它不會覆寫宿主根目錄的 `LICENSE` 或 `docs/`。更新前的聲明隨原技能一起保存在該次備份。

`novel-operating-system/INSTALLATION.json` 記錄各聲明的來源／安裝路徑、SHA-256 與位元組數。安裝完成後可從解壓的 ZIP 執行唯讀檢查：

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

檔案缺失或遭修改會失敗。這是本機完整性檢查，不能取代可信發布來源。詳見 `bundle-contract.md` 的明示文件清單；討論草稿不構成生效授權，也不會當作正式條款匯出。

B／C／D 等手動移植模式也必須把上述專案授權／商用條款與各上游聲明一併交付，不能只複製 `skills/` 而遺漏授權文件。

## 自訂 Agent／工具呼叫框架（B：需 adapter）

若框架沒有原生 `SKILL.md` runtime，但有 system prompt、function calling、檔案／命令工具，不能只把 ZIP 解壓後宣稱完成。整合者需要：

1. 將 `novel-operating-system/SKILL.md` 放入系統／開發者指令，並以它的 description 建立 intent router。
2. 將十六個專業 skill 作為 router 可按需讀取的 resources；保持其資料夾相對關係。
3. 若是斷更／未完成作品，先完成 `unfinished-novel-completion` 的 source／canon／evidence／intent／feasibility／branch／rights／provenance 交接，再把選定分支交給長篇 writer。
4. 映射檔案讀寫、目錄列舉、Python process、持久 workspace、`WORLD_DATABASE_ROOT`／`WORLD_DATABASE_WORK_ROOT`、`SPECIAL_OBJECT_DATABASE_ROOT`／`SPECIAL_OBJECT_DATABASE_WORK_ROOT`、web research 到該框架的 tool API。
5. 把 `independent_review.py` 的 `minis-model-use` 替換為該平台的第二模型／sub-agent／API；若沒有，關閉該步驟並記為未執行。
6. 用文件中的部署驗收清單測試跨 run 的檔案持久性與章後 state 更新。

常見的 LangGraph／CrewAI／AutoGen、MCP、OpenAI／Claude／Gemini、Dify／Flowise／Open WebUI 整合位置見 `platform-compatibility.md`；它們都需要框架端自行建立 router／tool adapter，不是本 ZIP 可以替陌生雲端帳號自動完成的操作。

## 只有單一 Skill 匯入欄位的平台（C：知識檔模式）

上傳或貼入 `skills/novel-operating-system/` 整個目錄（含其 references），並把其他十六個技能資料夾作為附件／知識檔保留在同層。提示該 AI：

> 先讀 novel-operating-system/SKILL.md。所有相鄰 skill 是此系統的必備協作者。沒有 shell 時，建立等價的 Markdown/JSON 專案檔，並顯示無法執行的 gate；不得假稱已建立 Git 快照、執行驗證器或完成圖譜匯出。

## 只有聊天／自訂指令的平台（D：手動降級）

以 `novel-operating-system/SKILL.md` 為主指令，以 `skills/` 整包為檢索文件。此模式可移植：流程、模板、schema、輸出格式、規則與檢查清單；不可保證：自動檔案建立、跨回合持久化、CLI 驗證、ZIP 安裝或觸發器偵測。

### 補完作品部署檢查

若要移交斷更作品，除了普通小說專案檔，還要保留 `completion-brief.md`、`source-manifest.json`、證據／意圖／版本／分支帳本、`rights-and-publication.md`、`completion-provenance.md`、`completion-state.json` 與補完 Gate。未知或未授權作品預設用 `private-only`／`research` 模式，不直接公開正文。

不要把專案直接塞入技能 ZIP。另交付一份專案資料夾或乾淨 ZIP：

1. 先檢查是否含真人敏感資料、私人來源、憑證、未授權原文或不希望分享的草稿。
2. 執行既有系統的 `snapshot_project.py`、`deep_consistency.py` 與 `chapter_gate.py`；將結果列入 handoff note。
3. 在 `project-brief.md` 清楚標註正典截止章、未定稿章、作者可覆寫權與已知風險。
4. 對方匯入後先讀 story bible、current state、timeline、reader ledger、plot threads、entity registry 和最新摘要，再開始續寫。
