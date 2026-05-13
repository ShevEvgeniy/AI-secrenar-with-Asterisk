# NODE-016 Dialog-Isolated RTP Diagnostics And Server STT Measurement

## Goal

NODE-016 separates live media/STT diagnostics from the normal customer dialog state machine.

The NODE-014 server smoke proved that the colocated ARI app can receive RTP and PCM chunks through `snoop_external_media_rtp`, but the same call later reached normal `NAME -> SAFE_FINISH` because batch STT was intentionally pointed at a dummy OpenAI endpoint. That was useful for RTP proof, but it made a diagnostic smoke look like a failed customer flow.

## Decision

Add an explicit diagnostics isolation flag:

```bash
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

When this flag is unset or false, normal production dialog behavior is unchanged.

When it is true, and live streaming diagnostics are enabled for `ISSUE`, `NAME`, or `CITY`, the ARI app still:

- starts the live RTP/STT proof path;
- logs RTP packet and PCM chunk diagnostics;
- runs the configured STT measurement/fallback path;
- logs timing and STT errors.

But the result is treated as a diagnostic result, not a customer answer. The call is finished with `diagnostic_call_finished` after measurement, without calling `apply_turn`.

## Diagnostic Events

Expected isolation events:

- `stt_live_diagnostics_isolated_enabled`
- `stt_live_diagnostics_result`
- `stt_live_diagnostics_dialog_bypass`
- `diagnostic_call_finished`

Existing RTP diagnostic events remain available:

- `stt_live_rtp_diagnostics_only_started`
- `stt_live_rtp_packet_received`
- `stt_live_pcm_chunk_created`
- `stt_live_rtp_packets_received_count`
- `stt_live_pcm_chunks_created_count`
- `stt_live_rtp_diagnostics_only_finished`
- `stt_live_rtp_diagnostics_result`

The terminal also prints `STT_LIVE_DIAGNOSTICS_ISOLATED_ENABLED` and `STT_LIVE_DIAGNOSTICS_DIALOG_BYPASS` for smoke-test visibility.

## Server Smoke Env

```bash
export STT_LIVE_STREAMING_ENABLED=true
export STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
export STT_LIVE_OPENAI_DISABLED=true
export STT_LIVE_STREAMING_FALLBACK_TO_BATCH=true
export STT_LIVE_STREAMING_STAGE_ALLOWLIST=ISSUE,NAME,CITY
export STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT=false
export STT_LIVE_STREAMING_TOPOLOGY=snoop_external_media_rtp
export STT_LIVE_RTP_BIND_HOST=0.0.0.0
export STT_LIVE_EXTERNAL_MEDIA_HOST=172.18.0.1
export STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

With this configuration, dummy or disabled OpenAI batch STT can be used during RTP smoke without incrementing business retry counters or producing misleading `SAFE_FINISH` outcomes.

## Preserved Contracts

- `PHONE` remains excluded from live streaming.
- `PHONE_CONFIRM` remains outside the default live allowlist.
- CITY validation is unchanged for normal calls.
- Russian-only caller-facing prompts are unchanged.
- Normal transfer, callback, after-hours, PHONE, PHONE_CONFIRM, and SAFE_FINISH behavior is unchanged when isolation is unset.
- NODE-014 local publish and `snoop_external_media_rtp` media path are preserved.

## Validation

Focused NODE-016 coverage proves:

- default behavior is unchanged when `STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED` is unset;
- isolated `rtp_diagnostics_only` plus empty batch STT does not increment business retry counters;
- isolated diagnostics do not transition `ISSUE`, `NAME`, or `CITY` through the business dialog;
- diagnostic events are emitted clearly;
- existing live streaming guards for `PHONE` and default `PHONE_CONFIRM` remain in place.
