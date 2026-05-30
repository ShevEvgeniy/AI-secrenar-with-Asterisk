# NODE-032N Codex Handoff

## Boundary

NODE-032N is local repo implementation and documentation only.

No SSH, live retry, live smoke, service action, `systemctl` action, reboot, provider power-cycle, firewall change, server env edit, server state change, business dialog enablement, token output, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, automation mode, GitHub push, or PR occurred.

This handoff intentionally contains no real secrets, token values, private keys, raw secret env output, logs, audio, binary artifacts, or transcript text.

## Problem From NODE-032M

NODE-032M reached Gateway service enable/reboot/autostart verification but the controlled smoke did not complete.

Safe summary:

```text
controlled_smoke_attempted=true
gateway_request_reached=false
error_type=ModuleNotFoundError
missing_module=ai_secretary.config
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=not_run
transcript_present=not_run
```

Cause:

```text
temporary helper bundle included src/ai_secretary/__init__.py
src/ai_secretary/__init__.py imports ai_secretary.config.settings
temporary helper bundle did not include ai_secretary.config
```

## Implementation

Added:

```text
scripts/asterisk_gateway_helper_bundle.py
tests/test_asterisk_gateway_helper_bundle.py
```

The helper provides:

```text
manifest
create --output <bundle-root>
validate --bundle-root <bundle-root>
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

Validation output is safe JSON only:

```text
required_files_present=<true|false>
preflight_import_ok=<true|false>
preflight_error_type=<safe class only>
preflight_missing_module=<module name only>
secret_pattern_hits=<relative file paths only>
secret_values_printed=false
transcript_text_logged=false
```

## Tests

New tests cover:

- complete bundle includes `ai_secretary.config`;
- preflight validates complete bundle imports;
- missing `ai_secretary.config` is caught before live retry;
- bundle reports do not print token values;
- NODE-032L safe temp-env guard remains part of the required bundle.

Existing tests continue to cover:

- Asterisk-side `OPENAI_API_KEY` refusal;
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` requirement;
- no transcript text logging;
- newline-safe temp-env guard behavior.

## Future Retry Boundary

NODE-032N does not run a live retry and does not authorize one.

Future retry should be:

```text
NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle
```

NODE-032O must use the NODE-032L safe temp-env guard and the NODE-032N complete helper bundle manifest, then run at most one controlled Asterisk-side non-business-dialog smoke after exact approval and immediate hard-gate re-confirmation.

No token values or transcript text may be printed or recorded.

