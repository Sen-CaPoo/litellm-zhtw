# 🌏 不改任何原始碼,把 LiteLLM 管理介面變成正體中文 —「字典注入法」完整教學

> **一句話:** 我們**沒有改 LiteLLM 的任何程式碼**,而是在打包 Docker 映像檔時,把一本「英翻中字典」和一位「即時翻譯員(一小段 JavaScript)」縫進管理介面的每一頁 HTML。之後每次開啟畫面,翻譯員就自動把英文換成中文;升級版本不會壞,漏翻的字會自動維持英文顯示。

已在正式環境實測沿用(含一次 LiteLLM 版本升級),介面幾乎全中文、升級後只需補少量新字串。

本文分兩部分:
- **Part 1|給所有人**:概念 + 完整操作(照著做就能跑起來)
- **Part 2|給工程師**:技術原理、完整原始碼、已知限制與取捨

---

## 這套做法適合誰

- 想把 LiteLLM 管理介面變成正體中文(或任何語言)的人
- 不想每次官方升級就把翻譯重做一次的人
- 只有 Docker 環境、希望「一次設定、長期沿用」的人

> 換語言只要替換字典內容即可,`inject.js` / `patch_ui.py` / `Dockerfile` 幾乎不用動。以下以正體中文(zh-TW)為例。

---

## 核心概念:三個角色

用一個比喻:LiteLLM 是一棟原廠進口的英文展示館,我們請了三位幫手。

**1. 字典 `dict.json`(英翻中對照表)**
一本收錄約 4,300+ 條「英文原句 → 中文譯句」的對照手冊。
例如:`"Virtual Keys": "虛擬金鑰"`、`"Usage": "用量"`、`"Spend": "花費"`。

**2. 翻譯員 `inject.js`(瀏覽器裡的即時翻譯)**
一段極小的 JavaScript。你一打開網頁,他先把整頁英文翻一遍,接著**持續盯著畫面**(介面內容是動態產生的),新冒出來的英文立刻查字典換成中文。他還懂「句型」——像 `Page 3 of 10` 這種含數字、字典查不到的句子,會套用規則翻成「第 3 頁,共 10 頁」。

**3. 裝訂工人 `patch_ui.py`(打包時執行一次)**
在建置 Docker 映像檔的那一刻,把字典和翻譯員**縫進**管理介面的每一頁 HTML,並順手把舊版由伺服器渲染的登入頁直接改成中文。做完這一次,之後每次開網頁翻譯員就自動就位。

---

## 為什麼不直接改原始碼?

- **直接改 LiteLLM 原始碼** → 官方每次更新,改過的地方全部要重做,維護成本極高,還容易衝突。
- **等官方推出中文版** → 目前沒有正體中文介面。
- **字典注入(本做法)** → 完全不動原始碼;升級版本時字典照常沿用;新增的英文字頂多先顯示英文,系統功能完全不受影響。

核心優點是**優雅降級(graceful degradation)**:就算某句話字典裡沒有,畫面也只是顯示原本的英文,系統一切正常。

---

# Part 1|完整操作(非資訊人員照著做)

## 你需要準備

- 已安裝 Docker(Windows 用 Docker Desktop 即可)
- 一個用 Docker / Docker Compose 跑 LiteLLM 的環境

## 步驟 0:資料夾長這樣

```
你的專案/
├─ Dockerfile
└─ zhtw/
   ├─ dict.json      # 英翻中字典
   ├─ inject.js      # 即時翻譯員(直接複製本文 Part 2 的版本)
   └─ patch_ui.py    # 裝訂工人(直接複製本文 Part 2 的版本)
```

## 步驟 1:建立 zhtw/ 三個檔案

`inject.js` 與 `patch_ui.py` 直接複製 **Part 2 的完整原始碼**,一字不改即可使用。
真正要維護的是 `dict.json`。它的格式是一個大 JSON 物件,每行一組「英文: 中文」:

```json
{
"Virtual Keys": "虛擬金鑰",
"Teams": "團隊",
"Usage": "用量",
"Logs": "紀錄",
"Models": "模型",
"Spend": "花費",
"Budget": "預算",
"Create New Key": "建立新金鑰",
"Test Key": "測試金鑰",
"Settings": "設定"
}
```

規則:
- 每組用**半形雙引號**包住,英文在前、中文在後,中間一個冒號。
- 每行結尾要有逗號,**最後一行不要逗號**。
- 若英文本身含有雙引號,要用反斜線跳脫,例:`"Say \"Hi\"": "說「你好」"`。

