# NODE-030 Controlled Russian Speech WAV Gateway Transcript Smoke

## Status

CLOSED as controlled live adapter smoke passed with transcript-bearing events and cleanup verified.

NODE-030 ran exactly one non-caller-facing gateway adapter smoke using a non-sensitive Russian speech WAV, the Kamatera gateway, explicit temporary flags, transcript logging disabled, and transcript use for dialog disabled.

This was not a production rollout. Gateway STT remains disabled by default, `ai-secretary-ari.service` was not modified, Asterisk runtime env was not modified, no caller-facing live call was run, and `OPENAI_API_KEY` remained absent from the Asterisk process environment.

## Goal

Answer whether real speech, rather than the NODE-028 silent WAV artifact, produces transcript-bearing gateway/OpenAI events.

Required safety boundaries:

- Do not enable production gateway STT by default.
- Do not change `ai-secretary-ari.service`.
- Do not persist Asterisk runtime env changes.
- Do not place `OPENAI_API_KEY` on Asterisk.
- Do not commit gateway tokens, OpenAI keys, root passwords, SSH private keys, secret env files, `data/storage/`, or `node014-server.tar`.
- Do not log transcript text by default.
- Do not use the transcript for dialog.
- Do not run a caller-facing live call.
- Stop the temporary gateway after the smoke.

## Implementation Note

NODE-030 made one scoped helper change so the manual smoke command can measure the gateway path with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.

The default business adapter behavior is unchanged:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false -> no gateway request from the ARI business path
```

Only the manual `gateway_adapter_smoke` helper passes `allow_request_without_dialog_use=true`. In that mode the adapter may send the one-off measurement request, but any transcript candidate is rejected with:

```text
fallback_reason=gateway_stt_dialog_use_disabled
dialog_transcript_used=false
```

## Speech WAV Source

The smoke used an existing safe generated system prompt WAV from the local untracked system-sound artifacts:

```text
source=data/storage/_system/prompt_1.wav
speech_wav_source=existing_safe_fixture
real_caller_audio_used=false
```

For the smoke, the source was converted to a temporary 24 kHz mono 16-bit PCM WAV:

```text
temporary_local_audio=tmp/node030-smoke/node030_russian_system_prompt_24k.wav
temporary_asterisk_audio=/tmp/ai-secretary-node030-smoke/node030_russian_system_prompt_24k.wav
```

The temporary audio was not committed.

## Audio Diagnostics

Pre-smoke diagnostics on Asterisk:

```text
audio_payload_valid=true
audio_duration_ms=4662
audio_sample_rate_hz=24000
audio_channels=1
audio_sample_width_or_codec=2 / pcm
audio_total_bytes=223878
audio_chunk_count=24
audio_rms=2666.07
audio_peak=29521
audio_non_silent_ratio=0.5535
audio_quality_classification=valid_speech_candidate
```

## Gateway Startup

Gateway host:

```text
provider=Kamatera
region=USA / New York 2
public_ip=45.61.48.199
deploy_path=/opt/ai-secretary-gateway
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env
gateway_endpoint=http://45.61.48.199:8080/v1/stt/realtime-measurement
```

Initial state:

```text
port_8080_at_node_start=not_listening
kamatera_gateway_running_at_node_start=false
```

Temporary launch shape:

```bash
cd /opt/ai-secretary-gateway
set -a
. /etc/ai-secretary/openai-realtime-gateway.env
set +a
export GATEWAY_PORT=8080
nohup env PYTHONPATH=/tmp/ai-secretary-node030-src:src .venv/bin/python -m ai_secretary.stt.realtime_gateway \
  --host 0.0.0.0 \
  --port 8080 \
  </dev/null >/var/log/ai-secretary-gateway-node030.log 2>&1 &
