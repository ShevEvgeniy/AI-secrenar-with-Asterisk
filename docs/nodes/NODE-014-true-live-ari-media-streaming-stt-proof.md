# NODE-014 True Live ARI Media Streaming STT Proof

## Status

Implemented as an isolated proof path behind feature flags. This is not a production adoption decision.

## Goal

Prove whether caller audio can be tapped from Asterisk/ARI and sent to Realtime Whisper while the caller is still speaking, then compare live first-delta/final transcript timing against the existing recording-finish batch Whisper baseline.

NODE-013 remains a stored-WAV streaming adapter spike. NODE-014 adds the first true-live media path.

## Chosen Live Media Approach

Chosen option after follow-up 4: ARI snoop channel bridged to ARI `externalMedia` with a local UDP RTP listener.

Implementation:

- `AriClient` now has proof-only bridge/externalMedia helpers:
  - `create_bridge_safe`
  - `snoop_channel_safe`
  - `add_channel_to_bridge_safe`
  - `create_external_media_safe`
  - `destroy_bridge_safe`
- `ai_secretary.stt.live_streaming` starts a local UDP socket, creates a temporary mixing bridge, creates a snoop channel for the caller, adds the snoop channel to the bridge, creates an externalMedia channel pointed at the UDP socket, adds that external channel to the bridge, strips RTP headers, and streams RTP payload bytes into the existing Realtime Whisper adapter.
- `RealtimeWhisperAdapter` now supports `transcribe_pcm_chunks(...)` so NODE-013 stored-WAV replay and NODE-014 live chunks share the same WebSocket/STT adapter code.
- Follow-up 2 split live proof startup into synchronous setup plus a background STT task. The bridge/externalMedia setup is now awaited before `record_start` is logged and before `record_safe(...)` enters ARI channel recording. Asterisk ARI documents `POST /bridges/{bridgeId}/addChannel` as returning `409` when the channel is currently recording, which matches the first smoke failure shape and is the failure this ordering change is intended to avoid.

This was selected over AudioSocket because the current repo already uses ARI heavily and has a shared ARI WebSocket/event model. No AudioSocket dialplan or channel-driver integration exists in the repo.

## Feature Flags

Defaults preserve the current production flow.

```text
STT_LIVE_STREAMING_ENABLED=false
STT_LIVE_STREAMING_PROVIDER=openai_realtime_whisper
STT_LIVE_OPENAI_DISABLED=false
STT_LIVE_OPENAI_API_MODE=ga
STT_LIVE_STREAMING_MODEL=gpt-realtime-whisper
STT_LIVE_STREAMING_FALLBACK_TO_BATCH=true
STT_LIVE_STREAMING_STAGE_ALLOWLIST=ISSUE,NAME,CITY
STT_LIVE_STREAMING_MEDIA_SOURCE=ari_external_media_rtp
STT_LIVE_STREAMING_TOPOLOGY=snoop_external_media_rtp
STT_LIVE_RTP_BIND_HOST=0.0.0.0
STT_LIVE_EXTERNAL_MEDIA_HOST=<ip reachable from Asterisk>
STT_LIVE_STREAMING_RTP_PORT=0
STT_LIVE_STREAMING_SAMPLE_RATE=24000
STT_LIVE_STREAMING_CHUNK_MS=200
STT_LIVE_STREAMING_TIMEOUT_SECONDS=12
STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false
```

`PHONE` is hard-excluded even if someone adds it to the allowlist. `PHONE_CONFIRM` is also excluded from the default live proof allowlist and should remain batch-only unless explicitly enabled for a controlled diagnostic smoke.

## What Worked

- The code now has a true-live proof path that can run before `RecordingFinished`.
- The proof is isolated from dialog routing by default: `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false` means the batch transcript still drives the business state machine while live STT is measured.
- Failure or non-use logs `stt_live_stream_fallback_to_batch` and keeps the existing batch path.
- Existing NODE-013 Realtime Whisper adapter is reused for live PCM chunks.
- PHONE remains excluded from live streaming by default and by code guard.

## What Failed / Limitations

