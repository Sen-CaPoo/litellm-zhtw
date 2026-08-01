# LiteLLM Admin UI 国际化

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

![LiteLLM version](https://img.shields.io/badge/LiteLLM-v1.94.0-5b5bd6)
![UI languages](https://img.shields.io/badge/UI_languages-5-0f766e)
![License](https://img.shields.io/badge/license-MIT-blue)

无需维护 LiteLLM 的分支，即可为 LiteLLM Admin UI 添加五种语言。
在 Docker 镜像构建期间，本项目会将选定的 JSON 字典和一个小型浏览器端翻译器嵌入 LiteLLM 导出的 UI 页面。字典中未包含的字符串会保持英文，因此在持续添加新翻译时，升级 LiteLLM 后仍可正常使用。

> 本仓库仅翻译 Admin UI，不翻译 API 请求、模型响应、日志或供应商内容。

## 支持的语言

| 构建值 | UI 语言 | 字典 | HTML `lang` |
|---|---|---|---|
| `en` | 英文（原文） | [`dict.en.json`](zhtw/dict.en.json) | `en` |
| `ja` | 日文 | [`dict.ja.json`](zhtw/dict.ja.json) | `ja` |
| `ko` | 韩文 | [`dict.ko.json`](zhtw/dict.ko.json) | `ko` |
| `zh-CN` | 简体中文 | [`dict.zh-CN.json`](zhtw/dict.zh-CN.json) | `zh-Hans` |
| `zh-TW` | 繁体中文（默认） | [`dict.json`](zhtw/dict.json) | `zh-Hant` |

每个字典都包含相同的 4,599 个源键。为兼容本项目较早的发布版本，`dict.json` 仍使用繁体中文文件名。

## 快速开始

### 构建本地化 LiteLLM 镜像

```bash
git clone https://github.com/Sen-CaPoo/litellm-zhtw.git
cd litellm-zhtw
docker build --build-arg LITELLM_UI_LANG=ja -t litellm-i18n:ja .
```

将 `ja` 替换为 `en`、`ko`、`zh-CN` 或 `zh-TW`。可在当前使用官方 LiteLLM 镜像的任何位置使用生成的镜像；现有的 LiteLLM 命令、配置、数据库和环境变量均可保持不变。

本仓库当前将基础镜像固定为 `ghcr.io/berriai/litellm:v1.94.0`。如需使用其他 LiteLLM 版本，只需修改 [`Dockerfile`](Dockerfile) 中的 `FROM` 行，然后重新构建并检查 Admin UI。

### 使用附带的 Docker Compose 示例

附带的堆栈是为 PostgreSQL 和 Ollama Cloud 配置的示例。在将其用作生产部署前，请查看 [`config/config.yaml`](config/config.yaml)，并替换为自己的模型和供应商设置。

```bash
# macOS / Linux
cp .env.example .env

# Windows PowerShell
Copy-Item .env.example .env
```

编辑 `.env`，设置 `LITELLM_UI_LANG` 和所有占位密钥，然后运行：

```bash
docker compose up -d --build
docker compose logs -f litellm
```

打开 <http://localhost:4000/ui>。更改语言或字典后，请重新构建 `litellm` 服务并在浏览器中强制刷新：

```bash
docker compose build litellm
docker compose up -d litellm
```

> 隐私说明：附带的 [`config/config.yaml`](config/config.yaml) 启用了 `store_prompts_in_spend_logs`。如果不得在 LiteLLM 数据库中存储提示词和模型响应，请将其禁用。

## 将此翻译层添加到另一个 LiteLLM 项目

将 [`zhtw/`](zhtw/) 目录复制到项目中，并在扩展 LiteLLM 的 Dockerfile 中添加以下行：

```dockerfile
FROM ghcr.io/berriai/litellm:<your-version>

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
```

使用所需语言构建：

```bash
docker build --build-arg LITELLM_UI_LANG=ko -t my-litellm:ko .
```

`LITELLM_UI_LANG` 是构建时选项。在运行中的容器上更改它不会切换 UI；请重新构建镜像。不受支持的值会有意使构建失败，并输出五个可接受的值。

## 工作原理

1. [`patch_ui.py`](zhtw/patch_ui.py) 在镜像构建期间根据 `LITELLM_UI_LANG` 选择一个字典。
2. 它会将字典和 [`inject.js`](zhtw/inject.js) 嵌入每个导出的 LiteLLM UI HTML 文件，并设置页面语言。
3. 在浏览器中，会翻译完全匹配的文本和常见属性。`MutationObserver` 还会处理稍后渲染的 UI 内容。
4. `Page 2 of 5` 等动态计数使用存储在同一字典文件中的特定语言模板。

如果未找到 LiteLLM UI HTML 文件，构建会停止。这会让上游目录变更在升级时显现，而不会悄然生成未翻译的镜像。

## 仓库结构

| 路径 | 用途 |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | 繁体中文字典和向后兼容的默认值 |
| [`zhtw/dict.*.json`](zhtw/) | 英文、日文、韩文和简体中文字典 |
| [`zhtw/inject.js`](zhtw/inject.js) | 共享的浏览器端翻译引擎 |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | 构建时语言选择与 UI 修补程序 |
| [`Dockerfile`](Dockerfile) | 本地化镜像构建 |
| [`docker-compose.yml`](docker-compose.yml) | 可选的 LiteLLM + PostgreSQL 示例 |
| [`.env.example`](.env.example) | 构建语言和示例运行时变量 |

## 更新翻译

字典键是 LiteLLM 输出的精确英文字符串；仅编辑值：

```json
{
  "Save": "保存",
  "Cancel": "取消"
}
```

请保持 `$1` 等占位符、URL、HTML 标签、模型名称和代码片段不变。五个字典都必须保持相同的键及键顺序。重新构建前请先运行验证，然后检查受影响的页面：

```bash
python scripts/validate_i18n.py
```

当前字典面向 LiteLLM `v1.94.0` 附带的 UI。较新的 LiteLLM 版本可能引入新的英文字符串；在将其键添加到每个字典前，这些字符串会保持英文。

## 故障排除

- **UI 仍为之前的语言：**重新构建镜像、重新创建容器，然后在浏览器中强制刷新。
- **只有部分文本被翻译：**确认所选字典中存在作为键的精确英文文本。超过 300 个字符的文本，以及代码、预格式化、文本区域或可编辑元素内的内容会被有意跳过。
- **构建提示 `no html files patched`：**所选 LiteLLM 版本移动了其导出的 UI 目录。仅在该 LiteLLM 镜像中确认新路径后，再更新 `patch_ui.py` 中的 `OUT`。
- **构建拒绝语言：**请严格使用 `en`、`ja`、`ko`、`zh-CN` 或 `zh-TW`。字母大小写和 `_`/`-` 差异会被标准化。

## 参与贡献

欢迎提交关于缺失字符串、术语改进和支持较新 LiteLLM 版本的 Issue 与 Pull Request。视觉上下文很重要时，请附上 LiteLLM 版本、页面名称、精确英文源文本、目标语言和截图。

LiteLLM 由 [LiteLLM 项目](https://github.com/BerriAI/litellm) 维护。
此翻译层以 [MIT 许可证](LICENSE) 发布。
