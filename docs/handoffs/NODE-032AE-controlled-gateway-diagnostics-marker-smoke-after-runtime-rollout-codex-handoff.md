# NODE-032AE / controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout

## Handoff

This handoff records NODE-032AE Phase A readiness and Phase B blocked live-smoke attempt after NODE-032AD runtime rollout. It excludes token values, raw env output, transcript text, transcript deltas, audio artifacts, binary artifacts, large logs, Notion writes, and Runtime/Evidence updates.

## Base

```text
branch=feat/node-032ae-controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout
base_master_head=d82bd8f783c9240b0830975ac5b5f49d8b72d756
phase_b_approval_phrase=APPROVE NODE-032AE PHASE B LIVE SMOKE
```

## Gate Results

```text
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
asterisk_service=active_enabled
asterisk_process_OPENAI_API_KEY=absent
asterisk_service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
gateway_service_before=inactive_disabled
target_listeners_443_8080_8081=absent
ufw_active_default_deny=true
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_masked_secret_presence=passed
deployed_realtime_gateway_marker_present=true
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
```

## Preparation

```text
local_helper_bundle_create_ok=true
local_helper_bundle_validate_ok=true
remote_helper_preflight_ok=true
runtime_modules_ok=true
smoke_audio_created=true
smoke_audio_validated=true
smoke_audio_format=24000_hz_mono_16bit_pcm_wav
safe_temp_env_create_ok=true
safe_temp_env_validate_ok=true
safe_temp_env_mode=600
token_supplied_via_stdin_only=true
token_values_printed=false
transcript_text_printed=false
```

## Blocker

Gateway service readiness failed before the Asterisk-side smoke helper invocation.

```text
gateway_service_start_attempted=true
gateway_listener_8080_seen=false
smoke_helper_invoked=false
gateway_request_reached=false
openai_realtime_from_gateway=not_run
error_type=ImportError
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
importing_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
diagnostic_classification=service_readiness_import_error
```

Interpretation:

```text
NODE_032AD_deployed_realtime_gateway_py=true
matching_realtime_measurement_runtime_not_deployed=true
```

## Required Smoke Fields

```text
gateway_reachable_from_asterisk=not_run
gateway_auth=not_run
gateway_http_status=not_run
openai_realtime_from_gateway=not_run
openai_session_created=not_run
chunks_sent=not_run
openai_event_type_counts_available=not_run
openai_event_type_counts_present=not_run
openai_event_type_counts=not_run
transcript_event_seen=not_run
transcript_bearing_event_seen=not_run
transcript_text_present=not_run
transcript_text_length_bucket=not_run
input_audio_buffer_commit_sent=not_run
timeout_observed=not_run
error_event_seen=not_run
diagnostic_propagation_gap=not_run
diagnostic_classification=service_readiness_import_error
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Cleanup / Final State

```text
gateway_service_final=inactive_disabled
gateway_target_listeners_443_8080_8081=absent
firewall_unchanged=true
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
deployed_realtime_gateway_marker_present=true
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
asterisk_process_OPENAI_API_KEY=absent
asterisk_service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
remote_helper_removed=true
remote_temp_env_removed=true
remote_audio_removed=true
local_temp_helper_bundle_removed=true
```

## Next Recommendation

```text
NODE-032AF / controlled-gateway-runtime-measurement-dependency-rollout
```

## Validation

```text
focused_suite=50_passed
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found_existing_placeholders_status_test_fixtures_only
scoped_docs_source_tests_scan=no_real_secret_values_found_status_placeholders_test_fixtures_only
transcript_text_delta_scan=no_new_transcript_text_or_delta_content_added
audio_binary_artifact_scan=none_added
```

## Safety

```text
live_smoke=false
smoke_helper_invoked=false
gateway_request_reached=false
token_values_printed=false
transcript_text_logged=false
transcript_delta_logged=false
business_dialog_enablement=false
systemctl_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
env_change=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
