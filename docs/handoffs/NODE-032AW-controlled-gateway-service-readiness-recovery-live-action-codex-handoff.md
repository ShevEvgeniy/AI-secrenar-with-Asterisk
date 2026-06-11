# NODE-032AW / controlled-gateway-service-readiness-recovery-live-action - Codex Handoff

Date: 2026-06-11

Branch:

```text
feat/node-032aw-controlled-gateway-service-readiness-recovery-live-action
```

## Scope

NODE-032AW ran the approved controlled Gateway service-readiness recovery cycle.

This was not a smoke node and not Phase B. No Gateway HTTP request, OpenAI request, call, smoke, helper deploy, temp env creation, token handling, Docker mutation, service enable/disable/restart/reload, firewall/env/server/app config change, apt action, audio generation/upload, or disk image action occurred.

Allowed live mutation was limited to:

```text
systemctl_start_ai_secretary_gateway_service=true
systemctl_stop_ai_secretary_gateway_service=true
```

## Approval

Exact approval phrase was provided:

```text
APPROVE NODE-032AW GATEWAY SERVICE READINESS RECOVERY
```

## Local Validation Before Live Action

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Live Commands Run

One bounded SSH session was used against Gateway `45.61.48.199`.

Read-only pre-state:

```text
hostname
uptime
whoami
uname -a
cat /etc/os-release
systemctl is-enabled ai-secretary-gateway.service || true
systemctl is-active ai-secretary-gateway.service || true
ss -lntup || true
ps aux | grep -E 'gateway|realtime|stt|uvicorn|gunicorn|python|node|nginx|caddy|docker' | grep -v grep || true
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null || true
docker ps -a --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null || true
```

Allowed live action:

```text
systemctl start ai-secretary-gateway.service
```

Read-only post-start:

```text
systemctl is-active ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service || true
systemctl status ai-secretary-gateway.service --no-pager -l || true
ss -lntup || true
ps aux | grep -E 'gateway|realtime|stt|uvicorn|gunicorn|python|node|nginx|caddy|docker' | grep -v grep || true
journalctl -u ai-secretary-gateway.service -n 80 --no-pager | grep -Ei 'started|listening|ready|error|failed|exception|8080|443|8081' | safe_redaction_filter
```

Allowed rollback:

```text
systemctl stop ai-secretary-gateway.service
```

Read-only final checks:

```text
systemctl is-active ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service || true
ss -lntup || true
ps aux | grep -E 'gateway|realtime|stt|uvicorn|gunicorn|python|node|nginx|caddy|docker' | grep -v grep || true
```

## Pre-State

Gateway identity:

```text
gateway_ssh=ok
hostname=ai-secretary-gateway-node023
whoami=root
os=Ubuntu 24.04.4 LTS
kernel=6.8.0-117-generic
uptime_at_check=1h13m
```

Pre-state service and listeners:

```text
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listener_443=false
target_listener_8080=false
target_listener_8081=false
gateway_runtime_process_observed=false
docker_inventory_empty=true
```

## Start Result

```text
systemctl_start_command_ran=true
ai_secretary_gateway_service_active_after_start=active
ai_secretary_gateway_service_enabled_after_start=disabled
gateway_runtime_process_observed_after_start=true
gateway_runtime_process_user=gateway
gateway_runtime_command=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
```

Note: the command output included `START_EXIT=True` due client-shell interpolation of `$?`; the numeric exit code was not used as evidence. Active service state and runtime process presence are the authoritative start evidence.

## Listener And Process Result

Immediate post-start listener inventory:

```text
listener_443=false
listener_8080=false
listener_8081=false
```

The service entered `active` state and a Gateway process was present with `--port 8080`, but the immediate `ss -lntup` check did not show an `8080` listener.

## Safe Log Result

The redacted journal filter command had a quoting error, so no reliable safe journal-filter evidence was captured. No raw journal lines from that command were recorded into this handoff.

Safe status evidence from `systemctl status` included only service metadata and a systemd start line, with no token values, raw env output, transcript text, or transcript deltas.

```text
safe_log_filter_result=unavailable_due_quoting_error
raw_journal_lines_committed=false
token_values_printed=false
transcript_text_or_delta_logged=false
```

## Stop And Final State

```text
systemctl_stop_command_ran=true
ai_secretary_gateway_service_active_final=inactive
ai_secretary_gateway_service_enabled_final=disabled
target_listener_443_final=false
target_listener_8080_final=false
target_listener_8081_final=false
gateway_runtime_process_observed_final=false
docker_mutation=false
```

Note: the command output included `STOP_EXIT=True` due client-shell interpolation of `$?`; final inactive state is the authoritative stop evidence.

## Hard-Gate Result

```text
service_start_result=active
gateway_process_after_start=true
listener_8080_after_start=false
final_state_restored=true
hard_gate_result=NO_GO
blocker=service_active_but_8080_listener_not_observed_in_immediate_check
secondary_note=safe_log_filter_unavailable_due_quoting_error
```

## Next Recommendation

```text
NODE-032AX / gateway-service-readiness-listener-and-log-preflight-fix
```

The next node should remain no-smoke and should plan a corrected readiness check with a bounded wait for the `8080` listener and a local-safe log redaction command that cannot leak token or transcript material.

## Safety

```text
smoke=false
call_run=false
phase_b=false
gateway_http_request=false
openai_request=false
audio_generated=false
audio_uploaded=false
helper_deploy=false
token_handling=false
temp_env_created=false
token_values_printed=false
service_enable=false
service_disable=false
service_restart=false
service_reload=false
docker_mutation=false
firewall_or_env_change=false
server_file_change=false
app_config_change=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

