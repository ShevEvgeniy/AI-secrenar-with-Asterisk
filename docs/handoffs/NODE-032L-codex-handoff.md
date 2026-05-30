# NODE-032L Codex Handoff

This handoff archives NODE-032L in sanitized form.

Do not include real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, large logs, audio, or binary artifacts in this file.

## Node

```text
NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
```

## Scope

Local implementation and documentation only. No SSH, live smoke, service action, systemctl action, reboot, provider power-cycle, firewall change, server env edit, Asterisk env change, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

## Implementation

Added:

```text
scripts/gateway_smoke_temp_env_guard.py
tests/test_gateway_smoke_temp_env_guard.py
```

Updated:

```text
scripts/asterisk_gateway_smoke_helper.py
tests/test_asterisk_gateway_smoke_helper.py
```

The new guard reads a gateway token from stdin, rejects missing or malformed secret material, atomically writes a temporary env file with mode `0600`, validates the env shape without printing values, and cleans it up.

Safe output contains only status flags:

```text
secret_values_printed=false
transcript_text_logged=false
token_present_masked=true
```

The Asterisk smoke helper also rejects gateway URL/token env values containing CR/LF or literal newline material before delegating to the adapter smoke helper.

## Future Retry Use

Future live retry should use the guard in the temporary helper bundle:

```text
create -> validate -> source env for one approved smoke -> cleanup
```

The future retry must not use ad hoc shell string assembly for the temp env and must not print env values.

## Validation

Focused local validation:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
```

Result:

```text
24 passed
```

Full suite expected environmental result:

```text
219 passed, 6 failed
```

Known environmental failures:

- missing `src/scripts/make_demo_audio.py`;
- missing `sentence_transformers`.

## Next Node

```text
NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
```

NODE-032M remains a future live node and requires exact approval plus immediate hard-gate re-confirmation.
