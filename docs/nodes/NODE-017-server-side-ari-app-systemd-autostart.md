# NODE-017 Server-Side ARI App Systemd Autostart

## Status

Docs and templates closeout. No production STT implementation.

## Goal

Make the proven server-side `ari_app` launch path restart-safe on the Asterisk server. After a server reboot or process crash, systemd should start the colocated ARI app again with the same NODE-014/NODE-016 RTP topology and diagnostics isolation.

## Scope Boundary

This node only documents and templates systemd/autostart for the server-side `ari_app`.

It does not change:

- PHONE behavior.
- PHONE_CONFIRM behavior.
- CITY validation.
- transfer, callback, after-hours, or SAFE_FINISH contracts.
- Russian-only caller-facing dialog behavior.
- NODE-014 RTP topology.
- NODE-016 diagnostic isolation behavior.
- production OpenAI STT adoption.

Production OpenAI egress remains a separate scoped decision. The default profile below is safe for RTP diagnostics only.

## Files Added

- `deploy/examples/systemd/ari-app.env.example`
- `deploy/examples/systemd/ai-secretary-ari-wrapper.sh`
- `deploy/examples/systemd/ai-secretary-ari.service`

These are templates. Install copies on the server; do not run them directly from git without checking server paths.

## Proven Server Path

Use the same server-side deployment shape proven by NODE-014 and NODE-016:

```text
project: /home/tulauser/AI-secrenar-with-Asterisk-node014
venv: /home/tulauser/AI-secrenar-with-Asterisk-node014/.venv
ARI_URL: http://127.0.0.1:8088/ari
ARI_USER: ai_secretary2
ARI_APP_NAME: ai_secretary
Stasis app: ai_secretary
publish mode: local
RTP bind host: 0.0.0.0
RTP externalMedia host advertised to Asterisk: 172.18.0.1
```

Local publish stays explicit:

```text
ASTERISK_PUBLISH_MODE=local
ASTERISK_LOCAL_SOUNDS_ROOT=<Asterisk sounds Docker volume _data path>
ASTERISK_SOUNDS_SUBDIR=ai_secretary
```

Do not hardcode the Docker volume path in code. Record the real path in `/etc/ai-secretary/ari-app.env` on the server.

One way to find the host-side sounds mount:

```bash
docker inspect asterisk --format '{{ range .Mounts }}{{ if eq .Destination "/var/lib/asterisk/sounds" }}{{ .Source }}{{ end }}{{ end }}'
```

## Secret Handling

Do not commit real secrets.

- Do not commit `OPENAI_API_KEY`.
- Do not commit `ARI_PASSWORD`.
- Store server runtime config in `/etc/ai-secretary/ari-app.env`.
- Read `ARI_PASSWORD` at runtime from `/home/tulauser/asterisk-config/ari.conf`.

Recommended installed permissions:

```bash
sudo install -d -o root -g root -m 0750 /etc/ai-secretary
sudo install -o root -g tulauser -m 0640 deploy/examples/systemd/ari-app.env.example /etc/ai-secretary/ari-app.env
sudo install -o root -g root -m 0755 deploy/examples/systemd/ai-secretary-ari-wrapper.sh /usr/local/bin/ai-secretary-ari-wrapper
sudo install -o root -g root -m 0644 deploy/examples/systemd/ai-secretary-ari.service /etc/systemd/system/ai-secretary-ari.service
```

Then edit only the installed env file:

```bash
sudo nano /etc/ai-secretary/ari-app.env
```

Set the real `ASTERISK_LOCAL_SOUNDS_ROOT`. Keep `OPENAI_API_KEY=dummy-for-rtp-diagnostics-only` only while running `rtp_diagnostics_only` with `STT_LIVE_OPENAI_DISABLED=true`.

## Environment File Template

Template path in git:

```text
deploy/examples/systemd/ari-app.env.example
```

Installed runtime path:

```text
/etc/ai-secretary/ari-app.env
```

Required diagnostic profile:

```bash
PROJECT_DIR=/home/tulauser/AI-secrenar-with-Asterisk-node014
VENV_PYTHON=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
ARI_CONF_PATH=/home/tulauser/asterisk-config/ari.conf
ARI_URL=http://127.0.0.1:8088/ari
ARI_USER=ai_secretary2
ARI_APP_NAME=ai_secretary
ASTERISK_PUBLISH_MODE=local
ASTERISK_LOCAL_SOUNDS_ROOT=<Asterisk sounds Docker volume _data path>
ASTERISK_SOUNDS_SUBDIR=ai_secretary
STT_LIVE_STREAMING_ENABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_FALLBACK_TO_BATCH=true
STT_LIVE_STREAMING_STAGE_ALLOWLIST=ISSUE,NAME,CITY
STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false
STT_LIVE_STREAMING_TOPOLOGY=snoop_external_media_rtp
STT_LIVE_RTP_BIND_HOST=0.0.0.0
STT_LIVE_EXTERNAL_MEDIA_HOST=172.18.0.1
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=dummy-for-rtp-diagnostics-only
```

