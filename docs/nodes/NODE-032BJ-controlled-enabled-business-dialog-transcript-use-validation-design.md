# NODE-032BJ / controlled-enabled-business-dialog-transcript-use-validation-design

## Summary

NODE-032BJ is a repository-only design/preflight node for a future enabled business-dialog transcript-use validation.

Result:

```text
node_outcome=REPO_ONLY_ENABLED_TRANSCRIPT_USE_VALIDATION_DESIGN
live_validation_performed=false
enabled_transcript_use_proven=false
business_dialog_transcript_use_enabled=false
ssh_used=false
server_access=false
gateway_action=false
smoke_run=false
token_handling=false
runtime_or_service_mutation=false
```

NODE-032BJ does not perform live validation and does not prove enabled business-dialog transcript use.

## Branch

```text
feat/node-032bj-controlled-enabled-business-dialog-transcript-use-validation-design
```

## Base

```text
starting_master_head=053f83e5d3f7d85d54f3d632baf3efbaf95db017
```

## Current Truth

```text
NODE_032BF_policy_code_exists=true
NODE_032BG_disabled_live_path_safe=true
NODE_032BH_safe_runtime_policy_fields_visible=true
NODE_032BI_policy_fields_visible_in_disabled_smoke=true
business_dialog_transcript_use_enabled=false
enabled_live_dialog_use_proven=false
```

NODE-032BI proved that `business_dialog_transcript_*` policy fields are visible in disabled live smoke diagnostics while business-dialog transcript use remains disabled.

NODE-032BI did not prove enabled business-dialog transcript use.

## Scope

Allowed in NODE-032BJ:

```text
repo_only_docs_design_preflight=true
future_validation_boundary_defined=true
future_flags_defined=true
future_hard_gates_defined=true
future_stop_gates_defined=true
future_rollback_defined=true
future_diagnostics_defined=true
future_evidence_format_defined=true
```

Forbidden in NODE-032BJ:

```text
ssh=false
server_access=false
provider_controls=false
gateway_action=false
smoke=false
transcript_enablement=false
token_handling=false
service_action=false
docker_mutation=false
firewall_env_server_app_config_change=false
audio=false
disk_image_action=false
notion_write=false
runtime_evidence_write=false
```

## Future Temporary Flags

Future enabled validation must use explicit temporary flags only for the approved smoke window:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
```

Required companion constraints:

```text
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS=30000
BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE=explicit_or_default_recorded
STT_GATEWAY_LOG_TRANSCRIPT=false
```

The future node must not persistently enable these flags in the deployed service profile unless separately approved. Temporary runtime state must be removed during cleanup.

## Future Hard Gates

Before any future enabled smoke, re-check:

```text
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
ai_secretary_ari_service_expected_state_recorded=true
asterisk_OPENAI_API_KEY_absent=true
helper_present_and_executable=true
policy_module_present=true
business_policy_fields_visible_in_safe_diagnostic=true
gateway_service_initial_state_inactive_disabled_or_exact_state_recorded=true
gateway_unit_verify_ok=true
gateway_env_present_masked_only=true
gateway_secret_presence_masked_only=true
target_listeners_443_8080_8081_absent_before_smoke=true
ufw_active_default_deny=true
ufw_8080_source_restricted_to_asterisk=true
transcript_text_logging_disabled=true
transcript_delta_logging_disabled=true
token_values_printed=false
raw_env_values_printed=false
```

If any hard gate fails, the future node must stop before smoke and report the blocker.

## Future Stop Gates

Stop immediately if any condition appears:

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

## Future Smoke Limit

```text
exactly_one_enabled_smoke_allowed=true
second_smoke_requires_new_explicit_approval=true
real_call_allowed=false
real_caller_or_customer_audio_allowed=false
```

The future smoke must be one controlled Asterisk-side non-customer validation using prepared non-sensitive audio only.

## Future Redaction Guarantees

Allowed evidence:

```text
booleans=true
counts=true
length_buckets=true
confidence_buckets=true
age_buckets=true
redacted_markers=true
diagnostic_classifications=true
hashes_without_payload=true
```

Forbidden evidence:

```text
raw_transcript_text=false
transcript_delta_content=false
raw_provider_event_body_with_text=false
token_values=false
authorization_headers=false
raw_env_values=false
audio_payload=false
audio_file_content=false
server_dump_or_log_artifacts=false
```

## Future Required Diagnostics

Future enabled validation must capture safe fields:

```text
gateway_reachable_from_asterisk
gateway_auth
gateway_http_status
openai_realtime_from_gateway
openai_session_created
chunks_sent
openai_event_type_counts_available
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
business_dialog_transcript_policy_enabled
business_dialog_transcript_allowed
business_dialog_transcript_used_for_dialog
business_dialog_transcript_reason
business_dialog_transcript_fail_closed
business_dialog_transcript_redact_logs
business_dialog_transcript_redaction_required
business_dialog_transcript_age_bucket
business_dialog_transcript_confidence_bucket
business_dialog_transcript_length_bucket
dialog_transcript_used
fallback_reason
transcript_text_logged
transcript_delta_logged
business_dialog_unchanged_or_expected_controlled_change
adapter_default_enabled_after_smoke
```

## Future Acceptance Criteria

The future enabled-validation node may be accepted only if all required criteria are met:

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
gateway_restored_to_safe_state=true
temporary_flags_removed=true
adapter_default_enabled_after_smoke=false
```

