# Codex Handoff - NODE-032BK / controlled-enabled-business-dialog-transcript-use-live-smoke

## Result

NODE-032BK Phase 2 received the exact approval phrase, ran read-only preflight, then attempted exactly one controlled enabled adapter smoke command. The command failed closed before any Gateway request because the Gateway smoke env was not loaded due to remote shell quoting, and the same quoting issue printed a non-secret shell environment dump.

```text
node_outcome=BLOCKED_BEFORE_GATEWAY_REQUEST
approval_phrase_received=true
required_approval_phrase=APPROVE NODE-032BK CONTROLLED ENABLED LIVE SMOKE
live_preflight_run=true
hard_gates_passed=true
smoke_invocation_count=1
gateway_request_sent=false
transcript_enablement_used=attempted_temporary_process_flags_only
enabled_live_dialog_use_proven=false
classification=blocked_command_quoting_env_dump_missing_gateway_flags
```

## Boundary

After approval, live actions were bounded to preflight, Gateway start/stop for smoke readiness, one attempted smoke command, and cleanup.

```text
ssh_used=true
server_access=true
provider_controls=false
gateway_action=start_stop_for_smoke_window
gateway_state_inspection=true
gateway_start=true
smoke_run=attempted_once_before_gateway_request
transcript_enablement=attempted_temporary_process_flags_only
token_handling=false
service_action=false
docker_firewall_env_server_app_config_change=false
audio_generated_or_uploaded=temporary_synthetic_audio_created_removed
disk_image_touched=false
```

## Current Truth

```text
NODE_032BF_policy_code_exists=true
NODE_032BG_disabled_live_path_safe=true
NODE_032BH_safe_runtime_policy_fields_visible=true
NODE_032BI_policy_fields_visible_in_disabled_smoke=true
NODE_032BJ_enabled_validation_design_complete=true
business_dialog_transcript_use_enabled=false
enabled_live_dialog_use_proven=false
```

## Future Approval Gate

The coordinator provided exactly:

```text
APPROVE NODE-032BK CONTROLLED ENABLED LIVE SMOKE
```

## Future Temporary Flags

For the future approved smoke window only:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

These flags were attempted only as temporary process env for the smoke command. They were not persisted.

## Preflight Results

```text
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_service_OPENAI_API_KEY_absent=true
asterisk_process_OPENAI_API_KEY_absent=true
helper_executable=true
policy_module_present=true
business_policy_fields_visible_in_safe_diagnostic=true
transcript_text_logged=false
gateway_service_initial_state=inactive_disabled
gateway_unit_verify_ok=true
gateway_target_listeners_absent_before_start=true
ufw_active_default_deny=true
ufw_8080_source_restricted_to_asterisk=true
gateway_env_and_secret_presence_masked_booleans_only=true
```

## Smoke Attempt

```text
smoke_invocation_count=1
gateway_request_sent=false
gateway_http_status=not_run
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=0
dialog_transcript_used=false
enabled_live_dialog_use_proven=false
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
blocker=remote_command_quoting_prevented_gateway_smoke_env_load
raw_shell_environment_dump_printed=true
token_values_printed=false
authorization_header_printed=false
transcript_text_printed=false
transcript_delta_printed=false
second_smoke_or_retry=false
```

## Future Hard Gates

```text
asterisk_ssh_reachable
asterisk_OPENAI_API_KEY_absent
helper_runtime_present_and_executable
policy_fields_visible
transcript_text_logging_disabled
transcript_delta_logging_disabled
gateway_ssh_reachable
gateway_pre_state_recorded
target_listeners_443_8080_8081_absent_or_exact_pre_state_recorded
ufw_active_default_deny
ufw_8080_source_restricted_to_asterisk
gateway_env_and_secret_presence_masked_booleans_only
token_env_values_printed=false
```

## Future Smoke Constraints

```text
exactly_one_smoke_allowed=true
second_smoke_requires_new_explicit_approval=true
prepared_non_sensitive_audio_only=true
real_call_allowed=false
real_caller_or_customer_audio_allowed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
token_env_values_printed=false
```

## Future Acceptance Criteria

```text
exactly_one_smoke_ran=true
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent_gt_0=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=true
transcript_text_length_bucket=nonzero_redacted
business_dialog_transcript_policy_enabled=true
business_dialog_transcript_allowed=true
business_dialog_transcript_used_for_dialog=true
dialog_transcript_used=true
transcript_text_logged=false
transcript_delta_logged=false
token_values_printed=false
raw_env_values_printed=false
temporary_flags_removed=true
gateway_restored_to_safe_state=true
asterisk_OPENAI_API_KEY_absent_after_cleanup=true
adapter_default_enabled_after_smoke=false
```

## Future Cleanup

```text
remove_temporary_flags=true
remove_temporary_env=true
remove_temporary_audio=true
remove_temporary_helper_or_bundle_if_created=true
restore_gateway_to_pre_smoke_safe_state=true
keep_gateway_disabled_unless_pre_state_proves_enabled=true
confirm_no_target_listeners_443_8080_8081=true
confirm_firewall_unchanged_source_restricted=true
confirm_asterisk_OPENAI_API_KEY_absent=true
confirm_transcript_logging_disabled=true
confirm_no_token_or_transcript_output=true
```

## Cleanup Result

```text
gateway_service_final_state=inactive_disabled
target_listeners_absent_final=true
temporary_audio_removed=true
temporary_env_created=false
temporary_helper_created=false
temporary_flags_removed=true
firewall_unchanged_source_restricted=true
asterisk_service_OPENAI_API_KEY_absent_final=true
transcript_logging_disabled_final=true
```

## Validation

```text
focused_gateway_adapter_tests=19_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
raw_transcript_text_exposed=false
transcript_delta_exposed=false
token_env_values_exposed=false
authorization_header_exposed=false
server_dump_or_log_artifact_added=false
audio_artifact_added=false
temp_env_artifact_added=false
disk_image_touched=false
raw_shell_environment_dump_printed=true
```

Protected artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
