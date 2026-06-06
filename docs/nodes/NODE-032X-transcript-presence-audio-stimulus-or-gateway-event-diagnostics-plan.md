# NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan

Status: local diagnostics and planning node.

Branch:

```text
feat/node-032x-transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```

Handoff archive:

```text
docs/handoffs/NODE-032X-transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan-codex-handoff.md
```

## Goal

Explain why NODE-032W did not prove transcript presence despite successful Asterisk-origin Gateway transport/auth/OpenAI Realtime behavior, and define the next safest boundary.

This node is local-only. It performs no live smoke, SSH, helper deploy, token handling, temp env creation, service action, dependency install, reboot, firewall/env/server change, business-dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation.

## Input Truth From NODE-032W

NODE-032W merged via PR #25:

```text
merge_commit=89ae0e32d95858f2ff02a40601f2621a302acf0d
```

NODE-032W proved:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
valid_audio=24000 Hz mono 16-bit PCM WAV
token_values_printed=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
gateway_service_rollback_safe=true
```

NODE-032W did not prove:

```text
transcript_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_quality=true
transcript_text_correctness=true
business_dialog_transcript_use=true
production_autostart=true
dual_channel_caller_bot_recording=true
```

NODE-032W result to preserve:

```text
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
chunks_sent=5
gateway_http_status=200
openai_realtime_from_gateway=ok
```

Interpretation:

```text
transport_auth_openai_realtime_success=true
transcript_presence_success=false
```

Do not describe NODE-032W as transcript-presence success.

## Local Inspection Summary

Inspected local code and docs only:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/asterisk_gateway_helper_bundle.py
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/realtime_gateway.py
tests/test_asterisk_gateway_smoke_helper.py
tests/test_gateway_stt_adapter.py
tests/test_realtime_gateway.py
docs/stt_gateway_protocol.md
docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md
docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md
docs/nodes/NODE-032W-controlled-gateway-transcript-presence-smoke.md
```

## Findings

### Transport Success Is Not Transcript-Presence Success

Gateway HTTP 200 and `chunks_sent=5` prove that the Asterisk-origin path reached the Gateway, authenticated, accepted the valid WAV format, created an OpenAI Realtime session, and sent audio chunks.

They do not prove that:

- OpenAI emitted transcript events;
- the Gateway recognized every transcript event type currently emitted by the Realtime API;
- the Gateway propagated redacted event flags into the HTTP response;
- the Asterisk-side adapter preserved those redacted event flags;
- the synthetic audio stimulus was speech-like or long enough to elicit transcript-bearing events.

### Audio Stimulus Hypothesis

The repo-created smoke WAV is now format-valid:

```text
sample_rate_hz=24000
channels=1
sample_width_bytes=2
format=PCM WAV
```

Format validity is necessary but not sufficient. The local smoke helper describes the generated stimulus as synthetic and non-transcript. NODE-032W therefore leaves these as plausible:

```text
synthetic_audio_not_speech_like_enough=plausible
audio_too_short=plausible
known_speech_fixture_may_be_needed=true
```

### Event Parsing / Diagnostics Hypothesis

The Gateway already contains a redacted event-count path:

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
```

Transcript-bearing detection currently recognizes:

```text
conversation.item.input_audio_transcription.delta
conversation.item.input_audio_transcription.completed
```

NODE-032W reported `transcript_event_seen=null` and `transcript_bearing_event_seen=null`, not `false`. That is diagnostic ambiguity. The next boundary should make the result classifiable without transcript text:

```text
no_transcript_event_observed
transcript_event_observed_empty_text
transcript_bearing_event_observed_text_redacted
event_counts_present_but_adapter_flags_missing
timeout_after_audio_commit
error_event_observed
```

### Session Settings Hypothesis

The Asterisk adapter sends `return_transcript=true`, and Gateway settings include an explicit transcript-return policy. Local tests cover Realtime transcription session shape and transcript event handling. NODE-032X cannot prove from local inspection alone whether live session settings caused NODE-032W to miss transcript events.

This remains:

```text
session_settings_gap=possible_but_unproven
```

### Redaction Boundary

`gateway_adapter._safe_gateway_payload` removes `transcript_text` unless transcript logging is explicitly enabled. `gateway_adapter_smoke.build_report` exposes safe booleans and counts. This is the right boundary: collect event names/counts and booleans, never text.

## Hypothesis Ranking

```text
primary_likely_next_failure_mode=insufficient_redacted_diagnostics
secondary_likely_failure_mode=audio_stimulus_not_speech_like_or_too_short
possible_failure_mode=event_parser_misses_current_realtime_event_alias
possible_failure_mode=session_settings_do_not_elicit_transcript_events
```

Why diagnostics first:

- A known speech fixture might produce transcript events, but without stronger event-count propagation the next live result can still be ambiguous.
- Event counts and booleans can identify whether the issue is audio, parser coverage, timeout, or response propagation.
- No transcript text is needed to make that classification safer.

## Selected Next Boundary

Primary recommendation:

```text
NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

NODE-032Y should be a local implementation/planning node. It should harden and test redacted transcript-event diagnostics before any further live smoke.

Expected NODE-032Y scope:

- verify `openai_event_type_counts` always propagates from Gateway response to adapter report when present;
- normalize missing event flags to explicit safe values or explicit `not_reported` status instead of ambiguous `null`;
- cover transcript event aliases currently used in tests and docs;
- preserve transcript text redaction;
- add local fixtures for:
  - transcript delta/completed with text redacted;
  - completed event with empty transcript;
  - no transcript event before timeout;
  - event counts present but transcript text absent;
  - Gateway response missing diagnostics;
- document a future live smoke boundary after diagnostics are hardened.

NODE-032Y must not run live smoke or handle tokens.

## Evidence Safe To Collect Next

The next node may collect or report:

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
first_delta_ms_present
final_ms_present
chunks_sent
gateway_http_status
audio_duration_ms
audio_rms
audio_peak
audio_non_silent_ratio
audio_quality_classification
transcript_text_present
transcript_text_length_zero_or_nonzero
```

The next node must not collect or report:

```text
raw_transcript_text
transcript_delta_text
token_values
raw_secret_env_output
large_logs
audio_files
binary_artifacts
business_dialog_profile_changes
```

## Deferred Alternatives

```text
NODE-032Y / controlled-transcript-presence-smoke-with-known-speech-stimulus = deferred
NODE-032Y / realtime-session-transcription-settings-fix = deferred
NODE-032Y / gateway-transcript-event-parser-local-fixture-hardening = folded into primary if needed
```

Reasons:

- Known speech stimulus is likely useful later, but should follow clearer event diagnostics.
- Session settings should be changed only if local diagnostics or future redacted evidence points there.
- Parser fixture hardening is part of the selected diagnostics node, not a separate live retry.

## What Remains Explicitly Unproven

Even after NODE-032Y, these must remain unproven unless separately scoped:

```text
transcript_quality
transcript_text_correctness
business_dialog_integration
business_dialog_transcript_use
production_autostart
reboot_or_power_cycle_persistence
dual_channel_caller_bot_recording
```

## Safety Confirmation

```text
live_smoke=false
ssh=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
production_autostart=false
systemctl_enable=false
business_dialog_enablement=false
transcript_used_for_dialog=true_not_allowed
transcript_text_logging=false
dual_channel_recording=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
