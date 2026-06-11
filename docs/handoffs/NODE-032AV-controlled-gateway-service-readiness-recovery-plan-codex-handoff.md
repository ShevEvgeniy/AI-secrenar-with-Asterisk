# NODE-032AV / controlled-gateway-service-readiness-recovery-plan - Codex Handoff

Date: 2026-06-11

Branch:

```text
feat/node-032av-controlled-gateway-service-readiness-recovery-plan
```

## Scope

NODE-032AV is a repository-only, docs-only planning node. It defines the next safe live-action boundary after NODE-032AU found the Gateway host reachable but the Gateway service not running.

No server access, SSH, provider controls, Gateway power action, smoke, call, helper deploy, token handling, temp env creation, OpenAI request, service action, Docker mutation, firewall/env/server/app config change, apt action, audio generation/upload, transcript text/delta logging, or disk image action occurred.

## Current Gateway Blocker

NODE-032AU established:

```text
gateway_ssh_reachable=true
host=ai-secretary-gateway-node023
os=Ubuntu_24.04.4_LTS
kernel=6.8.0-117-generic
target_listeners_443_8080_8081=absent
gateway_runtime_process=absent
ai_secretary_gateway_service_unit=present
ai_secretary_gateway_service_state=disabled
ai_secretary_gateway_service_preset=enabled
docker_inventory=empty
phase_b_hard_gate=NO_GO
blocker=gateway_service_installed_disabled_without_runtime_or_listener
```

## Controlled Recovery Objective

The next live-action node should prove whether the already-installed Gateway systemd service can be started for readiness, verified on the expected restricted listener path, and restored to a safe inactive/disabled final state without running a smoke.

This is a service-readiness recovery boundary only. It must not include Asterisk-origin smoke, helper deployment, token transfer into temp env, OpenAI requests, audio generation/upload, business-dialog integration, Docker mutation, firewall broadening, or service enablement.

## Future Approval Phrase

The next node must not perform live action unless the coordinator provides exactly:

```text
APPROVE NODE-032AW GATEWAY SERVICE READINESS RECOVERY
```

## Future Preconditions

Before any future state-changing command, NODE-032AW should re-confirm:

```text
gateway_ssh_reachable=true
gateway_host_expected=ai-secretary-gateway-node023
target_listeners_443_8080_8081_absent=true
ai_secretary_gateway_unit_present=true
ai_secretary_gateway_unit_verify_ok=true
ai_secretary_gateway_service_inactive_or_document_exact_state=true
ai_secretary_gateway_service_disabled_or_document_exact_state=true
gateway_env_metadata_safe=true
masked_gateway_secret_presence_passes=true
ufw_active_default_deny=true
ufw_8080_source_restricted_to_92.118.85.117=true
rollback_plan_clear=true
```

Secret checks must be masked presence only. Env values must never be printed.

## Future Read-Only Pre-Checks

Allowed future pre-checks, after exact approval and before any service action:

```text
hostname
uptime
whoami
uname -a
systemctl status ai-secretary-gateway.service --no-pager
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
systemd-analyze verify /etc/systemd/system/ai-secretary-gateway.service
stat -c '%U:%G:%a:%n' /etc/ai-secretary/openai-realtime-gateway.env
grep -q '^OPENAI_API_KEY=' /etc/ai-secretary/openai-realtime-gateway.env && echo OPENAI_API_KEY_PRESENT_MASKED || echo OPENAI_API_KEY_ABSENT
grep -q '^GATEWAY_TOKEN=' /etc/ai-secretary/openai-realtime-gateway.env && echo GATEWAY_TOKEN_PRESENT_MASKED || echo GATEWAY_TOKEN_ABSENT
ss -lntup
ufw status verbose
```

Do not print env values, token values, raw logs, transcript text, or transcript deltas.

## Future Recovery Commands

Allowed future recovery commands only after exact NODE-032AW approval and passing immediate hard gates:

```text
systemctl start ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
ss -lntup
systemctl status ai-secretary-gateway.service --no-pager
journalctl -u ai-secretary-gateway.service --no-pager -n 80
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -lntup
ufw status verbose
```

The journal check must be reviewed only for safe status/error evidence. It must not include token values, transcript text, transcript deltas, raw provider event bodies, or raw env dumps in the closeout.

## Forbidden Future Commands

NODE-032AW must not run:

```text
systemctl enable ai-secretary-gateway.service
systemctl disable ai-secretary-gateway.service
systemctl restart ai-secretary-gateway.service
systemctl reload ai-secretary-gateway.service
reboot
poweroff
docker start
docker restart
docker compose up
docker compose restart
apt update
apt upgrade
ufw allow
ufw delete
```

It must not run smoke, helper deploy, token handling, temp env creation, OpenAI requests, audio generation/upload, or business-dialog transcript integration.

## Stop Conditions

Stop before service action if:

```text
exact_approval_phrase_absent=true
gateway_ssh_unreachable=true
unit_missing_or_invalid=true
env_metadata_wrong=true
masked_secret_presence_fails=true
unexpected_listener_443_8080_8081_present=true
ufw_not_active_or_not_default_deny=true
ufw_8080_not_source_restricted=true
rollback_plan_unclear=true
any_command_would_print_secret_values=true
```

Stop after service start and roll back if:

```text
service_start_fails=true
service_active_false_after_start=true
listener_8080_absent_after_start=true
unexpected_listener_443_or_8081_present=true
firewall_broadened_or_changed=true
logs_show_secret_or_transcript_text=true
```

## Rollback Boundary

If the future node starts the service, it must restore the pre-node safe state:

```text
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -lntup
ufw status verbose
```

Expected final state unless a future approval explicitly says otherwise:

```text
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listeners_443_8080_8081_absent=true
firewall_unchanged=true
env_unchanged=true
server_files_unchanged=true
docker_unchanged=true
```

## Evidence To Capture

Before future service action:

```text
approval_phrase_exact
hard_gate_recheck_results
unit_verify_result
service_active_enabled_state
env_owner_group_mode
masked_secret_presence
target_listener_absence
ufw_source_restriction
```

After future service start:

```text
service_active_state
listener_8080_presence
listener_443_absence
listener_8081_absence
safe_log_review_summary
firewall_unchanged
```

After future rollback:

```text
service_inactive
service_disabled
target_listeners_absent
firewall_unchanged
env_unchanged
no_secret_or_transcript_output
```

## Next Recommendation

```text
NODE-032AW / controlled-gateway-service-readiness-recovery-live-action
```

## Safety

```text
docs_only=true
live_smoke=false
call_run=false
phase_b=false
server_access=false
ssh_used=false
provider_controls_used=false
gateway_power_on=false
service_action=false
docker_mutation=false
helper_deploy=false
token_handling=false
temp_env_created=false
openai_request=false
audio_generated=false
audio_uploaded=false
firewall_or_env_change=false
server_file_change=false
server_state_change=false
transcript_text_or_delta_logged=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

