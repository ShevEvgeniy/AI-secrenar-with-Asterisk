# NODE-027 Controlled Gateway Adapter Live Smoke With Explicit Temporary Flags

## Status

CLOSED as blocked live smoke with a safe one-off adapter smoke helper added.

NODE-027 attempted to run one controlled live smoke of the NODE-025 gateway STT adapter against the Kamatera USA gateway using explicit temporary flags. The live adapter smoke was not completed because SSH access to the Kamatera gateway host refused connections on port 22, so the temporary gateway listener could not be started.

The node does not fake success. Production gateway STT remains disabled by default, `ai-secretary-ari.service` was not changed, Asterisk runtime env was not changed, and `OPENAI_API_KEY` remains absent from the Asterisk process environment.

## Goal

Run exactly one controlled live smoke of the Asterisk-side gateway STT adapter:

```text
one-off WAV artifact -> NODE-025 gateway adapter -> Kamatera gateway -> OpenAI Realtime -> redacted adapter result
```

Required safety boundaries:

- Do not enable production gateway STT by default.
- Do not change `ai-secretary-ari.service`.
- Do not persist temporary Asterisk runtime env changes.
- Do not place `OPENAI_API_KEY` on Asterisk.
- Do not commit real gateway tokens or other secrets.
- Do not log transcript text by default.
- Do not change business dialog behavior, NODE-016 diagnostic isolation, NODE-014 RTP topology, or PHONE / PHONE_CONFIRM / CITY / transfer / callback / after-hours / SAFE_FINISH contracts.

## Implementation

Added a small one-off adapter smoke helper:

```text
src/ai_secretary/stt/gateway_adapter_smoke.py
```

The helper:

- Is inert unless run manually.
- Reads the existing NODE-025 env flags.
- Requires explicit flags when `--require-explicit-flags` is used.
- Refuses explicit smoke mode if `OPENAI_API_KEY` is present on the Asterisk side.
- Calls `transcribe_via_gateway(...)`, exercising the NODE-025 adapter path rather than the older NODE-021 measurement client.
- Emits only redacted JSON metadata.
- Does not print gateway token, transcript text, or OpenAI key.
- Reports `chunks_sent`, `gateway_auth`, `openai_realtime_from_gateway`, transcript presence, fallback reason, and whether transcript text was logged.
- Leaves default config unchanged: `config_from_env({}).enabled == false`.

Focused tests were added in:

```text
tests/test_gateway_stt_adapter.py
```

## Intended Smoke Command

The intended Asterisk-side one-off command shape was:

```bash
cd /home/tulauser/AI-secrenar-with-Asterisk-node014
export STT_GATEWAY_STT_ENABLED=true
export STT_GATEWAY_ADAPTER_ENABLED=true
export STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
export STT_GATEWAY_URL=http://45.61.48.199:8080/v1/stt/realtime-measurement
export STT_GATEWAY_TOKEN=<redacted gateway token from safe secret source>
export STT_GATEWAY_TIMEOUT_MS=10000
export STT_GATEWAY_MAX_RETRIES=0
export STT_GATEWAY_LOG_TRANSCRIPT=false
export STT_GATEWAY_LANGUAGE=ru
unset OPENAI_API_KEY
PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio /tmp/ai-secretary-node027/realtime_measurement_24k.wav \
  --require-explicit-flags
```

`STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` is required by the current NODE-025 adapter to make the adapter perform the gateway request. In this node it was intended only for a one-off CLI process, not the running ARI service or a live business call.

## Live Work Attempted

Local branch and untracked artifact boundary:

```text
branch=feat/node-027-controlled-gateway-adapter-live-smoke-with-explicit-temporary-flags
untracked_artifacts_left_uncommitted=data/storage/, node014-server.tar
```

Kamatera gateway SSH check:

```text
ssh root@45.61.48.199 "hostname; ss -ltnp | grep ':8080' || true; test -f /etc/ai-secretary/openai-realtime-gateway.env && echo env_exists"
```

Result:

```text
ssh_to_gateway=false
blocker=Connection refused on 45.61.48.199:22 before authentication
```

Asterisk service check:

```text
ssh tulauser@92.118.85.117 hostname
ssh tulauser@92.118.85.117 systemctl is-active ai-secretary-ari
```

Result:

```text
hostname=tula
ai-secretary-ari.service=active
```

Asterisk process env check:

```text
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Asterisk-to-gateway reachability check:

```text
curl --max-time 5 http://45.61.48.199:8080/v1/stt/realtime-measurement
```

Result:

```text
gateway_http_status=000
curl_error=Failed to connect to 45.61.48.199 port 8080
```

## Smoke Result

```text
gateway_started=false
gateway_reachable_from_asterisk=false
adapter_enabled_temporarily=false
adapter_default_enabled_after_smoke=false
adapter_smoke_exercised_node025_path=false
openai_realtime_from_gateway=not_run
gateway_auth=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=gateway_not_started
error_type=kamatera_ssh_connection_refused
error_status=not_available
error_redacted=true
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_after_smoke=not_verified_by_ssh_port_8080_unreachable
live_call_run=false
real_secrets_committed=false
```

Interpretation:

- The Kamatera gateway could not be started for this node because SSH to the gateway host was unavailable.
- The Asterisk server could not reach port 8080 because the gateway listener was not running.
- The NODE-025 adapter live path was not exercised against Kamatera/OpenAI in this node.
- No service restart, env-file edit, or live call was performed.
- Cleanup requirements were preserved because no gateway process was started and no temporary service/runtime changes were applied.

## Validation

Focused helper validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
12 passed
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
111 passed
```

Pre-commit whitespace validation:

```text
git diff --check
passed
```

## NODE-027 Result

```text
node_status=blocked live smoke closed
small_smoke_helper_added=true
docs_only=false
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed=false
live_server_changed=false
kamatera_gateway_started=false
kamatera_gateway_stopped_after_smoke=not_started_by_node_port_8080_unreachable
asterisk_service_changed=false
asterisk_runtime_env_changed=false
openai_key_on_asterisk_after_smoke=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_used_for_dialog=false
transcript_text_logged=false
live_call_run=false
real_secrets_committed=false
next_node_recommendation=restore gateway SSH/start listener, then rerun the one-off helper smoke
```

## Known Limitations

- NODE-027 does not prove live adapter-to-gateway behavior because the gateway host could not be reached over SSH and the listener was not running.
- The new helper is locally validated with fake gateway tests only in this node.
- No live call was run, by design.
- No persistent gateway service exists from earlier nodes; manual gateway startup remains required unless a later node adds a hardened gateway service.

## Next Recommendation

Open a follow-up node only after gateway host access is restored:

```text
NODE-028 / rerun controlled gateway adapter live smoke after gateway SSH recovery
```

Recommended scope:

- Restore or document the Kamatera SSH access path.
- Start the gateway temporarily from `/etc/ai-secretary/openai-realtime-gateway.env`.
- Run the new one-off adapter smoke helper from Asterisk with explicit temporary env flags.
- Stop the gateway listener after the smoke.
- Keep production gateway STT disabled by default.
