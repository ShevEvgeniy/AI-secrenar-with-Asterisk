# NODE-032Q / controlled-gateway-smoke-retry-with-runtime-dependency-preflight

NODE-032Q prepares a controlled Gateway smoke retry using all three current safety layers:

- NODE-032L newline-safe, redaction-safe temp-env guard.
- NODE-032N complete Asterisk helper bundle.
- NODE-032P runtime dependency preflight for `httpx`, `fastapi`, and `websockets`.

Phase A is read-only readiness and command planning only. No live retry was run.

## Scope Guard

No dependency install, live retry, live smoke, helper deploy, service start/stop/restart/reload/enable, `systemctl enable`, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, PR, or server state change occurred.

Pre-existing local untracked artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Handoff Archive

```text
docs/handoffs/NODE-032Q-phase-a-codex-handoff.md
```

The handoff contains no real secrets, token values, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Context

NODE-032P merged via PR #18 at:

```text
e2fb600785534ad6df088bbdfb055a82341d92cc
```

NODE-032P added runtime dependency manifest/preflight to `scripts/asterisk_gateway_helper_bundle.py`.

Required runtime modules:

```text
httpx
fastapi
websockets
```

NODE-032O was blocked because remote staged helper-bundle validation on Asterisk failed closed before token handling, service start, smoke, or Gateway request:

```text
preflight_missing_module=httpx
safe_temp_env_created=false
gateway_token_read=false
service_action=false
controlled_smoke_run=false
gateway_request_reached=false
```

NODE-032Q must therefore prove the runtime dependency preflight boundary before any token handling or smoke retry.

## Local Checks

Inspected:

```text
scripts/gateway_smoke_temp_env_guard.py
scripts/asterisk_gateway_helper_bundle.py
scripts/asterisk_gateway_smoke_helper.py
docs/nodes/NODE-032O-controlled-gateway-smoke-retry-with-complete-helper-bundle.md
docs/nodes/NODE-032P-helper-bundle-runtime-dependency-preflight-and-retry-plan.md
docs/handoffs/NODE-032P-codex-handoff.md
```

Safe temp-env guard command shape:

```text
python scripts/gateway_smoke_temp_env_guard.py create --output <temp_env_path> --gateway-url http://45.61.48.199:8080
python scripts/gateway_smoke_temp_env_guard.py validate --path <temp_env_path>
python scripts/gateway_smoke_temp_env_guard.py cleanup --path <temp_env_path>
```

The token must be supplied through stdin only. The guard writes a `0600` temp env, rejects CR/LF and literal newline material, prints safe JSON only, and does not print token values or transcript text.

Helper bundle command shape:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
python scripts/asterisk_gateway_helper_bundle.py create --output <bundle_root>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <bundle_root>
```

Local manifest result:

```text
runtime_modules=httpx,fastapi,websockets
secret_values_printed=false
transcript_text_logged=false
```

Local create/validate result:

```text
create_ok=true
validate_ok=true
required_files_present=true
runtime_modules_required=httpx,fastapi,websockets
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The helper bundle still includes:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/config/__init__.py
src/ai_secretary/config/settings.py
required STT adapter modules
```

No third-party packages are vendored.

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

No secret values were printed.

Runtime dependency read-only probe:

```text
runtime_module_httpx=missing
runtime_module_fastapi=missing
runtime_module_websockets=missing
```

This confirms NODE-032Q Phase B is currently NO-GO unless a separately approved dependency-install or alternate helper strategy node resolves the missing runtime modules first.

## Gateway Read-Only Gates

Server: `45.61.48.199`

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
unit_file_present=true
unit_verify=OK
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user=PRESENT
gateway_group=PRESENT
gateway_env_present=true
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
gateway_workdir_present=true
target_listeners_443_8080_8081=NONE
ufw_status=active
ufw_default_incoming=deny
ufw_8080_source=ASTERISK_ONLY
ufw_8080_broad=ABSENT
rollback_commands=AVAILABLE
```

No env values were printed.

## Phase B Approval Phrase

Exact future approval phrase:

```text
APPROVE NODE-032Q RUNTIME-PREFLIGHT SMOKE RETRY
```

Any other phrase is not approval.

## Phase B Command Set Summary

Phase B must begin with immediate hard-gate re-confirmation.

Gate re-check command groups:

- Asterisk: SSH reachability, hostname/uptime, `ai-secretary-ari.service` active/enabled, process/service/env-file `OPENAI_API_KEY_ABSENT`, business dialog Gateway transcript flag not enabled.
- Gateway: SSH reachability, unit present/verified, service inactive/disabled or documented current state, `gateway:gateway`, env present with `root:gateway 640`, masked secret presence, workdir, no unexpected listeners, UFW source restriction, rollback command availability.

Helper bundle and runtime preflight:

```text
python scripts/asterisk_gateway_helper_bundle.py create --output <local_bundle_root>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_bundle_root>
scp/ssh stage <local_bundle_root> to Asterisk only after approval and gates
python <remote_bundle>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_bundle>
```

Hard rule:

```text
if missing_runtime_modules contains httpx, fastapi, or websockets:
  stop as NO-GO
  do not install dependencies in NODE-032Q
```

Safe temp-env handling:

```text
<token_from_secure_operator_input> | python <remote_bundle>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
python <remote_bundle>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
python <remote_bundle>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

The token must never be echoed, printed, logged, or committed.

Smoke boundary:

- Start/check Gateway service readiness for the smoke only if gates pass and the service remains inactive.
- Do not run `systemctl enable`.
- Do not reboot.
- Verify listener `8080` only, no `443` or `8081`.
- Verify UFW remains restricted to `92.118.85.117`.
- Verify logs/redaction without printing secrets or transcript text.
- Run exactly one Asterisk-side non-business-dialog smoke only after runtime preflight and temp-env validation pass.
- Clean up temporary helper bundle, temp env, and audio.
- Preserve rollback path: stop/disable service if needed, preserve historical Gateway env unless separately approved, keep firewall unchanged, verify no unexpected listeners, verify Asterisk has no `OPENAI_API_KEY`.

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

Hard NO-GO if:

- Asterisk contains `OPENAI_API_KEY`.
- Business dialog Gateway transcript use is enabled.
- Runtime dependency preflight fails.
- Safe temp-env guard is unavailable or fails validation.
- Helper bundle preflight fails.
- Any command would print token values.
- Any command would print transcript text.
- Gateway env is missing or not `root:gateway 640`.
- Masked Gateway secret presence fails.
- Service unit is missing or invalid.
- Unexpected listener exists on `443` or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Exact approval phrase is absent.

## Validation Commands

Planned Phase A validation:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032Q-phase-a-codex-handoff.md docs/nodes/NODE-032Q-controlled-gateway-smoke-retry-with-runtime-dependency-preflight.md docs/master scripts tests
git status --short
```

Known full-suite environmental failures, if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

## Next Step

```text
NODE-032R / controlled-asterisk-runtime-dependency-resolution-or-alternate-helper-strategy
```

Do not proceed with NODE-032Q Phase B while Asterisk lacks `httpx`, `fastapi`, and `websockets`. Dependency installation remains out of scope for NODE-032Q and needs separate approval.
