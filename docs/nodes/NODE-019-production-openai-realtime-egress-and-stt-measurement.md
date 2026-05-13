# NODE-019 Production OpenAI Realtime Egress And STT Measurement

## Status

CLOSED. The safe one-off OpenAI Realtime transcription measurement path was prepared and then run manually on server `92.118.85.117`.

Result: direct OpenAI Realtime egress from the current Asterisk server is not viable. The server can reach `api.openai.com`, but OpenAI rejects the WebSocket request before audio is sent because the server location is in an unsupported country, region, or territory.

## Goal

Prepare a server-side, measurement-only OpenAI Realtime transcription path for server `92.118.85.117` without changing the production ARI service runtime profile or business dialog behavior.

This node is a measurement node, not a production rollout node.

## OpenAI Docs Recheck

Official OpenAI docs were rechecked on 2026-05-13.

Current implementation notes:

- Realtime transcription uses transcription-only sessions with `type: "transcription"`.
- Server-side pipelines can connect over WebSocket.
- The documented session payload uses `session.update`, `audio.input.format.type=audio/pcm`, and `audio.input.format.rate=24000`.
- `gpt-realtime-whisper` is the current live transcription model intended for streaming transcript deltas.
- Audio is sent with `input_audio_buffer.append` using base64 PCM chunks.
- With manual commit, `input_audio_buffer.commit` starts transcription for the buffered audio.
- Transcript timing is measured from `conversation.item.input_audio_transcription.delta` and `conversation.item.input_audio_transcription.completed`.
- Current public pricing lists GPT-Realtime-Whisper at `$0.017 per minute / $0.00028 per second`.

References:

- OpenAI Realtime transcription: https://developers.openai.com/api/docs/guides/realtime-transcription
- OpenAI Realtime WebSocket guide: https://developers.openai.com/api/docs/guides/realtime-websocket
- OpenAI API pricing: https://openai.com/api/pricing/

## Runtime Boundary

The server-side systemd service must remain in the NODE-018 safe diagnostic profile:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=dummy or absent for service runtime
```

This node does not change:

- `/etc/ai-secretary/ari-app.env`.
- `ai-secretary-ari.service`.
- Business dialog STT routing.
- PHONE behavior.
- PHONE_CONFIRM behavior.
- CITY validation.
- Transfer, callback, after-hours, or SAFE_FINISH contracts.
- Russian-only caller-facing dialog behavior.
- NODE-014 RTP topology.
- NODE-016 diagnostic isolation logic.

## Measurement Path

Module:

```text
ai_secretary.stt.realtime_measurement
```

The module is standalone and does not import `ai_secretary.telephony`, `ari_app`, `CallSession`, or dialog state helpers.

Safety properties:

- Reads `OPENAI_API_KEY` from the current process environment only.
- Does not accept an API key as a CLI argument.
- Does not print the key.
- Redacts likely secrets in all JSON event logs.
- Does not print transcript text; it only reports `realtime_transcript_text_present`.
- Accepts a server-local WAV file path.
- Requires mono 16-bit PCM WAV at 24 kHz by default.
- Emits cleanup completion even on missing-key and error paths.

Measured events:

```text
realtime_connection_attempt
realtime_connection_ok
realtime_connection_failed
realtime_session_created
realtime_audio_send_started
realtime_first_delta_ms
realtime_final_ms
realtime_transcript_text_present
realtime_error
realtime_cleanup_done
```

## Manual Server Measurement

Run manually after the prepared measurement path landed on `master` at `f50b6f1`.

Temporary shell environment only:

```bash
read -rsp "OPENAI_API_KEY: " OPENAI_API_KEY; echo
export OPENAI_API_KEY
PYTHONPATH=src python -m ai_secretary.stt.realtime_measurement \
  --audio /tmp/ai-secretary-node019/realtime_measurement_24k.wav \
  --language ru \
  --timeout-seconds 30
unset OPENAI_API_KEY
```

Audio:

```text
source=data/storage/_system/prompt_1.wav
converted_temp_file=/tmp/ai-secretary-node019/realtime_measurement_24k.wav
format=pcm_s16le, 24000 Hz, mono
duration=5.51 sec
```

Do not write the real key into:

```text
/etc/ai-secretary/ari-app.env
```

Do not restart or reconfigure:

```text
ai-secretary-ari.service
```

## Server Measurement Result

Observed events:

```text
realtime_connection_attempt
realtime_connection_failed
realtime_cleanup_done
```

Connection attempt details:

```text
model=gpt-realtime-whisper
websocket_host=api.openai.com/v1/realtime
language=ru
timeout_seconds=30
```

Failure:

```text
error_type=InvalidStatus
status_code=403 Forbidden
openai_error_code=unsupported_country_region_territory
message=Country, region, or territory not supported
chunks_sent=0
```

Interpretation:

- DNS/network egress to the OpenAI Realtime endpoint was sufficient to receive an OpenAI HTTP/WebSocket rejection.
- Rejection happened before session creation and before audio upload.
- `realtime_audio_send_started`, `realtime_first_delta_ms`, `realtime_final_ms`, and `realtime_transcript_text_present` were not reached.
- No production STT was enabled.
- No business dialog state was changed.

## Validation

Prepared repository validation:

```text
python -m pytest tests/test_realtime_measurement.py tests/test_transcription_integrity.py
python -m py_compile src/ai_secretary/stt/realtime_measurement.py
git diff --check
git status --short
```

Secret scan scope:

```text
rg for OpenAI key-shaped values, real OPENAI_API_KEY assignments, and bearer-token literals.
```

Expected local artifacts that must stay untracked:

```text
data/storage/
node014-server.tar
```

## Acceptance

- Measurement path exists and is safe.
- Normal business dialog remains unchanged.
- Systemd service remains in diagnostic profile.
- Real server measurement is recorded as failed before audio due to OpenAI `unsupported_country_region_territory`.

## Next Recommendation

Open:

```text
NODE-020 / openai-realtime-supported-region-gateway-proxy
```

Goal:

Design and test a supported-region gateway/proxy for OpenAI Realtime transcription while keeping:

- The Asterisk server in colocated RTP mode.
- The real `OPENAI_API_KEY` off the Asterisk server as the production plan.
- `ai-secretary-ari.service` in the safe diagnostic profile.
- Business dialog behavior unchanged until gateway measurement passes.
