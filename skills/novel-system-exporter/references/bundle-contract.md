# 可攜式 Novel OS 套件規約

<!-- language-navigation --> **繁體中文** | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

`novel-os-portable-v<version>/` 套件 layout 內，`skills/` 會包含 1 個總入口與 16 個專業技能；其中 `public-web-research/` 提供安全、可恢復的公開 HTTP(S) acquisition 與 Evidence Run candidate staging，`novel-model-capability-compatibility/` 保存模型能力 probe／L0–L5／fallback 契約，`novel-reality-state-engine/` 保存事件→狀態→能力→行為→正文驗證工具，`novel-world-database-builder/` 保存世界資料庫 schema、批次模板、交接包與查詢規格，`special-object-database-builder/` 保存道具／鎧甲／機體／裝置的版本、能力、規格與生命週期 schema。

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── LICENSE.{zh-TW,ja,ko,es,fr,de,pt}.md
├── THIRD_PARTY.md
├── THIRD_PARTY.{zh-TW,ja,ko,es,fr,de,pt}.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   └── COMMERCIAL_TERMS.{zh-TW,ja,ko,es,fr,de,pt}.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.{en,ja,ko,es,fr,de,pt}.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.{en,ja,ko,es,fr,de,pt}.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.{en,ja,ko,es,fr,de,pt}.md
│   ├── bundle-contract.md
│   └── bundle-contract.{en,ja,ko,es,fr,de,pt}.md
├── skills/
│   ├── novel-operating-system/      # mandatory single entry point
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

結構中的大括號表示每個列出語言各有一份獨立文件，並非檔名的一部分。

`MANIFEST.json` 包含套件結構／版本、套件清單、來源技能版本、每個封裝檔案的 SHA-256 雜湊與位元組數、獨立的 `distribution_notices` 聲明清單、建置時間、排除項目及執行依賴聲明。封裝內容亦包含可攜的**平台相容性指南**。其中不得包含秘密、本機絕對路徑、故事專案、帳戶設定或世界資料庫。

## 授權與聲明保留

- `--source-root` 指定來源 `skills/` 目錄。其上一層儲存庫必須具有全部 24 份必要聲明：英文的 `LICENSE`、`THIRD_PARTY.md`、`docs/COMMERCIAL_TERMS.md`，以及 `zh-TW`、`ja`、`ko`、`es`、`fr`、`de`、`pt` 各語言的 `LICENSE.<language>.md`、`THIRD_PARTY.<language>.md`、`docs/COMMERCIAL_TERMS.<language>.md`。重新整理會在改動封裝內容前拒絕缺失、非一般檔案或符號連結形式的必要文件。這些是擁有者選定的專案條款；上游聲明維持其自身適用範圍。
- 額外明示允許的文件為 `LICENSE.md`、`LICENSE.txt`、`NOTICE`、`NOTICE.md`、`NOTICE.txt` 及 `docs/COMMERCIAL_LICENSE.md`。存在時逐位元組複製。根目錄 `docs/` 的其他文件不會匯出，尤其 `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` 是未生效的討論草稿，不得作為授權或商業條款匯出。
- 技能內的 `LICENSE`、`LICENSE.md`、`LICENSE.txt`、`COPYING`、`COPYING.md`、`COPYING.txt`、`NOTICE`、`NOTICE.md`、`NOTICE.txt`、`THIRD_PARTY.md`，以及 `THIRD_PARTY_LICENSES/` 下所有文件，都隨技能保留並列於 `distribution_notices`。重新整理會比對來源位元組；建置及安裝會拒絕未宣告、缺失、遭變更、路徑不安全或缺少雜湊紀錄的文件。
- 現有 Humanizer-zh 改編材料特別要求保留 `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`。只要仍散布該材料，就不得從來源或清單移除此文件。
- 新增法律上必須保留的檔名，必須在發布前加入這份明示規約。不得僅依賴指向未封裝文件的連結。重新整理會從既有封裝內容移除已過時的選用根目錄聲明副本。
- ZIP 保留相同的根目錄相對結構。安裝時將所有聲明文件存於 `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`，保留如 `docs/COMMERCIAL_TERMS.md` 及 `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt` 的路徑，使相對授權連結仍有效。技能內的上游聲明也維持原位。安裝器絕不寫入 `<target>/LICENSE`、`<target>/THIRD_PARTY.md` 或 `<target>/docs/`。
- `novel-operating-system/INSTALLATION.json` 記錄每份已安裝聲明的原始路徑、安裝路徑、文件副本路徑、SHA-256 及位元組數。暫存及最終安裝會在適用時驗證兩份副本。升級時將原協調技能及其聲明存入一般技能備份，安裝失敗則還原。協調技能內的 `DISTRIBUTION_NOTICES/` 保留給安裝器管理文件。
- 要重新檢查安裝結果，請在解壓套件中執行 `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices`。此唯讀模式會依安裝紀錄檢查根目錄及上游聲明。雜湊只能確認本機完整性，不能防範同時更換檔案與紀錄的攻擊者；請另行保留可信版本。

