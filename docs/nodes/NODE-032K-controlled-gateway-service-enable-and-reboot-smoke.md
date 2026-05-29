# NODE-032K / controlled-gateway-service-enable-and-reboot-smoke

Status: Phase B attempted; hard NO-GO on token-output safety, rollback performed

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

Long-form sanitized Phase B handoff archive:

```text
docs/handoffs/NODE-032K-phase-b-codex-handoff.md
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

## Phase B Attempt After Exact Approval

Exact approval phrase was provided:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Phase B re-ran hard gates before state-changing commands. The gates passed and the staged service was manually started, enabled, and verified after a Gateway-only reboot. The controlled smoke did not run because a temporary Asterisk smoke env was malformed during preparation and a token value was printed during a diagnostic inspection. That is a hard NODE-032K NO-GO.

The exposed token value is not recorded in this document. Token rotation is required before any future gateway smoke or production use.

### Phase B Commands Run

Sanitized command groups:

```text
git status --short
ssh root@92.118.85.117 '<sanitized Asterisk hard gates>'
ssh root@45.61.48.199 '<sanitized Gateway hard gates>'
tar -cf C:\tmp\node032k-helper.tar '<approved helper bundle files>'
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 '<service/listener/firewall/log redaction readiness checks>'
ssh root@45.61.48.199 'systemctl enable ai-secretary-gateway.service'
ssh root@45.61.48.199 'reboot'
ssh root@45.61.48.199 '<post-reboot active/enabled/listener/firewall/log checks>'
ssh root@92.118.85.117 '<temporary helper bundle transfer>'
ssh root@92.118.85.117 '<temporary runtime env creation attempt>'
ssh root@92.118.85.117 '<temporary audio preparation>'
ssh root@92.118.85.117 '<sanitized temporary env inspection attempt; failed safety boundary>'
ssh root@45.61.48.199 'systemctl disable ai-secretary-gateway.service; systemctl stop ai-secretary-gateway.service'
ssh root@92.118.85.117 '<remove temporary helper/env/audio and re-check Asterisk safety>'
```

The smoke helper invocation did not reach a gateway request after the token-output failure. No transcript text was printed.

### Hard Gate Re-Confirmation

```text
asterisk_ssh=ok
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_process_openai_api_key=OPENAI_API_KEY_ABSENT
asterisk_service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
gateway_ssh=ok
gateway_hostname=ai-secretary-gateway-node023
gateway_unit_present=true
gateway_unit_verify=ok
gateway_service_active_before_phase_b=inactive
gateway_service_enabled_before_phase_b=disabled
gateway_user_group=gateway:gateway present
gateway_env_owner_mode=root:gateway 640
gateway_secret_presence=masked_pass
gateway_deploy_path=/opt/ai-secretary-gateway present
target_listeners_before_phase_b=NO_TARGET_LISTENERS_443_8080_8081
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
rollback_tools_available=true
```

### Pre-Enable Readiness And Enablement

```text
manual_start=true
service_active_after_manual_start=true
service_enabled_before_enablement=disabled
listener_after_manual_start=8080 only
listener_443=false
listener_8081=false
ufw_8080_allow=92.118.85.117 only
log_sensitive_pattern_absent=true
systemctl_enable=true
service_enabled_after_enablement=enabled
firewall_changed=false
env_files_edited=false
```

The first readiness check was too early and did not yet observe the `8080` listener; a delayed re-check observed the service active with `8080` listening and no `443` or `8081`.

### Gateway Reboot Result

```text
gateway_only_reboot=true
asterisk_reboot=false
provider_power_cycle=false
ssh_returned=true
post_reboot_hostname=ai-secretary-gateway-node023
post_reboot_service_active=active
post_reboot_service_enabled=enabled
post_reboot_listener=8080 only
post_reboot_listener_443=false
post_reboot_listener_8081=false
post_reboot_ufw_8080_allow=92.118.85.117 only
post_reboot_log_sensitive_pattern_absent=true
```

### Controlled Smoke Result

```text
controlled_smoke_run=false
controlled_smoke_blocker=token_value_printed_during_temporary_env_diagnostic
gateway_reachable_from_asterisk=not_run_after_blocker
gateway_auth=not_run_after_blocker
openai_realtime_from_gateway=not_run_after_blocker
transcript_text_logged=false
business_dialog_unchanged=true
transcript_used_for_dialog=false
adapter_default_enabled_after_smoke=not_run
```

The malformed temporary env caused the helper to fail closed on the first invocation before gateway access. A following env-key diagnostic printed a token value, which triggered hard NO-GO and stopped the smoke path.

### Rollback And Final State

Rollback was performed after the hard NO-GO:

```text
systemctl_disable=true
systemctl_stop=true
service_enabled_final=disabled
service_active_final=inactive
target_listeners_final=NO_TARGET_LISTENERS_443_8080_8081
firewall_changed=false
ufw_8080_allow=92.118.85.117 only
temporary_helper_bundle_removed=true
temporary_runtime_env_removed=true
temporary_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
env_file_edited=false
provider_power_cycle=false
business_dialog_enablement=false
tls_proxy_change=false
open_443=false
open_8081=false
github_push_pr=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation_added=false
```

The service unit remains installed as the staged artifact from NODE-032I/NODE-032K, but the service is disabled and inactive after rollback.

### Blockers And Next Recommendation

```text
phase_b_result=NO-GO
primary_blocker=token_value_exposed_in_command_output
required_before_retry=rotate_gateway_token
required_before_retry=replace_temporary_env_creation_with_verified_newline-safe_method
required_before_retry=reconfirm_all_hard_gates
next_node=NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
```

Recommendation: NO-GO for further enable/reboot/smoke work until the exposed gateway token is rotated and the helper env creation path is corrected. A future retry must use a safer one-shot env creation method that verifies keys without printing values and must re-confirm all hard gates before any state change.

## Security Remediation: Gateway Token Rotation

NODE-032K security remediation rotated the exposed Gateway token on the Gateway host only. No smoke retry, service enablement, service start, reboot, provider power-cycle, firewall change, Asterisk env change, business dialog enablement, transcript logging, GitHub push, Notion write, Runtime/Evidence update, scheduler, webhook, or automation loop occurred.

Token values were not printed or recorded.

Sanitized command groups:

```text
git status --short
ssh root@45.61.48.199 '<pre-rotation env stat, service/listener/firewall checks>'
ssh root@92.118.85.117 '<read-only Asterisk OPENAI_API_KEY absence check>'
ssh root@45.61.48.199 '<rotate GATEWAY_TOKEN with remote-only generated value; print marker only>'
ssh root@45.61.48.199 '<post-rotation env stat, masked token presence, service/listener/firewall checks>'
ssh root@92.118.85.117 '<read-only Asterisk OPENAI_API_KEY absence check>'
```

Sanitized pre-rotation state:

```text
gateway_ssh=ok
gateway_hostname=ai-secretary-gateway-node023
env_present=true
env_owner_mode=root:gateway:640
service_active=inactive
service_enabled=disabled
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
asterisk_service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
```

Sanitized rotation result:

```text
gateway_token_rotated=true
old_token_printed=false
new_token_printed=false
env_values_printed=false
```

Sanitized post-rotation state:

```text
env_owner_mode=root:gateway:640
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
service_active=inactive
service_enabled=disabled
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
asterisk_service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
```

Remaining before any retry:

```text
token_rotation_blocker=resolved
temp_env_creation_path_blocker=still_open
next_node=NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
smoke_retry=false
systemctl_enable=false
reboot=false
firewall_changed=false
```
