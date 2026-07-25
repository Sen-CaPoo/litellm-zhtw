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
