# NODE-032V Codex Handoff

NODE-032V is a local repo/docs decision node. No SSH, live smoke retry, helper deploy, token handling, temp env creation, service action, dependency install, reboot, provider power-cycle, firewall/env/server change, business-dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, automation, push, or PR occurred.

## Context

NODE-032U merged via PR #23 at merge commit:

```text
84421ce3295464315bd745ce000784e78274b194
```

NODE-032U resolved the NODE-032T invalid-audio blocker by requiring repo-created or repo-validated smoke audio before any Gateway request.

NODE-032U Phase B result:

```text
audio_format=24000 Hz mono 16-bit PCM WAV
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
token_values_printed=false
transcript_text_printed=false
```

Final NODE-032U server state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
gateway_env_meta=root:gateway:640
firewall=unchanged_source_restricted_to_92.118.85.117
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
```

## Acceptance Decision

Accept NODE-032U as successful controlled Gateway transport/auth/OpenAI Realtime smoke with valid 24 kHz audio.

Do not accept NODE-032U as:

- transcript-quality success;
- transcript-present success;
- transcript text correctness proof;
- business-dialog integration proof;
- production autostart proof;
- dual-channel caller/bot separation proof.

The `accepted=false` helper field is not treated as a transport failure in NODE-032U because `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remained enforced. That setting correctly kept transcript content from driving business dialog.

## Options Considered

1. Accept NODE-032U as final Gateway transport/auth/OpenAI Realtime smoke for this chain.

Accepted for the transport/auth/OpenAI Realtime boundary because Gateway HTTP 200, Gateway auth OK, OpenAI Realtime OK, `chunks_sent=5`, no token/transcript exposure, and safe rollback were recorded.

2. Run controlled transcript-presence smoke next.

Selected as the next boundary because NODE-032U still recorded `transcript_present=false`. The next proof should verify transcript event/presence behavior without enabling business-dialog transcript use and without logging transcript text.

3. Move directly to business-dialog integration design.

Deferred. Business-dialog integration should not begin until transcript-present behavior is accepted separately and rollback/redaction gates are preserved.

4. Production persistence/autostart.

Deferred. The Gateway service is installed but inactive/disabled. Autostart is operationally useful, but it is not the immediate acceptance blocker for this STT chain.

5. Dual-channel recording/caller-bot separation.

Deferred. It is useful for analytics/evaluation, but it is a separate architecture node rather than the next Gateway STT acceptance boundary.

## Selected Next Boundary

```text
NODE-032W / controlled-gateway-transcript-presence-smoke
```

NODE-032W should run one controlled Asterisk-side Gateway smoke to prove transcript event/presence behavior without enabling business-dialog transcript use and without logging transcript text.

Potential NODE-032W acceptance target:

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

## Safety Boundaries

- No token values may be printed, stored, committed, or logged.
- No transcript text may be printed, stored, committed, or logged.
- Business-dialog transcript use must remain disabled.
- Gateway service start/stop, helper deploy, token handling, temp env creation, and smoke execution require a separate approved live node.
- Production autostart and business-dialog integration remain separate boundaries.

## Validation Plan

NODE-032V validation is local only:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032V-codex-handoff.md docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md docs/master
git status --short
```

## Validation Result

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_scan=no_real_secret_values_found; status-field/placeholders only
```
