# NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env

Status: Phase A readiness and retry command planning complete

NODE-032M prepares a controlled retry of the Gateway enable/reboot/smoke path using the newline-safe temp-env guard added in NODE-032L.

Phase A is read-only readiness plus command planning only. No live retry, service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, or server state change occurred.

Phase B may retry the controlled enable/reboot/smoke path only after the exact approval phrase:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

No other phrase is approval.

## Handoff Archive

Long-form sanitized Phase A handoff:

```text
docs/handoffs/NODE-032M-phase-a-codex-handoff.md
```

Long-form sanitized Phase B handoff:

```text
docs/handoffs/NODE-032M-phase-b-codex-handoff.md
```

The handoff must not contain real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Context

NODE-032K proved the enable/reboot/autostart path up to active/enabled service after Gateway-only reboot, but the controlled smoke did not complete. A malformed temporary Asterisk env caused the helper to fail closed, and a follow-up diagnostic printed a Gateway token value. The token value is not recorded in repo docs. The Gateway token was rotated, and rollback left the service installed but inactive/disabled with no target listeners and unchanged firewall state.

NODE-032L added the newline-safe temp-env guard:

```text
scripts/gateway_smoke_temp_env_guard.py
```

NODE-032L also hardened:

```text
scripts/asterisk_gateway_smoke_helper.py
```

## Commands Run

Local setup:

```text
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032m-controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
```

Note: `git pull --ff-only origin master` was attempted twice and failed because GitHub was unreachable from the environment. Local `master` had already reported up to date with the last known `origin/master` from the NODE-032L merge, so Phase A continued from local `master`.

Local inspections:

```text
rg -n <NODE-032K/NODE-032L/NODE-032M planning patterns> docs/...
rg -n <guard/helper safety patterns> scripts/gateway_smoke_temp_env_guard.py scripts/asterisk_gateway_smoke_helper.py tests/...
Get-Content docs/handoffs/README.md
```

Read-only Asterisk gate:

```text
ssh root@92.118.85.117 '<hostname/uptime, service active/enabled, masked OPENAI_API_KEY absence, transcript flag absence>'
```

Read-only Gateway gate:

```text
ssh root@45.61.48.199 '<hostname/uptime, unit verify, service inactive/disabled, env stat, masked secret presence, listener/firewall/rollback checks>'
```

No command printed env values, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Local Guard / Helper Findings

NODE-032L guard command surface:

```text
create_supported=true
validate_supported=true
cleanup_supported=true
token_input=stdin_only
token_values_printed=false
atomic_write=true
temp_env_mode=0600
masked_safe_json_reports=true
cr_lf_token_material_rejected=true
literal_newline_material_rejected=true
missing_token_fails_closed=true
dialog_transcript_use_required_false=true
transcript_logging_required_false=true
```

Asterisk helper safety:

```text
asterisk_openai_api_key_refused=true
stt_gateway_use_transcript_for_dialog_false_required=true
stt_gateway_log_transcript_false_required=true
gateway_url_token_newline_material_rejected=true
transcript_text_logging_disabled=true
```

## Read-Only Asterisk Findings

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
business_dialog_unchanged=true
```

The first Asterisk command emitted a `tr` usage error from a formatting helper after the safe flags were printed. The command was re-run without that formatting helper and produced the clean sanitized result above. No secret values were printed.

## Read-Only Gateway Findings

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_owner_mode=root:gateway 640
openai_api_key_presence=masked_present
gateway_token_presence=masked_present
workdir_present=true
target_listeners_443_8080_8081=absent
rollback_command_tools=available
```

## Firewall / Listener Findings

```text
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
firewall_changed=false
```

## Phase B Command Set Summary

Phase B must immediately re-confirm all hard gates before state change. If any hard gate fails, stop and report NO-GO.

Exact approval phrase:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

Safe temp-env guard command shape:

```text
python scripts/gateway_smoke_temp_env_guard.py create --output <temp-env-path> --gateway-url http://45.61.48.199:8080
python scripts/gateway_smoke_temp_env_guard.py validate --path <temp-env-path>
python scripts/gateway_smoke_temp_env_guard.py cleanup --path <temp-env-path>
```

The future approved token input must be supplied through stdin only. Do not echo, cat, print, log, or display the token. Validation may emit only masked JSON presence/status fields.

Future helper-bundle strategy:

```text
copy the repo-supported guard, smoke helper, and required module files to an Asterisk temporary path
create the temporary env with the NODE-032L guard using stdin-only token input
validate the temporary env with the NODE-032L guard
source the temporary env for exactly one helper invocation
run scripts/asterisk_gateway_smoke_helper.py with approved smoke audio
cleanup temporary env, helper bundle, and audio
```

