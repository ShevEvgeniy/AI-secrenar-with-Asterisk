# NODE-024 Design Production Gateway STT Integration Boundary

## Status

CLOSED as design-only production integration boundary.

NODE-024 defines where future gateway-backed STT may connect to the business dialog, which feature flags and safety gates are required, and how failures must fall back without changing caller-facing behavior.

This node did not implement a gateway STT adapter, did not change runtime configuration, did not modify live servers, did not start the Kamatera gateway, and did not enable gateway STT in business dialog.

## Goal

Create a production integration boundary design for future gateway-backed STT in the business dialog after NODE-023 proved that the Kamatera USA gateway can reach OpenAI Realtime and can be reached from the Asterisk server.

This node explicitly preserves:

- NODE-014 `snoop_external_media_rtp` RTP topology.
- NODE-016 diagnostic isolation.
- NODE-018 `ai-secretary-ari.service` diagnostic-safe runtime profile.
- Existing PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, and Russian-only caller-facing contracts.
- Gateway-only `OPENAI_API_KEY`.
- Transcript text redaction by default.

## Repository Inspection

Base state:

```text
aaf8433 Record NODE-023 Kamatera gateway live measurement
```

Current branch:

```text
feat/node-024-design-production-gateway-stt-integration-boundary
```

Inspected:

```text
src/ai_secretary/telephony/ari_app.py
src/ai_secretary/stt/live_streaming.py
src/ai_secretary/stt/realtime_whisper.py
src/ai_secretary/stt/realtime_measurement.py
src/ai_secretary/stt/realtime_gateway.py
deploy/examples/systemd/ari-app.env.example
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
docs/stt_gateway_protocol.md
docs/nodes/NODE-016-dialog-isolated-rtp-diagnostics-and-server-stt-measurement.md
docs/nodes/NODE-020-openai-realtime-supported-region-gateway-proxy.md
docs/nodes/NODE-021-supported-region-gateway-minimal-realtime-measurement.md
docs/nodes/NODE-022-deploy-supported-region-gateway-and-run-live-measurement.md
docs/nodes/NODE-023-deploy-kamatera-usa-gateway-and-run-live-measurement.md
```

Observed local untracked artifacts and left untouched:

```text
data/storage/
node014-server.tar
```

## NODE-023 Baseline

NODE-023 proved:

```text
gateway_host=Kamatera USA / New York 2
gateway_public_ip=45.61.48.199
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=6
transcript_present=false
transcript_text_logged=false
business_dialog_changed=false
systemd_profile_changed=false
```

The gateway process was stopped after smoke. The gateway host retains code and host-only secrets, but port `8080` is not listening and no gateway systemd service is installed.

Current safe Asterisk-side runtime baseline remains:

```text
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY absent from Asterisk process environment
```

## Production Integration Boundary

Future gateway-backed STT may connect to business dialog only at the transcript-source boundary, after RTP/PCM capture and before `apply_turn(...)` receives text for dialog state transition.

Allowed future shape:

```text
Asterisk caller channel
  -> existing ari_app prompt/record/live RTP capture boundary
  -> NODE-014 snoop_external_media_rtp PCM path
  -> gateway STT adapter
  -> supported-region gateway
  -> OpenAI Realtime transcription
  -> validated transcript candidate
  -> existing dialog apply_turn(...)
```

The adapter must behave like another STT provider that returns a bounded transcript candidate plus structured metadata. It must not bypass dialog state policies or directly trigger transfer/callback/SAFE_FINISH.

Out of scope for the adapter:

- Choosing transfer targets.
- Marking required fields complete without `apply_turn(...)`.
- Changing PHONE or PHONE_CONFIRM flow.
- Emitting caller-facing language other than the existing Russian prompts.
- Persisting raw transcript text outside existing transcript artifact rules.
- Owning `OPENAI_API_KEY`.

## Required Feature Flags

Gateway-backed business-dialog STT must require all of these conditions before a transcript can drive `apply_turn(...)`:

```text
STT_LIVE_STREAMING_ENABLED=true
STT_LIVE_STREAMING_PROVIDER=gateway_realtime
STT_LIVE_OPENAI_DISABLED=true
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
STT_GATEWAY_URL=<secret/runtime config>
STT_GATEWAY_TOKEN=<secret/runtime config>
STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false unless explicitly replaced by gateway-specific gating
```

Default and template-safe values must remain:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

`OPENAI_API_KEY` must not be required, read, or present on the Asterisk server for the gateway-backed path.

## Stage Scope

Initial gateway-backed dialog use may be considered only for:

```text
ISSUE
NAME
CITY
```

PHONE remains excluded by default because the current conservative PHONE/PHONE_CONFIRM contract is already specialized for digit safety.

