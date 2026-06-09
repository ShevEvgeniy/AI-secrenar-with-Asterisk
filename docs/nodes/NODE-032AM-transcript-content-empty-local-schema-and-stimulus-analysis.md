# NODE-032AM / transcript-content-empty-local-schema-and-stimulus-analysis

## Status

```text
status=Closed, local analysis/docs
branch=feat/node-032am-transcript-content-empty-local-schema-and-stimulus-analysis
source_runtime_change=false
live_smoke=false
ssh=false
server_state_change=false
```

## Goal

Analyze local schema assumptions, transcript event-field parsing, redaction/bucketing behavior, and future stimulus/settings requirements after NODE-032AK and NODE-032AL.

This node is an analysis/specification boundary. It does not implement source/runtime changes.

## Context

NODE-032AK accepted proof:

```text
transport_auth_runtime_diagnostics=pass
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
```

Remaining blocker:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

NODE-032AL top hypothesis:

```text
prepared_stimulus_valid_signal_metrics_but_no_proof_of_actual_linguistic_speech_content
```

## 1 Local Schema Assumption Map

Current event paths treated as transcript-related:

```text
transcript_event_seen=event_type_startswith_conversation.item.input_audio_transcription.
transcript_bearing_event_seen=conversation.item.input_audio_transcription.delta_or_completed
```

Current event paths treated as transcript-text-bearing:

```text
delta_event=conversation.item.input_audio_transcription.delta
delta_text_field=payload.delta
completed_event=conversation.item.input_audio_transcription.completed
completed_text_field=payload.transcript
```

Current nested fields read:

```text
nested_fields_read=none
completed_item_content_fields_read=none
alternate_text_fields_read=none
```

Fields intentionally not logged:

```text
transcript_text
transcript_delta_content
raw_provider_event_body
token_values
raw_env_values
```

Safe counts:

```text
openai_event_type_counts=event_type_names_only
openai_event_type_counts_available=true_when_diagnostics_are_built
openai_event_type_counts_present=true_when_counts_non_empty
```

## 2 Provider Event Field Handling

Current code assumes a non-empty delta appears at top-level `delta`, and final transcript text appears at top-level `transcript` on the completed event.

Covered by local tests:

```text
top_level_delta_non_empty_sets_presence=true
top_level_completed_transcript_non_empty_sets_nonzero_bucket=true
top_level_completed_transcript_empty_sets_zero_bucket=true
```

Potential schema gaps that can be tested locally without real transcript text:

```text
completed_event_nested_transcript_field
completed_event_content_array_transcript_field
completed_event_item_transcript_field
delta_event_alternate_text_field
late_delta_after_completed_event
```

NODE-032AM does not fetch online docs. The next bounded local node can encode these as synthetic fixtures with placeholder-safe values and no transcript text logging.

## 3 Redaction And Bucket Proof Map

Proven locally:

```text
non_empty_transcript_text_sets_transcript_text_present=true
non_empty_transcript_text_sets_transcript_text_length_bucket=nonzero_redacted
empty_completed_transcript_sets_bucket=zero
actual_transcript_text_suppressed_by_default=true
adapter_removes_transcript_text_when_logging_disabled=true
smoke_report_removes_transcript_text_when_logging_disabled=true
safe_event_counts_preserved=true
diagnostic_gap_detected_when_counts_missing=true
empty_but_available_counts_do_not_create_gap=true
```

Not proven:

```text
live_provider_completed_event_shape_matches_top_level_transcript=true
prepared_synthetic_stimulus_contains_actual_linguistic_content=true
current_session_settings_are_optimal_for_content_output=true
```

Conclusion:

```text
false_zero_due_redaction=unlikely
alternate_event_schema_fixture_gap=open
```

## 4 Session Settings Context Review

Current Gateway Realtime session settings:

```text
model=gpt-realtime-whisper
language=ru
sample_rate=24000
audio_format=audio/pcm
chunk_ms=200
turn_detection=None
noise_reduction=None
prompt_or_context=absent
commit_timing=input_audio_buffer.append_chunks_then_input_audio_buffer.commit
timeout_seconds=30
```