> 完整的 4,300+ 條字典怎麼一次生出來?見 Part 2〈字典是怎麼做出來的〉。想先跑起來的話,先放幾十條最常見的詞就能動了。

## 步驟 2:建立 Dockerfile

```dockerfile
# 以官方 image 為基底(建議釘住版本號,不要用 latest)
FROM ghcr.io/berriai/litellm:v1.93.0

COPY zhtw/ /zhtw/
RUN python /zhtw/patch_ui.py && rm -rf /zhtw
```

只做兩件事:把 `zhtw/` 複製進去、執行裝訂工人(裝完就刪掉,不留在映像檔裡)。

## 步驟 3:建置並啟動

如果你用 docker-compose,把 litellm 服務改成用本地 build:

```yaml
services:
  litellm:
    build: .                      # ← 改用本地 Dockerfile 建置
    image: litellm-zhtw:v1.93.0   # ← 自訂一個 image 名稱
    # ...其餘設定(埠號、env_file、config 掛載)照你原本的不動
```

然後在專案資料夾執行:

```bash
docker compose build
docker compose up -d
```

（沒用 compose 的話:`docker build -t litellm-zhtw:v1.93.0 .`,再照你原本的方式啟動這個 image。）

建置時看到類似這兩行,就代表縫入成功(數字會依版本不同):

```
zhtw: patched 48 html files, dict entries = 4362
zhtw: patched legacy login form
```

## 步驟 4:驗證

1. 打開管理介面 `http://localhost:4000/ui`
2. 按 `Ctrl + F5` 強制重新整理(清掉瀏覽器快取)
3. 介面應該變成中文了 🎉

---

## 日常維護

### A. 發現某處還是英文(字典漏字)

1. 把畫面上那句**完整的英文**抄下來(大小寫、標點都要一模一樣)。
2. 打開 `zhtw/dict.json`,加一行:`"那句英文": "你的翻譯",`
3. 重新建置:`docker compose build && docker compose up -d`
4. 瀏覽器按 `Ctrl + F5`,確認該處變成中文。

> 小提醒:抄英文時,句中連續的空白會被系統視為一個空白(會自動壓縮),所以中間多幾個空格沒關係,但**字要完全相同**。

### B. 升級 LiteLLM 版本

1. 改 Dockerfile 第一行的版本號(例 `v1.93.0` → 新版本)。
2. `docker compose build && docker compose up -d`。
3. 升級後,新版新增的介面文字會**暫時顯示英文**——這是正常的優雅降級,不是故障。把新出現的英文照〈A〉的步驟補進字典即可。

### C. 翻譯要修正

直接在 `dict.json` 找到那句英文,改冒號後面的中文,重新 build 即可。

---

# Part 2|技術原理(給工程師)

## 整體流程

```
【建置期】docker build(只跑一次)
  官方 litellm image
     └─ patch_ui.py:
         1. 讀 dict.json + inject.js
         2. 把 inject.js 裡的 __ZHTW_DICT__ 佔位符換成壓縮後的字典 JSON
         3. 以 <script id="zhtw-i18n"> 包起來,插入每個 .html 的 </body> 前
         4. 字串替換伺服器端渲染的登入頁 ui_login.py
  → 產出自訂 image(zhtw 資料夾隨即刪除)

【執行期】使用者開啟 /ui(全在瀏覽器端)
  inject.js 甦醒:
     1. 先 walk 整個 DOM,翻譯現有文字與白名單屬性
     2. MutationObserver 持續監看 DOM 變動(React 重繪)
     3. 新節點/文字/屬性一出現 → 查字典或套規則 → 就地替換
```

關鍵:翻譯 100% 發生在**瀏覽器端**,LiteLLM 伺服器本體與 API 完全沒有被更動。

## patch_ui.py 做了什麼(建置期)

- 透過 `litellm.__file__` 定位套件路徑,找到 UI 匯出目錄 `proxy/_experimental/out`。
- 把 `inject.js` 裡的 `__ZHTW_DICT__` 佔位符,替換成 `json.dumps(dict, ensure_ascii=False, separators=(",",":"))` 的壓縮字典。
- **關鍵防呆**:把 payload 裡所有 `</` 換成 `<\/`。因為字典是內嵌進 `<script>` 標籤,若資料中出現 `</script>`(或任何 `</`)會讓 HTML parser 提前關閉 script;而在 JS/JSON 字串裡 `<\/` 與 `</` 完全等價,替換後語意不變、卻不會被 HTML 誤判。
- 對每個 `.html`:把 `<html lang="en">` 改為 `<html lang="zh-Hant">`,並在 `</body>` 前插入 `<script id="zhtw-i18n">…</script>`。以 `if "zhtw-i18n" in s` 判斷確保**冪等**(重跑不會重複注入)。
- `assert count > 0`:萬一未來官方改了 UI 路徑,建置會**直接失敗**提醒你,而不是默默產出一個沒翻譯的 image。
- 登入頁 `ui_login.py` 是**伺服器端 Python 動態渲染**的,不在 `out/*.html` 裡,JS 攔不到,因此改用精確字串替換處理。

