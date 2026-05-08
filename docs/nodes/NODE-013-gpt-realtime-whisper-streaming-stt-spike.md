# NODE-013 gpt-realtime-whisper Streaming STT Spike

## Goal

Evaluate whether an experimental OpenAI Realtime streaming STT path can reduce caller-perceived pauses compared with the current turn-based `whisper-1` file transcription path, without changing the business dialog state machine.

## Branch

```text
feat/node-013-gpt-realtime-whisper-streaming-stt-spike
```

## What Was Implemented

- Added `src/ai_secretary/stt/realtime_whisper.py`, an experimental WebSocket transcription adapter.
- Added feature flags:
  - `STT_STREAMING_ENABLED=false` by default.
  - `STT_STREAMING_PROVIDER=openai_realtime_whisper`.
  - `STT_STREAMING_MODEL=gpt-realtime-whisper`.
  - `STT_STREAMING_LANGUAGE=ru`.
  - `STT_STREAMING_SAMPLE_RATE=24000`.
  - `STT_STREAMING_FALLBACK_TO_BATCH=true`.
  - `STT_STREAMING_SESSION_MODEL=gpt-realtime`.
  - `STT_STREAMING_CHUNK_MS=200`.
  - `STT_STREAMING_TIMEOUT_SECONDS=30`.
- Integrated the adapter only through `_transcribe_audio_artifact_experimental`.
- Preserved the existing `_transcribe_audio_artifact` batch Whisper path.
- Preserved dialog contracts: transcript text still flows into `apply_turn`; no routing, transfer, callback, CITY, PHONE, PHONE_CONFIRM, or SAFE_FINISH behavior was changed.
- Added fallback to existing batch STT when streaming raises an error or the streaming provider is unsupported.

## Instrumentation

The experimental path emits:

- `stt_stream_session_started`
- `stt_stream_audio_chunk_sent`
- `stt_stream_first_delta_received`
- `stt_stream_final_received`
- `stt_stream_error`
- `stt_stream_fallback_to_batch`

Transcript details include:

- `stt_stream_latency_first_delta_ms`
- `stt_stream_latency_final_ms`
- `stt_stream_total_audio_ms`
- `stt_stream_text`
- `stt_batch_baseline_latency_ms` when batch is used as default or fallback.

## What Was Measured

Controlled offline tests exercised the streaming adapter with a local 24 kHz mono PCM WAV and a fake WebSocket server event stream. This verifies timing instrumentation and event plumbing without requiring live OpenAI or ARI media access.

Measured controlled smoke:

```text
streaming first delta: 37 ms
streaming final: 81 ms
streamed audio duration: 200 ms
batch fallback baseline: >= 0 ms in fixture mode
```

These numbers are not production latency claims. They prove the metrics are emitted and can be collected. A real network/audio smoke is still required to evaluate actual caller-perceived delay.

## Baseline Latency

The current default path remains:

```text
recording finish -> recording download -> whisper-1 request -> text ready
```

In test fixture mode the measured batch baseline is effectively local execution time. NODE-012 live observations remain the practical baseline for caller pause pressure:

- ISSUE record window around 8-9s.
- NAME record window around 6s.
- CITY record window around 10s.
- PHONE intentionally conservative.

## Streaming Latency

The implemented spike path is:

```text
stored WAV artifact -> chunked WebSocket append -> first transcript delta -> final transcript
```

This branch does not yet tap live ARI media before recording completion, so it validates the OpenAI Realtime transcription adapter and metrics but does not yet remove the Asterisk recording wait from caller-perceived latency.

## Quality Notes For Russian Speech

- The adapter sends `language=ru`.
- The adapter supports a prompt field, but this integration currently keeps prompt behavior unchanged at the dialog level and does not introduce routing or validation decisions inside the realtime model.
- Russian quality was not validated against real caller audio in this spike branch.
- A production decision should test real Russian call audio, regional/city/address vocabulary, and noisy telephony audio.

## Recommendation

Continue spike.

Reason:

- The feature-flagged adapter and fallback are in place.
- Default behavior remains unchanged with `STT_STREAMING_ENABLED=false`.
- Metrics are now available for first delta, final transcript, streamed audio duration, fallback, and batch baseline.
- The current implementation streams stored WAV artifacts after recording download, so it cannot yet prove caller-perceived pause reduction.
- The next useful step is a true live ARI media source or external media bridge that feeds 24 kHz PCM, PCMU, or PCMA chunks while the caller is speaking.

## Validation

Passed:

```text
.venv\Scripts\python.exe -m pytest tests\test_transcription_integrity.py
9 passed

.venv\Scripts\python.exe -m pytest tests\test_dialog_flow.py tests\test_turn_latency_hardening.py tests\test_post_phone_transfer.py
80 passed

.venv\Scripts\python.exe -m pytest
140 passed, 6 failed
```

Not run:

- Live OpenAI Realtime smoke.
- Live Asterisk/ARI streaming media smoke.

Broad-suite failures are existing environment-dependent cases:

- `src/scripts/make_demo_audio.py` is missing for synth pipeline tests.
- Hugging Face model access is unavailable for one RAG-backed runner test.

## Safety Notes

- `STT_STREAMING_ENABLED=false` leaves the current batch path active.
- Streaming errors fall back to the existing batch path when `STT_STREAMING_FALLBACK_TO_BATCH=true`.
- PHONE conservative behavior and PHONE_CONFIRM static fast path are unchanged.
- CITY validation and English filler rejection remain in the dialog layer.
- Transfer still depends on `phone_confirmed=true` and no missing required fields.
