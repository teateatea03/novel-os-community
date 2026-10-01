# Crawl4AI 設計借鏡與 Minis 適配

審查基線：`unclecode/crawl4ai` commit `7e801521428ee12509994d39151006f64055ebe3`（2026-08-22 取得），Apache-2.0。這是設計借鏡紀錄，不代表將上游程式碼複製進本技能。

## 採用的設計思想

| Crawl4AI 優點 | Minis 適配 |
|---|---|
| raw／fit Markdown | 保存 raw bytes、safe Markdown、plain text；任一 derived 均回指 raw hash |
| BFS／DFS／best-first deep crawl | P0 實作低預算 BFS／best-first；DFS 非預設 |
| URL/content filters、scorers | allowlist、deny/include patterns、query relevance、same-domain |
| crash recovery (`on_state_change`, `resume_state`) | 每 URL append-only hash event + atomic checkpoint + resume |
| prefetch／DomainMapper | sitemap、RSS、links discovery；CC/Wayback/CRT/probe 不預設 |
| cache／parallel dispatcher | canonical URL 去重、artifact cache；P0 同 host concurrency=1 |
| CSS/XPath/regex/LLM extraction | P0 safe text/Markdown；結構化抽取為後續 derived plugin，不可當證據 |
| JS/session/shadow DOM | 使用 Minis browser_use 作公開頁升級；不在 iSH 強制安裝 Chromium |
| secure-by-default releases | URL/DNS SSRF gate、redirect 重驗、byte/time budgets、safe output root |

## 不直接照搬

- 完整 Playwright/Patchright/Chromium 依賴：Alpine aarch64／iSH 不保證相容。
- Proxy rotation、stealth、undetected、任意 browser hooks：不作為存取限制繞過手段。
- 任意 JS code、任意 output path、未驗證的遠端 Docker API。
- 預設廣泛 DomainMapper discovery（Common Crawl、Wayback、CRT、path probe）。
- 將 LLM extraction 當原始證據，或將搜尋 snippet 直接入 Graphify。

## 安全背景

Crawl4AI README 記錄 v0.8.7 修補 Docker API 的 RCE、SSRF、auth bypass、file write、XSS 與硬編碼 JWT secret；v0.9.0 改為 secure-by-default。Minis 適配因此採「本機 CLI、無 server、無任意 hook、輸出根目錄固定、URL/IP/redirect 重驗」的更小攻擊面。

## 通用設計檢查清單

以下是設計與回歸審查時應檢查的項目，不是已執行的模型審查紀錄或結果：

1. 先做安全 HTTP-only P0，再做可選 backend escalation。
2. events append+fsync 後才更新 checkpoint；resume 驗 event chain 與 artifact hash。
3. 僅 canonicalize fragment、預設 port與明確 tracking params，未知 query 保留。
4. raw／一般 Markdown／fit Markdown並存，避免清理器刪掉證據。
5. crawler 只輸出 candidate ledger；deep-digger 做 claim adjudication，character-db 只收 checked claim。
6. 頁面內容永遠標為 untrusted；prompt injection 不可變成工具或政策指令。
7. browser_use／Crawl4AI fallback 不得變成登入、CAPTCHA 或 rate-limit 繞過機制。

實際審查應另行保存來源、測試輸入、結果與限制，不能以本清單代替驗證證據。
