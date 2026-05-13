# NODE-023 Deploy Kamatera USA Gateway And Run Live Measurement

## Status

CLOSED as live supported-region gateway smoke passed.

The NODE-021 measurement gateway was deployed on the Kamatera USA / New York 2 host, the Asterisk server reached it over HTTP, gateway auth worked, OpenAI Realtime was reached from the gateway, and the Asterisk-side one-off measurement returned a redacted structured success result.

## Goal

Deploy the NODE-021 FastAPI realtime measurement gateway on the Kamatera USA host, keep `OPENAI_API_KEY` only on the gateway, run exactly one one-off realtime STT measurement from the Asterisk server through the gateway, and record the redacted result.

This node does not:

- Change normal business dialog.
- Change `ai-secretary-ari.service`.
- Put `OPENAI_API_KEY` on the Asterisk server.
- Enable gateway STT for production calls.
- Change PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, Russian-only caller-facing behavior, NODE-016 diagnostic isolation, or NODE-014 RTP topology.

## Repository Inspection

Base state:

```text
34f055e Record NODE-022 gateway deployment smoke blocker
```

Current branch:

```text
feat/node-023-deploy-kamatera-usa-gateway-and-run-live-measurement
```

NODE-021/NODE-022 implementation inspected:

```text
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
tests/test_realtime_gateway.py
tests/test_realtime_measurement.py
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
docs/stt_gateway_protocol.md
docs/nodes/NODE-021-supported-region-gateway-minimal-realtime-measurement.md
docs/nodes/NODE-022-deploy-supported-region-gateway-and-run-live-measurement.md
```

Confirmed:

- Gateway endpoint is `POST /v1/stt/realtime-measurement`.
- Gateway reads `OPENAI_API_KEY` from gateway runtime environment only.
- Gateway requires `Authorization: Bearer <gateway token>`.
- Asterisk-side gateway mode uses gateway URL/token and does not require `OPENAI_API_KEY`.
- Gateway returns redacted structured JSON and does not return transcript text by default.
- Gateway/client modules do not import business dialog code.

Untracked forbidden artifacts observed locally and left untouched:

```text
data/storage/
node014-server.tar
```

## Gateway Host

Gateway host:

```text
provider=Kamatera
region=USA / New York 2
public_ip=45.61.48.199
hostname=ai-secretary-gateway-node023
os=Ubuntu 24.04.4 LTS
deploy_path=/opt/ai-secretary-gateway
gateway_port=8080
gateway_protocol=HTTP for smoke
```

Runtime secret path on the gateway host:

```text
/etc/ai-secretary/openai-realtime-gateway.env
```

Validated secret-file boundary:

```text
mode=0600
owner=root
group=root
OPENAI_API_KEY=<redacted>
GATEWAY_TOKEN=<redacted>
```

Only required gateway runtime packages were installed:

```text
python3-venv
python3-pip
ca-certificates
fastapi
uvicorn
httpx
websockets
```

Gateway source was deployed from tracked repository content only. Local untracked artifacts were not copied.

Manual smoke command shape:

```bash
cd /opt/ai-secretary-gateway
set -a
. /etc/ai-secretary/openai-realtime-gateway.env
set +a
export GATEWAY_REGION_LABEL=kamatera-us-ny2
export GATEWAY_PORT=8080
PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
```

The gateway listened locally on:

```text
0.0.0.0:8080
```

## Asterisk Server

Asterisk server:

```text
server=92.118.85.117
deployment_path=/home/tulauser/AI-secrenar-with-Asterisk-node014
systemd_service=ai-secretary-ari.service
```

Runtime profile verified before and after measurement:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

Asterisk measurement shell verified:

```text
asterisk_server_openai_key_present=no
```

The existing deployment tree did not include the NODE-021 gateway CLI flags, so the one-off measurement used a temporary copy of current tracked source at:

```text
/tmp/ai-secretary-node023-client
```

This did not change `ai-secretary-ari.service`, did not restart production runtime, and did not enable gateway STT in business dialog.

Measurement audio was created outside git:

```text
/tmp/ai-secretary-node023/realtime_measurement_24k.wav
```

## Reachability

Gateway host local auth check:

```text
POST http://127.0.0.1:8080/v1/stt/realtime-measurement without bearer token -> 401
```

Asterisk-to-gateway route check:

```text
GET http://45.61.48.199:8080/v1/stt/realtime-measurement -> 405
```

The `405` confirms the Asterisk server reached the FastAPI route over HTTP before the one-off POST measurement.

## Live Measurement Result

Asterisk-side one-off gateway-mode command used only:

```text
gateway_url=http://45.61.48.199:8080/v1/stt/realtime-measurement
gateway_token=<redacted>
```

Raw redacted client events:

```json
{"action":"gateway_measurement_request","details":{"audio_bytes":57644,"gateway_url":"45.61.48.199:8080/v1/stt/realtime-measurement","language":"ru"},"status":"start"}
{"action":"gateway_measurement_response","details":{"response":{"audio_send_started":true,"chunks_sent":6,"cleanup_done":true,"error_code":null,"error_message_redacted":null,"error_type":null,"final_ms":2232,"first_delta_ms":null,"gateway_connection_attempt":true,"gateway_region":"kamatera-us-ny2","gateway_request_id":"gw_cb0ba8f000d9","model":"gpt-realtime-whisper","ok":true,"openai_realtime_connection_ok":true,"openai_session_created":true,"transcript_text_present":false},"status_code":200},"status":"ok"}
```

Structured redacted result:

```json
{
  "gateway_reachable": true,
  "gateway_auth": "ok",
  "openai_realtime_from_gateway": "ok",
  "asterisk_server_openai_key_present": "no",
  "chunks_sent": 6,
  "transcript_present": false,
  "transcript_text_logged": false,
  "error_type": null,
  "error_status": null,
  "error_redacted": true,
  "business_dialog_changed": false,
  "systemd_profile_changed": false,
  "gateway_host": "Kamatera USA / New York 2",
  "gateway_public_ip": "45.61.48.199",
  "gateway_protocol": "HTTP for smoke",
  "gateway_port": 8080
}
```

Interpretation:

- The Asterisk server reached the Kamatera gateway.
- Gateway auth passed; the measurement did not return `401`.
- The gateway connected to OpenAI Realtime and created a transcription session.
- Audio upload started and 6 chunks were sent.
- OpenAI returned a final response in `2232 ms`.
- The synthetic measurement tone did not produce transcript text, so `transcript_present=false`.
- Transcript text was not requested, returned, or logged.
- No error was reported.

## Gateway Process Conclusion

The gateway process was stopped after the one-off smoke:

```text
gateway_listener_stopped=yes
```

Reason:

- The smoke gateway was exposed over plain HTTP on a public IP.
- Public scanners hit `/` and `/login` during the test window.
- NODE-023 required only one one-off measurement and did not request a persistent service.

Deployed code and host-only secrets remain in place:

```text
/opt/ai-secretary-gateway
/etc/ai-secretary/openai-realtime-gateway.env
```

No systemd gateway service was installed.

## Validation

Required focused tests:

```text
pytest tests/test_realtime_measurement.py tests/test_realtime_gateway.py
```

Result:

```text
16 passed in 0.59s
```

Required hygiene:

```text
git diff --check
git status --short
git diff --cached
git diff
```

Result:

```text
git diff --check passed
```

Secret/artifact rules preserved:

- `OPENAI_API_KEY` was not committed.
- Real `GATEWAY_TOKEN` was not committed.
- Root password was not committed.
- SSH private keys were not committed.
- `.env` files with real secrets were not committed.
- `data/storage/` was not committed.
- `node014-server.tar` was not committed.

## Runtime Boundary

Preserved:

- Business dialog unchanged.
- `ai-secretary-ari.service` unchanged.
- Gateway STT not enabled in production dialog.
- Asterisk server remains in NODE-016/NODE-018 diagnostic-safe profile.
- OpenAI key remains gateway-only.
- NODE-014 RTP topology unchanged.
- NODE-016 diagnostic isolation unchanged.

## Acceptance

- NODE-021/NODE-022 implementation was inspected.
- Gateway was deployed to the Kamatera USA host at `/opt/ai-secretary-gateway`.
- Gateway secrets stayed outside git at `/etc/ai-secretary/openai-realtime-gateway.env`.
- Gateway listened on port `8080` for smoke.
- Asterisk server reached the gateway endpoint.
- One gateway-mode measurement POST was run from the Asterisk server.
- OpenAI Realtime from the gateway worked.
- Redacted structured result was recorded.
- Transcript text was not logged.
- Gateway process was stopped after the smoke.
- Business dialog and systemd profile remained unchanged.

## Next Recommendation

Open a separate productionization node only if gateway STT should continue beyond measurement.

Recommended next scope:

```text
NODE-024 / productionize-supported-region-gateway-or-adopt-live-stt
```

That node should decide whether to add TLS, firewall allowlisting, systemd for the gateway, rotation/runbook for `GATEWAY_TOKEN`, and a feature-flagged dialog integration plan. Until then, keep the business dialog on the existing diagnostic-safe profile.
