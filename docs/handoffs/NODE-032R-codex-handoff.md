# NODE-032R Codex Handoff

This sanitized handoff archives the NODE-032R local decision pass.

NODE-032R evaluates how to resolve the NODE-032Q NO-GO before any future Gateway smoke retry. It does not perform live work.

## Scope Guard

No SSH, live retry, helper copy/deploy, dependency install, service start/stop/restart/reload/enable, `systemctl` action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, PR, or server state change occurred.

This handoff contains no real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts.

Pre-existing local untracked artifacts remain out of scope:

```text
course_submission/
data/storage/
node014-server.tar
```

## Context

NODE-032Q merged via PR #19 at:

```text
8c1848dd11c169ea3d004f16456343a3c593a853
```

NODE-032Q Phase A confirmed all non-dependency gates were ready, but stopped as NO-GO because the Asterisk host is missing the runtime modules required by the temporary helper bundle:

```text
runtime_module_httpx=missing
runtime_module_fastapi=missing
runtime_module_websockets=missing
phase_b_recommendation=NO_GO
```

NODE-032P runtime preflight requires those modules before token handling, temp-env creation, service action, smoke, or Gateway request.

## Local Findings

Inspected:

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

Repo dependency declaration finding:

```text
pyproject_dependencies=python_only
dev_dependencies=pytest_only
httpx_fastapi_websockets_not_declared_in_pyproject=true
```

Helper-bundle preflight finding:

```text
runtime_modules_required=httpx,fastapi,websockets
missing_runtime_modules_fail_closed=true
safe_json_only=true
gateway_token_read=false
token_values_printed=false
transcript_text_logged=false
```

## Options Considered

Option A: controlled dependency install/readiness on Asterisk.

```text
benefit=preserves_existing_helper_evidence_quality
benefit=keeps_gateway_adapter_smoke_path_unchanged
benefit=keeps_runtime_preflight_meaningful
risk=mutates_asterisk_python_runtime
risk=requires_operator_approval_and_rollback_plan
required_controls=separate_live_node, exact_approval, target_env_selection, pinned_versions, package_snapshot, rollback, no_smoke
```

Option B: use an existing Asterisk-side Python environment if one already has the modules.

```text
benefit=may_avoid_install
risk=implicit_coupling_to_unowned_runtime
risk=read_only_probe_has_already_confirmed_missing_modules_in_current_helper_runtime
decision=defer_unless_future_read_only_node_finds_and_approves_a_specific_env
```

Option C: implement an alternate helper that avoids third-party HTTP dependencies.

```text
benefit=may_avoid_dependency_install
risk=requires_new_local implementation_and_tests
risk=may_reduce_evidence_quality_vs_current_adapter_path
risk=must_reprove_redaction_and_fail_closed_boundaries
decision=defer_as_fallback_if_dependency_install_is_rejected
```

Option D: change the smoke boundary.

```text
benefit=may_split_network_reachability_from_full_adapter_smoke
risk=non_asterisk_origin_smoke_does_not_prove_ufw_source_restricted_route
risk=network_only_probe_does_not_prove_openai_realtime_adapter_path
decision=not_a_replacement_for_asterisk_origin_gateway_smoke
```

## Selected Strategy

NODE-032R selects a separate controlled Asterisk runtime dependency install/readiness node before any smoke retry.

Rationale:

- The existing helper path has already proven the desired evidence shape in earlier nodes.
- NODE-032P intentionally made `httpx`, `fastapi`, and `websockets` explicit preflight requirements.
- Installing or selecting the runtime environment is operationally distinct from running a smoke retry.
- Keeping dependency resolution separate avoids combining server mutation with Gateway smoke evidence.

Policy:

```text
dependency_install_in_NODE_032R=false
future_dependency_install_requires_exact_approval=true
future_install_node_runs_no_smoke=true
future_smoke_retry_requires_later_node=true
provider_power_cycle=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
```

## Future Dependency-Resolution Controls

The next live node should:

- Re-confirm Asterisk SSH reachability.
- Re-confirm Asterisk `OPENAI_API_KEY_ABSENT`.
- Re-confirm business dialog Gateway transcript use is disabled.
- Identify the exact target Python runtime or venv for the helper bundle.
- Prefer an isolated temporary/helper-specific venv over mutating system Python.
- Record Python version, venv path, ownership, package list, and rollback target before changes.
- Install only `httpx`, `fastapi`, and `websockets` or pinned compatible versions required by the helper.
- Run dependency preflight only after install/readiness.
- Not run Gateway smoke.
- Not start/stop/restart/reload/enable services.
- Not reboot or provider power-cycle.
- Not change firewall or server env files.
- Not print token values or transcript text.

If dependency installation is rejected, choose a separate local implementation node for an alternate helper strategy before any live retry.

## Next Recommendation

```text
NODE-032S / controlled-asterisk-runtime-dependency-install-readiness
```

Suggested future exact approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

NODE-032S should install or otherwise resolve the Asterisk runtime modules and verify readiness only. It should not run smoke. A later NODE-032T-style retry node should perform the Gateway smoke only after dependency readiness is proven and exact approval is provided.

## Validation

Validation commands for this node:

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
