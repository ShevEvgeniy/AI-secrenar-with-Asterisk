# NODE-032P / helper-bundle-runtime-dependency-preflight-and-retry-plan

Status: local implementation and documentation complete

NODE-032P fixes the NODE-032O blocker by adding explicit runtime dependency preflight to the temporary Asterisk helper bundle validator. This is not a live retry node.

No SSH, live smoke, service start/stop/restart/reload/enable, `systemctl` action, reboot, provider power-cycle, firewall change, server env edit, dependency installation on servers, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, PR, or server state change occurred.

## Handoff Archive

Long-form sanitized handoff:

```text
docs/handoffs/NODE-032P-codex-handoff.md
```

The handoff contains no real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## NODE-032O Blocker

NODE-032O Phase B reached remote staged helper-bundle validation and failed closed before smoke:

```text
error_type=ModuleNotFoundError
missing_module=httpx
safe_temp_env_created=false
gateway_token_read=false
service_started=false
controlled_smoke_run=false
gateway_request_reached=false
```

The Gateway token was not read, piped, printed, or validated. The Gateway service was not started. No Gateway request was reached.

## Implementation Decision

Selected strategy:

```text
runtime_dependency_manifest=true
runtime_dependency_preflight=true
vendor_third_party_packages=false
server_dependency_install=false
```

`scripts/asterisk_gateway_helper_bundle.py` now exposes required third-party runtime modules in the manifest and validates them during `validate`.

Runtime modules:

```text
httpx
fastapi
websockets
```

Reasoning:

```text
src/ai_secretary/stt/gateway_adapter.py imports httpx
src/ai_secretary/stt/gateway_adapter.py imports realtime_gateway, which imports fastapi
src/ai_secretary/stt/realtime_measurement.py imports httpx and websockets
```

The bundle helper does not vendor third-party packages. If a future Asterisk host lacks a required runtime dependency, the retry must stop or open a separate approved dependency-install node.

## Runtime Dependency Preflight Behavior

`manifest` now includes:

```text
runtime_modules=[httpx, fastapi, websockets]
```

`validate` now reports:

```text
runtime_modules_required=[httpx, fastapi, websockets]
runtime_modules_ok=<true_or_false>
missing_runtime_modules=<module_names_only>
preflight_import_ok=<true_or_false>
secret_values_printed=false
transcript_text_logged=false
```

Failure policy:

```text
missing_runtime_dependency=fail_closed
safe_json_only=true
gateway_token_read=false
token_values_printed=false
transcript_text_printed=false
smoke_allowed=false
```

The runtime preflight runs before the project import preflight. If a required runtime module is missing, validation fails before future temp-env creation, token handling, service start, or Gateway request.

## Tests Added / Updated

Updated:

```text
tests/test_asterisk_gateway_helper_bundle.py
```

Coverage:

```text
runtime dependency manifest includes httpx
runtime dependency manifest includes fastapi and websockets
complete bundle validation reports runtime_modules_ok=true
missing httpx fails closed
missing httpx is reported by module name only
missing ai_secretary.config is still caught
safe temp-env guard remains in bundle manifest
reports do not print token values
reports do not print transcript text
```

Existing safety boundaries remain:

```text
Asterisk-side OPENAI_API_KEY refusal remains in scripts/asterisk_gateway_smoke_helper.py
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false remains required
NODE-032L safe temp-env guard remains required for token material
```

## Local Validation Findings

Command:

```text
python scripts/asterisk_gateway_helper_bundle.py manifest
```

Sanitized result:

```text
ok=true
runtime_modules=[httpx, fastapi, websockets]
secret_values_printed=false
transcript_text_logged=false
```

Command:

```text
python scripts/asterisk_gateway_helper_bundle.py create --output <workspace-temp-bundle>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <workspace-temp-bundle>
```

Sanitized result:

```text
ok=true
required_files_present=true
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The temporary local validation bundle was removed after use.

## Retry Boundary

NODE-032P does not run or authorize a live retry.

Future retry requirements:

```text
exact approval required
immediate hard-gate re-confirmation required
local helper bundle create/validate required
remote staged helper bundle validate required before token handling
NODE-032L safe temp-env guard required
Gateway token supplied through stdin only
no token output
no transcript text output
cleanup temporary helper/env/audio
```

Hard NO-GO for future retry:

```text
missing_runtime_modules is non-empty
helper bundle project preflight fails
token value would be printed
transcript text would be printed
business dialog transcript use would be enabled
rollback/cleanup unclear
```

## Next Recommendation

```text
NODE-032Q / controlled-gateway-smoke-retry-with-runtime-dependency-preflight
```

If NODE-032Q remote preflight finds dependencies missing on Asterisk, it must stop or hand off to a separately approved dependency-install node. Do not install dependencies as part of NODE-032Q unless explicitly scoped.

## Validation

Validation commands:

```text
python -m pytest tests/test_asterisk_gateway_helper_bundle.py
python -m pytest tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_helper_bundle.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032P-codex-handoff.md docs/nodes/NODE-032P-helper-bundle-runtime-dependency-preflight-and-retry-plan.md docs/master/... scripts/asterisk_gateway_helper_bundle.py tests/test_asterisk_gateway_helper_bundle.py
git status --short
```

Results are recorded in the NODE-032P closeout report.
