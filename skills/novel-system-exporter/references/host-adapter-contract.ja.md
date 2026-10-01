# Novel OS ホストアダプター契約

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | **日本語** | [한국어](host-adapter-contract.ko.md) | [Español](host-adapter-contract.es.md) | [Français](host-adapter-contract.fr.md) | [Deutsch](host-adapter-contract.de.md) | [Português](host-adapter-contract.pt.md)

本契約は Minis 以外の AI フレームワークの統合担当者向けです。Novel OS は ZIP をアップロードするだけでファイル権限、モデル権限、会話間の記憶を獲得するプラグインではありません。自動展開と呼ぶには、ホストが以下の能力を提供する必要があります。

## A. ホストが提供すべき最小インターフェース

| 能力 | 最小操作 | Novel OS での用途 | ない場合 |
|---|---|---|---|
| Skill router | `load_skill(name)`／リソースファイル読込 | 調整役が意図に応じて 16 個の専門スキルをロード | 対応する Skill を手動でプロンプトに含める |
| 永続ストレージ | `read(path)`、`write(path)`、`list(path)`、`mkdir(path)` | プロジェクト聖典、章、台帳、state、グラフ、スナップショット | 文書モードのみ。run 間の連続性を保証しない |
| Process runner | `run(argv, cwd)` | Python 初期化・gate・state・graph ツールの実行 | テンプレート・チェックリストを手動利用し、検証済みとは主張しない |
| Project identity | 安定した `project_id` → storage root | 新しい会話・worker で同じ小説状態を読む | 毎回利用者がファイル・要約を提供 |
| Branch writer lock | `lock(project,session,branch)`／トランザクションロック | recovery、stale-hash、event、state、manifest commit を直列化 | single-writer のみ。複数 worker の安全性を主張しない |
| Model task adapter | `minis.model-task.v1` を受け取り、先に schedule を永続化、worker が lease で claim、固定 schema を返す | L1/L2 モデルを単一 extract/plan/render/repair に制限し、retry/cancel/stale/restart recovery に対応 | 文書モードまたは手動入力。モデルに state 権限なし |
| Runtime/event versioning | Runtime build、event schema、transition contract、golden replay fixture | 更新後の旧履歴再生でも同じ state hash。不明な契約は拒否 | 旧ランタイムを凍結し、手動移行後のみ更新 |
| Story solver | 上限付き storylet 状態探索 | unreachable、broken target、soft lock を検出し探索限界を公開 | 手動経路レビュー。全経路検証とは主張しない |
| Random-event suggestion control | branch 単位の `off`/`on-suggestion`、semantic window、seeded pool、non-canonical audit | 適格な窓だけで任意の方向カードを提示し、no-event と再現可能な来歴を保持 | `off` 固定。プロンプトで秘密の抽選をせず提案を正典扱いしない |
| Memory/Graph projector | event → episodic memory；events → Graphify projection | 追跡可能な記憶と再構築可能なグラフ | events を保持し派生索引を未更新と表示 |
| Graphify completion index | `sync_graph.py` が出典・主張・分岐を既存 `graph.json` に同期 | 出典、証拠、版、補完仮説を検索可能にする | グラフは派生索引であり本文・正典を逆方向に上書きしない |

プロセス実行機能は**連結した shell 文字列より argv 配列**を優先し、プロジェクト・スキルのワークスペース内に限定し、stdout、stderr、exit code を gate 成果物として保持してください。

## B. パスの対応付け

展開設定は次の値を提供し、別環境に Minis のパスをハードコードしないでください。

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` は `NOVEL_PROJECTS_ROOT` を読むか、明示的な `--root` を受け取れます
- `SPECIAL_OBJECT_DATABASE_ROOT` は特殊物データベースの正本 `graphify-out/graph.json` を保持し、`SPECIAL_OBJECT_DATABASE_WORK_ROOT` はバッチ JSON と引継ぎパッケージを保持します。後者は正本の代わりになりません
- `WORLD_DATABASE_ROOT` は世界データベースの正本 `graphify-out/graph.json` を保持し、`WORLD_DATABASE_WORK_ROOT` は世界バッチ JSON と引継ぎパッケージを保持します。後者は正本の代わりになりません
- その他の root はルーター・フレームワークアダプター設定です。関連 Skill の `<..._ROOT>` を実際の永続パスに置き換えます
- 1 冊の全ファイルは再読込できる同一プロジェクトルートに置きます。最新章だけを一時チャット文脈に保持してはいけません

## C. 必須の展開手順

1. バンドルを展開し、最初に実行します。

   ```bash
   # First confirm Python, hashes, and the complete smoke test are available:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. **17 個**の Skill（調整役＋専門 16 個）を登録します。`novel-reality-state-engine` は event/state JSON、Reality Card、実行可能な Reality Gate を提供する必要があります。`novel-model-capability-compatibility` は実エンドポイントの text/JSON/tool/state probe、能力レベル、fallback を提供します。`novel-sensory-sound-prose` は音・五感の本文契約を保持します。同階層の相対パスを維持します
