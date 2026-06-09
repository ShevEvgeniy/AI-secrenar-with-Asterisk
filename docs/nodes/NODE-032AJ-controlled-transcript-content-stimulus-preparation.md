# NODE-032AJ / controlled-transcript-content-stimulus-preparation

Date: 2026-06-09

Branch: `feat/node-032aj-controlled-transcript-content-stimulus-preparation`

Phase: Local repository preparation and documentation only.

## Goal

Prepare the next safe controlled stimulus boundary before another live smoke.

NODE-032AJ is not a live-smoke node.

## Context

NODE-032AI merged at:

```text
65ab5aa93d167c83630b3d8ac7941d26e5431430
```

NODE-032AI accepted the diagnostics propagation proof from NODE-032AG/NODE-032AH and classified the remaining issue as empty/zero transcript content, not transport/auth/runtime propagation failure.

Accepted prior proof:

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

Unproven hypotheses carried forward:

```text
smoke_audio_too_short
speech_stimulus_not_clear_or_speech_like_enough
audio_clipped_or_silence_dominant
commit_timing_or_buffer_window_too_short
session_transcription_settings_need_review
language_or_prompt_context_not_optimal
provider_transcription_completed_empty_despite_event
```

## Stimulus Strategy

The next live smoke should use a prepared stimulus with these target properties:

```text
speech_duration_longer_than_NODE_032AG
clear_speech_like_waveform
not_silence_dominant
not_clipped
24000_hz_mono_16_bit_pcm
pre_smoke_duration_reported=true
pre_smoke_rms_reported=true
pre_smoke_peak_reported=true
pre_smoke_non_silent_ratio_reported=true
no_real_caller_audio=true
no_sensitive_audio=true
no_committed_audio_binary_artifacts=true
```

NODE-032AJ does not invent, create, stage, or commit a final WAV. The next node may use a runtime-generated or approved local-only stimulus, but no real caller audio or sensitive audio may be committed.

## Redacted Success Metrics

The next live smoke should report:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent>0
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=true_or_nonzero_bucket
transcript_text_length_bucket=nonzero_bucket
actual_transcript_text_redacted=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
```

The evidence should use `transcript_text_length_bucket`. It must not require or allow actual transcript text to be logged.

## Out Of Scope

```text
business_dialog_integration
production_autostart
real_customer_call
dual_channel_recording_proof
transcript_text_logging
using_transcript_for_dialog
customer_audio
committed_audio_artifacts
```

## Decision

Recommend the next boundary:

```text
NODE-032AK / controlled-transcript-content-smoke-with-prepared-stimulus
```

Rationale:

- NODE-032AJ prepares the stimulus strategy only.
- NODE-032AK can later run one controlled smoke using this prepared strategy after exact approval.
- The next boundary must not jump to business-dialog integration or real customer calls.
- Transcript text must remain redacted and business-dialog transcript use must remain disabled.

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

NODE-032AJ did not run SSH, access servers, run live smoke, run a test call, deploy helpers, handle tokens, read or print token values, create temp env files, start/stop/restart/reload/enable services, install dependencies, reboot, power-cycle, change firewall, edit server env, log transcript text/deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
