# 本機設定與可攜式安裝

<!-- language-navigation --> **繁體中文** | [English](GETTING_STARTED.md) | [日本語](GETTING_STARTED.ja.md) | [한국어](GETTING_STARTED.ko.md) | [Español](GETTING_STARTED.es.md) | [Français](GETTING_STARTED.fr.md) | [Deutsch](GETTING_STARTED.de.md) | [Português](GETTING_STARTED.pt.md)

本指南涵蓋本機執行環境及可攜式套件。使用與再散布須遵守[授權條款](../LICENSE.zh-TW.md)；商用申報及付款詳情見[商用分潤與付款說明](COMMERCIAL_TERMS.zh-TW.md)。

## 語言涵蓋範圍

公開文件提供繁體中文、英文、日文、韓文、西班牙文、法文、德文及葡萄牙文版本。執行用技能、模板及其中的技術參考文件目前保留原有語言。本次八語文件發布不包含執行用內容的翻譯。

## 選擇模式

- **本機工具：** Python 3.10 以上，以及可持續保存的 UTF-8 檔案。核心驗證、專案架構建立與測試使用標準函式庫
- **代理執行環境：** 除上述需求外，宿主還須能載入同層級的 `SKILL.md` 套件、讀寫專案檔案及執行 Python。請將 `novel-operating-system` 註冊為進入點
- **文件／手動模式：** 沒有 shell 或持久化檔案的宿主可以依循模板，但不能聲稱已執行 CLI 檢查關卡、完成安裝或保存持久化狀態

Novel OS 不包含模型、API 帳號、網路服務或私人小說原稿。原始碼共有 18 個技能目錄：17 個可安裝的執行用技能（1 個協調技能與 16 個協作技能），以及匯出器。

## 檢查全新工作副本

請在 POSIX shell 中，從儲存庫根目錄執行下列指令：

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

實際創作請使用獨立的私人專案目錄。不要將既有小說原稿或資料庫複製到此工作副本。若要建立第一個合成資料專案，請使用根目錄 [README](../README.zh-TW.md) 中的 `mktemp` 範例。明確指定的 `--root` 優先於 `NOVEL_PROJECTS_ROOT`；若兩者都未提供，專案初始化工具會使用 `~/.novel-os/novels`。

## 建置與測試本機套件

以下指令只會使用儲存庫檔案與暫存目錄，不涉及上傳、實際模型、API 金鑰或外部研究。建置輸出必須保存在原始碼工作副本之外，以免誤將產生的套件內容提交到儲存庫。

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

完整驗證設定會執行使用合成資料、長度超過 10 萬字元的長篇試作，以及本機回歸測試套件。這是本機正確性檢查，不能作為實際模型品質或跨平台認證。除非明確提供 `--upgrade`，否則安裝工具會拒絕覆寫既有技能；升級時會建立本機備份。首次測試請勿以正在使用的技能目錄作為安裝目標。

上述檢查通過後，可用以下指令建立封存檔：

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

套件清單會列出所有封裝檔案並記錄其雜湊值，包括專案授權、商用條款與第三方指南的八種語言版本，以及 Humanizer-zh 改編技能內未更動的聲明。請在封存檔及安裝內容中保留這些聲明。安裝工具會將專案層級的聲明保存在 `novel-operating-system/DISTRIBUTION_NOTICES/`，不會覆寫宿主根目錄的授權檔。

## 選用功能

請只安裝宿主需要的功能，並使用隔離環境：

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

這個檔案列出的是相容版本範圍，並非可重現安裝的鎖定檔。如果啟用選用整合，請選定並測試其確切版本，並檢閱上游條款。上述核心操作流程不需要任何選用相依套件。

- NetworkX 提供選用的圖演算法／GraphML 功能；若需要 Graphify 額外的匯出器，請另行安裝 Graphify
- PyYAML 提供 YAML 格式的 NPC 投影輸入支援；MCP 及其外部 Instagram 伺服器為選用整合
- 在原有宿主以外使用獨立模型審查時，需要以符合宿主環境的替代方案取代 `minis-model-use`。若無法使用，請記錄為未執行
- 套件不包含 `lieflat-less-ai-tone`。必須另行確認其來源／授權；若未提供，請使用內建的人類語感工作流程，並將額外處理步驟記錄為未執行

請參閱[第三方元件與聲明](../THIRD_PARTY.zh-TW.md)、[平台相容性](../skills/novel-system-exporter/references/platform-compatibility.md)及[宿主配接器規約](../skills/novel-system-exporter/references/host-adapter-contract.md)。Windows／原生宿主及選用服務測試屬於獨立的驗收工作；Linux 冒煙測試無法驗證這些項目。
