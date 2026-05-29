# NODE-032K Phase A Codex Handoff

Status: Phase A readiness and command planning complete

## Scope

NODE-032K prepares controlled Gateway service enablement and reboot smoke after NODE-032J.

Phase A was read-only readiness plus command planning only. No live enablement, `systemctl enable`, reboot, provider power-cycle, service start/stop/restart/reload, firewall change, env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation loop, or server state change occurred.

Phase B remains blocked until the exact phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

No other phrase is approval.

## Starting Point

```text
start_branch=master
start_commit=8662f3f
feature_branch=feat/node-032k-controlled-gateway-service-enable-and-reboot-smoke
node=NODE-032K / controlled-gateway-service-enable-and-reboot-smoke
```

NODE-032I staged service state:

```text
gateway_user_group=gateway:gateway
env_owner_mode=root:gateway 640
unit=/etc/systemd/system/ai-secretary-gateway.service
env_file=/etc/ai-secretary/openai-realtime-gateway.env
working_directory=/opt/ai-secretary-gateway
listen=0.0.0.0:8080
restart=on-failure
pythonpath=/opt/ai-secretary-gateway/src
service_started_and_smoked=true
service_stopped_after_smoke=true
service_enabled=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
```

NODE-032J decision:

```text
keep_staged_service_installed=true
keep_service_disabled_until_next_exact_approval=true
next_node=NODE-032K
approval_phrase=APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

## Commands Run

Local setup and inspection:

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032k-controlled-gateway-service-enable-and-reboot-smoke
Get-Content docs\nodes\NODE-032J-gateway-service-enable-policy-and-autostart-decision.md
Get-Content docs\nodes\NODE-032I-controlled-persistent-gateway-service-install-start-smoke.md
Get-Content deploy\templates\gateway-systemd.service.example
Test-Path docs\handoffs\README.md
Get-Content docs\master\MASTER_STATUS.md -Tail 160
Get-Content docs\master\MASTER_PLAN.md -Tail 90
Get-Content docs\master\DECISIONS.md -Tail 120
Get-Content docs\master\RUNTIME_NOTES.md -Tail 120
Get-Content docs\master\NODE_REGISTRY.md -Tail 20
```

Asterisk read-only checks:

```text
ssh -o ConnectTimeout=20 root@92.118.85.117 '<hostname, uptime, ai-secretary-ari.service active/enabled, masked OPENAI_API_KEY process check, systemd Environment check>'
ssh -o ConnectTimeout=20 root@92.118.85.117 '<service env OPENAI_API_KEY masked absence and business dialog gateway transcript flag check>'
```

Gateway read-only checks:

```text
ssh -o ConnectTimeout=20 root@45.61.48.199 '<hostname, uptime, unit present, service active/enabled state, gateway user/group, env stat, masked secret presence, deploy path stat>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<systemd-analyze verify, unit shape, listener check, UFW status, rollback tool availability>'
```

One Asterisk unit-inspection command had a quoting issue and timed out before producing useful output. A later simpler read-only command produced the required sanitized checks. One later `sed` expression printed an error after the needed sanitized Asterisk env results. No state-changing command was run.

## Asterisk Read-Only Findings

```text
target=92.118.85.117
ssh_reachable=true
hostname=tula
uptime=up_1h33m_at_check
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_env_openai_api_key=OPENAI_API_KEY_ABSENT
systemd_environment=PYTHONUNBUFFERED_only
service_env_file=/etc/ai-secretary/ari-app.env
service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=BUSINESS_DIALOG_GATEWAY_TRANSCRIPT_NOT_ENABLED
business_dialog_unchanged=true_readonly_no_change
```

No Asterisk env values were printed.

## Gateway Read-Only Findings

