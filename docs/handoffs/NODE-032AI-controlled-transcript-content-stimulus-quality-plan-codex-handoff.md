# NODE-032AI / controlled-transcript-content-stimulus-quality-plan Handoff

Date: 2026-06-08

Branch: `feat/node-032ai-controlled-transcript-content-stimulus-quality-plan`

Phase: Local repository planning and documentation only.

Base master HEAD:

```text
16c8e5ead04b2d17044d6abf5eaf58a6cd9f0300
```

## Scope

NODE-032AI plans the next safe transcript-content investigation boundary after NODE-032AH accepted NODE-032AG as deployed Gateway diagnostics propagation proof.

This node is not a live-smoke node. It did not use SSH, access servers, run smoke, run a test call, deploy helpers, handle tokens, create temp env files, perform service actions, install dependencies, reboot, power-cycle, change firewall/env/server state, log transcript text or deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

## Accepted Prior Proof

NODE-032AH accepted NODE-032AG as successful deployed Gateway diagnostics propagation proof:

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

The accepted proof means the deployed Gateway/Auth/OpenAI Realtime path works and redacted diagnostics now propagate. It does not prove transcript text correctness or non-empty transcript content.

Remaining limitation:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
```

Safety boundary preserved:

```text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Classification

NODE-032AI classifies the remaining issue as:

```text
problem_class=empty_or_zero_transcript_content
not_gateway_transport_failure=true
not_gateway_auth_failure=true
not_openai_realtime_session_failure=true
not_runtime_diagnostics_propagation_failure=true
```

## Hypotheses

The following are hypotheses only. NODE-032AI does not prove any of them:

```text
smoke_audio_too_short
speech_stimulus_not_clear_or_speech_like_enough
audio_clipped_or_silence_dominant
commit_timing_or_buffer_window_too_short
session_transcription_settings_need_review
language_or_prompt_context_not_optimal
provider_transcription_completed_empty_despite_event
```

## Next Smoke Design Constraints

Any future smoke should remain:

```text
one_controlled_smoke_only
non_business_dialog_only
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
transcript_event_seen=true
transcript_bearing_event_seen=true
actual_transcript_text_redacted=true
```

The target improvement is:

```text
transcript_text_length_bucket=nonzero_bucket
```

Actual transcript text must remain suppressed in logs, docs, chat, and committed artifacts.

## Stimulus Improvements To Prepare

The next boundary should prepare a safer stimulus strategy before another live smoke:

```text
longer_speech_duration
clearer_speech_like_waveform
avoid_clipping
avoid_silence_dominant_segments
validate_24000_hz_mono_16_bit_pcm_wav
pre_smoke_audio_diagnostics_duration
pre_smoke_audio_diagnostics_rms
pre_smoke_audio_diagnostics_peak
pre_smoke_audio_diagnostics_non_silent_ratio
no_committed_real_caller_audio
no_committed_sensitive_audio
```

The stimulus may be a longer generated speech fixture, a known-safe speech fixture, or a strictly documented local-only generated stimulus, but NODE-032AI does not create or commit audio artifacts.

## Out Of Scope

```text
business_dialog_integration
production_autostart
real_customer_call
dual_channel_recording_proof
transcript_text_logging
using_transcript_for_dialog
```

## Decision

Recommend a preparation-only next node before another live smoke:

```text
NODE-032AJ / controlled-transcript-content-stimulus-preparation
```

Rationale:

- The previous live result already proves transport/auth/runtime diagnostics propagation.
- The remaining limitation is empty transcript text, so the next work should improve and measure the stimulus rather than repeat the same smoke unchanged.
- Transcript text must remain redacted.
- Business-dialog transcript use must remain disabled.

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

## Untouched Local Artifacts

```text
course_submission/
data/storage/
node014-server.tar
```
