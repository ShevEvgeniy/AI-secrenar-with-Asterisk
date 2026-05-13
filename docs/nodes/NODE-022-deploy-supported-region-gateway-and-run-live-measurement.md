# NODE-022 Deploy Supported-Region Gateway And Run Live Measurement

## Status

CLOSED as blocked live-smoke/runbook closeout.

No supported-region gateway host, gateway URL, or gateway token was available in this workspace, so the live measurement was not run and no success is fabricated.

Next live step:

```text
Provision or provide a supported-region gateway host, set secrets only on that host, then run the exact one-off Asterisk-side gateway measurement command recorded below.
```

## Goal

Deploy the NODE-021 FastAPI realtime measurement gateway on a supported-region host, keep `OPENAI_API_KEY` only on the gateway, run exactly one one-off realtime STT measurement from the Asterisk server through the gateway, and record the redacted result.

This node does not:

- Change normal business dialog.
- Change `ai-secretary-ari.service`.
- Put `OPENAI_API_KEY` on the Asterisk server.
- Enable gateway STT for production calls.
- Change PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, Russian-only caller-facing behavior, NODE-016 diagnostic isolation, or NODE-014 RTP topology.

## Repository Inspection

Base state:

```text
f91e713 NODE-021 prepare supported-region gateway measurement
```

Current branch:

```text
feat/node-022-deploy-supported-region-gateway-and-run-live-measurement
```

NODE-021 implementation inspected:

```text
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
tests/test_realtime_gateway.py
tests/test_realtime_measurement.py
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
docs/stt_gateway_protocol.md
```

Confirmed:

- Gateway endpoint is `POST /v1/stt/realtime-measurement`.
- Gateway reads `OPENAI_API_KEY` from gateway runtime environment only.
- Gateway requires `Authorization: Bearer <gateway token>`.
- Asterisk-side gateway mode reads `REALTIME_GATEWAY_URL` / `REALTIME_GATEWAY_TOKEN` or explicit CLI arguments.
- Asterisk-side gateway mode does not read or require `OPENAI_API_KEY`.
- Gateway returns redacted structured JSON and does not return transcript text by default.
- Gateway/client modules do not import business dialog code.

Untracked forbidden artifacts observed locally and left untouched:

```text
data/storage/
node014-server.tar
```

## Supported-Region Gateway Deployment Path

Use a supported-region Linux host that is allowed to reach OpenAI Realtime.

Recommended application path on the gateway host:

```text
/opt/ai-secretary-realtime-gateway
```

Recommended secret env path on the gateway host:

```text
/etc/ai-secretary/openai-realtime-gateway.env
```

The env file must be created only on the gateway host and must not be committed:

```text
OPENAI_API_KEY=<real-openai-api-key-on-gateway-only>
GATEWAY_TOKEN=<random-gateway-bearer-token>
STT_GATEWAY_SERVER_TOKEN=<same-random-gateway-bearer-token>
GATEWAY_REGION_LABEL=<safe-supported-region-label>
OPENAI_REALTIME_MODEL=gpt-realtime-whisper
OPENAI_REALTIME_LANGUAGE=ru
OPENAI_REALTIME_TIMEOUT_SECONDS=30
STT_GATEWAY_MAX_AUDIO_SECONDS=15
STT_GATEWAY_MAX_AUDIO_BYTES=1048576
STT_GATEWAY_ALLOW_RETURN_TRANSCRIPT=false
```

Minimal deployment commands on the gateway host:

```bash
sudo mkdir -p /opt/ai-secretary-realtime-gateway /etc/ai-secretary
sudo chown "$USER":"$USER" /opt/ai-secretary-realtime-gateway
cd /opt/ai-secretary-realtime-gateway
git clone <repo-url> .
git checkout f91e713
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install uvicorn fastapi websockets httpx
sudo install -m 0600 -o root -g root /tmp/openai-realtime-gateway.env /etc/ai-secretary/openai-realtime-gateway.env
```

Run the gateway manually for the one-off smoke:

```bash
cd /opt/ai-secretary-realtime-gateway
set -a
. /etc/ai-secretary/openai-realtime-gateway.env
set +a
PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8443
```

If fronted by TLS/reverse proxy, expose:

```text
https://<gateway-hostname>/v1/stt/realtime-measurement
```

For a private one-off smoke without public exposure, use an SSH tunnel or VPN between the Asterisk server and gateway host, but keep `OPENAI_API_KEY` only on the gateway.

