# LiteLLM Admin UI i18n

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

![LiteLLM version](https://img.shields.io/badge/LiteLLM-v1.99.0-5b5bd6)
![UI languages](https://img.shields.io/badge/UI_languages-5-0f766e)
![License](https://img.shields.io/badge/license-MIT-blue)

LiteLLM のフォークを維持することなく、LiteLLM Admin UI に 5 言語を追加できます。
Docker イメージのビルド時に、このプロジェクトは選択した JSON 辞書と小さなブラウザ側翻訳機能を
LiteLLM のエクスポート済み UI ページに埋め込みます。辞書にない文字列は英語のまま残るため、新しい
翻訳を追加している間も、LiteLLM をアップグレードした後で引き続き利用できます。

> このリポジトリが翻訳するのは Admin UI のみです。API リクエスト、モデル応答、ログ、プロバイダーのコンテンツは翻訳しません。

## 対応言語

| ビルド値 | UI 言語 | 辞書 | HTML `lang` |
|---|---|---|---|
| `en` | 英語（オリジナル） | [`dict.en.json`](zhtw/dict.en.json) | `en` |
| `ja` | 日本語 | [`dict.ja.json`](zhtw/dict.ja.json) | `ja` |
| `ko` | 韓国語 | [`dict.ko.json`](zhtw/dict.ko.json) | `ko` |
| `zh-CN` | 中国語（簡体字） | [`dict.zh-CN.json`](zhtw/dict.zh-CN.json) | `zh-Hans` |
| `zh-TW` | 中国語（繁体字、既定値） | [`dict.json`](zhtw/dict.json) | `zh-Hant` |

各辞書には同じ 5,060 個のソースキーが含まれます。`dict.json` は、このプロジェクトの以前のリリースとの互換性のため、中国語（繁体字）のファイル名として維持されています。

## クイックスタート

### ローカライズ済み LiteLLM イメージをビルドする

```bash
git clone https://github.com/Sen-CaPoo/litellm-zhtw.git
cd litellm-zhtw
docker build --build-arg LITELLM_UI_LANG=ja -t litellm-i18n:ja .
```

`ja` は `en`、`ko`、`zh-CN`、または `zh-TW` に置き換えられます。現在公式 LiteLLM イメージを使用している場所で生成されたイメージを使用してください。既存の LiteLLM コマンド、設定、データベース、環境変数はそのまま利用できます。

このリポジトリでは現在、ベースイメージを `ghcr.io/berriai/litellm:v1.99.0` に固定しています。別の LiteLLM リリースを使用するには、`FROM` 行だけを [`Dockerfile`](Dockerfile) で変更してから、再ビルドして Admin UI を確認してください。

### 同梱の Docker Compose サンプルを使う

同梱のスタックは PostgreSQL と Ollama Cloud 向けに設定されたサンプルです。本番環境に導入する前に、[`config/config.example.yaml`](config/config.example.yaml) を確認し、モデル／プロバイダー設定を独自の内容に置き換えてください。

```bash
# macOS / Linux
cp .env.example .env
cp config/config.example.yaml config/config.yaml

# Windows PowerShell
Copy-Item .env.example .env
Copy-Item config/config.example.yaml config/config.yaml
```

`.env` を編集し、`LITELLM_UI_LANG` とすべてのプレースホルダーシークレットを設定してから、次を実行します。

```bash
docker compose up -d --build
docker compose logs -f litellm
```

<http://localhost:4000/ui> を開きます。言語または辞書を変更した後は、`litellm` サービスを再ビルドし、ブラウザをハードリフレッシュしてください。

```bash
docker compose build litellm
docker compose up -d litellm
```

> プライバシーに関する注意: 同梱の [`config/config.example.yaml`](config/config.example.yaml) では `store_prompts_in_spend_logs` が有効です。プロンプトとモデル応答を LiteLLM データベースに保存してはならない場合は無効にしてください。

## この翻訳レイヤーを別の LiteLLM プロジェクトに追加する

[`zhtw/`](zhtw/) ディレクトリをプロジェクトにコピーし、LiteLLM を拡張する Dockerfile に次の行を追加します。

```dockerfile
FROM ghcr.io/berriai/litellm:<your-version>

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
```

希望する言語でビルドします。

```bash
docker build --build-arg LITELLM_UI_LANG=ko -t my-litellm:ko .
```

`LITELLM_UI_LANG` はビルド時のオプションです。実行中のコンテナで変更しても UI は切り替わりません。代わりにイメージを再ビルドしてください。未対応の値を指定すると、意図的にビルドが失敗し、受け付ける 5 つの値が表示されます。

## 仕組み

1. [`patch_ui.py`](zhtw/patch_ui.py) は、イメージビルド時に `LITELLM_UI_LANG` に基づいて 1 つの辞書を選択します。
2. 辞書と [`inject.js`](zhtw/inject.js) を、エクスポートされたすべての LiteLLM UI HTML ファイルに埋め込み、ページ言語を設定します。
3. ブラウザでは、完全一致するテキストと一般的な属性を翻訳します。`MutationObserver` は後から描画される UI コンテンツも処理します。
4. `Page 2 of 5` のような動的な件数表示には、同じ辞書ファイルに保存された言語別テンプレートを使用します。

LiteLLM UI HTML ファイルが見つからない場合、ビルドは停止します。これにより、上流のディレクトリ変更を翻訳されていないイメージを暗黙に生成するのではなく、アップグレード時に検出できます。

## リポジトリ構成

| パス | 用途 |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | 中国語（繁体字）の辞書および後方互換の既定値 |
| [`zhtw/dict.*.json`](zhtw/) | 英語、日本語、韓国語、中国語（簡体字）の辞書 |
| [`zhtw/inject.js`](zhtw/inject.js) | 共有ブラウザ側翻訳エンジン |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | ビルド時の言語選択と UI パッチャー |
| [`Dockerfile`](Dockerfile) | ローカライズ済みイメージのビルド |
| [`docker-compose.yml`](docker-compose.yml) | 任意の LiteLLM + PostgreSQL + Redis サンプル |
| [`config/config.example.yaml`](config/config.example.yaml) | プロキシ設定のサンプル。`config/config.yaml` にコピーして使用 |
| [`config/custom_callbacks.py`](config/custom_callbacks.py) | 上流の低エントロピーな応答 id を一意な値に置き換え、支出ログが黙って破棄されるのを防ぐ |
| [`.env.example`](.env.example) | ビルド言語と実行時変数のサンプル |

## 翻訳を更新する

辞書のキーは LiteLLM が出力する正確な英語文字列です。値だけを編集してください。

```json
{
  "Save": "保存",
  "Cancel": "キャンセル"
}
```

`$1` などのプレースホルダー、URL、HTML タグ、モデル名、コード断片は変更しないでください。5 つの辞書ではキーとキー順を同一に保つ必要があります。再ビルド前に検証を実行し、影響する画面を確認してください。

```bash
python scripts/validate_i18n.py
```

現在の辞書は LiteLLM `v1.99.0` に同梱される UI を対象としています。新しい LiteLLM バージョンでは新しい英語文字列が追加されることがあり、すべての辞書にキーを追加するまで、それらの文字列は英語のままです。

## トラブルシューティング

- **UI が以前の言語のまま:** イメージを再ビルドし、コンテナを再作成してから、ブラウザをハードリフレッシュしてください。
- **一部のテキストしか翻訳されない:** 選択した辞書に正確な英語テキストがキーとして存在することを確認してください。300 文字を超えるテキスト、およびコード、整形済み、テキストエリア、編集可能な要素の内部コンテンツは意図的にスキップされます。
- **ビルドに `no html files patched` と表示される:** 選択した LiteLLM バージョンでエクスポート済み UI ディレクトリが移動されています。`OUT` を `patch_ui.py` で更新するのは、その LiteLLM イメージ内の新しいパスを確認した後だけにしてください。
- **ビルドが言語を拒否する:** `en`、`ja`、`ko`、`zh-CN`、`zh-TW` のいずれかを正確に指定してください。大文字と小文字、および `_`／`-` の違いは正規化されます。

## コントリビュート

不足している文字列、用語の改善、または新しい LiteLLM リリースへの対応に関する Issue とプルリクエストを歓迎します。視覚的な文脈が重要な場合は、LiteLLM バージョン、ページ名、正確な英語ソーステキスト、対象言語、およびスクリーンショットを添付してください。

LiteLLM は [LiteLLM project](https://github.com/BerriAI/litellm) によって保守されています。
この翻訳レイヤーは [MIT License](LICENSE) の下で公開されています。
