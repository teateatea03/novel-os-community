# X／Twitter 研究路由

X（twitter.com／x.com）是真人研究的**一手社群層**，與 Instagram 同級。不要只把 P2002 當身份鍵就停。

## 何時自動使用

人物研究（尤其真人 R1／R2）遇到以下任一條件時，**自動執行本路由**，不要先問使用者是否要手動翻 X：

- 使用者提供 X／Twitter URL、`@handle`，或明確要求查 X／Twitter。
- 身份消歧、Wikidata `P2002`、Linktree、`rel=me` 或官網找到可核對的本人／官方 handle。
- 研究對象已有 X 資源節點，需要更新公開發言、活動或行為樣本。
- 公開人物的工作／作品／公共討論入口包含 X。

沒有可核對 handle 時不要猜相似帳號；記 `defer`／`blocked`，改其他來源。

## 固定呼叫順序

```bash
COL=<SKILLS_ROOT>/source-collectors/scripts/collect.py
python3 "$COL" x-profile <handle>
python3 "$COL" x-timeline <handle> --limit 20
# 單篇：
python3 "$COL" x-status 'https://x.com/<handle>/status/<id>'
```

- 先 profile，再依 R0／R1／R2 取時間線樣本；預設 20 篇、上限 50。
- 單篇 URL 用 `x-status`（FxTwitter → oEmbed）。
- 匿名／公開路由被擋、空結果或內容不完整時，若環境已有可用登入，改 `browser_use` 看該身份可見的 X 頁，標 `access_mode: logged_in`。
- 不向使用者要 Cookie／密碼，不把憑證寫進研究檔，不解 CAPTCHA，不換馬甲。

## 保存

raw JSON 進目前 research run：

```text
artifacts/raw/x_<handle>_<YYYYMMDDTHHMMSSZ>.json
```

至少記錄 schema／tool／arguments／`access_mode`／captured_at、canonical `https://x.com/<handle>/status/<id>`、text、created_at。每篇貼文進 candidates，以 status id 去重。同一推文被新聞轉載只算一個 source family。

## 判讀

- 本人／官方帳號的公開推文與 bio 是第一手自我發布，通常可作 P1「帳號公開說過／自我呈現」，不是所有外部事實自動成立。
- 引用必須帶到 status URL，不要只引帳號首頁。
- 讚／轉發／追蹤數是擷取當下的 `as_observed_at`，不是永久數字。
- syndication 時間線是**公開樣本，常不完整**；空結果 ≠ 沒有發過文。
- 從推文推導性格、感情、健康、家庭、收入、住址時禁止直接升格。

## 失敗

1. handle 找不到：查改名與消歧，不猜帳號。
2. protected／登入牆：匿名記 blocked；已登入且可見則改瀏覽器。
3. 限流／403：停止公開路由重試，改已登入瀏覽器或其他來源。
4. 工具失敗：標 `tool_failure`，不要寫成零結果。
