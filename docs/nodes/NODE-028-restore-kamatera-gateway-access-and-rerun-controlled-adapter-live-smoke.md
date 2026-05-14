# NODE-028 Restore Kamatera Gateway Access And Rerun Controlled Adapter Live Smoke

## Status

CLOSED as controlled live adapter smoke passed with empty-transcript fallback and cleanup verified.

NODE-028 restored Kamatera gateway access, started the gateway temporarily, verified Asterisk-to-gateway reachability, ran exactly one one-off NODE-027 helper smoke through the NODE-025 gateway adapter path, then stopped the gateway listener.

This was not a production rollout. Gateway STT remains disabled by default, `ai-secretary-ari.service` was not modified, Asterisk runtime env was not modified, no live caller-facing call was run, and `OPENAI_API_KEY` remained absent from the Asterisk process environment.

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

## Gateway Startup

Gateway host:

```text
provider=Kamatera
region=USA / New York 2
host=ai-secretary-gateway-node023
public_ip=45.61.48.199
deploy_path=/opt/ai-secretary-gateway
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_permissions=-rw-------
gateway_port=8080
gateway_endpoint=http://45.61.48.199:8080/v1/stt/realtime-measurement
ufw=active
ufw_8080_allow_from=92.118.85.117
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
  </dev/null >/var/log/ai-secretary-gateway-node028.log 2>&1 &
echo gateway_pid=$!
```

Gateway verification:

```text
gateway_pid=1170
port_8080_listening=true
listen_addr=0.0.0.0:8080
uvicorn_startup_complete=true
```

The initial SSH launch wrapper remained attached. The wrapper process was killed by the operator while preserving the gateway process `1170`.

## Asterisk Verification

Asterisk server:

```text
host=tula
ip=92.118.85.117
deploy_path=/home/tulauser/AI-secrenar-with-Asterisk-node014
ai-secretary-ari.service=active
service_main_pid=7775
```

Asterisk safe runtime profile before smoke:

```text
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Asterisk-to-gateway reachability before smoke:

```text
nc -vz -w 3 45.61.48.199 8080 -> succeeded
GET http://45.61.48.199:8080/v1/stt/realtime-measurement -> 405 Method Not Allowed
```

The `405` result was expected for a GET to the POST-only measurement endpoint and proved the listener was reachable from Asterisk.

## Smoke Method

The Asterisk deployment tree did not contain the NODE-025 adapter or NODE-027 helper files. To avoid modifying the protected deployment source or systemd service, NODE-028 used a temporary secret-free source overlay under `/tmp` on the Asterisk server and removed it after the smoke:

```text
temporary_source_overlay=/tmp/ai-secretary-node028-src
temporary_audio_dir=/tmp/ai-secretary-node028-smoke
temporary_audio=node028_silence_24k.wav
temporary_audio_format=mono 16-bit PCM 24000 Hz, 3 seconds
```

The gateway token was read from the gateway-only env file and placed briefly in a `0600` temporary file on Asterisk for the one-off process, then removed immediately after the helper exited:

```text
temporary_token_file=/tmp/ai-secretary-node028-smoke/gateway_token
temporary_token_file_permissions=-rw-------
temporary_token_file_after_smoke=absent
```

One-off helper command shape:

```bash
cd /tmp/ai-secretary-node028-smoke
export PYTHONPATH=/tmp/ai-secretary-node028-src
export STT_GATEWAY_STT_ENABLED=true
export STT_GATEWAY_ADAPTER_ENABLED=true
export STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
export STT_GATEWAY_URL=http://45.61.48.199:8080/v1/stt/realtime-measurement
export STT_GATEWAY_TOKEN=<redacted gateway token from safe secret source>
export STT_GATEWAY_TIMEOUT_MS=10000
export STT_GATEWAY_MAX_RETRIES=0
export STT_GATEWAY_LOG_TRANSCRIPT=false
export STT_GATEWAY_LANGUAGE=ru
unset OPENAI_API_KEY
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python \
  -m ai_secretary.stt.gateway_adapter_smoke \
  --audio /tmp/ai-secretary-node028-smoke/node028_silence_24k.wav \
  --require-explicit-flags
```

`STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` was used only in the one-off helper process because the current NODE-025 adapter does not perform a gateway request unless dialog-use is explicitly enabled. No business dialog or service process used the transcript. The returned transcript was empty and `dialog_transcript_used=false`.

## Smoke Result

```text
kamatera_ssh_restored=true
gateway_started=true
gateway_reachable_from_asterisk=true
adapter_enabled_temporarily=true
adapter_default_enabled_after_smoke=false
adapter_smoke_exercised_node025_path=true
openai_realtime_from_gateway=ok
gateway_auth=ok
chunks_sent=15
transcript_present=false
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=empty_transcript
error_type=none
error_status=200
error_redacted=true
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_after_smoke=stopped
live_call_run=false
real_secrets_committed=false
```

Redacted helper evidence:

```text
adapter_enabled_temporarily=true
adapter_smoke_exercised_node025_path=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=15
gateway_http_status=200
openai_realtime_connection_ok=true
openai_session_created=true
audio_send_started=true
transcript_text_present=false
transcript_text_logged=false
dialog_transcript_used=false
fallback_reason=empty_transcript
```

Interpretation:

- The NODE-025 adapter path was exercised live from the Asterisk server.
- Gateway auth worked.
- OpenAI Realtime from the Kamatera gateway worked.
- Audio was sent through the gateway (`chunks_sent=15`).
- The silent WAV produced no transcript; the adapter rejected it with `empty_transcript`.
- Transcript text was not logged.
- No business dialog consumed a transcript.
- Production gateway STT remains disabled by default.

## Cleanup Verification

Gateway cleanup:

```text
kill 1170 -> completed
gateway_process_after_smoke=stopped
port_8080_after_smoke=not_listening
asterisk_to_gateway_after_cleanup=connection_refused
```

Asterisk cleanup:

```text
temporary_token_file_after_smoke=absent
temporary_source_overlay_after_smoke=absent
temporary_audio_after_smoke=absent
ai-secretary-ari.service=active
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Local cleanup:

```text
temporary_local_wav_removed=true
```

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
untracked_left_uncommitted=data/storage/, node014-server.tar
git diff --cached
no OPENAI_API_KEY, real GATEWAY_TOKEN, root password, SSH private key, or .env secret committed
```

## NODE-028 Result

```text
node_status=closed live adapter smoke passed with empty-transcript fallback
docs_only=true
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed=false
live_call_run=false
kamatera_gateway_started=true
kamatera_gateway_stopped_after_smoke=true
asterisk_service_changed=false
asterisk_runtime_env_changed=false
openai_key_on_asterisk_after_smoke=false
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=15
transcript_present=false
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=empty_transcript
real_secrets_committed=false
```

## Known Limitations

- The smoke used a silent synthetic WAV, so it proves live adapter/gateway/OpenAI transport and fallback behavior, not useful transcript quality.
- The Asterisk deployment tree still lacks the NODE-025/NODE-027 source files; NODE-028 used a temporary overlay rather than changing the protected deployment.
- No production gateway service, TLS, token rotation, or persistent gateway process was installed or validated.
- No live caller-facing call was run, by design.

## Next Recommendation

Open a separate node only if the project is ready to test non-silent speech audio through the adapter or to productionize the gateway. A productionization node should add TLS, systemd, firewall/runbook hardening, secret rotation handling, and deployment of the adapter/helper source through the normal release path while keeping gateway STT disabled by default until an explicit adoption decision.