## Wrapper Template

Template path in git:

```text
deploy/examples/systemd/ai-secretary-ari-wrapper.sh
```

Installed runtime path:

```text
/usr/local/bin/ai-secretary-ari-wrapper
```

The wrapper:

- loads `/etc/ai-secretary/ari-app.env`;
- reads `ARI_PASSWORD` from `/home/tulauser/asterisk-config/ari.conf` for the configured `ARI_USER`;
- exports `PYTHONPATH=src`;
- exports `PYTHONUNBUFFERED=1`;
- execs:

```bash
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -u -m ai_secretary.telephony.ari_app
```

The wrapper should fail loudly if the project directory, venv python, env file, or `ari.conf` is missing.

Because the systemd service runs as `tulauser`, the installed env file must be readable by that service user. Use `0640 root:tulauser`, not `0600 root:root`.

## Systemd Unit Template

Template path in git:

```text
deploy/examples/systemd/ai-secretary-ari.service
```

Installed runtime path:

```text
/etc/systemd/system/ai-secretary-ari.service
```

The unit:

- runs as `tulauser`;
- starts after `network-online.target` and `docker.service`;
- uses `/etc/ai-secretary/ari-app.env`;
- sets `PYTHONUNBUFFERED=1`;
- logs to journald by default;
- restarts on failure with `RestartSec=5`.

`tulauser` is the default because the proven server deployment lives under that user's home directory. If operations moves the deployment to a system path, create a dedicated service user in a later hardening node.

## Operational Commands

Reload and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-secretary-ari
sudo systemctl start ai-secretary-ari
sudo systemctl status ai-secretary-ari --no-pager
```

Follow logs:

```bash
journalctl -u ai-secretary-ari -f
```

Restart after config changes:

```bash
sudo systemctl restart ai-secretary-ari
```

Stop:

```bash
sudo systemctl stop ai-secretary-ari
```

## Expected Startup Evidence

In `journalctl -u ai-secretary-ari -f`, expect the same readiness path as the manual server shell:

```text
ARI_LISTENING
ARI_WS_CONNECTED
READY_WAITING_FOR_CALLS
```

Local publish should use local mode, not SSH/SCP:

```text
publish_mode_selected mode=local
publish_local_success
SYSTEM_SOUNDS_DONE
```

The service must fail visibly if the env file is missing, `ari.conf` is unreadable, the ARI password cannot be found, or the virtualenv python is not executable.

## Reboot Validation Recipe

1. Reboot the server:

```bash
sudo reboot
```

2. After reconnecting, verify Asterisk is running:

```bash
docker ps --filter name=asterisk
```

3. Verify the ARI app service is active:

```bash
sudo systemctl status ai-secretary-ari --no-pager
```

4. Verify readiness in journal:

```bash
journalctl -u ai-secretary-ari --no-pager | grep -E 'ARI_LISTENING|ARI_WS_CONNECTED|READY_WAITING_FOR_CALLS'
```

5. Run the existing isolated RTP diagnostics smoke.

Use the NODE-016 diagnostic profile:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

6. Verify diagnostics evidence:

```bash
journalctl -u ai-secretary-ari --no-pager | grep -E 'stt_live_rtp_packets_received_count|stt_live_pcm_chunks_created_count|stt_live_rtp_diagnostics_result|diagnostic_call_finished'
```

Acceptance after reboot:

- Asterisk container is running.
- `ai-secretary-ari.service` is active.
- ARI readiness events are present.
- RTP packet count is greater than zero.
- PCM chunk count is greater than zero.
- `stt_live_rtp_diagnostics_result=rtp_packets_received`.
- `diagnostic_call_finished status=ok`.

## Safe Diagnostic Profile

For now, keep the service in RTP diagnostics mode:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

With this profile, `OPENAI_API_KEY` may be a dummy placeholder because OpenAI live STT is disabled. Before enabling production OpenAI STT, replace the dummy key outside git and make a separate scoped production-STT change.

## Validation

Docs/templates validation:

```text
git diff --check
```

Script validation:

```text
bash -n deploy/examples/systemd/ai-secretary-ari-wrapper.sh
```

Secret check:

```text
rg -n "OPENAI_API_KEY|ARI_PASSWORD|AiSec|sk-" deploy docs scripts src
```

Expected result: no committed real secrets. Placeholder names and documentation references are acceptable.

## Closeout

NODE-017 provides a restart-safe systemd launch plan for server-side `ari_app`, preserving the proven local publish and `snoop_external_media_rtp` topology. The service can be enabled for reboot survival, keeps logs in `journalctl`, reads `ARI_PASSWORD` from `ari.conf` at runtime, and keeps production STT out of scope.