## inject.js 的翻譯引擎(執行期)

核心是一個 IIFE,幾個重點設計:

- **精確比對優先**:`tr()` 先把字串正規化 `raw.replace(/\s+/g,' ').trim()`(壓縮空白、去頭尾),再查 `DICT[key]`。所以字典的 key 也必須是「單空白、去頭尾」的形式。
- **動態句型規則 `RULES`**:字典查不到時,依序套用一組錨定(`^…$`)的正則,處理含數字的句子。例:
  ```js
  [/^Page (\d+) of (\d+)$/, '第 $1 頁,共 $2 頁'],
  [/^(\d+) keys?$/, '$1 把金鑰'],
  ```
- **只翻該翻的**:
  - 跳過標籤 `SCRIPT / STYLE / NOSCRIPT / TEXTAREA / CODE / PRE / KBD / SAMP`,以及 `isContentEditable` 節點(不動使用者輸入框、程式碼區塊)。
  - 文字節點翻 `nodeValue`;元素只翻白名單屬性 `placeholder / title / aria-label / alt`,以及 `<input type=submit|button>` 的 `value`。
- **走訪 DOM**:`document.createTreeWalker(root, 5, …)`(`5` = `SHOW_ELEMENT | SHOW_TEXT`),一次翻完整棵子樹;`acceptNode` 對要跳過的標籤回 `FILTER_REJECT`,連同其子孫一起略過。
- **追動態內容**:`MutationObserver` 監聽 `childList / characterData / attributes`(屬性只聽白名單 `attributeFilter`)、`subtree: true`。這是能跟上 React 重繪的關鍵——任何新掛上的節點都會被 `walk()` 補翻。
- **長度保險**:`key.length > 300` 直接跳過,避免拿長段落去查字典。

## 字典是怎麼做出來的

不是人工一條條抄:

1. 從 LiteLLM 官方原始碼對應版本 tag 的 `ui/litellm-dashboard/src`,用正則萃取所有 UI 字串常值(約 4,300+ 條)。
2. 交給 LLM 分批平行翻譯,並使用**固定術語表**確保全站一致(Virtual Key→虛擬金鑰、Spend→花費、Team→團隊…)。
3. 合併去重,輸出成 `dict.json`(建議 `json.dumps(indent=0, sort_keys=True, ensure_ascii=False)` ——每行一條、依字母排序,方便日後 diff 與補字)。

**升級補字流程**:`docker cp` 匯出新舊兩版 image 的 `out/` → 抽取字串常值取差集 → 機械過濾雜訊(Tailwind class、SVG path、程式碼片段;注意別誤殺以引號開頭的 placeholder 範例)→ 交 LLM 翻譯新增部分 → 併回 `dict.json`。

## 已知限制與取捨

- **每頁都內嵌整份字典**:實作上把完整字典 inline 進**每一個** HTML 檔(數十個),換來零額外請求、無路徑/快取問題;代價是 image 稍大、字典有冗餘。要更省可改成共用一支外部 JS,但要自行處理載入時序與快取。
- **只翻畫面文字**:模型回覆內容、API 資料一律不碰(靠 `CODE/PRE/TEXTAREA/contentEditable` 白名單保護)。
- **極少數閃爍**:動態內容是「先出現英文 → observer 立刻替換」,理論上有極短暫的英文閃現,實務上肉眼幾乎無感。
- **精確比對的代價**:一句話被框架拆成多個文字節點時可能查不到;這類要靠 `RULES` 或拆句補字典解決。

## 版本釘選小抄

LiteLLM 的 ghcr 標籤現在用**純版本號**(如 `v1.93.0`);舊的 `main-v<版本>` 命名大約停在 v1.66。想查有哪些 tag 可用 `docker manifest inspect` 逐一探測。**強烈建議釘住版本**,不要用 `main-stable` / `latest`,以免某次 build 悄悄換版導致字典對不上、大量文字回退成英文。

