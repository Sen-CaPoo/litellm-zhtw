# LiteLLM 管理介面正體中文化（字典注入法）

不改 LiteLLM 任何原始碼，在建置 Docker 映像檔時，把一份英翻中字典和一小段翻譯用的 JavaScript
縫進管理介面每一頁 HTML 的 `</body>` 之前。翻譯 100% 發生在瀏覽器端，
升級官方版本不會壞，漏翻的字自動維持英文顯示（優雅降級）。

**📖 完整教學網頁（含可直接複製給 AI 代理的 Prompt）→ <https://sen-capoo.github.io/litellm-zhtw/>**

## 檔案指引

| 檔案 | 用途 |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | 英翻中字典，**完整 4,362 條**。長期要維護的只有這一個檔案 |
| [`zhtw/inject.js`](zhtw/inject.js) | 執行期翻譯引擎，複製即用、一字不改 |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | 建置期注入腳本，`docker build` 時跑一次 |
| [`Dockerfile`](Dockerfile) | 三行，以官方 image 為基底多做一道縫合手續 |
| [`docs/index.html`](docs/index.html) | 上面那個教學網頁的原始檔（單檔、零外部依賴） |
| [`docker-compose.yml`](docker-compose.yml)、[`config/config.yaml`](config/config.yaml) | 本專案實際的部署設定，可當範例參考 |
| [`.env.example`](.env.example) | 需要設定的環境變數範本（真正的 `.env` 不在版控裡） |

最快的用法：把 `zhtw/` 三個檔案放進你的專案，建立上面那個三行 `Dockerfile`，
然後 `docker compose build && docker compose up -d`，最後按 <kbd>Ctrl</kbd>+<kbd>F5</kbd>。
細節與疑難排解都在教學網頁裡。

換成簡體、日文或其他語言，只要替換 `dict.json` 的內容（以及 `inject.js` 裡 `RULES` 的句型），
其他檔案都不用動。

以 LiteLLM `v1.93.0` 實測，含一次跨版本升級。MIT 授權。

---

以下是本專案自己的部署紀錄，也可以當作 LiteLLM + PostgreSQL 的 Docker Compose 部署範例。

## LiteLLM 閘道(正體中文 UI)部署說明

以 Docker Compose 部署的 LiteLLM Proxy + PostgreSQL,前端管理介面已正體中文化,
上游串接 Ollama Cloud(glm-5.2、kimi-k2.7-code 等模型)。

## 架構

| 元件 | 說明 |
|---|---|
| `litellm`(容器) | API 閘道,對外埠 `4000`;管理介面在 `http://localhost:4000/ui` |
| `litellm_db`(容器) | PostgreSQL 16,儲存虛擬金鑰、用量、prompt 紀錄(僅綁定 127.0.0.1:5432) |
| `Dockerfile` + `zhtw/` | 以官方 image 為基底,build 時把正體中文翻譯字典注入 UI |
| `config/config.yaml` | 模型清單與 proxy 設定 |
| `.env` | 所有機密(master key、資料庫密碼、UI 帳密、Ollama API Key)。**請勿外流、勿提交版控** |

## 常用指令(在本資料夾執行)

```bash
docker compose up -d          # 啟動(背景執行,開機自動重啟)
docker compose logs -f litellm  # 看即時日誌
docker compose restart litellm  # 改 config.yaml 後重啟生效
docker compose build && docker compose up -d   # 改 zhtw/ 翻譯字典後重建生效
docker compose down           # 停止(資料保留在 volume)
```

## 首次設定:填入 Ollama API Key

1. 到 https://ollama.com/settings/keys 建立 API Key
2. 編輯 `.env`,把 `OLLAMA_API_KEY=REPLACE_WITH_YOUR_OLLAMA_KEY` 換成真實的 Key
3. `docker compose up -d` 重新載入

## 管理介面

- 網址:`http://localhost:4000/ui`(同事從區網連:`http://<你的電腦IP>:4000/ui`)
- 帳號/密碼:見 `.env` 的 `UI_USERNAME` / `UI_PASSWORD`

## 發金鑰給同事

1. 進 UI →「虛擬金鑰」→「建立新金鑰」
2. 建議做法:先在「團隊」建立部門團隊並設定預算/速率上限,再把金鑰掛在團隊底下,之後報表可按團隊彙整
3. 把產生的 `sk-...` 金鑰交給同事;同事端設定:

```python
from openai import OpenAI
client = OpenAI(base_url="http://<你的電腦IP>:4000/v1", api_key="sk-同事的虛擬金鑰")
resp = client.chat.completions.create(
    model="glm-5.2",   # 或 kimi-k2.7-code,或 ollama_chat/<任何 Ollama Cloud 模型>
    messages=[{"role": "user", "content": "你好"}],
)
```

也可以用 API 直接發金鑰(自動化用):

```bash
curl -s http://localhost:4000/key/generate \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"key_alias":"某同事","max_budget":20,"duration":"90d"}'
```

## 用量與 Prompt 監控

- **用量**頁:依模型/金鑰/團隊的請求數、Token 數、花費趨勢
- **紀錄**頁:每一筆請求的完整內容(已啟用 `store_prompts_in_spend_logs`,
  會保存 prompt 與回應內文,供日後分析)
- 想直接撈資料庫做分析:`postgresql://litellm:<POSTGRES_PASSWORD>@127.0.0.1:5432/litellm`,
  主要資料表為 `LiteLLM_SpendLogs`;prompt 內容在 `proxy_server_request` 欄位、
  模型回應在 `response` 欄位(`messages` 欄位是 Realtime API 專用,一般對話不會用到)

## 新增/調整模型

- 改 `config/config.yaml` 的 `model_list` 後 `docker compose restart litellm`
- 或直接在 UI「模型與端點」→ 新增模型(存進資料庫,不用改檔案)
- 已內建萬用路由:呼叫 `ollama_chat/<模型名>` 即可用任何 Ollama Cloud 模型

## 中文化維護

- 字典檔:`zhtw/dict.json`(英文 → 正體中文,精確比對)
- 介面上看到沒翻到的字串:把它加進 `dict.json`,然後
  `docker compose build && docker compose up -d`
- 動態字串規則(含數字的句型)在 `zhtw/inject.js` 的 `RULES`
- 翻譯是執行時注入(不改 LiteLLM 程式碼),升級 LiteLLM 版本後照常可用,
  新增的介面文字會顯示英文,補字典即可

## 讓同事連得進來(Windows 防火牆)

以系統管理員身分執行一次:

```powershell
netsh advfirewall firewall add rule name="LiteLLM 4000" dir=in action=allow protocol=TCP localport=4000
```

## 備份

```bash
docker exec litellm_db pg_dump -U litellm litellm > backup_$(date +%Y%m%d).sql
```
