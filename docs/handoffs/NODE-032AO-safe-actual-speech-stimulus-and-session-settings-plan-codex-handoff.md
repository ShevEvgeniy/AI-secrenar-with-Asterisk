# NODE-032AO Codex Handoff

Node:

```text
NODE-032AO / safe-actual-speech-stimulus-and-session-settings-plan
```

Branch:

```text
feat/node-032ao-safe-actual-speech-stimulus-and-session-settings-plan
```

Scope:

```text
repository_only=true
planning_only=true
source_runtime_change=false
live_smoke=false
ssh=false
server_access=false
helper_deploy=false
token_handling=false
temp_env_created=false
audio_generated=false
audio_uploaded=false
service_action=false
firewall_or_env_change=false
server_state_change=false
transcript_text_or_delta_logged=false
```

## Current Evidence

NODE-032AK remains the latest live transcript-content smoke reference. It proved the transport/auth/runtime diagnostics path but not transcript content:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

NODE-032AN then proved local placeholder-safe parsing and redacted nonzero bucket mapping for selected event schemas:

```text
top_level_delta=covered
top_level_completed_transcript=covered
nested_completed_transcript=covered
item_transcript=covered
content_array_transcript_or_text=covered
alternate_delta_text=covered
late_delta_after_completed=deferred
```

## Planning Result

NODE-032AO selects a future safe actual-speech stimulus boundary instead of another immediate smoke. The future stimulus must be non-sensitive, operator-approved, and described only by labels and metrics:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
expected_language=ru
expected_content_bucket=nonempty_linguistic
audio_format=24000_hz_mono_16_bit_pcm_wav
audio_committed=false
transcript_text_committed=false
transcript_delta_committed=false
```

The first future live retry should isolate the stimulus variable and keep current proven session/runtime settings unless immediate Phase A evidence demands a stop:

```text
model=gpt-realtime-whisper
language=ru
sample_rate=24000
chunk_ms=200
turn_detection=unchanged
noise_reduction=unchanged
prompt_or_context=unchanged
```

## Future Boundary

Recommended next node:

```text
NODE-032AP / controlled-actual-speech-transcript-content-smoke
```

Future approval phrase:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```

Acceptance target for NODE-032AP:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent_gt_0=true
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=true
transcript_text_length_bucket=nonzero_redacted
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Safety Notes

This handoff intentionally contains no real token values, private keys, transcript text, transcript deltas, raw provider event bodies, audio content, binary artifacts, or raw env output.
