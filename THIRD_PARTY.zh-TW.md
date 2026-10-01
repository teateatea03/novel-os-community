# 第三方元件與參考資料

<!-- language-navigation --> **繁體中文** | [English](THIRD_PARTY.md) | [日本語](THIRD_PARTY.ja.md) | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | [Deutsch](THIRD_PARTY.de.md) | [Português](THIRD_PARTY.pt.md)

Novel OS 包含與第三方專案互通或討論第三方專案的原創程式碼與文件。除非個別檔案明確另有說明，第三方專案**沒有以原始碼副本形式納入**本儲存庫。

## 執行環境或選用相依套件

| 元件 | 用途 | 授權／來源 |
|---|---|---|
| Python | 執行環境（3.10+） | Python Software Foundation License |
| NetworkX | 圖演算法與 GraphML 匯出 | BSD-3-Clause；https://networkx.org/ |
| PyYAML | NPC 投影工具的 YAML 狀態輸入 | MIT；https://pyyaml.org/ |
| MCP Python SDK | 選用的本機 Instagram MCP 用戶端 | MIT；https://github.com/modelcontextprotocol/python-sdk |
| Graphify（`graphifyy`） | 選用的圖分析／匯出互通功能 | 上游標示 Apache-2.0，並包含 MIT 授權材料；https://github.com/Graphify-Labs/graphify |

匿名 Instagram MCP 伺服器與 Instaloader 是獨立的選用元件，未包含在此。操作者須自行安裝，並遵守平台條款、適用法律、robots／存取控制，以及本專案僅限公開資料的限制。

## 研究參考資料

文件連結文章、規格、書籍、工具與公開專案作為研究引用。連結與描述不代表將那些作品的程式碼或文字納入 Novel OS。如果貢獻材料改作程式碼或文字，而非僅引用想法，必須指出確切來源、授權、修改與必要的出處標示。

## 本發行版包含的改作材料

- **Humanizer-zh**，copyright (c) 2026 歸藏，MIT：[上游 commit f4518a8eab97b8bfebc66a89d34320a89bef6930 的來源](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - 改作：`skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` 將 31 項編輯檢查點翻譯／濃縮成繁體中文，並加入小說專用的保留與衝突規則
  - 保留[上游 MIT 聲明](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt)，已對照該確切上游 commit 核實
  - 聲明隨技能保留於原始碼、可攜套件與安裝後的執行環境。它適用於上游材料，**不適用於整個 Novel OS**；專案自行撰寫的材料另依 [LICENSE](LICENSE.zh-TW.md) 處理

## 未隨本專案散布的外部宿主整合

`lieflat-less-ai-tone` 是宿主提供的選用編輯程序，不屬於 17 個執行技能。其整合文件記錄了外部修訂版本，但本儲存庫不包含已核實的上游網址／授權或其實作。不要自動抓取、納入其副本，或聲稱已執行。若不可用，保留內建人聲化工作流程，並將此額外程序記為未執行。安裝或散布前，須另行核實來源與授權。

`minis-model-use` 獨立審查轉接器需要原始宿主。其他宿主必須提供明確設定的替代方案，或將獨立模型審查記為未執行。本機回歸測試不會測試即時模型、Graphify、MCP 或 Instagram 服務。

## 相依套件界線

上述選用套件不會由核心發行版打包或安裝。它們的授權義務仍由各自的發行版規範；啟用整合或再散布組合套件前，請檢查確切上游版本。核心測試不需要這些相依套件。本清單協助審查，不構成法律意見。
