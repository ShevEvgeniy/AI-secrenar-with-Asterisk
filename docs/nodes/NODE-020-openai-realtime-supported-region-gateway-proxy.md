# NODE-020 OpenAI Realtime Supported-Region Gateway Proxy

## Status

CLOSED as design and prepared measurement node.

Direct OpenAI Realtime egress from the current Asterisk/`ari_app` server is blocked by OpenAI regional policy. NODE-020 defines a supported-region gateway/proxy path for the next measurement without enabling production STT or changing business dialog behavior.

## Goal

Design and prepare a supported-region OpenAI Realtime gateway/proxy path for STT measurement while preserving:

- Colocated Asterisk server RTP handling.
- NODE-014 `snoop_external_media_rtp` topology.
- NODE-016 diagnostic isolation.
- NODE-018 systemd/autostart diagnostic runtime profile.
- Existing business dialog, transfer, callback, after-hours, PHONE, PHONE_CONFIRM, CITY, SAFE_FINISH, and Russian-only caller-facing contracts.

This node does not deploy a gateway and does not switch normal calls to OpenAI-backed STT.

## Background

NODE-019 prepared and ran a direct OpenAI Realtime measurement from server `92.118.85.117`.

Observed result:

```text
endpoint=api.openai.com/v1/realtime
status_code=403 Forbidden
openai_error_code=unsupported_country_region_territory
chunks_sent=0
```

Interpretation:

- The server had enough DNS/network reachability to receive an OpenAI rejection.
- The rejection happened before session creation and before audio upload.
- Direct OpenAI Realtime from this server is not viable.
- A supported-region gateway/proxy is required for Realtime measurement.

## Official OpenAI Docs Recheck

Official OpenAI docs were rechecked on 2026-05-13 using OpenAI sources only.

Current implementation-relevant facts:

- Realtime transcription is intended for live speech-to-text without a spoken assistant response.
- Realtime transcription sessions can be used over WebSocket for server-side audio pipelines.
- The current Realtime transcription guide documents `type: "transcription"` sessions with `audio.input.format.type=audio/pcm` and `audio.input.format.rate=24000`.
- For `audio/pcm`, OpenAI documents 24 kHz mono PCM.
- The current live transcription model named in the guide is `gpt-realtime-whisper`.
- Audio chunks are sent as `input_audio_buffer.append` with base64 PCM audio.
- If turn detection is disabled, `input_audio_buffer.commit` starts transcription for the buffered audio.
- Transcript events include `conversation.item.input_audio_transcription.delta` and `conversation.item.input_audio_transcription.completed`; final event ordering across different turns is not guaranteed, so `item_id` must be used for reconciliation.
- The WebSocket guide positions WebSocket as suitable for server-to-server Realtime integrations and says a standard API key can authenticate from a secure backend server.
- The Speech-to-text guide keeps Audio API transcriptions as the bounded file/request-response path and points live media streams to Realtime transcription.
- File-based Audio API transcriptions support `gpt-4o-transcribe`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe-diarize`, and `whisper-1`; file uploads are limited to 25 MB and include `wav` among supported formats.
- Current OpenAI data-residency docs list `/v1/realtime/transcription_sessions` with `gpt-realtime-whisper` support in US and EU.
- Current public pricing lists GPT-Realtime-Whisper at `$0.017 per minute / $0.00028 per second`.

References:

- Realtime transcription: https://developers.openai.com/api/docs/guides/realtime-transcription
- Realtime WebSocket: https://developers.openai.com/api/docs/guides/realtime-websocket
- Speech to text: https://developers.openai.com/api/docs/guides/speech-to-text
- Data residency / regional endpoint support: https://developers.openai.com/api/docs/guides/your-data
- API pricing: https://openai.com/api/pricing/

## Architecture Decision

Use a supported-region gateway as the OpenAI-owning boundary.

Recommended first proof:

```text
Asterisk server
  -> short WAV upload over HTTPS
  -> supported-region gateway
  -> OpenAI Realtime transcription over WSS
  -> structured metrics and redacted result flags
  -> Asterisk server
```

Why this first:

- It is the smallest safe proof after NODE-019.
- It keeps RTP capture colocated with Asterisk.
- It does not require production streaming relay semantics yet.
- It keeps `OPENAI_API_KEY` off the Asterisk server.
- It returns measurement metrics without feeding transcripts into the business dialog.

Recommended later shape:

```text
Asterisk server
  -> authenticated WebSocket to gateway
  -> 24 kHz mono PCM chunks
  -> gateway WebSocket to OpenAI Realtime
  -> transcript deltas/finals and metrics back to ari_app