---

## 完整原始碼(可直接複製使用)

### `zhtw/inject.js`

```javascript
(function () {
  'use strict';
  var DICT = __ZHTW_DICT__;
  var RULES = [
    [/^Showing (\d+)\s*(?:to|-|–)\s*(\d+) of (\d+)(?: results?)?$/, '顯示第 $1 至 $2 筆,共 $3 筆'],
    [/^Total (\d+) items?$/, '共 $1 筆'],
    [/^Page (\d+) of (\d+)$/, '第 $1 頁,共 $2 頁'],
    [/^(\d+) \/ page$/, '$1 筆/頁'],
    [/^Showing (\d+) of (\d+) results?$/, '顯示 $1 筆,共 $2 筆'],
    [/^(\d+) selected$/, '已選 $1 筆'],
    [/^Copied!?$/, '已複製'],
    [/^(\d+) models?$/, '$1 個模型'],
    [/^(\d+) members?$/, '$1 位成員'],
    [/^(\d+) keys?$/, '$1 把金鑰'],
    [/^(\d+) rows?$/, '$1 列'],
    [/^(\d+) results?$/, '$1 筆結果'],
    [/^(\d+) teams?$/, '$1 個團隊'],
    [/^(\d+) users?$/, '$1 位使用者'],
    [/^(\d+) organizations?$/, '$1 個組織'],
    [/^(\d+) items?$/, '$1 筆']
  ];
  var ATTRS = ['placeholder', 'title', 'aria-label', 'alt'];
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, CODE: 1, PRE: 1, KBD: 1, SAMP: 1 };

  function tr(raw) {
    if (!raw) return null;
    var key = raw.replace(/\s+/g, ' ').trim();
    if (!key || key.length > 300) return null;
    var hit = DICT[key];
    if (hit !== undefined) return hit;
    for (var i = 0; i < RULES.length; i++) {
      if (RULES[i][0].test(key)) return key.replace(RULES[i][0], RULES[i][1]);
    }
    return null;
  }

  function processText(node) {
    var p = node.parentElement;
    if (p && (SKIP_TAGS[p.tagName] || p.isContentEditable)) return;
    var v = tr(node.nodeValue);
    if (v != null && v !== node.nodeValue) node.nodeValue = v;
  }

  function processElement(el) {
    if (SKIP_TAGS[el.tagName]) return;
    for (var i = 0; i < ATTRS.length; i++) {
      var a = ATTRS[i];
      if (el.hasAttribute && el.hasAttribute(a)) {
        var val = el.getAttribute(a);
        var v = tr(val);
        if (v != null && v !== val) el.setAttribute(a, v);
      }
    }
    if (el.tagName === 'INPUT' && (el.type === 'submit' || el.type === 'button') && el.value) {
      var v2 = tr(el.value);
      if (v2 != null && v2 !== el.value) el.value = v2;
    }
  }

  function walk(root) {
    if (!root) return;
    if (root.nodeType === 3) { processText(root); return; }
    if (root.nodeType !== 1 && root.nodeType !== 9 && root.nodeType !== 11) return;
    if (root.nodeType === 1) {
      if (SKIP_TAGS[root.tagName] || root.isContentEditable) return;
      processElement(root);
    }
    var w = document.createTreeWalker(root, 5, {
      acceptNode: function (n) {
        if (n.nodeType === 1) {
          return (SKIP_TAGS[n.tagName] || n.isContentEditable) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var n;
    while ((n = w.nextNode())) {
      if (n.nodeType === 3) processText(n); else processElement(n);
    }
  }

  var mo = new MutationObserver(function (muts) {
    for (var i = 0; i < muts.length; i++) {
      var m = muts[i];
      if (m.type === 'characterData') {
        processText(m.target);
      } else if (m.type === 'attributes') {
        if (m.target.nodeType === 1) processElement(m.target);
      } else {
        for (var j = 0; j < m.addedNodes.length; j++) walk(m.addedNodes[j]);
      }
    }
  });

  function start() {
    walk(document.documentElement);
    var t = tr(document.title);
    if (t) document.title = t;
    mo.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ATTRS
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
```

### `zhtw/patch_ui.py`

