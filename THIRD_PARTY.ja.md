# 第三者のコンポーネントと参考資料

<!-- language-navigation --> [繁體中文](THIRD_PARTY.zh-TW.md) | [English](THIRD_PARTY.md) | **日本語** | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | [Deutsch](THIRD_PARTY.de.md) | [Português](THIRD_PARTY.pt.md)

Novel OS には、第三者プロジェクトと連携する、またはそれらについて説明する独自のコードと文書が含まれます。ファイルに明示されている場合を除き、第三者プロジェクトのソース副本は本リポジトリに**同梱されていません**。

## 実行環境と任意の依存関係

| コンポーネント | 用途 | ライセンス／出典 |
|---|---|---|
| Python | 実行環境（3.10+） | Python Software Foundation License |
| NetworkX | グラフアルゴリズムと GraphML エクスポート | BSD-3-Clause; https://networkx.org/ |
| PyYAML | NPC 投影ユーティリティへの YAML 状態入力 | MIT; https://pyyaml.org/ |
| MCP Python SDK | 任意のローカル Instagram MCP クライアント | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify（`graphifyy`） | 任意のグラフ分析／エクスポート連携 | 上流は Apache-2.0 と記載し、MIT ライセンス素材も含む; https://github.com/Graphify-Labs/graphify |

匿名 Instagram MCP サーバーと Instaloader は別個の任意コンポーネントであり、ここには含まれません。運用者は自らインストールし、プラットフォーム条件、適用法、robots・アクセス制御、本プロジェクトの公開データ限定要件を守る責任があります。

## 研究の参考資料

文書は研究の引用として記事、仕様、書籍、ツール、公開プロジェクトにリンクしています。リンクと説明は、それらのコードや文章を Novel OS に取り込むものではありません。単にアイデアを参照するのではなく、コードや文章を改作する貢献には、正確な出典、ライセンス、変更点および必要な帰属表示を示さなければなりません。

## 本配布物に含まれる改作素材

- **Humanizer-zh**、copyright (c) 2026 歸藏、MIT：[commit f4518a8eab97b8bfebc66a89d34320a89bef6930 の上流ソース](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - 改作：`skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` は 31 の編集チェックポイントを繁体字中国語に翻訳・要約し、小説向けの保持・競合ルールを加えています
  - [上流 MIT 表示](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt)を保持し、その正確な上流 commit と照合済みです
  - この表示はソース、可搬バンドル、インストール済みランタイムのスキルに付随します。上流素材に適用されるもので、Novel OS 全体に適用される**ものではありません**。プロジェクト独自の素材には別途 [LICENSE](LICENSE.ja.md) が適用されます

## ここで配布していない外部ホスト連携

`lieflat-less-ai-tone` はホスト提供の任意の編集工程であり、17 個のランタイムスキルには含まれません。連携文書は外部リビジョンを記録していますが、本リポジトリには確認済みの上流 URL・ライセンスも実装もありません。自動的に取得、同梱、実行済みと主張しないでください。存在しない場合は内蔵の人間らしい文体のワークフローを維持し、追加工程は未実行と記録してください。インストールや配布の前に、来歴とライセンスを別途確認してください。

`minis-model-use` の独立レビューアダプターは元のホストを必要とします。他のホストは明示的に設定された代替手段を用意するか、独立モデルレビューを未実行と記録しなければなりません。ローカル回帰テストは実モデル、Graphify、MCP、Instagram サービスを試験しません。

## 依存関係の境界

上記の任意パッケージはコア配布物に同梱・インストールされません。それぞれのライセンス義務は各配布物に従います。連携の有効化や組合せパッケージの再配布前に、正確な上流バージョンを確認してください。コアテストはこれらの依存関係なしで動作します。この一覧はレビューの補助であり、法的助言ではありません。
