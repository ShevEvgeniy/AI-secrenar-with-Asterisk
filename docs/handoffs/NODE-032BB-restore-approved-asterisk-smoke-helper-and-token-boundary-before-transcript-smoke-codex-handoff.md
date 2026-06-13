# NODE-032BB Codex Handoff

## Node

```text
NODE-032BB / restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

## Branch

```text
feat/node-032bb-restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

## Approval

The exact approval phrase was present:

```text
APPROVE NODE-032BB RESTORE SMOKE HELPER AND TOKEN BOUNDARY ONLY
```

## Outcome

NODE-032BB restored the two NODE-032BA blockers without running smoke.

```text
node_outcome=RESTORE_COMPLETE_NO_SMOKE
hard_gate_result=GO_FOR_FUTURE_APPROVAL_GATED_SMOKE
smoke_attempt_count=0
gateway_request=false
phase_b=false
gateway_service_started=false
```

## Pre-State

Asterisk:

```text
asterisk_ssh=ok
hostname=tula
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_process_running=true
ai_secretary_process_running=true
```

Gateway:

```text
gateway_ssh=ok
hostname=ai-secretary-gateway-node023
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listeners_443_8080_8081=ABSENT
gateway_runtime_process=ABSENT
```

## Helper Restore

The approved repo-supported helper bundle was created locally from tracked source, validated locally, and copied to the Asterisk project path. No smoke command was run.

```text
local_bundle_create=ok
local_bundle_validate=ok
runtime_modules_ok=true
secret_pattern_hits=[]
helper_present=true
helper_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/scripts/asterisk_gateway_smoke_helper.py
helper_owner=tulauser:tulauser
helper_mode=755
helper_executable=true
helper_source=repo_supported
helper_smoke_run=false
```

Supporting files restored from the validated bundle:

```text
scripts/gateway_smoke_temp_env_guard.py owner=tulauser:tulauser mode=755
src/ai_secretary/config/settings.py owner=tulauser:tulauser mode=644
src/ai_secretary/stt/gateway_adapter_smoke.py owner=tulauser:tulauser mode=644
src/ai_secretary/stt/realtime_gateway.py owner=tulauser:tulauser mode=644
src/ai_secretary/stt/realtime_measurement.py owner=tulauser:tulauser mode=644
```

## Credential Boundary Restore

The Gateway token was piped from the Gateway env file to the Asterisk guard stdin only. No token value, raw env file, Authorization header, or Bearer material was printed.

The first create attempt failed closed because the Gateway-side extraction command was misquoted and no token reached stdin:

```text
first_credential_create_attempt=failed_closed
first_credential_create_error=STT_GATEWAY_TOKEN missing
token_value_printed=false
raw_env_printed=false
```

The corrected guarded create succeeded:

```text
credential_boundary_present=true
credential_boundary_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.runtime/gateway-smoke.env
credential_boundary_owner=tulauser:tulauser
credential_boundary_mode=600
credential_boundary_size_bytes=263
token_present_masked=true
required_keys_present=true
credential_value_printed=false
raw_env_printed=false
business_dialog_transcript_enabled=false
transcript_text_logging_enabled=false
```

Asterisk safety checks after restore:

```text
service_OPENAI_API_KEY=ABSENT
process_OPENAI_API_KEY=ABSENT
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

Gateway masked env checks:

```text
gateway_env_path=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_metadata=root:gateway:640
OPENAI_API_KEY_PRESENT_MASKED=true
GATEWAY_TOKEN_PRESENT_MASKED=true
```

## Final State

```text
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listener_443=false
target_listener_8080=false
target_listener_8081=false
gateway_runtime_process=false
gateway_request=false
smoke_attempt_count=0
phase_b=false
```

The local temporary helper-bundle directory was removed after use.

## Local Validation

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
```

## Safety

```text
smoke=false
gateway_request=false
phase_b=false
real_customer_audio=false
audio_generated=false
audio_uploaded=false
token_values_printed=false
raw_env_printed=false
transcript_text_logged=false
transcript_delta_logged=false
business_dialog_config_mutation=false
docker_mutation=false
firewall_mutation=false
service_enable_disable_restart_reload=false
disk_image_touched=false
```

## Next Recommendation

```text
NODE-032BC / controlled-actual-speech-transcript-content-smoke-after-helper-and-token-boundary-restore
```

NODE-032BC should require fresh exact approval, immediate hard-gate re-check, and exactly one controlled non-business-dialog smoke if gates pass. NODE-032BB approval must not be reused for smoke.

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
