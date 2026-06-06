# NODE-032W / controlled-gateway-transcript-presence-smoke

Status: Phase A readiness and command planning only.

Branch:

```text
feat/node-032w-controlled-gateway-transcript-presence-smoke
```

Handoff archive:

```text
docs/handoffs/NODE-032W-phase-a-codex-handoff.md
```

Phase B handoff archive:

```text
docs/handoffs/NODE-032W-phase-b-codex-handoff.md
```

## Goal

Prepare a controlled Gateway transcript-presence smoke after NODE-032U proved the Asterisk-origin Gateway transport/auth/OpenAI Realtime path with valid `24000 Hz mono 16-bit PCM` audio.

Phase A is read-only readiness, helper capability inspection, and command planning only. It does not run live smoke.

## Approval Gate

Future Phase B requires the exact phrase:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Any other phrase is not approval.

## Context

NODE-032U merged via PR #23:

```text
merge_commit=84421ce3295464315bd745ce000784e78274b194
```

NODE-032V merged via PR #24:

```text
merge_commit=11a141b161380ee4eda6585d8e0c9f94bd67fa47
```

NODE-032U is accepted as transport/auth/OpenAI Realtime proof only:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent=5
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

NODE-032W must not enable business-dialog transcript use, must not log transcript text, and must prove only transcript event/presence behavior if possible.

## Local Helper Findings

Inspected:

```text
docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md
docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md
scripts/asterisk_gateway_smoke_helper.py
scripts/asterisk_gateway_helper_bundle.py
scripts/gateway_smoke_temp_env_guard.py
tests/test_asterisk_gateway_smoke_helper.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/realtime_gateway.py
```

Safe helper capabilities:

```text
audio_create_supported=true
audio_create_command=python scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <path>
audio_validate_supported=true
audio_validate_command=python scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <path>
audio_exact_format_required=24000 Hz mono 16-bit PCM WAV
helper_bundle_create_validate_supported=true
runtime_dependency_preflight_supported=true
safe_temp_env_create_validate_cleanup_supported=true
selected_asterisk_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Transcript-presence capability:

```text
adapter_report_transcript_present=true
adapter_report_transcript_event_seen=true
adapter_report_transcript_bearing_event_seen=true
adapter_report_transcript_text_logged=true
adapter_report_transcript_used_for_dialog=true
adapter_report_business_dialog_unchanged=true
phase_b_can_prove_transcript_event_or_presence_with_existing_helper=true
future_local_implementation_node_required_before_phase_b=false
```

`gateway_adapter_smoke.build_report` maps redacted Gateway/adapter details into safe fields, including `transcript_present`, `transcript_event_seen`, and `transcript_bearing_event_seen`. `gateway_adapter._safe_gateway_payload` strips transcript text unless transcript logging is explicitly enabled. NODE-032W Phase B must keep `STT_GATEWAY_LOG_TRANSCRIPT=false` and `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.

## Phase A Read-Only Gates

### Asterisk

Commands were read-only and did not print env values.

```text
ssh_reachable=true
hostname=tula
uptime_observed=true
ai-secretary-ari.service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_env_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog_unchanged=true
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_present=true
selected_runtime_python=3.12.3
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

### Gateway

Commands were read-only and did not print env values.

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
unit_present=true
unit_verify=OK
ai-secretary-gateway.service=inactive_disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
opt_gateway_present=true
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
rollback_commands_available=true
```

## Phase B Plan

Phase B may proceed only after the exact approval phrase and immediate hard-gate re-confirmation.

Approval:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Hard gate re-checks:

```text
ssh root@92.118.85.117 "<hostname/uptime/ari-service/env-absence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/pip/import/runtime-module checks>"
ssh root@45.61.48.199 "<gateway unit/service/user/env/listener/UFW masked checks>"
```

Helper bundle:

```text
python scripts/asterisk_gateway_helper_bundle.py create --output <local_temp_bundle_dir>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_temp_bundle_dir>
scp -r <local_temp_bundle_dir> root@92.118.85.117:<remote_temp_bundle_dir>
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>'
```

Valid 24 kHz smoke audio:

```text
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <remote_temp_audio>'
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <remote_temp_audio>'
```

Safe temp env:

```text
<gateway token supplied through stdin only> | <selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

Gateway readiness only if needed:

```text
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service'
ssh root@45.61.48.199 '<listener/firewall/log-redaction checks>'
```

Do not run `systemctl enable`.

Smoke:

```text
ssh root@92.118.85.117 '<load remote temp env without printing values; <selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --audio <remote_temp_audio>'
```

Acceptance target:

```text
controlled_smoke_invocations=1
origin=Asterisk
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent>0
transcript_event_or_presence_confirmed=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Transcript-presence may be accepted through any safe redacted flag that confirms the event/presence boundary, such as:

```text
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_present=true
```

Transcript text must not be printed, logged, committed, or used for dialog.