```

Gateway verification:

```text
gateway_started=true
gateway_pid=2544
port_8080_listening=true
listen_addr=0.0.0.0:8080
uvicorn_startup_complete=true
```

## Asterisk Verification

Before the smoke:

```text
ai-secretary-ari.service=active
service_main_pid=7775
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
STT_GATEWAY_* variables in service env=<absent>
```

Asterisk-to-gateway reachability:

```text
nc -vz -w 3 45.61.48.199 8080 -> succeeded
GET http://45.61.48.199:8080/v1/stt/realtime-measurement -> 405 Method Not Allowed
gateway_reachable_from_asterisk=true
```

The gateway token was read from the gateway-only env file and placed briefly in a `0600` temporary file on Asterisk for the one-off process, then removed after the smoke:

```text
temporary_token_file=/tmp/ai-secretary-node030-smoke/gateway_token
temporary_token_file_after_smoke=absent
```

## Smoke Method

The smoke ran once from Asterisk using a temporary source overlay under `/tmp`, without changing the protected deployment tree or systemd service:

```text
temporary_source_overlay=/tmp/ai-secretary-node030-src
temporary_audio_dir=/tmp/ai-secretary-node030-smoke
```

One-off helper flags:

```bash
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
python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio /tmp/ai-secretary-node030-smoke/node030_russian_system_prompt_24k.wav \
  --require-explicit-flags
```

## Smoke Result

Structured redacted result:

```text
speech_wav_source=existing_safe_fixture
real_caller_audio_used=false
audio_payload_valid=true
audio_duration_ms=4662
audio_sample_rate_hz=24000
audio_channels=1
audio_sample_width_or_codec=2 / pcm
audio_total_bytes=223878
audio_chunk_count=24
audio_rms=2666.07
audio_peak=29521
audio_non_silent_ratio=0.5535
audio_quality_classification=valid_speech_candidate
gateway_started=true
gateway_reachable_from_asterisk=true
adapter_smoke_exercised_node025_path=true
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=24
openai_event_type_counts={
  conversation.item.added: 1,
  conversation.item.done: 1,
  conversation.item.input_audio_transcription.completed: 1,
  conversation.item.input_audio_transcription.delta: 22,
  input_audio_buffer.committed: 1,
  session.created: 1,
  session.updated: 1
}
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_present=true
transcript_text_logged=false
transcript_used_for_dialog=false
fallback_reason=gateway_stt_dialog_use_disabled
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

Interpretation:

- Valid speech-bearing Russian audio produced transcript-bearing OpenAI Realtime events.
- `transcript_present` became `true` with real speech audio.
- NODE-029 audio diagnostics classified the payload as `valid_speech_candidate`.
- Gateway/OpenAI event diagnostics were captured.
- Transcript text was not logged or returned by the gateway by default.
- The transcript was not used for dialog.
- Business dialog remained unaffected.

## Cleanup Verification

Gateway cleanup:

```text
gateway_process_after_smoke=stopped
port_8080_after_smoke=not_listening
asterisk_to_gateway_after_cleanup=connection_refused
temporary_gateway_source_overlay_after_smoke=absent
```

Asterisk cleanup:

```text
temporary_token_file_after_smoke=absent
temporary_source_overlay_after_smoke=absent
temporary_audio_after_smoke=absent
ai-secretary-ari.service=active
OPENAI_API_KEY=<absent>
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

## Validation

Focused helper validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
13 passed
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
115 passed
```

Pre-commit whitespace validation:

```text
git diff --check
passed
```

## NODE-030 Result

```text
node_status=closed live speech adapter smoke passed
code_test_changes_added=true
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
chunks_sent=24
transcript_event_seen=true
transcript_present=true
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=gateway_stt_dialog_use_disabled
likely_root_cause_if_prior_empty_transcript=NODE-028 used silent/non-speech audio
real_secrets_committed=false
```

## Known Limitations

- The speech WAV came from a generated system prompt fixture, not a live caller recording.
- Transcript text remained intentionally unavailable by default, so this node proves transcript presence and event flow, not transcript wording accuracy.
- The gateway was still run as a temporary HTTP process for a controlled smoke. Productionization remains a separate node.

## Next Recommendation

Close the NODE-028 empty-transcript issue as caused by silent/non-speech audio. The next useful node is gateway productionization only if the project is ready for TLS, systemd, firewall/runbook hardening, token rotation handling, and normal deployment of the adapter/helper source while still keeping gateway STT disabled by default until an explicit adoption decision.
