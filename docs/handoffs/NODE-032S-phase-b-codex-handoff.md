# NODE-032S Phase B Codex Handoff

## Scope

NODE-032S Phase B was approved with the exact phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

This phase was dependency readiness only. It did not run Gateway smoke, did not deploy a helper bundle, did not change Gateway service state, did not reboot, did not change firewall, and did not edit server env files.

## Sanitized Commands

Local setup and validation:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032S-phase-b-codex-handoff.md docs/handoffs/NODE-032S-phase-a-codex-handoff.md docs/nodes/NODE-032S-controlled-asterisk-runtime-dependency-install-readiness.md docs/master
git status --short
```

Read-only Asterisk checks:

```text
ssh root@92.118.85.117 "<sanitized hostname/uptime/service/env-presence/business-dialog checks>"
ssh root@92.118.85.117 "<selected project venv Python/pip/package/version checks>"
```

Read-only Gateway checks:

```text
ssh root@45.61.48.199 "<sanitized hostname/uptime/unit/service/env-metadata/masked-secret/listener/UFW checks>"
```

No env values, token values, or transcript text were printed.

## Hard Gate Reconfirmation

Asterisk:

```text
ssh=reachable
hostname=tula
ai_secretary_ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog=unchanged
```

Gateway:

```text
ssh=reachable
hostname=ai-secretary-gateway-node023
gateway_unit=present
gateway_unit_verify=OK
ai_secretary_gateway_service=inactive_disabled
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
```

## Selected Target Runtime

```text
target_python=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
site_packages=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/lib/python3.12/site-packages
```

## Import / Version Readiness

The selected project venv imported all required runtime modules successfully:

```text
imports_ok=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

Phase B expected install need was `false`, and immediate re-check confirmed that no dependency installation was required.

## Install Result

```text
dependency_install_occurred=false
pip_install_occurred=false
apt_install_occurred=false
system_python_mutated=false
project_venv_mutated=false
```

No packages were installed, removed, upgraded, or downgraded.

## Final Safety State

```text
gateway_smoke_retry=false
helper_copy_deploy=false
gateway_service_action=false
systemctl_state_change=false
reboot_or_power_cycle=false
provider_power_cycle=false
firewall_change=false
server_env_edit=false
business_dialog_enablement=false
token_values_printed=false
transcript_text_logged=false
notion_write=false
runtime_evidence_update=false
github_push_or_pr=false
scheduler_webhook_automation=false
```

## Next Recommendation

```text
NODE-032T / controlled-gateway-smoke-retry-after-asterisk-runtime-readiness
```

NODE-032T should remain separate from NODE-032S and should require its own exact approval phrase, immediate hard-gate re-confirmation, safe temp-env handling, complete helper-bundle validation, runtime dependency preflight, and exactly one controlled Asterisk-side non-business-dialog Gateway smoke.