## Asterisk-Side One-Off Measurement

Current Asterisk server runtime remains:

```text
server=92.118.85.117
deployment_path=/home/tulauser/AI-secrenar-with-Asterisk-node014
systemd_service=ai-secretary-ari.service
```

The service profile must remain:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

Before running the one-off client, verify that the Asterisk server has no OpenAI key in the measurement shell:

```bash
test -z "${OPENAI_API_KEY:-}" && echo "asterisk_server_openai_key_present=no"
```

Use only gateway URL and gateway token on the Asterisk server:

```bash
cd /home/tulauser/AI-secrenar-with-Asterisk-node014
set +a
unset OPENAI_API_KEY
export REALTIME_GATEWAY_URL="https://<supported-region-gateway>/v1/stt/realtime-measurement"
export REALTIME_GATEWAY_TOKEN="<gateway-token>"
PYTHONPATH=src .venv/bin/python -m ai_secretary.stt.realtime_measurement \
  --audio /tmp/ai-secretary-node019/realtime_measurement_24k.wav \
  --timeout-seconds 45
unset REALTIME_GATEWAY_TOKEN
```

If the previous NODE-019 sample is not present, create a new short mono 16-bit PCM 24 kHz WAV outside git and use that path. Do not commit the audio artifact.

## Expected Result Mapping

Map the gateway client response to the NODE-022 summary like this:

```text
gateway_reachable=true if an HTTP response is received from the gateway; otherwise false
gateway_auth=ok for 2xx gateway auth pass; failed for 401/403; not_run if no gateway request was made
openai_realtime_from_gateway=ok if response.ok=true and openai_realtime_connection_ok=true; failed for structured gateway/OpenAI error; not_run if gateway was unavailable
chunks_sent=response.chunks_sent if present
transcript_present=response.transcript_text_present if present, otherwise unknown
transcript_text_logged=false unless transcript text was explicitly enabled and logged
error_type=response.error_type if present
error_status=HTTP status code if non-2xx or transport failure status if available
error_redacted=true when only structured redacted fields are recorded
business_dialog_changed=false
systemd_profile_changed=false
```

## Live Measurement Result

Live deployment and measurement were not completed because no supported-region host or gateway endpoint was available during NODE-022.

Structured redacted result:

```json
{
  "gateway_reachable": false,
  "gateway_auth": "not_run",
  "openai_realtime_from_gateway": "not_run",
  "asterisk_server_openai_key_present": "no",
  "chunks_sent": null,
  "transcript_present": "unknown",
  "transcript_text_logged": false,
  "error_type": "supported_region_gateway_unavailable",
  "error_status": null,
  "error_redacted": true,
  "business_dialog_changed": false,
  "systemd_profile_changed": false
}
```

Interpretation:

- Gateway was not reached.
- Gateway auth was not exercised.
- OpenAI Realtime from the gateway was not exercised.
- No transcript text was logged.
- No business dialog or systemd profile change was made.
- `OPENAI_API_KEY` was not placed on the Asterisk server by this node.

## Validation

Required focused tests:

```text
pytest tests/test_realtime_measurement.py tests/test_realtime_gateway.py
```

Required hygiene:

```text
git diff --check
git status --short
git diff --cached
git diff
```

Secret/artifact rules:

- Do not commit `OPENAI_API_KEY`.
- Do not commit real `GATEWAY_TOKEN`.
- Do not commit `data/storage/`.
- Do not commit `node014-server.tar`.
- Do not commit `.env` files with real secrets.

## Runtime Boundary

Preserved:

- Business dialog unchanged.
- `ai-secretary-ari.service` unchanged.
- Gateway STT not enabled in production dialog.
- Asterisk server remains in NODE-016/NODE-018 diagnostic-safe profile.
- OpenAI key remains gateway-only by design.
- NODE-014 RTP topology unchanged.
- NODE-016 diagnostic isolation unchanged.

## Acceptance

- NODE-021 implementation was inspected.
- Exact supported-region gateway deployment path and commands are recorded.
- Exact Asterisk-side one-off measurement command is recorded.
- Secrets are documented as runtime-only and outside git.
- No live success is fabricated.
- Blocked live-smoke result is recorded in the required structured shape.

## Next Recommendation

Provision a supported-region gateway host and rerun this exact one-off smoke. Once the smoke reaches the gateway and OpenAI Realtime from the gateway, record the real structured result before considering any production dialog integration.
