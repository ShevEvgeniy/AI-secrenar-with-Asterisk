# NODE-032J / gateway-service-enable-policy-and-autostart-decision

Status: Docs-only decision complete

## Summary

NODE-032J decides the enable/autostart policy for the staged gateway service installed by NODE-032I.

This node is documentation only. No live apply, SSH, service start/stop/restart/reload/enable, `systemctl enable`, reboot, provider power-cycle, firewall change, env edit, live smoke, call, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, GitHub write, scheduler, webhook, or automation loop occurred.

## Baseline

- NODE-032I merged via PR #11 / merge commit `990dc59d83d26b8a7e851becec69c8327f6e7bbf`.
- NODE-032I completed a controlled staged persistent gateway service install/start/smoke.
- NODE-032I did not enable the service, reboot, provider power-cycle, expose `443`, open `8081`, broaden firewall, or enable business dialog transcript use.

## Commands Run

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032j-gateway-service-enable-policy-and-autostart-decision
git rev-parse --short HEAD
Get-Content docs\nodes\NODE-032I-controlled-persistent-gateway-service-install-start-smoke.md
Get-Content docs\nodes\NODE-032H-production-gateway-persistence-and-reboot-strategy.md
Get-Content docs\master\MASTER_STATUS.md
Get-Content docs\master\MASTER_PLAN.md
Get-Content docs\master\DECISIONS.md -Tail 220
Get-Content docs\master\NODE_REGISTRY.md
Get-Content docs\master\RUNTIME_NOTES.md -Tail 240
Get-Content docs\master\MASTER_STATUS.md -Tail 260
```

No SSH was run. Local docs inspection was sufficient.

## Current Staged Service Truth

NODE-032I left the gateway in this staged state:

```text
service_unit_installed=true
unit=/etc/systemd/system/ai-secretary-gateway.service
unit_preserved_as_staged_artifact=true
service_active=false
service_stopped=true
service_enabled=false
systemctl_enable=false
runtime_user_group=gateway:gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
env_owner_mode=root:gateway 640
working_directory=/opt/ai-secretary-gateway
listen_policy=0.0.0.0:8080 only with UFW restricted to 92.118.85.117
restart=on-failure
pythonpath=/opt/ai-secretary-gateway/src
target_listeners_443_8080_8081=absent_after_cleanup
firewall_changed=false
reboot_proof=false
provider_power_cycle_proof=false
business_dialog_integration=false
```

Important interpretation:

- The staged service artifact exists and passed one manual start plus one controlled Asterisk-side smoke.
- The service is intentionally stopped and disabled.
- Autostart safety is not proven because no enablement, reboot, or provider power-cycle proof has occurred.
- Business dialog integration remains out of scope and must not be combined with service enablement.

## Enable / Autostart Policy Decision

Accepted decision: proceed only through a separate controlled enablement and reboot-smoke node.

```text
policy=separate_controlled_enablement_reboot_smoke
keep_staged_service_installed=true
keep_service_disabled_until_next_exact_approval=true
cleanup_now=false
enable_now=false
business_dialog_integration_now=false
provider_power_cycle_in_next_node=false_unless_separately_scoped
```

Rationale:

- NODE-032I already proved the installed disabled unit can start, listen, authenticate gateway requests, reach OpenAI Realtime, and support one controlled Asterisk-side smoke.
- The remaining production question is unattended startup behavior after enablement and reboot, not another install/start/smoke.
- Enablement changes boot behavior and must be explicitly gated, measured, and reversible.
- Combining enablement with business dialog integration would mix persistence safety with transcript-use policy and increase rollback ambiguity.
- Provider power-cycle proof is stronger than a guest reboot proof and should remain separately scoped unless the operator explicitly includes it.

Rejected for now:

- Immediate `systemctl enable`: not safe without a dedicated gate/reboot proof.
- Keeping the service installed disabled forever as the final production state: acceptable temporarily, but it does not prove production recovery after reboot.
- Cleanup/rollback now: not required because NODE-032I left a useful staged artifact with service stopped, disabled, no target listeners, unchanged firewall, and preserved env.

## Future Enablement Gates

Before any future `systemctl enable ai-secretary-gateway.service`, NODE-032K must re-confirm all gates:

```text
asterisk_reachable=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript_use=disabled
gateway_reachable=true
gateway_env_readable_by_service_runtime=true
gateway_openai_api_key_presence=masked_pass
gateway_token_presence=masked_pass
service_unit_present=true
service_unit_valid=true
manual_service_start_passes=true
service_disabled_before_enablement=true
unexpected_listener_443=false
unexpected_listener_8080=false_before_manual_start
unexpected_listener_8081=false
ufw_8080_allow=92.118.85.117 only
rollback_commands_accepted=true
token_values_printed=false
transcript_text_printed=false
```

Hard NO-GO:

- Asterisk contains `OPENAI_API_KEY`.
- Gateway env is missing or masked secret presence fails.
- Env is not readable by the service runtime.
- Service unit is absent, invalid, or cannot start manually.
- Service is already enabled before the enablement node without explanation.
- Any unexpected listener exists on `443`, `8080`, or `8081` before manual start.
- UFW `8080/tcp` allow is not source-restricted to `92.118.85.117`.
- Rollback commands are not accepted.
- Business dialog transcript use would need to be enabled.
- Token values or transcript text would be printed.

## Future Approval Phrase

The next live enablement node must require this exact phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

No other phrase is approval.

## Next Live Node Recommendation

Next node:

```text
NODE-032K / controlled-gateway-service-enable-and-reboot-smoke
```

Expected NODE-032K scope:

- Re-confirm all hard gates before state change.
- Start the service manually if needed and verify health/readiness.
- Run `systemctl enable ai-secretary-gateway.service`.
- Reboot the Gateway server.
- Verify SSH returns.
- Verify `ai-secretary-gateway.service` auto-starts.
- Verify listener/firewall state.
- Verify logs remain redacted and contain no transcript text.
- Run one controlled Asterisk-side smoke.
- Document final service state and rollback path.

Explicitly out of scope for NODE-032K unless separately approved:

- Provider power-cycle.
- Business dialog enablement.
- TLS/proxy.
- `443`.
- `8081`.
- Firewall broadening.

## Rollback Strategy

Rollback from enabled or partially enabled state:

```bash
systemctl disable ai-secretary-gateway.service || true
systemctl stop ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || echo disabled_or_not_enabled
systemctl is-active ai-secretary-gateway.service 2>/dev/null || echo inactive_or_not_found
ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081
ufw status verbose
```

Unit rollback if the next node changes unit content:

```bash
test -f /etc/systemd/system/ai-secretary-gateway.service.node032k.bak && cp -a /etc/systemd/system/ai-secretary-gateway.service.node032k.bak /etc/systemd/system/ai-secretary-gateway.service
systemctl daemon-reload
```

Cleanup rollback if policy chooses to remove the staged artifact:

```bash
systemctl disable ai-secretary-gateway.service || true
systemctl stop ai-secretary-gateway.service || true
rm -f /etc/systemd/system/ai-secretary-gateway.service
systemctl daemon-reload
ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081
ufw status verbose
```

Env policy:

- Preserve historical env values unless explicitly changed.
- Keep `root:gateway 640` while the staged non-root service remains installed.
- Restore env ownership/mode only if a cleanup/rollback node explicitly chooses full pre-NODE-032I restoration.
- If any token, bearer header, env value, or transcript text is exposed, stop and rotate exposed tokens.

Post-rollback verification:

```text
service_disabled_or_absent=true
service_inactive_or_absent=true
target_listeners_443_8080_8081=absent
firewall_unchanged=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
token_rotation_if_exposure=true
```

## Cleanup Alternative

Choose a cleanup/rollback node instead of NODE-032K if any of these become true:

- The installed unit is not stable or no longer matches the documented service shape.
- Env readability as `root:gateway 640` is disputed or no longer acceptable.
- The operator does not want gateway autostart.
- Monitoring or log redaction is insufficient.
- Reboot risk is not acceptable in the current maintenance window.
- Firewall source restriction cannot be guaranteed.
- Business dialog enablement pressure would mix transcript-use changes with service enablement.

Cleanup node recommendation if needed:

```text
NODE-032K-alt / rollback-staged-gateway-service-artifact
```

## Remaining Blockers

```text
enable_reboot_proof=false
node032k_exact_approval_phrase_provided=false
provider_power_cycle=separately_scoped
business_dialog_integration=out_of_scope
```

Implications:

- No service enablement may occur until `APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE` is provided in a future node.
- No reboot proof exists yet for the Gateway service.
- Provider power-cycle proof is not included in NODE-032K unless separately approved.
- Business dialog transcript use must remain disabled and out of scope.

## Result

```text
node_status=docs_only_decision_complete
decision=separate_controlled_enablement_reboot_smoke
next_node=NODE-032K_controlled_gateway_service_enable_and_reboot_smoke
approval_phrase=APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
live_apply=false
ssh_used=false
server_state_changed=false
service_started_stopped_restarted_reloaded_enabled=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_changed=false
env_files_edited=false
live_smoke=false
calls=false
business_dialog_enabled=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
course_submission_staged=false
data_storage_staged=false
node014_server_tar_staged=false
```
