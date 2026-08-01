"""Build-time patcher: inline the selected UI translation into LiteLLM HTML.

Runs INSIDE the litellm docker image (see Dockerfile).
"""

import json
import os
import pathlib
import re

import litellm

PKG = pathlib.Path(litellm.__file__).parent
OUT = PKG / "proxy" / "_experimental" / "out"
HERE = pathlib.Path(__file__).parent

LANGUAGES = {
    "en": ("en", "dict.en.json"),
    "ja": ("ja", "dict.ja.json"),
    "ko": ("ko", "dict.ko.json"),
    "zh-cn": ("zh-Hans", "dict.zh-CN.json"),
    # Keep dict.json as the zh-TW filename for backward compatibility.
    "zh-tw": ("zh-Hant", "dict.json"),
}


def selected_language():
    requested = os.environ.get("LITELLM_UI_LANG", "zh-TW").strip()
    normalized = requested.replace("_", "-").lower()
    if normalized not in LANGUAGES:
        choices = ", ".join(("en", "ja", "ko", "zh-CN", "zh-TW"))
        raise ValueError(
            f"Unsupported LITELLM_UI_LANG={requested!r}. Choose one of: {choices}"
        )
    html_lang, filename = LANGUAGES[normalized]
    return requested, html_lang, HERE / filename


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate dictionary key: {key!r}")
        result[key] = value
    return result


language, html_lang, dict_path = selected_language()
dict_data = json.loads(
    dict_path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
)
if not isinstance(dict_data, dict) or not all(
    isinstance(key, str) and isinstance(value, str) for key, value in dict_data.items()
):
    raise TypeError(f"{dict_path.name} must be a JSON object containing string values")

# --- 1) inline translator into all exported HTML files ---
inject = (HERE / "inject.js").read_text(encoding="utf-8")
payload = json.dumps(dict_data, ensure_ascii=False, separators=(",", ":"))
js = inject.replace("__I18N_DICT__", payload)
js = js.replace("__I18N_HTML_LANG__", json.dumps(html_lang))
if "__I18N_" in js:
    raise ValueError("unresolved i18n placeholder in inject.js")
# never emit a literal "</" inside the inline <script> (would close it early);
# "<\/" is identical to "</" inside JS/JSON strings
js = js.replace("</", "<\\/")
snippet = '<script id="litellm-i18n">' + js + "</script>"

count = 0
for f in OUT.rglob("*.html"):
    s = f.read_text(encoding="utf-8")
    if "litellm-i18n" in s:
        continue
    s = re.sub(
        r'(<html\b[^>]*\blang=)(["\'])en\2',
        lambda match: f'{match.group(1)}"{html_lang}"',
        s,
        count=1,
        flags=re.IGNORECASE,
    )
    if "</body>" in s:
        s = s.replace("</body>", snippet + "</body>", 1)
    else:
        s += snippet
    f.write_text(s, encoding="utf-8")
    count += 1
print(
    f"i18n: language={language}, patched {count} html files, "
    f"dict entries={len(dict_data)}"
)
assert count > 0, "no html files patched — UI path changed?"

# --- 2) legacy python-rendered login form ---
login_py = PKG / "proxy" / "common_utils" / "html_forms" / "ui_login.py"
if login_py.exists():
    s = login_py.read_text(encoding="utf-8")
    s = s.replace('<html lang="en">', f'<html lang="{html_lang}">')

    def tr(source):
        return dict_data.get(source, source)

    for source, target in (
        ("<title>LiteLLM Login</title>", f"<title>{tr('LiteLLM Login')}</title>"),
        ("<h2>Login</h2>", f"<h2>{tr('Login')}</h2>"),
        ("Access your LiteLLM Admin UI.", tr("Access your LiteLLM Admin UI.")),
        ("Default Credentials", tr("Default Credentials")),
        (
            "By default, Username is <code>admin</code> and Password is your set LiteLLM Proxy <code>MASTER_KEY</code>.",
            tr(
                "By default, Username is <code>admin</code> and Password is your set LiteLLM Proxy <code>MASTER_KEY</code>."
            ),
        ),
        (
            'Need to set UI credentials or SSO? <a href="https://docs.litellm.ai/docs/proxy/ui" target="_blank">Check the documentation</a>.',
            tr(
                'Need to set UI credentials or SSO? <a href="https://docs.litellm.ai/docs/proxy/ui" target="_blank">Check the documentation</a>.'
            ),
        ),
        (">Username<", f">{tr('Username')}<"),
        (">Password<", f">{tr('Password')}<"),
        (
            'placeholder="Enter your username"',
            f'placeholder="{tr("Enter your username")}"',
        ),
        (
            'placeholder="Enter your password"',
            f'placeholder="{tr("Enter your password")}"',
        ),
        (">Show password<", f">{tr('Show password')}<"),
        ('value="Login"', f'value="{tr("Login")}"'),
    ):
        s = s.replace(source, target)
    login_py.write_text(s, encoding="utf-8")
    print(f"i18n: patched legacy login form ({language})")
