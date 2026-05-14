# NODE-028 Restore Kamatera Gateway Access And Rerun Controlled Adapter Live Smoke

## Status

CLOSED as blocked live smoke with cleanup preserved.

NODE-028 was opened to restore or document Kamatera gateway SSH access, start the gateway temporarily if access was restored, and rerun one controlled NODE-027 helper smoke of the NODE-025 gateway STT adapter.

The controlled adapter smoke was not completed. No production gateway STT rollout was performed, no live caller-facing call was run, `ai-secretary-ari.service` was not modified, Asterisk runtime env was not modified, and `OPENAI_API_KEY` remained absent from the Asterisk process environment.

## Goal

Run exactly one controlled one-off adapter smoke:

```text
one-off WAV artifact -> NODE-025 gateway adapter -> Kamatera gateway -> OpenAI Realtime -> redacted adapter result
```

Required safety boundaries:

- Do not enable production gateway STT by default.
- Do not change `ai-secretary-ari.service`.
- Do not persist temporary Asterisk runtime env changes.
- Do not place `OPENAI_API_KEY` on Asterisk.
- Do not commit real gateway tokens, OpenAI keys, root passwords, SSH private keys, or secret env files.
- Do not log transcript text by default.
- Do not change business dialog behavior, NODE-016 diagnostic isolation, NODE-014 RTP topology, or PHONE / PHONE_CONFIRM / CITY / transfer / callback / after-hours / SAFE_FINISH contracts.

## Intended Smoke Method

Gateway host:

```text
provider=Kamatera
region=USA / New York 2
host=ai-secretary-gateway-node023
public_ip=45.61.48.199
deploy_path=/opt/ai-secretary-gateway
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env
gateway_port=8080
gateway_endpoint=http://45.61.48.199:8080/v1/stt/realtime-measurement
```

Temporary gateway start command shape, with secrets staying in the gateway-only env file:

```bash
cd /opt/ai-secretary-gateway
set -a
. /etc/ai-secretary/openai-realtime-gateway.env
set +a
export GATEWAY_PORT=8080
nohup env PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.realtime_gateway \
  --host 0.0.0.0 \
  --port 8080 \
  </dev/null >/tmp/ai-secretary-gateway-node028.log 2>&1 &
echo "$!" >/tmp/ai-secretary-gateway-node028.pid
```

Intended Asterisk-side one-off helper command shape:

```bash
cd /home/tulauser/AI-secrenar-with-Asterisk-node014
export STT_GATEWAY_STT_ENABLED=true
export STT_GATEWAY_ADAPTER_ENABLED=true
export STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
export STT_GATEWAY_URL=http://45.61.48.199:8080/v1/stt/realtime-measurement
export STT_GATEWAY_TOKEN=<redacted gateway token from safe secret source>
export STT_GATEWAY_TIMEOUT_MS=10000
export STT_GATEWAY_MAX_RETRIES=0
export STT_GATEWAY_LOG_TRANSCRIPT=false
export STT_GATEWAY_LANGUAGE=ru
unset OPENAI_API_KEY
PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio <redacted one-off WAV artifact> \
  --require-explicit-flags
```

The helper was not run in NODE-028.

## Live Work And Blocker

User-provided external evidence during the node:

```text
ssh root@45.61.48.199:22 -> connection refused before authentication
local ping/ICMP -> timeout
from Asterisk 92.118.85.117:
  nc -vz -w 3 45.61.48.199 8080 -> connection refused
  curl -m 3 http://45.61.48.199:8080/ -> failed to connect
```

Codex also observed that one interrupted gateway-start command partially executed after the turn was aborted. That left a temporary gateway process listening on `0.0.0.0:8080` before any adapter smoke was run. Cleanup was performed immediately:

```text
temporary_gateway_process=stopped
port_8080_after_cleanup=not_listening
adapter_helper_run=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
```

Asterisk service and safe runtime profile after cleanup:

```text
host=tula
ai-secretary-ari.service=active
service_main_pid=7775
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Asterisk-to-gateway reachability after cleanup:

```text
nc -vz -w 3 45.61.48.199 8080 -> connection refused
curl -m 3 http://45.61.48.199:8080/ -> http_status=000, failed to connect
```

## Smoke Result

```text
kamatera_ssh_restored=false
gateway_started=false
gateway_reachable_from_asterisk=false
adapter_enabled_temporarily=false
adapter_default_enabled_after_smoke=false
adapter_smoke_exercised_node025_path=false
openai_realtime_from_gateway=not_run
gateway_auth=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=kamatera_ssh_unavailable_or_gateway_not_listening
error_type=kamatera_gateway_unavailable
error_status=not_available
error_redacted=true
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_after_smoke=stopped
live_call_run=false
real_secrets_committed=false
```

Interpretation:

- NODE-028 does not claim a successful live adapter smoke.
- The NODE-025 adapter path was not exercised live.
- Gateway auth was not run.
- OpenAI Realtime from the gateway was not run.
- No transcript was returned or logged.
- The interrupted temporary gateway process was stopped.
- Gateway STT remains disabled by default.

## Validation

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
111 passed
```

Pre-commit whitespace validation:

```text
git diff --check
passed
```

Secret/artifact checks:

```text
git status --short
tracked_changes_only_safe_docs=true
untracked_left_uncommitted=data/storage/, node014-server.tar
git diff --cached
no OPENAI_API_KEY, real GATEWAY_TOKEN, root password, SSH private key, or .env secret committed
```

## NODE-028 Result

```text
node_status=blocked live smoke closed
docs_only=true
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed=false
live_call_run=false
kamatera_gateway_started=false
kamatera_gateway_stopped_after_smoke=true
asterisk_service_changed=false
asterisk_runtime_env_changed=false
openai_key_on_asterisk_after_smoke=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_used_for_dialog=false
transcript_text_logged=false
real_secrets_committed=false
```

## Known Limitations

- NODE-028 does not prove the live adapter path because the one-off helper was not run.
- Gateway control remains operationally unreliable for this smoke path.
- No production gateway service, TLS, token rotation, or persistent gateway process was installed or validated.
- No live caller-facing call was run, by design.

## Next Recommendation

Before opening another live adapter smoke node, restore reliable Kamatera console/SSH control and verify from both operator and Asterisk networks that:

```text
ssh root@45.61.48.199
ss -ltnp | grep ':8080' # only when intentionally started
nc -vz -w 3 45.61.48.199 8080 # from Asterisk only after start
```

Then rerun the NODE-027 helper exactly once with temporary process env only, stop the gateway immediately afterward, and keep production gateway STT disabled by default.
