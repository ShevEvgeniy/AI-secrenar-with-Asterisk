# STT Gateway Protocol

## Purpose

Define the supported-region gateway contract for OpenAI Realtime STT measurement.

The gateway keeps OpenAI secrets and OpenAI network egress off the Asterisk server. The Asterisk server remains colocated with RTP and ARI. The first implementation target is a measurement-only HTTP endpoint; a streaming WebSocket relay can be added later without changing the business dialog by default.

## Non-Goals

- No production STT rollout.
- No normal business dialog integration by default.
- No OpenAI API key on the Asterisk server.
- No transcript text in logs or responses by default.
- No changes to PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, Russian-only caller-facing behavior, NODE-014 RTP topology, or NODE-016 diagnostic isolation.

## Endpoint: One-Shot Realtime Measurement

```text
POST /v1/stt/realtime-measurement
Authorization: Bearer <gateway token>
Content-Type: audio/wav
```

NODE-021 minimal skeleton sends the WAV as the raw request body with optional query parameters:

| Field | Required | Description |
| --- | --- | --- |
| raw body | yes | Short WAV file. Required first-proof format: PCM signed 16-bit, 24 kHz, mono. |
| `language` | no | Query parameter. Use `ru` for current Russian telephony measurement. |
| `return_transcript` | no | Query parameter. Default `false`. Must require explicit gateway policy to allow `true`. |
| `X-Request-ID` | no | Client-generated trace id. Gateway generates one if absent. |

Future multipart form fields may add `call_id`, `stage`, and `audio` without changing the response contract.

Default limits:

```text
max_audio_duration_seconds=15
max_audio_bytes=1048576
gateway_request_timeout_seconds=45
openai_realtime_timeout_seconds=30
```

The gateway should reject audio that exceeds the configured limit before contacting OpenAI.

## One-Shot Success Response

NODE-021 implementation response is intentionally flat so the Asterisk-side
measurement client can log one compact JSON object:

```json
{
  "ok": true,
  "gateway_request_id": "gw_20260513_abcdef",
  "gateway_connection_attempt": true,
  "gateway_region": "eu",
  "model": "gpt-realtime-whisper",
  "openai_realtime_connection_ok": true,
  "openai_session_created": true,
  "audio_send_started": true,
  "chunks_sent": 28,
  "first_delta_ms": 820,
  "final_ms": 1420,
  "transcript_text_present": true,
  "error_type": null,
  "error_code": null,
  "error_message_redacted": null,
  "cleanup_done": true
}
```

Legacy/expanded protocol shape retained for later gateway versions:

```json
{
  "ok": true,
  "request_id": "gw_20260513_abcdef",
  "gateway_region": "eu",
  "model": "gpt-realtime-whisper",
  "audio": {
    "format": "wav",
    "encoding": "pcm_s16le",
    "sample_rate_hz": 24000,
    "channels": 1,
    "duration_ms": 5510,
    "bytes_received": 264600,
    "chunks_sent": 28
  },
  "events": {
    "openai_connection_attempt": true,
    "openai_connection_ok": true,
    "session_created": true,
    "session_updated": true,
    "audio_send_started": true,
    "first_delta_ms": 820,
    "final_ms": 1420,
    "completed": true
  },
  "transcript": {
    "text_present": true,
    "text_returned": false,
    "length_chars": 42,
    "item_id": "item_003"
  },
  "error": null
}
```

If `return_transcript=true` is explicitly enabled by gateway policy, the gateway may add `transcript.text`. This must remain disabled for default measurement and default logging.

## Redacted Transcript-Event Diagnostics

Gateway and Asterisk-side smoke reports may include redacted transcript-event diagnostics. These fields are safe for logs and node closeouts because they do not include transcript text, token values, raw secret env output, audio, or large raw logs.

Preferred flat fields:

```text
openai_event_type_counts
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
diagnostic_propagation_gap
diagnostic_classification
```

`transcript_text_length_bucket` must be one of:

```text
zero
nonzero_redacted
unknown
```

`diagnostic_classification` may be one of:

```text
no_event_counts_available
no_transcript_event_observed
transcript_event_observed_empty_or_no_text
transcript_bearing_event_observed_text_redacted
timeout_after_audio_commit
openai_error_event_observed
diagnostic_propagation_gap
unknown
```

