# Gate Authority Contract v1

## 核心原則

Gate 檔案存在、名稱正確或 hash 未漂移，都不等於具正典授權。唯一合法鏈為：

```text
known runner → GateEnvelope → deterministic CommitPolicy
→ state/scene-bound GateAuthorization → commit-time full revalidation
→ canonical event authorization hash → HEAD/project projections
```

## GateEnvelope

schema：`minis.gate-envelope.v1`

必須包含：

- `policy_version`
- 已列入 policy allowlist 的 runner ID／version
- `payload` 與 `payload_hash`
- `envelope_hash`
- 可選 artifact path／SHA-256 綁定

核准證據與 HEAD gate bundle 必須保留每個 Gate 的 envelope／payload schema、runner ID／version、payload／envelope hash、verdict、severity、coded finding、artifact binding，以及存在時的作者 override（author、reason、scope、finding codes、hash）。只列檔名或只列 authorization hash 不算完整授權集合。

Gate payload schema 為 `minis.gate-result.v1`，必須包含：

- gate type
- turn ID
- scene SHA-256
- source state hash
- verdict：PASS／WARN／FAIL
- severity：OK／P2／P1／P0
- coded findings
- details

PASS 只能搭配 OK；WARN 只能搭配 P1／P2；P0 必須是 FAIL。

## 預設必備 Gate

1. `turn_contract`
2. `reality`
3. `scene_progression`
4. `prose`
5. `fact_agency`
6. `interactive_agency`
7. `blind_read`

缺一、重複、未知 runner、錯 schema、payload/envelope hash mismatch、scene mismatch、state stale、artifact drift 均 fail closed。

## 作者 override

- 只有識別出的 author 可建立 override。
- 必須寫 reason、`scope: gate_findings`，並綁 turn、scene、state、gate envelope hash。
- 必須明列並覆蓋該 Gate 當下全部 finding codes；空白、部分或未知 finding scope 都拒絕。
- 只允許 WARN/P1-P2。
- FAIL／P0 永不 override。
- `turn_contract`、`reality`、`fact_agency`、`interactive_agency` 永不 override。
- override finding code 若提供，必須是該 Gate 已存在 finding。

## Approval 與 Commit

`approve_gate_bundle()` 在 branch lock 內：

1. 核對目前 state hash；
2. 完整解析全部 envelopes；
3. 驗證 overrides；
4. 產生 `minis.gate-authorization.v1`；
5. 一個 turn 只准核准一次，修訂必須建立新 candidate revision／turn identity。

`ProjectRuntimeAdapter.commit()` 仍在 branch lock 內重新：

1. 核對 source state；
2. 重算 bundle hash；
3. 逐個重驗 envelope／runner／payload／artifact／override；
4. 驗證 authorization record hash；
5. 比對重新計算的 authorization hash；
6. 把 authorization hash 寫進 canonical event、runtime HEAD、project pointer。

所以 approve 後竄改檔案、換 scene、state 前進、改 policy、刪 authorization，commit 都會失敗。

## Production 邊界

production authority 必須執行本契約。既有專案須完成有來源的歷史重建與 cutover；新建互動／傳統長篇專案從空歷史直接建立 active authority。既有 legacy Gate artifact 只能保留為歷史 evidence，不因檔案存在而追認為 authorization；任何新 candidate 都必須重新產生 envelope，並走 commit-time 全重驗。

## Authority Layers

Gate authorization remains the commit firewall for canon safety. Literary quality, reader enjoyment and author preference are handled by the separate authority-layer report (`references/authority-layers-contract.md`). A prose WARN or editorial ticket does not by itself create or revoke GateAuthorization.
