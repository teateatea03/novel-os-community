# ローカル設定と可搬インストール

<!-- language-navigation -->

[繁體中文](../zh-TW/GETTING_STARTED.md) | [English](../../GETTING_STARTED.md) | **日本語** | [한국어](../ko/GETTING_STARTED.md) | [Español](../es/GETTING_STARTED.md) | [Français](../fr/GETTING_STARTED.md) | [Deutsch](../de/GETTING_STARTED.md) | [Português](../pt/GETTING_STARTED.md)

本ガイドはローカルランタイムと可搬バンドルを扱います。利用・再配布は [LICENSE](LICENSE.md)、商用申告と支払の詳細は [COMMERCIAL_TERMS.md](COMMERCIAL_TERMS.md) に従います。

## 言語の対応範囲

公開文書は 8 言語で提供します。ランタイムスキル、テンプレートおよびその技術参考文書は現在、元の言語を保持します。この多言語文書リリースはランタイムの翻訳ではありません。

## モードを選ぶ

- **ローカルツール：** Python 3.10+ と永続 UTF-8 ファイル。コア検証、プロジェクト雛形作成、テストは標準ライブラリを使います
- **エージェントランタイム：** 上記に加え、同階層の `SKILL.md` パッケージを読み込み、プロジェクトファイルを読み書きし、Python を実行できるホスト。`novel-operating-system` を入口に登録します
- **文書・手動モード：** シェルや永続ファイルがないホストでもテンプレートに従えますが、CLI ゲート、インストール、永続状態が実行済みとは主張できません

Novel OS はモデル、API アカウント、Web サービス、非公開原稿を含みません。ソーススキルディレクトリは 18 個で、17 個のランタイムスキル（調整役 1 個と協働スキル 16 個）およびエクスポーターです。

## 新しいチェックアウトを確認する

リポジトリのルートで POSIX シェルから実行してください。

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

実際の作業には別の非公開プロジェクトディレクトリを使い、既存原稿やデータベースをこのチェックアウトへコピーしないでください。最初の合成プロジェクトには[README](README.md) の `mktemp` 例を使います。明示的な `--root` は `NOVEL_PROJECTS_ROOT` より優先され、どちらもない場合は `~/.novel-os/novels` を使います。

## ローカルバンドルの構築とテスト

次のコマンドはリポジトリファイルと一時ディレクトリだけを使います。アップロード、実モデル、API キー、外部研究はありません。生成ペイロードを誤ってコミットしないよう、出力はソースチェックアウトの外に置いてください。

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

完全検証プロファイルは、ローカル回帰スイートに加えて合成の 10 万文字超の長編パイロットを実行します。ローカルの正しさの検査であり、実モデルの品質やクロスプラットフォームの認証ではありません。`--upgrade` を明示しない限り、インストーラーは既存スキルの上書きを拒否します。更新時はローカルバックアップを作ります。初回テストで稼働中のスキルディレクトリを指定しないでください。

検査が合格したらアーカイブを作成できます。

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

マニフェストは全梱包ファイルとハッシュを記録します。これにはプロジェクトライセンス、商用条件、第三者ガイドの全 8 言語版と、改作スキル内の未改変の Humanizer-zh 表示が含まれます。アーカイブとインストールでこれらの表示を保持してください。インストーラーはホストのルートライセンスを上書きせず、プロジェクト表示を `novel-operating-system/DISTRIBUTION_NOTICES/` に保持します。

## 任意機能

ホストが必要とするものだけを隔離環境にインストールしてください。

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

このファイルは互換バージョン範囲を示し、再現可能なロックではありません。任意連携を使う場合は正確なバージョンを選択・試験し、上流条件を確認してください。上のコア手順には任意依存関係は不要です。

- NetworkX は任意のグラフアルゴリズム・GraphML を有効にします。Graphify の追加エクスポーターは別途インストールします
- PyYAML は YAML の NPC 投影入力を有効にします。MCP と外部 Instagram サーバーは任意の連携です
- 元のホスト以外での独立モデルレビューには `minis-model-use` のホスト別代替が必要です。利用できなければ未実行と記録します
- `lieflat-less-ai-tone` は同梱しません。出典・ライセンスを別途確認し、不在の場合は内蔵の人間らしい文体のワークフローを使って追加工程を未実行と記録します

[THIRD_PARTY.md](THIRD_PARTY.md)、[プラットフォーム互換性](../../../skills/novel-system-exporter/references/platform-compatibility.ja.md)、[ホストアダプター契約](../../../skills/novel-system-exporter/references/host-adapter-contract.ja.md)を参照してください。Windows・ネイティブホスト・任意サービスの試験は別の受入作業であり、Linux スモークテストはそれらを検証しません。
