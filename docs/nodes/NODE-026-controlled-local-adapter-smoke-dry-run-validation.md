# NODE-026 Controlled Local Adapter Smoke Dry-Run Validation

## Status

CLOSED as local dry-run smoke.

NODE-026 validates the NODE-025 gateway STT adapter through local tests and a localhost fake gateway only. It does not enable production gateway STT, does not modify live servers, does not use the Kamatera gateway, and does not require real secrets.

## Goal

Prove adapter wiring and safety behavior without enabling production gateway STT or touching live infrastructure.

Preserved:

- Production gateway STT disabled by default.
- Dialog-driving gateway transcript use disabled by default.
- Existing business dialog behavior unchanged by default.
- NODE-014 RTP topology unchanged.
- NODE-016 diagnostic isolation unchanged.
- PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, and Russian-only caller-facing contracts unchanged.
- Asterisk-side `OPENAI_API_KEY` not required.
- Transcript text not logged by default.

## Dry-Run Method

The dry-run is a pytest-based local smoke with mocks and a localhost-only fake HTTP gateway:

- `tests/test_gateway_stt_adapter.py` uses injected fake `post(...)` callables for failure and redaction cases.
- `_FakeGatewayServer` binds to `127.0.0.1` on an ephemeral port and accepts only a fake bearer token.
- The fake gateway returns local JSON responses, including a fake transcript for explicit positive-path validation.
- No Kamatera host, OpenAI endpoint, Asterisk server, live call, SSH session, systemd service, or real gateway token is used.

Exact validation command:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
```

Pre-commit whitespace validation:

```text
git diff --check
```

## Implementation

Changed files:

```text
tests/test_gateway_stt_adapter.py
docs/master/NODE_REGISTRY.md
docs/master/MASTER_STATUS.md
docs/master/MASTER_PLAN.md
docs/master/DECISIONS.md
docs/master/RUNTIME_NOTES.md
docs/nodes/NODE-026-controlled-local-adapter-smoke-dry-run-validation.md
```

Added validation coverage:

- Disabled config remains inert and makes no gateway call.
- Enabled adapter with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` does not send a gateway request and falls back to batch STT at the ARI boundary.
- Enabled local dry-run config reads gateway URL/token from the env abstraction.
- Local fake gateway auth success returns `transcript_text_present=true`.
- Accepted fake transcript can drive the transcript-source boundary only when both gateway and dialog-use flags are explicitly enabled.
- Empty transcript, malformed response, timeout, unavailable gateway, and auth failure fall back safely.
- Transcript text is not present in adapter events or ARI events by default.
- `OPENAI_API_KEY` is absent during dry-run tests and is not required.
- Only fake gateway tokens are used.

## Validation

Focused NODE-026 smoke:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
9 passed
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
```

Result:

```text
108 passed
```

Pre-commit validation:

```text
git diff --check
passed
```

## NODE-026 Result

```text
node_status=local dry-run smoke closed
gateway_stt_adapter_dry_run_validated=true
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed_by_default=false
live_server_changed=false
kamatera_gateway_started=false
live_calls_run=false
openai_key_required_for_dry_run=false
real_gateway_token_required_for_dry_run=false
transcript_text_logged_by_default=false
dry_run_method=pytest fake/mocked gateway plus localhost-only fake HTTP gateway
tests_added_or_updated=true
next_node_recommendation=NODE-027 controlled gateway adapter live smoke with explicit temporary flags
```

## Operational Notes

- Live servers were not modified.
- No SSH was used for Kamatera or Asterisk.
- Kamatera gateway was not started.
- No live calls were run.
- `ai-secretary-ari.service` was not changed.
- Asterisk runtime env was not changed.
- No `OPENAI_API_KEY` was placed on Asterisk.
- No real gateway token was used.
- No real secrets were committed.
- `data/storage/` and `node014-server.tar` remain untracked artifacts and are not part of this node.

## Known Limitations

- This node proves local adapter wiring and fallback behavior only; it does not prove live gateway quality or caller-perceived latency.
- The positive transcript path uses a fake local transcript and fake token.
- Production gateway STT enablement, live gateway process management, TLS/systemd hardening, and live-call validation remain out of scope.

## Next Recommendation

Open:

```text
NODE-027 / controlled gateway adapter live smoke with explicit temporary flags
```

Recommended scope:

- Use explicit temporary runtime flags only for the smoke.
- Keep `OPENAI_API_KEY` gateway-only.
- Use a real supported-region gateway only after it is intentionally started and scoped for the node.
- Preserve rollback to the disabled-by-default NODE-025/NODE-026 profile.