Default Gateway and smoke-helper behavior must not return or log transcript text. If a transcript-bearing OpenAI event contains text, reports may set `transcript_text_present=true` and `transcript_text_length_bucket=nonzero_redacted` only.

## One-Shot Error Response

NODE-021 implementation error response:

```json
{
  "ok": false,
  "gateway_request_id": "gw_20260513_abcdef",
  "gateway_connection_attempt": true,
  "gateway_region": "eu",
  "model": "gpt-realtime-whisper",
  "openai_realtime_connection_ok": false,
  "openai_session_created": false,
  "audio_send_started": false,
  "chunks_sent": 0,
  "first_delta_ms": null,
  "final_ms": null,
  "transcript_text_present": false,
  "error_type": "RuntimeError",
  "error_code": "openai_region_rejected",
  "error_message_redacted": "OpenAI rejected the gateway region",
  "cleanup_done": true
}
```

Legacy/expanded protocol shape retained for later gateway versions:

```json
{
  "ok": false,
  "request_id": "gw_20260513_abcdef",
  "gateway_region": "eu",
  "model": "gpt-realtime-whisper",
  "audio": {
    "format": "wav",
    "encoding": "pcm_s16le",
    "sample_rate_hz": 24000,
    "channels": 1,
    "duration_ms": 5510,
    "bytes_received": 264600,
    "chunks_sent": 0
  },
  "events": {
    "openai_connection_attempt": true,
    "openai_connection_ok": false,
    "session_created": false,
    "session_updated": false,
    "audio_send_started": false,
    "first_delta_ms": null,
    "final_ms": null,
    "completed": false
  },
  "transcript": {
    "text_present": false,
    "text_returned": false,
    "length_chars": 0,
    "item_id": null
  },
  "error": {
    "code": "openai_region_rejected",
    "http_status": 403,
    "provider_code": "unsupported_country_region_territory",
    "retryable": false,
    "message": "OpenAI rejected the gateway region"
  }
}
```

## Error Codes

| Code | Retryable | Meaning |
| --- | --- | --- |
| `gateway_auth_failed` | false | Missing or invalid Asterisk-to-gateway token. |
| `gateway_audio_invalid` | false | Unsupported audio format, duration, size, channel count, or sample rate. |
| `gateway_timeout` | true | Gateway request deadline reached before provider completion. |
| `openai_region_rejected` | false | OpenAI returned regional unsupported error. |
| `openai_auth_failed` | false | Gateway OpenAI key rejected. |
| `openai_rate_limited` | true | Provider rate limit response. |
| `openai_transient` | true | Provider/network transient failure. |
| `openai_transcription_empty` | false | Provider completed without usable transcript. |
| `gateway_internal_error` | true | Gateway bug or unexpected exception. |

## Authentication Model

The Asterisk server authenticates to the gateway:

```text
Authorization: Bearer <STT_GATEWAY_TOKEN>
```

Gateway verification rules:

- Use constant-time comparison.
- Reject missing, malformed, or repeated `Authorization` headers.
- Return `401` for missing/invalid token.
- Do not log the header value.
- Prefer firewall IP allowlisting in addition to bearer auth.
- Rotate tokens by allowing two active token hashes during a planned rotation window.

The gateway authenticates to OpenAI:

```text
Authorization: Bearer <OPENAI_API_KEY>
```

The OpenAI key is read only from gateway-side environment/secret storage.

## Secret Handling

Gateway environment:

```text
OPENAI_API_KEY=replace-with-real-openai-key-on-gateway-only
GATEWAY_TOKEN=replace-with-random-gateway-token
STT_GATEWAY_SERVER_TOKEN=replace-with-random-gateway-token
```

Asterisk server environment:

```text
STT_GATEWAY_URL=https://gateway.example.com
STT_GATEWAY_TOKEN=replace-with-random-gateway-token
REALTIME_GATEWAY_URL=https://gateway.example.com/v1/stt/realtime-measurement
REALTIME_GATEWAY_TOKEN=replace-with-random-gateway-token
```

Rules:

