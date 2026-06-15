# NODE-032BM / controlled-enabled-live-smoke-retry-with-safe-env-loader

## Summary

NODE-032BM prepares the approval-gated retry of the enabled business-dialog transcript-use live smoke using the NODE-032BL quote-safe helper path.

Phase 1 result:

```text
node_outcome=REPO_READINESS_PREPARED_PENDING_EXACT_LIVE_APPROVAL
repo_readiness_prepared=true
live_approval_received=false
live_preflight_run=false
dry_run_env_check_run=false
smoke_count=0
gateway_request_sent=false
enabled_live_dialog_use_proven=false
final_proof_classification=blocked_pending_exact_live_approval
```

Phase 2 result:

```text
approval_phrase_received=true
required_approval_phrase=APPROVE NODE-032BM CONTROLLED ENABLED LIVE SMOKE WITH SAFE ENV LOADER
read_only_live_preflight_started=true
asterisk_read_only_gates_passed=true
gateway_ssh_reachable=false
gateway_ssh_result=timeout
hard_gate_result=NO_GO
dry_run_env_check_run=false
gateway_started=false
smoke_count=0
gateway_request_sent=false
enabled_live_dialog_use_proven=false
final_proof_classification=blocked
classification=blocked_pending_kamatera_gateway_power_on
```

No smoke, Gateway start, Gateway request, token handling, transcript enablement, or temp env creation occurred.

Coordinator clarification: Kamatera/Gateway host had not been powered on by the operator before the Phase 2 Gateway SSH check. Therefore the observed Gateway SSH timeout is treated as an expected infrastructure precondition, not as an unexplained Gateway failure.

## Branch

```text
feat/node-032bm-controlled-enabled-live-smoke-retry-with-safe-env-loader
```

## Base

```text
starting_master_head=fc07e8c466402982613b49c36dcbebfaef234602
```

## Approval Status

The exact approval phrase was provided for Phase 2:

```text
APPROVE NODE-032BM CONTROLLED ENABLED LIVE SMOKE WITH SAFE ENV LOADER
```

Approval allowed read-only live preflight first. The Gateway SSH gate timed out, so NODE-032BM stopped before quote-safe env dry-run and before smoke. Coordinator later clarified that Kamatera/Gateway had not yet been powered on, so the timeout is now classified as `blocked_pending_kamatera_gateway_power_on` rather than an unexplained Gateway failure.

Forbidden before approval:

```text
ssh=false
server_access=false
asterisk_inspection=false
gateway_inspection=false
gateway_start=false
smoke=false
transcript_enablement=false
token_handling=false
real_env_value_handling=false
service_action=false
docker_action=false
firewall_action=false
server_or_app_config_mutation=false
live_audio_generation_or_upload=false
disk_image_action=false
```

## Current Truth

NODE-032BK passed live preflight and hard gates but failed closed before Gateway request:

```text
NODE_032BK_classification=blocked_command_quoting_env_dump_missing_gateway_flags
gateway_request_sent=false
enabled_live_dialog_use_proven=false
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
shell_environment_dump_printed=true
second_smoke_or_retry=false
```

NODE-032BL prepared the quote-safe helper path:

```text
quote_safe_env_loading_preflight_ready=true
enabled_live_dialog_use_proven=false
```

Supported helper options:

```text
--env-file <path>
--dialog-transcript-use disabled
--dialog-transcript-use enabled
--dry-run-env-check
```

## Future Required Helper Path

After exact approval only, future live execution must first use the quote-safe dry-run shape:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --dry-run-env-check
```

Only if every hard gate and dry-run gate passes may the approved smoke use:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --audio <approved_audio_path>
```

The future command path must not use shell `source`, `set -a`, nested shell quoting, inline env dumps, token output, Authorization header output, raw transcript text output, or transcript delta output.

## Temporary Smoke Flags

Allowed only inside the future approved smoke window:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

No persistent transcript-use enablement is approved by Phase 1.

## Future Hard Gates

After exact approval and before any smoke, the future operator must verify:

```text
asterisk_ssh_reachable
gateway_ssh_reachable
ai_secretary_ari_service_active_enabled
asterisk_OPENAI_API_KEY_absent_in_service_and_process_env
helper_present_executable
policy_module_present
safe_diagnostic_policy_fields_visible
gateway_initial_state_recorded
gateway_target_listeners_443_8080_8081_absent_or_exact_pre_state_recorded
firewall_active_default_deny
8080_tcp_restricted_to_asterisk_source
gateway_env_secret_presence_masked_booleans_only
quote_safe_dry_run_env_check_passed
no_token_or_env_values_printed
no_authorization_headers_printed
no_raw_transcript_text_printed
no_transcript_deltas_printed
no_shell_environment_dump_printed
rollback_path_clear
```

