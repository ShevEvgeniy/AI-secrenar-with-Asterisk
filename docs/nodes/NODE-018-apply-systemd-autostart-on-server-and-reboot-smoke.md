# NODE-018 Apply Systemd Autostart On Server And Reboot Smoke

## Status

PASS. Server-side systemd autostart is installed, enabled, reboot-safe, and validated with isolated RTP diagnostics.

## Goal

Apply the NODE-017 systemd/autostart templates on the actual Asterisk server and record a reboot-safe RTP diagnostics smoke.

Server:

```text
92.118.85.117
```

Deployment path:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014
```

## Scope Boundary

No application code was changed.

This node does not change:

- PHONE behavior.
- PHONE_CONFIRM behavior.
- CITY validation.
- Transfer, callback, after-hours, or SAFE_FINISH contracts.
- Russian-only caller-facing dialog behavior.
- NODE-014 RTP topology.
- NODE-016 diagnostic isolation logic.

## Installed Runtime Files

Installed on the server:

```text
/etc/ai-secretary/ari-app.env
/usr/local/bin/ai-secretary-ari-wrapper
/etc/systemd/system/ai-secretary-ari.service
/etc/systemd/system/ai-secretary-ari.service.d/local-publish-permissions.conf
```

`/etc/ai-secretary/ari-app.env` contains no real OpenAI key and no ARI password. `ARI_PASSWORD` is read at runtime by the wrapper from:

```text
/home/tulauser/asterisk-config/ari.conf
```

Safe diagnostic profile installed:

```text
TELEPHONY_STT_BACKEND=openai
OPENAI_API_KEY=dummy
OPENAI_BASE_URL=http://127.0.0.1:9/v1
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
ASTERISK_PUBLISH_MODE=local
ASTERISK_LOCAL_SOUNDS_ROOT=/var/lib/docker/volumes/40c494a6543fbb493376133cfc53ef56471bdf18819aebfb20d4ffd9bfffeeb9/_data
ASTERISK_SOUNDS_SUBDIR=ai_secretary
STT_LIVE_RTP_BIND_HOST=0.0.0.0
STT_LIVE_EXTERNAL_MEDIA_HOST=172.18.0.1
```

## Exact Server Commands Used

Initial server inspection:

```bash
ssh root@92.118.85.117 "id && hostname"
ssh tulauser@92.118.85.117 "id; ls -l /home/tulauser/asterisk-config/ari.conf; systemctl is-active ai-secretary-ari 2>/dev/null || true; systemctl is-enabled ai-secretary-ari 2>/dev/null || true"
ssh tulauser@92.118.85.117 "docker inspect asterisk --format '{{json .Mounts}}'"
```

Template staging and install:

```bash
ssh root@92.118.85.117 "mkdir -p /tmp/node018-systemd"
scp deploy/examples/systemd/ai-secretary-ari-wrapper.sh deploy/examples/systemd/ai-secretary-ari.service root@92.118.85.117:/tmp/node018-systemd/
scp C:/tmp/node018-ari-app.env root@92.118.85.117:/tmp/node018-systemd/ari-app.env
ssh root@92.118.85.117 "install -d -o root -g root -m 0750 /etc/ai-secretary && install -o root -g tulauser -m 0640 /tmp/node018-systemd/ari-app.env /etc/ai-secretary/ari-app.env && install -o root -g root -m 0755 /tmp/node018-systemd/ai-secretary-ari-wrapper.sh /usr/local/bin/ai-secretary-ari-wrapper && install -o root -g root -m 0644 /tmp/node018-systemd/ai-secretary-ari.service /etc/systemd/system/ai-secretary-ari.service && bash -n /usr/local/bin/ai-secretary-ari-wrapper && systemctl daemon-reload && systemctl enable ai-secretary-ari && systemctl start ai-secretary-ari && systemctl --no-pager --full status ai-secretary-ari"
```

Runtime permission fixes required by the copied server deployment:

```bash
ssh root@92.118.85.117 "chown root:tulauser /etc/ai-secretary && chmod 0750 /etc/ai-secretary && systemctl restart ai-secretary-ari"
ssh root@92.118.85.117 "chown -R tulauser:tulauser /home/tulauser/AI-secrenar-with-Asterisk-node014/data/storage && systemctl restart ai-secretary-ari"
ssh root@92.118.85.117 "mkdir -p /home/tulauser/AI-secrenar-with-Asterisk-node014/tmp/diag && chown -R tulauser:tulauser /home/tulauser/AI-secrenar-with-Asterisk-node014/tmp && systemctl restart ai-secretary-ari"
```

Docker restored `/var/lib/docker` to `0710` after reboot, blocking the non-root service from traversing to the local sounds volume. The final server-side drop-in makes the local publish permission fix reboot-safe:

```bash
ssh root@92.118.85.117 "mkdir -p /etc/systemd/system/ai-secretary-ari.service.d && printf '%s\n' '[Service]' 'ExecStartPre=+/usr/bin/chmod 0711 /var/lib/docker' > /etc/systemd/system/ai-secretary-ari.service.d/local-publish-permissions.conf && systemctl daemon-reload && systemctl restart ai-secretary-ari"
```

Reboot validation:

```bash
ssh root@92.118.85.117 "systemctl reboot"
ssh root@92.118.85.117 "docker ps --filter name=asterisk --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
ssh root@92.118.85.117 "systemctl is-enabled ai-secretary-ari; systemctl is-active ai-secretary-ari; systemctl --no-pager --full status ai-secretary-ari"
ssh root@92.118.85.117 "journalctl -u ai-secretary-ari -b --no-pager | grep -E 'SYSTEM_SOUNDS_DONE|SYSTEM_SOUNDS_BG_OK|ARI_LISTENING|ARI_WS_CONNECTED|READY_WAITING_FOR_CALLS|publish_local_success'"
```

RTP diagnostics smoke:

```bash
ssh root@92.118.85.117 "docker exec asterisk /usr/sbin/asterisk -rx 'channel originate Local/501@from-internal application Echo'"
ssh root@92.118.85.117 "cd /home/tulauser/AI-secrenar-with-Asterisk-node014 && .venv/bin/python - <<'PY'
import json
from pathlib import Path
p=Path('data/storage/artifacts/1778672473.13/events.jsonl')
events=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]
interesting={'stt_live_rtp_packets_received_count','stt_live_pcm_chunks_created_count','stt_live_rtp_diagnostics_result','stt_live_diagnostics_dialog_bypass','diagnostic_call_finished'}
for e in events:
    if e.get('action') in interesting:
        print(json.dumps({k:e.get(k) for k in ('action','status','reason')}, ensure_ascii=False), json.dumps(e.get('details',{}), ensure_ascii=False))