Gateway STT must not weaken:

- PHONE digit parsing and confirmation.
- PHONE_CONFIRM fast path and positive-confirmation requirement.
- CITY plausibility validation and Russian/region-anchor checks.
- Mandatory data gate before live transfer.
- After-hours callback collection.
- SAFE_FINISH terminal/non-transfer behavior.

## Timeout Policy

Future implementation defaults:

```text
gateway_connect_timeout_seconds=2
gateway_first_transcript_timeout_seconds=5
gateway_final_transcript_timeout_seconds=8
gateway_total_turn_timeout_seconds=10
gateway_close_timeout_seconds=2
```

Timeouts are stage budgets. They must not extend caller dead air beyond the current stage recording/playback contours without a separate latency acceptance node.

On timeout:

- Emit a structured event.
- Mark the gateway transcript candidate as rejected.
- Fall back to the current deterministic prompt/retry path or configured batch STT fallback.
- Do not increment business retry counters more than the existing no-transcript behavior would.
- Do not trigger transfer, callback, or SAFE_FINISH from the timeout itself.

## Retry Policy

Retries must be bounded and class-aware:

| Condition | Retry |
| --- | --- |
| Missing/invalid gateway URL or token | No retry |
| Gateway auth failed | No retry |
| Gateway unreachable/connect timeout | At most one retry only if it fits the stage budget |
| Gateway request timeout | No immediate retry unless stage budget remains and retry is explicitly enabled |
| OpenAI regional rejection | No retry |
| OpenAI auth failed | No retry |
| OpenAI rate limit | No retry in caller path by default |
| OpenAI transient/network error | At most one retry only if it fits the stage budget |
| Empty transcript | No transport retry; evaluate as unusable transcript |
| Low-quality transcript | No transport retry; fall back to deterministic prompt/retry behavior |

Retries must not replay caller-facing prompts or restart the dialog stage by themselves. They are transport-level only.

## Fallback Behavior

If gateway STT is unavailable, rejected, timed out, or disabled:

- Preserve current dialog behavior.
- Use the existing deterministic prompt/retry path.
- Use configured batch STT fallback only if already allowed by the current stage policy.
- Never fabricate transcript text.
- Keep required-field and confirmation gates unchanged.
- Keep transfer/callback/after-hours/SAFE_FINISH contracts unchanged.

Gateway failure is an STT-provider outcome, not a business intent.

## Auth Failure Behavior

If gateway auth fails:

```text
event=gateway_stt_auth_failed
status=fail
retry=false
dialog_transcript_used=false
```

Required behavior:

- Do not expose the token or full auth header.
- Do not retry with the same token inside the caller path.
- Do not ask the caller to repeat because of an infrastructure auth failure unless the normal fallback path would do so.
- Raise operator-visible structured diagnostics.
- Preserve current deterministic fallback behavior.

## Empty Transcript Behavior

If OpenAI Realtime succeeds but transcript is absent:

```text
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
transcript_present=false
dialog_transcript_used=false
fallback_reason=openai_transcription_empty
```

Required behavior:

- Treat as unusable STT, not as caller silence unless stage policy already maps empty STT that way.
- Do not pass an empty gateway transcript into `apply_turn(...)` as a success.
- Preserve existing retry/no-transcript behavior.
- Emit structured metrics so operators can distinguish network success from transcription absence.

## Transcript Quality Gate

A gateway transcript may drive dialog only if all gates pass:

- Non-empty normalized text.
- Language/character sanity compatible with Russian caller-facing flow for ISSUE/NAME/CITY.
- Stage-specific validation passes where it exists, especially CITY.
- Confidence/quality metadata is either acceptable or absent with a conservative fallback policy.
- Transcript is within configured length bounds for the stage.
- No redaction failure or token/key leak is detected in metadata.

If confidence/quality is insufficient:

- Reject the transcript candidate.
- Emit `gateway_stt_transcript_rejected`.
- Preserve deterministic retry/fallback behavior.
- Do not advance required fields.

## Logging Policy

Default logs may include:

- `call_id`
- `stage`
- `turn_idx`
- `request_id`
- `gateway_region`
- model
- provider
- durations and timeout buckets
- bytes/chunks/sample rate
- transcript presence
- transcript length
- quality decision
- fallback reason
- error class/code

Default logs must not include:

- `OPENAI_API_KEY`
- `GATEWAY_TOKEN`
- `STT_GATEWAY_TOKEN`
- Authorization headers
- Raw audio bytes
- Base64 audio
- Raw transcript text
- Root passwords
- SSH private keys

Transcript text may be recorded only under an explicit separate debug flag, must be off by default, and must be covered by a redaction review before production use.

## Redaction Policy

Structured events must redact:

