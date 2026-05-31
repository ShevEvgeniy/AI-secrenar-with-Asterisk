# NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle

Status: Phase B blocked before smoke; cleanup complete

NODE-032O prepares a controlled Gateway smoke retry using both local safety fixes:

```text
NODE-032L safe temp-env guard
NODE-032N complete Asterisk helper bundle manifest/preflight
```

Phase A is read-only readiness plus command planning only. No live retry, service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, or server state change occurred.

Phase B may run only after the exact approval phrase:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

No other phrase is approval.

## Handoff Archive

Long-form sanitized Phase A handoff:

```text
docs/handoffs/NODE-032O-phase-a-codex-handoff.md
```

Long-form sanitized Phase B handoff:

```text
docs/handoffs/NODE-032O-phase-b-codex-handoff.md
```

The handoffs contain no real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Context

NODE-032L added:

```text
scripts/gateway_smoke_temp_env_guard.py
```

Guard behavior:

```text
create_supported=true
validate_supported=true
cleanup_supported=true
token_input=stdin_only
token_values_printed=false
temp_env_mode=0600
safe_json_only=true
cr_lf_and_literal_newline_material_rejected=true
```

NODE-032N added:

```text
scripts/asterisk_gateway_helper_bundle.py
```

Bundle behavior:

```text
manifest_supported=true
create_supported=true
validate_supported=true
includes_smoke_helper=true
includes_temp_env_guard=true
includes_ai_secretary_config=true
includes_required_stt_adapter_modules=true
preflight_catches_missing_ai_secretary_config=true
safe_json_only=true
token_values_printed=false
transcript_text_logged=false
```

NODE-032M proved safe temp-env handling and Gateway enable/reboot/autostart, but smoke stopped before any Gateway request because the temporary helper bundle lacked `ai_secretary.config`. NODE-032N fixed that local bundle completeness blocker. NODE-032O Phase B should therefore retry only the Gateway smoke path, not enable/reboot proof.

## Commands Run

Local setup:

```text
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032o-controlled-gateway-smoke-retry-with-complete-helper-bundle
```

Local inspections:

```text
Get-Content scripts/gateway_smoke_temp_env_guard.py
Get-Content scripts/asterisk_gateway_helper_bundle.py
Get-Content scripts/asterisk_gateway_smoke_helper.py
Get-Content docs/nodes/NODE-032M-controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env.md
Get-Content docs/nodes/NODE-032N-complete-safe-asterisk-helper-bundle-and-retry-plan.md
```

Read-only Asterisk gate:

```text
ssh root@92.118.85.117 '<hostname/uptime, service active/enabled, masked OPENAI_API_KEY absence, business-dialog transcript flag absence>'
```

Read-only Gateway gates:

```text
ssh root@45.61.48.199 '<hostname/uptime, unit verify, service inactive/disabled, gateway account/env masked checks, workdir, listeners, UFW, rollback tool>'
ssh root@45.61.48.199 '<env owner/mode and listener labels only>'
```

No command printed secret values, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Local Guard / Helper-Bundle Findings

Safe temp-env guard command shape:

```text
python scripts/gateway_smoke_temp_env_guard.py create --output <temp-env-path> --gateway-url http://45.61.48.199:8080
python scripts/gateway_smoke_temp_env_guard.py validate --path <temp-env-path>
python scripts/gateway_smoke_temp_env_guard.py cleanup --path <temp-env-path>
```

Gateway token material must be supplied through stdin only for `create`. Do not echo, cat, print, log, or display token values.

Helper bundle command shape:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
python scripts/asterisk_gateway_helper_bundle.py create --output <bundle-root>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <bundle-root>
```

The manifest includes:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/__init__.py
src/ai_secretary/config/__init__.py
src/ai_secretary/config/settings.py
src/ai_secretary/stt/__init__.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
```

## Read-Only Asterisk Findings

```text
ssh_reachable=true
hostname=tula
uptime_observed=true
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog_unchanged=true
```

## Read-Only Gateway Findings

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
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
rollback_systemctl_available=true
```

The first Gateway command had a shell quoting issue around a `stat` format and listener filter. It printed no secret values. A second read-only command confirmed:

```text
gateway_env_stat=root:gateway:640
listener_443=absent
listener_8080=absent
listener_8081=absent
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

Phase B must immediately re-confirm all hard gates before any state-changing command. If any hard gate fails, stop and report NO-GO.

Exact approval phrase:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Gate re-check command groups:

```text
Asterisk: SSH reachability, hostname/uptime, ai-secretary-ari.service active/enabled, process/service OPENAI_API_KEY_ABSENT, business dialog Gateway transcript flag not enabled
Gateway: SSH reachability, unit present/verify OK, service state, gateway:gateway, env root:gateway 640, masked secret presence, workdir, listeners, UFW source restriction, rollback tool availability
```

Helper bundle staging plan:

```text
create local bundle with scripts/asterisk_gateway_helper_bundle.py create --output <local-bundle-root>
validate local bundle with scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local-bundle-root>
only after Phase B approval and hard gates, copy complete bundle to temporary Asterisk path
validate staged bundle before smoke
```

Safe temp-env plan:

```text
create temp env on Asterisk with scripts/gateway_smoke_temp_env_guard.py create --output <temp-env-path> --gateway-url http://45.61.48.199:8080
provide Gateway token through stdin only
validate temp env with scripts/gateway_smoke_temp_env_guard.py validate --path <temp-env-path>
cleanup temp env with scripts/gateway_smoke_temp_env_guard.py cleanup --path <temp-env-path>
```

Service readiness plan:

```text
if ai-secretary-gateway.service remains inactive, start it only after Phase B approval and hard gates
verify service active
verify listener on 8080 only
verify no 443 or 8081
verify UFW still restricts 8080/tcp to 92.118.85.117
verify log/redaction checks without token or transcript text output
```

Smoke plan:

```text
run exactly one Asterisk-side non-business-dialog smoke using the complete helper bundle and safe temp env
verify gateway reachable/auth result
verify OpenAI Realtime result if reached
record HTTP status/chunks/transcript flags if produced
require transcript_text_logged=false
require transcript_used_for_dialog=false
require business_dialog_unchanged=true
require adapter_default_enabled_after_smoke=false
cleanup temporary helper bundle, temp env, and audio
```

Rollback:

```text
stop ai-secretary-gateway.service if Phase B started it and rollback/final state requires stopped
do not systemctl enable
preserve historical Gateway env unless a separate approved change is required
keep firewall unchanged
verify no unexpected listeners
verify Asterisk OPENAI_API_KEY_ABSENT
rotate tokens if any exposure occurs
```

Explicit exclusions:

```text
systemctl_enable=false
reboot=false
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

Phase A recommendation was conditional GO for Phase B only after the exact approval phrase is provided and all hard gates are re-confirmed immediately before any state-changing command.

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
technical_readiness=pass
```

Hard NO-GO if Asterisk contains `OPENAI_API_KEY`, business dialog Gateway transcript use is enabled, safe temp-env guard is unavailable or fails local validation, helper bundle preflight fails, any command would print token values or transcript text, Gateway env is missing or not `root:gateway 640`, masked secret presence fails, the service unit is missing/invalid, unexpected listener exists on `443` or `8081`, UFW `8080/tcp` is not source-restricted to `92.118.85.117`, rollback is unclear, or the exact approval phrase is absent.

## Phase B Blocked Result

Phase B received the exact approval phrase:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Hard gates were re-confirmed before any state-changing command. Asterisk was reachable, `ai-secretary-ari.service` was active/enabled, Asterisk process/service env had `OPENAI_API_KEY_ABSENT`, the business dialog Gateway transcript flag was not enabled, Gateway was reachable, the Gateway unit verified OK, the Gateway service was inactive/disabled, Gateway env remained `root:gateway 640`, masked Gateway secret presence passed, no target listeners existed on `443`, `8080`, or `8081`, and UFW allowed `8080/tcp` only from `92.118.85.117`.

Local helper bundle creation first failed closed when the selected `C:\tmp` output path could not be used. The retry using a workspace-local temporary directory succeeded. Local bundle validation passed with safe JSON only:

```text
required_files_present=true
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The complete bundle was copied to the Asterisk host by using the explicit Windows OpenSSH `scp.exe` path after the shell `scp` shim did not transfer the archive. The validator script was copied separately for remote staged preflight because the bundle manifest intentionally contains the smoke runtime files, not the bundle-builder script.

Remote staged bundle validation failed closed before any token handling, service start, or Gateway request:

```text
remote_bundle_validate_ok=false
required_files_present=true
preflight_import_ok=false
preflight_error_type=ModuleNotFoundError
preflight_missing_module=httpx
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

Result:

```text
phase_b_result=blocked_no_go
safe_temp_env_created=false
gateway_token_read=false
service_started=false
controlled_smoke_run=false
gateway_request_reached=false
openai_realtime_from_gateway=not_run
chunks_sent=not_run
transcript_present=not_run
transcript_text_logged=false
business_dialog_unchanged=true
```

Cleanup completed:

```text
remote_helper_bundle_removed=true
remote_temp_env_removed=true
remote_temp_audio_removed=true
local_helper_bundle_removed=true
local_helper_archive_removed=true
```

Final state:

```text
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
firewall_changed=false
env_files_edited=false
server_state_changed=false
```

No `systemctl enable`, reboot, provider power-cycle, `443`, `8081`, TLS/proxy change, firewall broadening, Asterisk env change, business dialog enablement, token output, transcript text logging, Notion write, Runtime/Evidence update, GitHub push/PR, scheduler, webhook, or automation mode occurred.

Next recommendation:

```text
NODE-032P / helper-bundle-runtime-dependency-preflight-and-retry-plan
```

NODE-032P should make the helper bundle preflight complete for runtime dependencies such as `httpx`, without printing token values or transcript text, before any further live retry.

## Validation

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032O-phase-a-codex-handoff.md docs/nodes/NODE-032O-controlled-gateway-smoke-retry-with-complete-helper-bundle.md docs/master/... scripts/... tests/...
git status --short
```

Phase B validation results:

```text
focused_tests=29 passed
full_pytest=224 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_token_scan=no_real_gateway_token_value_found; safe status-field hits only
final_git_status=docs_only_changes_plus_historical_untracked_artifacts
```