print('forbidden_actions', [e.get('action') for e in events if e.get('action') in {'safe_finish','transfer','callback'}])
PY"
```

## Operational Findings

The server deployment is a copied tree, not a git checkout, and it did not contain the `deploy/` templates. Templates were copied from the local branch to `/tmp/node018-systemd` and then installed as root.

The first service start failed because `/etc/ai-secretary` was `root:root 0750`, so `tulauser` could not traverse it even though `/etc/ai-secretary/ari-app.env` was `root:tulauser 0640`. Final installed directory permissions are `root:tulauser 0750`.

The copied deployment had runtime directories owned by `root:root`. The service runs as `tulauser`, so these runtime paths were changed to `tulauser:tulauser`:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/data/storage
/home/tulauser/AI-secrenar-with-Asterisk-node014/tmp
```

Local publish from a non-root service also required traverse access through `/var/lib/docker`. Docker reset `/var/lib/docker` during reboot, so the final systemd drop-in runs:

```text
ExecStartPre=+/usr/bin/chmod 0711 /var/lib/docker
```

This grants traverse-only access, not directory listing, and preserves the service process itself as `tulauser`.

## Startup Evidence

After final reboot:

```text
enabled
active
Drop-In: /etc/systemd/system/ai-secretary-ari.service.d
         local-publish-permissions.conf
Process: 3810 ExecStartPre=/usr/bin/chmod 0711 /var/lib/docker (code=exited, status=0/SUCCESS)
Main PID: 3812 (python)
```

