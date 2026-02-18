# Анализ legacy-ARI (Asya) и перенос в AI-secrenar-with-Asterisk

## 1) Найденные точки входа
- asya_server: `src/ari_bot/nemo_ari_app.py` — основной ARI-бот (WebSocket loop, запись/воспроизведение, основной диалог).
- asya_server: `src/main.py` — запуск FastAPI через `uvicorn`.
- asya_server: `src/api/main.py` — FastAPI app и роуты.
- asya_server: `scripts/start_service.sh` — запуск сервиса (FastAPI) в Linux.
- asya_server: `scripts/setup_asterisk.sh` — установка/копирование конфигов Asterisk.
- asya_server: `asterisk_configs/ari.conf`, `asterisk_configs/extensions.conf`, `asterisk_configs/sip.conf` — конфиги Asterisk.
- Giper2: явных ARI/telephony entrypoint не найдено (есть только общие аудио/транскрипция/FFmpeg-утилиты и web UI).

## 2) Список ключевых файлов ARI/telephony
- `src/ari_bot/nemo_ari_app.py` — обработка событий ARI (StasisStart/RecordingFinished/PlaybackFinished/StasisEnd), запись и воспроизведение.
- `src/utils/ari_client.py` — ARI REST клиент (hangup, play, redirect/transfer, originate).
- `src/api/routes/call_endpoints.py` — HTTP endpoints для hangup/play.
- `src/api/routes/websocket_handler.py` — обработка WebSocket событий (в API слое).
- `asterisk_configs/ari.conf` — настройки ARI и permissions.
- `asterisk_configs/extensions.conf` — dialplan с `Stasis(asya_app,...)`.
- `scripts/setup_asterisk.sh` — копирование конфигов в `/etc/asterisk`.

## 3) Как устроен диалог и state machine
- Состояние хранится в `CALL_PROFILES` (dict по channel_id) и `DIALOG_HISTORIES`.
- `CallProfile` содержит: имя, телефон, город, ИНН/компания, отдел, потребность, флаги `conversation_ended`, `record_index`.
- Цикл:
  1. `StasisStart` → `start_recording(...)`
  2. `RecordingFinished` → скачивание wav → ASR → LLM → TTS
  3. `play_tts_on_channel(...)` → `PlaybackFinished` → если `conversation_ended`=False, новая запись
  4. `StasisEnd` → сохранение профиля и очистка состояния

## 4) Запись/скачивание/обработка аудио
- Запись: ARI `POST /channels/{id}/record` с параметрами `format=wav`, `maxDurationSeconds`, `maxSilenceSeconds`, `ifExists=overwrite`, `beep=false`.
- Файлы записей берутся из `/var/spool/asterisk/recording` внутри контейнера Asterisk.
- Скачивание на хост реализовано через `docker cp`.
- ASR: NeMo (`EncDecCTCModelBPE`), распознавание после копирования записи.

## 5) TTS и форматирование под Asterisk
- TTS: Silero, функция `synthesize_tts_to_wav(...)`.
- Формат: WAV mono, 16-bit PCM, `sample_rate=8000`.
- Выкладка на Asterisk: `docker cp` в `/var/lib/asterisk/sounds` внутри контейнера.
- Воспроизведение: `sound:<basename>` через ARI `POST /channels/{id}/play`.

## 6) Playback и ожидание событий
- Используются события `PlaybackFinished` и `RecordingFinished`.
- WebSocket loop на `ARI_BASE_URL/events?app=<app>&subscribeAll=true`.
- Логика повторной записи запускается именно после `PlaybackFinished`.

## 7) Перевод на оператора
- В `nemo_ari_app.py` команда `TRANSFER_TO_MANAGER` от LLM помечает `conversation_ended=True`.
- В `utils/ari_client.py` есть метод `transfer_call(...)` через `POST /channels/{id}/redirect?endpoint=...`.
- Прямого bridge/queue в коде не обнаружено — скорее использовался redirect/dialplan.

## 8) Что переносим в новый проект
| Модуль/файл | Куда переносим | Что менять | Зависимости/примечания |
|---|---|---|---|
| `src/ari_bot/nemo_ari_app.py` | `src/ai_secretary/telephony/ari_app.py` | Переписать под наш `AriClient`, убрать docker cp, интегрировать `run_pipeline(...)` | aiohttp → httpx/websockets, Silero из текущего проекта |
| `src/utils/ari_client.py` | `src/ai_secretary/telephony/ari_client.py` | Сохранить идею методов (play/record/redirect), но с httpx и современными ошибками | BasicAuth, корректный base_url без двойного `/ari` |
| `asterisk_configs/*.conf` | `docs/` или шаблоны | Обновить под новое app_name/ARI user | Пароли не хранить в репо |
| `scripts/setup_asterisk.sh` | `docs/`/`scripts/` | Выровнять под текущие пути, убрать секреты | Только для Linux окружений |
| TTS формат 8kHz | `src/ai_secretary/tts/*` | Оставить 8kHz mono для Asterisk | Важно для корректного playback |

## 9) Риски/затыки
- Формат аудио: Asterisk часто ожидает 8kHz mono; несоответствие приводит к артефактам/ошибкам.
- В legacy проекте использовался `docker cp` (контейнер). В новом проекте — scp/ssh; нужно учесть права и задержки.
- В `nemo_ari_app.py` модели грузятся при старте — тяжело для быстрого рестарта.
- Использование абсолютных путей в legacy (`LLM_MODEL_PATH`) — в новом проекте нужно только env/относительные пути.
- Перевод на оператора реализован частично (через redirect), нужен единый сценарий bridge/queue.

## Примечания по переменным окружения (без значений)
- В legacy встречаются: `ARI_BASE_URL`, `ARI_USERNAME`, `ARI_PASSWORD`, `ARI_APP_NAME`, `ASTERISK_CONTAINER_NAME`.
- В конфиге `config/asterisk_ari_config.yaml` также есть `base_url`, `username`, `password`, `app_name`.