# NODE-032BO / controlled-enabled-live-smoke-retry-after-readiness-passed

## Summary

NODE-032BO prepares the next approval-gated enabled live smoke retry after NODE-032BN confirmed server power-on readiness.

Phase 1 result:

```text
node_outcome=PHASE1_REPO_PLANNING_READY_PENDING_SERVER_POWER_ON
phase=phase1_repo_planning_only
server_power_on_requested=false
live_server_action=false
ssh_used=false
preflight_run=false
quote_safe_dry_run_env_check_run=false
gateway_started=false
smoke_run=false
gateway_request_sent=false
enabled_live_dialog_use_proven=false
final_classification=phase1_repo_planning_ready_pending_server_power_on
```

This node does not infer that servers are currently powered on or available.

## Branch

```text
feat/node-032bo-controlled-enabled-live-smoke-retry-after-readiness-passed
```

## Base

```text
starting_master_head=c469802c5b549be353681e1e49e0342cef1f9c97
```

## Inherited Truth

```text
NODE_032BM_classification=blocked_pending_kamatera_gateway_power_on
NODE_032BN_classification=readiness_passed
NODE_032BN_asterisk_ssh_reachable=true
NODE_032BN_gateway_ssh_reachable=true
NODE_032BN_gateway_service_active=inactive
NODE_032BN_gateway_service_enabled=disabled
NODE_032BN_gateway_target_listeners_443_8080_8081_absent=true
enabled_live_dialog_use_proven=false
```

Codex continuation was paused after NODE-032BN; servers may have been powered off until resume. NODE-032BO Phase 1 must not request power-on and must not access servers.

## Phase 1 Scope

Allowed:

```text
create_or_update_NODE_032BO_docs=true
update_master_docs=true
record_future_live_flow_and_guardrails=true
local_repo_inspection_only=true
local_validation_only=true
```

Forbidden:

```text
ssh=false
server_access=false
asterisk_access=false
gateway_access=false
read_only_preflight=false
quote_safe_dry_run_env_check=false
gateway_start=false
smoke=false
gateway_request=false
token_or_real_env_value_handling=false
transcript_use_flags_enabled=false
service_mutation=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
live_audio_generation_or_upload=false
disk_image_touched=false
notion_write=false
runtime_evidence_write=false
```

## Future Live/Server Gate

Future live phase may begin only after all of the following occur in coordinator chat:

```text
coordinator_explicitly_tells_operator_which_servers_to_power_on=true
operator_confirms_asterisk_92_118_85_117_powered_on=true
operator_confirms_kamatera_gateway_45_61_48_199_powered_on=true
coordinator_issues_new_explicit_live_server_instruction_for_NODE_032BO=true
```

No live approval is inherited from NODE-032BM or NODE-032BN.

## Future Live Phase Order

After the future live/server gate is satisfied, the required order is:

```text
step_1=read_only_quick_preflight
step_2=quote_safe_dry_run_env_check
step_3=gateway_start_only_if_all_hard_gates_pass
step_4=exactly_one_controlled_enabled_smoke
step_5=safe_diagnostics_only
step_6=cleanup_rollback
step_7=stop_for_coordinator_review
```

Stop before the next step if any gate fails.

## Future Helper Path

Future quote-safe dry-run env validation must use:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --dry-run-env-check
```

Only if all hard gates pass may the future smoke use:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --audio <approved_audio_path>
```

## Future Temporary Smoke Flags

Use only during the future approved smoke window:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

No persistent transcript-use enablement is allowed.

## Future Stop Conditions

Stop before smoke if any of these are true:

```text
server_power_on_not_confirmed=true
asterisk_ssh_unreachable=true
gateway_ssh_unreachable=true
asterisk_OPENAI_API_KEY_present=true
business_dialog_transcript_use_already_enabled=true
transcript_text_logging_enabled=true
helper_or_policy_missing=true
credential_boundary_missing_or_wrong_mode=true
gateway_unexpected_listener_or_runtime_state=true
gateway_firewall_not_source_restricted=true
gateway_env_secret_presence_not_maskable=true
quote_safe_dry_run_env_check_failed=true
token_or_env_value_would_be_printed=true
authorization_header_would_be_printed=true
raw_transcript_text_or_delta_would_be_printed=true
shell_environment_dump_would_be_printed=true
gateway_start_requires_unapproved_mutation=true
second_smoke_or_retry_needed_without_new_approval=true
```

## Future Acceptance Criteria

The future enabled live dialog proof may be accepted only if:

```text
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
adapter_default_remains_disabled_after_smoke=true
second_smoke_or_retry=false
```

## Validation

```text
git_diff_check=passed
source_runtime_diff=empty
pytest_run=false
pytest_skip_reason=docs_only_node
```

## Safety Scans

```text
changed_docs_secret_token_env_dump_transcript_delta_hits=0
added_line_secret_token_env_dump_transcript_delta_hits=0
audio_binary_temp_env_log_server_dump_disk_artifact_hits=0
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Final Classification

```text
final_classification=phase1_repo_planning_ready_pending_server_power_on
```


## Pause Handoff (2026-07-11)

```text
status=Paused, reproducible checkpoint
enabled_live_dialog_use_proven=false
```

The repository-approved helper is deployed and validated, but the existing credential boundary does not satisfy `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` and `BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true`. The project was intentionally paused after the agreed two-day decision sprint. No credential mutation, retry, Gateway start, or enabled smoke is approved.

Resume after reprioritization through a separate temporary-enabled-credential-boundary node. One quote-safe dry-run must pass before any Gateway start or controlled enabled smoke.
