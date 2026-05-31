# NODE-032R / controlled-asterisk-runtime-dependency-resolution-or-alternate-helper-strategy

Status: local docs-only decision complete

NODE-032R decides how to resolve the NODE-032Q runtime dependency NO-GO before any future Gateway smoke retry.

This is not a live retry node.

## Scope Guard

No SSH, live retry, helper copy/deploy, dependency install, service start/stop/restart/reload/enable, `systemctl` action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, PR, or server state change occurred.

Pre-existing local untracked artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Handoff Archive

```text
docs/handoffs/NODE-032R-codex-handoff.md
```

The handoff contains no real secrets, token values, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

## Context

NODE-032Q merged via PR #19 at:

```text
8c1848dd11c169ea3d004f16456343a3c593a853
```

NODE-032Q Phase A confirmed the Gateway smoke retry remains blocked because the Asterisk helper runtime is missing:

```text
httpx
fastapi
websockets
```

NODE-032P made those modules explicit runtime preflight requirements for the helper bundle. Missing modules fail closed before project import, token handling, temp-env creation, service action, smoke, or Gateway request.

## Local Findings

Inspected local docs and tooling:

```text
docs/nodes/NODE-032Q-controlled-gateway-smoke-retry-with-runtime-dependency-preflight.md
docs/handoffs/NODE-032Q-phase-a-codex-handoff.md
docs/nodes/NODE-032P-helper-bundle-runtime-dependency-preflight-and-retry-plan.md
scripts/asterisk_gateway_helper_bundle.py
scripts/gateway_smoke_temp_env_guard.py
scripts/asterisk_gateway_smoke_helper.py
tests/test_asterisk_gateway_helper_bundle.py
pyproject.toml
```

Current local package declaration:

```text
pyproject_declares_httpx=false
pyproject_declares_fastapi=false
pyproject_declares_websockets=false
```

The helper-bundle runtime manifest remains:

```text
runtime_modules_required=httpx,fastapi,websockets
runtime_modules_preflight_required=true
missing_runtime_modules_fail_closed=true
safe_json_only=true
gateway_token_read=false
token_values_printed=false
transcript_text_logged=false
```

## Options Considered

### Option A: Controlled Dependency Install / Readiness

Resolve the missing Asterisk runtime modules in a separate approved live node.

Controls required:

```text
exact_approval_required=true
target_python_runtime_identified=true
prefer_isolated_helper_venv=true
pre_change_python_and_package_snapshot=true
pinned_or_explicit_versions=true
rollback_plan_required=true
smoke_retry_in_same_node=false
```

Advantages:

- Preserves the current helper-bundle and adapter smoke path.
- Keeps evidence comparable to earlier Gateway smoke nodes.
- Keeps NODE-032L temp-env guard and NODE-032P runtime preflight intact.

Risks:

- Mutates Asterisk runtime state.
- Requires careful target venv selection and rollback.
- Must not touch Asterisk business dialog behavior or add `OPENAI_API_KEY`.

### Option B: Existing Asterisk-Side Python Environment

Use an already-present venv only if future read-only inspection finds one with the required modules.

Decision:

```text
selected=false
reason=current_probe_missing_modules_in_helper_runtime
future_allowed_if_specific_env_is_read_only_verified_and_approved=true
```

Risk:

- Hidden coupling to an unowned runtime can make the smoke path fragile.

### Option C: Alternate Helper Without Third-Party HTTP Dependencies

Build a different Asterisk-origin helper using stdlib or shell/curl mechanics.

Decision:

```text
selected=false
deferred_as_fallback=true
```

Reason:

- This would require local implementation and tests before live retry.
- It may reduce parity with the existing adapter smoke path and evidence quality.

### Option D: Different Smoke Boundary

Split the retry into a network-only proof or a non-Asterisk-origin check.

Decision:

```text
selected=false
```

Reason:

- A non-Asterisk-origin smoke does not prove the UFW source-restricted route from `92.118.85.117`.
- A network-only probe does not prove the OpenAI Realtime adapter path.

## Selected Strategy

Selected path:

```text
controlled_asterisk_runtime_dependency_install_readiness
```

NODE-032R chooses a separate controlled live dependency-install/readiness node before any smoke retry.

The dependency node must be limited to resolving Asterisk runtime readiness. It must not run smoke, start or enable Gateway service, reboot, change firewall, edit server env files, enable business dialog behavior, print tokens, or print transcript text.

The later Gateway smoke retry should happen only after dependency readiness is proven and a separate exact approval phrase is provided.

## Future Dependency-Resolution Plan

Required future gates:

- Asterisk SSH reachable.
- Asterisk `OPENAI_API_KEY_ABSENT` in process/service/env-file checks.
- Business dialog Gateway transcript use disabled.
- Current Python runtime and venv candidates identified.
- Chosen target runtime recorded before mutation.
- Existing package list captured before mutation.
- Rollback commands accepted.
- No helper copy/deploy or Gateway smoke until dependency readiness is proven.

Install policy:

```text
dependency_install_allowed_only_after_exact_approval=true
packages=httpx,fastapi,websockets
prefer_isolated_helper_venv=true
system_python_mutation=avoid_if_possible
server_env_edit=false
asterisk_openai_api_key=false
business_dialog_enablement=false
smoke_retry=false
```

If the operator does not approve dependency installation, choose a separate local node to design and test an alternate helper strategy.

## Next Node Recommendation

```text
NODE-032S / controlled-asterisk-runtime-dependency-install-readiness
```

Suggested future exact approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

NODE-032S should verify or install the required Asterisk runtime dependencies and stop. It should not run the Gateway smoke retry.

## Blockers Remaining

```text
asterisk_runtime_modules_missing=httpx,fastapi,websockets
dependency_install_not_yet_approved=true
gateway_smoke_retry_blocked=true
next_node_exact_approval_absent=true
```

## Validation

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032R-codex-handoff.md docs/nodes/NODE-032R-controlled-asterisk-runtime-dependency-resolution-or-alternate-helper-strategy.md docs/master
git status --short
```

Known full-suite environmental failures, if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```
