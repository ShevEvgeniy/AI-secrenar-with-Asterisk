# NODE-032BH / controlled-asterisk-helper-runtime-refresh-for-business-transcript-policy-fields

## Summary

NODE-032BH refreshed the deployed Asterisk-side helper/runtime reporting files so NODE-032BF business-dialog transcript policy fields appear in safe diagnostics.

Result:

```text
approval_phrase=APPROVE NODE-032BH CONTROLLED ASTERISK HELPER RUNTIME REFRESH
node_outcome=SUCCESSFUL_HELPER_RUNTIME_POLICY_FIELD_REFRESH
gateway_start=false
gateway_smoke=false
gateway_request=false
call_run=false
openai_request=false
service_action=false
```

NODE-032BH did not start Gateway, run a smoke, send a Gateway request, run a call, or enable business-dialog transcript use.

## Branch

```text
feat/node-032bh-controlled-asterisk-helper-runtime-refresh-for-business-transcript-policy-fields
```

## Context

NODE-032BG proved the live path stayed disabled and safe but did not expose the NODE-032BF `business_dialog_transcript_*` reporting fields in the deployed Asterisk helper/runtime report.

NODE-032BH checked and refreshed only the Asterisk helper/runtime reporting path.

## Local Preflight

```text
starting_master_head=e7e8b758771f757440483403adde7336a4cd3c3a
focused_pytest_before_refresh=65_passed
helper_bundle_manifest_ok=true
helper_bundle_includes_policy_module=true
helper_bundle_runtime_modules_ok=true
local_secret_values_printed=false
local_transcript_text_logged=false
```

The local bundle manifest included:

```text
src/ai_secretary/telephony/__init__.py
src/ai_secretary/telephony/transcript_policy.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
scripts/asterisk_gateway_smoke_helper.py
scripts/gateway_smoke_temp_env_guard.py
```

## Asterisk Preflight

Before refresh, Asterisk was reachable and safe:

```text
asterisk_reachable=true
project_root=/home/tulauser/AI-secrenar-with-Asterisk-node014
ai_secretary_process_running=true
helper_present=true
helper_executable=true
helper_mode=755
adapter_file_present=true
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_enabled_env=false
raw_transcript_logging_env=false
secret_values_printed=false
transcript_text_printed=false
```

The pre-refresh no-network diagnostic showed the refresh was required:

```text
policy_module_present=false
business_dialog_transcript_policy_enabled=FIELD_MISSING
business_dialog_transcript_allowed=FIELD_MISSING
business_dialog_transcript_reason=FIELD_MISSING
business_dialog_transcript_used_for_dialog=FIELD_MISSING
safe_diagnostic_ok=false
```

The diagnostic used a local stubbed adapter call only. It did not reach Gateway or OpenAI and did not print transcript text.

## Refresh Action

Refresh was required and performed.

Local bundle:

```text
bundle_create_ok=true
bundle_validate_ok=true
runtime_modules_required=httpx,fastapi,websockets
runtime_modules_ok=true
archive_size_bytes=47608
```

Remote controlled refresh:

```text
refresh_performed=true
target=/home/tulauser/AI-secrenar-with-Asterisk-node014
backup_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.runtime/node032bh-backup-20260615091729
files_backed_up_count=11
files_copied_count=12
missing_staging_files_count=0
policy_module_deployed=true
helper_executable=true
service_action_used=false
gateway_action_used=false
```

Files copied from the validated helper bundle:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/__init__.py
src/ai_secretary/config/__init__.py
src/ai_secretary/config/settings.py
src/ai_secretary/stt/__init__.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
src/ai_secretary/telephony/__init__.py
src/ai_secretary/telephony/transcript_policy.py
```

Notes:

```text
scp_attempt_failed_to_create_remote_archive=true
first_base64_upload_attempt_created_zero_byte_archive=true
successful_ascii_base64_upload=true
secret_values_printed=false
token_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
```

The failed upload attempts did not print token/env/transcript values. They did not create committed artifacts.

## Required Proof

After refresh, the no-network safe diagnostic exposed the required fields:

```text
policy_module_present=true
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=false
business_dialog_transcript_used_for_dialog=false
business_dialog_transcript_reason=business_dialog_transcript_disabled
transcript_text_logged=false
dialog_transcript_used=false
safe_diagnostic_ok=true
```

Runtime safety after refresh:

```text
ai_secretary_process_running=true
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_enabled_env=false
raw_transcript_logging_env=false
helper_executable=true
```

## Cleanup

Temporary bundle/upload artifacts were removed:

```text
remote_temp_bundle_removed=true
remote_temp_archive_removed=true
local_temp_bundle_removed=true
local_temp_archive_removed=true
audio_artifact_created=false
temp_env_created=false
server_dump_created=false
log_artifact_created=false
```

Rollback backup remains on Asterisk:

```text
backup_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.runtime/node032bh-backup-20260615091729
```

## Validation

```text
focused_pytest=65_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
gateway_start=false
gateway_smoke=false
gateway_request=false
call_run=false
phase_b=false
openai_request=false
service_action=false
docker_mutation=false
firewall_or_env_mutation=false
server_or_app_config_mutation=false
business_dialog_transcript_enablement=false
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
audio_committed=false
server_dump_or_log_artifact_added=false
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
NODE-032BI / controlled-disabled-business-dialog-policy-field-live-smoke-after-helper-refresh
```

The next node should be separate and approval-gated. It should run one controlled live smoke to prove the refreshed Asterisk helper/runtime now reports the NODE-032BF `business_dialog_transcript_*` fields during the disabled-by-default live path.

