# NODE-032AE / controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout

## Goal

Run one controlled Asterisk-side non-business-dialog Gateway smoke after NODE-032AD rolled out the safe diagnostics marker into the deployed Gateway runtime.

NODE-032AE Phase B was approved, but the live smoke did not run because Gateway service readiness failed before the Asterisk-side smoke helper invocation.

## Base

```text
branch=feat/node-032ae-controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout
base_master_head=d82bd8f783c9240b0830975ac5b5f49d8b72d756
previous_node=NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
phase_b_approval_phrase=APPROVE NODE-032AE PHASE B LIVE SMOKE
```

## Phase A And Phase B Gates

```text
asterisk_ssh_reachable=true
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_process_OPENAI_API_KEY=absent
asterisk_service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
asterisk_target_listeners_443_8080_8081=absent
gateway_ssh_reachable=true
gateway_hostname=ai-secretary-gateway-node023
gateway_service_before=inactive_disabled
gateway_unit_verify=ok
gateway_target_listeners_443_8080_8081_before=absent
ufw_active=true
ufw_default_incoming=deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_masked_secret_presence=passed
deployed_realtime_gateway_marker_present=true
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
```

No token values or raw env values were printed.

## Phase B Approval

```text
APPROVE NODE-032AE PHASE B LIVE SMOKE
```

## Smoke Preparation

```text
local_helper_bundle_created=true
local_helper_bundle_validated=true
remote_helper_staged=true
remote_helper_preflight_ok=true
runtime_modules_ok=true
smoke_audio_created=true
smoke_audio_validated=true
smoke_audio_format=24000_hz_mono_16bit_pcm_wav
safe_temp_env_created=true
safe_temp_env_validated=true
safe_temp_env_mode=root:root 600
gateway_token_supplied_via_stdin_only=true
secret_values_printed=false
transcript_text_logged=false
```

## Blocker

Gateway service readiness failed before the controlled smoke helper invocation.

```text
gateway_service_start_attempted=true
gateway_service_active_state=activating_then_failed
gateway_listener_8080_seen=false
error_type=ImportError
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
importing_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
```

Cause:

```text
NODE_032AD_deployed_realtime_gateway_py=true
matching_realtime_measurement_py_not_deployed=true
```

The smoke did not run:

```text
smoke_helper_invoked=false
gateway_request_reached=false
openai_realtime_from_gateway=not_run
```

## Required Smoke Result Fields

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

Recommended NODE-032AF boundary:

```text
read_only_inventory_deployed_realtime_measurement_py
compare_local_and_deployed_hashes
after_exact_approval_back_up_and_roll_out_matching_realtime_measurement_py
verify_gateway_service_readiness
do_not_run_smoke_unless separately approved
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

## Handoff

```text
docs/handoffs/NODE-032AE-controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout-codex-handoff.md
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
gateway_stt_default_enablement=false
systemctl_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
env_change=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
