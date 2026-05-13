# NODE-021 Supported-Region Gateway Minimal Realtime Measurement

## Status

CLOSED as prepared gateway measurement path. No supported-region host was available during this node, so no live OpenAI Realtime result is fabricated.

Next live step:

```text
NODE-022 / deploy-supported-region-gateway-and-run-live-measurement
```

## Goal

Implement a minimal, isolated gateway measurement path for OpenAI Realtime transcription after NODE-019 proved direct Asterisk-server egress is blocked by `unsupported_country_region_territory`.

This node does not:

- Switch normal business calls to gateway STT.
- Change `ai-secretary-ari.service`.
- Put `OPENAI_API_KEY` on the Asterisk server.
- Change PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, Russian-only caller-facing behavior, NODE-016 diagnostic isolation, or NODE-014 RTP topology.

## Official OpenAI Docs Recheck

Official OpenAI docs were rechecked on 2026-05-13 using OpenAI docs sources before documenting API details.

Implementation-relevant facts:

- Realtime transcription is for live speech-to-text without a spoken assistant response.
- The Realtime transcription guide documents WebSocket use for server-side audio pipelines.
- The documented transcription session shape uses `type: "transcription"`, `audio.input.format.type=audio/pcm`, and `audio.input.format.rate=24000`.
- For `audio/pcm`, OpenAI documents 24 kHz mono PCM.
- `gpt-realtime-whisper` is documented for streaming transcription with transcript deltas.
- Audio is sent as base64 `input_audio_buffer.append`; with turn detection disabled, `input_audio_buffer.commit` starts transcription for the buffered audio.
- Transcript events include `conversation.item.input_audio_transcription.delta` and `conversation.item.input_audio_transcription.completed`.
- The WebSocket guide says server-to-server Realtime integrations can authenticate with a standard API key on a secure backend server.
- The Speech-to-text guide remains the bounded file/request-response fallback path, while live media streams should use Realtime transcription.
- GPT Realtime Whisper pricing is duration-based rather than text-token-based.

References:

- https://developers.openai.com/api/docs/guides/realtime-transcription
- https://developers.openai.com/api/docs/guides/realtime-websocket
- https://developers.openai.com/api/docs/guides/speech-to-text
- https://developers.openai.com/api/docs/models/gpt-realtime-whisper
- https://developers.openai.com/api/docs/guides/realtime-costs

## Implementation

Added gateway skeleton:

```text
src/ai_secretary/stt/realtime_gateway.py
```

Gateway behavior:

- Exposes `POST /v1/stt/realtime-measurement`.
- Accepts raw `audio/wav` request body for the minimal NODE-021 path.
- Requires `Authorization: Bearer <gateway token>`.
- Reads `OPENAI_API_KEY` only from gateway runtime environment.
- Validates short mono 16-bit PCM WAV at 24 kHz.
- Connects from gateway to OpenAI Realtime WebSocket.
- Sends `session.update`, `input_audio_buffer.append`, and `input_audio_buffer.commit`.
- Returns structured JSON with:
  - `gateway_request_id`
  - `gateway_connection_attempt`
  - `openai_realtime_connection_ok`
  - `openai_session_created`
  - `audio_send_started`
  - `chunks_sent`
  - `first_delta_ms`
  - `final_ms`
  - `transcript_text_present`
  - `error_type`
  - `error_code`
  - `error_message_redacted`
  - `cleanup_done`
- Returns non-2xx structured JSON on hard failure.
- Does not return transcript text by default, even if the client requests it.
- Redacts OpenAI keys, bearer headers, tokens, and likely secret fields.

Added Asterisk-side gateway client mode:

```text
python -m ai_secretary.stt.realtime_measurement --gateway-url ... --gateway-token ... --audio ...
```

Client behavior:

- Does not read or require `OPENAI_API_KEY`.
- Uses `REALTIME_GATEWAY_URL` / `REALTIME_GATEWAY_TOKEN` or explicit CLI args.
- Sends the WAV to the gateway with the gateway bearer token.
- Logs only redacted structured gateway response fields.

## Environment Templates

Gateway host:

