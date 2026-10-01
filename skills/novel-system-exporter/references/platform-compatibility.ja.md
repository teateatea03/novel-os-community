# Novel OS プラットフォーム互換性・依存関係一覧

<!-- language-navigation --> [繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | **日本語** | [한국어](platform-compatibility.ko.md) | [Español](platform-compatibility.es.md) | [Français](platform-compatibility.fr.md) | [Deutsch](platform-compatibility.de.md) | [Português](platform-compatibility.pt.md)

本書は ZIP と一緒に引き渡してください。Novel OS は**スキル指示＋ローカルテンプレート・Python 検証器**の集合であり、独立モデル、チャット基盤、ベクトルデータベース、クラウドサービスではありません。「自動展開」の可否は、対象 AI フレームワークが複数ファイルのスキル読込、ファイル書込、コマンド実行、任意のモデル呼出し・ネットワーク接続を許すかに依存します。

```text
- 調整役 1＋協働スキル 16＝ランタイム Skill 17 個（ソースにはエクスポーターも含む）
- モデル能力互換性：novel-model-capability-compatibility。実エンドポイント probe、L0–L5、adapter、fallback、切替後回帰を担当
- 現実状態：novel-reality-state-engine。イベント→状態→能力→行動→本文の検証連鎖
- 世界データベース：novel-world-database-builder
- 特殊物データベース：special-object-database-builder。正本ルートは SPECIAL_OBJECT_DATABASE_ROOT
- 中断作品の補完：unfinished-novel-completion
```

## 1. コア構成と依存関係

| 構成・機能 | 使用システム・形式 | 最低依存関係 | 任意依存関係 | ない場合の代替 |
|---|---|---|---|---|
| スキル振分け | `SKILL.md` YAML frontmatter＋Markdown；`novel-operating-system` | 複数テキストをロードできる AI・agent | description に応じ自動起動する Skills runtime | 調整役を system prompt・project instructions とし他スキルを手動添付 |
| プロジェクト永続化 | Markdown、JSON、通常フォルダー | UTF-8 ファイル読み書き | Git | chat・Canvas・クラウド文書で同名ファイルを維持し、ターン間永続性は保証しないと明示 |
| 長編初期化とローカルゲート | Python CLI、標準ライブラリ | **Python 3.10+**、shell、書込可能ディスク | Git | テンプレート・チェックリストを手動コピーし gate・snapshot 実行を主張しない |
| 関係グラフ正本 | Graphify 互換 node-link JSON | Python 3.10+（初期化、JSON 検証） | `networkx`：path/affected；`graphifyy`＋`networkx`：HTML、コミュニティ、Cypher | graph.json を保存・読込みし手動で関係を調べ、可視化・最短経路を生成したと主張しない |
| 世界データベース | Graphify 互換 JSON；世界・場所・派閥・資源・規則・イベント・主張 node、出典証拠、増分バッチ | Python 3.10+、永続 UTF-8 ファイル | `networkx`/`graphifyy`：path、affected、HTML、GraphML、Cypher | graph.json と Markdown 台帳を保存し版・知識を手動検査、可視化エクスポート完了を主張しない |
| 特殊物データベース | Graphify 互換 JSON；物体・版・変種・module・能力・仕様・エネルギー・制約・所持・運用・生命周期 node と出典証拠 | Python 3.10+、永続 UTF-8 ファイル | `networkx`/`graphifyy`：path、affected、HTML、GraphML、Cypher | graph.json と物体台帳を保存し版・仕様競合を手動検査、可視化エクスポート完了を主張しない |
| インタラクティブ小説 | JSON 互換 state、Markdown turn log | ファイル読み書き；Python 3.10+ で検証・checkpoint | 長期記憶・データベース | 毎ターン chat 内の state を確認。会話再開後の保持は保証しない |
| 補完の出典研究・検証 | 未完作品 | `unfinished-novel-completion`；研究・添付ツールは任意 | `source_ingest.py` は hash・版・完全性・権利状態を記録；`completion_gate.py` は意図の過大主張と公開境界を検査 | |
| 独立モデルレビュー | ホストのモデル呼出し CLI/API | なし、必須でない | 第二モデル・sub-agent 呼出し | 手動・同一モデルのチェックリストを使い「独立モデルによるレビュー済み」と主張しない |

### 出典研究と未完作品のツール

`unfinished-novel-completion` の基本ツールは Python 標準ライブラリのみを使います：`init_completion_project.py`、`source_ingest.py`、`compare_source_versions.py`、`branch_diff.py`、`feasibility_report.py`、`sync_graph.py`、`completion_gate.py`、`provenance_report.py`、`run_regression.py`。ネットワーク、OCR、PDF ツール、browser、第二モデルはすべて任意です。なくても利用者提供ファイルは処理できますが、出典範囲と不明点を示し、検証したふりをしてはいけません。

### 「完全自動」の最低環境

- **Python 3.10 以降：** 現行コアスクリプトは `X | None` 型共用構文を使い、Python 3.11+ を推奨します
- **POSIX shell または同等のプロセス実行機能：** Python CLI を動かします
- **書込可能な永続ファイルシステム：** スキルのインストールと小説プロジェクト保存用。最低 1 つの書込可能スキルディレクトリと 1 つのプロジェクトディレクトリが必要です
- **UTF-8 対応：** 物語、テンプレート、JSON、繁体字中国語はすべて UTF-8 を使います
- **ZIP 展開：** ZIP 配布時だけ必要です。Git・フォルダーアップロードでも代替できます
- **ローカル標準ライブラリ：** コアの initializer、ledger、gate、state、bundle スクリプトは Python 標準ライブラリだけに依存し、基本スモークテストに `pip install` は不要です

これらに API キー、データベース、Node.js、ネットワークアクセスは不要です。

### 任意依存関係（基本ワークフローではなく拡張）

```bash
# Graph paths, cascading queries, GraphML
python -m pip install networkx

# Graphify HTML/community/Cypher exports; the upstream package is named graphifyy
python -m pip install graphifyy networkx

# Git version snapshots and gate-protected commits
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` は Python 標準ライブラリのみで利用でき、`path`・一部 cycle 検査は `networkx` が必要です
- `relationship_graph.py export` は **`networkx`＋`graphifyy`** が必要です。不在なら `graph.json` を保持し、HTML/GraphML/Cypher 出力を生成したと偽らないでください
- `independent_review.py` は現在 `minis-model-use` を呼ぶ **Minis 専用アダプター**です。他環境ではその第二モデル・sub-agent・API アダプターへ置換するか、この任意工程を無効にします
- `novel_git.py` は任意の版管理層です。Git がなくても `snapshot_project.py` でファイルスナップショットを作れます

## 3.2 ホスト結合箇所と必要な置換

バンドルのコア形式は移植可能ですが、統合担当者は次の**ホスト・フレームワーク結合箇所**を処理する必要があります。

| 結合箇所 | 現在の Minis での使用 | 他フレームワークが行うこと |
|---|---|---|
| 小説の既定 root | `<NOVEL_PROJECTS_ROOT>` | `NOVEL_PROJECTS_ROOT` を設定するか各初期化ツールへ `--root <persistent-projects-root>`。`<MINIS_ROOT>` の存在を仮定しない |
| 人物 DB root | `<CHARACTER_DATABASE_ROOT>` | `<CHARACTER_DATABASE_ROOT>` とバッチ用 `<CHARACTER_DATABASE_WORK_ROOT>` を対応付け、同じ project・agent から両方にアクセス可能にする |
| 特殊物 DB root | `<SPECIAL_OBJECT_DATABASE_ROOT>` | `<SPECIAL_OBJECT_DATABASE_ROOT>` とバッチ用 `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>` を対応付け、同じ project・agent から両方にアクセス可能にする |
| 対話小説 state root | `<INTERACTIVE_PROJECTS_ROOT>` | 対応付け、state/checkpoints/logs を run 間で読めるようにする |
| 独立レビュー | `minis-model-use run` | `independent_review.py` のコマンドアダプターを書換えるか同等 sub-agent 関数を作る。JSON schema、エラー成果物、正典への自動昇格禁止を保持 |
| スキル発見 | Minis skill registry＋同階層ディレクトリ | description **17 個**（調整役＋専門 16）を登録するか意図ルーターを構築し、必要時に同階層リソースを読めるようにする |
| 長期状態 | Minis 共有ディレクトリ | 永続 volume、DB、artifact store、framework checkpointer を対応付け、project ID で state を取得 |
| 研究ツール | Minis browser/shell | framework の browser/search/file ツールを対応付け、なければ利用者提供資料に限定 |

- `init_novel_project.py` はすでに `NOVEL_PROJECTS_ROOT` に対応し、明示 `--root` が優先します。人物・世界・特殊物 DB と対話小説の `<..._ROOT>` は framework router・展開設定で置換してください。元文書の `<MINIS_ROOT>/...` は Minis 以外では**既定パスの例**であり、システムの必須要件ではありません

## 4. AI フレームワークの能力段階

### A | ネイティブ Skills＋shell＋ファイルシステム（完全モード）

Skill runtime、agent tools、sandbox・terminal を持つ framework 向けです。完全パッケージを直接インストールします。

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**フレームワークの必須事項：**

1. `<SKILLS_DIR>/novel-operating-system/SKILL.md` を主要な起動可能スキルとして登録する
2. **17 個**（調整役＋協働 16）のフォルダーを同階層で保持する。入口ファイルだけをアップロードしない
3. 同階層スキルの `SKILL.md`、テンプレート、参考文書、スクリプトを agent が読めるようにする
4. `python3` 用の安全なコマンドツール・プロセス実行機能を提供する
5. skill registry の再索引・再起動後、スモークテスト結果で受入判断する

**推奨追加機能：** web 研究、第二モデルアダプター、Git、`networkx`、`graphifyy`。

### B | 独自 agent・tool-calling framework（アダプター必須）

system prompt、function calling、ファイルツールを持ち、`SKILL.md` を解釈しない framework 向けです。

**統合担当者の必須事項：**

1. `novel-operating-system/SKILL.md` を agent の system/developer 指示に置き、YAML description を振分けルールとして保持する
2. 残る専門スキル **16 個**を検索可能な参考文書とするか、利用者意図に応じて適切な `SKILL.md` を読むルーターを作る
3. ツールを対応付ける
   - shell → Python scripts
   - read/write/list files → project files と state
   - web search/browser → 公開出典の研究
   - second-model/sub-agent → `independent_review.py` の代替アダプター
4. Minis 固有の `minis-model-use` を framework 自身の model client に置換する。元の JSON review schema、失敗成果物、「machine_suggestion を正典へ自動昇格しない」原則を保持する
5. 永続 storage key・workspace を指定し、同じ作品のファイルを会話・worker 間で引き継ぐ
6. 自動スキル起動を実装するか明示的に無効にする。**17 個の Skill 文書**を文脈に入れるだけで自動協働すると主張してはいけない

### C | 知識ファイルアップロード・独自指示のみ対応のチャット AI（文書モード）

執筆規約、テンプレート、データスキーマ、チェックリストは移植できますが、真の自動化はできません。

**必須：** `skills/` サブツリー全体をアップロードし、調整役を project instructions に設定します。毎ターン、作品の現状態、story bible、timeline、人物ファイル、reader ledger、前章要約を添付するか AI に参照させます。

**約束しないこと：** 自動フォルダー作成、CLI gates、hash 検証、Git、Graphify export、会話間記憶、background tasks、第二モデルレビュー。

### D | 単一 system prompt のみのモデル（手動代替）

調整役の要約を system prompt に貼り、専門スキルとプロジェクトテンプレートを知識基盤にします。利用者・統合担当者は毎ターン生成される状態文書を手動保存しなければなりません。推論の枠組みは保てますが、完全な Novel OS と同等ではありません。

## 5. 一般的なフレームワーク統合一覧

| 種別 | 配置先 | 必須設定 | 注意点 |
|---|---|---|---|
| OpenAI Assistants/Responses 型 | System instructions＋vector/file search＋code interpreter/独自 sandbox | router、永続 file store、Python 実行アダプターを構築 | run 間の自動同期を仮定せず project file を明示保存 |
| Claude Projects/MCP 型 | Project instructions＋knowledge files；MCP filesystem/shell server | skills を resources とし MCP で read/write/runner/web | MCP がなければ C でスクリプト実行不可 |
| Gemini Gems/Vertex Agent 型 | System instruction＋File Search/Code Execution/Cloud Storage | 永続 storage、function router、Python runner を接続 | Gem 指示だけでは通常、会話間ファイル処理を提供しない |
| LangChain/LangGraph/CrewAI/AutoGen 型 | Router node＋file tools＋subprocess tool＋durable checkpointer | 意図別 skill load、project ID 保持、review-agent adapter 構築 | skill 発見・state checkpoint の実装が必要。展開だけでは有効にならない |
| Open WebUI/AnythingLLM/Dify/Flowise 型 | Knowledge base＋agent workflow/tool nodes | skill file を upload、shell/Python tool 接続、persistent volume を mount | 単なる RAG chat は C。A/B には workflow が必要 |
| 世界 DB ホスト | `WORLD_DATABASE_ROOT`＋`WORLD_DATABASE_WORK_ROOT` | 永続 world graph と batch workspace を mount、snapshot/validate/affected/export を提供 | runner がなければ JSON/Markdown 保存のみ、Graphify CLI 実行を主張しない |
| 特殊物 DB ホスト | `SPECIAL_OBJECT_DATABASE_ROOT`＋`SPECIAL_OBJECT_DATABASE_WORK_ROOT` | 永続 special-object graph と batch workspace を mount、snapshot/validate/affected/export を提供 | runner がなければ JSON/Markdown 保存のみ、特殊物の検証・export 実行を主張しない |
| Cursor/Claude Code/Codex CLI などの coding agent | Skills/commands directory＋workspace | **17 フォルダー**をインストールし Python と workspace root を設定 | 会話型 model-review adapter は該当 CLI 向けに書換えが必要 |

名称は統合種別の例です。製品版、プラン、権限は異なるため、展開前に最新文書を確認してください。

## 6. 展開受入チェックリスト

統合後、ホスト・統合担当者が各項目を検証します。

- [ ] `novel-operating-system` と隣接する専門スキル 16 個を読める
- [ ] テストファイルを書いた後、新しい agent run・会話から読める
- [ ] `python3 --version` が ≥ 3.10。graph exporter が必要なら `networkx`/`graphifyy` を import できる
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` が通るか、実行できない項目を明記した
- [ ] 新規テスト小説に story bible、state、timeline、reader ledger、graph.json が作成された
- [ ] agent が短文を書き state を更新し、新 run で続行し、連続性が残存文脈だけに依存しないと示せる
- [ ] 研究を有効にした場合、検索 snippet を正典扱いせず URL・出典・confidence を記録できる
- [ ] 第二モデルレビューを有効にした場合、adapter 失敗は unavailable 成果物だけを作り、停止や結果の捏造をしない

## 7. プラットフォーム制限と責任範囲

- 対象モデルのコンテンツ方針、ツール権限、token 制限、データ保持、ネットワーク規則は Novel OS と独立しており、この Skill は上書きできません
- 「自動展開」は、**インストール・ファイル・shell 権限を持つ agent framework 内**での自動インストール、雛形作成、router load を意味します。任意のチャットモデルに ZIP を渡せば永続インストールできるという意味ではありません
- 外部モデル、browser、Git は任意の拡張です。ない場合は代替モードを明示し、完了という表現で能力不足を隠さないでください
