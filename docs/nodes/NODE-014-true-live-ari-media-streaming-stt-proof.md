# NODE-014 True Live ARI Media Streaming STT Proof

## Status

Implemented as an isolated proof path behind feature flags. This is not a production adoption decision.

## Goal

Prove whether caller audio can be tapped from Asterisk/ARI and sent to Realtime Whisper while the caller is still speaking, then compare live first-delta/final transcript timing against the existing recording-finish batch Whisper baseline.

NODE-013 remains a stored-WAV streaming adapter spike. NODE-014 adds the first true-live media path.

## Chosen Live Media Approach

Chosen option: ARI `externalMedia` with a local UDP RTP listener.

Implementation:

- `AriClient` now has proof-only bridge/externalMedia helpers:
  - `create_bridge_safe`
  - `add_channel_to_bridge_safe`
  - `create_external_media_safe`
  - `destroy_bridge_safe`
- `ai_secretary.stt.live_streaming` starts a local UDP socket, creates a temporary mixing bridge, adds the caller channel, creates an externalMedia channel pointed at the UDP socket, adds that external channel to the bridge, strips RTP headers, and streams RTP payload bytes into the existing Realtime Whisper adapter.
- `RealtimeWhisperAdapter` now supports `transcribe_pcm_chunks(...)` so NODE-013 stored-WAV replay and NODE-014 live chunks share the same WebSocket/STT adapter code.
- Follow-up 2 split live proof startup into synchronous setup plus a background STT task. The bridge/externalMedia setup is now awaited before `record_start` is logged and before `record_safe(...)` enters ARI channel recording. Asterisk ARI documents `POST /bridges/{bridgeId}/addChannel` as returning `409` when the channel is currently recording, which matches the first smoke failure shape and is the failure this ordering change is intended to avoid.

This was selected over AudioSocket because the current repo already uses ARI heavily and has a shared ARI WebSocket/event model. No AudioSocket dialplan or channel-driver integration exists in the repo.

## Feature Flags

Defaults preserve the current production flow.

```text
STT_LIVE_STREAMING_ENABLED=false
STT_LIVE_STREAMING_PROVIDER=openai_realtime_whisper
STT_LIVE_STREAMING_MODEL=gpt-realtime-whisper
STT_LIVE_STREAMING_FALLBACK_TO_BATCH=true
STT_LIVE_STREAMING_STAGE_ALLOWLIST=ISSUE,NAME,CITY,PHONE_CONFIRM
STT_LIVE_STREAMING_MEDIA_SOURCE=ari_external_media_rtp
STT_LIVE_STREAMING_RTP_HOST=127.0.0.1
STT_LIVE_STREAMING_RTP_PORT=0
STT_LIVE_STREAMING_SAMPLE_RATE=16000
STT_LIVE_STREAMING_CHUNK_MS=200
STT_LIVE_STREAMING_TIMEOUT_SECONDS=12
STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false
```

`PHONE` is hard-excluded even if someone adds it to the allowlist. `PHONE_CONFIRM` remains allowed for proof metrics, but the static fast path and confirmation safety are unchanged.

## What Worked

- The code now has a true-live proof path that can run before `RecordingFinished`.
- The proof is isolated from dialog routing by default: `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false` means the batch transcript still drives the business state machine while live STT is measured.
- Failure or non-use logs `stt_live_stream_fallback_to_batch` and keeps the existing batch path.
- Existing NODE-013 Realtime Whisper adapter is reused for live PCM chunks.
- PHONE remains excluded from live streaming by default and by code guard.

## What Failed / Limitations

- Follow-up smoke `CALL_ID=1778266458.4` failed immediately on `bridge_add_channel_http_error` for `ISSUE`, `NAME`, and `CITY`.
- Follow-up smoke `CALL_ID=1778267391.6` confirmed the exact blocker: `POST /ari/bridges/<bridge_id>/addChannel?channel=<original_channel_id>` returned HTTP `409 Conflict` with `{"message":"Channel 1778267391.6 currently recording"}`. The code was starting the proof via a background task before `record_safe(...)`, but the task could race behind recording startup.
- This implementation cannot prove the remote Asterisk host actually supports `externalMedia` until a controlled ARI run is executed against that host.
- Moving the active caller channel into a temporary mixing bridge is the riskiest part of the proof. It is guarded by `STT_LIVE_STREAMING_ENABLED=false` and should be tested only on a controlled call.
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

Current Follow-up 2 setup order:

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

## Follow-up 3 Recursion Guard

Smoke `CALL_ID=1778562482.0` showed that ARI `externalMedia` channels enter the same Stasis app as normal caller channels. Because the proof channel id was `live-proof-ext-...`, the app accidentally started a full dialog flow for the externalMedia channel, which then created another `live-proof-ext-...` channel recursively.

The dispatch path and `handle_call` entry now ignore channels whose id or name contains the proof marker `live-proof-ext-` before normal call setup side effects. Ignored channels log `stt_live_external_media_channel_ignored` with reason `external_media_channel_excluded`; they are not answered, do not start MOH, do not play prompts, do not record, and cannot create another live proof channel.

Live setup also refuses to run on a `live-proof-ext-...` channel and logs `stt_live_stream_probe_failed` with reason `external_media_channel_excluded` if reached directly. Realtime adapter task failures, including `invalid_api_key` and connection-closed failures, are caught and logged as `stt_live_stream_error`, then the normal batch fallback path remains responsible for dialog text.

## Checkpoint After Follow-ups 2 And 3

Follow-ups 2 and 3 improved the live proof path:

- ExternalMedia recursion is guarded.
- The old HTTP `409` blocker with message `Channel currently recording` is gone.
- ExternalMedia channels are ignored before normal call setup side effects.
- Live setup still falls back to the normal batch path when the Realtime task fails.

Current blocker:

- After the caller channel is bridged for `externalMedia`, normal `record_safe` / channel recording fails with `RecordingFailed`.
- Because normal recording fails, the batch fallback/baseline is not preserved.
- This means NODE-014 still has not proven a usable true-live streaming STT path that preserves the existing batch fallback contract.

Likely next follow-up:

- Preserve batch recording when the caller channel is bridged.
- Investigate bridge recording, a snoop channel, or another media tap that does not break normal channel recording.

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

Next node should run a controlled ARI call with `STT_LIVE_STREAMING_ENABLED=true` on `ISSUE`, `NAME`, or `CITY`, then inspect whether `stt_live_stream_first_delta_received` and `stt_live_stream_final_received` occur before `record_done`. If the externalMedia bridge disrupts normal playback/recording, reject this bridge approach and test an AudioSocket or dialplan-level RTP fork instead.
