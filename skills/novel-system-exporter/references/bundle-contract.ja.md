# 可搬 Novel OS バンドル契約

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | **日本語** | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | [Português](bundle-contract.pt.md)

`novel-os-portable-v<version>/` のパッケージ構造では、`skills/` に調整役 1 個と専門スキル 16 個を含めます。`public-web-research/` は安全で再開可能な公開 HTTP(S) 取得と Evidence Run 候補のステージングを提供します。`novel-model-capability-compatibility/` はモデル能力 probe・L0–L5・fallback 契約を保持します。`novel-reality-state-engine/` はイベント → 状態 → 能力 → 行動 → 本文の検証ツールを保持します。`novel-world-database-builder/` は世界データベースのスキーマ、バッチテンプレート、引継ぎパッケージ、クエリ仕様を保持します。`special-object-database-builder/` は小道具・鎧・機体・装置の版、能力、仕様、ライフサイクルのスキーマを保持します。

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── THIRD_PARTY.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   └── i18n/
│       ├── zh-TW/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── ja/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── ko/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── es/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── fr/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       ├── de/
│       │   ├── LICENSE.md
│       │   ├── THIRD_PARTY.md
│       │   └── COMMERCIAL_TERMS.md
│       └── pt/
│           ├── LICENSE.md
│           ├── THIRD_PARTY.md
│           └── COMMERCIAL_TERMS.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.{en,ja,ko,es,fr,de,pt}.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.{en,ja,ko,es,fr,de,pt}.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.{en,ja,ko,es,fr,de,pt}.md
│   ├── bundle-contract.md
│   └── bundle-contract.{en,ja,ko,es,fr,de,pt}.md
├── skills/
│   ├── novel-operating-system/      # mandatory single entry point
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

構造内の波括弧は、列挙した各言語の別ファイルを略記しています。

`MANIFEST.json` はバンドルスキーマ・版、パッケージ一覧、ソーススキルの版、各ペイロードファイルの SHA-256 とバイト数、別の `distribution_notices` 一覧、構築時刻、除外項目、ランタイム依存関係宣言を含みます。ペイロードには**プラットフォーム互換性ガイド**の可搬コピーも含めます。秘密、ローカル絶対パス、物語プロジェクト、アカウント設定、世界データベースは含めません。

## ライセンスと表示の保持

- `--source-root` はソースの `skills/` ディレクトリを指します。その親リポジトリには必須表示 24 文書すべてが必要です。英語の `LICENSE`、`THIRD_PARTY.md`、`docs/COMMERCIAL_TERMS.md` と、`zh-TW`、`ja`、`ko`、`es`、`fr`、`de`、`pt` の各 `docs/i18n/<language>/LICENSE.md`、`docs/i18n/<language>/THIRD_PARTY.md`、`docs/i18n/<language>/COMMERCIAL_TERMS.md` です。refresh は、必須文書がない、通常ファイルでない、またはシンボリックリンクの場合、ペイロードを変更する前に拒否します。これらは所有者が選択したプロジェクト条件であり、上流表示には固有の適用範囲が残ります
- 追加の明示的な許可リストは `LICENSE.md`、`LICENSE.txt`、`NOTICE`、`NOTICE.md`、`NOTICE.txt`、`docs/COMMERCIAL_LICENSE.md` です。存在する場合はバイト単位でそのままコピーします。他のルート `docs/` ファイルはエクスポートしません。特に `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` は非発効の議論用草案であり、ライセンス・商用条件としてエクスポートしません
- スキル内の `LICENSE`、`LICENSE.md`、`LICENSE.txt`、`COPYING`、`COPYING.md`、`COPYING.txt`、`NOTICE`、`NOTICE.md`、`NOTICE.txt`、`THIRD_PARTY.md` および `THIRD_PARTY_LICENSES/` 内の全ファイルをスキルとともに保持し、`distribution_notices` に宣言します。refresh はソースとのバイト一致を確認します。build・install は宣言漏れ、欠落、改変、不安全なパス、ダイジェスト項目の欠落を拒否します
- 既存の Humanizer-zh 改作素材には `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt` が特に必要です。その素材を配布する間はソースやマニフェストから除去できません
- 新しい法的必須ファイル名はリリース前にこの明示的契約に追加します。同梱していない文書へのリンクに頼らないでください。refresh は既存ペイロード内の不要になった任意のルート表示コピーを除去します
- ZIP は同じルート相対構造を維持します。インストールは全表示文書を `<target>/novel-operating-system/DISTRIBUTION_NOTICES/` に保存し、`docs/COMMERCIAL_TERMS.md` や `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt` などのパスを保ち、相対ライセンスリンクを有効にします。スキル内の上流表示も元のスキルディレクトリに残します。インストーラーは `<target>/LICENSE`、`<target>/THIRD_PARTY.md`、`<target>/docs/` には書き込みません
- `novel-operating-system/INSTALLATION.json` は各表示の元パス、インストールパス、文書コピーのパス、SHA-256、バイト数を記録します。該当する場合、ステージングと最終インストールで両コピーを検証します。更新時は旧調整役とその表示を通常のスキルバックアップに保存し、失敗すれば復元します。調整役内の `DISTRIBUTION_NOTICES/` はインストーラー管理文書の予約領域です
- 再検査には展開済みバンドルから `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` を実行します。この読み取り専用モードはルート・上流表示をインストール記録と照合します。ダイジェストはローカル整合性を示すだけで、ファイルと記録の両方を置換できる攻撃者に対する真正性ではありません。信頼できるリリースを別途保持してください

