# NODE-032AA / gateway-event-diagnostics-propagation-gap-fix

## Goal

Diagnose and fix the local redacted diagnostic propagation ambiguity observed in NODE-032Z.

NODE-032AA is local/repo implementation and documentation only. It is not a live-smoke node.

## Base

```text
master_head=ce3814cf6ad500b6236a6e63b4d00bdb196fe8b6
latest_closed_node=NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

## NODE-032Z Result Preserved

NODE-032Z ran one corrected Asterisk-side non-business-dialog smoke after exact approval and hard-gate re-confirmation:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

NODE-032Z diagnostic output:

```text
openai_event_type_counts={}
openai_event_type_counts_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
input_audio_buffer_commit_sent=null
timeout_observed=null
error_event_seen=null
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

## Confirmed Local Issue

The smoke report path preserved provided diagnostic dictionaries, but the schema lacked an explicit safe marker for whether the event-count field itself had propagated.

Without that marker, an intentionally empty event-count dictionary could look too similar to missing event-count diagnostics when `openai_event_type_counts_present=false`.

## Implemented Fix

Added a safe field:

```text
openai_event_type_counts_available
```

Meaning:

```text
true=the openai_event_type_counts field was propagated, even if it is {}
false=the event-count field was missing/not propagated
```

Updated behavior:

```text
diagnostic_propagation_gap=true only when diagnostics are missing/not propagated
diagnostic_propagation_gap=false when openai_event_type_counts={} is present and marked available
openai_event_type_counts_present remains a value/content marker
openai_event_type_counts_available is the field-availability marker
```

## Code Changes

```text
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/gateway_adapter_smoke.py
```

Gateway response diagnostics now include:

```text
openai_event_type_counts_available=true
```

Asterisk-side smoke reports now include:

```text
openai_event_type_counts_available=true|false
```

The smoke report also defensively removes `transcript_text` from details whenever transcript logging is disabled.

## Tests

Updated:

```text
tests/test_realtime_gateway.py
tests/test_gateway_stt_adapter.py
```

Coverage added/confirmed:

```text
non_empty_event_counts_preserved=true
empty_but_present_event_counts_gap=false
missing_diagnostics_gap=true
transcript_text_not_emitted_when_logging_disabled=true
token_like_values_not_emitted=true
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

## Protocol Docs

Updated:

```text
docs/stt_gateway_protocol.md
```

The protocol now distinguishes:

```text
openai_event_type_counts_available=field propagated
openai_event_type_counts_present=counts contain event entries
```

## Safety

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
transcript_delta_logging=false
audio_artifacts_committed=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Validation

```text
focused_gateway_adapter_tests=28_passed
required_focused_suite=50_passed
full_pytest=234_passed_6_failed_known_environmental
known_environmental_failure_1=missing src/scripts/make_demo_audio.py
known_environmental_failure_2=missing sentence_transformers
git_diff_check=pass
source_runtime_diff=intended source/test files only
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status/test fixtures only
scoped_source_docs_tests_scan=no_real_secret_values_found; placeholders/status/synthetic fixtures only
transcript_delta_scan=no_transcript_text_added; policy labels and existing synthetic event-type fixtures only
audio_binary_artifacts_added=false
```

## Remaining Unproven Items

NODE-032AA does not prove live Gateway behavior after the fix. It only fixes and tests local propagation semantics.

Still unproven:

```text
live_openai_event_type_counts_available=true
live_transcript_event_seen classification
live_transcript_bearing_event_seen classification
live_transcript_text_length_bucket classification
```

## Next Recommendation

```text
NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix
```

NODE-032AB should run exactly one controlled Asterisk-side non-business-dialog smoke after exact approval and immediate hard-gate re-confirmation. It must keep token output disabled, transcript text logging disabled, and business-dialog transcript use disabled.
