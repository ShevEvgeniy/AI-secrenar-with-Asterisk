# NODE-032S / controlled-asterisk-runtime-dependency-install-readiness

Status: Phase A readiness and dependency-install planning complete

NODE-032S prepares a controlled Asterisk runtime dependency install/readiness path. Phase A is read-only readiness and command planning only. It does not install dependencies or run Gateway smoke.

## Scope Guard

No dependency install, `pip install`, `apt install`, server package change, venv creation, server file write, helper copy/deploy, live retry, live smoke, Gateway service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, PR, or server state change occurred.

Pre-existing local untracked artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Handoff Archive

```text
docs/handoffs/NODE-032S-phase-a-codex-handoff.md
```

The handoff contains no real secrets, token values, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Context

NODE-032Q merged via PR #19:

```text
8c1848dd11c169ea3d004f16456343a3c593a853
```

NODE-032Q found the Asterisk helper runtime missing:

```text
httpx
fastapi
websockets
```

NODE-032R merged via PR #20:

```text
1d53d77e62c7414007411f8c71b08f1a6dd76eb3
```

NODE-032R selected a separate controlled Asterisk runtime dependency install/readiness node before any Gateway smoke retry. Gateway smoke retry remains separate from dependency resolution.

## Local Findings

Inspected:

```text
docs/nodes/NODE-032Q-controlled-gateway-smoke-retry-with-runtime-dependency-preflight.md
docs/nodes/NODE-032R-controlled-asterisk-runtime-dependency-resolution-or-alternate-helper-strategy.md
docs/handoffs/NODE-032R-codex-handoff.md
scripts/asterisk_gateway_helper_bundle.py
tests/test_asterisk_gateway_helper_bundle.py
pyproject.toml
```

Required runtime modules:

```text
httpx
fastapi
websockets
```

Local repo dependency declaration:

```text
pyproject_declares_httpx=false
pyproject_declares_fastapi=false
pyproject_declares_websockets=false
```

NODE-032S does not include a Gateway smoke retry.

## Asterisk Read-Only Findings

Server:

```text
92.118.85.117
```

Read-only gates:

```text
ssh_reachable=true
hostname=tula
uptime_observed=true
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog=UNCHANGED_BY_READONLY_GATE
```

No env values were printed.

Python runtime candidates:

```text
system_python3=/usr/bin/python3
system_python3_version=3.12.3
system_python3_pip=24.0
system_python3_httpx=missing
system_python3_fastapi=missing
system_python3_websockets=missing
```

Existing venvs:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
/home/tulauser/tone_gpu_env/bin/python
/home/tulauser/venv/bin/python
```

Project venv:

```text
path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
site_packages=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/lib/python3.12/site-packages
httpx=present version 0.28.1
fastapi=present version 0.136.1
websockets=present version 16.0
```

Other venvs:

```text
/home/tulauser/tone_gpu_env/bin/python: httpx=missing,fastapi=missing,websockets=missing
/home/tulauser/venv/bin/python: httpx=present,fastapi=missing,websockets=missing
```

## Gateway Read-Only Findings

Server:

```text
45.61.48.199
```

Read-only gates:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
unit_file_present=true
unit_verify=OK
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
target_listeners_443_8080_8081=NONE
ufw_status=active
ufw_default_incoming=deny
ufw_8080_source=92.118.85.117 only
ufw_8080_broad=ABSENT
```

No env values were printed.

## Target Runtime Recommendation

Selected Phase B target:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Reason:

- It is the existing deployed project venv under the Asterisk project path.
- It already imports `httpx`, `fastapi`, and `websockets`.
- It avoids modifying system Python.
- It keeps dependency readiness separate from Gateway smoke retry.

Expected Phase B result if re-checks remain true:

```text
dependency_install_needed=false
readiness_verification_only=true
gateway_smoke_retry=false
```

## Phase B Approval Phrase

Exact future approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

Any other phrase is not approval.

## Phase B Command Set Summary

Phase B must begin with immediate hard-gate re-confirmation.

Gate re-checks:

- Asterisk SSH reachable.
- `ai-secretary-ari.service` active/enabled.
- Asterisk process/service/env-file `OPENAI_API_KEY_ABSENT`.
- Business dialog Gateway transcript flag not enabled.
- Gateway unit present/verified, service inactive/disabled, no target listeners, UFW unchanged.

Target runtime:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Pre-install/readiness snapshot:

```text
<target_python> -V
<target_python> -m pip --version
<target_python> -m pip show httpx fastapi websockets
<target_python> -c "<safe import status for httpx, fastapi, websockets>"
```

If imports pass:

```text
dependency_install=false
record_readiness=true
stop_without_smoke=true
```

If a required module is missing after exact approval and hard-gate re-check:

```text
<target_python> -m pip install httpx==0.28.1 fastapi==0.136.1 websockets==16.0
```

If pinned versions are unavailable or install behavior would broaden beyond the project venv:

```text
stop_as_NO_GO=true
```

Post-readiness verification:

- Import `httpx`, `fastapi`, `websockets`.
- Record versions.
- Re-confirm Asterisk `OPENAI_API_KEY_ABSENT`.
- Re-confirm business dialog Gateway transcript flag not enabled.
- Stop without Gateway smoke.

Rollback if packages are installed:

```text
<target_python> -m pip uninstall -y httpx fastapi websockets
```

Rollback must only remove packages newly installed by Phase B. If the packages were already present at pre-snapshot, do not uninstall them.

Explicit exclusions:

```text
gateway_smoke_retry=false
helper_copy_deploy=false
gateway_service_action=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_change=false
server_env_edit=false
token_output=false
transcript_text_logging=false
```

## GO / NO-GO

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
expected_dependency_install_needed=false
recommended_action=verify_project_venv_readiness_and_stop
```

Hard NO-GO if:

- Exact approval phrase is absent.
- Asterisk contains `OPENAI_API_KEY`.
- Business dialog Gateway transcript use is enabled.
- Target project venv is missing or unclear.
- Required modules are missing and install would require system Python, apt, unrelated venv mutation, or new venv creation.
- Rollback path is unclear.
- Package source/index behavior is unclear.
- Any command would print secrets, token values, env values, or transcript text.
- Dependency readiness would require Gateway smoke in the same node.

## Validation

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032S-phase-a-codex-handoff.md docs/nodes/NODE-032S-controlled-asterisk-runtime-dependency-install-readiness.md docs/master
git status --short
```

Known full-suite environmental failures, if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

## Phase B Result

Phase B was approved with the exact phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

This phase remained dependency readiness only. It did not include Gateway smoke retry, helper copy/deploy, Gateway service action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, token output, or transcript text logging.

Phase B handoff archive:

```text
docs/handoffs/NODE-032S-phase-b-codex-handoff.md
```

Hard gates were re-confirmed:

```text
asterisk_ssh=reachable
asterisk_hostname=tula
asterisk_ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
gateway_ssh=reachable
gateway_hostname=ai-secretary-gateway-node023
gateway_unit=present
gateway_unit_verify=OK
gateway_service=inactive_disabled
gateway_env_meta=root:gateway:640
gateway_secret_presence=masked_pass
target_listeners_443_8080_8081=absent
ufw_8080_allow=92.118.85.117 only
```

Selected target runtime readiness:

```text
target_python=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
imports_ok=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

Install result:

```text
expected_dependency_install_needed=false
dependency_install_occurred=false
pip_install_occurred=false
apt_install_occurred=false
system_python_mutated=false
project_venv_mutated=false
```

No packages were installed, removed, upgraded, or downgraded because the selected project venv already satisfied the runtime dependency readiness gate.

Final safety state:

```text
gateway_smoke_retry=false
helper_copy_deploy=false
gateway_service_action=false
systemctl_state_change=false
reboot_or_power_cycle=false
firewall_or_env_changed=false
server_state_changed=false
token_values_printed=false
transcript_text_logged=false
```

Next recommendation:

```text
NODE-032T / controlled-gateway-smoke-retry-after-asterisk-runtime-readiness
```
