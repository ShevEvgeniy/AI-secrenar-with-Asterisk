# NODE-032AV / controlled-gateway-service-readiness-recovery-plan

## Summary

NODE-032AV is a docs-only planning node. It defines the next safe live-action boundary after NODE-032AU found that the Gateway host is reachable and has an installed disabled Gateway service unit, but no Gateway runtime or target listener is active.

No recovery command was executed in this node.

## Branch

```text
feat/node-032av-controlled-gateway-service-readiness-recovery-plan
```

## Current Blocker

NODE-032AU hard-gate result:

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

Interpretation: host recovery is complete enough for a future controlled service-readiness node, but not enough for smoke. The next action must prove Gateway service readiness and rollback without token handling, helper deploy, temp env creation, OpenAI requests, calls, or smoke.

## Controlled Recovery Objective

Future NODE-032AW should:

```text
reconfirm_gateway_hard_gates=true
start_gateway_service_only_if_exactly_approved=true
verify_service_active=true
verify_expected_8080_listener=true
verify_no_443_or_8081_listener=true
verify_firewall_unchanged_source_restricted=true
review_logs_for_safe_status_only=true
restore_service_to_inactive_disabled=true
avoid_smoke_and_openai_requests=true
```

This is a service-readiness recovery boundary only.

## Future Approval Phrase

No live action is allowed unless the coordinator provides exactly:

```text
APPROVE NODE-032AW GATEWAY SERVICE READINESS RECOVERY
```

## Future Read-Only Pre-Checks

Allowed future pre-checks after exact approval and before service action:

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

Env values must not be printed. Secret checks must remain masked presence only.

## Future Allowed Recovery Commands

Allowed only after exact approval and passing immediate hard gates:

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

The journal review must summarize only safe status/error findings. Do not copy secrets, raw env output, transcript text, transcript deltas, raw provider event bodies, or large logs into docs/chat.

## Forbidden Future Commands

The next node must not run:

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

The next node must also not run smoke, calls, helper deploy, temp env creation, token handling, OpenAI requests, audio generation/upload, business-dialog transcript integration, Docker mutation, firewall broadening, persistent env changes, or app config changes.

## Stop Conditions

Stop before service action if any of these occur:

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

If NODE-032AW starts the service, it must restore the safe final state:

```text
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listeners_443_8080_8081_absent=true
firewall_unchanged=true
env_unchanged=true
server_files_unchanged=true
docker_unchanged=true
```

Rollback command shape:

```text
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -lntup
ufw status verbose
```

## Evidence Requirements

Before service action:

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

After service action:

```text
service_active_state
listener_8080_presence
listener_443_absence
listener_8081_absence
safe_log_review_summary
firewall_unchanged
```

After rollback:

```text
service_inactive
service_disabled
target_listeners_absent
firewall_unchanged
env_unchanged
no_secret_or_transcript_output
```

## Validation

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
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

## Next Recommendation

```text
NODE-032AW / controlled-gateway-service-readiness-recovery-live-action
```

## Handoff

```text
docs/handoffs/NODE-032AV-controlled-gateway-service-readiness-recovery-plan-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

