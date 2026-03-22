# AI Secretary with Asterisk

Проект для голосового AI-секретаря с опциональной интеграцией Asterisk ARI.

## Режимы работы

1) prototyping (без Asterisk)
- текстовый вход -> summary -> rag -> response -> tts

2) local-dev (API поднят)
- локальный API для отладки модулей и интеграций

3) production (Asterisk ARI)
- при подключении ARI обрабатываются реальные вызовы

## Установка через venv + pip

`python -m venv .venv`

`.venv\Scripts\activate`

`pip install -r requirements.txt`

`pip install -r requirements-dev.txt`

## Запуск pytest

`python -m pytest`

## Запуск demo

`DEMO_MODE=real python -m ai_secretary`

`DEMO_MODE=synth python -m ai_secretary`

## RAG

`KB_PATH=./data/kb/mikizol_by_category.md`

В artifacts сохраняются transcript/summary/response/response_for_tts.

## Run API

`.venv\Scripts\python -m ai_secretary.api.main`

`curl -X POST http://127.0.0.1:8000/demo/run -H "Content-Type: application/json" -d "{\"mode\":\"synth\"}"`

## Run ARI listener (debug)

`$env:ARI_URL="http://localhost:8088/ari"`

`$env:ARI_USER="asterisk"`

`$env:ARI_PASSWORD="asterisk"`

`$env:ARI_APP_NAME="ai_secretary"`

`$env:PYTHONPATH="src"`

`python -m ai_secretary.telephony.ari_app`

## Iteration 4.2 demo call

Env vars:
- `ARI_URL`
- `ARI_USER`
- `ARI_PASSWORD`
- `ARI_APP_NAME`
- `PLAY_TEST=1` (включает тестовый звук перед ответом)
- `ASTERISK_SSH_HOST`
- `ASTERISK_SSH_USER`
- `ASTERISK_SSH_KEY` (или `ASTERISK_SSH_PASSWORD`)
- `ASTERISK_SOUNDS_DIR`
- `ASTERISK_SOUNDS_SUBDIR`
- `ASTERISK_DOCKER_CONTAINER` (если Asterisk в контейнере)

Command:
`$env:PYTHONPATH="src"`
`python -m ai_secretary.telephony.ari_app`

Примечание: если ssh просит пароль — на сервере включен AuthenticationMethods publickey,password. Для автопубликации нужен key-only (AuthenticationMethods publickey).

## Docker Asterisk и sounds

Если Asterisk работает в Docker-контейнере, есть два варианта:
- volume mount `/var/lib/asterisk/sounds` с хоста внутрь контейнера
- или использовать `ASTERISK_DOCKER_CONTAINER` — тогда после `scp` выполняется `docker exec` и `docker cp` на хосте

WAV перед playback конвертируется в 8kHz mono PCM s16le (через `ffmpeg`).

## Логи чек-лист

Ожидаемые шаги:
- `RECORD_DONE`
- `DOWNLOAD_OK`
- `PUBLISH_OK`
- `PLAY_OK`

## Скрипты запуска (Windows)

- `scripts\run_ari.cmd` — запуск ARI listener (cmd)
- `scripts\check_env.cmd` — проверка окружения
- `scripts\preflight_win.ps1` — единый preflight (venv + .env + check_env + ssh key-only + Silero smoke, опционально pytest)

## Windows scripts (.cmd)

- `scripts\check_env.cmd` — проверяет окружение (ARI/SSH/.venv). Читает `.env` из корня проекта.
- `scripts\run_ari.cmd` — запускает ARI listener. Читает `.env` из корня проекта.

**Проверка окружения**
- Команда проверки: `scripts\check_env.cmd`
- Ожидаемый успешный вывод: строки `[OK] ...` и в конце `ALL_OK`
- Проверка exit code (cmd): `cmd /v:on /c "scripts\check_env.cmd & echo EXITCODE=!ERRORLEVEL!"`
- Проверка exit code (PowerShell): `cmd /c scripts\check_env.cmd; Write-Host "EXITCODE=$LASTEXITCODE"`
- Успех: `EXITCODE=0`
- Если `CHECKS FAILED` — смотреть ближайшую строку `[FAIL]`

Пример:

`scripts\check_env.cmd`

`scripts\run_ari.cmd`



