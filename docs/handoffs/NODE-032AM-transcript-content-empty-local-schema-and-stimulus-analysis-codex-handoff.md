# NODE-032AM Codex Handoff

Node:

```text
NODE-032AM / transcript-content-empty-local-schema-and-stimulus-analysis
```

Branch:

```text
feat/node-032am-transcript-content-empty-local-schema-and-stimulus-analysis
```

Scope:

```text
repo_local_analysis_only=true
source_runtime_change=false
live_smoke=false
ssh=false
server_access=false
helper_deploy=false
token_handling=false
temp_env=false
audio_generation=false
service_action=false
firewall_env_server_change=false
```

## Context

NODE-032AK remains accepted as a successful controlled Gateway transport/auth/OpenAI Realtime diagnostics smoke:

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
```

The remaining blocker is transcript content:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

NODE-032AL classified the likely leading cause as valid signal metrics without proof of actual linguistic speech content.

## 1 Local Schema Assumption Map

Current transcript event type assumptions:

```text
delta_event_type=conversation.item.input_audio_transcription.delta
completed_event_type=conversation.item.input_audio_transcription.completed
transcript_event_seen=any_event_type_starting_conversation.item.input_audio_transcription.
transcript_bearing_event_seen=delta_event_or_completed_event_count_present
```

Current transcript text-bearing field assumptions:

```text
delta_text_field=payload.delta
completed_text_field=payload.transcript
nested_transcript_fields_read=none
alternate_completed_text_fields_read=none
alternate_delta_text_fields_read=none
```

Fields intentionally not logged:

```text
transcript_text
transcript_delta_content
raw_provider_event_body
token_values
raw_env_values
```

Safe event counts include event type names only:

```text
openai_event_type_counts=dict_sorted_by_event_type
openai_event_type_counts_available=true_when_gateway_builds_diagnostics
openai_event_type_counts_present=true_when_counts_non_empty
```

## 2 Provider Event Field Handling

Current code assumes:

```text
delta_text_source=top_level_delta
completed_text_source=top_level_transcript
completed_event_without_top_level_transcript=completed_event_empty_or_no_text
```

Local tests cover these expected fields with synthetic provider events:

```text
delta_field_non_empty_sets_transcript_text_present=true
completed_transcript_field_non_empty_sets_nonzero_bucket=true
completed_transcript_field_empty_sets_zero_bucket=true
```

Likely local-testable schema gaps:

```text
completed_event_nested_transcript_field
completed_event_content_array_transcript_field
completed_event_item_transcript_field
delta_event_alternate_text_field
late_delta_after_completed_event
```

NODE-032AM did not fetch external docs. A future node can add local fixtures for these alternate event shapes without real transcript text.

## 3 Redaction And Bucket Proof Map

Proven locally:

```text
non_empty_transcript_sets_transcript_text_present=true
non_empty_transcript_sets_bucket=nonzero_redacted
actual_text_suppressed_when_gateway_return_disabled=true
actual_text_suppressed_when_adapter_log_transcript_false=true
diagnostics_preserve_safe_event_counts=true
missing_diagnostics_marked_as_gap=true
empty_present_event_counts_not_marked_as_gap=true
```

Not proven:

```text
live_provider_completed_event_shape_matches_current_top_level_transcript_assumption
prepared_synthetic_stimulus_contains_actual_linguistic_content
current_session_settings_are_optimal_for_content_output
```

Conclusion:

```text
redaction_bucket_false_zero=unlikely
schema_fixture_gap=still_open
```

## 4 Session Settings Context Review

Current settings:

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
timeout_seconds=30_gateway_default
```

Classification:

```text
sample_rate=proven_ok_for_transport_and_format
audio_format=proven_ok_for_transport_and_format
commit_timing=proven_ok_for_completed_event
model=likely_ok_but_content_unproven
language=likely_ok_but_stimulus_language_match_unproven
turn_detection=candidate_for_future_controlled_review
noise_reduction=candidate_for_future_controlled_review
prompt_or_context=candidate_for_future_controlled_review
timeout_seconds=likely_ok_for_completed_event_but_not_content_quality
```

None should be changed without a bounded node.

## 5 Stimulus Semantics Requirements

Future stimulus strategy should prove actual lexical content exists before live smoke, without logging later live transcript text.

Requirements:

```text
non_sensitive_actual_linguistic_content=true
real_caller_audio=false
sensitive_audio=false
language_matches_session_setting=true
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

The future proof should use safe identifiers, expected length buckets, or generated fixture labels. It must not require committing audio or transcript content.

## 6 What Current Tests Prove

Current tests prove:

```text
gateway_parses_supported_delta_and_completed_event_fields=true
gateway_preserves_nonzero_bucket_without_returning_text=true
gateway_classifies_empty_completed_event_as_zero=true
adapter_strips_transcript_text_when_logging_disabled=true
smoke_report_preserves_safe_event_diagnostics=true
smoke_report_marks_missing_event_diagnostics_as_gap=true
smoke_report_preserves_empty_present_counts_without_gap=true
helper_requires_STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG_false_for_smoke=true
helper_refuses_Asterisk_OPENAI_API_KEY=true
helper_refuses_newline_token_material=true
helper_validates_24000_hz_mono_16_bit_pcm_audio=true
helper_bundle_and_temp_env_guards_are_safe=true
```

## 7 What Current Tests Do Not Prove

Current tests do not prove:

```text
alternate_provider_event_shapes_are_parsed=true
live_provider_completed_event_uses_top_level_transcript=true
generated_speech_like_stimulus_contains_lexical_content=true
Russian_language_setting_matches_future_stimulus=true
prompt_context_changes_affect_content=true
turn_detection_or_noise_reduction_changes_affect_content=true
late_delta_after_completed_is_collected=true
```

## 8 Rejected Causes

Carried forward and reinforced:

```text
transport_auth_runtime_failure=false
diagnostic_propagation_gap=false
firewall_env_service_state_blocker=false
business_dialog_disabled_state_caused_empty_provider_transcript=false
redaction_bucket_false_zero=unlikely
```

Evidence:

```text
NODE_032AK_http_200=true
NODE_032AK_openai_realtime_ok=true
NODE_032AK_session_created=true
NODE_032AK_chunks_sent=20
NODE_032AK_transcript_event_seen=true
NODE_032AK_transcript_bearing_event_seen=true
NODE_032AK_diagnostic_propagation_gap=false
local_tests_preserve_nonzero_bucket_under_redaction=true
```

## 9 Next Node Recommendation

Recommended:

```text
NODE-032AN / transcript-event-schema-fixtures-and-nonzero-bucket-local-proof
```

Rationale:

```text
local_repo_only_first=true
add_alternate_provider_event_shape_fixtures=true
prove_nonzero_bucket_mapping_without_real_transcript_text=true
document_safe_actual_speech_stimulus_requirements=true
do_not_run_live_smoke_yet=true
```

The alternate `safe-actual-speech-stimulus-and-session-settings-plan` can follow if NODE-032AN confirms schema coverage is sufficient or adds the missing fixture coverage.

## Safety

NODE-032AM did not run smoke, retry NODE-032AK, use SSH, access servers, deploy helpers, handle tokens, create temp env files, generate or upload audio, start/stop/restart/reload services, change firewall, change server env, install dependencies, reboot, power-cycle, log transcript text, log transcript deltas, use transcript for dialog, write Notion, write Runtime/Evidence, or commit audio/binary artifacts.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
