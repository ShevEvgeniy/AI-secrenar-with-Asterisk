# NODE-032T / controlled-gateway-smoke-retry-after-asterisk-runtime-readiness

## Purpose

Prepare a controlled Gateway smoke retry after NODE-032S confirmed Asterisk runtime dependency readiness in the selected project venv.

Phase A is read-only readiness and command planning only. It does not run live smoke retry.

Handoff archive:

```text
docs/handoffs/NODE-032T-phase-a-codex-handoff.md
```

## Approval Gate

Future Phase B requires the exact phrase:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Any other phrase is not approval.

## Context

NODE-032S merged via PR #21 / merge commit `6148901261f37c33617a558959cb125c091daf0d`.

NODE-032S confirmed:

```text
target_python=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
imports_ok=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
dependency_install_occurred=false
gateway_smoke_retry=false
```

Prior readiness fixes:

```text
NODE-032L=safe temp-env guard
NODE-032N=complete helper bundle with ai_secretary.config
NODE-032P=runtime dependency preflight for httpx,fastapi,websockets
NODE-032Q=system Python NO-GO, fixed by NODE-032S selected venv readiness
```

## Phase A Local Findings

Inspected:

```text
scripts/gateway_smoke_temp_env_guard.py
scripts/asterisk_gateway_helper_bundle.py
scripts/asterisk_gateway_smoke_helper.py
docs/nodes/NODE-032S-controlled-asterisk-runtime-dependency-install-readiness.md
docs/handoffs/NODE-032S-phase-a-codex-handoff.md
docs/handoffs/NODE-032S-phase-b-codex-handoff.md
```

Findings:

```text
safe_temp_env_guard=create_validate_cleanup
safe_temp_env_token_input=stdin_only
safe_temp_env_reports=masked_safe_json_only
safe_temp_env_rejects_newline_material=true
helper_bundle_manifest=present
helper_bundle_includes_temp_env_guard=true
helper_bundle_includes_ai_secretary_config=true
runtime_modules_required=httpx,fastapi,websockets
runtime_dependency_preflight=present
smoke_helper_refuses_asterisk_OPENAI_API_KEY=true
smoke_helper_requires_transcript_for_dialog_false=true
transcript_text_logging_disabled=true
```

Phase B must execute helper-bundle validation and smoke helper commands with:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

## Asterisk Phase A Read-Only Gates

Host: `92.118.85.117`

```text
ssh=reachable
hostname=tula
ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog=unchanged
selected_venv=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_venv_present=true
python_version=3.12.3
pip_version=26.1.1
imports_ok=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

No env values, token values, or transcript text were printed.

## Gateway Phase A Read-Only Gates

Host: `45.61.48.199`

```text
ssh=reachable
hostname=ai-secretary-gateway-node023
gateway_unit=present
gateway_unit_verify=OK
ai_secretary_gateway_service=inactive_disabled
gateway_user=present
gateway_group=present
gateway_env=present
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
gateway_workdir=/opt/ai-secretary-gateway present
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
```

No env values, token values, or transcript text were printed.

## Phase B Plan

Phase B may proceed only after the exact approval phrase and immediate hard-gate re-confirmation.

Approval:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Hard gate re-checks:

```text
ssh root@92.118.85.117 "<hostname/uptime/service/env-presence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/pip/import/runtime-module checks>"
ssh root@45.61.48.199 "<gateway unit/service/user/env/listener/UFW masked checks>"
```

Selected runtime:

```text
ASTERISK_PY=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Local helper bundle:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
python scripts/asterisk_gateway_helper_bundle.py create --output <local_temp_bundle_dir>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_temp_bundle_dir>
```

Remote helper bundle validation:

```text
scp -r <local_temp_bundle_dir> root@92.118.85.117:<remote_temp_bundle_dir>
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>'
```

Safe temp-env guard:

```text
<gateway token supplied through stdin only> | <selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

Gateway readiness if service remains inactive:

```text
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service'
ssh root@45.61.48.199 '<listener/firewall/log-redaction checks>'
```

Do not run `systemctl enable`.

Smoke:

```text
ssh root@92.118.85.117 '<load remote temp env without printing values; <selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --audio <operator-approved-safe-audio>'
```

Smoke boundary:

```text
smoke_count=1
origin=Asterisk
business_dialog_enablement=false
transcript_text_logging=false
token_output=false
```

Cleanup:

```text
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
rm -rf <remote_temp_bundle_dir> <remote_temp_audio_if_created>
rm -rf <local_temp_bundle_dir>
```

Gateway rollback / final state:

```text
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -ltn | grep -e :443 -e :8080 -e :8081 || true
ufw status verbose
```

