# NODE-032AI / controlled-transcript-content-stimulus-quality-plan

Date: 2026-06-08

Branch: `feat/node-032ai-controlled-transcript-content-stimulus-quality-plan`

Phase: Local repository planning and documentation only.

## Goal

Create the next safe transcript-content investigation plan after NODE-032AH accepted NODE-032AG as deployed Gateway diagnostics propagation proof.

NODE-032AI is not a live-smoke node.

## Context

NODE-032AH merged at:

```text
16c8e5ead04b2d17044d6abf5eaf58a6cd9f0300
```

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

NODE-032AG did not prove transcript text correctness or non-empty transcript content:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
```

Safety remained intact:

```text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Problem Classification

The remaining issue is classified as:

```text
empty_or_zero_transcript_content
```

It is not currently classified as:

```text
gateway_transport_failure=false
gateway_auth_failure=false
gateway_runtime_propagation_failure=false
openai_realtime_session_failure=false
```

Reasoning:

- Gateway HTTP status was `200`.
- OpenAI Realtime from Gateway was `ok`.
- Session creation succeeded.
- Audio chunks were sent.
- Redacted event diagnostics were available and present.
- Transcript-bearing event observation was true.
- `diagnostic_propagation_gap=false`.

## Hypotheses

The following likely causes remain hypotheses only:

```text
smoke_audio_too_short
speech_stimulus_not_clear_or_speech_like_enough
audio_clipped_or_silence_dominant
commit_timing_or_buffer_window_too_short
session_transcription_settings_need_review
language_or_prompt_context_not_optimal
provider_transcription_completed_empty_despite_event
```

NODE-032AI does not prove any one cause. It narrows the next work to stimulus/session quality because the Gateway/Auth/OpenAI Realtime and diagnostic propagation path has already been proven.

## Next Smoke Design Constraints

The next live smoke, if separately approved later, should preserve:

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

Expected evidence target:

```text
transcript_text_length_bucket moves from zero to nonzero bucket
```

Actual transcript text must remain redacted. The smoke should record only safe booleans, event-count fields, and length buckets.

## Stimulus Improvements To Prepare

The next preparation node should define a safer stimulus strategy with:

```text
longer_speech_duration
clearer_speech_like_waveform
avoid_clipping
avoid_silence_dominant_segments
explicit_sample_rate_format_validation=24000_hz_mono_16_bit_pcm_wav
pre_smoke_audio_diagnostics_duration=true
pre_smoke_audio_diagnostics_rms=true
pre_smoke_audio_diagnostics_peak=true
pre_smoke_audio_diagnostics_non_silent_ratio=true
no_committed_real_caller_audio=true
no_committed_sensitive_audio=true
```

Acceptable future stimulus options to decide:

```text
longer_generated_speech
known_safe_speech_fixture
strictly_documented_local_only_generated_stimulus
```

NODE-032AI does not create, stage, or commit real audio artifacts.

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

Proceed to a preparation-only boundary:

```text
NODE-032AJ / controlled-transcript-content-stimulus-preparation
```

Rationale:

- A repeat live smoke should not run until the content stimulus is better specified.
- The next node should define expected audio characteristics without committing real caller audio or sensitive audio.
- The next node should define redacted success metrics before live action.
- The next node should keep transcript text suppressed and business-dialog transcript use disabled.

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

NODE-032AI did not run SSH, access servers, run live smoke, run a test call, deploy helpers, handle tokens, read or print token values, create temp env files, start/stop/restart/reload/enable services, install dependencies, reboot, power-cycle, change firewall, edit server env, log transcript text/deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