Gateway retry sequence after exact approval and clean hard gates:

```text
verify service inactive/disabled unless current state differs and is documented
start service manually only if needed for readiness proof
verify service active and listener 8080 only
run systemctl enable ai-secretary-gateway.service only if service is disabled and retry plan requires re-enablement
reboot Gateway server only if retry plan requires proving autostart again
wait for SSH return
verify service active/enabled after reboot
verify listener 8080 only, no 443, no 8081
verify UFW 8080/tcp remains restricted to 92.118.85.117
verify logs/redaction without printing token values or transcript text
run exactly one Asterisk-side smoke using the safe temp env
verify transcript_text_logged=false
verify transcript_used_for_dialog=false
verify business_dialog_unchanged=true
verify Asterisk OPENAI_API_KEY_ABSENT
cleanup temporary helper/env/audio
```

Rollback:

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

## GO / NO-GO Recommendation

Recommendation: conditional GO for Phase B only after the exact approval phrase is provided and all hard gates are re-confirmed immediately before any state-changing command.

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
technical_readiness=pass
```

Hard NO-GO if Asterisk contains `OPENAI_API_KEY`, business dialog gateway transcript use is enabled, the safe temp-env guard is unavailable or fails local validation, any command would print token values or transcript text, Gateway env is missing or not `root:gateway 640`, masked secret presence fails, the service unit is missing/invalid, unexpected target listeners exist on `443`, `8080`, or `8081`, UFW `8080/tcp` is not source-restricted to `92.118.85.117`, rollback is unclear, or the exact approval phrase is absent.

## Validation

Validation commands:

```text
git status --short
python -m pytest tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032M-phase-a-codex-handoff.md docs/nodes/NODE-032M-controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env.md docs/master/... scripts/... tests/...
git status --short
```

Results are recorded in the Phase A closeout.

## Phase B Closeout

Exact approval phrase was provided:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

Hard gates were re-confirmed before state-changing commands.

Asterisk:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service=active_enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
business_dialog_unchanged=true
```

Gateway:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
service_active_before=inactive
service_enabled_before=disabled
gateway_user_group=present
env_owner_mode=root:gateway 640
masked_secret_presence=pass
workdir_present=true
listener_8080_before=absent
forbidden_listeners_443_8081=absent
ufw_8080_allow=92.118.85.117 only
rollback_tools=available
```

Safe temp-env result:

```text
guard_create=ok_after_one_fail_closed_missing_stdin_attempt
guard_validate=ok
temp_env_mode=600
token_input=stdin_pipeline_only
token_values_printed=false
transcript_text_printed=false
```

The first guard create command was misquoted and supplied no token to stdin; it failed closed with safe JSON only. The corrected command piped the Gateway token directly into guard stdin and printed only masked JSON.

Service enable/reboot proof:

```text
manual_start=ok
service_active_after_start=active
listener_after_start=8080 only
forbidden_listeners_after_start=absent
systemctl_enable=true
service_enabled_after_enable=enabled
gateway_only_reboot=true
ssh_returned=true
post_reboot_service_active=active
post_reboot_service_enabled=enabled
post_reboot_listener=8080 only
post_reboot_forbidden_listeners_443_8081=absent
post_reboot_ufw_8080_allow=92.118.85.117 only
post_reboot_log_sensitive_pattern=absent
```

Controlled smoke result:

```text
controlled_smoke_attempted=true
gateway_request_reached=false
gateway_reachable_from_asterisk=not_run
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=not_run
transcript_present=not_run
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=not_run
```

Blocker:

```text
smoke_blocker=incomplete_temporary_helper_bundle_missing_ai_secretary.config
error_type=ModuleNotFoundError
missing_module=ai_secretary.config
```

The helper failed before any Gateway request because the temporary helper bundle included `src/ai_secretary/__init__.py`, which imports `ai_secretary.config.settings`, but the bundle did not include `ai_secretary.config`. No token values or transcript text were printed.

Rollback and cleanup:

```text
systemctl_disable=true
systemctl_stop=true
final_service_active=inactive
final_service_enabled=disabled
final_target_listeners_443_8080_8081=absent
firewall_changed=false
env_owner_mode=root:gateway 640
temp_env_cleanup_guard=ok
temp_env_removed=true
helper_bundle_removed=true
temp_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
token_rotation_required=false
```

Next recommendation:

```text
NODE-032N / complete-safe-asterisk-helper-bundle-and-retry-plan
```

NODE-032N should fix helper-bundle completeness locally before any future live retry. A later live retry must require a new exact approval phrase, immediate hard-gate re-confirmation, NODE-032L safe temp-env handling, no token output, and no transcript text output.