```python
"""Build-time patcher: inline zh-TW translator into every UI HTML + patch legacy login form.

Runs INSIDE the litellm docker image (see Dockerfile).
"""
import json
import pathlib

import litellm

PKG = pathlib.Path(litellm.__file__).parent
OUT = PKG / "proxy" / "_experimental" / "out"
HERE = pathlib.Path(__file__).parent

# --- 1) inline translator into all exported HTML files ---
dict_data = json.loads((HERE / "dict.json").read_text(encoding="utf-8"))
inject = (HERE / "inject.js").read_text(encoding="utf-8")
payload = json.dumps(dict_data, ensure_ascii=False, separators=(",", ":"))
js = inject.replace("__ZHTW_DICT__", payload)
# never emit a literal "</" inside the inline <script> (would close it early);
# "<\/" is identical to "</" inside JS/JSON strings
js = js.replace("</", "<\\/")
snippet = '<script id="zhtw-i18n">' + js + "</script>"

count = 0
for f in OUT.rglob("*.html"):
    s = f.read_text(encoding="utf-8")
    if "zhtw-i18n" in s:
        continue
    s = s.replace('<html lang="en"', '<html lang="zh-Hant"')
    if "</body>" in s:
        s = s.replace("</body>", snippet + "</body>", 1)
    else:
        s += snippet
    f.write_text(s, encoding="utf-8")
    count += 1
print(f"zhtw: patched {count} html files, dict entries = {len(dict_data)}")
assert count > 0, "no html files patched — UI path changed?"

# --- 2) legacy python-rendered login form ---
login_py = PKG / "proxy" / "common_utils" / "html_forms" / "ui_login.py"
if login_py.exists():
    s = login_py.read_text(encoding="utf-8")
    for a, b in [
        ('<html lang="en">', '<html lang="zh-Hant">'),
        ("<title>LiteLLM Login</title>", "<title>LiteLLM 登入</title>"),
        ("<h2>Login</h2>", "<h2>登入</h2>"),
        ("Access your LiteLLM Admin UI.", "登入 LiteLLM 管理介面。"),
        (">Default Credentials", ">預設登入資訊"),
        (
            "By default, Username is <code>admin</code> and Password is your set LiteLLM Proxy <code>MASTER_KEY</code>.",
            "預設帳號為 <code>admin</code>,密碼為您設定的 LiteLLM Proxy <code>MASTER_KEY</code>。",
        ),
        (
            'Need to set UI credentials or SSO? <a href="https://docs.litellm.ai/docs/proxy/ui" target="_blank">Check the documentation</a>.',
            '需要設定 UI 帳密或 SSO?請<a href="https://docs.litellm.ai/docs/proxy/ui" target="_blank">參閱文件</a>。',
        ),
        (">Username<", ">帳號<"),
        (">Password<", ">密碼<"),
        ('placeholder="Enter your username"', 'placeholder="請輸入帳號"'),
        ('placeholder="Enter your password"', 'placeholder="請輸入密碼"'),
        (">Show password<", ">顯示密碼<"),
        ('value="Login"', 'value="登入"'),
    ]:
        s = s.replace(a, b)
    login_py.write_text(s, encoding="utf-8")
    print("zhtw: patched legacy login form")
```

### `zhtw/dict.json`(格式範例,完整版由萃取+翻譯產生)

```json
{
"Virtual Keys": "虛擬金鑰",
"Teams": "團隊",
"Usage": "用量",
"Logs": "紀錄",
"Models": "模型",
"Spend": "花費",
"Budget": "預算",
"+ Create New Key": "+ 建立新金鑰",
"(Learn More)": "(了解更多)",
"(opens in a new tab)": "(在新分頁開啟)"
}
```

---

## FAQ

**Q:改了字典後畫面沒變?**
先 `docker compose build && docker compose up -d`,再 `Ctrl + F5` 清快取。瀏覽器快取是最常見的原因。

**Q:會拖慢系統嗎?**
不會有可感知的影響。翻譯發生在你自己的瀏覽器裡,查字典是瞬間完成的,伺服器端(API 本體)完全沒被更動。

**Q:API 回覆的內容也會被翻譯嗎?**
不會。這套機制**只翻管理介面的畫面文字**,模型回答與 API 資料完全不受影響。

**Q:萬一整個中文化壞掉怎麼辦?**
最壞情況就是介面變回英文、功能一切正常;因為從未修改 LiteLLM 本體,把 Dockerfile 換回官方 image 即可完全還原。

**Q:能翻成簡體 / 日文 / 其他語言嗎?**
可以。只換 `dict.json` 的內容(以及 `RULES` 的句型),其他檔案不用動。

---

*本文分享的是方法本身,程式碼可自由取用、修改。有問題歡迎在討論串交流!* 🙌
