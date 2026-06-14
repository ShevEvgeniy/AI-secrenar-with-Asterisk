# NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default

## Summary

NODE-032BG ran exactly one approved Asterisk-side controlled smoke after NODE-032BF was merged.

Result:

```text
approval_phrase=APPROVE NODE-032BG CONTROLLED DISABLED-BY-DEFAULT LIVE SMOKE
node_outcome=PARTIAL_DISABLED_DIALOG_USE_LIVE_SMOKE_WITH_POLICY_FIELD_GAP
hard_gate_result=GO
smoke_attempt_count=1
gateway_request=true
repeated_smoke_loop=false
```

The live path reached Gateway/Auth/OpenAI Realtime and remained safe: transcript text and deltas were not logged, token/env values were not printed, and dialog transcript use stayed disabled. The smoke did not fully prove the NODE-032BF policy-reporting boundary because the deployed Asterisk helper/runtime report did not include the new `business_dialog_transcript_*` policy fields.

## Branch

```text
feat/node-032bg-controlled-business-dialog-transcript-use-live-smoke-disabled-by-default
```

## Preflight

Repository:

```text
starting_master_head=9cfec3ea972e3b60b5d7804a16c3ed9a26f92b74
focused_validation_before_smoke=65_passed
```

Asterisk:

```text
asterisk_reachable=true
hostname=tula
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_process_running=true
ai_secretary_process_running=true
helper_present=true
helper_executable=true
helper_mode=755
credential_boundary_present=true
credential_boundary_mode=600
credential_required_keys_present=true
credential_values_printed=false
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_enabled=false
raw_transcript_logging=false
listener_443_present=false
listener_8080_present=false
listener_8081_present=false
```

Gateway:

```text
gateway_reachable=true
hostname=ai-secretary-gateway-node023
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
gateway_unit_verify_ok=true
gateway_env_file_present=true
gateway_env_file_path=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_mode=640
gateway_openai_key_present_masked=true
gateway_token_present_masked=true
gateway_env_values_printed=false
ufw_active=true
ufw_default_incoming_deny=true
ufw_8080_source_restricted=true
listener_443_present=false
listener_8080_present=false
listener_8081_present=false
```

Hard gates:

```text
asterisk_reachable=true
asterisk_ready=true
helper_present=true
helper_executable=true
credential_boundary_present=true
credential_values_not_printed=true
gateway_reachable=true
gateway_start_allowed=true
business_dialog_transcript_policy_enabled=false
raw_transcript_logging=false
prepared_audio_only=true
smoke_count_planned=1
hard_gate_result=GO
```

## Smoke Window

Gateway was started only for the approved smoke window:

```text
gateway_service_start=performed
gateway_service_active_after_start=active
gateway_service_enabled_after_start=disabled
listener_443_present_after_start=false
listener_8080_present_after_start=true
listener_8081_present_after_start=false
```

The Asterisk-side helper created and validated a temporary synthetic prepared test WAV:

```text
audio_path=/tmp/node032bg-smoke.wav
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
frame_count=24000
audio_duration_ms=1000
real_customer_audio=false
audio_committed=false
```

Exactly one smoke invocation ran with `--audio /tmp/node032bg-smoke.wav`.

Smoke result:

```text
smoke_attempt_count=1
adapter_smoke_exercised_node025_path=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
transcript_text_logged=false
transcript_used_for_dialog=false
dialog_transcript_used=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

Safe redaction:

```text
token_values_printed=false
env_values_printed=false
authorization_header_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
stt_gateway_token_configured=redacted_marker_only
```

## Policy Field Gap

NODE-032BF added `business_dialog_transcript_*` policy metadata to the local adapter. The live Asterisk-side smoke report did not include those fields.

Classification:

```text
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=not_reported_by_deployed_helper
business_dialog_transcript_used_for_dialog=false_by_dialog_flag_and_report
node032bf_policy_runtime_reporting_proven=false
gap=deployed_helper_or_runtime_policy_fields_not_visible_in_smoke_report
```

This means NODE-032BG proves the live path still fails safely with dialog transcript use disabled, but it should not be treated as a full live proof that the newly implemented NODE-032BF policy reporting is deployed and observable on Asterisk.

## Cleanup And Final State

Gateway was stopped because NODE-032BG started it.

```text
gateway_service_stop=performed
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
listener_443_present=false
listener_8080_present=false
listener_8081_present=false
temporary_audio_removed=true
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_enabled=false
raw_transcript_logging=false
```

## Validation

```text
focused_pytest=65_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
server_access_after_approval=bounded_to_preflight_smoke_cleanup
ssh_used=true
provider_controls_used=false
gateway_power_action=false
smoke_attempt_count=1
second_smoke_attempt=false
call_run=false
phase_b=false
real_customer_audio=false
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
helper_deploy=false
credential_boundary_recreated=false
temp_env_created=false
service_enable_disable_restart_reload=false
docker_mutation=false
firewall_or_env_mutation=false
server_or_app_config_mutation=false
audio_committed=false
server_dump_or_log_artifact_added=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Next Recommendation

```text
NODE-032BH / controlled-asterisk-helper-runtime-refresh-for-business-transcript-policy-fields
```

The next node should be separate and approval-gated. It should validate or refresh the deployed Asterisk helper/runtime bundle so the NODE-032BF `business_dialog_transcript_*` policy fields are present in the smoke report before any later enabled business-dialog transcript-use validation.