If any gate fails, NODE-032BM must stop before smoke with `smoke_count=0`.

## Acceptance Criteria

Enabled proof may be accepted only if all of the following are true:

```text
exact_approval_phrase_received=true
read_only_preflight_passed=true
quote_safe_dry_run_env_check_passed=true
exactly_one_controlled_enabled_smoke_ran=true
gateway_request_sent=true
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent_gt_0=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=true
transcript_text_diagnostics_redacted_or_bucketed_only=true
business_dialog_transcript_policy_enabled=true
business_dialog_transcript_allowed=true
business_dialog_transcript_used_for_dialog=true
dialog_transcript_used=true
transcript_text_logged=false
transcript_delta_logged=false
token_values_printed=false
raw_env_values_printed=false
authorization_header_printed=false
shell_environment_dump_printed=false
temporary_flags_removed=true
temporary_env_removed=true
temporary_audio_removed=true
gateway_restored_to_safe_state=true
asterisk_OPENAI_API_KEY_absent_after_cleanup=true
transcript_logging_disabled_after_cleanup=true
adapter_default_remains_disabled_after_smoke=true
second_smoke_or_retry=false
```

If smoke runs but proof is incomplete, close as partial or blocked, not as enabled proof.

## Phase 1 Repo Readiness

Phase 1 records the safe retry plan only:

```text
repo_readiness_result=prepared
live_preflight_result=not_run_no_approval
quote_safe_dry_run_env_check_result=not_run_no_approval
hard_gate_result=not_run_no_approval
smoke_count=0
gateway_request_result=not_sent
transcript_event_diagnostics=not_run
business_dialog_transcript_policy_result=not_proven
cleanup_or_rollback_result=not_needed_no_live_action
```

## Phase 2 Read-Only Preflight

Asterisk read-only gates:

```text
asterisk_ssh_reachable=true
hostname=tula
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
helper_present=true
helper_executable=true
policy_module_present=true
credential_boundary_present=true
credential_boundary_nonempty=true
credential_boundary_mode=600
required_gateway_env_keys_present=true
service_OPENAI_API_KEY_absent=true
process_OPENAI_API_KEY_absent=true
business_dialog_transcript_flag_not_enabled=true
transcript_text_logging_disabled=true
secret_values_printed=false
raw_env_values_printed=false
```

Gateway read-only gates:

```text
gateway_ssh_reachable=false
gateway_ssh_result=timeout
operator_clarification=kamatera_gateway_not_powered_on_before_check
timeout_interpretation=expected_infrastructure_precondition
gateway_service_initial_state=not_checked_due_ssh_timeout
gateway_listeners=not_checked_due_ssh_timeout
firewall_source_restriction=not_checked_due_ssh_timeout
gateway_env_metadata=not_checked_due_ssh_timeout
gateway_secret_presence_masked=not_checked_due_ssh_timeout
```

Stop result:

```text
hard_gate_result=NO_GO
blocker=gateway_ssh_timeout
classification=blocked_pending_kamatera_gateway_power_on
quote_safe_dry_run_env_check_run=false
gateway_start=false
smoke_count=0
gateway_request_sent=false
second_smoke_or_retry=false
```

## Cleanup And Rollback

No smoke-window state was created because the stop gate occurred before dry-run env check and before Gateway start.

```text
temporary_flags_created=false
temporary_env_created=false
temporary_audio_created=false
temporary_helper_created=false
gateway_service_action=false
gateway_restore_required=false
firewall_change_attempted=false
service_or_app_config_change_attempted=false
asterisk_OPENAI_API_KEY_absent_after_stop=true
transcript_logging_disabled_after_stop=true
```

## Validation

```text
focused_helper_adapter_bundle_temp_env_tests=45_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
ssh_used=false
server_access=false
provider_controls=false
gateway_action=false
gateway_state_inspection=false
gateway_start=false
smoke_run=false
call_run=false
phase_b=false
gateway_request=false
transcript_enablement=false
token_handling=false
real_env_value_handling=false
openai_request=false
service_action=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
live_audio_generation_or_upload=false
disk_image_touched=false
notion_write=false
runtime_evidence_write=false
```

Safety scan result:

```text
no_real_tokens=true
no_gateway_token_strings=true
no_authorization_headers=true
no_raw_env_values=true
no_shell_environment_dumps=true
no_raw_transcript_text=true
no_transcript_deltas=true
no_audio_log_temp_env_server_dump_or_disk_image_artifacts=true
```

Protected artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Final Classification

```text
enabled_live_dialog_use_proven=false
final_proof_classification=blocked
classification=blocked_pending_kamatera_gateway_power_on
```
