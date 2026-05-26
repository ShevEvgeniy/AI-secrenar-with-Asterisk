# NODE-032F / prepare-asterisk-side-gateway-smoke-helper-or-approved-smoke-path

## Summary

NODE-032F prepares a repo-supported Asterisk-side gateway smoke helper/path for a future controlled live node. It does not deploy to servers, does not SSH into servers, does not run live smoke, and does not change live state.

Selected path:

```text
scripts/asterisk_gateway_smoke_helper.py
```

The script is a manual-only Asterisk-side wrapper around the existing, tested:

```text
python -m ai_secretary.stt.gateway_adapter_smoke
```

It exists to make the future live command explicit and to close the NODE-032E blocker where the deployed Asterisk path did not contain an approved helper/path.

## Baseline

- NODE-032E merged via PR #7 / merge commit `2b88c26`.
- NODE-032E recorded exact approval phrase `APPROVE NODE-032E LIVE APPLY/SMOKE`.
- NODE-032E re-confirmed live gates and stopped before any state-changing command.
- NODE-032E blocker: no safe Asterisk-side smoke helper/path was identified on the deployed Asterisk host.
- Running smoke from a non-Asterisk source would not prove the source-restricted `8080/tcp` path from `92.118.85.117` to `45.61.48.199:8080`.

## Local Inspection

Commands run:

```text
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032f-prepare-asterisk-side-gateway-smoke-helper-or-approved-smoke-path
rg --files
rg -n "gateway|realtime|smoke|stt|transcript_text_logged|business_dialog" src tests deploy docs -g "*.py" -g "*.md" -g "*.example"
Get-Content src\ai_secretary\stt\gateway_adapter_smoke.py
Get-Content src\ai_secretary\stt\gateway_adapter.py
Get-Content tests\test_gateway_stt_adapter.py
```

Findings:

- Existing `src/ai_secretary/stt/gateway_adapter_smoke.py` is a manual one-off helper for the disabled-by-default gateway adapter.
- Existing tests already verify local fake gateway behavior, explicit flags, secret redaction, transcript redaction, and no dialog transcript use during smoke.
- Existing helper was safe enough to reuse as the core smoke engine, but the live node needs a clear Asterisk-side operator script path and stricter non-business-dialog gating.

## Implementation

Added:

```text
scripts/asterisk_gateway_smoke_helper.py
tests/test_asterisk_gateway_smoke_helper.py
```

Updated:

```text
src/ai_secretary/stt/gateway_adapter_smoke.py
```

The wrapper:

- is manual-only;
- has no autostart, cron, systemd, timer, webhook, or scheduler behavior;
- validates runtime environment before delegation;
- requires gateway URL and gateway token via runtime env only;
- refuses to run if `OPENAI_API_KEY` exists on Asterisk;
- requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`;
- requires transcript logging to remain disabled;
- prints only safe status/errors and never prints secret values;
- delegates to `gateway_adapter_smoke` with `--require-explicit-flags`.

The existing smoke report now also includes safe invariant flags:

```text
helper_manual_only=true
persistent_server_state_created=false
autostart_configured=false
business_dialog_unchanged=true
```

## Why This Proves Asterisk To Gateway

The future live node must run the wrapper from the Asterisk host after the approved helper/path is present there. Because the command originates on `92.118.85.117`, an authenticated request to:

```text
http://45.61.48.199:8080
```

will prove the source-restricted firewall path from Asterisk to Gateway. A non-Asterisk operator workstation cannot prove that boundary.

## Required Runtime Env

The future live node may set these only in a one-off process environment or explicitly approved temporary secure runtime file:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_URL=http://45.61.48.199:8080
STT_GATEWAY_TOKEN=<gateway-token-from-secure-runtime>
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_LOG_TRANSCRIPT=false
```

Allowed compatibility names:

```text
STT_GATEWAY_ADAPTER_ENABLED=true
REALTIME_GATEWAY_URL=http://45.61.48.199:8080
REALTIME_GATEWAY_TOKEN=<gateway-token-from-secure-runtime>
```

