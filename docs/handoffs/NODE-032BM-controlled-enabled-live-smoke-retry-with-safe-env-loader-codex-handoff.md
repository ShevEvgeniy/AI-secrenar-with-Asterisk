# Codex Handoff - NODE-032BM / controlled-enabled-live-smoke-retry-with-safe-env-loader

## Result

NODE-032BM Phase 1 prepared the repository-only retry package for a future enabled business-dialog transcript-use smoke using the NODE-032BL quote-safe helper path.

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

Phase 2 received the exact approval phrase and started read-only live preflight. The Gateway SSH hard gate timed out, so NODE-032BM stopped before quote-safe dry-run env check and before smoke.

```text
approval_phrase_received=true
required_approval_phrase=APPROVE NODE-032BM CONTROLLED ENABLED LIVE SMOKE WITH SAFE ENV LOADER
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
classification=blocked_gateway_ssh_timeout_before_dry_run_env_check
```

## Approval Gate

No live approval is inherited from NODE-032BK or NODE-032BL. Phase 2 received this exact phrase:

```text
APPROVE NODE-032BM CONTROLLED ENABLED LIVE SMOKE WITH SAFE ENV LOADER
```

Until then:

```text
ssh_used=false
server_access=false
asterisk_inspection=false
gateway_inspection=false
gateway_start=false
smoke_run=false
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

Phase 2 live approval was used only for read-only preflight. Because a hard gate failed, no dry-run env check, Gateway start, smoke, Gateway request, token handling, real env value handling, transcript enablement, or temp env creation occurred.

## Inherited Context

NODE-032BK failed closed before Gateway request:

```text
classification=blocked_command_quoting_env_dump_missing_gateway_flags
gateway_request_sent=false
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
shell_environment_dump_printed=true
enabled_live_dialog_use_proven=false
```

NODE-032BL prepared quote-safe env loading:

```text
quote_safe_env_loading_preflight_ready=true
helper_env_file_parser=python_allowlist
shell_source_used=false
set_a_used=false
nested_shell_quoting_required=false
shell_environment_dump_printed=false
```

## Future Command Shape

After exact approval only, first run the dry-run gate:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --dry-run-env-check
```

Only if all hard gates pass:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --audio <approved_audio_path>
```

## Future Temporary Flags

Use only during an approved smoke window:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## Stop Gates

Fail closed before smoke if any future hard gate fails, including missing env shape, token/env output, Authorization header output, raw transcript text, transcript delta output, shell environment dump, missing helper/policy fields, unexpected Gateway/listener/firewall state, or unclear rollback.

## Phase 2 Stop Result

```text
stop_gate=gateway_ssh_timeout
quote_safe_dry_run_env_check_result=not_run_due_hard_gate
hard_gate_result=NO_GO
smoke_count=0
gateway_request_sent=false
second_smoke_or_retry=false
```

## Validation

```text
focused_helper_adapter_bundle_temp_env_tests=45_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety Scans

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

## Protected Artifacts

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Next Step

Wait for coordinator review. Do not commit, push, open PR, run live preflight, or run smoke until directed.
