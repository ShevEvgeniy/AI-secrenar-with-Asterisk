# Codex Handoff - NODE-032BJ / controlled-enabled-business-dialog-transcript-use-validation-design

## Result

NODE-032BJ is a repo-only design/preflight closeout for future enabled business-dialog transcript-use validation.

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

## Current Truth

```text
NODE_032BF_policy_code_exists=true
NODE_032BG_disabled_live_path_safe=true
NODE_032BH_safe_runtime_policy_fields_visible=true
NODE_032BI_policy_fields_visible_in_disabled_smoke=true
business_dialog_transcript_use_enabled=false
enabled_live_dialog_use_proven=false
```

## Future Temporary Flags

Future enabled validation requires a separate approval and explicit temporary flags:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
```

Companion safety settings:

```text
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS=30000
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## Future Hard Gates

```text
asterisk_ssh_reachable
gateway_ssh_reachable
asterisk_OPENAI_API_KEY_absent
helper_present_and_executable
policy_module_present
business_policy_fields_visible_in_safe_diagnostic
gateway_unit_verify_ok
gateway_env_present_masked_only
gateway_secret_presence_masked_only
target_listeners_443_8080_8081_absent_before_smoke
ufw_active_default_deny
ufw_8080_source_restricted_to_asterisk
transcript_text_logging_disabled
transcript_delta_logging_disabled
token_values_printed=false
raw_env_values_printed=false
```

## Future Stop Gates

```text
raw_transcript_text_would_be_logged
transcript_delta_would_be_logged
token_or_env_value_would_be_printed
authorization_header_would_be_printed
business_dialog_transcript_policy_fields_missing
temporary_flags_not_confirmed_or_not_removable
more_than_one_smoke_needed_without_new_approval
real_customer_or_caller_audio_required
service_enable_restart_reload_required_without_approval
docker_mutation_required
disk_image_action_required
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
gateway_restored_to_safe_state=true
temporary_flags_removed=true
adapter_default_enabled_after_smoke=false
```

## Future Rollback

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
```

## Future Evidence Format

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
audio_payload
audio_file_content
server_dump_or_log_artifacts
```

## Non-Proofs

NODE-032BJ does not prove enabled business-dialog transcript use, live enabled smoke, production call path, real caller/customer audio, semantic accuracy, latency/SLA, repeated-run stability, load/error resilience, production monitoring/alerting, or approval to persistently enable transcript use.

## Next Recommendation

```text
NODE-032BK / controlled-enabled-business-dialog-transcript-use-live-smoke
```

NODE-032BK must be separately approved. Do not reuse NODE-032BJ approval.
