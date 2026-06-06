# NODE-032Y Codex Handoff

## Scope

Node:

```text
NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

Branch:

```text
feat/node-032y-safe-transcript-event-diagnostics-with-redacted-event-counts
```

This node is local/repo-only diagnostics hardening. It does not run a live smoke and does not touch servers.

## Preserved Context

NODE-032W remains accepted only as Gateway transport/auth/OpenAI Realtime success:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

NODE-032X selected this node because the next safe step is to remove ambiguity from redacted transcript-event diagnostics before another live smoke.

## Implementation Summary

Gateway diagnostics now expose safe, redacted fields:

```text
openai_event_type_counts
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
diagnostic_propagation_gap
diagnostic_classification
```

Supported safe classifications:

```text
no_event_counts_available
no_transcript_event_observed
transcript_event_observed_empty_or_no_text
transcript_bearing_event_observed_text_redacted
timeout_after_audio_commit
openai_error_event_observed
diagnostic_propagation_gap
unknown
```

Transcript text remains suppressed. The adapter redacts payloads and converts any transcript text content into safe booleans and buckets only. The Asterisk-side smoke report now preserves missing diagnostic propagation as an explicit gap instead of leaving transcript-event fields ambiguous.

## Files Changed

```text
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
tests/test_realtime_gateway.py
tests/test_gateway_stt_adapter.py
docs/handoffs/NODE-032Y-safe-transcript-event-diagnostics-with-redacted-event-counts-codex-handoff.md
docs/nodes/NODE-032Y-safe-transcript-event-diagnostics-with-redacted-event-counts.md
docs/master/MASTER_STATUS.md
docs/master/MASTER_PLAN.md
docs/master/DECISIONS.md
docs/master/NODE_REGISTRY.md
docs/master/RUNTIME_NOTES.md
```

## Safety Boundary

No live systems were touched:

```text
live_smoke=false
ssh=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_env_server_change=false
business_dialog_enablement=false
transcript_text_logging=false
audio_artifact_commit=false
```

No real token values, private keys, transcript text, raw secret env output, large logs, audio, or binary artifacts are included in this handoff.

## Validation

Required validation for closeout:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
tracked secret scan
scoped docs/source/tests token and transcript-text scan
```

Known full-suite environmental failures may include:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

## Next Recommended Node

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

Purpose: run one controlled Asterisk-side non-business-dialog smoke after exact approval, then classify the transcript-event result using the new safe diagnostics without logging transcript text or using transcript text for dialog.
