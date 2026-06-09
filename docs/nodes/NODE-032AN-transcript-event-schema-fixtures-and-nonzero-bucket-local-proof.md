# NODE-032AN / transcript-event-schema-fixtures-and-nonzero-bucket-local-proof

## Status

```text
status=Closed, local implementation/tests/docs
branch=feat/node-032an-transcript-event-schema-fixtures-and-nonzero-bucket-local-proof
live_smoke=false
ssh=false
server_state_change=false
```

## Goal

Implement placeholder-safe local fixtures and tests for transcript event schema handling after NODE-032AM, before any future live smoke.

## Implemented Parser Cases

Updated `src/ai_secretary/stt/realtime_gateway.py` with a bounded transcript text extraction helper for Realtime transcription events.

Current fields:

```text
delta_event_payload_delta_non_empty=supported
completed_event_payload_transcript_non_empty=supported
completed_event_payload_transcript_empty=supported
```

Selected alternate fields:

```text
delta_event_payload_text_non_empty=supported
completed_event_payload_transcript_text=supported
completed_event_payload_transcript_value=supported
completed_event_payload_item_transcript=supported
completed_event_payload_content_array_transcript=supported
completed_event_payload_content_array_text=supported
completed_event_payload_item_content_array_transcript=supported
completed_event_payload_item_content_array_text=supported
```

All alternate support is limited to non-empty string fields on known transcript events.

## Cases Intentionally Not Supported

```text
late_delta_after_completed_event=not_supported
```

Reason:

```text
completed_event_is_terminal_in_current_measurement_loop=true
changing_terminal_event_collection_requires_separate_bounded_node=true
```

## Test Proof Summary

Updated:

```text
tests/test_realtime_gateway.py
tests/test_gateway_stt_adapter.py
```

Fixture labels:

```text
PLACEHOLDER_NONZERO_TRANSCRIPT
PLACEHOLDER_DELTA_TEXT
PLACEHOLDER_ALT_SCHEMA_TEXT
```

Proofs:

```text
current_delta_event_payload_delta_non_empty_sets_nonzero_bucket=true
current_completed_event_payload_transcript_non_empty_sets_nonzero_bucket=true
current_completed_event_payload_transcript_empty_sets_zero_bucket=true
transcript_bearing_event_with_no_text_classification=transcript_event_observed_empty_or_no_text
completed_event_nested_transcript_field_sets_nonzero_bucket=true
completed_event_item_transcript_field_sets_nonzero_bucket=true
completed_event_content_array_transcript_field_sets_nonzero_bucket=true
delta_event_alternate_text_field_sets_nonzero_bucket=true
```

## Redaction And Bucket Proof

Local tests prove:

```text
actual_text_not_returned_to_dialog_by_default=true
actual_text_not_logged_by_default=true
placeholder_text_not_serialized_in_gateway_payload=true
safe_bucket_preserved=true
event_type_counts_preserved=true
empty_event_counts_do_not_create_diagnostic_gap=true
```

## Smoke Report Proof

Local tests prove:

```text
nonzero_bucket_survives_adapter_and_smoke_report=true
missing_diagnostics_still_gap=true
present_empty_counts_not_gap=true
zero_bucket_classification_preserved=true
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

## Remaining Gaps

NODE-032AN does not prove:

```text
live_provider_event_shape_matches_fixtures=true
late_delta_after_completed_event_collection=true
future_stimulus_contains_actual_linguistic_content=true
current_session_settings_are_best_for_content=true
```

## Validation

```text
focused_suite=55_passed
git_diff_check=pass
deploy_scripts_pyproject_diff=empty
```

## Decision

NODE-032AN reduces the local schema fixture gap and keeps live smoke deferred.

Next recommended node:

```text
NODE-032AO / safe-actual-speech-stimulus-and-session-settings-plan
```

## Safety

```text
smoke_or_retry=false
ssh=false
server_access=false
helper_deploy=false
token_handling=false
temp_env=false
audio_generation_or_upload=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_or_env_change=false
real_transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
notion_write=false
runtime_evidence_update=false
audio_binary_artifact_added=false
```

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
