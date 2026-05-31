# NODE-032P Codex Handoff

This archive records the sanitized handoff for `NODE-032P / helper-bundle-runtime-dependency-preflight-and-retry-plan`.

It excludes real secrets, token values, bearer headers, private keys, raw env output, transcript text, large logs, audio, and binary artifacts.

## Context

NODE-032O was blocked before smoke because remote staged helper-bundle validation failed closed:

```text
error_type=ModuleNotFoundError
missing_module=httpx
gateway_token_read=false
safe_temp_env_created=false
service_started=false
controlled_smoke_run=false
gateway_request_reached=false
```

NODE-032O confirmed the safe temp-env guard and complete project-file bundle were available, but the remote preflight did not separately check third-party runtime modules before importing bundled project code.

## Implementation Decision

Selected strategy:

```text
runtime_dependency_manifest=true
runtime_dependency_preflight=true
vendor_third_party_packages=false
server_dependency_install=false
live_retry=false
```

`scripts/asterisk_gateway_helper_bundle.py` now reports required runtime modules before project import preflight:

```text
httpx
fastapi
websockets
```

Why these modules:

```text
gateway_adapter imports httpx
gateway_adapter imports realtime_gateway, which imports fastapi
realtime_measurement imports httpx and websockets
```

The helper bundle still includes only the minimal repo files needed for the Asterisk-side smoke helper and safe temp-env guard. It does not vendor third-party dependency code.

## Safe Preflight Behavior

The validate command now reports:

```text
runtime_modules_required=[httpx, fastapi, websockets]
runtime_modules_ok=<true_or_false>
missing_runtime_modules=<safe_module_names_only>
preflight_import_ok=<true_or_false>
secret_values_printed=false
transcript_text_logged=false
```

If a runtime dependency is missing, validation fails closed before smoke and before temp-env token handling:

```text
ok=false
errors includes runtime dependencies missing
preflight_import_ok=false
preflight_missing_module=<missing_module_name>
```

The report contains module names only. It never reads Gateway token material and never prints token values or transcript text.

## Local Validation

Local helper-bundle manifest output includes:

```text
runtime_modules=[httpx, fastapi, websockets]
```

Local create/validate against a workspace temporary bundle passed:

```text
required_files_present=true
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The temporary local validation bundle was removed after use.

## Future Retry Boundary

NODE-032P does not authorize a live retry. A future live retry must:

```text
re-confirm hard gates
create and validate helper bundle locally
copy temporary helper bundle only after approval
run remote staged validation before token handling
stop if missing_runtime_modules is non-empty
use NODE-032L safe temp-env guard for token material
run at most one approved non-business-dialog smoke
cleanup temporary helper/env/audio
```

If future remote preflight finds missing runtime modules on Asterisk, the retry must stop or move dependency installation into a separately approved node. Do not install dependencies inside the retry node unless explicitly scoped.

## Next Recommendation

```text
NODE-032Q / controlled-gateway-smoke-retry-with-runtime-dependency-preflight
```

NODE-032Q may retry only after exact approval and immediate hard-gate re-confirmation. It must not print token values or transcript text.

## Safety Confirmations

```text
live_retry=false
ssh=false
server_state_changed=false
service_action=false
systemctl_action=false
reboot=false
provider_power_cycle=false
firewall_changed=false
server_env_edited=false
server_dependency_install=false
business_dialog_enablement=false
token_values_printed=false
transcript_text_printed=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation_added=false
```
