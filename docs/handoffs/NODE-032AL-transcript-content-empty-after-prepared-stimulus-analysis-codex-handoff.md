# NODE-032AL Codex Handoff

Node:

```text
NODE-032AL / transcript-content-empty-after-prepared-stimulus-analysis
```

Branch:

```text
feat/node-032al-transcript-content-empty-after-prepared-stimulus-analysis
```

Scope:

```text
repo_local_analysis_only=true
live_smoke=false
ssh=false
helper_deploy=false
token_handling=false
temp_env=false
service_action=false
firewall_env_server_change=false
audio_generation=false
commit_or_pr=false
```

## Context

NODE-032AK ran exactly one controlled Asterisk-side non-business-dialog smoke with a prepared non-sensitive stimulus. The smoke proved the Gateway/Auth/OpenAI Realtime diagnostics path but did not produce non-zero redacted transcript content.

NODE-032AK result summary:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
```

Prepared stimulus diagnostics:

```text
stimulus_duration_ms=4000
stimulus_sample_rate=24000
stimulus_channels=1
stimulus_sample_width=16_bit_pcm
stimulus_rms=0.191375
stimulus_peak=0.715424
stimulus_non_silent_ratio=0.857115
```

## Local Code Findings

`src/ai_secretary/stt/realtime_gateway.py` records transcript text presence before redacting or withholding transcript text. It marks non-zero text when a non-empty `delta` or completed-event `transcript` field is observed.

`src/ai_secretary/stt/gateway_adapter.py` preserves safe Gateway diagnostic fields after removing any `transcript_text` value.

`src/ai_secretary/stt/gateway_adapter_smoke.py` reports safe transcript event fields and classifies a transcript-bearing event with no text as:

```text
transcript_event_observed_empty_or_no_text
```

`src/ai_secretary/stt/realtime_measurement.py` builds a transcription session with:

```text
model=gpt-realtime-whisper
language=ru
sample_rate=24000
turn_detection=None
noise_reduction=None
prompt_or_extra_context=absent
```

Local tests already prove that when transcript text exists in synthetic events, the redacted length bucket remains non-zero even when transcript text is not returned to the caller.

## Ranked Hypotheses

1. `audio_semantics_not_real_speech_despite_signal_metrics`

The prepared stimulus had valid 24 kHz mono PCM format, higher duration, high RMS, and a high non-silent ratio, but it was still a generated speech-like waveform rather than known linguistic speech. The provider emitted a transcript-bearing completed event with empty content, which is consistent with an uncertain or non-speech-like signal.

2. `provider_completed_empty_event_expected_under_current_input`

The code and tests treat a completed transcription event with empty text as a valid diagnostic outcome, not a transport failure. NODE-032AK had no timeout, no error event, no diagnostic propagation gap, and no auth/session failure.

3. `session_transcription_settings_suboptimal_for_synthetic_stimulus`

The session uses model/language/sample-rate settings but no prompt or context. `turn_detection` and `noise_reduction` are disabled. These settings reached OpenAI Realtime successfully, but may not be sufficient for a synthetic non-word stimulus.

4. `language_or_model_context_issue`

The configured language is Russian, while the prepared stimulus did not prove actual Russian lexical content. The model may complete empty when the acoustic signal is speech-like but not recognizably linguistic.

5. `event_field_or_response_path_gap`

The Gateway checks the expected `delta` and completed-event `transcript` fields. Existing tests prove these paths work for synthetic payloads, but a future local schema review can still verify current provider event shapes without logging transcript text.

6. `audio_commit_or_receive_window_issue`

This is less likely because `input_audio_buffer_commit_sent=true`, `chunks_sent=20`, the completed event arrived, and `timeout_observed=false`.

7. `gateway_or_helper_event_race_condition`

This is less likely because the completed event is terminal evidence and no late delta evidence was recorded.

8. `redaction_or_bucket_logic_false_zero`

This is weakest because local tests prove non-zero text presence survives redaction as a bucket, and the Gateway computes presence before suppressing transcript text.

## Rejected Causes

```text
transport_auth_runtime_blocker=false
diagnostic_propagation_gap=false
gateway_secret_or_env_blocker=false
firewall_or_listener_blocker=false
business_dialog_disabled_caused_empty_transcript=false
transcript_text_redaction_caused_false_zero=unlikely_existing_tests_cover
```

## Selected Next Boundary

Recommended next node:

```text
NODE-032AM / transcript-content-empty-local-schema-and-stimulus-analysis
```

The next node should remain local/repo-only. It should verify current OpenAI Realtime transcription event schema assumptions, compare event-field handling against local tests, and design a safe non-sensitive actual-speech stimulus/settings strategy before any further live smoke.

## Safety

No live smoke, SSH, helper deploy, token handling, temp env creation, audio generation, service action, dependency install, reboot, firewall/env/server change, transcript text logging, transcript delta logging, Notion write, Runtime/Evidence update, scheduler/webhook/automation, commit, push, or PR occurred in NODE-032AL.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
