# NODE-032N / complete-safe-asterisk-helper-bundle-and-retry-plan

## Scope

NODE-032N is a local repo implementation and documentation node. It fixes the NODE-032M helper-bundle completeness blocker before any future live Gateway smoke retry.

No SSH, live retry, live smoke, service start/stop/restart/reload/enable, `systemctl` action, reboot, provider power-cycle, firewall change, server env edit, server state change, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation mode, GitHub push, or PR occurred during this node.

## Context

NODE-032M merged via PR #15 / merge commit `d67ced76412d80e7fc8753a6efecf88889dd009b`.

NODE-032M proved the safe temp-env path and Gateway service enable/reboot/autostart path, but the controlled smoke did not complete. Exactly one Asterisk-side helper invocation was attempted and failed before any Gateway request with:

```text
error_type=ModuleNotFoundError
missing_module=ai_secretary.config
gateway_request_reached=false
```

Cause:

```text
temporary helper bundle included src/ai_secretary/__init__.py
src/ai_secretary/__init__.py imports ai_secretary.config.settings
temporary helper bundle did not include ai_secretary.config
```

Gateway auth, OpenAI Realtime, chunks, and transcript flags did not run in NODE-032M. Rollback completed, leaving `ai-secretary-gateway.service` installed but inactive/disabled, no target listeners on `443`, `8080`, or `8081`, firewall unchanged, Gateway env `root:gateway 640`, temporary helper/env/audio removed, and Asterisk with `OPENAI_API_KEY_ABSENT`.

## Design Decision

Selected fix:

```text
add an explicit minimal helper-bundle manifest plus local preflight validator
```

New helper:

```text
scripts/asterisk_gateway_helper_bundle.py
```

The helper supports:

```text
manifest
create --output <bundle-root>
validate --bundle-root <bundle-root>
```

The bundle manifest includes the manual smoke helper, NODE-032L safe temp-env guard, and the minimal package files needed for import completeness:

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

The smallest safe fix is to include `ai_secretary.config` rather than modifying package import behavior. This keeps the future live helper path aligned with repo imports and catches missing package files locally before any server copy or smoke attempt.

## Safety Behavior

Bundle validation:

```text
required_files_present=<true|false>
preflight_import_ok=<true|false>
preflight_error_type=<safe class only>
preflight_missing_module=<module name only>
secret_pattern_hits=<relative file paths only>
secret_values_printed=false
transcript_text_logged=false
```

Secret hygiene:

- The bundle helper does not read Gateway token material.
- The bundle helper does not print token values.
- The bundle helper scans bundle text for secret-like assignment/header patterns.
- The NODE-032L temp-env guard remains the required token-handling path for future retry.
- Asterisk-side `OPENAI_API_KEY` refusal remains in `scripts/asterisk_gateway_smoke_helper.py`.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remains required.
- Transcript text logging remains disabled by default and explicitly refused when enabled.

## Local Validation Commands

```powershell
python -m pytest tests/test_asterisk_gateway_helper_bundle.py
python -m pytest tests/test_gateway_smoke_temp_env_guard.py tests/test_asterisk_gateway_helper_bundle.py tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032N-codex-handoff.md docs/nodes/NODE-032N-complete-safe-asterisk-helper-bundle-and-retry-plan.md docs/master/... scripts/... tests/...
git status --short
```

Expected full-suite environmental failures remain:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

## Future Retry Boundary

NODE-032N does not authorize a live retry.

Future retry must occur only in a separately approved live node and must:

- re-confirm Asterisk and Gateway hard gates immediately before state change;
- use `scripts/gateway_smoke_temp_env_guard.py` for temp env create/validate/cleanup;
- supply Gateway token material through stdin only;
- use the complete helper bundle manifest from `scripts/asterisk_gateway_helper_bundle.py`;
- run local or server-side bundle validation before the helper invocation;
- run at most one Asterisk-side non-business-dialog smoke;
- never print token values or transcript text;
- keep business dialog transcript use disabled;
- clean up temporary helper/env/audio.

## Next Recommendation

```text
NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle
```

NODE-032O should use the NODE-032L safe temp-env guard and NODE-032N complete helper bundle. It must require a new exact approval phrase, immediate hard-gate re-confirmation, and explicit rollback/cleanup. Provider power-cycle, business dialog enablement, TLS/proxy, `443`, `8081`, token output, transcript text logging, and firewall broadening remain out of scope unless separately approved.

