# Instagram MCP 研究路由

## 何時自動使用

人物研究（尤其真人／公開人物 R1 或 R2）遇到以下任一條件時，**自動啟用本機 Instagram MCP，不要先問使用者是否要手動爬文**：

- 使用者提供 Instagram URL、`@username`、Linktree 指向 Instagram，或明確要求查 IG。
- 身份消歧找到疑似本人／官方 Instagram 帳號。
- 研究對象已有 Instagram 資源節點，且需要更新公開內容、近期活動或行為樣本。
- 公開人物研究需要社群一手材料，且 Instagram 是其公開工作／作品／活動入口。

若沒有可核對的 Instagram 帳號，不要用相似帳號猜測；把 Instagram route 記為 `defer`／`blocked`，進行其他來源路由。

## 固定呼叫順序

以 MCP stdio client 呼叫，不要直接繞過 MCP 在技能內另寫 Instaloader：

```bash
python3 scripts/instagram_mcp_client.py profile <username>
python3 scripts/instagram_mcp_client.py research <username> --limit 20
```

- 先呼叫 `get_instagram_profile`，保存帳號 identity、bio、公開網址、粉絲／貼文數、private／verified 狀態。
- 身份已綁定且需要內容樣本時，再呼叫 `research_public_profile`；預設最近 20 篇，最多 50 篇。R0 可用 `posts --limit 5`。
- 需要核對單篇貼文時，呼叫 `get_instagram_post` 並保存原始貼文 URL。
- `include_media` 預設關閉；只有影像／Reel 本身是研究問題時才開啟，避免無必要下載／擴散媒體。

## 保存與 evidence run 接合

MCP wrapper 輸出的整個 JSON 是 raw capture artifact，不可只保存 AI 摘要。保存至目前 research run：

```text
artifacts/raw/ig_<username>_<YYYYMMDDTHHMMSSZ>.json
```

至少記錄：

- `schema: minis.instagram-mcp-capture.v1`
- tool、arguments、captured_at_utc、server_path、Instaloader 版本
- `access_mode: anonymous_public | logged_in`（MCP 預設 `anonymous_public`）
- MCP 回傳的 profile／posts／source_url／date_utc／caption／metrics
- 若失敗：error、message、rate-limit／forbidden 狀態與停止理由

在 `events.jsonl` 追加實際事件：

```json
{
  "type":"BROWSE",
  "actor":"agent",
  "platform":"Instagram via local Instaloader MCP",
  "tool":{"name":"instagram_mcp_client.py","version":"local"},
  "input":{"username":"...","limit":20,"access_mode":"anonymous_public"},
  "result":{"status":"success|zero|blocked|error","artifact_id":"..."}
}
```

在 `candidates.jsonl` 將每篇貼文視為候選來源；以貼文 shortcode／canonical URL 去重。原始 IG 帳號與貼文各自是 `source_family`，不要把同一貼文轉載到新聞的副本算成獨立來源。需要 hash 時對 raw JSON 計算 SHA-256；若不能保存媒體，只保存 metadata、caption、source URL、時間與擷取限制。

## 研究判讀規則

- IG 本人／官方帳號的 caption、公開 bio、公開作品／活動貼文是第一手公開紀錄，通常可作 P1；它證明的是「帳號公開發布／自我呈現」，不是所有外部事實自動成立。
- 每一筆 claim 保留精確 `source_url`、`shortcode`、`date_utc`、`captured_at_utc` 與原始 caption；避免只引用帳號首頁。
- IG 公開貼文是 source family；同一 caption 被新聞轉載時要做 source genealogy，不可假裝兩個獨立來源。
- 貼文的公開數字是擷取時間點的 metadata，不當成永久數字；標明 `as_observed_at`。
- 從 caption／影像推導性格、動機、感情、健康、家庭、收入、住址或私生活時，禁止直接升格。只能形成【推論】並附替代解釋、信心與可推翻條件；敏感項目優先不保存。
- Instagram 沒有抓到、帳號找不到或 API／匿名 route 被擋，不等於事情不存在；標 `UNAVAILABLE`／`blocked`／`search_nonresult`，改試已登入瀏覽器或其他來源。
- 本 MCP 是匿名公開路由。環境已有可用登入時，改用 `browser_use` 看該身份可見的內容，並標 `access_mode: logged_in`。不向使用者要 session、Cookie、密碼；不把憑證寫進研究檔；不解 CAPTCHA。
- 預設仍不掃追蹤者名單、不建個人追蹤檔。留言／限時動態僅在該身份已能看見、且研究問題需要時擷取；看不見就標 blocked，換方法。

## 失敗與 fallback

1. `profile_not_found`：檢查大小寫、拼法、改名與身份消歧；不要猜另一帳號。
2. `private_profile`：匿名 MCP 看不到就標 blocked；若環境已有可用登入且該身份可見，改 `browser_use` 並標 `access_mode: logged_in`。仍不可見才停這條，改其他來源。
3. `rate_limited`／`forbidden_or_rate_limited`：停止匿名 MCP 重試；改已登入瀏覽器或其他來源面，不要增加匿名重試密度。
4. `connection_error`：保存錯誤 artifact，改用 Instagram 官方可讀頁、已登入瀏覽器、Linktree、其他本人平台或可靠二手來源。
5. MCP server not found／工具錯誤：標 `tool_failure`，改瀏覽器或其他方法；不要把未取得資料寫成空結果。

Instagram MCP 是自動研究路由，不是完成度捷徑。R1／R2 仍必須完成身份消歧、其他來源面、source genealogy、claim audit、反證與 evidence-run validator；IG 單一路由不可獨立證明完整人物研究。
