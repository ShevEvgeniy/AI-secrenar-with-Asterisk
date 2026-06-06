# NODE-032X Codex Handoff

Node:

```text
NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```

Branch:

```text
feat/node-032x-transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```

Base:

```text
master
base_commit=89ae0e32d95858f2ff02a40601f2621a302acf0d
latest_closed_node=NODE-032W / controlled-gateway-transcript-presence-smoke
```

## Scope

NODE-032X is a local-only diagnostics and planning node. It does not run live smoke, contact servers, deploy helper bundles, handle tokens, create temp env files, start/stop/restart/reload/enable services, install dependencies, reboot, change firewall or env state, enable business dialog, log transcript text, write Notion, update Runtime/Evidence, create a scheduler, create a webhook, or create an automation loop.

## NODE-032W Truth To Preserve

NODE-032W proved the Asterisk-origin Gateway transport/auth/OpenAI Realtime path again:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
```

NODE-032W did not prove transcript presence:

```text
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Final safety state from NODE-032W:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
local_temp_bundle_removed=true
token_values_printed=false
transcript_text_printed=false
```

## Local Files Inspected

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
docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md
docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md
docs/nodes/NODE-032W-controlled-gateway-transcript-presence-smoke.md
docs/stt_gateway_protocol.md
```

## Local Diagnostic Findings

### Transport Is Not Transcript Presence

NODE-032W reached the Gateway, authenticated, returned HTTP 200, created an OpenAI Realtime session, and sent five audio chunks. That proves request routing, Gateway auth, audio format acceptance, websocket/session creation, and audio append/commit behavior.

It does not prove that OpenAI emitted a transcript event, that the Gateway classified transcript events correctly, that the Asterisk-side adapter preserved those redacted event flags, or that the audio stimulus was speech-like enough to elicit transcript-bearing events.

### Audio Stimulus

The repo smoke helper creates a valid `24000 Hz mono 16-bit PCM WAV`, but the generated stimulus is synthetic and intentionally non-transcript text. Valid audio format is necessary, but not sufficient for transcript-presence proof.

Likely risk:

```text
audio_stimulus_speech_like_enough=unknown
audio_duration_sufficient=unknown
```

### Gateway Event Diagnostics

`src/ai_secretary/stt/realtime_gateway.py` already counts event types without returning transcript text:

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
```

Transcript event detection currently keys on:

```text
conversation.item.input_audio_transcription.delta
conversation.item.input_audio_transcription.completed
```

The Gateway can safely report event-type counts and boolean event flags without transcript text.

### Adapter Report Boundary

`src/ai_secretary/stt/gateway_adapter.py` strips `transcript_text` unless transcript logging is explicitly enabled. `src/ai_secretary/stt/gateway_adapter_smoke.py` exposes redacted report fields:

```text
transcript_present
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
transcript_text_logged
transcript_used_for_dialog
business_dialog_unchanged
```

NODE-032W returned `transcript_event_seen=null` and `transcript_bearing_event_seen=null`, not `false`. That leaves an important ambiguity:

```text
gateway_did_not_emit_event=false_or_unknown
gateway_payload_did_not_include_event_flags=possible
adapter_report_did_not_receive_flags=possible
```

### Session Settings

The Gateway constructs a Realtime transcription session and sends `return_transcript=true` from the Asterisk-side adapter request. Local tests show expected transcription-session shape and event-count handling. Without new live evidence, NODE-032X cannot prove whether session settings caused the missing transcript events.

## Hypothesis Evaluation

```text
synthetic_audio_not_speech_like_enough=plausible
audio_too_short=plausible
gateway_event_parsing_misses_event_type=possible
helper_fields_distinguish_event_and_text_presence=true
session_settings_do_not_request_transcript=possible_but_not_confirmed
current_redacted_diagnostics_insufficient=true
event_type_counts_without_text_needed=true
known_speech_fixture_needed=possible_after_diagnostics_boundary
```

## Selected Primary Recommendation

```text
NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

Choose a local implementation and planning node before another live smoke. The next node should harden the redacted diagnostics path so a future smoke can distinguish:

- no transcript event observed;
- transcript event observed with empty transcript;
- transcript-bearing event observed with text redacted;
- Gateway produced event counts but adapter did not propagate them;
- timeout or error event occurred after audio commit.

Why this is primary:

- NODE-032W already proved transport/auth/OpenAI Realtime; repeating smoke with the same diagnostic ambiguity risks another inconclusive result.
- A known speech stimulus may be needed, but without stronger event-count propagation a future result could still be hard to classify safely.
- Event names, counts, boolean flags, audio diagnostics, and timing can be collected without transcript text.
- This keeps transcript text logging, business-dialog transcript use, and live retry out of the next local boundary.

## Evidence Safe To Collect Without Transcript Text

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
first_delta_ms_present
final_ms_present
audio_duration_ms
audio_rms
audio_peak
audio_non_silent_ratio
audio_quality_classification
gateway_http_status
chunks_sent
transcript_text_present
transcript_text_length_bucket_or_zero
```

Do not collect:

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
controlled_transcript_presence_smoke_with_known_speech_stimulus=deferred_until_redacted_event_diagnostics_are_hardened
realtime_session_transcription_settings_fix=deferred_until_diagnostics_show_session_setting_gap
gateway_transcript_event_parser_local_fixture_hardening=part_of_NODE_032Y_or_follow_up_if_event_aliases_are_found
business_dialog_integration=out_of_scope
production_autostart=out_of_scope
dual_channel_recording=out_of_scope
```

## What Must Remain Unproven After NODE-032Y

```text
transcript_quality=false
transcript_text_correctness=false
business_dialog_transcript_use=false
production_autostart=false
reboot_power_cycle_persistence=false
dual_channel_caller_bot_recording=false
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
business_dialog_enablement=false
transcript_text_logging=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
