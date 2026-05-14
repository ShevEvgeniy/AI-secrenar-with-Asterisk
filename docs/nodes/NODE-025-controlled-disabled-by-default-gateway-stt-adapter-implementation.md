# NODE-025 Controlled Disabled-By-Default Gateway STT Adapter Implementation

## Status

CLOSED as implementation.

NODE-025 implements an Asterisk-side gateway STT adapter at the transcript-source boundary before `apply_turn(...)`. The path is controlled by disabled-by-default flags, falls back safely, does not require `OPENAI_API_KEY` on the Asterisk side, and does not change production behavior by default.

## Goal

Implement the NODE-024 boundary design without enabling gateway STT in production/business dialog by default.

Preserved:

- NODE-014 `snoop_external_media_rtp` topology.
- NODE-016 diagnostic isolation.
- Existing PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, and Russian-only caller-facing contracts.
- Gateway-only `OPENAI_API_KEY`.
- Transcript text redaction by default.

## Implementation

Changed files:

```text
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/telephony/ari_app.py
tests/test_gateway_stt_adapter.py
deploy/examples/systemd/ari-app.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
docs/master/NODE_REGISTRY.md
docs/master/MASTER_STATUS.md
docs/master/MASTER_PLAN.md
docs/master/DECISIONS.md
docs/master/RUNTIME_NOTES.md
docs/nodes/NODE-025-controlled-disabled-by-default-gateway-stt-adapter-implementation.md
```

Adapter behavior:

- `transcribe_via_gateway(...)` returns a transcript candidate plus redacted metadata.
- The adapter is inert unless `STT_GATEWAY_STT_ENABLED=true` or `STT_GATEWAY_ADAPTER_ENABLED=true`.
- Dialog use also requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true`.
- Missing URL/token, auth failure, timeout, unavailable gateway, malformed response, empty transcript, and low-confidence transcript all return a safe non-accepted result.
- `ari_app.py` calls the adapter only when enabled and before the existing streaming/batch artifact transcription path.
- If the adapter rejects or fails, the existing batch STT fallback path is used.
- If disabled, no gateway network call is attempted and no gateway event is emitted in the business path.
- Transcript text is returned to the caller in memory only when accepted for dialog, but adapter events/details omit transcript text unless `STT_GATEWAY_LOG_TRANSCRIPT=true`.

## Config

Safe defaults:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_URL=
STT_GATEWAY_TOKEN=
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_MAX_RETRIES=0
STT_GATEWAY_LOG_TRANSCRIPT=false
STT_GATEWAY_LANGUAGE=ru
STT_GATEWAY_MIN_CONFIDENCE=
```

Compatibility aliases:

```text
REALTIME_GATEWAY_URL
REALTIME_GATEWAY_TOKEN
```

The Asterisk-side adapter does not read or require `OPENAI_API_KEY`.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py
22 passed
```

Business dialog validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_dialog_flow.py
45 passed
```

Transcription integration validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_transcription_integrity.py
38 passed
```

Pre-commit validation:

```text
git diff --check
passed
```

## NODE-025 Result

```text
node_status=implementation closed
gateway_stt_adapter_implemented=true
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed_by_default=false
systemd_profile_changed=false
live_server_changed=false
openai_key_on_asterisk_required=false
gateway_secret_committed=false
transcript_text_logged_by_default=false
tests_added_or_updated=true
next_node_recommendation=NODE-026 controlled local adapter smoke / dry-run validation
```

## Operational Notes

- No live servers were modified.
- Kamatera gateway was not started.
- No live calls were run.
- `ai-secretary-ari.service` was not changed.
- Asterisk runtime env was not changed.
- `OPENAI_API_KEY` remains gateway-only.
- No real gateway token, root password, SSH private key, or `.env` secret was committed.
- `data/storage/` and `node014-server.tar` remain untracked artifacts and are not part of this node.

## Known Limitations

- The adapter uses the existing short WAV artifact upload shape; it is not yet a production streaming relay.
- Gateway transcript quality acceptance is intentionally conservative and minimal in NODE-025; richer stage-specific scoring should be accepted only after dry-run evidence.
- Production enablement, real gateway process management, TLS/systemd hardening, and live-call validation remain out of scope.

## Next Recommendation

Open:

```text
NODE-026 / controlled local adapter smoke / dry-run validation
```

Recommended scope:

- Run a controlled local/mock gateway dry-run with gateway STT flags explicitly enabled outside production.
- Confirm accepted and rejected transcript candidates through the full `ari_app` boundary without live-server changes.
- Keep production gateway STT disabled until a later explicit enablement node.
