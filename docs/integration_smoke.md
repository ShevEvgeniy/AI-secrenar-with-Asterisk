# Integration smoke test: Asterisk ARI → AI Secretary

Цель: за 2–3 минуты подтвердить, что end-to-end цепочка работает:

Answer → Record → Download → Pipeline (RAG/LLM) → TTS → Publish WAV → Playback → Hangup

## Предусловия

### Asterisk (Linux host, Docker container `asterisk`)
- Контейнер: `asterisk` (образ `andrius/asterisk:20.16.0_debian-trixie`)
- ARI/HTTP доступен на хосте: `http://<HOST>:8088/ari`
- Dialplan: `/etc/asterisk/extensions.conf` содержит маршрут:
  - `exten => 501,... Stasis(ai_secretary)`

Быстрые проверки на сервере:
```bash
docker ps | grep asterisk
docker exec -it asterisk sh -lc '/usr/sbin/asterisk -rx "http show status"; /usr/sbin/asterisk -rx "ari show users"'
docker exec -it asterisk sh -lc 'nl -ba /etc/asterisk/extensions.conf | sed -n "20,40p"'

Windows (где запускается listener)
Активировано .venv
Python запускается из проекта
Доступ до <HOST>:8088 есть (возможно через VPN)
Конфигурация .env (минимум)
ARI
ARI_URL=http://<HOST>:8088/ari
ARI_USER=<ari_user>
ARI_PASSWORD=<ari_password>
ARI_APP_NAME=ai_secretary

Проверка ARI (должно быть 200):

curl.exe -s -o NUL -w "%{http_code}`n" -u "$env:ARI_USER`:$env:ARI_PASSWORD" "$env:ARI_URL/asterisk/info"
Publish (для Playback ответа)

Рекомендованная схема (Asterisk в Docker):

ASTERISK_SSH_HOST=<HOST>
ASTERISK_SSH_USER=tulauser
ASTERISK_SSH_KEY=C:\Users\<you>\.ssh\<key>
ASTERISK_SOUNDS_DIR=/var/lib/asterisk/sounds
ASTERISK_SOUNDS_SUBDIR=ai_secretary
ASTERISK_DOCKER_CONTAINER=asterisk

Проверка key-only SSH:

ssh.exe -i "$env:ASTERISK_SSH_KEY" -o BatchMode=yes -o IdentitiesOnly=yes `
  "$env:ASTERISK_SSH_USER@$env:ASTERISK_SSH_HOST" "echo OK"

Проверка docker-доступа по SSH:

ssh.exe -i "$env:ASTERISK_SSH_KEY" -o BatchMode=yes -o IdentitiesOnly=yes `
  "$env:ASTERISK_SSH_USER@$env:ASTERISK_SSH_HOST" "docker ps --format '{{.Names}}' | head -n 5"
Шаги прогона
1) Preflight
.\scripts\check_env.cmd

Ожидаем ALL_OK (или минимум: ARI OK, SSH key-only OK, publish enabled OK).

2) Запуск ARI listener

Рекомендуемый запуск (обходит возможные проблемы скриптов):

$env:PYTHONPATH="src"
python -m ai_secretary.telephony.ari_app

Ожидаем:

ARI_LISTENING ... ai_secretary
ARI_WS_CONNECTED
3) Тестовый звонок

Позвонить на 501 (в dialplan это Stasis(ai_secretary)).

4) Критерии успеха (в консоли listener)

Ожидаемые ключевые строки:

STASIS_START <channel_id>
ANSWERED <channel_id>
RECORD_DONE <channel_id>
DOWNLOAD_OK <channel_id>
MOH_START_OK ... → PIPELINE_OK ... → MOH_STOP_OK ...
TTS_OK ...
PUBLISH_OK ... sound:ai_secretary/<channel_id>/reply
PLAY_OK ...
5) Артефакты и события

Папка артефактов:

data/storage/artifacts/<channel_id>/

Важное:

events.jsonl — единый трейс
input.wav, reply.wav, reply_8k.wav
transcript.txt, summary.txt, response_for_tts.txt, chunks.json, profile.json

Быстро посмотреть хвост событий:

Get-Content .\data\storage\artifacts\<channel_id>\events.jsonl -Tail 40
Типовые проблемы и быстрые решения
401 Unauthorized на ARI
неверный ARI_USER/ARI_PASSWORD
проверь ari show users внутри контейнера
curl возвращает 000
нет сетевого доступа до <HOST>:8088 (VPN/фаервол)
проверь Test-NetConnection <HOST> -Port 8088
Publish FAIL: SSH key-only
root часто запрещён; используй tulauser
ключ должен быть в /home/tulauser/.ssh/authorized_keys
проверка: ssh ... "echo OK"
Playback FAIL: media_missing

Проверить наличие файла внутри контейнера:

docker exec -it asterisk sh -lc 'ls -la /var/lib/asterisk/sounds/ai_secretary/<channel_id>/'
docker exec -it asterisk sh -lc '/usr/sbin/asterisk -rx "file show file ai_secretary/<channel_id>/reply"'
Долгая первая обработка

Модель эмбеддингов может грузиться при первом звонке. Это отдельная оптимизация (warmup/cache).

Фиксация результата в git
git status
git add docs/integration_smoke.md
# (опционально) добавь README.md только если он реально менялся:
# git add README.md
git commit -m "Add integration smoke test guide"
git push

### Шаг 2 — Зафиксируй документ в git
В терминале:

```powershell
git status
git add docs/integration_smoke.md
git commit -m "Add integration smoke test guide"
git push

(Если README не менял — не добавляй его.)