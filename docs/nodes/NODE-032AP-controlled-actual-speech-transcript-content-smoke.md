# NODE-032AP / Controlled Actual Speech Transcript Content Smoke

## Scope

NODE-032AP Phase A is read-only preflight and planning for a future controlled actual-speech transcript-content smoke.

```text
phase=Phase_A_read_only_preflight_only
branch=feat/node-032ap-controlled-actual-speech-transcript-content-smoke
source_runtime_change=false
live_smoke=false
audio_generated=false
audio_uploaded=false
temp_env_created=false
helper_deploy=false
token_handling=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_or_env_change=false
server_state_change=false
transcript_text_or_delta_logging=false
business_dialog_integration=false
```

Handoff archive:

```text
docs/handoffs/NODE-032AP-controlled-actual-speech-transcript-content-smoke-codex-handoff.md
```

## Current Context

NODE-032AO selected the future safe actual-speech stimulus boundary:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
expected_language=ru
expected_content_bucket=nonempty_linguistic
actual_spoken_text_committed=false
audio_committed=false
transcript_text_committed=false
```

The first next smoke should keep the current proven settings to isolate the stimulus variable:

```text
model=gpt-realtime-whisper
language=ru
sample_rate=24000
chunk_ms=200
turn_detection=unchanged
noise_reduction=unchanged
prompt_or_context=unchanged
```

NODE-032AK live reference proved transport/auth/runtime diagnostics:

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

NODE-032AK did not prove content:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

NODE-032AN reduced local schema risk:

```text
selected_alternate_schema_fixtures_supported=true
nonzero_placeholder_text_maps_to_nonzero_redacted_bucket=true
empty_transcript_bearing_events_remain_zero_bucket=true
placeholder_values_not_serialized_in_reports=true
```

## Phase A Local Validation

Local focused validation passed:

```text
python_focused_suite=55_passed
git_diff_check=passed
source_runtime_diff=empty
repo_branch_exact=true
```

Focused command:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
```

## Phase A Read-Only Server Preflight

The read-only Asterisk SSH gate failed before Gateway-side checks:

```text
asterisk_host=92.118.85.117
asterisk_ssh_reachable=false
asterisk_ssh_result=timeout_to_port_22
gateway_ssh_checked=false
gateway_host=45.61.48.199
```

Because the first required server gate failed, Phase A stopped without further server checks.

Checked or inferred gates:

```text
repo_branch_exact=passed
source_runtime_diff_empty=passed
asterisk_ssh_reachable=failed_timeout
gateway_ssh_reachable=not_checked_after_asterisk_gate_failure
asterisk_openai_api_key_absent_masked_only=not_checked
gateway_env_file_exists_masked_only=not_checked
gateway_service_initial_state=not_checked
target_listeners_443_8080_8081=not_checked
firewall_source_restricted=not_checked
business_dialog_transcript_use_disabled=not_checked
transcript_text_logging_disabled=not_checked
transcript_delta_logging_disabled=not_checked
no_unexpected_gateway_process_running=not_checked
```

Phase B recommendation:

```text
phase_b_recommendation=NO_GO
blocker=asterisk_ssh_timeout
```

## Future Stimulus Readiness Plan

No audio was generated in Phase A. The future stimulus remains metadata-only:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
expected_language=ru
expected_content_bucket=nonempty_linguistic
audio_format=24000_hz_mono_16_bit_pcm_wav
duration_bucket=short_controlled
audio_committed=false
actual_spoken_text_committed=false
```

Allowed future Phase B stimulus metrics:

```text
duration_ms
sample_rate
channels
sample_width
rms_bucket_or_value
peak_bucket_or_value
non_silent_ratio_bucket_or_value
clipping_check
silence_dominance_check
```

Forbidden outputs:

```text
actual_spoken_phrase
transcript_text
transcript_delta
provider_event_body_that_contains_text
token_values
audio_body_content
audio_file_body_content
```

## Phase B Blocked Until Exact Approval

Phase B must not run in this node turn and remains blocked by the Asterisk SSH timeout.

Exact future approval phrase:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```

Any other phrase is not approval.

## Future Phase B Plan

After Asterisk SSH reachability is restored and the exact approval phrase is provided, Phase B should:

1. Re-run immediate hard gates for Asterisk and Gateway.
2. Create only ephemeral safe actual-speech audio with no committed phrase or audio content.
3. Validate 24 kHz mono 16-bit PCM WAV and safe stimulus metrics.
4. Use safe stdin-only Gateway token handling.
5. Create any temporary env only through the safe guard.
6. Deploy the helper bundle only for the single smoke attempt.
7. Start Gateway service only for smoke readiness if required.
8. Run exactly one controlled Asterisk-side non-business-dialog smoke.
9. Capture only redacted metrics and transcript presence/bucket flags.
10. Clean temporary helper/env/audio artifacts.
11. Restore Gateway service to the pre-smoke safe state.
12. Verify no target listeners, firewall unchanged, Asterisk `OPENAI_API_KEY` absent, and business dialog unchanged.

Phase B target metrics:

```text
exactly_one_smoke_ran=true
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent_gt_0=true
openai_event_type_counts_available=true
openai_event_type_counts_present=true
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
temporary_audio_removed=true
temporary_env_removed=true
temporary_helper_removed=true
gateway_service_restored=true
```

## Safety Constraints

Forbidden in Phase B unless separately approved by the coordinator:

```text
business_dialog_integration
transcript_text_logging
transcript_delta_logging
token_value_output
multiple_smoke_retries
service_enablement
dependency_install
reboot_or_power_cycle
firewall_broadening
persistent_env_change
audio_or_binary_commit
Notion_write
Runtime_or_Evidence_update
```
