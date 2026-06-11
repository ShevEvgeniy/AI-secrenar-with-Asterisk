# NODE-032AU / full-gateway-readonly-hard-gate-after-kamatera-recovery - Codex Handoff

Date: 2026-06-11

Branch:

```text
feat/node-032au-full-gateway-readonly-hard-gate-after-kamatera-recovery
```

## Scope

NODE-032AU ran a fuller read-only Gateway hard-gate after NODE-032AT proved Kamatera Gateway TCP/SSH recovery.

This was not a smoke node. No Phase B, call, helper deploy, token handling, temp env creation, OpenAI request, service action, Docker mutation, firewall/env/server/app config change, audio generation/upload, or disk image action occurred.

## Local Baseline

Starting master:

```text
47b2f935b90a95ce6e107a1c68b2372f5ef1292f
```

Focused validation before docs:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
result=55_passed

git diff --check
result=passed

git diff --name-only -- src tests deploy scripts pyproject.toml
result=empty
```

## Gateway Read-Only Session

One bounded read-only SSH session was used against Gateway host `45.61.48.199`.

Commands were limited to:

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

No env file values, tokens, secrets, raw app logs, transcript text, or transcript deltas were requested or printed.

## Read-Only Findings

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

## Hard-Gate Result

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

Interpretation: Gateway host access is recovered and a disabled `ai-secretary-gateway.service` unit file exists, but the runtime and target listener gates are not ready. NODE-032AU did not start or inspect secret-bearing runtime state.

## Next Recommendation

```text
NODE-032AV / controlled-gateway-service-readiness-recovery-plan
```

The next node should decide whether to request approval for a controlled Gateway service readiness recovery/start gate, while preserving no-smoke and redaction boundaries until explicitly approved.

## Safety

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

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