- Follow-up smoke `CALL_ID=1778266458.4` failed immediately on `bridge_add_channel_http_error` for `ISSUE`, `NAME`, and `CITY`.
- Follow-up smoke `CALL_ID=1778267391.6` confirmed the exact blocker: `POST /ari/bridges/<bridge_id>/addChannel?channel=<original_channel_id>` returned HTTP `409 Conflict` with `{"message":"Channel 1778267391.6 currently recording"}`. The code was starting the proof via a background task before `record_safe(...)`, but the task could race behind recording startup.
- Follow-up smoke `CALL_ID=1778563548.0` proved that bridging the original caller channel before `record_safe(...)` avoids the old `409`, but breaks normal channel recording with `RecordingFailed`. That topology is now retained only as explicit diagnostic mode `STT_LIVE_STREAMING_TOPOLOGY=bridge_original_external_media_rtp`.
- This implementation cannot prove the remote Asterisk host actually supports `externalMedia` until a controlled ARI run is executed against that host.
- Moving the active caller channel into a temporary mixing bridge is no longer the default proof topology because it broke batch recording. The default proof topology uses a snoop channel so the original caller channel can keep normal channel recording.
- Codec assumptions are explicit: the RTP payload is treated as raw `slin16` PCM at `STT_LIVE_STREAMING_SAMPLE_RATE`.
- No production routing, transfer, callback, after-hours, SAFE_FINISH, CITY validation, or PHONE digit behavior was changed.

## Follow-up Diagnostics And Ordering

Bridge/externalMedia setup now logs each ARI step:

- `stt_live_bridge_create_attempt`
- `stt_live_bridge_create_ok`
- `stt_live_bridge_add_channel_attempt`
- `stt_live_bridge_add_channel_failed`
- `stt_live_bridge_add_channel_ok`
- `stt_live_external_media_create_attempt`
- `stt_live_external_media_create_ok`
- `stt_live_external_media_create_failed`
- `stt_live_bridge_cleanup_attempt`
- `stt_live_bridge_cleanup_done`
- `stt_live_bridge_cleanup_failed`

Failure events include `bridge_id`, `original_channel_id`, `external_media_channel_id`, `ari_endpoint`, `ari_request_params`, `ari_http_status`, `ari_response_body`, `ari_request_method`, `ari_request_url`, `ari_request_path`, and `ari_request_query`.

Legacy Follow-up 2 setup order:

1. Prompt playback barrier completes.
2. `stt_live_stream_probe_started`.
3. Create temporary mixing bridge.
4. Add original caller channel to the bridge before starting ARI recording.
5. Create externalMedia channel pointed at the local RTP socket.
6. Add returned/configured externalMedia channel id to the bridge.
7. Log `stt_live_stream_media_started`.
8. Log `record_start`.
9. Start the normal ARI channel recording through `record_safe(...)`.

Acceptance-critical event ordering is now covered by tests: `stt_live_bridge_add_channel_ok` and `stt_live_stream_media_started` must occur before `record_start` in the live-enabled setup-success path. If setup fails before recording, cleanup and `stt_live_stream_fallback_to_batch` are logged, then the normal batch recording path still starts.

The externalMedia channel is not assumed to auto-join the bridge; Asterisk documentation describes creating the externalMedia channel and then adding it to an existing bridge. If a future smoke shows the externalMedia channel is already bridged in this deployment, the next change should make the second add conditional on the failure/status/body details.

## Follow-up 4 Snoop Topology

Follow-up 4 changes the selected proof topology to `snoop_external_media_rtp` so live media tap does not require adding the original caller channel to the proof bridge.

Current default setup order:

1. Prompt playback barrier completes.
2. `stt_live_stream_probe_started`.
3. `live_media_topology_selected` with `live_media_topology=snoop_external_media_rtp`.
4. Create temporary mixing bridge.
5. Create ARI snoop channel `live-proof-snoop-...` spying on the original caller channel.
6. Add the snoop channel to the proof bridge.
7. Create externalMedia channel `live-proof-ext-...` pointed at the local RTP socket.
8. Add the externalMedia channel to the proof bridge.
9. Log `stt_live_stream_media_started`.
10. Log `stt_live_stream_session_started`.
11. Start normal `record_safe(...)` on the original caller channel.

The original caller channel is not added to the proof bridge in this topology. Batch recording therefore remains on the same original channel path as the default call flow. Tests cover both the old `bridge_original_external_media_rtp` `RecordingFailed` conflict and the new snoop topology preserving batch fallback/baseline transcription.

## Follow-up 3 Recursion Guard

Smoke `CALL_ID=1778562482.0` showed that ARI `externalMedia` channels enter the same Stasis app as normal caller channels. Because the proof channel id was `live-proof-ext-...`, the app accidentally started a full dialog flow for the externalMedia channel, which then created another `live-proof-ext-...` channel recursively.

The dispatch path and `handle_call` entry now ignore channels whose id or name contains proof markers `live-proof-ext-` or `live-proof-snoop-` before normal call setup side effects. Ignored channels log `stt_live_external_media_channel_ignored` with reason `external_media_channel_excluded`; they are not answered, do not start MOH, do not play prompts, do not record, and cannot create another live proof channel.

