# NODE-032AU / full-gateway-readonly-hard-gate-after-kamatera-recovery

## Summary

NODE-032AU ran a fuller read-only Gateway hard-gate after NODE-032AT confirmed Kamatera Gateway TCP/SSH recovery.

Result:

```text
phase_b_hard_gate=NO_GO
blocker=gateway_service_installed_disabled_without_runtime_or_listener
```

Gateway SSH is recovered, and a disabled `ai-secretary-gateway.service` unit file exists. No Gateway runtime process, Docker runtime candidate, or target listener on `443`, `8080`, or `8081` was observed.

This was not a smoke node. No live smoke, call, retry, helper deploy, token handling, temp env creation, OpenAI request, service action, Docker mutation, firewall/env/server/app config change, audio generation/upload, or disk image action occurred.

## Branch

```text
feat/node-032au-full-gateway-readonly-hard-gate-after-kamatera-recovery
```

## Inputs

Latest expected master:

```text
47b2f935b90a95ce6e107a1c68b2372f5ef1292f
```

Prior NODE-032AT result:

```text
gateway_tcp_22_recovered=true
gateway_ssh_recovered=true
gateway_host=ai-secretary-gateway-node023
os=Ubuntu 24.04.4 LTS
target_listeners_443_8080_8081_observed=false
gateway_runtime_process_observed=false
matching_running_services_observed=false
phase_b_recommendation=NO-GO_PENDING_FULL_GATE_RECHECK
```

## Local Validation

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

Command set:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
```

## Gateway Read-Only Inventory

One bounded read-only SSH session was used. No env values, token values, raw logs, transcript text, or transcript deltas were requested or printed.

Commands:

```text
hostname
uptime
whoami
uname -a
cat /etc/os-release
ss -lntup || true
ps aux | grep -E 'gateway|realtime|stt|uvicorn|gunicorn|python|node|nginx|caddy|docker' | grep -v grep || true
systemctl list-units --type=service --all --no-pager | grep -Ei 'gateway|realtime|stt|nginx|caddy|docker' || true
systemctl list-unit-files --type=service --no-pager | grep -Ei 'gateway|realtime|stt|nginx|caddy|docker' || true
docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null || true
docker ps -a --format '{{.Names}} {{.Status}} {{.Ports}}' 2>/dev/null || true
```

Identity:

```text
gateway_ssh=ok
hostname=ai-secretary-gateway-node023
whoami=root
os=Ubuntu 24.04.4 LTS
kernel=6.8.0-117-generic
uptime_at_check=30_min
```

Listeners:

```text
ssh_tcp_22_listening=true
local_dns_53_listening=true
target_listener_443=false
target_listener_8080=false
target_listener_8081=false
```

Process inventory:

```text
gateway_runtime_process_observed=false
uvicorn_or_gunicorn_process_observed=false
nginx_or_caddy_process_observed=false
docker_process_observed=false
non_gateway_python_process_observed=unattended-upgrades-shutdown-wait
```

Service/unit inventory:

```text
matching_running_or_loaded_service_units_observed=false
ai_secretary_gateway_unit_file_present=true
ai_secretary_gateway_unit_file_state=disabled
ai_secretary_gateway_unit_file_preset=enabled
```

Docker inventory:

```text
docker_ps_output_empty=true
docker_ps_all_output_empty=true
docker_container_candidate_observed=false
```

## Hard-Gate Decision

```text
gateway_tcp_22_recovered=true
gateway_ssh_recovered=true
gateway_unit_file_candidate_present=true
gateway_runtime_process_observed=false
gateway_target_listener_observed=false
docker_runtime_candidate_observed=false
phase_b_hard_gate=NO_GO
blocker=gateway_service_installed_disabled_without_runtime_or_listener
```

The Gateway host is reachable and the unit file candidate is present, but no active Gateway runtime or target listener exists. NODE-032AU therefore does not clear the hard gate for any smoke or call path.

## Safety Boundary

```text
live_smoke=false
call_run=false
retry_run=false
openai_request=false
audio_generated=false
audio_uploaded=false
helper_deploy=false
token_handling=false
temp_env_created=false
service_start_stop_restart_reload=false
docker_mutation=false
apt_update_or_upgrade=false
firewall_or_env_change=false
server_file_change=false
server_state_change=false
provider_controls_used=false
gateway_power_on=false
transcript_text_or_delta_logged=false
disk_image_touched=false
```

## Next Recommendation

```text
NODE-032AV / controlled-gateway-service-readiness-recovery-plan
```

Recommended next boundary: plan a controlled Gateway service readiness recovery/start gate, with explicit approval required before any service action. Smoke, calls, helper deploy, token handling, temp env creation, OpenAI requests, Docker mutation, firewall/env/server/app config changes, transcript text/delta logging, and audio generation/upload remain out of scope unless separately approved.

## Artifacts

Handoff:

```text
docs/handoffs/NODE-032AU-full-gateway-readonly-hard-gate-after-kamatera-recovery-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

