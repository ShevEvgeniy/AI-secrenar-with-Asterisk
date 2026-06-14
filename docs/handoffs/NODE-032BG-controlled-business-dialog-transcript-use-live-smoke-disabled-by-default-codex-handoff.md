# Codex Handoff - NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default

## Result

NODE-032BG ran one approved controlled Asterisk-side smoke.

```text
node_outcome=PARTIAL_DISABLED_DIALOG_USE_LIVE_SMOKE_WITH_POLICY_FIELD_GAP
smoke_attempt_count=1
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
dialog_transcript_used=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
fallback_reason=gateway_stt_dialog_use_disabled
```

## Important Gap

The smoke did not expose the new NODE-032BF `business_dialog_transcript_*` policy fields in the deployed Asterisk helper/runtime report.

```text
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=not_reported_by_deployed_helper
node032bf_policy_runtime_reporting_proven=false
```

Treat NODE-032BG as proof that the live path remains safe and disabled by the legacy dialog-use gate, not as full proof that NODE-032BF policy reporting is deployed on Asterisk.

## Preflight Summary

Asterisk:

```text
asterisk_reachable=true
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
helper_present=true
helper_executable=true
credential_boundary_present=true
credential_boundary_mode=600
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_enabled=false
raw_transcript_logging=false
```

Gateway:

```text
gateway_reachable=true
ai_secretary_gateway_service_active_before=inactive
ai_secretary_gateway_service_enabled_before=disabled
gateway_unit_verify_ok=true
gateway_env_file_path=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_mode=640
gateway_secret_presence_masked=true
ufw_active=true
ufw_default_incoming_deny=true
ufw_8080_source_restricted=true
target_listeners_absent_before=true
```

## Cleanup

```text
gateway_service_stop=performed
gateway_service_active_final=inactive
gateway_service_enabled_final=disabled
listener_443_present_final=false
listener_8080_present_final=false
listener_8081_present_final=false
temporary_audio_removed=true
asterisk_OPENAI_API_KEY_absent_final=true
business_dialog_transcript_policy_enabled_final=false
raw_transcript_logging_final=false
```

## Validation

```text
focused_pytest=65_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
real_customer_audio=false
audio_committed=false
helper_deploy=false
temp_env_created=false
credential_boundary_recreated=false
service_enable_disable_restart_reload=false
docker_mutation=false
firewall_or_env_mutation=false
server_or_app_config_mutation=false
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

Do not reuse NODE-032BG approval. The next node must be separately approved.