Live setup also refuses to run on a `live-proof-ext-...` channel and logs `stt_live_stream_probe_failed` with reason `external_media_channel_excluded` if reached directly. Realtime adapter task failures, including `invalid_api_key` and connection-closed failures, are caught and logged as `stt_live_stream_error`, then the normal batch fallback path remains responsible for dialog text.

## Checkpoint After Follow-up 4

Follow-ups 2, 3, and 4 improved the live proof path:

- ExternalMedia recursion is guarded.
- The old HTTP `409` blocker with message `Channel currently recording` is gone.
- ExternalMedia and snoop proof channels are ignored before normal call setup side effects.
- Live setup still falls back to the normal batch path when the Realtime task fails.
- The selected topology no longer bridges the original caller channel, so batch channel recording should remain available during live proof.

Current unknown until next smoke:

- Whether the remote Asterisk deployment supports snoop channel creation with the chosen parameters: `spy=in`, `whisper=none`.
- Whether RTP payload arrives from the snoop-to-externalMedia bridge in the expected signed-linear format (`slin24` by default for 24 kHz PCM).

If follow-up 4 smoke fails:

- `snoop_channel_failed` or `live_media_topology_failed` should identify the ARI status/body/path/query.
- If snoop succeeds but no chunks arrive, the next blocker is RTP/media format or snoop direction, not batch fallback.

## Follow-up 5 Realtime Protocol And RTP Diagnostics

Smoke `CALL_ID=1778565454.11` showed that the snoop topology preserves batch fallback, but OpenAI Realtime rejected the adapter's session config with `Unknown parameter: 'session.type'`.

At this checkpoint the adapter moved to the transcription WebSocket intent and stopped attempting to set `session.type` through a normal Realtime conversation session. It logs session config sent/ok/failed before audio streaming starts. PCM live proof defaults now use 24 kHz because OpenAI Realtime transcription PCM input requires 24 kHz mono 16-bit PCM; externalMedia format follows the sample rate (`slin24` by default).

Added diagnostics distinguish the live pipeline stages:

- RTP listener started.
- RTP packets received.
- PCM chunks created from RTP payloads.
- OpenAI session config sent/accepted/rejected.
- OpenAI audio chunks sent.
- OpenAI delta/final received.
- No RTP/no audio and no delta/final cases.

## Follow-up 6 Session Handshake And RTP Target

Smoke `CALL_ID=1778571204.0` showed two separate blockers:

- The server emits `transcription_session.created` when a transcription WebSocket is established. The adapter treated that as an unexpected config response.
- externalMedia was advertised as `127.0.0.1:<port>`, which is only valid when Asterisk and the Python process are colocated. In the remote/container deployment, RTP was sent to Asterisk's own loopback instead of the Python listener.

The adapter now accepts `transcription_session.created` or `session.created` as the initial session creation event and logs `stt_live_openai_session_created`.

RTP binding and advertising are now separate:

- `STT_LIVE_RTP_BIND_HOST`: local interface for the Python UDP listener, default `0.0.0.0`.
- `STT_LIVE_EXTERNAL_MEDIA_HOST`: host/IP advertised to Asterisk in `external_host`, required for remote Asterisk.
- Legacy aliases are also accepted: `STT_LIVE_RTP_ADVERTISED_HOST`, `STT_LIVE_RTP_HOST`, `STT_LIVE_STREAMING_RTP_ADVERTISED_HOST`, `STT_LIVE_STREAMING_RTP_HOST`.

For remote Asterisk, live setup fails cleanly with `live_rtp_advertised_host_required_for_remote_asterisk` if no advertised host is set, and with `live_rtp_loopback_advertised_for_remote_asterisk` if `127.0.0.1` / localhost is advertised. Batch fallback remains stable.

## Follow-up 7 Config Wrapper And PHONE_CONFIRM Safety

Smoke `CALL_ID=1778572758.20` showed OpenAI accepting the transcription session connection but rejecting the update event with `Missing required parameter: 'session'`. Follow-up 7 added the required top-level `session` object; follow-up 8 replaced that beta-shaped update with the GA `session.update` payload.

The default live proof stage allowlist is now `ISSUE,NAME,CITY`. `PHONE_CONFIRM` logs `stt_live_stream_probe_failed` with reason `phone_confirm_not_in_default_live_allowlist` unless explicitly added through `STT_LIVE_STREAMING_STAGE_ALLOWLIST` for diagnostics. `PHONE` remains excluded even if configured.

## Follow-up 8 GA API And RTP Isolation

Smoke `CALL_ID=1778573897.50` split the remaining failure into two independent blockers:

