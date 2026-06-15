# NODE-032BK / controlled-enabled-business-dialog-transcript-use-live-smoke

## Summary

NODE-032BK Phase 2 received the exact approval phrase, ran read-only hard-gate preflight, then attempted one controlled enabled smoke command.

The smoke command failed closed before any Gateway request because the remote shell quoting loaded neither `STT_GATEWAY_URL` nor `STT_GATEWAY_TOKEN`. The same quoting issue printed a non-secret shell environment dump, so NODE-032BK is classified as blocked and no second smoke was run.

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

## Branch

```text
feat/node-032bk-controlled-enabled-business-dialog-transcript-use-live-smoke
```

## Base

```text
starting_master_head=9bd7b3f55a1dda6627530e2547e57df815b9c271
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

NODE-032BJ was repo-only design/preflight. It did not perform live validation and did not prove enabled transcript use.

## Phase 1 Scope

Allowed before exact approval:

```text
create_feature_branch=true
inspect_repo_files_locally=true
prepare_docs_and_checklists=true
run_local_tests=true
run_git_diff_and_status_checks=true
```

Forbidden before exact approval:

```text
ssh=false
server_access=false
provider_controls=false
gateway_action=false
gateway_state_inspection=false
smoke=false
transcript_enablement=false
token_handling=false
service_action=false
docker_firewall_env_server_app_config_change=false
audio_upload_or_generation_for_live_use=false
disk_image_action=false
```

## Approval Gate

NODE-032BK requires the exact future approval phrase before any SSH/server/Gateway/smoke/transcript-enable action:

```text
APPROVE NODE-032BK CONTROLLED ENABLED LIVE SMOKE
```

Current task status:

```text
exact_approval_phrase_present=true
phase_2_read_only_live_preflight_allowed=true
phase_3_controlled_enabled_smoke_allowed=true_after_hard_gates
```

## Future Temporary Flags

Future approved smoke must use temporary flags only for the approved smoke window:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

These flags were documented in NODE-032BK Phase 1 but not used.

```text
temporary_flags_used=attempted_process_only
temporary_flags_persisted=false
deployed_service_config_changed=false
```

## Phase 2 Read-Only Preflight

Asterisk:

```text
asterisk_ssh_reachable=true
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_service_OPENAI_API_KEY_absent=true
asterisk_process_OPENAI_API_KEY_absent=true
helper_executable=true
policy_module_present=true
business_policy_fields_visible_in_safe_diagnostic=true
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_redact_logs=true
business_dialog_transcript_fail_closed=true
transcript_text_logged=false
secret_values_printed=false
```

Gateway:

```text
gateway_ssh_reachable=true
gateway_service_initial_active=inactive
gateway_service_initial_enabled=disabled
gateway_unit_verify_ok=true
gateway_listener_443_present_before_start=false
gateway_listener_8080_present_before_start=false
gateway_listener_8081_present_before_start=false
ufw_active=true
ufw_default_incoming_deny=true
ufw_8080_source_restricted_to_asterisk=true
gateway_env_file_present_nonempty=true
gateway_env_mode=640
gateway_openai_key_present_masked=true
gateway_token_present_masked=true
secret_values_printed=false
```

Hard gates passed, so Gateway was started only for smoke readiness:

```text
gateway_service_active_after_start=active
gateway_service_enabled_after_start=disabled
gateway_listener_443_present_after_start=false
gateway_listener_8080_present_after_start=true
gateway_listener_8081_present_after_start=false
```

## Future Read-Only Live Preflight

Only after exact approval, future Phase 2 should check:

Asterisk:

```text
asterisk_ssh_reachable
asterisk_OPENAI_API_KEY_absent
helper_runtime_present_and_executable
safe_diagnostic_only
policy_fields_visible
transcript_text_logging_disabled
transcript_delta_logging_disabled
token_env_values_printed=false
```

Gateway:

```text
gateway_ssh_reachable
gateway_pre_state_recorded
target_listeners_443_8080_8081_absent_or_exact_pre_state_recorded
ufw_active_default_deny
ufw_8080_source_restricted_to_asterisk
gateway_env_and_secret_presence_masked_booleans_only
token_env_values_printed=false
```

Stop before smoke if any hard gate fails.

## Controlled Enabled Smoke Attempt

Temporary non-customer audio was created and validated:

```text
audio_sample_rate_hz=24000
audio_channels=1
audio_sample_width_bytes=2
audio_compression=PCM
audio_format_errors=[]
real_call_allowed=false
real_caller_or_customer_audio_allowed=false
```

Exactly one enabled adapter smoke command invocation was attempted.

```text
smoke_invocation_count=1
gateway_request_sent=false
gateway_http_status=not_run
gateway_auth=not_run
openai_realtime_from_gateway=not_run
openai_session_created=false
chunks_sent=0
transcript_event_seen=false
transcript_bearing_event_seen=false
transcript_text_present=false
dialog_transcript_used=false
enabled_live_dialog_use_proven=false
```

Blocked result:

```text
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
blocker=remote_command_quoting_prevented_gateway_smoke_env_load
raw_shell_environment_dump_printed=true
token_values_printed=false
authorization_header_printed=false
transcript_text_printed=false
transcript_delta_printed=false
gateway_request_sent=false
second_smoke_or_retry=false
```

Because a raw shell environment dump was printed, NODE-032BK stopped at the stop gate. No retry or second smoke was run.

## Future Controlled Enabled Smoke

Only after exact approval and passing hard gates:

```text
start_gateway_only_if_needed_for_smoke_readiness=true
apply_temporary_transcript_use_flags_for_smoke_window_only=true
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