Cleanup and final state:

```text
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
rm -rf <remote_temp_bundle_dir> <remote_temp_audio>
rm -rf <local_temp_bundle_dir>
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -ltn | grep -e :443 -e :8080 -e :8081 || true
ufw status verbose
```

Expected final state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
asterisk_OPENAI_API_KEY=ABSENT
business_dialog=unchanged
temporary_helper_env_audio_removed=true
```

## Exclusions

NODE-032W excludes:

```text
business_dialog_transcript_use=false
business_dialog_enablement=false
transcript_text_logging=false
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
token_output=false
port_443=false
port_8081=false
tls_proxy_changes=false
firewall_broadening=false
stereo_dual_channel_architecture=false
```

## GO / NO-GO

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=approval_phrase_absent
```

Hard NO-GO if:

- Asterisk contains `OPENAI_API_KEY`.
- Business dialog Gateway transcript use is enabled.
- Selected Asterisk project venv is missing or import checks fail.
- Helper bundle preflight fails.
- Runtime dependency preflight fails.
- Valid audio check is not exactly `24000 Hz mono 16-bit PCM`.
- Safe temp-env guard is unavailable or fails validation.
- Helper cannot report transcript event/presence safely without transcript text.
- Transcript text would be printed by any command.
- Token would be printed by any command.
- Gateway env is missing or not `root:gateway 640`.
- Masked Gateway secret presence fails.
- Gateway service unit is missing or invalid.
- Unexpected listener exists on `443` or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Exact approval phrase is absent.

## Phase A Validation

Result:

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_source_test_scan=no_real_secret_values_found; masked/status/placeholders/test-fixture hits only
final_status_expected_untracked=course_submission/,data/storage/,node014-server.tar
```

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032W-phase-a-codex-handoff.md docs/nodes/NODE-032W-controlled-gateway-transcript-presence-smoke.md docs/master scripts tests
git status --short
```

## Phase B Controlled Transcript-Presence Smoke

Phase B was approved with the exact phrase:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Hard gates were re-confirmed before helper staging, token handling, temp env creation, service action, or smoke.

### Gate Reconfirmation

```text
asterisk_hostname=tula
asterisk_ari_service=active_enabled
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_python=3.12.3
selected_runtime_imports=httpx:0.28.1,fastapi:0.136.1,websockets:16.0
gateway_hostname=ai-secretary-gateway-node023
gateway_unit_verify=OK
gateway_service_before=inactive_disabled
gateway_env_meta=root:gateway:640
gateway_secret_presence=masked_pass
target_listeners_443_8080_8081_before=absent
ufw_8080_allow=92.118.85.117 only
```

### Helper Bundle

```text
local_bundle_create=ok
local_bundle_validate=ok
remote_validate_first_attempt=failed_closed_missing_validator_script
remote_validate_fix=staged_validator_script_into_temp_bundle
remote_bundle_validate=ok
remote_runtime_modules_ok=true
missing_runtime_modules=[]
secret_values_printed=false
transcript_text_logged=false
```

The first remote preflight failed closed before token handling, service action, smoke, or Gateway request because the temporary bundle did not include `scripts/asterisk_gateway_helper_bundle.py`. The validator script was staged into the temporary bundle and remote preflight then passed.

### Valid Audio

```text
audio_create=ok
audio_validate=ok
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
frame_count=24000
audio_format_errors=[]
```

### Safe Temp Env

```text
first_create_attempt=failed_closed_missing_token_due_command_quoting
retry_create=ok
token_source=Gateway env piped to guard stdin only
token_values_printed=false
validate=ok
required_keys_present=true
token_present_masked=true
temp_env_mode=600
cleanup=ok
```

No token value was printed, committed, logged, or recorded.

### Gateway Service Readiness

```text
service_started_for_smoke=true
service_active=true
service_enabled_state=disabled
listener_8080=present
listener_443=absent
listener_8081=absent
ufw_8080_allow=92.118.85.117 only
log_secret_or_transcript_pattern=absent
systemctl_enable=false
reboot=false
provider_power_cycle=false
```

### Smoke Result

Exactly one controlled Asterisk-side non-business-dialog smoke ran.

```text
controlled_smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

Result classification:

```text
node032w_transcript_presence_success=false
node032w_transport_auth_openai_realtime_success=true
blocker=transcript_event_or_presence_not_confirmed
retry_within_node=false
```

Transport/auth/OpenAI Realtime succeeded again, but transcript-presence evidence was not confirmed. NODE-032W therefore closes as a safe blocker, not a transcript-presence success.

### Final State

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_asterisk_helper_env_audio_removed=true
local_temp_bundle_removed=true
log_secret_or_transcript_pattern=absent
dependency_install=false
systemctl_enable=false
reboot_or_power_cycle=false
business_dialog_enablement=false
business_dialog_transcript_use=false
transcript_text_printed=false
token_values_printed=false
```

Next recommendation:

```text
NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```