Expected final target state:

```text
gateway_service=inactive
gateway_service_enabled=disabled
target_listeners_443_8080_8081=absent
firewall=unchanged
asterisk_OPENAI_API_KEY=ABSENT
business_dialog=unchanged
```

Explicit exclusions:

```text
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
port_443=false
port_8081=false
tls_proxy=false
firewall_broadening=false
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
- Selected project venv is missing or import checks fail.
- Runtime dependency preflight fails.
- Safe temp-env guard is unavailable or fails validation.
- Helper bundle preflight fails.
- Token would be printed by any command.
- Transcript text would be printed.
- Gateway env is missing or not `root:gateway 640`.
- Masked Gateway secret presence fails.
- Gateway service unit is missing or invalid.
- Unexpected listener exists on `443` or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Exact approval phrase is absent.

## Validation

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032T-phase-a-codex-handoff.md docs/nodes/NODE-032T-controlled-gateway-smoke-retry-after-asterisk-runtime-readiness.md docs/master
git status --short
```

Known full-suite environmental failures, if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

## Phase B Controlled Smoke Retry

Status: Phase B blocked after exactly one Asterisk-side smoke invocation; cleanup and rollback complete.

Approval phrase recorded:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Servers were stopped after Phase A and later made reachable again, so all Phase A live gates were stale. Phase B re-ran every Asterisk and Gateway hard gate before helper staging, token handling, temp env creation, service action, or smoke.

Handoff archive:

```text
docs/handoffs/NODE-032T-phase-b-codex-handoff.md
```

Hard gate reconfirmation:

```text
asterisk_hostname=tula
asterisk_ari_service=active_enabled
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_python=3.12.3
selected_runtime_pip=26.1.1
selected_runtime_imports=httpx:0.28.1,fastapi:0.136.1,websockets:16.0
gateway_hostname=ai-secretary-gateway-node023
gateway_unit_verify=OK
gateway_service_before=inactive_disabled
gateway_env_meta=root:gateway:640
gateway_secret_presence=masked_pass
target_listeners_443_8080_8081_before=absent
ufw_8080_allow=92.118.85.117 only
```

Helper bundle result:

```text
local_helper_bundle_create=ok
local_helper_bundle_validate=ok
remote_helper_bundle_staged=true
remote_helper_bundle_validate=ok
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

Safe temp-env guard result:

```text
token_source=Gateway env piped to guard stdin only
token_values_printed=false
temp_env_create=ok
temp_env_validate=ok
temp_env_mode=600
token_present_masked=true
temp_env_cleanup=ok
temp_env_absent_after_cleanup=true
```

Gateway service readiness:

```text
service_started_for_smoke=true
service_active_after_start=true
service_enabled_state=disabled
listener_8080_after_start=present
listener_443_after_start=absent
listener_8081_after_start=absent
ufw_8080_allow=92.118.85.117 only
log_secret_literal_checks=absent
log_transcript_text_literal=absent
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_change=false
```

Controlled smoke result:

```text
controlled_smoke_invocations=1
origin=Asterisk
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=400
error_type=gateway_audio_invalid
error_code=invalid_wav
blocker=synthetic_smoke_wav_sample_rate_16000_but_gateway_requires_24000_mono_16bit_pcm
openai_realtime_from_gateway=failed
chunks_sent=0
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
```

The Gateway request was reached and authenticated, but the Gateway rejected the generated smoke WAV before audio send because it was mono 16-bit PCM at 16000 Hz instead of the required 24000 Hz. No second smoke was attempted because NODE-032T allowed exactly one controlled smoke invocation.

Final rollback state:

```text
ai-secretary-gateway.service=inactive
ai-secretary-gateway.service_enabled=disabled
listener_443=absent
listener_8080=absent
listener_8081=absent
firewall=unchanged
ufw_8080_allow=92.118.85.117 only
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_helper_bundle_removed=true
temporary_env_removed=true
temporary_audio_removed=true
local_temp_bundle_removed=true
```

Blocked next step:

```text
phase_b_result=BLOCKED_AFTER_SINGLE_SMOKE
remaining_blocker=valid_24khz_mono_16bit_pcm_smoke_audio_needed
next_node=NODE-032U / controlled-gateway-smoke-retry-with-valid-24khz-audio
```

Phase B validation:

```text
focused_tests=31 passed
full_pytest=226 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_scan=no_real_secret_values_found; masked/status/placeholders only
```

Safety confirmations:

```text
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
token_values_printed=false
transcript_text_printed=false
port_443=false
port_8081=false
tls_proxy=false
firewall_broadening=false
server_env_edit=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation=false
```
