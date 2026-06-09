# NODE-032AO / Safe Actual Speech Stimulus And Session Settings Plan

## Scope

NODE-032AO is a local repository planning node after NODE-032AN. It does not run a live smoke and does not change runtime code.

```text
branch=feat/node-032ao-safe-actual-speech-stimulus-and-session-settings-plan
scope=repo_planning_docs_only
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
dependency_install=false
reboot_or_power_cycle=false
firewall_or_env_change=false
server_state_change=false
transcript_text_or_delta_logging=false
```

Handoff archive:

```text
docs/handoffs/NODE-032AO-safe-actual-speech-stimulus-and-session-settings-plan-codex-handoff.md
```

## 1 Current Evidence Summary

NODE-032AK proved the deployed Gateway transport/auth/runtime diagnostics path:

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

NODE-032AK did not prove non-empty transcript content:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

NODE-032AK stimulus metrics were strong enough to rule out simple silence or format failure, but did not prove actual linguistic speech content:

```text
stimulus_duration_ms=4000
stimulus_sample_rate=24000
stimulus_channels=1
stimulus_sample_width=16_bit_pcm
stimulus_rms=0.191375
stimulus_peak=0.715424
stimulus_non_silent_ratio=0.857115
actual_linguistic_content_proven=false
```

NODE-032AN proved local parser and redaction behavior with placeholder-safe fixtures:

```text
local_nonzero_bucket_mapping_proven=true
current_schema_fields_covered=true
selected_alternate_schema_fields_covered=true
empty_completed_event_preserves_zero_bucket=true
placeholder_transcript_values_not_serialized=true
late_delta_after_completed=deferred
```

Remaining unproven items:

```text
actual_linguistic_content_in_live_stimulus=false
future_provider_nonzero_transcript=false
session_settings_content_quality=false
late_delta_after_completed=false
business_dialog_integration=false
production_autostart=false
```

## 2 Safe Actual Speech Stimulus Requirements

The next live content smoke must use a safe actual-speech stimulus instead of synthetic tones, silence, or a speech-like signal that lacks linguistic proof.

Required stimulus label:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
stimulus_expected_language=ru
stimulus_expected_content_bucket=nonempty_linguistic
```

The exact spoken content must not be committed, logged, or included in handoffs. The stimulus must satisfy:

```text
non_sensitive_content_only=true
real_customer_audio=false
real_caller_audio=false
personal_data=false
medical_financial_private_content=false
sensitive_or_token_material=false
audio_file_committed=false
audio_file_logged=false
transcript_text_committed=false
transcript_delta_committed=false
live_transcript_text_logged=false
live_transcript_delta_logged=false
```

Required audio format and local quality checks:

```text
format=24000_hz_mono_16_bit_pcm_wav
duration_bucket=short_command
rms_checked=true
peak_checked=true
non_silent_ratio_checked=true
clipping_checked=true
silence_dominance_checked=true
language_label_matches_session_setting=true
```

## 3 Stimulus Proof Without Committing Audio

Future proof must be metadata-only. It may record safe labels and metrics, never audio or text:

```text
generation_recipe_hash_or_label_only=true
ephemeral_audio_created_in_future_node=true
ephemeral_audio_deleted_after_future_smoke=true
duration_ms_recorded=true
sample_rate_recorded=true
channels_recorded=true
sample_width_recorded=true
rms_recorded=true
peak_recorded=true
non_silent_ratio_recorded=true
content_bucket_label_recorded=true
actual_text_recorded=false
audio_byte_count_recorded=false
audio_file_committed=false
```

Future cleanup proof must include:

```text
temporary_audio_removed=true
temporary_env_removed=true
temporary_helper_removed=true
local_temporary_bundle_removed=true
audio_binary_artifact_scan_clean=true
transcript_text_or_delta_scan_clean=true
```

## 4 Session Settings Matrix

The next live smoke should isolate the stimulus variable before changing session configuration. Current settings have already proven transport, session creation, audio commit, and transcript event observation.

| Setting | Current / Planned Value | NODE-032AO Classification | Rationale |
| --- | --- | --- | --- |
| `model` | `gpt-realtime-whisper` | keep_for_next_smoke | Transport/session/event path is proven; changing model would add a second variable. |
| `language` | `ru` | keep_for_next_smoke | Future stimulus is labeled `SAFE_RU_SHORT_COMMAND`; language should match. |
| `sample_rate` | `24000` | keep_for_next_smoke | Format is already accepted by Gateway and OpenAI path. |
| `audio_format` | mono 16-bit PCM WAV upload, Gateway PCM chunks | keep_for_next_smoke | NODE-032U and later nodes proved this boundary. |
| `chunk_ms` | `200` | keep_for_next_smoke | Audio chunks were sent and events were observed. |
| `turn_detection` | current deployed default | keep_for_next_smoke | Change only in a separate session-settings node if actual speech remains empty. |
| `noise_reduction` | current deployed default | keep_for_next_smoke | Avoid mixing acoustic preprocessing changes with the stimulus proof. |
| `prompt_or_context` | current deployed default | deferred_candidate_change | Possible future lever, but not for the first actual-speech stimulus smoke. |
| `commit_timing` | append chunks then `input_audio_buffer.commit` | keep_for_next_smoke | Commit and completed transcript events were already observed. |
| `timeout` | current helper/Gateway default | keep_for_next_smoke | Completed events arrived; extending timeout is a later lever if needed. |

## 5 Preflight Gate Design

Future live smoke preflight must fail closed before token handling, temp env creation, helper deploy, service start, or Gateway request if any hard gate fails.

Repository gates:

```text
expected_branch_confirmed=true
source_runtime_diff_reviewed=true
no_audio_binary_artifacts=true
no_transcript_text_or_delta_added=true
no_real_token_values_in_repo=true
course_submission_untracked_untouched=true
data_storage_untracked_untouched=true
node014_server_tar_untracked_untouched=true
```

Asterisk gates:

```text
ssh_reachable=true
ai_secretary_ari_service_active_enabled=true
OPENAI_API_KEY_absent_in_service_env=true
OPENAI_API_KEY_absent_in_process_env=true
business_dialog_gateway_transcript_flag_not_enabled=true
transcript_text_logging_flag_not_enabled=true
target_listeners_443_8080_8081_absent=true
```

Gateway gates:

```text
ssh_reachable=true
gateway_unit_verify_ok=true
gateway_service_initially_inactive_disabled=true
gateway_env_metadata_root_gateway_640=true
gateway_masked_presence_only=true
target_listeners_443_8080_8081_absent_before_smoke=true
ufw_active_default_deny=true
ufw_8080_allowed_only_from_92_118_85_117=true
```

Stimulus gates:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
actual_text_not_printed=true
audio_format_24000_hz_mono_16_bit_pcm=true
audio_quality_metrics_recorded=true
audio_not_committed=true
```