## 執行依賴聲明

每次發布必須包含全部 32 份明示允許的可攜性參考文件：`references/` 下 `portable-install`、`platform-compatibility`、`host-adapter-contract`、`bundle-contract` 各四類，繁體中文使用 `.md`，其餘 `en`、`ja`、`ko`、`es`、`fr`、`de`、`pt` 使用 `.<language>.md`。請據實宣告以下層級：

- **基本文件工作流**：可讀取技能文件的大型語言模型，不要求執行程式碼。
- **自動化本地工作流（v2.7）**：Python 3.10+（建議 3.11+）、shell／程序執行器、持久 UTF-8 檔案、多技能發現或等價路由器、分支鎖定、單一 `ProjectRuntimeAdapter.commit()` 正式寫入權限、七道 Gate、具型別語意事件、專案就緒／投影新鮮度、作者回饋 Quality Eval，以及（若以 ZIP 分發）解壓能力。世界資料庫另需可寫入的 `WORLD_DATABASE_ROOT`／`WORLD_DATABASE_WORK_ROOT`；特殊物資料庫另需可寫入的 `SPECIAL_OBJECT_DATABASE_ROOT`／`SPECIAL_OBJECT_DATABASE_WORK_ROOT`。
- **圖譜增強**：`networkx` 提供圖譜遍歷；`graphifyy` 搭配 `networkx` 提供 Graphify HTML／社群／Cypher 匯出。沒有這兩個套件仍可使用圖譜 JSON 本身。
- **選用整合**：Git 用於提交、網頁／瀏覽器工具用於來源研究，以及宿主專用的第二模型／子代理配接器用於獨立審查。`independent_review.py` 在替換前僅適用於 Minis。

本機基本模式不需要 Node.js、資料庫伺服器、API 金鑰或網路連線。缺少檔案／程序存取能力的框架必須標明為文件／手動模式，不得稱為完整自動安裝。

## 建置政策

- 封裝內容必須包含明示允許的 **17 個**技能目錄（1 個總入口＋16 個專業技能）、可攜參考文件、安裝／建置腳本及一般文字／來源／測試資料／模板檔案。
- 排除 `.git`、`.DS_Store`、`__pycache__`、`*.pyc`、`.env*`、`node_modules`、`dist`、`build`，以及所有小說專案、資料庫、封存檔與系統專屬檔案。
- 改動封裝內容前，拒絕來源技能路徑或任何封裝技能內的符號連結；不得沿著技能連結讀取無關的宿主檔案。既有未核准的封裝文件也會使重新整理失敗，不得默默進入新清單。
- 若來源具有可執行權限，保留 `scripts/*.py` 的可執行位元。
- 僅讀取本機來源技能樹與明示允許的儲存庫層級聲明。除 `built_at` 外，建置結果應具確定性。
- 套件應自足：執行輔助工具使用 Python 標準函式庫，並依安裝位置的相對路徑發現依賴。

## 驗證政策

`verify` 必須拒絕缺失、遭修改、非預期或雜湊不符的封裝檔案，接著編譯每個 Python 檔案。安裝器冒煙測試還必須：

1. 在有效的正式寫入權限下初始化暫存小說專案；
2. 驗證直接透過 FileStore 修改正典內容受到阻擋；
3. 執行完整 Novel Judge 測試，包含 Gate 權限、就緒狀態、指令執行器、Quality Eval v2、具型別語意事件及傳統長篇製作；
4. 執行圖譜驗證器及長篇／Reality／能力回歸測試；
5. 驗證套件技能清單及來源集合漂移；
6. 完整發布時，執行隔離的第二專案契約探測，加上十萬字以上傳統長篇／知識反轉／連鎖效應試作。

無法執行 Python 的平台僅支援工作流／文件層級；交接時必須明示此限制。
