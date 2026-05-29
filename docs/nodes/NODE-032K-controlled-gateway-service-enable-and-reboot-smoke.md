# NODE-032K / controlled-gateway-service-enable-and-reboot-smoke

Status: Phase A readiness and command planning complete

## Summary

NODE-032K prepares controlled Gateway service enablement and reboot smoke after NODE-032J.

Phase A is read-only readiness plus command planning only. No live enablement, `systemctl enable`, reboot, provider power-cycle, service start/stop/restart/reload, firewall change, env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation loop, or server state change occurred.

Phase B may enable `ai-secretary-gateway.service`, reboot the Gateway server, verify auto-start, and run one Asterisk-side smoke only after the exact approval phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

No other phrase is approval.

Long-form sanitized Phase A handoff archive:

```text
docs/handoffs/NODE-032K-phase-a-codex-handoff.md
```

## Baseline

- NODE-032I merged via PR #11 / merge commit `990dc59d83d26b8a7e851becec69c8327f6e7bbf`.
- NODE-032I installed the staged gateway service, created `gateway:gateway`, changed the gateway env to `root:gateway 640`, started and smoked the service, then stopped it.
- NODE-032I left the service disabled / not enabled and did not run `systemctl enable`, reboot, provider power-cycle, or business dialog enablement.
- NODE-032J merged via PR #12 / merge commit `8662f3f91bcdc39d37d516d47d405d71cd63c98c`.
- NODE-032J decided to keep the staged service installed but disabled until a separate controlled enablement/reboot-smoke node receives exact approval.

## Commands Run

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

Read-only SSH checks:

```text
ssh -o ConnectTimeout=20 root@92.118.85.117 '<sanitized Asterisk readiness checks>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<sanitized Gateway readiness checks>'
```

No SSH command printed env values, token values, bearer headers, private keys, transcript text, or raw secret env output.

## Local Docs And Template Findings

```text
start_commit=8662f3f
branch=feat/node-032k-controlled-gateway-service-enable-and-reboot-smoke
handoff_readme_preexisting=false
template=deploy/templates/gateway-systemd.service.example
template_env_file=/etc/ai-secretary/gateway.env
template_exec=/usr/local/bin/ai-secretary-gateway --bind ${GATEWAY_BIND}
staged_live_unit_env_file=/etc/ai-secretary/openai-realtime-gateway.env
staged_live_unit_working_directory=/opt/ai-secretary-gateway
staged_live_unit_exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
staged_live_unit_pythonpath=/opt/ai-secretary-gateway/src
```

The repo systemd file is still an example template only. NODE-032K Phase B must re-check the live staged unit rather than reapply the template.

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

## Service Enablement Readiness

```text
asterisk_reachable=true
asterisk_openai_api_key_absent=true
business_dialog_gateway_transcript_use_disabled=true
gateway_reachable=true
gateway_env_root_gateway_640=true
gateway_masked_secrets_present=true
service_unit_present=true
service_unit_valid=true
service_inactive_before_phase_b=true
service_disabled_before_phase_b=true
gateway_user_group_present=true
target_listeners_absent=true
ufw_8080_source_restricted=true
rollback_commands_available=true
```

NODE-032K Phase A did not manually start the service. Manual start is part of Phase B only after exact approval and immediate gate re-checks.

## Phase B Command Set Summary

Phase B remains blocked until:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Required Phase B sequence:

1. Re-confirm all hard gates on Asterisk and Gateway with masked output only.
2. Manually start `ai-secretary-gateway.service` if needed.
3. Verify manual readiness through service/process/listener/firewall checks and a safe local endpoint check if available.
4. Run `systemctl enable ai-secretary-gateway.service`.
5. Reboot the Gateway server only.
6. Wait for SSH to return.
7. Verify service active/enabled after reboot.
8. Verify listener on `8080`, no `443`, no `8081`, and UFW still restricted to `92.118.85.117`.
9. Check logs for redacted lifecycle/status facts only.
10. Run one Asterisk-side smoke using the existing temporary helper-bundle strategy.
11. Remove temporary helper/env/audio from Asterisk.
12. Document final state or rollback.

Explicit Phase B exclusions:

```text
provider_power_cycle=false
business_dialog_enablement=false
open_443=false
open_8081=false
tls_proxy_change=false
firewall_broadening=false
```

Rollback summary:

```text
systemctl disable ai-secretary-gateway.service
systemctl stop ai-secretary-gateway.service
verify service inactive/disabled
verify no target listeners
verify firewall unchanged
preserve historical env values
restore env ownership/mode only if explicitly chosen
rotate tokens if exposure occurs
```

## GO / NO-GO Recommendation

Recommendation: conditional GO for Phase B only after the exact approval phrase is provided and all hard gates are re-confirmed immediately before state change.

```text
phase_b_go=conditional_after_exact_approval
exact_approval_phrase_absent=true
technical_gates_passed=true
service_enablement_readiness=pass
rollback_plan=clear
```

Current blocker:

```text
exact_approval_phrase_absent=true
```

Hard NO-GO if any gate changes before Phase B, if service is already enabled unexpectedly, if UFW is not source-restricted, if an unexpected listener exists, if business dialog transcript use is enabled, if masked secret presence fails, if rollback is unclear, or if token/transcript values would be printed.

## Result

```text
node_status=phase_a_readiness_and_command_planning_complete
handoff_archive_created=true
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