Classification:

```text
sample_rate=proven_OK_for_transport_and_format
audio_format=proven_OK_for_transport_and_format
commit_timing=proven_OK_for_completed_event
chunk_ms=likely_OK_but_content_unproven
model=likely_OK_but_content_unproven
language=likely_OK_but_stimulus_match_unproven
timeout_seconds=likely_OK_for_completed_event_but_content_quality_unproven
turn_detection=candidate_for_future_controlled_change
noise_reduction=candidate_for_future_controlled_change
prompt_or_context=candidate_for_future_controlled_change
```

These settings should not be changed without a separate bounded node.

## 5 Stimulus Semantics Requirements

A future stimulus must prove actual lexical content before smoke without using real caller/sensitive audio or committing audio artifacts.

Requirements:

```text
non_sensitive_actual_linguistic_content=true
language_matches_session_setting=true
real_caller_audio=false
sensitive_audio=false
audio_format=24000_hz_mono_16_bit_pcm
duration_reported=true
rms_reported=true
peak_reported=true
non_silent_ratio_reported=true
clipping_checked=true
silence_dominance_checked=true
audio_file_committed=false
actual_transcript_text_logged=false
actual_transcript_text_committed=false
```

Acceptable future evidence should use safe identifiers, length buckets, and generated fixture labels rather than transcript text.

## 6 What Current Tests Prove

Current tests prove:

```text
supported_delta_event_field_parsed=true
supported_completed_event_field_parsed=true
nonzero_bucket_survives_text_suppression=true
empty_completed_event_classified_zero=true
diagnostic_propagation_gap_detected_when_missing=true
empty_available_event_counts_preserved_without_gap=true
adapter_and_smoke_reports_suppress_transcript_text=true
Asterisk_OPENAI_API_KEY_refused_by_smoke_helper=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG_false_required_for_smoke=true
newline_token_material_rejected=true
temp_env_guard_create_validate_cleanup_safe=true
helper_bundle_preflight_safe=true
24khz_mono_16bit_pcm_audio_guard_exists=true
```

## 7 What Current Tests Do Not Prove

Current tests do not prove:

```text
alternate_provider_event_shapes_are_supported=true
live_provider_completed_event_uses_top_level_transcript=true
generated_speech_like_stimulus_has_lexical_content=true
language_setting_matches_future_actual_speech_stimulus=true
prompt_or_context_would_improve_content=true
turn_detection_or_noise_reduction_would_improve_content=true
late_delta_after_completed_event_is_collected=true
```

## 8 Rejected Causes

Rejected or deprioritized causes:

```text
transport_auth_runtime_failure=false
diagnostic_propagation_gap=false
firewall_env_service_state_blocker=false
business_dialog_disabled_state_caused_empty_provider_transcript=false
redaction_bucket_false_zero=unlikely
```

Evidence:

```text
NODE_032AK_gateway_http_status=200
NODE_032AK_openai_realtime_from_gateway=ok
NODE_032AK_openai_session_created=true
NODE_032AK_chunks_sent=20
NODE_032AK_transcript_event_seen=true
NODE_032AK_transcript_bearing_event_seen=true
NODE_032AK_diagnostic_propagation_gap=false
local_tests_preserve_nonzero_bucket_under_redaction=true
```

## 9 Next Node Recommendation

Recommended next node:

```text
NODE-032AN / transcript-event-schema-fixtures-and-nonzero-bucket-local-proof
```

Rationale:

```text
preferred_boundary=local_repo_only_implementation_tests_specs
add_alternate_event_schema_fixtures=true
prove_nonzero_bucket_mapping_with_placeholder_safe_values=true
document_safe_actual_speech_stimulus_requirements=true
live_smoke_retry=false
```

The alternate `NODE-032AN / safe-actual-speech-stimulus-and-session-settings-plan` should be deferred unless schema fixture coverage is already sufficient or is completed first.

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
transcript_text_logged=false
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
