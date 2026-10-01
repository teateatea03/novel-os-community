# 公開圖比對入庫（Visual Comparison Store）

角色資料庫正本仍是 `graphify-out/graph.json`。公開圖**另存檔**，圖譜只留可追溯指標，方便外貌／作品視覺比對，不是相簿、不是整站下載。

## 何時入庫

- 官方頭像、官網／作品視覺、本人公開帳號的代表圖、活動官方照、研究問題需要並排比對的公開圖。
- 使用者明確要求「存圖比對」或深挖時該圖本身是證據。

## 不入庫

- IG／X 整批原圖、追蹤者大頭、限時動態、私人訊息圖。
- S 類：性私密、可識別未公開身體、精確住址門牌、證件。只記「發現未擷取」。
- 沒有來源 URL 的圖（聊天隨意上傳除外：仍要標 `source_url` 或 `source_note: user_provided` 與同意範圍）。

## 磁碟配置

```text
<CHARACTER_DATABASE_ROOT>/<slug>/
├── graphify-out/graph.json    # 正本；不含圖 bytes
└── visuals/
    ├── <sha256>.<ext>         # 圖檔
    └── <sha256>.json          # sidecar：來源、MIME、角色、擷取日
```

路徑相對資料庫根目錄，不寫進 `graphify-out/`。聊天 `<ATTACHMENTS_ROOT>/` 不是資料庫。

## Sidecar 與節點

```yaml
schema: minis.character-visual.v1
visual_id: visual:<slug>-<short>
role: official_avatar|work_visual|event_photo|comparison_still|other
source_url: https://...
page_url: https://...
captured_at: ISO-8601
sha256: ...
mime: image/jpeg
local_path: visuals/<sha256>.jpg
width: 0
height: 0
access_mode: anonymous_public|logged_in
privacy_class: P1
rights_note: public_page|official_asset|user_provided
```

圖譜：

- `resource` 節點 `id: visual:...`，properties 複製 sidecar（不含 bytes）。
- 角色 `person` → `has_visual` → `visual:...`
- 主節點 `properties.visual_refs[]`：`visual_id`、`role`、`local_path`、`sha256`、`source_url`
- 可選 `primary_visual_id`

同一 `sha256` 不重複存檔；新來源只追加 evidence／source_url。

## 比對

```bash
python3 scripts/ingest_public_visual.py compare --db <DB> --id visual:a --id visual:b
```

優先 `apple-vision similarity`。結果寫 sidecar／報告，不當成身份證明。真人外貌比對只作「同一公開形象是否一致」的輔助，不作生物辨識或人臉資料庫。

## 入庫指令

```bash
python3 scripts/ingest_public_visual.py add \
  --db <CHARACTER_DATABASE_ROOT>/<slug> \
  --person person:<slug> \
  --file /path/to/image.jpg \
  --source-url 'https://...' \
  --role official_avatar
```

`--url` 可下載公開圖（http(s)、圖 MIME、大小上限）；失敗不視為沒有這張圖。不把 Cookie 寫進 sidecar。
