# AI agent guide: install or upgrade litellm-zhtw

You are an AI agent with shell and file access. A user pointed you here so you can install, upgrade,
or add the localized Admin UI to their LiteLLM gateway. Follow this guide from top to bottom.
Talk to the user in their language. If you cannot run commands (chat-only), walk the user
through the same steps one command at a time and ask them to paste the output back.

Repository: <https://github.com/Sen-CaPoo/litellm-zhtw> · Raw files:
`https://raw.githubusercontent.com/Sen-CaPoo/litellm-zhtw/main/<path>`

```text
Detect scenario ─┬─ A. Fresh install      → clone → .env + config → build → verify
                 ├─ B. Upgrade this repo  → release notes → DB backup → pull → build → verify
                 └─ C. Own LiteLLM setup  → copy zhtw/ → Dockerfile → build → verify
```

## 0. Ground rules

1. Explain your plan and ask the questions in each scenario **before** changing anything.
2. Report the result of every step. Stop and ask when output differs from what this guide expects.
3. Never do these without the user's explicit request:
   - `docker compose down -v`, `docker volume rm`, or anything that deletes the database or Redis volume.
   - Overwrite an existing `.env`, `config/config.yaml` or `docker-compose.override.yml`.
   - Change `LITELLM_SALT_KEY` after virtual keys exist. It encrypts stored keys and cannot be rotated in place.
   - Rename or move an existing deployment folder. Compose names volumes after the project, so a
     new name starts with an empty database. (`COMPOSE_PROJECT_NAME` in `.env` pins the name.)
   - Restore a database backup, or publish port 4000 to the internet.
4. Secrets: generate them locally, write them only into `.env`, and never print them in chat,
   logs or commits. Tell the user *where* a secret is stored, not its value. If the user prefers,
   let them paste provider API keys into `.env` themselves.
5. Always pin image versions. Never use `latest`, `main-latest` or `main-stable`.
6. Commands below use bash (Linux, macOS, Git Bash on Windows). In PowerShell use the equivalent
   cmdlets (`Copy-Item`, `Select-String`) and do not redirect database dumps with `>` (it re-encodes them).

## 1. Detect the scenario

```bash
docker version && docker compose version && git --version
docker ps --format "{{.Names}}\t{{.Image}}\t{{.Status}}"
```

| What you find | Scenario |
|---|---|
| No LiteLLM container, user wants a new gateway | **A. Fresh install** |
| A folder whose `git remote -v` is `Sen-CaPoo/litellm-zhtw`, running `litellm-i18n:*` | **B. Upgrade** |
| LiteLLM running from the official `ghcr.io/berriai/litellm*` image in the user's own project | **C. Add the translation layer** |

Confirm the scenario with the user. Also ask for the folder to use and the UI language:
`en`, `ja`, `ko`, `zh-CN` or `zh-TW` (default `zh-TW`).

## 2. Scenario A: fresh install

**Requirements:** Docker Engine with Compose v2 running, about 6 GB of free disk, port 4000 free.

**Ask the user:**
- Which model providers and models to offer, and their API keys. The example config uses Ollama Cloud.
- Whether prompts and responses may be stored in the database. The example enables `store_prompts_in_spend_logs`.
- The Admin UI username.

**Steps:**

1. Clone and enter the folder:
   ```bash
   git clone https://github.com/Sen-CaPoo/litellm-zhtw.git <folder> && cd <folder>
   ```
2. Create the private files only if they do not exist yet:
   ```bash
   [ -f .env ] || cp .env.example .env
   [ -f config/config.yaml ] || cp config/config.example.yaml config/config.yaml
   ```
