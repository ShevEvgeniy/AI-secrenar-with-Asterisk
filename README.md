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

### Department transfer routing

Before live transfer, the ARI listener must have collected `name`, `city`, and `phone_digits`, and the phone must pass `PHONE_CONFIRM`.

The caller can ask for an immediate transfer early, but the dialog does not transfer until mandatory data is complete. The detected department is preserved and the active slot is collected with a bounded stage-aware prompt.

Routing contract:
- Sales default: `context=from-internal`, `extension=sales_real`, `priority=1`
- Accounting default: `context=from-internal`, `extension=accounting`, `priority=1`
- Delivery default: `context=from-internal`, `extension=delivery`, `priority=1`
- Per-department overrides: `DEPARTMENT_ROUTE_<DEPARTMENT>_CONTEXT`, `DEPARTMENT_ROUTE_<DEPARTMENT>_EXTEN`, `DEPARTMENT_ROUTE_<DEPARTMENT>_PRIORITY`
- Sales also honors legacy `TRANSFER_CONTEXT`, `TRANSFER_EXTEN`, and `TRANSFER_PRIORITY` when the new sales-specific vars are not set.

Intent rules are deterministic keyword matches:
- `sales`: buy/purchase/price/quote/new order/product/cylinder and Russian продаж/купить/цена/заказать/товар/баллон/цилиндр terms.
- `accounting`: accounting/billing/invoice/payment/receipt/documents/reconciliation and Russian бухгалтер/счет/счёт/оплат/платеж/документ/сверк terms.
- `delivery`: delivery/shipping/arrival/logistics/courier/tracking/order status and Russian достав/отгруз/логист/курьер/груз/трек/где заказ terms.

Transfer phrase/audio mapping:
- `sales`: `sound:ai_secretary/_system/transfer` — "Хорошо, я соединяю вас с отделом продаж."
- `accounting`: `sound:ai_secretary/_system/transfer_accounting` — "Хорошо, я соединяю вас с бухгалтерией."
- `delivery`: `sound:ai_secretary/_system/transfer_delivery` — "Хорошо, я соединяю вас с отделом доставки."

Unclear or tied intent now triggers a bounded clarification prompt: "Уточните, пожалуйста, отдел: продажи, бухгалтерия или доставка." The caller's answer must resolve to `sales`, `accounting`, or `delivery`; then the normal data collection flow continues.

Runtime events log `department_intent`, `transfer_phrase_resolved`, the resolved transfer target, early-transfer status, missing required fields, and clarification results before the `transfer` event.

Bounded retry policy:
- `ISSUE`: empty/silence retries up to 2 total, then moves to `INTENT_CLARIFY`.
- `INTENT_CLARIFY`: empty/silence/unclear retries up to 2 total, then resolves to `DEPARTMENT_INTENT_DEFAULT` and continues collection.
- `NAME`, `CITY`, `PHONE`: retry up to 3 total, then safe-finish without transfer.
- `PHONE_CONFIRM`: retry confirmation up to 2 total, then returns to `PHONE`; if phone collection still cannot complete, safe-finish applies.

Safe-finish is terminal and does not transfer. It logs `safe_finish_reason`, retry count/limit, and missing required fields, plays fallback media when available, and hangs up.

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
- `scripts\diag_publish_win.ps1` — диагностика SSH/SCP/Docker/ARI/events одним запуском

## Windows diagnostics

Запуск:

`powershell -ExecutionPolicy Bypass -File .\scripts\diag_publish_win.ps1 -CallId <id> -Verbose`

Скрипт печатает проверки в формате `[OK]/[FAIL]`, сохраняет логи в `tmp\diag` и завершаетcя с `exit 0` только при успешных ключевых проверках.

Временный dialplan-тест playback (для проверки, что Asterisk видит `ai_secretary/_system/prompt_1`):

```asterisk
; extensions_custom.conf (временный тест)
[from-internal-custom]
exten => 5999,1,NoOp(System prompt test)
 same => n,Answer()
 same => n,Playback(ai_secretary/_system/prompt_1)
 same => n,Hangup()
```

Применение на сервере:
- `asterisk -rx "dialplan reload"`
- позвонить на `5999` и убедиться, что звук воспроизводится.

## Windows scripts (.cmd)

- `scripts\check_env.cmd` — проверяет окружение (ARI/SSH/.venv). Читает `.env` из корня проекта.
- `scripts\run_ari.cmd` — запускает ARI listener. Читает `.env` из корня проекта.

**Stress Dictionary For TTS**
- Set `TTS_STRESS_DICT_PATH` in `.env` to a dictionary file with lines like `word=stressed_form`.
- Example file: `data/tts/stress_dict.example.txt`.
- After editing the dictionary, restart ARI listener so cache is reloaded.

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
