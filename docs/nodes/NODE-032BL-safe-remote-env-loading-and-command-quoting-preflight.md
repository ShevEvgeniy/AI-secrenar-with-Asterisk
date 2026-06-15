# NODE-032BL / safe-remote-env-loading-and-command-quoting-preflight

## Summary

NODE-032BL hardens the future Asterisk-side smoke helper path so enabled business-dialog transcript-use retry work can avoid fragile nested shell quoting.

Result:

```text
node_outcome=QUOTE_SAFE_ENV_LOADING_PREFLIGHT_READY
quote_safe_env_loading_preflight_ready=true
enabled_live_dialog_use_proven=false
live_smoke_run=false
gateway_request_sent=false
ssh_used=false
server_access=false
token_handling=false
real_env_value_handling=false
```

NODE-032BL is repo-first only. It did not access Asterisk or Gateway and did not run a live smoke.

## Branch

```text
feat/node-032bl-safe-remote-env-loading-and-command-quoting-preflight
```

## Base

```text
starting_master_head=e07c9d44744438493469aabe49658dacd0c78522
```

## Inherited Blocker

NODE-032BK passed live preflight and hard gates, then attempted exactly one smoke command. The command failed closed before Gateway request:

```text
NODE_032BK_status=Done_with_blocked_result
enabled_live_dialog_use_proven=false
partial_proof=false
blocked=true
classification=blocked_command_quoting_env_dump_missing_gateway_flags
gateway_request_sent=false
second_smoke_or_retry=false
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
shell_environment_dump_printed=true
```

Root cause recorded for NODE-032BL:

```text
remote_command_quoting_prevented_gateway_smoke_env_load=true
ad_hoc_inline_shell_source_path_risky=true
no_second_smoke_without_new_approval=true
```

## Implementation

NODE-032BL hardens:

```text
scripts/asterisk_gateway_smoke_helper.py
tests/test_asterisk_gateway_smoke_helper.py
```

The helper now supports:

```text
--env-file <path>
--dialog-transcript-use disabled
--dialog-transcript-use enabled
--dry-run-env-check
```

The env-file path uses a small Python allowlist parser rather than shell `source`, `set -a`, nested `bash -lc`, or inline env dumps.

Allowed smoke env keys:

```text
STT_GATEWAY_STT_ENABLED
STT_GATEWAY_ADAPTER_ENABLED
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG
STT_GATEWAY_LOG_TRANSCRIPT
STT_GATEWAY_URL
STT_GATEWAY_TOKEN
REALTIME_GATEWAY_URL
REALTIME_GATEWAY_TOKEN
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS
BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE
```

## Safer Command Strategy

Future live retry should use one helper entrypoint instead of shell-sourced inline module calls:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --audio <approved_audio_path>
```

Before any future smoke, a dry-run check can prove env shape without reading audio or sending a Gateway request:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --dry-run-env-check
```

This command shape avoids:

```text
set -a
remote_shell_source_side_effects
inline_python_shell_quote_fragility
shell_environment_dump_on_failure
raw_env_value_output
```

## Missing-Flag Behavior

Required behavior is now covered locally:

```text
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
token_values_printed=false
raw_env_values_printed=false
shell_environment_dump_printed=false
gateway_request_sent=false
```

The helper reports missing fields by key name only. It does not print token values, raw env values, Authorization headers, raw transcript text, or transcript deltas.

## Enabled Mode Guardrails

When `--dialog-transcript-use enabled` is selected, validation requires:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
STT_GATEWAY_LOG_TRANSCRIPT=false
```

When `--dialog-transcript-use disabled` is selected, validation requires:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

The helper still fails closed if `OPENAI_API_KEY` is present on Asterisk.

## Tests

Added/updated local tests prove:

```text
dry_run_env_file_missing_url_and_token_fails_closed=true
missing_flags_reported_by_name_only=true
enabled_env_file_allowlist_accepts_shape_without_printing_values=true
unapproved_env_keys_rejected_without_values=true
enabled_mode_delegates_to_existing_smoke_module_without_shell_source=true
temporary_os_environ_overlay_restored_after_delegation=true
shell_environment_dump_printed=false
gateway_request_sent=false
```

No tests use real tokens or real env values.

## Validation

```text
focused_helper_tests=13_passed
focused_helper_adapter_bundle_temp_env_tests=45_passed
git_diff_check=passed
source_runtime_diff=scripts/asterisk_gateway_smoke_helper.py,tests/test_asterisk_gateway_smoke_helper.py
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
transcript_enablement=false
token_handling=false
real_env_value_handling=false
service_action=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
audio_generated_or_uploaded_for_live_use=false
disk_image_touched=false
notion_write=false
runtime_evidence_write=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Non-Proofs

NODE-032BL does not prove:

```text
enabled_live_dialog_use_proven=false
future_live_retry_success=false
gateway_request_sent=false
business_dialog_transcript_used_for_dialog=false
production_call_path=false
real_caller_or_customer_audio=false
```

Future live retry still requires a separate node and exact approval.

## Next Recommendation

```text
NODE-032BM / controlled-enabled-live-smoke-retry-with-safe-env-loader
```
