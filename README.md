# LiteLLM Admin UI i18n

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

![LiteLLM version](https://img.shields.io/badge/LiteLLM-v1.97.0-5b5bd6)
![UI languages](https://img.shields.io/badge/UI_languages-5-0f766e)
![License](https://img.shields.io/badge/license-MIT-blue)

Add five languages to the LiteLLM Admin UI without maintaining a fork of LiteLLM.
During the Docker image build, this project embeds one selected JSON dictionary and
a small browser-side translator into LiteLLM's exported UI pages. Strings that are
not in the dictionary stay in English, so a LiteLLM upgrade remains usable while new
translations are being added.

> This repository translates the Admin UI only. It does not translate API requests,
> model responses, logs, or provider content.

## Supported languages

| Build value | UI language | Dictionary | HTML `lang` |
|---|---|---|---|
| `en` | English (original) | [`dict.en.json`](zhtw/dict.en.json) | `en` |
| `ja` | Japanese | [`dict.ja.json`](zhtw/dict.ja.json) | `ja` |
| `ko` | Korean | [`dict.ko.json`](zhtw/dict.ko.json) | `ko` |
| `zh-CN` | Simplified Chinese | [`dict.zh-CN.json`](zhtw/dict.zh-CN.json) | `zh-Hans` |
| `zh-TW` | Traditional Chinese (default) | [`dict.json`](zhtw/dict.json) | `zh-Hant` |

Each dictionary contains the same 4,852 source keys. `dict.json` remains the
Traditional Chinese filename for compatibility with earlier releases of this project.

## Quick start

### Build a localized LiteLLM image

```bash
git clone https://github.com/Sen-CaPoo/litellm-zhtw.git
cd litellm-zhtw
docker build --build-arg LITELLM_UI_LANG=ja -t litellm-i18n:ja .
```

Replace `ja` with `en`, `ko`, `zh-CN`, or `zh-TW`. Use the resulting image wherever
you currently use the official LiteLLM image; your existing LiteLLM command,
configuration, database, and environment variables can stay the same.

This repository currently pins the base image to `ghcr.io/berriai/litellm:v1.97.0`.
To use another LiteLLM release, change only the `FROM` line in [`Dockerfile`](Dockerfile),
then rebuild and check the Admin UI.

### Use the included Docker Compose example

The included stack is an example configured for PostgreSQL and Ollama Cloud. Review
[`config/config.yaml`](config/config.yaml) and replace its model/provider settings
with your own before treating it as a production deployment.

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

Edit `.env`, set `LITELLM_UI_LANG` and every placeholder secret, then run:

```bash
docker compose up -d --build
docker compose logs -f litellm
```

Open <http://localhost:4000/ui>. After changing the language or a dictionary, rebuild
the `litellm` service and hard-refresh the browser:

```bash
docker compose build litellm
docker compose up -d litellm
```

> Privacy note: the included [`config/config.yaml`](config/config.yaml) enables
> `store_prompts_in_spend_logs`. Disable it if prompts and model responses must not be
> stored in the LiteLLM database.

## Add this translation layer to another LiteLLM project

Copy the [`zhtw/`](zhtw/) directory into your project and add these lines to the
Dockerfile that extends LiteLLM:

```dockerfile
FROM ghcr.io/berriai/litellm:<your-version>

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
```

Build it with the desired language:

```bash
docker build --build-arg LITELLM_UI_LANG=ko -t my-litellm:ko .
```

`LITELLM_UI_LANG` is a build-time option. Changing it on a running container does not
switch the UI; rebuild the image instead. An unsupported value intentionally fails the
build and prints the five accepted values.

## How it works

1. [`patch_ui.py`](zhtw/patch_ui.py) selects one dictionary from
   `LITELLM_UI_LANG` during the image build.
2. It embeds the dictionary and [`inject.js`](zhtw/inject.js) into every exported
   LiteLLM UI HTML file and sets the page language.
3. In the browser, exact text and common attributes are translated. A
   `MutationObserver` also handles UI content rendered later.
4. Dynamic counts such as `Page 2 of 5` use language-specific templates stored in
   the same dictionary files.

The build stops if no LiteLLM UI HTML file is found. This makes an upstream directory
change visible during upgrade instead of silently producing an untranslated image.

## Repository layout

| Path | Purpose |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | Traditional Chinese dictionary and backward-compatible default |
| [`zhtw/dict.*.json`](zhtw/) | English, Japanese, Korean, and Simplified Chinese dictionaries |
| [`zhtw/inject.js`](zhtw/inject.js) | Shared browser-side translation engine |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | Build-time language selection and UI patcher |
| [`Dockerfile`](Dockerfile) | Localized image build |
| [`docker-compose.yml`](docker-compose.yml) | Optional LiteLLM + PostgreSQL example |
| [`.env.example`](.env.example) | Build language and example runtime variables |

## Update a translation

Dictionary keys are the exact English strings emitted by LiteLLM. Edit the value only:

```json
{
  "Save": "保存",
  "Cancel": "キャンセル"
}
```

Keep placeholders such as `$1`, URLs, HTML tags, model names, and code fragments
unchanged. All five dictionaries must keep the same keys and key order. Run the
validator before rebuilding, then check the affected screen:

```bash
python scripts/validate_i18n.py
```

The current dictionaries target the UI bundled with LiteLLM `v1.97.0`. A newer
LiteLLM version can introduce new English strings; those strings will remain English
until their keys are added to every dictionary.

## Troubleshooting

- **The UI is still in the previous language:** rebuild the image, recreate the
  container, then hard-refresh the browser.
- **Only some text is translated:** confirm the exact English text exists as a key in
  the selected dictionary. Text longer than 300 characters and content inside code,
  preformatted, text-area, or editable elements is intentionally skipped.
- **The build says `no html files patched`:** the selected LiteLLM version moved its
  exported UI directory. Update `OUT` in `patch_ui.py` only after confirming the new
  path in that LiteLLM image.
- **The build rejects the language:** use exactly `en`, `ja`, `ko`, `zh-CN`, or
  `zh-TW`. Letter case and `_`/`-` differences are normalized.

## Contributing

Issues and pull requests are welcome for missing strings, terminology improvements,
and support for newer LiteLLM releases. Please include the LiteLLM version, page name,
exact English source text, target language, and a screenshot when visual context matters.

LiteLLM is maintained by the [LiteLLM project](https://github.com/BerriAI/litellm).
This translation layer is released under the [MIT License](LICENSE).
