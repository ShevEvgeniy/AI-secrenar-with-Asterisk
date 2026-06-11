# NODE-032AX / gateway-service-readiness-listener-and-log-preflight-fix

## Summary

NODE-032AX is a docs-only correction for the Gateway service-readiness procedure after NODE-032AW.

NODE-032AW proved that the installed Gateway service can become active and spawn the expected `gateway` runtime process, but readiness was not accepted:

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

NODE-032AX does not run a live retry. It fixes the future evidence procedure by requiring a bounded listener wait and a simpler safe journal filter.

## Branch

```text
feat/node-032ax-gateway-service-readiness-listener-and-log-preflight-fix
```

## Scope

```text
docs_only=true
live_checks=false
ssh=false
provider_controls=false
gateway_power_on=false
smoke=false
calls=false
phase_b=false
gateway_requests=false
helper_deploy=false
temp_env_creation=false
token_handling=false
openai_requests=false
service_actions=false
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_change=false
audio_generation_or_upload=false
disk_image_action=false
```

## Corrected Listener Wait

Future readiness must not rely on a single immediate `ss` sample after `systemctl start`. Use this bounded check:

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do
  ss -lntup | grep -E '(:8080\s|:8080$)' && break
  sleep 1
done
ss -lntup || true
```

Acceptance rules:

```text
listener_8080_seen_within_bounded_wait=required
listener_443_absent=required
listener_8081_absent=required
bounded_wait_seconds_max=10
```

If `8080` remains absent after the bounded wait, the future node must stop as NO-GO and restore the safe final state.

## Corrected Safe Journal Filter

Future readiness must avoid the quoting failure seen in NODE-032AW. Use this simple command:

```bash
journalctl -u ai-secretary-gateway.service -n 120 --no-pager | grep -Ei 'started|listening|ready|error|failed|exception|8080|443|8081|uvicorn|server' || true
```

The filter is not permission to publish raw logs. It is only for readiness/status lines matching safe terms. The future operator must not record raw env, request bodies, transcript text, transcript deltas, token values, or complete unfiltered logs.

## Redaction Rules

Any secret-like or token-like future log line must be replaced with:

```text
REDACTED_TOKEN_LIKE_LOG_LINE
```

If redaction cannot be guaranteed, the future node must stop before preserving output.

Forbidden outputs remain:

```text
token_values
secret_values
raw_env_output
transcript_text
transcript_delta_content
raw_provider_event_body_with_text
audio_payload
```

## Future Stop Conditions

Future live readiness must stop before any smoke if any condition is true:

```text
exact_approval_phrase_absent=true
hard_gate_failed=true
unexpected_listener_443=true
unexpected_listener_8081=true
listener_8080_absent_after_bounded_wait=true
safe_log_filter_unavailable=true
log_output_would_print_token_or_secret=true
rollback_or_final_restore_unclear=true
```

## Future Approval Phrase

Future NODE-032AY must not run unless this exact phrase is provided:

```text
APPROVE NODE-032AY GATEWAY LISTENER AND LOG READINESS CHECK
```

## Next Recommended Node

```text
NODE-032AY / controlled-gateway-listener-and-log-readiness-check
```

NODE-032AY should remain a controlled service-readiness check only. It should not be a smoke node and should not handle tokens, create temp env files, deploy helpers, make Gateway/OpenAI requests, mutate Docker, broaden firewall, change env/app config, enable the service, reboot, generate audio, or touch the disk image.

## Handoff

```text
docs/handoffs/NODE-032AX-gateway-service-readiness-listener-and-log-preflight-fix-codex-handoff.md
```

## Protected Local Artifacts

These artifacts remain untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