```text
target=45.61.48.199
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime=up_1h35m_at_check
unit=/etc/systemd/system/ai-secretary-gateway.service present
unit_verify=UNIT_VERIFY_OK
service_active=inactive
service_enabled=disabled
gateway_user=GATEWAY_USER_PRESENT
gateway_group=GATEWAY_GROUP_PRESENT
env=/etc/ai-secretary/openai-realtime-gateway.env
env_owner_mode=root:gateway:640
openai_api_key_presence=OPENAI_API_KEY_PRESENT_MASKED
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
deploy_path=/opt/ai-secretary-gateway root:root:755
unit_user=User=gateway
unit_group=Group=gateway
unit_working_directory=/opt/ai-secretary-gateway
unit_pythonpath=/opt/ai-secretary-gateway/src
unit_env_file=/etc/ai-secretary/openai-realtime-gateway.env
unit_exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
unit_restart=on-failure
target_listeners_443_8080_8081=NO_TARGET_LISTENERS_443_8080_8081
ufw_status=active
ufw_default_incoming=deny
ufw_default_outgoing=allow
ufw_8080_allow=92.118.85.117 only
rollback_systemctl_available=true
rollback_ss_available=true
rollback_ufw_available=true
```

No gateway env values or token values were printed.

## Local Docs / Template Findings

```text
template=deploy/templates/gateway-systemd.service.example
template_env_file=/etc/ai-secretary/gateway.env
template_exec=/usr/local/bin/ai-secretary-gateway --bind ${GATEWAY_BIND}
live_staged_unit_env_file=/etc/ai-secretary/openai-realtime-gateway.env
live_staged_unit_exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
live_staged_unit_pythonpath=/opt/ai-secretary-gateway/src
handoff_readme_preexisting=false
```

The repo template remains an example only. NODE-032K should validate the live staged unit, not blindly reapply the template.

## Phase B GO / NO-GO

Recommendation: conditional GO for Phase B only after the exact approval phrase is provided and all hard gates are re-confirmed immediately before any state change.

```text
phase_b_go=conditional_after_exact_approval
approval_phrase_present=false
asterisk_gates=pass
gateway_gates=pass
service_enablement_readiness=pass
firewall_listener_gates=pass
business_dialog_enablement_required=false
transcript_or_token_printing_required=false
```

Current blocker:

```text
exact_approval_phrase_absent=true
```

Hard NO-GO for Phase B if any of these occur:

- Asterisk contains `OPENAI_API_KEY`.
- Business dialog gateway transcript use is enabled.
- Gateway env is missing or not `root:gateway 640`.
- Masked gateway secret presence fails.
- Service unit is missing or invalid.
- Service is already enabled unexpectedly before Phase B.
- Unexpected listener exists on `443`, `8080`, or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Smoke would require business dialog enablement.
- Transcript text or token values would be printed.
- Exact approval phrase is absent.

## Phase B Command Plan

Phase B requires exact approval:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Gate re-checks:

```bash
ssh root@92.118.85.117 'hostname; uptime; systemctl is-active ai-secretary-ari.service; systemctl is-enabled ai-secretary-ari.service; pid=$(systemctl show ai-secretary-ari.service -p MainPID --value); if [ -n "$pid" ] && [ "$pid" != 0 ] && tr "\0" "\n" < /proc/$pid/environ | grep -q "^OPENAI_API_KEY="; then echo OPENAI_API_KEY_PRESENT; else echo OPENAI_API_KEY_ABSENT; fi; if test -f /etc/ai-secretary/ari-app.env; then if grep -q "^OPENAI_API_KEY=" /etc/ai-secretary/ari-app.env; then echo SERVICE_ENV_OPENAI_API_KEY_PRESENT; else echo SERVICE_ENV_OPENAI_API_KEY_ABSENT; fi; if grep -q "^STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true" /etc/ai-secretary/ari-app.env; then echo BUSINESS_DIALOG_GATEWAY_TRANSCRIPT_ENABLED; else echo BUSINESS_DIALOG_GATEWAY_TRANSCRIPT_NOT_ENABLED; fi; fi'
ssh root@45.61.48.199 'hostname; uptime; test -f /etc/systemd/system/ai-secretary-gateway.service && echo UNIT_PRESENT || echo UNIT_ABSENT; systemd-analyze verify /etc/systemd/system/ai-secretary-gateway.service && echo UNIT_VERIFY_OK || echo UNIT_VERIFY_FAILED; systemctl is-active ai-secretary-gateway.service 2>/dev/null || true; systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || true; stat -c "%U:%G:%a:%n" /etc/ai-secretary/openai-realtime-gateway.env; grep -q "^OPENAI_API_KEY=" /etc/ai-secretary/openai-realtime-gateway.env && echo OPENAI_API_KEY_PRESENT_MASKED || echo OPENAI_API_KEY_ABSENT; grep -q "^GATEWAY_TOKEN=" /etc/ai-secretary/openai-realtime-gateway.env && echo GATEWAY_TOKEN_PRESENT_MASKED || echo GATEWAY_TOKEN_ABSENT; getent passwd gateway >/dev/null && echo GATEWAY_USER_PRESENT || echo GATEWAY_USER_ABSENT; getent group gateway >/dev/null && echo GATEWAY_GROUP_PRESENT || echo GATEWAY_GROUP_ABSENT; ss -ltnp | grep -q -e ":443" -e ":8080" -e ":8081" && echo TARGET_LISTENER_PRESENT || echo NO_TARGET_LISTENERS_443_8080_8081; ufw status verbose'
```