Accept as successful enabled transcript-use proof only if all are true:

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

If transcript content is absent, metadata is incomplete, confidence/age gates fail, or policy decision is not allowed, classify as blocked or partial proof. Do not claim `enabled_live_dialog_use_proven=true`.

## Future Stop Gates

```text
raw_transcript_text_would_be_logged=true
transcript_delta_would_be_logged=true
token_or_env_value_would_be_printed=true
authorization_header_would_be_printed=true
gateway_listener_exposes_unapproved_port=true
firewall_broadened_or_unexpected=true
business_dialog_transcript_policy_fields_missing=true
temporary_flags_not_confirmed_or_not_removable=true
more_than_one_smoke_needed_without_new_approval=true
real_customer_or_caller_audio_required=true
service_enable_restart_reload_required_without_approval=true
docker_mutation_required=true
disk_image_action_required=true
```

## Future Cleanup And Rollback

Always cleanup after an approved smoke attempt or stop condition:

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

## Cleanup And Rollback Result

```text
gateway_service_active_final=inactive
gateway_service_enabled_final=disabled
gateway_listener_443_present_final=false
gateway_listener_8080_present_final=false
gateway_listener_8081_present_final=false
temporary_audio_removed=true
temporary_flags_removed=true
temporary_env_created=false
temporary_helper_created=false
firewall_unchanged_source_restricted=true
asterisk_service_OPENAI_API_KEY_absent_final=true
transcript_logging_disabled_final=true
```

## Allowed Evidence Format

Allowed:

```text
booleans
counts
length_buckets
confidence_buckets
age_buckets
redacted_markers
diagnostic_classifications
hashes_without_payload
```

Forbidden:

```text
raw_transcript_text
transcript_delta_content
token_values
authorization_headers
raw_env_values
audio_payloads
audio_file_content
server_dump_or_log_artifacts
```

## Phase 1 Validation

```text
focused_gateway_adapter_tests=19_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
ssh_used=true
server_access=true
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
raw_transcript_text_exposed=false
transcript_delta_exposed=false
authorization_header_exposed=false
server_dump_or_log_artifact_added=false
raw_shell_environment_dump_printed=true
token_values_exposed=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Proof Classification

```text
enabled_live_dialog_use_proven=false
partial_proof=false
blocked=true
classification=blocked_command_quoting_env_dump_missing_gateway_flags
```

## Next Step

Do not retry NODE-032BK without coordinator review. A future node or explicit re-approval must correct the command quoting/env-load path before another enabled smoke:

```text
APPROVE NODE-032BK CONTROLLED ENABLED LIVE SMOKE
```
