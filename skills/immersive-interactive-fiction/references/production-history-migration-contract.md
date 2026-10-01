# Production History Migration Contract v1

## 目的

歷史遷移將已驗證的 reconciliation checkpoint 至 frozen HEAD 的 legacy evidence 轉為唯一、append-only、可驗證且可重播的 production history。遷移不能把推測冒充原始事件。

## 來源層級

每筆 migration event 必須標一種：

- `ORIGINAL`：原 committed candidate event＋state checkpoint 可取得。
- `ARTIFACT_REVISION`：正文／artifact 修訂，事件語意不變，保留前後 scene/state 證據。
- `CANONICAL_CORRECTION`：作者已提交的語意／時間 correction，有明確 event 或 state 證據。
- `RECONSTRUCTED_CHECKPOINT`：原 event payload 缺失，但 committed state checkpoint 可驗證。
- `UNKNOWN`：沒有足夠證據；不得填造內容。

每筆保存 source paths、source hashes、legacy event/state hashes、turn、scene hash 與 note。

## Replay 表示

Legacy candidate 的 `operations` 並不足以重建其完整 state；因此歷史遷移使用 migration-only `replace_snapshot` operation：

1. value 是來源 checkpoint 的完整可變狀態；
2. project/session/branch/schema/revision/state hash/event head 仍由 runtime 控制；
3. normal delta validation 與 `ProjectRuntimeAdapter.commit()` 不接受 `replace_snapshot`；
4. replay 與 projector 可讀，來源狀態 hash 必須逐筆吻合；
5. migration event 不宣稱每個欄位都是原 writer 的獨立 operation。

## Gate 遷移

歷史 Gate 只作 evidence，不把檔案存在追認為原回合的 authorization。Cutover frozen HEAD 建立一份 migration Gate authorization，意義僅為：來源盤點、完整性、replay 與 frozen HEAD 對照已通過。新回合仍必須使用七 Gate 的 scene/state-bound authorization。

## Cutover

只有以下全部成立才可 active：

- 完整快照與 SHA-256；
- frozen HEAD 在 cutover 鎖內未變；
- events JSONL／manifest／index integrity PASS；
- 從 reconciliation checkpoint replay 至 frozen state hash 完全一致；
- point-in-time checkpoints 可查；
- Graph/timeline rebuild PASS；
- race 與 SIGKILL 回歸 PASS；
- legacy writer fail closed 且保留 migration read-only evidence；
- 一鍵 rollback 指引已驗證。

Cutover 不推進回合、不改 scene 正文、不改事件語意。後續狀態規則升級不得混入本次歷史遷移。
