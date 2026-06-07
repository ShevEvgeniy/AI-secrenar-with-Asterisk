# NODE-032AA Codex Handoff

## Node

```text
NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
```

Branch:

```text
feat/node-032aa-gateway-event-diagnostics-propagation-gap-fix
```

Base:

```text
master_head=ce3814cf6ad500b6236a6e63b4d00bdb196fe8b6
latest_closed_node=NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

## Scope

NODE-032AA is local/repo-only. It did not run live smoke, SSH, helper deploy, token handling, server temp env creation, service action, dependency install, reboot, provider power-cycle, firewall/env/server change, business-dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation.

## NODE-032Z Problem

NODE-032Z proved Gateway transport/auth/OpenAI Realtime again:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

But the redacted diagnostic report showed a propagation gap:

```text
openai_event_type_counts={}
openai_event_type_counts_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

## Local Cause

The report path could distinguish `openai_event_type_counts` being present as a dictionary from missing diagnostics, but it did not expose a safe explicit availability marker. That made empty event counts and missing event-count diagnostics hard to reason about in live closeouts when `openai_event_type_counts_present=false`.

NODE-032AA adds a safe marker:

```text
openai_event_type_counts_available=true|false
```

This marker means the event-count field propagated through the Gateway/adapter/smoke-report path, even when the dictionary is intentionally empty.

## Implementation

Changed local code:

```text
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/gateway_adapter_smoke.py
```

Behavior after fix:

```text
openai_event_type_counts_available=true when Gateway diagnostics include the event-count field
diagnostic_propagation_gap=false when openai_event_type_counts={} is present and marked available
diagnostic_propagation_gap=true when diagnostics are missing/not propagated
transcript_text remains stripped from smoke reports when transcript logging is disabled
```

Docs updated:

```text
docs/stt_gateway_protocol.md
docs/nodes/NODE-032AA-gateway-event-diagnostics-propagation-gap-fix.md
docs/master/MASTER_STATUS.md
docs/master/MASTER_PLAN.md
docs/master/DECISIONS.md
docs/master/NODE_REGISTRY.md
docs/master/RUNTIME_NOTES.md
```

Tests updated:

```text
tests/test_realtime_gateway.py
tests/test_gateway_stt_adapter.py
```

Synthetic tests only; no real tokens, transcript text, raw env output, logs, audio, or binary artifacts were added.

## Validation Summary

Focused validation:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py
result=28 passed
```

Required focused validation:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
result=50 passed
```

Full suite:

```text
python -m pytest
result=234 passed, 6 failed
known_environmental_failure_1=missing src/scripts/make_demo_audio.py
known_environmental_failure_2=missing sentence_transformers
```

Diff and safety:

```text
git_diff_check=pass
source_runtime_diff=intended source/test files only
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status/test fixtures only
scoped_source_docs_tests_scan=no_real_secret_values_found; placeholders/status/synthetic fixtures only
transcript_delta_scan=no_transcript_text_added; policy labels and existing synthetic event-type fixtures only
audio_binary_artifacts_added=false
```

## Next Recommendation

```text
NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix
```

NODE-032AB should be a separate controlled live node only after exact approval and immediate hard-gate re-confirmation. It should run one Asterisk-side non-business-dialog smoke and verify `openai_event_type_counts_available` plus the existing redacted diagnostic fields without logging transcript text or enabling business-dialog transcript use.
