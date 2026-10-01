# Novel OS

<!-- language-navigation -->

[繁體中文](README.zh-TW.md) | [English](README.md) | **日本語** | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | [Português](README.pt.md)

Novel OS は、長編小説、インタラクティブ小説、連続性、人物・世界研究、行動の一貫性、来歴を追跡できるグラフ、物語検証のための、再利用可能な AI エージェントスキルとローカル Python ツールの集合です。

> **ライセンス：** teateatea03 著作権の [Novel OS 商用利益分配ライセンス](LICENSE.ja.md)によるソース公開です。非商用利用は無料、商用利用は年間関連正純利益の 0.5% を支払います。改変・再配布も同じ条件と表示を保持します。MIT、GPL、OSI 認定のオープンソースライセンスではありません。

商用利用と 2 種類のトークンによる支払は、[商用利益分配・支払情報](docs/COMMERCIAL_TERMS.ja.md)を参照してください。利用者の小説やその他の出力の権利はシステム所有者に移転しません。

## 言語の対応範囲

公開文書は 8 言語で提供します。ランタイムスキル、テンプレートおよびその技術参考文書は現在、元の言語を維持しています。この多言語文書のリリースはランタイムの翻訳ではありません。

## プライバシーの境界

このソースリポジトリは、意図的に次を含めていません。

- 原稿、章の下書き、対話プレイセッション、物語の状態、著者フィードバックのデータセット
- 人物、世界、特殊物、実在人物の研究データベース
- チャットの記憶、端末ローカルの状態、バックアップ、エクスポート、認証情報、非公開エンドポイント、環境ファイル

公開例とテストデータは合成でなければなりません。push やリリース前に毎回プライバシースキャナーを実行し、ステージ済みの一覧を確認してください。

## リポジトリの構成

- `skills/`：再利用可能なスキルパッケージ、スクリプト、テンプレート、合成テストデータ
- `scripts/`：プライバシー、検証、テストのユーティリティ
- `docs/`：プロジェクト運営と公開範囲の文書

ソースツリーには 18 個のスキルディレクトリがあります。17 個のインストール可能なランタイムスキル（調整役 1 個と協働スキル 16 個）およびバンドルエクスポーターです。エクスポーターはパッケージ化ツールであり、ランタイムスキルとしてはインストールしません。

## 要件

- Python 3.10+
- 永続的な UTF-8 ストレージ
- コア処理は標準ライブラリのみ
- 任意機能：`requirements-optional.txt` と [THIRD_PARTY.ja.md](THIRD_PARTY.ja.md) を参照

任意の Python 依存関係は隔離環境にインストールしてください。

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

Graphify 連携は任意で、上流文書に従い別途インストールします。

## 初回ローカル実行（モデル・ネットワーク不要）

リポジトリのルートから Python 3.10+ と Git を使います。コア検査と合成デモには任意パッケージ、API キー、非公開原稿は不要です。

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Keep generated project state outside the source repository.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

初期化ツールは空の計画・状態の雛形を作成します。小説を生成したりモデルを呼び出したりはしません。自分の物語は別の非公開ディレクトリに置いてください。初期化ツールは既存プロジェクトへの上書きを拒否します。

エージェントホストでは、ランタイムスキルを同階層のディレクトリとして保持し、`novel-operating-system` を入口に登録してください。永続ファイルや Python プロセス実行機能がないホストは文書・手動モードのみです。バンドルコマンド、スモークテスト、任意連携、プラットフォーム制限は[検証済みのローカル構築・インストールガイド](docs/GETTING_STARTED.ja.md)を参照してください。

## 検証

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Novel Judge スイートは必ず `scripts/run_tests.py` 経由で実行してください。パッケージ相対のテストファイルを個別に実行する方法は対応していません。

プライバシーと JSON の検査は、未追跡・gitignore 対象を含むソースファイルを調べます。Git メタデータ、生成された Python・テストキャッシュ、確認済みのルート仮想環境は除外し、追跡済みファイルは引き続き検査します。シンボリックリンク、読めないファイル、非 UTF-8 テキストは安全側に倒して拒否します。生成バンドルと物語状態はチェックアウトの外に置いてください。スキャナーが報告するのはファイル名と検出カテゴリのみで、一致した内容は表示しません。これはヒューリスティックな検査であり、プライバシーの証明や履歴スキャンではありません。

## プラットフォームのパス

文書では `<SKILLS_ROOT>`、`<WORKSPACE_ROOT>`、`<NOVEL_PROJECTS_ROOT>` などのプレースホルダーを使います。ホストに合わせて設定してください。実行可能な初期化ツールは、`NOVEL_PROJECTS_ROOT` または明示的な `--root` がない場合、`~/.novel-os/novels` を既定値とします。

## 安全と研究範囲

研究スキルは合法で公開アクセス可能な資料用です。ログイン壁、CAPTCHA、ペイウォール、robots・アクセス制御、プラットフォーム制限を回避してはいけません。実在人物の研究には出典の来歴が必要で、未検証・機微な素材を事実と断定してはいけません。

## 運営

次をお読みください。

- [CONTRIBUTING.ja.md](CONTRIBUTING.ja.md)
- [CODE_OF_CONDUCT.ja.md](CODE_OF_CONDUCT.ja.md)
- [SECURITY.ja.md](SECURITY.ja.md)
- [THIRD_PARTY.ja.md](THIRD_PARTY.ja.md)

## ライセンスと貢献

商用利用前に [LICENSE](LICENSE.ja.md) と[商用支払の詳細](docs/COMMERCIAL_TERMS.ja.md)をお読みください。関連製品、サービス、小説の年間の正の純利益だけが対象で、無関係の事業は除きます。申告は自己申告で、隠れたテレメトリや自動徴収はありません。第三者コンポーネントは固有のライセンスと表示を維持します。

商用利用者は利用前にライセンス版への同意を明示します。非公開の申告経路を用意するため、私的・財務的な詳細を含まない GitHub issue から始めてください。財務諸表や支払記録を公開しないでください。貢献・再配布ルールは [CONTRIBUTING.ja.md](CONTRIBUTING.ja.md) にあります。

## 検証の限界

コアの Linux テストと合成インストール検査を提供しています。任意の Graphify・MCP・Instagram サービス、実モデル、ネイティブエージェント連携、複数プラットフォーム・Python 版の組合せは認証していません。モデル報告例は合成の説明例で、プロバイダーやモデルの実測性能の証拠ではありません。
