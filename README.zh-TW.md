# LiteLLM Admin UI 多語系支援

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

![LiteLLM version](https://img.shields.io/badge/LiteLLM-v1.94.0-5b5bd6)
![UI languages](https://img.shields.io/badge/UI_languages-5-0f766e)
![License](https://img.shields.io/badge/license-MIT-blue)

為 LiteLLM Admin UI 新增五種語言，無須維護 LiteLLM 的分支版本。
在 Docker 映像檔建置期間，本專案會將一份選定的 JSON 字典與小型瀏覽器端翻譯器嵌入 LiteLLM 匯出的 UI 頁面。字典中未收錄的字串會維持英文，因此即使仍在新增翻譯，也可在升級 LiteLLM 後繼續使用。

> 本儲存庫僅翻譯 Admin UI；不會翻譯 API 請求、模型回應、日誌或供應商內容。

## 支援的語言

| 建置值 | UI 語言 | 字典 | HTML `lang` |
|---|---|---|---|
| `en` | 英文（原文） | [`dict.en.json`](zhtw/dict.en.json) | `en` |
| `ja` | 日文 | [`dict.ja.json`](zhtw/dict.ja.json) | `ja` |
| `ko` | 韓文 | [`dict.ko.json`](zhtw/dict.ko.json) | `ko` |
| `zh-CN` | 簡體中文 | [`dict.zh-CN.json`](zhtw/dict.zh-CN.json) | `zh-Hans` |
| `zh-TW` | 繁體中文（預設） | [`dict.json`](zhtw/dict.json) | `zh-Hant` |

每份字典都包含相同的 4,599 個來源鍵。`dict.json` 為了相容本專案的舊版發行，仍使用繁體中文的檔名。

## 快速開始

### 建置本地化的 LiteLLM 映像檔

```bash
git clone https://github.com/Sen-CaPoo/litellm-zhtw.git
cd litellm-zhtw
docker build --build-arg LITELLM_UI_LANG=ja -t litellm-i18n:ja .
```

將 `ja` 替換為 `en`、`ko`、`zh-CN` 或 `zh-TW`。您可在目前使用官方 LiteLLM 映像檔的任何地方使用產生的映像檔；既有的 LiteLLM 命令、設定、資料庫與環境變數皆可維持不變。

本儲存庫目前將基底映像檔固定為 `ghcr.io/berriai/litellm:v1.94.0`。若要使用其他 LiteLLM 發行版本，僅需變更 [`Dockerfile`](Dockerfile) 中的 `FROM` 行，然後重新建置並檢查 Admin UI。

### 使用內附的 Docker Compose 範例

內附堆疊是為 PostgreSQL 與 Ollama Cloud 設定的範例。將它當成正式環境部署前，請檢閱 [`config/config.yaml`](config/config.yaml)，並改為自己的模型與供應商設定。

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

編輯 `.env`，設定 `LITELLM_UI_LANG` 與每個預留位置的祕密值，然後執行：

```bash
docker compose up -d --build
docker compose logs -f litellm
```

開啟 <http://localhost:4000/ui>。變更語言或字典後，請重新建置 `litellm` 服務並在瀏覽器進行強制重新整理：

```bash
docker compose build litellm
docker compose up -d litellm
```

> 隱私提醒：內附的 [`config/config.yaml`](config/config.yaml) 啟用了 `store_prompts_in_spend_logs`。若提示詞與模型回應不得儲存在 LiteLLM 資料庫中，請停用它。

## 將此翻譯層加入另一個 LiteLLM 專案

將 [`zhtw/`](zhtw/) 目錄複製到您的專案，並在擴充 LiteLLM 的 Dockerfile 中加入以下各行：

```dockerfile
FROM ghcr.io/berriai/litellm:<your-version>

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
```

以所需語言建置：

```bash
docker build --build-arg LITELLM_UI_LANG=ko -t my-litellm:ko .
```

`LITELLM_UI_LANG` 是建置時選項。在執行中的容器變更它不會切換 UI；請改為重新建置映像檔。不支援的值會刻意使建置失敗，並列出五個可接受的值。

## 運作方式

1. [`patch_ui.py`](zhtw/patch_ui.py) 在映像檔建置期間依 `LITELLM_UI_LANG` 選擇一份字典。
2. 它會將字典和 [`inject.js`](zhtw/inject.js) 嵌入每一個匯出的 LiteLLM UI HTML 檔案，並設定頁面語言。
3. 在瀏覽器中，會翻譯完全相符的文字與常見屬性。`MutationObserver` 也會處理稍後才轉譯出的 UI 內容。
4. `Page 2 of 5` 等動態計數會使用儲存在相同字典檔中的語言專屬範本。

如果找不到任何 LiteLLM UI HTML 檔案，建置就會停止。這可讓上游目錄異動在升級時顯現，而非悄悄產生未翻譯的映像檔。

## 儲存庫結構

| 路徑 | 用途 |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | 繁體中文字典與向下相容的預設值 |
| [`zhtw/dict.*.json`](zhtw/) | 英文、日文、韓文與簡體中文字典 |
| [`zhtw/inject.js`](zhtw/inject.js) | 共用的瀏覽器端翻譯引擎 |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | 建置時語言選擇器與 UI 修補程式 |
| [`Dockerfile`](Dockerfile) | 本地化映像檔建置 |
| [`docker-compose.yml`](docker-compose.yml) | 選用的 LiteLLM + PostgreSQL 範例 |
| [`.env.example`](.env.example) | 建置語言與範例執行階段變數 |

## 更新翻譯

字典鍵是 LiteLLM 輸出的完全相同英文文字；僅編輯值：

```json
{
  "Save": "儲存",
  "Cancel": "取消"
}
```

請維持 `$1` 等預留位置、URL、HTML 標籤、模型名稱與程式碼片段不變。五份字典都必須維持相同的鍵與鍵順序。重新建置前先執行驗證，再檢查受影響的畫面：

```bash
python scripts/validate_i18n.py
```

目前字典的目標為 LiteLLM `v1.94.0` 內附的 UI。新版 LiteLLM 可能引入新的英文文字；在新增至每份字典的鍵之前，這些文字會維持英文。

## 疑難排解

- **UI 仍顯示先前的語言：**重新建置映像檔、重新建立容器，然後在瀏覽器進行強制重新整理。
- **只有部分文字被翻譯：**確認選取字典中存在完全相同的英文文字作為鍵。超過 300 個字元的文字，以及位於程式碼、預先格式化、文字區域或可編輯元素內的內容，會刻意略過。
- **建置顯示 `no html files patched`：**選取的 LiteLLM 版本已移動匯出的 UI 目錄。只有在該 LiteLLM 映像檔中確認新路徑後，才更新 `patch_ui.py` 的 `OUT`。
- **建置拒絕語言：**請精確使用 `en`、`ja`、`ko`、`zh-CN` 或 `zh-TW`。字母大小寫及 `_`/`-` 差異會正規化。

## 貢獻

歡迎回報遺漏字串、術語改善與支援新版 LiteLLM 的 Issue 與 Pull Request。視覺情境重要時，請提供 LiteLLM 版本、頁面名稱、完全相同的英文來源文字、目標語言與螢幕截圖。

LiteLLM 由 [LiteLLM 專案](https://github.com/BerriAI/litellm) 維護。
此翻譯層依 [MIT 授權條款](LICENSE) 發布。
