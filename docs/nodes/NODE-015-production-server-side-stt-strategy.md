# NODE-015 Production Server-Side STT Strategy

## Status

Planning closeout. Docs-only.

## Goal

Define the production-ready server-side STT strategy now that NODE-014 has proven colocated ARI RTP delivery from Asterisk to the server-side listener.

## Branch Name

```text
feat/node-015-production-server-side-stt-strategy
```

## Context From NODE-014

NODE-014 proved the colocated/server-side media path:

```text
server-side ari_app -> Stasis(ai_secretary) -> snoop_external_media_rtp -> RTP/PCM received on 172.18.0.1
```

Validated evidence:

- Local sound publish works with `ASTERISK_PUBLISH_MODE=local`.
- Server-side ARI connects locally as `Stasis(ai_secretary)`.
- `snoop_external_media_rtp` delivers RTP from the Asterisk container to the server host.
- `stt_live_rtp_packets_received_count > 0`.
- `stt_live_pcm_chunks_created_count > 0`.
- `stt_live_rtp_diagnostics_result=rtp_packets_received`.

Boundary:

- NODE-014 is closed as media-path proof only.
- Production STT adoption was explicitly out of scope.
- The later RTP-only smoke dialog failure was expected because batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1`.
- That failure is not evidence against the media path.

## Constraints

- Do not change PHONE behavior.
- Do not change PHONE_CONFIRM fast path.
- Do not change CITY validation.
- Do not change transfer, callback, after-hours, or SAFE_FINISH contracts.
- Do not weaken the Russian-only caller-facing dialog invariant.
- Do not commit secrets.
- Do not commit `data/storage/`.
- Do not commit `node014-server.tar`.
- Do not make production STT implementation in this node.
- Preserve NODE-014 diagnostics and the proven RTP path.
- Keep production STT adoption as an explicit feature-flagged decision.

## Current OpenAI Documentation Check

Official documentation was rechecked on 2026-05-13.

Sources:

- Realtime transcription guide: <https://developers.openai.com/api/docs/guides/realtime-transcription>
- Speech-to-text guide: <https://developers.openai.com/api/docs/guides/speech-to-text>
- OpenAI API pricing: <https://developers.openai.com/api/docs/pricing>
- Public pricing page for realtime transcription pricing: <https://openai.com/api/pricing/>

Relevant current facts:

- Realtime transcription is for live speech-to-text without a spoken assistant response. It streams transcript deltas as audio arrives.
- The lowest-latency current streaming transcription path in the docs is `gpt-realtime-whisper`.
- Realtime transcription sessions use `type: "transcription"` and can connect with WebSocket for server-side audio pipelines.
- For `audio/pcm`, realtime transcription expects 24 kHz mono PCM.
- The docs position `gpt-realtime-whisper` as a live transcription option that must be tested against real audio, languages, vocabulary, and latency needs before switching production traffic.
- The Audio API `transcriptions` endpoint currently supports `whisper-1`, `gpt-4o-mini-transcribe`, `gpt-4o-transcribe`, and `gpt-4o-transcribe-diarize`.
- File uploads to the Audio API are limited to 25 MB and support `mp3`, `mp4`, `mpeg`, `mpga`, `m4a`, `wav`, and `webm`.
- Current documented estimated Audio API transcription costs are `gpt-4o-transcribe` at `$0.006 / minute` and `gpt-4o-mini-transcribe` at `$0.003 / minute`.
- The public pricing page currently lists `GPT-Realtime-Whisper` at `$0.017 / minute`.

## Options Considered

### Option 1: OpenAI STT Through Production-Safe Egress

Run colocated `ari_app` on the Asterisk server, preserve the NODE-014 RTP topology, and send live server-side audio to OpenAI Realtime transcription over a production-approved route.

Recommended shape:

- Primary STT: `gpt-realtime-whisper` for live ISSUE, NAME, and CITY experiments.
- Keep batch Audio API transcription as baseline/fallback during rollout.
- Use server-side WebSocket egress from `ari_app`, not browser/WebRTC.
- Keep `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false` for the first validation smoke, then explicitly enable live transcript use only after transcript quality and fallback are proven.
- Do not include PHONE by default. PHONE remains batch/conservative because digit safety is more important than latency.
- Keep PHONE_CONFIRM on the existing fast path.

Network decision:

- Prefer direct HTTPS/WSS egress from the server to OpenAI if the host has stable outbound internet, TLS inspection is absent or well understood, and secrets can be stored safely.
- Use a small outbound proxy/gateway if operations require allowlisted egress, central audit, IP restrictions, or provider failover controls.
- Do not route OpenAI through the Windows development host or VPN path. NODE-014 already showed the production shape is colocated/server-side, not Windows/VPN.

Operational requirements:

- No API key in repo or shell history.
- Store `OPENAI_API_KEY`, `OPENAI_BASE_URL` if overridden, ARI credentials, and publish paths in a root-owned env file or secret manager.
- Set explicit timeouts and fallback reasons.
- Log provider, model, endpoint mode, transcript timing, fallback reason, and dialog outcome without logging secrets or raw credentials.

### Option 2: Local STT On The Server

Run an offline STT engine on the same server as `ari_app`.

Candidate engines:

- `faster-whisper` or CTranslate2-based Whisper variants.
- `whisper.cpp` with CPU quantized models.
- Vosk/Kaldi-style Russian models as a low-resource fallback.

Assessment:

- Local STT is viable only after measuring the actual server hardware. The repo docs do not record CPU model, RAM, GPU availability, or sustained load capacity for this server.
- CPU-only Whisper-class models can be acceptable for short utterances, but latency and Russian name/number accuracy must be proven with real telephony audio.
- Local STT reduces external dependency and data egress, but adds model deployment, warmup, CPU/RAM sizing, monitoring, and accuracy maintenance.
- Local STT is not the best first production path for this project because NODE-013/NODE-014 already built and proved the OpenAI adapter/media foundations, while no local STT runtime exists in the repo.

When to adopt:

- As a fallback or later privacy/resilience enhancement after a hardware benchmark node.
- As primary only if egress to OpenAI is disallowed or measured remote STT is not operationally acceptable.

### Option 3: Hybrid Remote Primary With Local/Offline Fallback

Use remote OpenAI STT as the primary production path and a local/offline engine as a bounded fallback.

Recommended failover semantics:

- Remote live STT failure before a final transcript should fall back to the existing batch STT path when dialog flow is enabled.
- If both remote live and batch remote STT are unavailable, local STT may be attempted if configured and warmed.
- If no STT returns usable text, do not fabricate text. Use the existing bounded retry/SAFE_FINISH behavior with an explicit `stt_unavailable` or equivalent reason.
- Fallback must not bypass required data collection.
- Fallback must not transfer unless mandatory data and `phone_confirmed=true` are satisfied.

Recommended rollout:

- NODE-016 should implement the remote-primary portion with dialog-isolated diagnostics first.
- A later node should benchmark and add local fallback only after hardware is known.

### Option 4: Dialog-Isolated RTP Diagnostics Mode

Make RTP diagnostics fully isolated from business dialog.

Problem observed in NODE-014:

- RTP diagnostics succeeded.
- The normal dialog later failed because batch STT was pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1`.
- This failure was expected, but it creates noisy validation and can look like a business-flow regression.