- OpenAI accepted the transcription WebSocket session but rejected `gpt-realtime-whisper` with `invalid_model` because the adapter still used the beta Realtime header path.
- RTP packet counts stayed at zero even after advertising a non-loopback externalMedia target.

The adapter now defaults to GA Realtime mode for transcription sessions:

- `STT_LIVE_OPENAI_API_MODE=ga` omits the legacy `OpenAI-Beta: realtime=v1` header.
- `STT_STREAMING_OPENAI_API_MODE=ga` does the same for the NODE-013/NODE-014 shared streaming config path.
- GA mode sends `session.update` with nested `audio.input.format`, `audio.input.transcription`, `audio.input.turn_detection`, and `audio.input.noise_reduction`.
- The selected OpenAI mode, WebSocket path, and model are logged as `stt_live_openai_api_mode`, `stt_live_openai_ws_path`, and `stt_live_openai_model_selected` without logging API keys.

RTP reachability can now be tested without opening an OpenAI session:

```text
STT_LIVE_STREAMING_ENABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
# or
STT_LIVE_OPENAI_DISABLED=true
```

Diagnostics-only mode uses the same `snoop_external_media_rtp` topology, starts the same UDP listener, counts RTP packets and PCM chunks, cleans up the snoop/externalMedia bridge, and leaves batch STT as the dialog transcript. It logs `stt_live_rtp_diagnostics_only_started`, `stt_live_rtp_diagnostics_only_finished`, and `stt_live_rtp_diagnostics_result`.

Interpretation:

- `stt_live_rtp_packets_received_count > 0`: Asterisk externalMedia can reach the Python UDP listener; continue with OpenAI/audio-format debugging.
- `stt_live_rtp_packets_received_count = 0`: Remaining blocker is network/VPN/firewall/Asterisk externalMedia routing, independent of OpenAI.

## Follow-up 9 Colocated RTP Diagnostics

Decision: do not spend more NODE-014 time trying to route Asterisk externalMedia RTP from the remote server to Windows over VPN. The preferred proof architecture is to run `ari_app` colocated with Asterisk on the server, or at least on the same network side as Asterisk.

Why:

- Windows VezarusPro IP `10.67.186.74` is active locally, but the Asterisk server `92.118.85.117` has no VPN/tun/wg/tailscale/zerotier/vezarus interface.
- Server route check showed `10.67.186.74 via 92.118.85.113 dev eth0 src 92.118.85.117`, so packets to the Windows VPN IP leave through the public gateway instead of a VPN route.
- A direct UDP test from `92.118.85.117` to a Windows listener on `10.67.186.74:50555` did not arrive.
- This explains the prior live proof counters: `stt_live_rtp_packets_received_count=0`, `stt_live_pcm_chunks_created_count=0`, and `stt_live_openai_no_audio_received reason=rtp_packets_zero`.

Server-side RTP diagnostics should be run before another OpenAI-enabled smoke. First identify which server-side address the Asterisk container can reach.

Inspect host/container networking on the server:

```bash
ip -br addr
ip route
docker inspect asterisk
docker exec asterisk ip route
docker exec asterisk ip addr
```

Start a UDP listener on the server:

```bash
python -c "import socket; host='0.0.0.0'; port=50555; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.bind((host,port)); print(f'UDP listening on {host}:{port}'); data,addr=s.recvfrom(2048); print('RECEIVED',data,'FROM',addr)"
```

Send UDP from the Asterisk container, replacing `<SERVER_REACHABLE_HOST>` with each candidate:

```bash
docker exec asterisk bash -lc 'echo container-udp-test > /dev/udp/<SERVER_REACHABLE_HOST>/50555'
```

Candidate values for `<SERVER_REACHABLE_HOST>`:

- `172.18.0.1`
- `172.17.0.1`
- `92.118.85.117`

Acceptance for the preflight:

- If the listener prints `RECEIVED`, use that exact `<SERVER_REACHABLE_HOST>` as `STT_LIVE_EXTERNAL_MEDIA_HOST`.
- If no packet arrives, try the next candidate and document the failed candidate/result.
- If all candidates fail, the next blocker is Asterisk/Docker/server firewall routing, not OpenAI and not Windows/VPN.

Server-side RTP diagnostics-only smoke environment:

```bash
export STT_LIVE_STREAMING_ENABLED=true
export STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
export STT_LIVE_OPENAI_DISABLED=true
export STT_LIVE_STREAMING_FALLBACK_TO_BATCH=true
export STT_LIVE_STREAMING_STAGE_ALLOWLIST=ISSUE,NAME,CITY
export STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false
export STT_LIVE_STREAMING_TOPOLOGY=snoop_external_media_rtp
export STT_LIVE_RTP_BIND_HOST=0.0.0.0
export STT_LIVE_EXTERNAL_MEDIA_HOST=<SERVER_REACHABLE_HOST>
```