Asterisk container:

```text
NAMES      STATUS
asterisk   Up 16 seconds (health: starting)
```

Readiness journal:

```text
May 13 14:43:11 ARI_LISTENING http://127.0.0.1:8088/ari ai_secretary
May 13 14:43:11 ARI_WS_CONNECTED
May 13 14:43:12 publish_local_success ... sound:ai_secretary/_system/prompt_1
May 13 14:43:15 SYSTEM_SOUNDS_DONE ok 3952 {... all system sounds true ...}
May 13 14:43:15 SYSTEM_SOUNDS_BG_OK {... all system sounds true ...}
May 13 14:43:15 READY_WAITING_FOR_CALLS
```

## Smoke Evidence

Smoke source:

```text
docker exec asterisk /usr/sbin/asterisk -rx 'channel originate Local/501@from-internal application Echo'
```

The earlier self-contained `Playback(demo-congrats)` attempt was rejected because `demo-congrats` was not installed. `Playback(ai_secretary/_system/prompt_1)` reached Stasis but ended the Local caller leg before snoop setup. `Echo` kept the Local caller leg alive and produced the accepted RTP diagnostics smoke.

Smoke result:

```text
call_id=1778672473.13
stage=ISSUE
provider=rtp_diagnostics_only
topology=snoop_external_media_rtp
rtp_bind_host=0.0.0.0
advertised_host=172.18.0.1
stt_live_rtp_packets_received_count=228
stt_live_pcm_chunks_created_count=228
stt_live_rtp_diagnostics_result=rtp_packets_received
stt_live_diagnostics_dialog_bypass status=handled reason=diagnostic_dialog_isolated
diagnostic_call_finished status=ok reason=diagnostic_dialog_isolated
dialog_stage_at_finish=ISSUE
turns_done=0
```

Expected dummy STT failure was isolated:

```text
stt_backend=openai
error=ConnectError('[Errno 111] Connection refused')
diagnostic_dialog_isolated=true
dialog_state_preserved=true
safe_finish_suppressed=true
transfer_suppressed=true
callback_suppressed=true
```

Forbidden business actions check:

```text
forbidden_actions []
```

The only `safe_finish`, `transfer`, and `callback` strings in the smoke event file are the expected suppression fields above; there were no business `safe_finish`, `transfer`, or `callback` action events.

## Secret Check

No real `OPENAI_API_KEY` was used or recorded. The installed diagnostic env uses:

```text
OPENAI_API_KEY=dummy
OPENAI_BASE_URL=http://127.0.0.1:9/v1
```

No `ARI_PASSWORD` was written into the repository or the installed env file. The wrapper reads it from `/home/tulauser/asterisk-config/ari.conf` at runtime.

## Validation

Server-side:

- `ai-secretary-ari.service` is enabled.
- `ai-secretary-ari.service` is active after reboot.
- Asterisk container is running after reboot.
- The ARI app reaches `ARI_LISTENING`, `ARI_WS_CONNECTED`, and `READY_WAITING_FOR_CALLS` without manual shell exports.
- Local publish uses `ASTERISK_PUBLISH_MODE=local` and reaches `SYSTEM_SOUNDS_DONE ok`.
- Isolated RTP diagnostics smoke passes after reboot.

Repository:

```text
git diff --check
bash -n deploy/examples/systemd/ai-secretary-ari-wrapper.sh
git status --short
```

Secret scans were also run for real OpenAI key patterns and ARI password assignments. Hits were limited to documented placeholders and the wrapper export from `ari.conf`.

`data/storage/` and `node014-server.tar` remain untracked local artifacts and must not be committed.