Recommended behavior:

- Add a diagnostics mode that exercises local publish, ARI, snoop/externalMedia, UDP listener, RTP packet counting, PCM chunk counting, and optional STT session setup without advancing the business dialog.
- Diagnostics mode must not call batch OpenAI STT when the purpose is RTP-only validation.
- Diagnostics mode must not run the normal required-data state machine.
- Diagnostics mode must end the call with a controlled Russian diagnostic phrase or hang up after the diagnostic window, depending on the smoke script design.
- Diagnostics results must be reported through events such as `stt_live_rtp_diagnostics_result`, not through SAFE_FINISH.

Decision:

- Yes, RTP diagnostics should be made fully dialog-isolated before production STT implementation drives dialog. This prevents dummy or blocked STT endpoints from poisoning business-flow validation.

### Option 5: Server-Side Process Management

Run `ari_app` as a managed Linux service on the Asterisk server.

Recommended systemd strategy:

- Create an `ai-secretary-ari.service` unit that runs `python -m ai_secretary.telephony.ari_app` from a fixed deployment directory and virtualenv.
- Use a root-owned `EnvironmentFile`, for example `/etc/ai-secretary/ari.env`, mode `0600`.
- Keep generated data under the configured runtime data path and keep `data/storage/` out of git.
- Use `Restart=always` or `Restart=on-failure` with a short `RestartSec`.
- Use `After=network-online.target docker.service` and, if possible, require the Asterisk container/service readiness through a separate preflight or health check.
- Log to journald and preserve application event logs.
- On reboot, service startup must republish local sounds, connect to local ARI, and reach `READY_WAITING_FOR_CALLS`.

Secrets and config:

- `OPENAI_API_KEY` only in the environment file or secret manager.
- ARI credentials only in the environment file or secret manager.
- `ASTERISK_PUBLISH_MODE=local`.
- `ASTERISK_LOCAL_SOUNDS_ROOT` set from the real Docker volume path, not hardcoded in code.
- `STT_LIVE_EXTERNAL_MEDIA_HOST=172.18.0.1` for the validated colocated Docker host route unless a future network preflight proves another value.

Restart behavior:

- Restart after crash.
- Restart after reboot.
- Fail visibly if ARI credentials, OpenAI credentials, or local publish path are missing.
- Do not loop silently without clear logs when ARI or Asterisk is unavailable.

## Decision Matrix