3. Fill in `.env`:
   - `LITELLM_UI_LANG`: the chosen language.
   - `LITELLM_MASTER_KEY`: `sk-` followed by a random value, e.g. `python -c "import secrets;print('sk-'+secrets.token_hex(24))"`.
   - `LITELLM_SALT_KEY`, `UI_PASSWORD`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`: random values, e.g.
     `python -c "import secrets;print(secrets.token_hex(24))"`. Hex avoids characters that break `.env` or URLs.
   - `UI_USERNAME`, provider keys (`OLLAMA_API_KEY` or the variables your config references).
   - Recommended: add `COMPOSE_PROJECT_NAME=litellm` so volume names survive a folder rename.
4. Edit `config/config.yaml`:
   - Replace `model_list` with the user's models. Each entry needs `model_name`, `litellm_params.model`
     (`<provider>/<model>`) and `api_key: os.environ/<VAR>`; add every `<VAR>` to `.env`.
   - The example's model list may be outdated. Check model names with the provider (Ollama Cloud: `curl -s https://ollama.com/v1/models`)
     and remove models that no longer exist.
   - Keep `litellm_settings.callbacks: custom_callbacks.unique_request_id` and `general_settings.coordination_redis`.
   - Set `store_prompts_in_spend_logs: false` if the user does not want prompts stored.
5. Build and start:
   ```bash
   docker compose up -d --build
   ```
   The build log **must** contain `i18n: language=<lang>, patched N html files` with N > 0. Otherwise stop.