If transcript content is absent, metadata is incomplete, confidence/age gates fail, or policy decision is not allowed, the future node must classify the result as blocked or partial proof rather than successful enabled transcript use.

## Future Rollback And Cleanup

Required future cleanup:

```text
remove_temporary_flags=true
remove_temporary_env=true
remove_temporary_audio=true
remove_temporary_helper_or_bundle_if_created=true
restore_gateway_service_to_pre_smoke_state=true
keep_gateway_disabled_unless_previously_enabled=true
confirm_no_target_listeners_443_8080_8081=true
confirm_firewall_unchanged_source_restricted=true
confirm_asterisk_OPENAI_API_KEY_absent=true
confirm_transcript_logging_disabled=true
confirm_no_token_or_transcript_output=true
```

Rollback plan:

```text
if_enabled_policy_causes_failure_remove_temporary_flags=true
if_gateway_start_was_used_stop_gateway=true
if_helper_or_env_was_staged_remove_temporary_artifacts=true
if_unexpected_listener_seen_stop_before_request=true
if_raw_sensitive_output_risk_seen_stop_and_report_security_blocker=true
```

## Future Runtime/Evidence Format

Future Runtime/Evidence entry should be safe JSON or Markdown with only:

```text
node_id
approval_phrase
gate_results
smoke_attempt_count
safe_diagnostic_fields
redacted_length_buckets
event_counts
cleanup_results
validation_results
safety_scan_results
explicit_non_proofs
next_recommendation
```

It must not include raw transcript text, transcript deltas, token values, authorization headers, raw env values, audio payloads, server dumps, or log files.

## Explicit Non-Proofs

NODE-032BJ does not prove:

```text
enabled_business_dialog_transcript_use=false
live_enabled_smoke=false
production_call_path=false
real_caller_or_customer_audio=false
semantic_transcript_accuracy=false
latency_or_sla=false
repeated_run_stability=false
load_or_error_resilience=false
production_monitoring_or_alerting=false
approval_to_persistently_enable_transcript_use=false
```

## Validation

```text
focused_gateway_adapter_tests=19_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
no_ssh=true
no_server_access=true
no_gateway_action=true
no_smoke=true
no_transcript_enablement=true
no_token_handling=true
no_service_action=true
no_docker_firewall_env_server_app_config_change=true
no_audio=true
no_disk_image_action=true
```

Protected local artifacts must remain untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Next Recommendation

```text
NODE-032BK / controlled-enabled-business-dialog-transcript-use-live-smoke
```

NODE-032BK must be separately approved and must not reuse NODE-032BJ repo-only approval.
