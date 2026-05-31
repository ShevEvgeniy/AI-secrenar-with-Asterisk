# NODE-032Q Phase A Codex Handoff

This sanitized handoff archives the NODE-032Q Phase A readiness and command planning pass.

It contains no real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Scope

NODE-032Q prepares a controlled Gateway smoke retry using all three local safety layers:

- NODE-032L safe temp-env guard.
- NODE-032N complete Asterisk helper bundle.
- NODE-032P runtime dependency preflight for `httpx`, `fastapi`, and `websockets`.

Phase A was read-only readiness and planning only. No live retry, dependency install, service action, `systemctl enable`, reboot, provider power-cycle, firewall change, server env edit, helper deploy, live smoke, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, PR, or server state change occurred.

## Branch Base

```text
branch=feat/node-032q-controlled-gateway-smoke-retry-with-runtime-dependency-preflight
base_commit=e2fb600785534ad6df088bbdfb055a82341d92cc
base_context=NODE-032P merge commit from PR #18
```

## Local Tooling Findings

Safe temp-env guard:

```text
script=scripts/gateway_smoke_temp_env_guard.py
commands=create,validate,cleanup
token_source=stdin_only
temp_env_mode=0600
cr_lf_rejected=true
literal_newline_material_rejected=true
safe_json_only=true
secret_values_printed=false
transcript_text_logged=false
```

Helper bundle:

```text
script=scripts/asterisk_gateway_helper_bundle.py
commands=manifest,create,validate
bundle_includes_smoke_helper=true
bundle_includes_temp_env_guard=true
bundle_includes_ai_secretary_config=true
bundle_includes_stt_adapter_modules=true
third_party_vendoring=false
gateway_token_read=false
secret_values_printed=false
transcript_text_logged=false
```

Runtime dependency preflight:

```text
runtime_modules_required=httpx,fastapi,websockets
reports_runtime_modules_required=true
reports_runtime_modules_ok=true
reports_missing_runtime_modules=true
missing_runtime_dependency_fails_closed=true
preflight_before_project_import=true
preflight_before_token_handling=true
preflight_before_temp_env_creation=true
preflight_before_smoke=true
preflight_before_gateway_request=true
```

Local command checks:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
python scripts/asterisk_gateway_helper_bundle.py create --output <workspace_temp_bundle>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <workspace_temp_bundle>
```

Local validation result:

```text
manifest_ok=true
create_ok=true
validate_ok=true
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
local_temp_bundle_removed=true
```

The first local cleanup attempt hit Windows file attribute deletion friction for the temporary bundle. Only the temporary workspace bundle created by this Phase A run was cleaned up after a path safety check and read-only attribute clearing. No tracked source or server state was changed.

## Asterisk Read-Only Gates

Server: `92.118.85.117`

```text
ssh_reachable=true
hostname=tula
uptime_observed=true
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog=UNCHANGED_BY_READONLY_GATE
```

One initial read-only service-env command emitted a shell `tr` syntax error from command quoting; it did not print secrets. The service env check was rerun without `tr` and confirmed `OPENAI_API_KEY=ABSENT`.

A direct read-only runtime module import probe on Asterisk also confirmed the prior NODE-032O blocker is still present:

```text
runtime_module_httpx=missing
runtime_module_fastapi=missing
runtime_module_websockets=missing
secret_values_printed=false
transcript_text_logged=false
```

## Gateway Read-Only Gates

Server: `45.61.48.199`

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
unit_file=/etc/systemd/system/ai-secretary-gateway.service present
unit_verify=OK
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user=PRESENT
gateway_group=PRESENT
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env present
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
gateway_workdir=/opt/ai-secretary-gateway present
target_listeners_443_8080_8081=NONE
ufw_status=active
ufw_default_incoming=deny
ufw_8080_source=ASTERISK_ONLY
ufw_8080_broad=ABSENT
rollback_commands=AVAILABLE
```

No env values were printed.

## Phase B Approval Gate

Exact approval phrase:

```text
APPROVE NODE-032Q RUNTIME-PREFLIGHT SMOKE RETRY
```

Any other phrase is not approval.

## Phase B Command Plan Summary

Phase B must re-confirm hard gates before any state-changing command.

Planned command groups:

1. Re-check Asterisk gates: SSH, hostname/uptime, `ai-secretary-ari.service` active/enabled, process/service/env-file `OPENAI_API_KEY_ABSENT`, business dialog Gateway transcript flag not enabled.
2. Re-check Gateway gates: SSH, unit present and verified, service state, `gateway:gateway`, env metadata `root:gateway 640`, masked OpenAI/Gateway secret presence, workdir, listeners, UFW source restriction, rollback command availability.
3. Create local helper bundle and validate it locally.
4. Stage temporary helper bundle to Asterisk only after exact approval and successful hard gates.
5. Run remote staged helper-bundle validation before token handling.
6. Stop as NO-GO if `missing_runtime_modules` is non-empty for `httpx`, `fastapi`, or `websockets`; do not install dependencies in NODE-032Q.
7. Only if remote runtime preflight passes, use NODE-032L guard to create and validate temporary env with Gateway token supplied through stdin only.
8. Start Gateway service for smoke readiness only if it remains inactive and gates pass; do not enable it.
9. Verify listener `8080`, no `443` or `8081`, UFW restriction, and log redaction.
10. Run exactly one Asterisk-side non-business-dialog smoke.
11. Capture safe metrics only: Gateway reachable/auth result, Gateway HTTP status if available, OpenAI Realtime/session result, chunk/event counts if available, transcript presence flag if applicable, `transcript_text_logged=false`, `transcript_used_for_dialog=false`, `business_dialog_unchanged=true`, and `adapter_default_enabled_after_smoke=false`.
12. Clean up temporary helper bundle, temp env, and audio.
13. Roll back service state if needed, keeping firewall unchanged and Asterisk without `OPENAI_API_KEY`.

Explicit exclusions:

```text
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
port_443=false
port_8081=false
tls_proxy_changes=false
firewall_broadening=false
```

## GO / NO-GO

Current recommendation:

```text
phase_b_recommendation=NO_GO
reason=asterisk_runtime_modules_missing
missing_runtime_modules=httpx,fastapi,websockets
dependency_install_in_NODE_032Q=false
```

Hard NO-GO if any of the following occurs:

- Asterisk contains `OPENAI_API_KEY`.
- Business dialog Gateway transcript use is enabled.
- Runtime dependency preflight fails.
- Safe temp-env guard is unavailable or fails validation.
- Helper bundle preflight fails.
- Any command would print token values.
- Any command would print transcript text.
- Gateway env is missing or not `root:gateway 640`.
- Masked Gateway secret presence fails.
- Gateway service unit is missing or invalid.
- Unexpected listener exists on `443` or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Exact approval phrase is absent.

## Next Step

```text
NODE-032R / controlled-asterisk-runtime-dependency-resolution-or-alternate-helper-strategy
```

NODE-032Q Phase B should not run while the Asterisk runtime modules are missing. A separately approved node should either install the missing runtime dependencies on Asterisk or choose an alternate helper strategy that avoids those imports without weakening token/transcript safety.