Expected diagnostic logs:

- `stt_live_rtp_listener_started` with `stt_live_rtp_bind_host=0.0.0.0`, the selected `stt_live_rtp_advertised_host`, and the dynamic `stt_live_rtp_port`.
- `stt_live_external_media_target` showing `<SERVER_REACHABLE_HOST>:<dynamic_port>`.
- `stt_live_rtp_diagnostics_only_started`.
- `stt_live_rtp_packets_received_count`.
- `stt_live_pcm_chunks_created_count`.
- `stt_live_rtp_diagnostics_result`.

Interpretation:

- RTP packets greater than zero means the server/container media path works; then run OpenAI GA mode.
- RTP packets equal zero means the blocker is colocated Asterisk/Docker/externalMedia topology or server firewall.

Windows/VPN RTP remains a debug-only path. It is not the recommended architecture for this project unless the Asterisk host later gets an explicit route/interface to the Windows VPN network.

Status:

```text
NODE-014 remains open.
```

## Metrics

NODE-014 emits:

- `stt_live_stream_probe_started`
- `stt_live_stream_probe_failed`
- `stt_live_stream_session_started`
- `stt_live_stream_media_started`
- `stt_live_stream_audio_chunk_sent`
- `stt_live_stream_first_delta_received`
- `stt_live_stream_final_received`
- `stt_live_stream_error`
- `stt_live_stream_fallback_to_batch`
- `live_media_topology_selected`
- `live_media_topology_failed`
- `snoop_channel_started`
- `snoop_channel_failed`
- `stt_live_rtp_listener_started`
- `stt_live_rtp_packet_received`
- `stt_live_rtp_packets_received_count`
- `stt_live_pcm_chunk_created`
- `stt_live_pcm_chunks_created_count`
- `stt_live_openai_session_config_sent`
- `stt_live_openai_session_created`
- `stt_live_openai_session_config_ok`
- `stt_live_openai_session_config_failed`
- `stt_live_openai_audio_chunk_sent`
- `stt_live_openai_audio_chunks_sent_count`
- `stt_live_openai_delta_received`
- `stt_live_openai_final_received`
- `stt_live_openai_no_audio_received`
- `stt_live_openai_no_delta_received`
- `stt_live_openai_api_mode`
- `stt_live_openai_ws_path`
- `stt_live_openai_model_selected`
- `stt_live_rtp_diagnostics_only_started`
- `stt_live_rtp_diagnostics_only_finished`
- `stt_live_rtp_diagnostics_result`
- `stt_batch_baseline_latency_ms`
- `stt_live_vs_batch_delta_ms`

Metric details include:

- `stt_live_stream_latency_first_delta_ms`
- `stt_live_stream_latency_final_ms`
- `stt_live_stream_audio_started_before_recording_finished`
- `stt_live_stream_recording_finish_to_final_ms`
- stage, turn index, record name, provider, model, and media source

## Timestamp Comparison

Implemented comparison semantics:

- Live first delta: live proof start -> first Realtime Whisper delta.
- Live final: live proof start -> final Realtime Whisper transcript.
- Recording finish to live final: `RecordingFinished` perf timestamp -> live final perf timestamp. Negative values mean final transcript arrived before recording finish.
- Batch baseline: recording download artifact -> existing batch STT text ready.
- Live vs batch delta: `recording_finish_to_live_final_ms - stt_batch_baseline_latency_ms`.

No controlled remote call has been run in this workspace, so measured real-call values are not yet available. Unit tests prove the metric plumbing and fallback behavior; the next node or manual proof run must capture real Asterisk timestamps.

## Fallback Behavior

If the proof is disabled, unsupported, not allowlisted, fails, times out, or is configured not to drive dialog, the existing batch path remains active.

When live proof succeeds but `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false`, the event log still records live timings and logs `stt_live_stream_fallback_to_batch` with reason `live_transcript_not_used_for_dialog`.

## Recommendation

Continue, not adopt yet.

Next smoke should run RTP diagnostics-only colocated with Asterisk, using the preflight UDP test above to choose `STT_LIVE_EXTERNAL_MEDIA_HOST`. If RTP remains zero colocated, fix Asterisk/Docker/externalMedia topology before spending more time on OpenAI. If RTP is positive, run OpenAI-enabled GA mode and inspect whether chunks are sent and whether delta/final events arrive before `record_done`.