```text
OPENAI_API_KEY=<set on gateway only>
GATEWAY_TOKEN=<gateway inbound auth token>
STT_GATEWAY_SERVER_TOKEN=<same token, compatibility alias>
GATEWAY_REGION_LABEL=<safe label, e.g. eu>
OPENAI_REALTIME_MODEL=gpt-realtime-whisper
OPENAI_REALTIME_LANGUAGE=ru
```

Asterisk server one-off measurement client:

```text
REALTIME_GATEWAY_URL=https://gateway.example.com/v1/stt/realtime-measurement
REALTIME_GATEWAY_TOKEN=<gateway inbound auth token>
```

Do not add `OPENAI_API_KEY` to the Asterisk server.

Updated templates:

```text
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
```

## Run Commands

Gateway host, after installing project dependencies and setting gateway env:

```powershell
python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8443
```

Equivalent uvicorn form:

```powershell
uvicorn ai_secretary.stt.realtime_gateway:create_app --factory --host 0.0.0.0 --port 8443
```

Asterisk server one-off measurement:

```powershell
python -m ai_secretary.stt.realtime_measurement --gateway-url https://gateway.example.com/v1/stt/realtime-measurement --gateway-token <gateway-token> --audio /tmp/ai-secretary-node019/realtime_measurement_24k.wav
```

Environment-driven form:

```powershell
$env:REALTIME_GATEWAY_URL='https://gateway.example.com/v1/stt/realtime-measurement'
$env:REALTIME_GATEWAY_TOKEN='<gateway-token>'
python -m ai_secretary.stt.realtime_measurement --audio /tmp/ai-secretary-node019/realtime_measurement_24k.wav
```

## Live Measurement

No supported-region host was available during NODE-021.

Recorded result:

```text
live_gateway_deployed=false
live_openai_realtime_connection_ok=not_run
chunks_sent=not_run
first_delta_ms=not_run
final_ms=not_run
transcript_text_present=not_run
cleanup_done=not_run
```

This is a prepared measurement path only.

## Tests

Added focused tests:

```text
tests/test_realtime_gateway.py
```

Coverage:

- Missing gateway token is rejected.
- Missing gateway-side `OPENAI_API_KEY` fails clearly.
- Secret redaction removes bearer/OpenAI-looking secrets.
- Transcript text is not returned by default.
- Invalid WAV request is rejected.
- OpenAI regional failure maps to structured `openai_region_rejected`.
- Gateway client mode does not require `OPENAI_API_KEY` on the Asterisk side.
- Gateway config reads gateway env vars, not OpenAI key.
- Gateway module has no business dialog imports or side effects.

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_realtime_measurement.py tests\test_realtime_gateway.py
```

Result:

```text
16 passed
```

Syntax checks:

```text
python -c "import ast, pathlib; ast.parse(pathlib.Path('src/ai_secretary/stt/realtime_measurement.py').read_text(encoding='utf-8'))"
python -c "import ast, pathlib; ast.parse(pathlib.Path('src/ai_secretary/stt/realtime_gateway.py').read_text(encoding='utf-8'))"
```

Result:

```text
syntax ok
```

`python -m py_compile` was attempted first but Windows denied writing into the existing `__pycache__`; AST parse was used for syntax validation without bytecode writes.

## Runtime Boundary

Preserved:

- `ai-secretary-ari.service` unchanged.
- No systemd profile change.
- No production gateway STT flag enabled.
- Business dialog imports are absent from the gateway and client measurement modules.
- NODE-016 diagnostic isolation remains the expected runtime posture.
- NODE-014 RTP topology remains unchanged.

## Acceptance

- Minimal gateway measurement skeleton exists.
- Asterisk-side one-off client can target the gateway without `OPENAI_API_KEY`.
- OpenAI key boundary is enforced by config shape and tests: gateway only.
- Structured success/error JSON is implemented.
- Secrets and transcript text are redacted/omitted by default.
- No live result was fabricated.
- Next live deployment/measurement node is explicit.

## Next Recommendation

Open:

```text
NODE-022 / deploy-supported-region-gateway-and-run-live-measurement
```

Goal:

Deploy the NODE-021 gateway on a supported-region host, set `OPENAI_API_KEY` only on that host, run the Asterisk-side one-off measurement against `/tmp/ai-secretary-node019/realtime_measurement_24k.wav` or equivalent, and record the real connection/result metrics.