Manual service start and health/readiness before enablement:

```bash
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service; systemctl is-active ai-secretary-gateway.service; systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || true; ss -ltnp | grep ":8080"; ss -ltnp | grep -q -e ":443" -e ":8081" && echo UNEXPECTED_443_OR_8081 || echo NO_443_OR_8081; ufw status verbose; curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/docs'
```

Enable and reboot Gateway only:

```bash
ssh root@45.61.48.199 'systemctl enable ai-secretary-gateway.service; systemctl is-enabled ai-secretary-gateway.service; reboot'
```

Wait and SSH-return checks:

```powershell
# Poll until SSH returns. Do not use provider power-cycle.
ssh -o ConnectTimeout=10 root@45.61.48.199 'hostname; uptime'
```

Post-reboot checks:

```bash
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service; systemctl is-enabled ai-secretary-gateway.service; ss -ltnp | grep ":8080"; ss -ltnp | grep -q -e ":443" -e ":8081" && echo UNEXPECTED_443_OR_8081 || echo NO_443_OR_8081; ufw status verbose; journalctl -u ai-secretary-gateway.service -n 80 --no-pager'
```

Review logs for lifecycle/status/error facts only. If token values, bearer headers, env dumps, transcript text, or caller audio content appear, stop and rotate exposed tokens.

Asterisk-side smoke using existing helper-bundle strategy:

```bash
ssh root@92.118.85.117 '<create temporary NODE-032K helper bundle and root:root 600 runtime env without printing token values; run scripts/asterisk_gateway_smoke_helper.py with OPENAI_API_KEY unset and STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false; remove temporary helper/env/audio after smoke>'
```

Safe smoke evidence only:

```text
gateway_reachable_from_asterisk
gateway_auth
openai_realtime_from_gateway
gateway_http_status
chunks_sent
transcript_present
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Rollback commands:

```bash
ssh root@45.61.48.199 'systemctl disable ai-secretary-gateway.service || true; systemctl stop ai-secretary-gateway.service || true; systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || echo disabled_or_not_enabled; systemctl is-active ai-secretary-gateway.service 2>/dev/null || echo inactive_or_not_found; ss -ltnp | grep -q -e ":443" -e ":8080" -e ":8081" && echo TARGET_LISTENER_PRESENT || echo NO_TARGET_LISTENERS_443_8080_8081; ufw status verbose'
```

Rollback should preserve historical env values. Restore env ownership/mode only if explicitly chosen by the operator. Rotate tokens if any exposure occurs.

Explicit exclusions:

```text
provider_power_cycle=false
business_dialog_enablement=false
open_443=false
open_8081=false
tls_proxy_change=false
firewall_broadening=false
```

## Phase A Result

```text
node_status=phase_a_readiness_and_command_planning_complete
handoff_archive=docs/handoffs/NODE-032K-phase-a-codex-handoff.md
live_enablement=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
service_started_stopped_restarted_reloaded=false
firewall_changed=false
env_files_edited=false
helper_copied_or_deployed=false
live_smoke=false
business_dialog_enabled=false
server_state_changed=false
notion_write=false
runtime_evidence_create=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
course_submission_staged=false
data_storage_staged=false
node014_server_tar_staged=false
```
