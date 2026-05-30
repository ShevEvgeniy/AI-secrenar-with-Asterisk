# NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan

Status: local implementation and docs complete

## Summary

NODE-032L fixes the local blocker found in NODE-032K by adding a newline-safe, redaction-safe temporary env creation and validation path for a future Asterisk-side Gateway smoke retry.

This is not a live retry node. No SSH, live smoke, service start/stop/restart/reload/enable, reboot, provider power-cycle, firewall change, server env edit, Asterisk env change, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

Long-form sanitized handoff archive:

```text
docs/handoffs/NODE-032L-codex-handoff.md
```

## Context

NODE-032K merged via PR #13 / merge commit `cf1480c`.

NODE-032K proved the enable/reboot/autostart path up to service active/enabled after Gateway-only reboot, but the controlled smoke did not complete. A malformed temporary Asterisk env caused the helper to fail closed, then a follow-up diagnostic printed a Gateway token value. The Gateway token was rotated, and final service state returned to installed but inactive/disabled with no listeners on `443`, `8080`, or `8081`.

Before NODE-032L, retry remained blocked until the temporary env creation and verification path became newline-safe and guaranteed to never print values.

## Implementation

NODE-032L adds:

```text
scripts/gateway_smoke_temp_env_guard.py
```

The guard supports three local CLI actions for future helper-bundle use:

```text
create   # read GATEWAY_TOKEN from stdin and write a root/helper-owned temp env
validate # verify required keys and safe flags without printing values
cleanup  # remove the temporary env file
```

It writes only this future smoke env shape:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_ADAPTER_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
STT_GATEWAY_URL=<gateway-url>
STT_GATEWAY_TOKEN=<token-read-from-stdin>
```

The token value is read from stdin and is never printed by the guard. Reports include only safe fields such as `token_present_masked=true`, `secret_values_printed=false`, and `transcript_text_logged=false`.

NODE-032L also hardens:

```text
scripts/asterisk_gateway_smoke_helper.py
```

The smoke helper now fails closed if gateway URL or token env values contain newline material, including literal escaped newline markers. Error output names the offending key but does not print the value.

## Safe Temp-Env Behavior

```text
newline_safe=true
token_source=stdin_only
token_values_printed=false
transcript_text_printed=false
missing_token_fails_closed=true
multiline_token_fails_closed=true
literal_newline_material_fails_closed=true
dialog_transcript_use_required_false=true
transcript_logging_required_false=true
asterisk_openai_api_key_refused=true
temp_env_mode=0600
atomic_write=true
cleanup_supported=true
```

The guard validates required keys and fails closed if:

- the token is missing;
- the token contains CR/LF or literal newline material;
- the gateway URL contains CR/LF or literal newline material;
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG` is not `false`;
- `STT_GATEWAY_LOG_TRANSCRIPT` is not `false`;
- gateway adapter enablement flags are not explicit.

## Future Retry Boundary

NODE-032L does not authorize a smoke retry. A future retry must be a separate live node with exact approval and immediate hard-gate re-confirmation.

Future Asterisk-side helper-bundle shape should use the guard instead of hand-built shell `printf` env assembly:

```text
ssh root@45.61.48.199 '<masked token extraction without printing value>' |
ssh root@92.118.85.117 'python3 /tmp/node032m-asterisk-helper/scripts/gateway_smoke_temp_env_guard.py create --output /tmp/node032m-gateway-client.env --gateway-url http://45.61.48.199:8080'
ssh root@92.118.85.117 'python3 /tmp/node032m-asterisk-helper/scripts/gateway_smoke_temp_env_guard.py validate --path /tmp/node032m-gateway-client.env'
ssh root@92.118.85.117 '<run one approved smoke with set -a; . /tmp/node032m-gateway-client.env; set +a; unset OPENAI_API_KEY>'
ssh root@92.118.85.117 'python3 /tmp/node032m-asterisk-helper/scripts/gateway_smoke_temp_env_guard.py cleanup --path /tmp/node032m-gateway-client.env'
```

The retry node must not print token values, transcript text, bearer headers, raw env output, or private keys.

## Validation

Focused tests:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
```

Result:

```text
24 passed
```

Full suite:

```text
python -m pytest
```

Expected environmental result remains:

```text
219 passed, 6 failed
```

Known environmental failures:

- missing `src/scripts/make_demo_audio.py`;
- missing `sentence_transformers`.

## Next Recommendation

```text
NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
```

NODE-032M may retry the controlled enable/reboot/smoke only after exact approval, immediate hard-gate re-confirmation, and use of the newline-safe temp env guard.

## Result

```text
node_status=local_implementation_docs_complete
live_smoke=false
ssh=false
service_action=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_changed=false
server_env_edited=false
server_state_changed=false
business_dialog_enabled=false
token_values_printed=false
transcript_text_printed=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation_added=false
course_submission_staged=false
data_storage_staged=false
node014_server_tar_staged=false
```
