# NODE-032S Phase A Codex Handoff

This sanitized handoff archives the NODE-032S Phase A readiness and dependency-install planning pass.

NODE-032S prepares a controlled Asterisk runtime dependency install/readiness path after NODE-032Q and NODE-032R. Phase A is read-only readiness and planning only.

## Scope Guard

No dependency install, `pip install`, `apt install`, server package change, venv creation, server file write, helper copy/deploy, live retry, live smoke, Gateway service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, PR, or server state change occurred.

This handoff contains no real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

Pre-existing local untracked artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Context

NODE-032Q merged via PR #19 at:

```text
8c1848dd11c169ea3d004f16456343a3c593a853
```

NODE-032Q recorded a Phase A NO-GO because the Asterisk runtime used by the helper preflight lacked:

```text
httpx
fastapi
websockets
```

NODE-032R merged via PR #20 at:

```text
1d53d77e62c7414007411f8c71b08f1a6dd76eb3
```

NODE-032R selected a separate controlled Asterisk runtime dependency install/readiness node before any Gateway smoke retry. Smoke retry remains separate from dependency resolution.

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

Required runtime modules from `scripts/asterisk_gateway_helper_bundle.py`:

```text
httpx
fastapi
websockets
```

Repo dependency declaration:

```text
pyproject_declares_httpx=false
pyproject_declares_fastapi=false
pyproject_declares_websockets=false
```

Retry boundary:

```text
gateway_smoke_retry_in_NODE_032S=false
helper_deploy_for_smoke=false
token_handling=false
transcript_text_logging=false
```

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

No environment values were printed.

Python candidate findings:

```text
system_python3_path=/usr/bin/python3
system_python3_version=3.12.3
system_python3_pip=24.0
system_python3_site_packages=/usr/local/lib/python3.12/dist-packages
system_python3_httpx=missing
system_python3_fastapi=missing
system_python3_websockets=missing
```

Existing venv candidates:

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

Recommended Phase B target:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Reason:

- It is the existing deployed project venv under the current Asterisk project path.
- It already has `httpx`, `fastapi`, and `websockets`.
- It avoids mutating system Python.
- It may allow Phase B to be readiness verification only, with no package installation, if immediate re-checks still pass.

Conditional install policy:

```text
install_only_if_immediate_recheck_finds_missing_required_module=true
install_target=project_venv_only
system_python_install=false
apt_install=false
new_venv_creation=false
smoke_retry=false
```

## Phase B Plan Summary

Exact future approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

Immediate re-checks:

- Asterisk SSH reachable.
- Asterisk `ai-secretary-ari.service` active/enabled.
- Asterisk process/service/env-file `OPENAI_API_KEY_ABSENT`.
- Business dialog Gateway transcript flag not enabled.
- Gateway remains inactive/disabled with no target listeners and UFW source restriction unchanged.
- Project venv exists at `/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python`.
- Project venv imports `httpx`, `fastapi`, and `websockets`.

Pre-install/readiness snapshots:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -V
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -m pip --version
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -m pip show httpx fastapi websockets
import_status_for=httpx,fastapi,websockets
```

If all modules remain present:

```text
dependency_install=false
record_readiness=true
stop_without_smoke=true
```

If any required module is missing after approval and re-check:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -m pip install httpx fastapi websockets
```

Pinning policy:

- Prefer exact already-observed compatible versions if installation is needed:
  - `httpx==0.28.1`
  - `fastapi==0.136.1`
  - `websockets==16.0`
- If the live package index cannot provide those versions, stop as NO-GO rather than broadening install behavior.

Post-install/readiness verification:

- Import `httpx`, `fastapi`, `websockets`.
- Record versions.
- Re-confirm Asterisk `OPENAI_API_KEY_ABSENT`.
- Re-confirm business dialog Gateway transcript flag not enabled.
- Do not deploy helper bundle.
- Do not run smoke.

Rollback:

- If Phase B installs packages, uninstall only the newly installed packages from the project venv if rollback is required.
- Do not touch system Python.
- Do not touch unrelated venvs.
- Do not edit server env files.
- Do not change services, firewall, or Gateway state.

Explicit exclusions:

```text
gateway_smoke_retry=false
helper_deploy_for_smoke=false
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

Current Phase B recommendation:

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
- Target Python runtime is unclear or the project venv disappears.
- Required modules are missing and install would need system Python, apt, a new venv, or unrelated runtime mutation.
- Rollback path is unclear.
- Package source/index behavior is unclear.
- Any command would print secrets, env values, token values, or transcript text.
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
