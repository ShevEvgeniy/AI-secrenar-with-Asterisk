# NODE-032BB / restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke

## Summary

NODE-032BB restored the approved Asterisk-side smoke helper and the safe Gateway credential boundary that blocked NODE-032BA.

This node did not run transcript smoke, did not start Gateway for smoke, and did not send a Gateway request.

Result:

```text
approval_phrase=APPROVE NODE-032BB RESTORE SMOKE HELPER AND TOKEN BOUNDARY ONLY
node_outcome=RESTORE_COMPLETE_NO_SMOKE
hard_gate_result=GO_FOR_FUTURE_APPROVAL_GATED_SMOKE
smoke_attempt_count=0
gateway_request=false
phase_b=false
gateway_service_started=false
```

## Branch

```text
feat/node-032bb-restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

## Context

NODE-032BA stopped before Gateway service start and before smoke because:

```text
blocker_1=asterisk_smoke_helper_absent
blocker_2=asterisk_gateway_token_runtime_env_absent
```

NODE-032BB approval allowed restoring those prerequisites only. It did not authorize smoke, Gateway requests, calls, service enablement, Docker mutation, firewall mutation, business-dialog config changes, raw token output, transcript text logging, or transcript delta logging.

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

## Helper Restore Result

A local helper bundle was built from tracked repo-supported source and validated before copy:

```text
local_bundle_create=ok
local_bundle_validate=ok
runtime_modules_required=httpx,fastapi,websockets
runtime_modules_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The validated bundle was copied to the Asterisk project path:

```text
helper_present=true
helper_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/scripts/asterisk_gateway_smoke_helper.py
helper_owner=tulauser:tulauser
helper_mode=755
helper_executable=true
helper_source=repo_supported
helper_smoke_run=false
```

Supporting tracked bundle files restored:

```text
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/__init__.py
src/ai_secretary/config/__init__.py
src/ai_secretary/config/settings.py
src/ai_secretary/stt/__init__.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
```

No ad-hoc server helper was written.

## Credential Boundary Result

The Gateway token was supplied from the Gateway env to the Asterisk guard through stdin only. No token value, raw env file, Authorization header, or Bearer material was printed.

One initial create attempt failed closed due local quoting and supplied no token:

```text
first_create_attempt=failed_closed
error=STT_GATEWAY_TOKEN missing
token_value_printed=false
raw_env_printed=false
```

The corrected guarded create succeeded:

```text
credential_boundary_present=true
credential_boundary_path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.runtime/gateway-smoke.env
credential_boundary_owner=tulauser:tulauser
credential_boundary_mode=600
token_present_masked=true
required_keys_present=true
credential_value_printed=false
raw_env_printed=false
```

Boundary safety values verified by masked/boolean checks:

```text
business_dialog_transcript_enabled=false
transcript_text_logging_enabled=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
service_OPENAI_API_KEY=ABSENT
process_OPENAI_API_KEY=ABSENT
```

Gateway env metadata and masked presence:

```text
gateway_env_path=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_metadata=root:gateway:640
OPENAI_API_KEY_PRESENT_MASKED=true
GATEWAY_TOKEN_PRESENT_MASKED=true
```

## Final Gateway Baseline

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

## Local Validation

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
smoke=false
gateway_request=false
phase_b=false
calls=false
real_customer_audio=false
audio_generated=false
audio_uploaded=false
token_values_printed=false
raw_env_values_printed=false
transcript_text_logged=false
transcript_delta_logged=false
business_dialog_config_mutation=false
docker_mutation=false
firewall_mutation=false
service_enable_disable_restart_reload=false
apt_update_or_upgrade=false
disk_image_touched=false
local_temp_helper_bundle_removed=true
```

## Next Recommendation

```text
NODE-032BC / controlled-actual-speech-transcript-content-smoke-after-helper-and-token-boundary-restore
```

NODE-032BC should be a separate smoke node with fresh exact approval and immediate hard-gate re-check. NODE-032BB approval only covered helper and credential-boundary restore.

## Handoff

```text
docs/handoffs/NODE-032BB-restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
