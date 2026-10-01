# Novel OS のインポートと展開

<!-- language-navigation --> [繁體中文](portable-install.md) | [English](portable-install.en.md) | **日本語** | [한국어](portable-install.ko.md) | [Español](portable-install.es.md) | [Français](portable-install.fr.md) | [Deutsch](portable-install.de.md) | [Português](portable-install.pt.md)

## まず機能を棚卸しし、適切な展開モードを選ぶ

引渡し前に、対象環境に次を確認してください。

```text
1. 複数の Skill・コマンドをインストールできるか。入口ディレクトリや設定はどこか。
2. エージェントは永続ファイルの読み書き、ディレクトリ一覧、Python・shell 実行ができるか。
3. Python のバージョンは何か。networkx、graphifyy、Git のインストールは許可されるか。
4. web・browser、第二モデル、sub-agent はあるか。ツールからどう呼び出すか。
5. 新しい会話、新しい worker、再起動の後もプロジェクトファイルはどこに残るか。
```

回答に基づき **A：完全インストール**（Skills＋shell＋storage）、**B：アダプター連携**（独自エージェントツール）、**C：知識ファイルモード**、**D：単一プロンプト手動モード**を選びます。完全な評価、パッケージ、フレームワーク別のアダプター要件は [platform-compatibility.ja.md](platform-compatibility.ja.md) を参照してください。A・B の前提を満たさなければ「自動展開が完了した」とは主張できません。

## カスタムスキルディレクトリを持つ AI プラットフォーム（A：完全モード）

1. ZIP を展開します。
2. 展開先のルートで実行します。

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. プラットフォームにスキルを再走査させるか、スキルインデックスを再起動します。
4. 「長編小説プロジェクトを作成して」で試します。`novel-operating-system` が起動し、プロジェクト雛形を作り、研究・世界構築・行動・文体・グラフ作業の要否を判断し、本文執筆前に計画とゲートを完了するはずです。

**更新：** `--upgrade` を追加します。インストーラーは同名の既存スキルを `<target>/backups/novel-os-<timestamp>-<unique>/` に移してから置換し、失敗時は元のファイルを復元します。

### ライセンスと第三者の表示

完全な ZIP は、プロジェクトのライセンス、第三者ガイド、商用条件の 8 言語版（計 24 個のルート表示文書）と各スキルの元の第三者ライセンスファイルを保持しなければなりません。英語は `LICENSE`、`THIRD_PARTY.md`、`docs/COMMERCIAL_TERMS.md`、他言語はそれぞれ `.zh-TW.md`、`.ja.md`、`.ko.md`、`.es.md`、`.fr.md`、`.de.md`、`.pt.md` を用います（ライセンスは `LICENSE.<言語>.md`）。インストーラーは `<target>/novel-operating-system/DISTRIBUTION_NOTICES/` に元の相対パスで保持し、文書内のライセンスリンクを有効に保ちます。スキル内の上流表示も元の位置に残します。ホストのルート `LICENSE` や `docs/` は上書きしません。更新前の表示は、元のスキルとともにその更新のバックアップへ保存します。

`novel-operating-system/INSTALLATION.json` は各表示の出典・インストール先、SHA-256、バイト数を記録します。インストール後、展開済み ZIP から読み取り専用検査を実行します。

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

欠落や改変があれば失敗します。これはローカル整合性検査であり、信頼できるリリース元の代わりではありません。明示的な文書一覧は [bundle-contract.ja.md](bundle-contract.ja.md) を参照してください。議論用草案は有効なライセンスではなく、正式条件としてエクスポートしません。

手動移植モード B・C・D でも、プロジェクトライセンス・商用条件とすべての上流表示を一緒に引き渡してください。`skills/` だけをコピーしてライセンス文書を省略しないでください。

## カスタムエージェント・ツール呼出しフレームワーク（B：アダプター必須）

ネイティブの `SKILL.md` ランタイムがなくても、system prompt、function calling、ファイル・コマンドツールがある場合、ZIP の展開だけでは展開完了にはなりません。統合担当者は次を行います。

1. `novel-operating-system/SKILL.md` を system・developer 指示に置き、その description で意図ルーターを構築する
2. 16 個の専門スキルをルーターが必要時に読めるリソースとし、フォルダーの相対関係を保持する
3. 中断・未完作品は、まず `unfinished-novel-completion` で出典・正典・証拠・意図・実現可能性・分岐・権利・来歴を引き継ぎ、選択した分岐を長編執筆側へ渡す
4. ファイル読み書き、ディレクトリ一覧、Python プロセス、永続ワークスペース、`WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`、`SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT`、Web 研究をフレームワークのツール API に対応付ける
5. `independent_review.py` の `minis-model-use` 呼出しを、プラットフォームの第二モデル・sub-agent・API 連携に置換する。ない場合は無効にし未実行と記録する
6. 文書の展開受入チェックリストで、run 間のファイル永続性と章完了後の状態更新を試験する

LangGraph/CrewAI/AutoGen、MCP、OpenAI/Claude/Gemini、Dify/Flowise/Open WebUI の一般的な統合箇所は [platform-compatibility.ja.md](platform-compatibility.ja.md) にあります。いずれも統合担当者によるルーター・ツールアダプターが必要で、この ZIP が未知のクラウドアカウントに自動で構築することはありません。

## Skill の取込欄が 1 個だけのプラットフォーム（C：知識ファイルモード）

参照文書を含む `skills/novel-operating-system/` 全体をアップロードまたは貼り付け、他の 16 個のスキルフォルダーを同階層の添付・知識ファイルとして保持します。AI に次を指示してください。

> 最初に novel-operating-system/SKILL.md を読む。同階層のすべてのスキルは本システムに必須の協働要素である。shell がなければ同等の Markdown/JSON プロジェクトファイルを作り、実行できないゲートを示す。Git スナップショット、検証器、グラフエクスポートを実行したと偽らない。

## チャット・カスタム指示のみのプラットフォーム（D：手動代替）

`novel-operating-system/SKILL.md` を主指示、`skills/` 全体を検索用文書として使います。このモードで移植できるのはワークフロー、テンプレート、スキーマ、出力形式、ルール、チェックリストです。自動ファイル作成、ターン間永続性、CLI 検証、ZIP インストール、トリガー検知は保証できません。

### 未完作品を完成させるための展開検査

中断作品の引渡し時は、通常の小説プロジェクトファイルに加え、`completion-brief.md`、`source-manifest.json`、証拠・意図・版・分岐の台帳、`rights-and-publication.md`、`completion-provenance.md`、`completion-state.json`、completion Gate を保持します。権利不明・未許諾の作品は既定で `private-only`/`research` モードとし、本文を直接公開しません。

プロジェクトをスキル ZIP に直接入れず、別のプロジェクトフォルダーまたは整理済み ZIP として引き渡します。

1. 実在人物の機微情報、非公開出典、認証情報、未許諾の原文、共有すべきでない下書きがないか先に確認する
2. 既存システムの `snapshot_project.py`、`deep_consistency.py`、`chapter_gate.py` を実行し、結果を引継ぎメモに含める
3. `project-brief.md` で正典の確定最終章、未完の下書き章、著者の上書き権限、既知のリスクを明示する
4. 取込後は、受領者が story bible、現在状態、年表、読者台帳、伏線、エンティティ台帳、最新要約を読んでから物語を続ける
