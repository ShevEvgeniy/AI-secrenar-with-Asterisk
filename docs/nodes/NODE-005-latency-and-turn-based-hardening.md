# NODE-005 Latency And Turn-Based Hardening

## Goal

Reduce perceived latency inside the existing turn-based ARI flow without adding partial STT, streaming STT, realtime voice agent behavior, or barge-in.

The validated business path remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> play_transfer_phrase -> transfer(context=from-internal, exten=sales_real, priority=1)
```

## Latency Contributors Addressed

- Recording used one contour for every stage: `6s maxDurationSeconds`, `2s maxSilenceSeconds`, and a fixed `30s` RecordingFinished wait.
- Short slot stages waited longer than needed for tail silence.
- The RecordingFinished wait timeout was much larger than the configured recording envelope.
- Download, STT, dialog decision, transfer phrase, and ARI continue were not individually timed in runtime events.
- STT ran synchronously on the event loop; it is now dispatched through `asyncio.to_thread()` while preserving the same turn-based call order.

## Behavior Changes

Default real-call recording profiles are now stage-specific:

```text
ISSUE: max_duration=8s, max_silence=2s, wait_timeout=13s
NAME:  max_duration=4s, max_silence=1s, wait_timeout=8s
CITY:  max_duration=4s, max_silence=1s, wait_timeout=8s
PHONE: max_duration=5s, max_silence=1s, wait_timeout=9s
```

The ISSUE stage remains more tolerant because callers may describe the problem. NAME, CITY, and PHONE are shorter and more aggressive because they are slot-filling stages.

Operators can override the defaults:

```text
RECORD_MAX_DURATION_SECONDS
RECORD_MAX_SILENCE_SECONDS
RECORD_WAIT_TIMEOUT_SECONDS
RECORD_WAIT_PAD_SECONDS
RECORD_SLOT_MAX_DURATION_SECONDS
RECORD_SLOT_MAX_SILENCE_SECONDS
RECORD_SLOT_WAIT_TIMEOUT_SECONDS
RECORD_SLOT_WAIT_PAD_SECONDS
RECORD_ISSUE_MAX_DURATION_SECONDS
RECORD_NAME_MAX_SILENCE_SECONDS
RECORD_CITY_WAIT_TIMEOUT_SECONDS
RECORD_PHONE_WAIT_PAD_SECONDS
```

Stage-specific variables win over slot-level variables, which win over global variables.

## Tracing Added

Runtime `events.jsonl` now records `dur_ms` and stage details for:

- `play_prompt`
- `record_start`
- `record_done`
- `download_recording`
- `user_transcribed`
- `dialog_decision`
- `play_transfer_phrase`
- `transfer`

`scripts/latency_report.py` now reports:

```text
prompt, record, download, stt, decision, pipeline, tts, publish, transfer_phrase, transfer, total
```

For turn-based calls, repeated actions such as `play_prompt`, `record_done`, `download_recording`, `user_transcribed`, and `dialog_decision` are summed.

## Preserved Behavior

- NODE-004 successful PHONE transfer boundary is unchanged.
- The transfer target remains `from-internal,sales_real,1`.
- Generic pipeline work still does not run after successful PHONE capture.
- Publish hardening and controlled fallback media remain in place.
- Transcription integrity remains tied to the downloaded audio artifact and SHA-256 metadata.
- No realtime, partial STT, streaming STT, or barge-in behavior was introduced.

## Regression Coverage

Added focused coverage proving:

- ISSUE uses the longer recording profile.
- NAME, CITY, and PHONE use shorter slot profiles.
- Recording wait timeouts track the stage profile instead of fixed `30s`.
- The successful PHONE path still transfers and does not hang up or run the generic pipeline.
- Latency events include `dur_ms` for the hot-path stages.
- The latency report includes the new turn-based buckets.

## Validation

Run:

```text
python -m pytest tests/test_turn_latency_hardening.py tests/test_post_phone_transfer.py tests/test_latency_report.py tests/test_ari_client_record_params.py tests/test_transcription_integrity.py
```

Focused regression validation passed.

Full-suite validation was attempted with `python -m pytest`; it failed outside the NODE-005 surface because synth pipeline tests could not open `src/scripts/make_demo_audio.py`, and one runner events test attempted a blocked Hugging Face model fetch.

## Status

READY for live smoke validation.