| Option | Latency | Accuracy | Reliability | Operational burden | Data egress | Fit now | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI Realtime via direct server egress | Best candidate | Must be validated on Russian telephony audio | Depends on internet/provider | Moderate | Yes | High | Recommended primary if egress is allowed |
| OpenAI through proxy/gateway | Good | Same as direct | Better audit/control | Higher | Yes, controlled | High if ops requires allowlisting | Recommended when direct egress is not acceptable |
| Audio API batch only | Existing baseline | Good baseline | Simple | Low | Yes | Medium | Keep as fallback/baseline, not latency solution |
| Local STT primary | Hardware-dependent | Unknown for names/numbers | Independent of internet | High | No | Low until benchmarked | Defer as primary |
| Hybrid remote primary + local fallback | Good | Potentially strongest resilience | Best if implemented carefully | Highest | Partial | Medium | Target architecture after local benchmark |
| Dialog-isolated RTP diagnostics | Not a user STT path | N/A | High for validation | Low/moderate | Optional | Very high | Implement before dialog-driving STT |
| systemd/autostart | N/A | N/A | Required for production | Moderate | N/A | High | Required for production launch |

## Recommended Strategy

Use OpenAI Realtime transcription as the first production STT candidate for colocated `ari_app`, reached from the server through a production-approved egress route.

Default recommendation:

1. Make RTP diagnostics fully dialog-isolated first.
2. Add production server-side service management for `ari_app`.
3. Validate direct server egress to OpenAI. If direct egress is not acceptable, add an outbound proxy/gateway and configure `OPENAI_BASE_URL`/network policy accordingly.
4. Run OpenAI Realtime transcription in measurement mode on ISSUE, NAME, and CITY with `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false`.
5. Compare live final transcript timing and quality against batch baseline.
6. Only after a passing measurement smoke, explicitly enable live transcript use for selected stages.
7. Keep PHONE and PHONE_CONFIRM out of live transcript adoption unless a separate digit-safety node proves it.
8. Keep Audio API batch transcription as fallback/baseline.
9. Defer local STT implementation until actual server hardware is benchmarked.

Answer to key questions:

1. Best production STT path: colocated `ari_app` plus `snoop_external_media_rtp` plus OpenAI Realtime transcription over approved server egress, with batch fallback.
2. Reach OpenAI directly from the server if egress and secret handling are acceptable; otherwise use a controlled outbound proxy/gateway. Do not route through Windows/VPN.
3. Local STT may be viable, but viability is unknown until server CPU/RAM/GPU and real telephony latency are benchmarked.
4. If STT is unavailable, fall back to batch if possible, then local fallback if configured, then existing bounded retry/SAFE_FINISH without fabricated text or unsafe transfer.
5. Yes, RTP diagnostics should be fully dialog-isolated before production STT drives dialog.
6. NODE-016 should implement dialog-isolated RTP diagnostics, server-side service/env guidance, and production-safe OpenAI Realtime measurement mode without enabling dialog-driving live STT by default.

## Risks

- OpenAI API model names, pricing, and supported fields can change; implementation nodes must recheck official docs before coding.
- Server egress may be blocked, unstable, inspected, or policy-disallowed.
- Telephony audio may need format conversion/resampling before Realtime transcription performs well.
- Russian names, city/address phrases, and phone-adjacent utterances may require stage-specific prompts and validation.
- Realtime partial transcripts may be lower quality than final transcripts; dialog must not act on premature partials.
- Local STT may be too slow or inaccurate on the current server.
- systemd restart loops could hide configuration errors unless startup failures are explicit.
- Diagnostics mode could accidentally enter normal dialog if not isolated at the call/session level.

## NODE-016 Acceptance Criteria

NODE-016 should implement, at minimum:

- A dialog-isolated RTP diagnostics mode that can run without batch OpenAI STT.
- Diagnostics mode preserves NODE-014 RTP path and emits RTP/PCM counters and a final diagnostics result.
- Diagnostics mode does not run the business dialog state machine and does not force SAFE_FINISH because of dummy STT.
- A server-side launch/service plan or sample systemd unit with env/secrets handling documented.
- A production-safe OpenAI Realtime measurement mode for server-side `ari_app` that keeps `STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false` by default.
- Explicit egress mode documentation: direct OpenAI egress or proxy/gateway.
- PHONE remains excluded from live STT adoption.
- PHONE_CONFIRM fast path remains unchanged.
- CITY validation, transfer, callback, after-hours, SAFE_FINISH, and Russian-only dialog contracts remain unchanged.
- Secrets and runtime artifacts remain uncommitted.

Validation for NODE-016:

- Focused tests for diagnostics isolation and fallback behavior.
- Focused dialog/transfer/PHONE regressions if code touches call flow.
- Server-side smoke:
  - local publish ok;
  - ARI local connection ok;
  - diagnostics RTP packets and PCM chunks greater than zero;
  - no batch dummy OpenAI STT call in diagnostics-only mode;
  - no business SAFE_FINISH caused by diagnostics-only run.

## NODE-015 Validation

Docs-only node. No tests required.

Validation run:

```text
git diff --check
PASS
```