3. `project_id` を上記の永続ルートへ対応付け、エージェントに対象プロジェクトのファイル読み書きを許可します
4. 新規プロジェクトの初期化ツールを実行し、Markdown/JSON/`graphify-out/graph.json` がすべて作成されることを確認します
5. エージェント run を終了して新しい run を開始し、続きの執筆前に状態を読むよう求め、一時文脈に頼っていないことを検証します
6. 同じソース state hash に 2 worker で同時 commit し、ちょうど 1 つだけ成功し、他方は stale-hash/conflict となることを確認します。その後 event replay で現在の state hash を検証します
7. episodic memory を 2 個作り、reflection が既存の evidence ID を少なくとも 2 個引用することを確認します。L1 render task をコンパイルし、パッケージに hidden truth がなく `may_commit_state=false` であることを確認します
8. events から対話型 Graphify projection を再構築します。削除して再構築しても source hash が同じになる必要があります
9. golden-history fixture を少なくとも 1 個保持します。新ランタイムで再生すると期待する state hash となり、不明な transition contract を拒否しなければなりません
10. model activity を作り、lease 期限後の回復、state 前進後の旧結果の stale 化、activity が pending 中の author console の停止を確認します
11. unreachable state、broken target、soft lock を含む storylet fixture を作り、solver がすべて検出し max depth/max states を明示することを確認します
12. events の compaction 後、索引を削除してアーカイブを改ざんします。manifest integrity gate は索引再構築前に拒否する必要があります
13. 新 branch は既定で `off`、抽選・audit 書込みなしと確認します。利用者が `on-suggestion` を有効にした後、scene 境界で固定 seed を使って同じ suggestion/no-event を得ること、正典 event log、State、Graph、Knowledge、本文が変わらないことを確認します
14. meta input、保留中の直接的帰結、自然な休止のない高圧状況、既存の決定的帰結、伏線のない脅威へのリクエストを送ります。すべて抑止されなければなりません。提案の採用は計画引継ぎだけを作成でき、Reality/Knowledge/Agency/Behavior/World/Canon Gates を列挙する必要があります
15. active segment の manifest hash/bytes/count を検証します。event index 削除後の active log 改ざんは拒否しなければなりません。activity claim は fencing token を返し、旧 token、token 欠如、lease 期限切れによる完了は拒否します。すべてのファイルベース ID は path traversal を拒否します。同じ random-event `request_id` の再試行で再抽選や第 2 audit 項目を作ってはいけません。改ざんされた audit hash chain は再生せず、期限切れ提案から adoption handoff を作ってはいけません

## D. 任意のツールアダプター

### Web 研究

ホストが browser/search ツールを提供する場合、ルーターは検索結果、URL、発行者、日付、短い引用を research/graph の証拠欄に記録します。browser がなければ利用者提供資料だけを扱い、`【待定】`（未確定）/`【提案】`を使い、出典を検証したふりをしてはいけません。

### 第二モデル・sub-agent レビュー

`long-form-novel-writer/scripts/independent_review.py` は現在 Minis の `minis-model-use` を呼び出します。他のフレームワークは次のいずれかを行います。

1. `role`、`prompt`、`max_tokens` を受け取り、別モデル・sub-agent を呼び、原文と解析済み JSON を `reviews/` に保存するアダプターを書く
2. 独立レビューを無効にし、ローカルゲート・手動チェックリストを使い、引継ぎで「第二モデル未実行」と記録する

どちらでも出力ルールを保持します。`machine_suggestion` を `[CANON]` へ直接昇格できません。裏付ける証拠が 2 件ない問題は `questions` にのみ入れます。失敗時は `unavailable` 成果物を生成し、黙って合格扱いにしてはいけません。

### グラフと版管理

- `networkx`：path、affected、GraphML などを有効化
- `graphifyy`＋`networkx`：Graphify HTML、コミュニティ分析、Cypher エクスポートを有効化
- Git：commit・branch のみ。なくてもファイルスナップショットは可能

これらは拡張であり、小説を開始する前提条件ではありません。

## E. 最小ルーターのロジック

```text
if request is to create/update/query/compare/export a special-object database:
    load special-object-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add character-db + behavior when operator/autonomous-machine/personality matters
    add long-form when linked to a novel project or chapter state
elif request is to create/update/query/export a world database:
    load novel-world-database-builder
    add novel-worldbuilding-architect + knowledge-relationship-graph
    add long-form when linked to a novel project or chapter state
elif request is cross-chapter writing/continuation/outline revision:
    load long-form + behavior
    add world/style/graph only when the story state needs them
elif request is character research:
    load character-deep-digger
    add behavior + character-db/graph when evidence or persistence is needed
elif request is a human-voice/Taiwan Traditional Chinese/character-voice revision:
    load human-voice-editor after content/continuity/style checks
elif request is completion of an abandoned/unfinished novel, original-author intent, or an alternative ending:
    load unfinished-novel-completion
    add long-form + evidence/source tools + world/behavior/style/graph as needed
elif request is free-input interactive fiction:
    load immersive-interactive-fiction
    add world/behavior/style/graph by scene complexity
```

調整役が最初にこのルーターを処理します。毎ターンすべての Skill を無差別にモデル文脈へ詰め込まないでください。

## F. バンドルが自動でできないこと

- 未許可のクラウドアカウントへ Skill をインストールし、API キーを設定し、ツール権限を有効化し、データベースを作ること
- チャット専用モデルに shell、ファイルシステム、永続記憶、複数モデル能力を与えること
- 対象モデル・プラットフォームのコンテンツ方針、token 制限、プライバシールール、ネットワーク制約を上書きすること

前提が欠ける場合は [platform-compatibility.ja.md](platform-compatibility.ja.md) の B/C/D 代替モードを使い、展開報告に無効な機能を一つずつ列挙してください。