```

The later streaming relay must remain feature-flagged and dialog-isolated until transcript quality, failure handling, and fallback behavior are accepted.

## Gateway Placement

Run the gateway on a host in an OpenAI-supported Realtime region. Based on the current official data-residency endpoint support table, US or EU are appropriate candidates for `gpt-realtime-whisper` Realtime transcription.

Operational preference:

1. A small Linux VM in EU or US, nearest acceptable legal/network location to the Asterisk server.
2. HTTPS/WSS only; no inbound public access from arbitrary clients.
3. Firewall allowlist the Asterisk server egress IP where possible.
4. Store gateway secrets outside git in a root-owned env file or secret manager.

The Asterisk server remains the owner of RTP and ARI. The gateway is only an OpenAI egress and measurement boundary.

## Options Evaluated

### A. Minimal Gateway

The Asterisk server sends preformatted 24 kHz mono PCM chunks or a short WAV to the gateway. The gateway owns `OPENAI_API_KEY`, connects to OpenAI Realtime, and returns structured results.

Decision: accepted as the target abstraction. Use HTTP one-shot first, then reuse the same schema for streaming.

### B. WebSocket Relay

The Asterisk server opens a WebSocket to the gateway. The gateway opens a WebSocket to OpenAI Realtime and relays audio append/commit plus transcript/error events.

Decision: correct production-adjacent design, but not first proof. Implement after the one-shot gateway proves regional OpenAI access and secret isolation.

### C. HTTP One-Shot Measurement Gateway

The Asterisk server uploads a short WAV. The gateway validates audio, runs a Realtime transcription measurement, and returns metrics.

Decision: recommended NODE-021 proof. This mirrors NODE-019 measurement while moving only the OpenAI call to a supported region.

### D. Production Relay Later

The gateway streams live chunks from `ari_app` to OpenAI and transcript deltas/finals back to `ari_app`.

Decision: defer until after NODE-021. Production relay must not drive business dialog until a later acceptance node explicitly enables it.

## Gateway Protocol

Detailed protocol: `docs/stt_gateway_protocol.md`.

Summary:

- `POST /v1/stt/realtime-measurement` for NODE-021 one-shot proof.
- Optional later `GET /v1/stt/realtime-relay` WebSocket for streaming.
- Asterisk authenticates to gateway with `Authorization: Bearer <gateway token>`.
- Gateway authenticates to OpenAI using `OPENAI_API_KEY` stored only on gateway.
- The Asterisk server never receives or stores the OpenAI key.
- Audio boundary for the first proof is mono 16-bit PCM WAV at 24 kHz.
- Responses return event names, timing, chunk counts, byte counts, error class/code, and transcript presence flags.
- Responses do not return transcript text by default.

## Secret Boundary

Gateway-only:

```text
OPENAI_API_KEY
GATEWAY_SERVER_TOKEN
```

Asterisk server only:

```text
STT_GATEWAY_URL
STT_GATEWAY_TOKEN
```

Rules:

- Do not put `OPENAI_API_KEY` in `/etc/ai-secretary/ari-app.env` on the Asterisk server as the production plan.
- Do not pass the OpenAI key through CLI arguments or request payloads.
- Do not log bearer tokens, OpenAI keys, transcript text, raw audio bytes, base64 audio, or full request headers.
- Do not commit real gateway tokens.

## Failure Behavior

Gateway measurement failures must return structured errors and must not affect business dialog:

- `gateway_auth_failed`
- `gateway_audio_invalid`
- `gateway_timeout`
- `openai_region_rejected`
- `openai_auth_failed`
- `openai_rate_limited`
- `openai_transient`
- `openai_transcription_empty`
- `gateway_internal_error`

On the Asterisk server, NODE-021 measurement must remain outside normal dialog decisions. Failed gateway measurement may be logged as diagnostics, but must not:

- Increment business retry counters.
- Trigger `SAFE_FINISH`.
- Trigger transfer or callback.
- Change PHONE or PHONE_CONFIRM behavior.
- Change CITY validation.
- Change Russian-only caller-facing behavior.

## Logging And Redaction

Allowed:

- `request_id`, `call_id`, `stage`, duration, byte count, chunk count, sample rate, channel count, model, gateway region label, event names, first delta timing, final timing, error type/code, transcript text presence.

Not allowed:

- OpenAI API key.
- Gateway token.
- Authorization headers.
- Raw transcript text by default.
- Raw audio or base64 audio.
- Caller phone number unless already handled by existing project logging rules.

NODE-021 should include tests for redaction before any skeleton code is used for real measurement.

## Env Templates

Added secret-free templates:

```text
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
```

The gateway template contains only placeholders for `OPENAI_API_KEY` and gateway auth. The Asterisk template contains only gateway URL/token placeholders and explicitly keeps OpenAI disabled for the local service profile.

## Runtime Boundary

Do not change:

- `/etc/ai-secretary/ari-app.env` on the server.
- `ai-secretary-ari.service`.
- `STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only`.
- `STT_LIVE_OPENAI_DISABLED=true`.
- `STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true`.
- `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false`.
- PHONE behavior.
- PHONE_CONFIRM behavior.
- CITY validation.
- Transfer, callback, after-hours, or SAFE_FINISH contracts.
- Russian-only caller-facing invariant.
- NODE-014 RTP topology.

## Smallest Safe NODE-021 Proof

Implement and deploy a minimal supported-region HTTP gateway:

1. Gateway host in US or EU.
2. `POST /v1/stt/realtime-measurement`.
3. Bearer-token auth from the Asterisk server.
4. Gateway-side `OPENAI_API_KEY` only.
5. Upload one short 24 kHz mono PCM WAV.
6. Gateway runs OpenAI Realtime transcription measurement using `gpt-realtime-whisper`.
7. Gateway returns structured metrics and redacted transcript presence, not transcript text by default.
8. Asterisk-side caller remains in diagnostic-only profile.
9. No normal business call uses gateway STT by default.

## Validation

NODE-020 is docs/templates only. No runtime code was changed.

Required validation:

```text
git diff --check
secret scan for OpenAI key-shaped values and real gateway-token leaks
git status --short
```

Expected untracked artifacts that must stay out of git:

```text
data/storage/
node014-server.tar
```

## Acceptance

- NODE-020 records why direct OpenAI egress failed and why a gateway/proxy is required.
- Gateway/proxy architecture is specified enough to implement next.
- Secret boundary is clear: OpenAI key lives on gateway, not on the Asterisk server.
- Business dialog remains unchanged.
- NODE-016 diagnostic isolation and NODE-018 systemd diagnostic profile remain intact.
- Next node is clearly defined.

## Next Recommendation

Open:

```text
NODE-021 / supported-region-gateway-minimal-realtime-measurement
```

Goal:

Implement and run the one-shot supported-region gateway measurement, then record whether OpenAI Realtime transcription works from the gateway host with the current short WAV measurement sample.