## 6 Redaction And Logging Boundary

Allowed evidence fields:

```text
duration_ms
sample_rate
channels
sample_width
rms
peak
non_silent_ratio
chunks_sent
openai_event_type_counts
openai_event_type_counts_available
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
diagnostic_classification
gateway_http_status
openai_realtime_from_gateway
openai_session_created
business_dialog_unchanged
adapter_default_enabled_after_smoke
```

Forbidden evidence:

```text
token_values
raw_env_output_with_sensitive_material
transcript_text
transcript_delta
provider_event_body_that_contains_text
audio_body_content
audio_file_body_content
real_customer_or_caller_audio
private_or_personal_content
```

## 7 Future Live Smoke Phase Gates

Recommended next node:

```text
NODE-032AP / controlled-actual-speech-transcript-content-smoke
```

Future approval phrase:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```

Any other phrase is not approval. NODE-032AP Phase B should run exactly one controlled Asterisk-side non-business-dialog smoke only after immediate hard-gate re-confirmation.

Expected NODE-032AP acceptance target:

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

If transcript content remains empty after a safe actual-speech stimulus, the next boundary should be a separate session-settings or provider-event-order analysis node, not repeated live attempts.

## 8 Rejected Or Deferred Options

Rejected in NODE-032AO:

```text
live_smoke_now
ssh_or_server_access
token_handling
temp_env_creation
helper_deploy
service_action
firewall_or_env_change
audio_generation
audio_upload
business_dialog_integration
production_autostart
real_customer_audio
committed_audio_fixture
logging_actual_transcript_text
logging_transcript_deltas
multiple_smoke_retries
```

Deferred:

```text
late_delta_after_completed_support
session_settings_change
prompt_or_context_change
noise_reduction_change
turn_detection_change
business_dialog_transcript_use
dual_channel_recording_or_caller_bot_separation
```

## 9 Next Node Recommendation

```text
NODE-032AP / controlled-actual-speech-transcript-content-smoke
```

Purpose:

```text
Run one controlled Asterisk-side, non-business-dialog Gateway smoke with an ephemeral safe actual-speech stimulus and existing proven session settings, after exact approval and immediate hard-gate re-confirmation.
```

Boundary:

```text
phase_a=read_only_readiness_and_command_plan
phase_b=exactly_one_live_smoke_after_exact_approval
approval_phrase=APPROVE NODE-032AP PHASE B LIVE SMOKE
no_business_dialog_transcript_use=true
no_transcript_text_logging=true
no_token_output=true
cleanup_required=true
```
