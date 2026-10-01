# All-NPC Drift Firewall｜通用擴充

在任何互動小說回合使用本流程，對所有 NPC、生物、系統角色與自主機械一視同仁；不可把 actor 名稱寫死在 Gate 中。

1. 維護動態 registry；新 speaker 沒有 contract 就阻斷。
2. 每個 NPC 生成前建立局部視角 manifest：可知事實、noticed_one、dialogue act、資訊／句數上限與 fallback。
3. 只把角色局部投影交給生成器；不得將全局 state、所有未結問題或其他人心理摘要直接灌入。
4. 對最終全文做 speaker extraction；抽取失敗即 fail，不能用人工摘要代替。
5. 以 scene hash 綁 manifest、semantic review 與提交稿；hash 不同即 fail。
6. deterministic gate 管結構，semantic review 管 report／host／therapist／voice bleed 等功能；兩者通過才 commit。
7. fail 時只重寫違規 actor span；最多兩次，之後用 contract fallback 或停止提交。
8. 壞例只進 regression corpus，不作生成 few-shot；新增 actor 要提供正例、壞例、對抗例。

## 長度修正：角色短答不等於場景短路

本防火牆只限制角色聲音、知識與對話功能，不限制全文長度。不得把 `max_sentences`、`max_information_units`、`noticed_one` 或 fallback 誤用成整個場景的 prose／beat 預算。

互動回合另需通過 Scene Progress／Handoff Gate：玩家行動落點後，至少完成 NPC 第一反應、NPC／世界自主 followthrough、次級後果，再在真正需要玩家意志的位置交棒。能由 NPC 目標、世界時鐘、已啟動設備、物件狀態或非焦點角色自行發生的事，應繼續推演，不因一句短答或一個問句就停止。

禁止：`EARLY_YIELD`、`PLAYER_PING_LOOP`、`NO_AUTONOMOUS_FOLLOWTHROUGH`、`DIALOGUE_BUDGET_LEAK`、`PADDED_NO_PROGRESS`。修復方式是補上合角色的動作、世界反作用、時間／物件／關係差分，不是把 NPC 台詞寫成更長報告。

分類與詳細流程見專案或宿主的 `all-npc-drift-firewall.md`。

## 明示 speaker registry

`extract_scene_speakers.py --registry <project>/interactive/npc-registry.json --scene <scene.md> --out <manifest.json>` 必須讀取專案設定；工具不內建角色名、玩家 ID 或第二人稱對應。以下是獨立編寫的合成器材盤點範例：

```json
{
  "player_id": "visitor",
  "actors": {
    "technician": {"kind": "npc", "contract": "voice-contracts/technician.json"}
  },
  "speaker_aliases": {"技術員": "technician", "你": "visitor"}
}
```

只接受緊接引號前的直接 label（如 `技術員：`）或簡單 attribution（如 `技術員說：`）。複合主詞、未設定的代詞、無歸屬引文與缺少設定一律 parse failure，不能沿用上一句 speaker。抽取產生的 NPC 空 manifest 仍須補上經核准的 per-turn manifest，才能通過 firewall；抽取成功不表示允許提交。

Firewall 必須有明示非空 `player_id`，沒有設定時不得推定任何 speaker 為玩家並略過 NPC Gate。hash、完整引文覆蓋、Voice Contract 與 semantic review 的原有要求仍適用。

完整引文不因長度被省略，超過 500 字的引文仍須逐一歸屬並受完整覆蓋檢查。未閉合、多餘、同式巢狀或空引號一律阻斷；沒有引號的純敘述則明示 `quotation_status: none`，仍受其他 Gate 約束。
