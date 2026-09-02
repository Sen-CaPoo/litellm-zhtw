# LiteLLM Admin UI 다국어화

[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md)

![LiteLLM version](https://img.shields.io/badge/LiteLLM-v1.99.1-5b5bd6)
![UI languages](https://img.shields.io/badge/UI_languages-5-0f766e)
![License](https://img.shields.io/badge/license-MIT-blue)

LiteLLM을 포크하지 않고 LiteLLM Admin UI에 5개 언어를 추가합니다.
Docker 이미지 빌드 중 이 프로젝트는 선택한 JSON 사전 하나와 소규모 브라우저 측 번역기를
LiteLLM의 내보낸 UI 페이지에 삽입합니다. 사전에 없는 문자열은 영어로 유지되므로, 새 번역을
추가하는 동안에도 LiteLLM을 업그레이드한 뒤 계속 사용할 수 있습니다.

> 이 저장소는 Admin UI만 번역합니다. API 요청, 모델 응답, 로그 또는 제공업체 콘텐츠는 번역하지 않습니다.

## 지원 언어

| 빌드 값 | UI 언어 | 사전 | HTML `lang` |
|---|---|---|---|
| `en` | 영어(원본) | [`dict.en.json`](zhtw/dict.en.json) | `en` |
| `ja` | 일본어 | [`dict.ja.json`](zhtw/dict.ja.json) | `ja` |
| `ko` | 한국어 | [`dict.ko.json`](zhtw/dict.ko.json) | `ko` |
| `zh-CN` | 중국어 간체 | [`dict.zh-CN.json`](zhtw/dict.zh-CN.json) | `zh-Hans` |
| `zh-TW` | 중국어 번체(기본값) | [`dict.json`](zhtw/dict.json) | `zh-Hant` |

각 사전에는 동일한 5,060개의 원본 키가 있습니다. `dict.json`은 이 프로젝트의 이전 릴리스와의
호환성을 위해 중국어 번체 파일명으로 유지됩니다.

## 빠른 시작

### 현지화된 LiteLLM 이미지 빌드

```bash
git clone https://github.com/Sen-CaPoo/litellm-zhtw.git
cd litellm-zhtw
docker build --build-arg LITELLM_UI_LANG=ja -t litellm-i18n:ja .
```

`ja`를 `en`, `ko`, `zh-CN` 또는 `zh-TW`로 바꾸세요. 현재 공식 LiteLLM 이미지를 사용하는 곳에
결과 이미지를 사용하면 됩니다. 기존 LiteLLM 명령, 구성, 데이터베이스 및 환경 변수는 그대로 유지할 수 있습니다.

이 저장소는 현재 기본 이미지를 `ghcr.io/berriai/litellm:v1.99.1`으로 고정합니다.
다른 LiteLLM 릴리스를 사용하려면 [`Dockerfile`](Dockerfile)의 `FROM` 줄만 변경한 뒤,
다시 빌드하고 Admin UI를 확인하세요.

### 포함된 Docker Compose 예제 사용

포함된 스택은 PostgreSQL 및 Ollama Cloud용으로 구성된 예제입니다. 프로덕션 배포로 사용하기 전에
[`config/config.example.yaml`](config/config.example.yaml)을 검토하고 모델/제공업체 설정을 자체 설정으로 바꾸세요.

```bash
# macOS / Linux
cp .env.example .env
cp config/config.example.yaml config/config.yaml

# Windows PowerShell
Copy-Item .env.example .env
Copy-Item config/config.example.yaml config/config.yaml
```

`.env`를 편집하여 `LITELLM_UI_LANG` 및 모든 자리표시자 시크릿을 설정한 다음 실행하세요.

```bash
docker compose up -d --build
docker compose logs -f litellm
```

<http://localhost:4000/ui>를 여세요. 언어 또는 사전을 변경한 후에는 `litellm` 서비스를 다시 빌드하고
브라우저를 강력 새로고침하세요.

```bash
docker compose build litellm
docker compose up -d litellm
```

> 개인정보 보호 참고: 포함된 [`config/config.example.yaml`](config/config.example.yaml)은
> `store_prompts_in_spend_logs`를 활성화합니다. 프롬프트와 모델 응답을 LiteLLM 데이터베이스에
> 저장하면 안 되는 경우 비활성화하세요.

## 이 번역 계층을 다른 LiteLLM 프로젝트에 추가

[`zhtw/`](zhtw/) 디렉터리를 프로젝트에 복사하고 LiteLLM을 확장하는 Dockerfile에 다음 줄을 추가하세요.

```dockerfile
FROM ghcr.io/berriai/litellm:<your-version>

ARG LITELLM_UI_LANG=zh-TW
COPY zhtw/ /zhtw/
RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
```

원하는 언어로 빌드합니다.

```bash
docker build --build-arg LITELLM_UI_LANG=ko -t my-litellm:ko .
```

`LITELLM_UI_LANG`는 빌드 시 옵션입니다. 실행 중인 컨테이너에서 이를 변경해도 UI는 전환되지 않으므로
대신 이미지를 다시 빌드하세요. 지원하지 않는 값은 의도적으로 빌드를 실패시키고 허용되는 5개 값을 출력합니다.

## 작동 방식

1. [`patch_ui.py`](zhtw/patch_ui.py)가 이미지 빌드 중 `LITELLM_UI_LANG`에서 사전 하나를 선택합니다.
2. 사전과 [`inject.js`](zhtw/inject.js)를 내보낸 모든 LiteLLM UI HTML 파일에 삽입하고 페이지 언어를 설정합니다.
3. 브라우저에서 정확히 일치하는 텍스트와 일반적인 속성을 번역합니다. `MutationObserver`는 나중에 렌더링되는 UI 콘텐츠도 처리합니다.
4. `Page 2 of 5`와 같은 동적 개수는 동일한 사전 파일에 저장된 언어별 템플릿을 사용합니다.

LiteLLM UI HTML 파일을 찾지 못하면 빌드가 중단됩니다. 따라서 업그레이드 중 업스트림 디렉터리가 변경되면
번역되지 않은 이미지를 조용히 생성하는 대신 변경 사실을 확인할 수 있습니다.

## 저장소 구성

| 경로 | 용도 |
|---|---|
| [`zhtw/dict.json`](zhtw/dict.json) | 중국어 번체 사전 및 하위 호환 기본값 |
| [`zhtw/dict.*.json`](zhtw/) | 영어, 일본어, 한국어 및 중국어 간체 사전 |
| [`zhtw/inject.js`](zhtw/inject.js) | 공용 브라우저 측 번역 엔진 |
| [`zhtw/patch_ui.py`](zhtw/patch_ui.py) | 빌드 시 언어 선택 및 UI 패처 |
| [`Dockerfile`](Dockerfile) | 현지화 이미지 빌드 |
| [`docker-compose.yml`](docker-compose.yml) | 선택 사항인 LiteLLM + PostgreSQL + Redis 예제 |
| [`config/config.example.yaml`](config/config.example.yaml) | 프록시 설정 예제. `config/config.yaml`로 복사해 사용 |
| [`config/custom_callbacks.py`](config/custom_callbacks.py) | 상위 응답 id의 낮은 엔트로피 값을 고유 값으로 바꿔 지출 로그가 조용히 삭제되는 것을 방지 |
| [`.env.example`](.env.example) | 빌드 언어 및 런타임 변수 예제 |

## 번역 업데이트

사전 키는 LiteLLM이 출력하는 정확한 영어 문자열입니다. 값만 편집하세요.

```json
{
  "Save": "저장",
  "Cancel": "취소"
}
```

`$1` 같은 자리표시자, URL, HTML 태그, 모델 이름 및 코드 조각은 변경하지 마세요. 5개 사전은 모두
같은 키와 키 순서를 유지해야 합니다. 다시 빌드하기 전에 검증을 실행한 다음 영향을 받는 화면을 확인하세요.

```bash
python scripts/validate_i18n.py
```

현재 사전은 LiteLLM `v1.99.1`에 번들된 UI를 대상으로 합니다. 이후 LiteLLM 버전에는 새 영어 문자열이
추가될 수 있으며, 해당 키가 모든 사전에 추가될 때까지는 영어로 유지됩니다.

## 문제 해결

- **UI가 이전 언어로 표시됩니다:** 이미지를 다시 빌드하고 컨테이너를 다시 생성한 뒤 브라우저를 강력 새로고침하세요.
- **일부 텍스트만 번역됩니다:** 선택한 사전에 정확한 영어 텍스트가 키로 있는지 확인하세요. 300자를 초과하는 텍스트와 코드, 서식이 지정된 텍스트, 텍스트 영역 또는 편집 가능한 요소 내부의 콘텐츠는 의도적으로 건너뜁니다.
- **빌드에 `no html files patched`가 표시됩니다:** 선택한 LiteLLM 버전에서 내보낸 UI 디렉터리가 이동했습니다. 해당 LiteLLM 이미지에서 새 경로를 확인한 후에만 `patch_ui.py`의 `OUT`을 업데이트하세요.
- **빌드가 언어를 거부합니다:** 정확히 `en`, `ja`, `ko`, `zh-CN` 또는 `zh-TW`를 사용하세요. 대소문자와 `_`/`-` 차이는 정규화됩니다.

## 기여하기

누락된 문자열, 용어 개선 및 최신 LiteLLM 릴리스 지원에 관한 이슈와 풀 리퀘스트를 환영합니다. 시각적 맥락이 중요할 때는 LiteLLM 버전, 페이지 이름, 정확한 영어 원본 텍스트, 대상 언어 및 스크린샷을 포함해 주세요.

LiteLLM은 [LiteLLM 프로젝트](https://github.com/BerriAI/litellm)가 유지 관리합니다.
이 번역 계층은 [MIT 라이선스](LICENSE)에 따라 배포됩니다.
