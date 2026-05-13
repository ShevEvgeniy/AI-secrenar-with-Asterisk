# NODE-019 Production OpenAI Realtime Egress And STT Measurement

## Status

PREPARED. The safe one-off OpenAI Realtime transcription measurement path exists, but the real server measurement has not been run yet.

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

Not run yet.

When authorized later, use a temporary shell environment only:

```bash
read -rsp "OPENAI_API_KEY: " OPENAI_API_KEY; echo
export OPENAI_API_KEY
PYTHONPATH=src python -m ai_secretary.stt.realtime_measurement --audio <server-local-wav>
unset OPENAI_API_KEY
```

Do not write the real key into:

```text
/etc/ai-secretary/ari-app.env
```

Do not restart or reconfigure:

```text
ai-secretary-ari.service
```

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
- Real server measurement is explicitly recorded as not run.