## ランタイム依存関係の宣言

各リリースには、明示的に許可した可搬参考文書 32 個をすべて含めます。`references/` の `portable-install`、`platform-compatibility`、`host-adapter-contract`、`bundle-contract` それぞれに、繁体字中国語の `.md` と、`en`、`ja`、`ko`、`es`、`fr`、`de`、`pt` の `.<language>.md` が必要です。次の段階を正直に宣言してください。

- **基本の文書ワークフロー：** Skill ファイルを読める LLM。コード実行は不要です
- **自動ローカルワークフロー（v2.7）：** Python 3.10+（3.11+ 推奨）、shell・プロセス実行機能、永続 UTF-8 ファイル、複数スキル発見機能または同等ルーター、branch lock、単一の `ProjectRuntimeAdapter.commit()` production authority、7 つの Gate、型付き意味イベント、project readiness・projection freshness、著者フィードバックの Quality Eval、ZIP 配布時の展開機能。世界データベースには書込可能な `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`、特殊物データベースには `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` も必要です
- **グラフ拡張：** 探索には `networkx`、Graphify HTML・コミュニティ・Cypher エクスポートには `graphifyy` と `networkx`。どちらがなくてもグラフ JSON 自体は使えます
- **任意連携：** コミット用 Git、出典研究用 web・browser、独立レビュー用のホスト固有第二モデル・sub-agent アダプター。置換するまでは `independent_review.py` は Minis 専用です

基本のローカル動作に Node.js、データベースサーバー、API キー、インターネット接続は不要です。ファイル・プロセスアクセスがないフレームワークは完全自動インストールではなく、文書・手動モードと表現してください。

## 構築方針

- ペイロードは許可リストのスキルディレクトリ **17 個**（調整役 1＋専門 16）、可搬参考文書、インストール・構築スクリプト、通常のテキスト・ソース・テストデータ・テンプレートを含む必要があります
- `.git`、`.DS_Store`、`__pycache__`、`*.pyc`、`.env*`、`node_modules`、`dist`、`build`、全小説プロジェクト、データベース、アーカイブ、システム固有ファイルを除きます
- ペイロード変更前に、ソーススキルパスや梱包スキル内のシンボリックリンクを拒否し、無関係のホストファイルへ追従しません。既存の未承認ペイロード文書も、黙って新マニフェストに入れず refresh を失敗させます
- ソースの `scripts/*.py` に実行ビットがあれば保持します
- ローカルのソーススキルツリーとリポジトリ階層の明示的表示許可リストだけを読みます。構築は `built_at` 以外は決定的です
- バンドルは自己完結です。ランタイム補助は Python 標準ライブラリを使い、インストール場所から相対的に依存関係を発見します

## 検証方針

`verify` は欠落、改変、想定外、ハッシュ不一致のペイロードを拒否し、続いて全 Python ファイルをコンパイルしなければなりません。インストーラーのスモークテストはさらに次を実行します。

1. 有効な production authority の下で一時小説プロジェクトを初期化する
2. FileStore の直接的な正典変更がフェンスで阻止されることを検証する
3. Gate authority、readiness、command executor、Quality Eval v2、型付き意味イベント、通常の長編制作を含む完全な Novel Judge スイートを実行する
4. グラフ検証器と長編・Reality・能力の回帰を実行する
5. 同梱スキル集合とソース集合のずれを検証する
6. 完全リリースでは、隔離した第 2 プロジェクトの契約 probe と 10 万文字超の通常長編・知識反転・連鎖修正パイロットを実行する

Python を実行できないプラットフォームはワークフロー・文書レベルのみの対応です。引渡し時にその制限を明示してください。
