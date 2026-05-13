# NODE-015 Production Server-Side STT Strategy

## Status

Recommended next node. Not started.

## Goal

Decide and validate the production server-side STT strategy now that NODE-014 has proven colocated ARI RTP delivery from Asterisk to the server-side listener.

## Branch Name

```text
feat/node-015-production-server-side-stt-strategy
```

## Background

NODE-014 proved the media path:

```text
server-side ari_app -> Stasis(ai_secretary) -> snoop_external_media_rtp -> RTP/PCM received on 172.18.0.1
```

Validated evidence:

- Local sound publish works without SSH.
- ARI connects locally as `Stasis(ai_secretary)`.
- `snoop_external_media_rtp` delivers RTP from the Asterisk container to the server host.
- `stt_live_rtp_packets_received_count > 0`.
- `stt_live_pcm_chunks_created_count > 0`.
- `stt_live_rtp_diagnostics_result=rtp_packets_received`.

NODE-014 did not decide production STT adoption. Its later dialog failure was expected because batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1` for RTP-only diagnostics.

## Scope

- Choose the bounded production STT path to test server-side.
- Validate whether live/server-side STT can reduce caller-perceived pauses without breaking the existing required-data flow.
- Preserve batch STT fallback unless explicitly disabled for an isolated diagnostic mode.
- Preserve required data collection before transfer:
  - `issue`;
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Preserve working-hours transfer, after-hours callback, SAFE_FINISH, department routing, and callback persistence contracts.
- Preserve tracing for RTP packets, PCM chunks, STT session setup, transcript timing, fallback, and dialog outcome.

## Out Of Scope

- Broad dialog refactors.
- Realtime agent adoption.
- Barge-in redesign.
- Changing transfer routes.
- Changing callback persistence schema.
- Committing runtime output under `data/storage/`.

## Candidate Paths

### Option A: Production Server-Side STT Strategy

Run colocated/server-side `ari_app` with the proven NODE-014 media topology and a real STT backend. Validate transcript quality, latency, fallback behavior, and impact on the normal dialog.

### Option B: Dialog-Isolated RTP Diagnostics

Create a smaller diagnostic mode that proves RTP/STT behavior without depending on batch STT or advancing the full dialog. This avoids false failures when the purpose of the run is media/STT diagnostics only.

## Validation Steps

1. Start server-side `ari_app` with local sound publish.
2. Confirm `SYSTEM_SOUNDS_DONE ok`.
3. Confirm ARI local connection and `ARI_WS_CONNECTED`.
4. Confirm `snoop_external_media_rtp` setup.
5. Confirm RTP and PCM counters are greater than zero.
6. Run with the selected real STT backend or isolated diagnostics path.
7. Confirm fallback behavior is explicit and diagnosable.
8. Confirm normal call contracts remain unchanged if dialog flow is enabled.

## Success Criteria

- Production recommendation is explicit: adopt, defer, or keep diagnostics-only.
- RTP/PCM diagnostics remain traceable.
- STT failures do not become opaque dialog failures.
- Normal transfer remains gated by required data and `phone_confirmed=true` if dialog flow is enabled.
- Runtime artifacts remain uncommitted.
