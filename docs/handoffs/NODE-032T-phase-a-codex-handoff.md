# NODE-032T Phase A Codex Handoff

## Scope

NODE-032T prepares a controlled Gateway smoke retry after NODE-032S confirmed Asterisk runtime dependency readiness in the selected project venv.

Phase A is read-only readiness and command planning only. No live smoke retry, helper copy/deploy, token handling, server temp env creation, dependency install, Gateway service action, reboot, firewall change, server env edit, business dialog enablement, Notion write, or Runtime/Evidence update occurred.

Future Phase B requires the exact approval phrase:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

## Context

NODE-032S merged via PR #21 / merge commit `6148901261f37c33617a558959cb125c091daf0d`.

NODE-032S confirmed the selected Asterisk runtime:

```text
target_python=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
imports_ok=true
dependency_install_occurred=false
gateway_smoke_retry=false
```

Prior retry readiness pieces:

```text
NODE-032L=safe temp-env guard
NODE-032N=complete helper bundle with ai_secretary.config
NODE-032P=runtime dependency preflight for httpx,fastapi,websockets
NODE-032S=selected Asterisk project venv readiness confirmed
```

## Local Repo Findings

Inspected:

```text
docs/nodes/NODE-032S-controlled-asterisk-runtime-dependency-install-readiness.md
docs/handoffs/NODE-032S-phase-a-codex-handoff.md
docs/handoffs/NODE-032S-phase-b-codex-handoff.md
scripts/gateway_smoke_temp_env_guard.py
scripts/asterisk_gateway_helper_bundle.py
scripts/asterisk_gateway_smoke_helper.py
```

Local guard/helper findings:

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

Phase B must use the selected runtime for helper-bundle validation and smoke helper execution:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

No real token values were embedded in docs, tests, handoffs, or source by this node.

## Asterisk Read-Only Gates

Host: `92.118.85.117`

Sanitized commands:

```text
ssh root@92.118.85.117 "<hostname/uptime/service/env-presence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/pip/package checks>"
ssh root@92.118.85.117 "<selected venv import/version checks>"
```

Findings:

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

## Gateway Read-Only Gates

Host: `45.61.48.199`

Sanitized command:

```text
ssh root@45.61.48.199 "<hostname/uptime/unit/service/user/env/listener/UFW masked checks>"
```

Findings:

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

## Phase B Command Plan

Approval gate:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Phase B must immediately re-confirm all hard gates before any state-changing command.

Hard gate re-check command shape:

```text
ssh root@92.118.85.117 "<hostname/uptime/service/env-presence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/pip/import/runtime-module checks>"
ssh root@45.61.48.199 "<gateway unit/service/user/env/listener/UFW masked checks>"
```

Selected Asterisk runtime command shape:

```text
ASTERISK_PY=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Helper bundle local create/validate shape:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
python scripts/asterisk_gateway_helper_bundle.py create --output <local_temp_bundle_dir>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_temp_bundle_dir>
```

Remote staged helper bundle validation shape:

```text
scp -r <local_temp_bundle_dir> root@92.118.85.117:<remote_temp_bundle_dir>
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>'
```

Runtime dependency preflight shape:

```text
<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>
```

Safe temp-env guard shape:

```text
<gateway token supplied through stdin only> | <selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

Gateway service readiness for smoke if still inactive:

```text
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service'
ssh root@45.61.48.199 '<listener/firewall/log-redaction checks>'
```

Smoke command shape:

```text
ssh root@92.118.85.117 '<load remote temp env without printing values; <selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --audio <operator-approved-safe-audio>'
```

Smoke must be exactly one Asterisk-side, non-business-dialog Gateway smoke if all gates pass.

Safe result fields to capture:

```text
gateway_reachable
gateway_auth_ok
openai_realtime_ok
gateway_http_status
chunks_sent
transcript_present
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Cleanup:

```text
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
rm -rf <remote_temp_bundle_dir> <remote_temp_audio_if_created>
rm -rf <local_temp_bundle_dir>
```

Gateway rollback/final state:

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

Phase B recommendation:

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

