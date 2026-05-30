# NODE-032M Phase A Codex Handoff

This handoff archives NODE-032M Phase A in sanitized form.

Do not include real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts in this file.

## Node

NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env

## Phase

Phase A readiness and retry command planning only.

## Scope Boundary

No live retry, service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, or server state change occurred.

## Approval Gate

Phase B requires the exact approval phrase:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

No other phrase is approval.

## Local Findings

NODE-032L guard:

```text
script=scripts/gateway_smoke_temp_env_guard.py
commands=create,validate,cleanup
token_input=stdin_only
token_output=false
atomic_write=true
temp_env_mode=0600
masked_json_reports=true
cr_lf_rejected=true
literal_newline_material_rejected=true
cleanup_supported=true
```

Asterisk smoke helper:

```text
script=scripts/asterisk_gateway_smoke_helper.py
asterisk_openai_api_key_refused=true
transcript_for_dialog_required_false=true
transcript_logging_required_false=true
gateway_url_token_newline_material_rejected=true
```

## Read-Only Asterisk Gate

Target:

```text
92.118.85.117
```

Sanitized result:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service=active_enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
business_dialog_unchanged=true
```

No env values, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts were printed.

## Read-Only Gateway Gate

Target:

```text
45.61.48.199
```

Sanitized result:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
service_active=inactive
service_enabled=disabled
gateway_user=present
gateway_group=present
env_present=true
env_owner_mode=root:gateway 640
openai_api_key_presence=masked_present
gateway_token_presence=masked_present
workdir_present=true
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
rollback_command_tools=available
```

No env values, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts were printed.

## Phase B Command Plan

Phase B must start by re-running all hard gates. If any gate fails, stop with NO-GO before state change.

Safe temp-env command shape for future Asterisk helper bundle:

```text
python scripts/gateway_smoke_temp_env_guard.py create --output <temp-env-path> --gateway-url http://45.61.48.199:8080
python scripts/gateway_smoke_temp_env_guard.py validate --path <temp-env-path>
python scripts/gateway_smoke_temp_env_guard.py cleanup --path <temp-env-path>
```

The token must be supplied through stdin by a future approved runtime-only step. Commands must never echo, cat, print, log, or store token values outside the temporary env file. Validation may print only masked JSON status.

Future helper-bundle strategy:

```text
copy repo-supported helper bundle to Asterisk temporary path
create temporary env with NODE-032L guard using stdin token input
validate temporary env with NODE-032L guard
source temporary env for one manual helper invocation only
run scripts/asterisk_gateway_smoke_helper.py with approved smoke audio
cleanup temporary env, helper bundle, and audio
```

Gateway Phase B plan after exact approval and gate re-check:

```text
verify service inactive/disabled before retry unless documented otherwise
start service manually only if the approved retry requires readiness proof
verify service active and listener 8080 only
run systemctl enable ai-secretary-gateway.service only if service is disabled and retry plan requires re-enablement
reboot Gateway server only if retry plan requires proving autostart again
wait for SSH return
verify service active/enabled after reboot
verify listener 8080 only, no 443, no 8081
verify UFW 8080/tcp remains restricted to 92.118.85.117
run one Asterisk-side smoke using safe temp env
verify transcript_text_logged=false
verify transcript_used_for_dialog=false
verify business_dialog_unchanged=true
verify Asterisk OPENAI_API_KEY_ABSENT
cleanup temporary helper/env/audio
```

Rollback command plan:

```text
systemctl disable ai-secretary-gateway.service
systemctl stop ai-secretary-gateway.service
verify service inactive/disabled
verify no target listeners on 443, 8080, or 8081
keep firewall unchanged
preserve historical Gateway env unless a separate approved change is required
verify Asterisk OPENAI_API_KEY_ABSENT
rotate tokens if any exposure occurs
```

Explicit exclusions:

```text
provider_power_cycle=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
port_443=false
port_8081=false
tls_proxy_change=false
firewall_broadening=false
```

## GO / NO-GO

Phase B recommendation:

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
technical_readiness=pass
```

Hard NO-GO if any gate changes, if token or transcript text would be printed, if the guard is unavailable or fails validation, if the Gateway env is missing or not `root:gateway 640`, if masked secret presence fails, if the service unit is missing/invalid, if unexpected target listeners exist, if UFW is not source-restricted to `92.118.85.117`, if rollback is unclear, or if business dialog transcript use is enabled.

