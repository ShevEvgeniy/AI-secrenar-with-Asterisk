# NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts

## Goal

Harden local Gateway/OpenAI transcript-event diagnostics so a future live smoke can distinguish transcript event behavior without logging transcript text.

This node is local/repo-only. It does not run a live smoke and does not touch servers.

## Starting Truth

NODE-032W remains transport/auth/OpenAI Realtime success only:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

NODE-032X selected this node because insufficient redacted diagnostics is the primary next failure mode. Transcript presence, transcript quality, transcript text correctness, business-dialog integration, production autostart, and dual-channel caller/bot proof remain unproven.

## Implementation

The Gateway response diagnostics now include:

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

`transcript_text_length_bucket` is limited to:

```text
zero
nonzero_redacted
unknown
```

The Asterisk-side smoke report propagates these fields and marks missing event-count diagnostics as:

```text
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

This reduces the prior `null` ambiguity by distinguishing absent/not-propagated diagnostics from observed `false` fields.

## Supported Classifications

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

## Tests

Tests cover:

- transcript-bearing OpenAI events with text redacted into `nonzero_redacted`;
- transcript-bearing events with empty text bucketed as `zero`;
- OpenAI error events classified safely;
- Asterisk-side smoke report propagation of event counts and diagnostic flags;
- missing event diagnostics classified as a propagation gap;
- existing safety boundaries for Asterisk `OPENAI_API_KEY`, gateway token handling, no transcript logging, and no business-dialog transcript use.

Synthetic test transcript values are fake placeholders only and are asserted absent from serialized reports/logs.

## Safety

Forbidden data remains excluded:

```text
raw_transcript_text=false
transcript_delta_text=false
token_values=false
raw_secret_env_output=false
large_raw_logs=false
audio_artifacts=false
business_dialog_profile_changes=false
```

No live systems were touched:

```text
live_smoke=false
ssh=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_env_server_change=false
business_dialog_enablement=false
transcript_text_logging=false
```

## Next Boundary

Recommended next node:

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

NODE-032Z should run exactly one controlled Asterisk-side non-business-dialog smoke only after exact approval and hard-gate re-confirmation. It should accept only the new safe diagnostic fields, not transcript text, and it must keep `transcript_used_for_dialog=false`.