Forbidden on Asterisk:

```text
OPENAI_API_KEY
```

## Future Live Command Shape

Placeholder-only command shape for `NODE-032G`:

```text
cd /home/tulauser/AI-secrenar-with-Asterisk-node014
export STT_GATEWAY_STT_ENABLED=true
export STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
export STT_GATEWAY_URL=http://45.61.48.199:8080
export STT_GATEWAY_TOKEN=<gateway-token-from-secure-runtime>
export STT_GATEWAY_TIMEOUT_MS=10000
export STT_GATEWAY_LOG_TRANSCRIPT=false
unset OPENAI_API_KEY
python scripts/asterisk_gateway_smoke_helper.py --audio <approved-non-sensitive-smoke-wav>
unset STT_GATEWAY_STT_ENABLED STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG STT_GATEWAY_URL STT_GATEWAY_TOKEN STT_GATEWAY_TIMEOUT_MS STT_GATEWAY_LOG_TRANSCRIPT REALTIME_GATEWAY_URL REALTIME_GATEWAY_TOKEN
```

The command must run from the Asterisk host. It must not be run from a developer workstation for boundary proof.

## Secret Handling

- `OPENAI_API_KEY` remains gateway-only.
- The Asterisk helper may use only gateway URL/token runtime material.
- Token values must not be committed, logged, pasted into docs, or printed in chat.
- If a token is exposed, rotate it before any further smoke.
- The helper validation reports only missing/safe flags and never prints env values.

## Redaction Behavior

- Transcript text is never printed by the wrapper.
- The core smoke helper redacts secrets and transcript text in report details/events.
- The report may include safe flags and metrics such as:
  - `gateway_reachable_from_asterisk`;
  - `gateway_auth`;
  - `openai_realtime_from_gateway`;
  - `chunks_sent`;
  - `transcript_present`;
  - `transcript_text_logged=false`;
  - `business_dialog_unchanged=true`.

## Power-Cycle Safety

- No service is installed.
- No autostart is configured.
- No timer, cron, webhook, scheduler, or automation loop is configured.
- No persistent server state is created by the helper.
- No shell-history secret dependency is required; `NODE-032G` should use secure operator injection and clear env afterward.
- After reboot or power-on, no smoke starts automatically.
- Business dialog remains unchanged after reboot/power-on.

## Business Dialog Boundary

- The wrapper requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- It does not import, start, or modify the business dialog flow.
- The smoke may exercise the adapter request path but must not use transcript text to drive dialog.
- Gateway STT remains disabled by default outside the one-off smoke process.

## Validation

Focused tests:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_gateway_stt_adapter.py
```

Result:

```text
17 passed
```

Full validation result is recorded in the closeout report. Known pre-existing environmental failures remain unrelated to NODE-032F if the full suite reports `208 passed, 6 failed`:

- missing `src/scripts/make_demo_audio.py`;
- missing `sentence_transformers`.

## Next Recommended Node

```text
NODE-032G / controlled-gateway-live-smoke-with-asterisk-side-helper
```

`NODE-032G` should deploy or make available the approved Asterisk-side helper/path only under explicit scope, re-confirm all live gates, start/apply only if approved, run one controlled non-business-dialog smoke from Asterisk, keep transcript text redacted, then stop/rollback unless persistent service state is explicitly approved.

## Closeout Boundaries

- No live deploy was performed.
- No SSH was performed.
- No server state changed.
- No service was installed, started, stopped, restarted, or reloaded.
- No firewall changes were made.
- No server env files were edited.
- No Asterisk restart occurred.
- No live call or live smoke was run.
- No business dialog enablement occurred.
- No Notion write occurred.
- No Runtime/Evidence create or update occurred.
- No GitHub write occurred.
- No scheduler, webhook, timer, cron, or automation mode was added.
- No real secrets or tokens were committed, logged, or printed.
