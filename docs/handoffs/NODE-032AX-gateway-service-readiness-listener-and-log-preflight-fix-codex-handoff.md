# NODE-032AX Codex Handoff

## Node

```text
NODE-032AX / gateway-service-readiness-listener-and-log-preflight-fix
```

## Branch

```text
feat/node-032ax-gateway-service-readiness-listener-and-log-preflight-fix
```

## Scope

NODE-032AX is a docs-only correction after NODE-032AW. It does not run live checks and does not touch the Gateway, Asterisk, provider controls, Docker, services, firewall, env files, server files, app config, tokens, temp env files, audio, OpenAI, or the Selectel disk image.

## NODE-032AW Blockers Carried Forward

```text
service_became_active=true
service_remained_disabled=true
gateway_process_observed=true
gateway_process_user=gateway
gateway_process_command_included=--host_0.0.0.0_--port_8080
listener_443=absent
listener_8081=absent
listener_8080=not_observed_in_immediate_ss_check
safe_log_filter_unavailable_due_quoting_error=true
final_service_state=inactive_disabled
final_gateway_runtime_process=absent
hard_gate=NO_GO
```

Readiness remains unaccepted because the prior procedure used an immediate listener check and the intended journal filter had a quoting error.

## Corrected Future Listener Wait

Future service-readiness live action must use a bounded wait for the `8080` listener before declaring listener absence:

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  ss -lntup | grep -E '(:8080\s|:8080$)' && break
  sleep 1
done
ss -lntup || true
```

The wait is bounded to ten one-second iterations. Any unexpected listener on `443` or `8081` remains a stop condition.

## Corrected Future Safe Log Filter

Future service-readiness live action must use a simple grep pipeline that avoids nested awk quoting:

```bash
journalctl -u ai-secretary-gateway.service -n 120 --no-pager | grep -Ei 'started|listening|ready|error|failed|exception|8080|443|8081|uvicorn|server' || true
```

The command is for safe readiness/status terms only. It must not dump raw env, request bodies, transcript text, transcript deltas, token values, or complete unfiltered logs.

## Redaction Rule

If any token-like or secret-like line appears in future readiness log output, it must be replaced with:

```text
REDACTED_TOKEN_LIKE_LOG_LINE
```

The future live node must stop rather than preserve or publish raw secret-bearing output.

## Future Stop Conditions

Future live readiness must stop before any smoke or Gateway request if any of these occur:

```text
missing_exact_approval=true
hard_gate_failed=true
unexpected_listener_443_or_8081=true
listener_8080_absent_after_bounded_wait=true
safe_log_filter_unavailable=true
log_output_would_print_secret_or_token=true
rollback_or_final_restore_unclear=true
```

## Future Approval Boundary

The next node must not run without this exact approval phrase:

```text
APPROVE NODE-032AY GATEWAY LISTENER AND LOG READINESS CHECK
```

## Next Recommended Node

```text
NODE-032AY / controlled-gateway-listener-and-log-readiness-check
```

NODE-032AY should remain a readiness check, not a smoke node. It may only re-check hard gates, start the already-installed Gateway service if approved, run the corrected listener wait and safe log filter, then restore the service to inactive/disabled.

## Safety Confirmation

```text
docs_only=true
server_access=false
ssh_used=false
provider_controls_used=false
gateway_power_on=false
smoke_run=false
call_run=false
phase_b=false
gateway_request=false
helper_deploy=false
temp_env_created=false
token_handling=false
openai_request=false
service_action=false
docker_mutation=false
firewall_or_env_change=false
server_file_change=false
app_config_change=false
transcript_text_or_delta_logged=false
audio_generated_or_uploaded=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
