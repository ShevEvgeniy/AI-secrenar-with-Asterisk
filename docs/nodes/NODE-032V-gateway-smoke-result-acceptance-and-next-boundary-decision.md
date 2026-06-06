# NODE-032V / gateway-smoke-result-acceptance-and-next-boundary-decision

Status: local repo/docs decision node.

Branch:

```text
feat/node-032v-gateway-smoke-result-acceptance-and-next-boundary-decision
```

Handoff archive:

```text
docs/handoffs/NODE-032V-codex-handoff.md
```

## Goal

Decide how to accept the NODE-032U Gateway smoke result and choose the next safe boundary.

This node performs no live action. It does not contact servers, run smoke, deploy helpers, handle tokens, create temp env files on servers, change services, install dependencies, reboot, change firewall/env state, enable business dialog, log transcript text, write Notion, update Runtime/Evidence, create a scheduler, create a webhook, or create an automation loop.

## Input Result From NODE-032U

NODE-032U merged via PR #23:

```text
merge_commit=84421ce3295464315bd745ce000784e78274b194
```

NODE-032U Phase B ran a controlled Asterisk-origin smoke with repo-created and repo-validated `24000 Hz mono 16-bit PCM WAV` audio.

Recorded result:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

Recorded final state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
gateway_env_meta=root:gateway:640
firewall=unchanged_source_restricted_to_92.118.85.117
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
token_values_printed=false
transcript_text_printed=false
```

## Acceptance Classification

NODE-032U is accepted as successful controlled Gateway transport/auth/OpenAI Realtime smoke with valid 24 kHz audio.

This means NODE-032U proves:

- the Asterisk-origin helper path can reach the Gateway;
- Gateway auth succeeds without exposing token values;
- the Gateway returns HTTP 200 for a valid `24000 Hz mono 16-bit PCM WAV` input;
- the Gateway reaches OpenAI Realtime and creates a session;
- audio chunks are sent (`chunks_sent=5`);
- transcript text remains unlogged;
- transcript is not used for dialog;
- business dialog remains unchanged;
- the adapter default remains disabled after smoke;
- cleanup/rollback leaves the Gateway service inactive/disabled with no target listeners.

NODE-032U does not prove:

- transcript-present success;
- transcript quality;
- transcript text correctness;
- business-dialog transcript integration;
- production service autostart;
- reboot or power-cycle persistence;
- dual-channel caller/bot separation;
- long-running operational reliability.

The helper reported `accepted=false` because `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remained enforced. That is expected for this non-business-dialog smoke and is not treated as transport/auth failure.

## Options Considered

### 1. Accept NODE-032U As Final Transport/Auth/OpenAI Realtime Smoke

Selected for the transport boundary.

Reasons:

- Gateway HTTP status was `200`.
- Gateway auth was OK.
- OpenAI Realtime from Gateway was OK.
- `chunks_sent=5`.
- No token values or transcript text were exposed.
- Final state was safe.

Limit:

- This does not close transcript-presence or transcript-quality acceptance because `transcript_present=false`.

### 2. Run Controlled Transcript-Presence Smoke Next

Selected as the next boundary.

Reasons:

- NODE-032U resolved the invalid-audio blocker but still recorded `transcript_present=false`.
- The next proof can target transcript event/presence flags only.
- Transcript text can remain redacted.
- Business-dialog transcript use can remain disabled.
- This keeps smoke retry and business-dialog integration separate.

### 3. Move Directly To Business-Dialog Integration Design

Rejected as next.

Reasons:

- Transcript-present behavior should be proven before dialog integration design is allowed to lean on Gateway STT.
- Enabling `transcript_used_for_dialog` too early would raise rollback and business-contract risk.
- Business dialog integration must remain separately scoped.

### 4. Production Persistence Or Autostart

Deferred.

Reasons:

- The Gateway service is installed but inactive/disabled.
- Autostart is operationally useful, but it is not the immediate blocker for accepting the STT evidence chain.
- Enabling autostart before transcript/business-dialog acceptance may be premature.

### 5. Dual-Channel Recording Or Caller/Bot Separation

Deferred.

Reasons:

- It may be useful for analytics and evaluation.
- It is an architecture decision outside the current Gateway STT acceptance chain.
- It should not be smuggled into a transcript-presence smoke node.

## Selected Next Boundary

```text
NODE-032W / controlled-gateway-transcript-presence-smoke
```

Purpose:

Run one controlled Asterisk-side Gateway smoke to prove transcript event/presence behavior without enabling business-dialog transcript use and without logging transcript text.

Expected NODE-032W acceptance target:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent>0
transcript_event_or_presence_confirmed=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
final_state_safe=true
```

NODE-032W should not:

- enable business-dialog transcript use;
- log transcript text;
- print token values;
- broaden firewall;
- enable Gateway service autostart;
- introduce TLS/proxy, `443`, or `8081`;
- introduce dual-channel recording architecture.

## Safety Boundaries

Future live work must keep these constraints:

- no Asterisk-side `OPENAI_API_KEY`;
- Gateway token handled only through approved safe temp-env handling;
- token values never printed;
- transcript text never printed or logged;
- business dialog unchanged;
- transcript used for dialog remains false;
- temporary helper/env/audio cleaned after smoke;
- Gateway service final state explicitly documented.

## Validation

To close this node locally:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032V-codex-handoff.md docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md docs/master
git status --short
```

Validation result:

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_scan=no_real_secret_values_found; status-field/placeholders only
```
