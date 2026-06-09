# NODE-032AK / controlled-transcript-content-smoke-with-prepared-stimulus

Date: 2026-06-09

Branch: `feat/node-032ak-controlled-transcript-content-smoke-with-prepared-stimulus`

Phase: Phase B controlled live smoke completed; transcript-content target blocked.

## Goal

Prepare for exactly one controlled transcript-content smoke with prepared stimulus after explicit approval.

NODE-032AK is a live-risk smoke node. Phase A did not run live smoke. Phase B ran exactly one controlled non-business-dialog Asterisk-side smoke after exact approval.

## Context

NODE-032AJ merged at:

```text
2d05ad5d0710437dfae47e548c7081e830570c45
```

NODE-032AJ prepared this target:

```text
speech_duration_longer_than_NODE_032AG
clear_speech_like_waveform
not_silence_dominant
not_clipped
audio_format=24000_hz_mono_16_bit_pcm
pre_smoke_duration_reported=true
pre_smoke_rms_reported=true
pre_smoke_peak_reported=true
pre_smoke_non_silent_ratio_reported=true
no_real_caller_audio=true
no_sensitive_audio=true
no_committed_audio_binary_artifacts=true
```

Prior accepted proof:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

Remaining limitation:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
problem_class=empty_or_zero_transcript_content
```

## Phase A Repo Gates

```text
base_master_head=2d05ad5d0710437dfae47e548c7081e830570c45
smoke_helper_present=true
helper_bundle_present=true
safe_temp_env_guard_present=true
node032aj_doc_present=true
focused_suite=50_passed
git_diff_check=pass
source_runtime_diff=empty
untracked_artifacts_untouched=true
```

## Phase A Asterisk Read-Only Gates

```text
asterisk_ssh_reachable=true
asterisk_hostname=tula
ai_secretary_ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
tmp_helper_env_markers=ABSENT
test_call_placed=false
helper_deployed=false
temp_env_created=false
```

## Phase A Gateway Read-Only Gates

```text
gateway_ssh_reachable=true
gateway_hostname=ai-secretary-gateway-node023
ai_secretary_gateway_service=inactive_disabled
gateway_unit_verify=OK
target_listeners_443_8080_8081=ABSENT
ufw=active_default_deny
ufw_8080_tcp=ALLOW_FROM_92.118.85.117_ONLY
gateway_env_metadata=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
realtime_gateway_marker_openai_event_type_counts_available=PRESENT
realtime_measurement_symbol_diagnose_pcm_wav_audio_bytes=PRESENT
service_action=false
listener_started=false
```

## Phase B Stimulus Plan

Phase B must not run without exact approval.

Planned stimulus:

```text
non_sensitive_generated_speech_like_stimulus
speech_duration_longer_than_NODE_032AG
audio_format=24000_hz_mono_16_bit_pcm
duration_reported_before_smoke=true
rms_reported_before_smoke=true
peak_reported_before_smoke=true
non_silent_ratio_reported_before_smoke=true
no_real_caller_audio=true
no_sensitive_audio=true
no_committed_audio_binary_artifacts=true
actual_transcript_text_redacted=true
```

Planned success target:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent>0
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_length_bucket=nonzero_bucket
actual_transcript_text_redacted=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
```

## Phase B Gate

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
approval_phrase=APPROVE NODE-032AK PHASE B LIVE SMOKE
```

Phase B approval was received exactly and hard gates were re-confirmed immediately before the smoke.

## Phase B Smoke Result

```text
phase_b_started_after_exact_approval=true
hard_gates_reconfirmed=true
repo_branch_is_NODE_032AK=true
repo_source_runtime_diff_empty=true
asterisk_OPENAI_API_KEY_absent=true
business_dialog_gateway_transcript_flag_not_enabled=true
transcript_text_logging_flag_not_enabled=true
gateway_service_initial_state=inactive_disabled
gateway_no_unexpected_target_listeners=true
ufw_source_restricted=true
gateway_secret_presence_masked_only=true
deployed_realtime_gateway_has_openai_event_type_counts_available=true
deployed_realtime_measurement_has_diagnose_pcm_wav_audio_bytes=true
```

Stimulus diagnostics:

```text
stimulus_duration_ms=4000
stimulus_rms=0.191375
stimulus_peak=0.715424
stimulus_non_silent_ratio=0.857115
stimulus_format=24000_hz_mono_16_bit_pcm
no_real_caller_audio=true
no_sensitive_audio=true
no_committed_audio_binary_artifacts=true
```

Smoke result:

```text
smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
openai_event_type_counts_present=true
openai_event_type_counts={conversation.item.added:1,conversation.item.done:1,conversation.item.input_audio_transcription.completed:1,input_audio_buffer.committed:1,session.created:1,session.updated:1}
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
actual_transcript_text_redacted=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

NODE-032AK did not achieve the target `transcript_text_length_bucket=nonzero_bucket`.

## Phase B Cleanup And Final State

```text
temporary_helper_removed=true
temporary_env_removed=true
temporary_audio_removed=true
local_temporary_helper_bundle_removed=true
gateway_service_final_state=inactive_disabled
target_listeners_final_state=443_absent_8080_absent_8081_absent
firewall_final_state=unchanged_source_restricted
asterisk_OPENAI_API_KEY_final_state=ABSENT
business_dialog_gateway_transcript_flag_not_enabled=true
transcript_text_logging_flag_not_enabled=true
adapter_default_enabled_after_smoke=false
```

## Phase B Outcome

```text
node_outcome=BLOCKED_TRANSCRIPT_CONTENT_STILL_EMPTY
transport_auth_runtime_diagnostics=pass
transcript_content_target=blocked
next_recommendation=NODE-032AL / transcript-content-empty-after-prepared-stimulus-analysis
```

## Validation

```text
focused_suite=50_passed
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found_existing_placeholders_status_test_fixtures_only
scoped_docs_source_tests_scan=no_real_secret_values_found_existing_placeholders_status_test_fixtures_only
transcript_text_delta_scan=no_transcript_text_or_delta_content_added_status_fields_only
audio_binary_artifact_scan=none_added
```

## Safety

NODE-032AK Phase A did not run SSH beyond sanitized read-only gates, run live smoke, place a test call, deploy helpers, handle tokens, read or print token values, create temp env files, create or upload audio stimulus, start/stop/restart/reload/enable services, install dependencies, reboot, power-cycle, change firewall, edit server env, log transcript text/deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
