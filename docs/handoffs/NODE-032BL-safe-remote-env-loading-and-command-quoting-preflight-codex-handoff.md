# Codex Handoff - NODE-032BL / safe-remote-env-loading-and-command-quoting-preflight

## Result

NODE-032BL prepared a repo-local quote-safe env-loading and command invocation path for a future enabled business-dialog transcript-use smoke retry.

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

## Inherited Blocker

```text
NODE_032BK_status=Done_with_blocked_result
classification=blocked_command_quoting_env_dump_missing_gateway_flags
gateway_request_sent=false
second_smoke_or_retry=false
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
shell_environment_dump_printed=true
```

## Implementation

Changed:

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

## Safe Env Loading

The helper parses KEY=VALUE env files directly through an allowlist. It does not require shell `source`, `set -a`, nested `bash -lc`, or inline Python module calls.

Required missing-flag behavior:

```text
missing_required_flags=STT_GATEWAY_URL,STT_GATEWAY_TOKEN
token_values_printed=false
raw_env_values_printed=false
shell_environment_dump_printed=false
gateway_request_sent=false
```

## Future Enabled Smoke Command Shape

Future retry should use:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --audio <approved_audio_path>
```

Future dry-run should use:

```text
python scripts/asterisk_gateway_smoke_helper.py \
  --env-file <approved_remote_env_path> \
  --dialog-transcript-use enabled \
  --dry-run-env-check
```

## Tests

Local tests cover:

```text
missing_url_and_token_fail_closed=true
missing_flags_by_name_only=true
enabled_env_file_allowlist_accepts_shape_without_printing_values=true
unapproved_env_keys_rejected_without_values=true
enabled_mode_delegates_to_smoke_module_without_shell_source=true
temporary_environ_restored_after_delegation=true
```

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

## Next Recommendation

```text
NODE-032BM / controlled-enabled-live-smoke-retry-with-safe-env-loader
```

Future live retry still requires a separate node and exact approval.