- Never store `OPENAI_API_KEY` on the Asterisk server as the production plan.
- Never commit real tokens or keys.
- Never accept OpenAI key as a request parameter.
- Never return OpenAI key, gateway token, or full request headers in errors.

## Logging And Redaction

Gateway logs may include:

- `request_id`
- `call_id`
- `stage`
- `gateway_region`
- `model`
- sample rate, channels, duration, bytes, chunks
- event booleans
- timing metrics
- error code/provider code
- transcript text presence and length

Gateway logs must redact or omit:

- `Authorization`
- `OPENAI_API_KEY`
- `STT_GATEWAY_SERVER_TOKEN`
- `STT_GATEWAY_TOKEN`
- raw transcript text by default
- raw audio bytes
- base64 audio
- OpenAI request/response headers

Recommended replacement:

```text
[REDACTED]
```

## Timeout, Retry, And Fallback

Client timeout:

```text
45 seconds for one-shot measurement
```

Gateway to OpenAI timeout:

```text
30 seconds for Realtime measurement
```

Retry policy:

- Do not retry invalid audio, invalid auth, or regional rejection.
- Retry `openai_rate_limited` only if the gateway has explicit backoff policy and the measurement caller can tolerate delay.
- Retry transient gateway/OpenAI network failures at most once in NODE-021, then return a structured error.

Asterisk-side fallback:

- For NODE-021, log only. Do not drive business dialog.
- Later production relay may fall back to batch STT only behind an explicit feature flag.
- Never fabricate transcript text.

## Metrics

Required gateway metrics:

```text
gateway_requests_total
gateway_auth_failures_total
gateway_audio_invalid_total
gateway_openai_connection_attempts_total
gateway_openai_connection_failures_total
gateway_openai_region_rejections_total
gateway_openai_rate_limited_total
gateway_transcription_completed_total
gateway_transcription_empty_total
gateway_first_delta_ms
gateway_final_ms
gateway_audio_duration_ms
gateway_audio_bytes
gateway_audio_chunks_sent
```

The first implementation may emit JSON log events instead of a metrics backend, but event names and fields should map cleanly to these counters/timers.

## Optional Streaming Relay

Later endpoint:

```text
GET /v1/stt/realtime-relay
Authorization: Bearer <gateway token>
Upgrade: websocket
```

Client-to-gateway events:

```json
{
  "type": "measurement.session.start",
  "request_id": "call_123_issue_1",
  "call_id": "1778672473.13",
  "stage": "ISSUE",
  "language": "ru",
  "audio": {
    "encoding": "pcm_s16le",
    "sample_rate_hz": 24000,
    "channels": 1
  },
  "return_transcript": false
}
```

```json
{
  "type": "audio.append",
  "sequence": 1,
  "audio_b64": "..."
}
```

```json
{
  "type": "audio.commit"
}
```

Gateway-to-client events:

```json
{
  "type": "transcript.delta",
  "request_id": "call_123_issue_1",
  "item_id": "item_003",
  "delta_present": true,
  "delta": null,
  "elapsed_ms": 820
}
```

```json
{
  "type": "transcript.completed",
  "request_id": "call_123_issue_1",
  "item_id": "item_003",
  "text_present": true,
  "text": null,
  "length_chars": 42,
  "elapsed_ms": 1420
}
```

```json
{
  "type": "measurement.error",
  "request_id": "call_123_issue_1",
  "code": "openai_transient",
  "retryable": true
}
```

For default diagnostics, transcript content remains `null`; only presence and length are returned.

## Test Requirements For Any Implementation

Add focused tests for:

- Secret redaction.
- Request schema validation.
- WAV format validation.
- Auth header handling.
- OpenAI error mapping.
- Transcript text disabled by default.
- No import or mutation of business dialog state.
- No dependency on `OPENAI_API_KEY` in Asterisk-side client config.

## NODE-021 Implementation Target

Implement only:

- Gateway one-shot endpoint.
- Gateway-side OpenAI Realtime measurement call.
- Asterisk-side measurement client or script.
- Focused tests.
- Server deployment/run notes.

Keep out of scope:

- Streaming relay.
- Normal business dialog integration.
- Production STT enablement.
- Systemd diagnostic profile changes on the Asterisk server.
