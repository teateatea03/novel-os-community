# Novel OS

<!-- language-navigation -->

**繁體中文** | [English](README.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

Novel OS 是一套可重複使用的 AI 代理技能與本機 Python 工具，適用於長篇小說、互動小說、情節連貫性、角色／世界觀研究、行為一致性、具來源追溯能力的圖譜，以及敘事驗證。

> **授權：** 採用 [Novel OS 原始碼公開與商業分潤授權](LICENSE.zh-TW.md)，著作權屬於 teateatea03。非商業使用免費；商業使用須支付年度相關正淨利的 0.5%。修改與再散布須保留相同條件及聲明。這不是 MIT、GPL 或 OSI 認可的開源授權。

商用與雙幣收款資料見[商用分潤與付款說明](docs/COMMERCIAL_TERMS.zh-TW.md)。使用者的小說及其他產出權利不轉移給系統方。

## 語言涵蓋範圍

公開文件提供繁體中文、英文、日文、韓文、西班牙文、法文、德文及葡萄牙文版本。執行用技能、模板及其中的技術參考文件目前保留原有語言。本次八語文件發布不包含執行用內容的翻譯。

## 隱私邊界

本原始碼儲存庫刻意不包含：

- 小說原稿、章節草稿、互動遊玩紀錄、故事狀態及作者回饋資料集
- 角色、世界觀、特殊物件及真人研究資料庫
- 對話記憶、裝置本機狀態、備份、匯出資料、憑證、私人端點及環境設定檔

公開範例與測試資料必須使用合成資料。每次推送或發布前，請執行隱私掃描器並檢查暫存區中的檔案清單。

## 儲存庫結構

- `skills/`：可重複使用的技能套件、腳本、模板及合成測試資料
- `scripts/`：隱私檢查、驗證與測試工具
- `docs/`：專案治理及發布邊界文件

原始碼目錄樹共有 18 個技能目錄：17 個可安裝的執行用技能（1 個協調技能與 16 個協作技能），以及套件匯出器。匯出器是封裝工具，不會作為執行用技能安裝。

## 環境需求

- Python 3.10 以上
- 可持續保存資料的 UTF-8 儲存空間
- 核心執行流程僅使用標準函式庫
- 選用功能：請參閱 `requirements-optional.txt` 與 [THIRD_PARTY.zh-TW.md](THIRD_PARTY.zh-TW.md)

請在隔離環境中安裝選用的 Python 相依套件：

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Graphify 整合為選用功能，請依其上游文件另行安裝。

## 首次本機執行（不需要模型或網路）

請從儲存庫根目錄執行，並使用 Python 3.10 以上與 Git。核心檢查及合成示範不需要選用套件、API 金鑰或私人小說原稿：

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Keep generated project state outside the source repository.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

初始化工具會建立空白的規劃／狀態架構，不會生成小說或呼叫模型。請將自己的故事保存在另一個私人目錄。初始化工具會拒絕覆寫既有專案。

使用代理宿主時，請將執行用技能保留為同一層級的目錄，並將 `novel-operating-system` 註冊為進入點。不支援持久化檔案或 Python 程序執行器的宿主，只能使用文件／手動模式。有關套件指令、冒煙測試、選用整合及平台限制，請參閱[經本機測試的建置與安裝指南](docs/GETTING_STARTED.zh-TW.md)。

## 驗證

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Novel Judge 測試套件必須透過 `scripts/run_tests.py` 執行；不支援逐一直接執行使用套件相對匯入的測試檔案。

隱私與 JSON 檢查會檢查來源檔案，包括未追蹤與被 Git 忽略的檔案。檢查會排除 Git 中繼資料、自動產生的 Python／測試快取，以及經確認位於根目錄的虛擬環境；已追蹤的檔案仍會接受檢查。遇到符號連結、無法讀取的檔案或非 UTF-8 文字時，檢查會直接判定失敗。請將產生的套件與故事狀態保存在此工作副本之外。掃描器只會回報檔名與問題類別，不會顯示符合規則的內容；它是啟發式檢查，不能作為隱私保證，也不會掃描版本歷史。

## 平台路徑

文件使用 `<SKILLS_ROOT>`、`<WORKSPACE_ROOT>` 與 `<NOVEL_PROJECTS_ROOT>` 等佔位符。請依宿主平台設定這些路徑。可執行的初始化工具預設使用 `~/.novel-os/novels`，除非提供 `NOVEL_PROJECTS_ROOT` 或明確指定 `--root`。

## 安全與研究範圍

研究技能僅適用於合法、公開可存取的資料，不得繞過登入限制、CAPTCHA、付費牆、robots／存取控制或平台限制。真人研究必須記錄資料來源，不得將未經證實或敏感的資料當成事實陳述。

## 專案治理

請閱讀：

- [貢獻指南](CONTRIBUTING.zh-TW.md)
- [行為準則](CODE_OF_CONDUCT.zh-TW.md)
- [安全政策](SECURITY.zh-TW.md)
- [第三方元件與聲明](THIRD_PARTY.zh-TW.md)

## 授權與貢獻

商業使用前，請閱讀[授權條款](LICENSE.zh-TW.md)及[商用付款說明](docs/COMMERCIAL_TERMS.zh-TW.md)。計算範圍僅包含相關產品、服務及小說的年度正淨利，不包含無關業務。申報採自行申報制，沒有隱藏遙測或自動蒐集。第三方元件保留各自的授權及聲明。

商業使用者須在使用前明確表示接受授權版本。請先透過不含私人或財務資料的 GitHub issue 聯絡，以安排私下申報管道；不要公開張貼財務報表或付款紀錄。貢獻及再散布規則見[貢獻指南](CONTRIBUTING.zh-TW.md)。

## 驗證限制

專案提供 Linux 核心測試與合成資料安裝檢查。選用的 Graphify／MCP／Instagram 服務、實際模型、原生代理整合，以及跨平台／Python 版本測試矩陣尚未通過認證。模型報告範例為合成示例，不能作為已量測供應商／模型效能的證據。