- Gateway token and auth headers.
- OpenAI key and provider headers.
- Phone numbers unless using existing approved phone logging rules.
- Full transcript text by default.
- Raw audio and base64 audio.
- Provider error bodies that may echo request content.

Recommended transcript metadata fields:

```text
text_present=true|false
text_length_chars=<int>
text_sha256=<optional debug-safe hash>
text_logged=false
redaction_applied=true
```

## Required Metrics And Events

Before production enablement, future implementation must emit structured events or metrics for:

```text
gateway_stt_config_resolved
gateway_stt_disabled
gateway_stt_request_started
gateway_stt_auth_failed
gateway_stt_gateway_unavailable
gateway_stt_openai_session_created
gateway_stt_audio_started
gateway_stt_first_delta
gateway_stt_final
gateway_stt_empty_transcript
gateway_stt_transcript_candidate
gateway_stt_transcript_accepted
gateway_stt_transcript_rejected
gateway_stt_fallback
gateway_stt_timeout
gateway_stt_redaction_applied
gateway_stt_dialog_applied
```

Required dimensions:

```text
call_id
stage
turn_idx
provider
gateway_region
gateway_request_id
model
audio_duration_ms
audio_bytes
chunks_sent
first_delta_ms
final_ms
total_ms
error_type
error_code
fallback_reason
transcript_text_present
transcript_text_logged
dialog_transcript_used
```

## Rollback Procedure

Rollback must be one environment-only change on the Asterisk side:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

Then restart only after an explicit future implementation node authorizes service changes.

Gateway-side rollback:

- Stop the gateway service/process.
- Keep firewall allowlist restricted to the Asterisk server.
- Rotate `GATEWAY_TOKEN` if an auth failure or leak is suspected.
- Do not move `OPENAI_API_KEY` to the Asterisk server.

## Acceptance Gates For NODE-025

NODE-025 may implement a controlled, disabled-by-default gateway STT adapter only if it satisfies:

- No `OPENAI_API_KEY` on the Asterisk server.
- Gateway token read only from secret runtime env, never committed.
- Adapter disabled by default.
- Dialog transcript use disabled by default.
- Transcript text not logged by default.
- Russian-only caller-facing behavior preserved.
- PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, and SAFE_FINISH contracts preserved.
- Fallback to current deterministic prompts when gateway STT is unavailable or rejected.
- NODE-016 diagnostic isolation preserved.
- NODE-014 RTP topology unchanged.
- Gateway auth failure does not alter business dialog.
- OpenAI success with absent transcript does not advance business dialog.
- Low-quality transcript does not advance business dialog.
- Metrics/events above are present before enablement.
- Focused tests prove redaction, disabled defaults, fallback behavior, and no Asterisk-side OpenAI key dependency.

## NODE-024 Result

```text
node_status=design closed
production_gateway_stt_enabled=false
business_dialog_changed=false
systemd_profile_changed=false
live_server_changed=false
openai_key_on_asterisk=false
gateway_secret_committed=false
config_scaffolding_added=false
runtime_behavior_changed=false
next_node_recommendation=NODE-025 controlled disabled-by-default gateway STT adapter implementation
```

## Validation

NODE-024 is docs-only. No code or config parsing changed, so the focused realtime pytest command was not required.

Required validation:

```text
git diff --check
git status --short
git diff --cached
git diff
```

Secret/artifact rules to preserve:

- Do not commit `OPENAI_API_KEY`.
- Do not commit real `GATEWAY_TOKEN`.
- Do not commit root password.
- Do not commit SSH private keys.
- Do not commit `.env` files with real secrets.
- Do not commit `data/storage/`.
- Do not commit `node014-server.tar`.

## Acceptance

- Future production integration boundary is defined.
- Required feature flags are explicit and disabled by default.
- Timeout, retry, fallback, auth failure, empty transcript, and low-quality transcript behavior are specified.
- Transcript logging and redaction policy are specified.
- Required structured events/metrics are specified.
- Rollback procedure is specified.
- NODE-025 implementation gates are defined.
- Business dialog remains unchanged.
- `ai-secretary-ari.service` remains unchanged.
- No live servers were modified.
- Gateway STT remains disabled.

## Next Recommendation

Open:

```text
NODE-025 / controlled-disabled-by-default-gateway-stt-adapter-implementation
```

Recommended scope:

- Implement a gateway STT adapter behind disabled-by-default flags.
- Keep `OPENAI_API_KEY` gateway-only.
- Keep transcript use for dialog disabled by default.
- Add focused tests for config defaults, redaction, auth failure fallback, empty transcript fallback, low-quality transcript rejection, and preservation of existing business contracts.
- Do not change live servers or production service profile until a later explicit enablement node.
