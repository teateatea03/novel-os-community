# 獨立審稿與深度一致性稽核

獨立 reviewer 用於補盲，不是作者、正典或 gate 的替代品。優先角色：

- **continuity**：只找可由雙證據支持的矛盾；不評論喜好。
- **beta-reader**：描述讀者理解、困惑、期待與情緒效果；不重寫成自己的風格。
- **style-editor**：依 `style-sheet.md` 查可定位漂移、角色同聲與無效重複。

## 證據契約
每個 issue 必須有 category、severity、claim、evidence_a、evidence_b、minimal_fix、confidence。無法提供兩個可定位證據時只能列 `question`，不能判 P0。模型輸出永遠標 `machine_suggestion`；合併進 gate 前由主流程複核原文。

## 深度 sweep 時機
每卷中點、每 10 章、重大改綱後、卷末。輸入以 context pack、最近章節、帳本和風格契約為主，避免無差別塞全稿。不同 reviewer 應分開呼叫，避免一個模型同時扮演作者、讀者與裁判造成角色污染。

## 成本與失敗
模型不可用、JSON 不合法或超時時，保留原始回傳與 WARN；不阻止正文保存。除非作者設定 fail-closed，深度 reviewer 不自動把草稿標 FAIL。

## v2 證據綁定（最小切片）

`independent_review.py` 保持原有產生審稿的參數，輸出改為 `minis.novel-review.v2`。
`summary`／`issues`／`questions` 仍保留供既有讀取端使用，但必須辨識版本，不能把這些模型欄位當已驗證結論。原始回傳保存在獨立 `.raw.txt`；解析後的完整模型物件保存在 `machine_suggestion`，機器驗證結果另放 `validation`。模型自行填入的 accepted／resolved 等欄位不會升格為系統決策。

- `anchored` 只代表兩段不同、唯一、連續的引文，在指定來源的 1-based 起始行找到，而且完整落在實際送入 prompt 的字元範圍內；不證明矛盾成立、嚴重程度正確或修正已被接受
- 重複引文即使附行號仍視為歧義；錯誤行號、拼接／不存在引文、缺欄位、重複使用同一證據（含同來源內一段引文包含另一段）、未送入 prompt 的內容均為 `unverified`，不因 P0 自動成立
- `finding_id` 綁定章稿路徑、原始位元組 hash 和 issue 內容；相同輸入可重現。章稿一改就產生不同身份，不能當跨版本自動對應／結案機制
- `source_binding` 保存章稿、風格檔、context pack／manifest 與 v5 manifest 列出的來源 hash（含 overflow）。`freshness` 在模型回傳後再次核對；途中改稿會標 `stale`
- `prompt_sha256` 綁定實際 UTF-8 prompt 檔案內容，`prompt_sections` 與 `context_receipt` 明列字元納入／截斷情況。章稿、風格與證據定位使用 `splitlines()` 後以 LF 連接的文字；來源 hash 仍綁原始位元組，所以 CRLF／空白改動也失效。字元位置是 Python Unicode character、0-based、半開區間，不是 token 或語義 coverage
- style 最多直接帶入 12,000 字元、context 最多 30,000 字元；若同一來源也透過 context 實際帶入，會合併可定位範圍。overflow 位址不能充當已載入原文
- v5 context 為 stale／invalid 時，在呼叫模型前停止並保留錯誤報告。缺 pack、無 sidecar 的舊 pack、v4 pack 有明確 missing／legacy_unverified 標記；其中未驗證來源不獲得引用錨點資格

讀取舊審稿前可執行只讀檢查：

```sh
python3 scripts/independent_review.py --root PROJECT --check-review PROJECT/reviews/REPORT.json
```

`current` **只代表記錄的來源 hash 仍相符**，不代表內容正確、全部 finding 已 anchored、可以自動套用修訂或 Owner 接受。舊 v1 報告與失敗報告回 `unverified`；來源改動／刪除回 `stale`。檢查不改寫原報告，也不會因只改空白、改別處或模型宣稱 resolved 就關閉問題。所有 finding 的語義狀態仍為 `unverified`、修訂狀態仍為 `unresolved`。

來源路徑限專案內的 canonical 相對路徑，拒絕 symlink／向外穿越；自訂 `--context-pack` 亦須位於專案內。`--chapter` 使用單一章節識別字，不接受子目錄。舊有外部 pack 可先在專案內重新建立，再取得可攜的來源綁定。

此切片沒有修訂套用、修訂決策帳本、跨稿 finding 對應或自動結案；不新增每章人工確認義務，也不修改 Gate／正典。Agent 測試與錨點檢查不是 Owner acceptance，真正模型表現與文學品質需另行評估。

安全界線：這些 hash 是來源一致性檢查，不是經認證的數位簽章；`--check-review` 不能認證任意手改報告或語義正確性。路徑檢查拒絕靜態 traversal／absolute／symlink 與非 canonical 別名，但不是用來防禦惡意程序同時替換檔案系統的 sandbox。

來源檢查以每次呼叫為界：同一 canonical 檔案在該次檢查只讀取／hash 一次，但逐一核對所有預期 fingerprint；相同檔案若有互相衝突的 hash，不會挑選其中一個而放行。CLI 合併相同檔案與 hash 的重複 binding，保留其字元範圍；模型呼叫前、回傳後與日後重查之間不共用快取，因此任何其間改動仍會標 stale。