6. Wait until `docker compose ps` shows `litellm` as `(healthy)`. The first start runs database migrations and can take a few minutes.
7. Run the checks in [section 5](#5-verify).

## 3. Scenario B: upgrade an existing deployment

1. Inspect the deployment folder:
   ```bash
   cd <deployment folder>
   git remote -v            # must point to Sen-CaPoo/litellm-zhtw
   git status --short       # tracked changes? show them and ask; never stash or discard silently
   git rev-parse --short HEAD && head -1 Dockerfile     # write these down for rollback
   ```
   `.env`, `config/config.yaml` and `docker-compose.override.yml` are git-ignored, so `git pull` does not touch them.
2. See what is new:
   ```bash
   git fetch origin --tags
   git log --oneline HEAD..origin/main
   git show origin/main:Dockerfile | head -1             # target LiteLLM version
   ```
   Read this repo's [releases](https://github.com/Sen-CaPoo/litellm-zhtw/releases) and the
   [LiteLLM releases](https://github.com/BerriAI/litellm/releases) for **every** version between the current and the target one.
   Look for "Action required", breaking changes (`!:`), removed features and database migrations.
   Summarize them for the user and wait for a go-ahead. If nothing is new, stop here.
3. Check free disk space. You need about twice the database size plus 3 GB:
   ```bash
   docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select pg_size_pretty(pg_database_size(current_database()))"'
   ```
4. Back up the database. The dump contains virtual keys and prompts, so keep it private (`*.sql` and `backup_*` are git-ignored):
   ```bash
   B=backup_pre_<target-version>_$(date +%Y%m%d).sql
   docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/backup.sql'
   docker compose cp db:/tmp/backup.sql "./$B" && docker compose exec -T db sh -c 'rm /tmp/backup.sql'
   tail -n 5 "$B" | grep -q "PostgreSQL database dump complete" && ls -lh "$B"
   ```
   Do not continue unless the last command prints the file.
5. Update the code:
   ```bash
   git pull --ff-only origin main        # or: git checkout <release tag>
   git diff <old commit>..HEAD -- .env.example config/config.example.yaml docker-compose.yml
   ```
   If new variables or settings appear, propose adding them to the user's `.env` / `config/config.yaml`. Do not overwrite those files.
6. Rebuild and restart only the gateway. Migrations run automatically at startup:
   ```bash
   docker compose build litellm
   docker compose up -d litellm
   ```
7. Wait for `(healthy)`, then check the logs:
   ```bash
   docker compose logs --since 10m litellm | grep -iE "error|exception|migration"
   ```
8. Run the checks in [section 5](#5-verify). If the gateway does not become healthy or requests fail, follow [section 6](#6-roll-back-an-upgrade).

## 4. Scenario C: add the translation layer to your own LiteLLM

1. Find how LiteLLM starts (Compose file or `docker run`) and its exact image tag (`docker ps`).
   If the tag is not a fixed version, ask the user which version to pin.
2. Copy the files you will change to `*.bak` (Dockerfile, Compose file).
3. Copy the [`zhtw/`](zhtw/) folder (7 files: 5 `dict*.json`, `inject.js`, `patch_ui.py`) into the project,
   e.g. `git clone --depth 1 https://github.com/Sen-CaPoo/litellm-zhtw.git /tmp/litellm-zhtw && cp -r /tmp/litellm-zhtw/zhtw .`
4. Create or extend the Dockerfile. Keep the user's image variant (`litellm`, `litellm-database`, …) and version:
   ```dockerfile
   FROM ghcr.io/berriai/litellm:<pinned-version>

   ARG LITELLM_UI_LANG=zh-TW
   COPY zhtw/ /zhtw/
   RUN LITELLM_UI_LANG="$LITELLM_UI_LANG" python /zhtw/patch_ui.py && rm -rf /zhtw
   ```
   On a non-root variant, if the build fails with a permission error, add `USER root` before `RUN`
   and restore the original `USER` after it.
5. Point the service at the new image and change nothing else:
   - Compose: replace `image: ghcr.io/berriai/litellm:…` with
     `build: { context: ., args: { LITELLM_UI_LANG: <lang> } }` and `image: litellm-i18n:<version>-<lang>`.
     Then run `docker compose build <service> && docker compose up -d <service>`.
   - `docker run`: `docker build --build-arg LITELLM_UI_LANG=<lang> -t litellm-i18n:<version>-<lang> .`,
     then recreate the container with the same options and the new image.
6. Run the checks in [section 5](#5-verify). The dictionaries target the LiteLLM version pinned in this repo's
   [`Dockerfile`](Dockerfile). Other versions work, but strings that are not in the dictionary stay in English.

## 5. Verify

```bash
docker compose exec litellm python -c "import importlib.metadata as m; print(m.version('litellm'))"   # = pinned version
curl -s http://localhost:4000/health/liveliness                         # "I'm alive!"
curl -s http://localhost:4000/health/readiness                          # "db":"connected"
curl -sL http://localhost:4000/ui/ | grep -c 'id="litellm-i18n"'        # 1
curl -sL http://localhost:4000/ui/ | grep -o '<html lang="[^"]*"'       # zh-Hant / zh-Hans / ja / ko / en
```

Send one real request (costs a few tokens). Read the master key without printing it:

```bash
MK=$(grep '^LITELLM_MASTER_KEY=' .env | cut -d= -f2-)
curl -s http://localhost:4000/v1/chat/completions -H "Authorization: Bearer $MK" -H "Content-Type: application/json" \
  -d '{"model":"<a model_name from config.yaml>","messages":[{"role":"user","content":"Reply with: pong"}],"max_tokens":20}'
```

Then ask the user to open <http://localhost:4000/ui>, sign in with `UI_USERNAME` / `UI_PASSWORD` from `.env`,
and hard-refresh the page (Ctrl+F5, or Cmd+Shift+R on macOS).

## 6. Roll back an upgrade

1. `git checkout <old commit>` (from step B1). The previous image `litellm-i18n:<old-version>-<lang>` is still
   local, so `docker compose up -d litellm` starts it again. If it is missing, run `docker compose build litellm` first.
2. LiteLLM migrations are forward-only and almost always additive, so the old version usually starts on the upgraded database.
3. Restore the backup **only** if the old version cannot start and the user agrees. This replaces all data written since the backup:
   ```bash
   docker compose stop litellm
   docker compose exec -T db sh -c 'dropdb --force -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB"'
   docker compose exec -T db sh -c 'psql -q -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < backup_pre_<version>_<date>.sql
   docker compose up -d litellm
   ```

## 7. Final report

Tell the user:
- Scenario, LiteLLM version before and after, UI language, and the result of each check in section 5.
- Admin UI URL, and that the login and master key are in `.env` (not their values).
- The backup file path (upgrade), plus any "Action required" items or new settings they still need to apply.
- How to switch language later: change `LITELLM_UI_LANG` in `.env`, run `docker compose build litellm && docker compose up -d litellm`, then hard-refresh.
- How to upgrade later: give an AI agent this guide again.
- `docker compose down` stops the stack and keeps the data. Removing volumes deletes all data.
