# NODE-029 Diagnose Empty Transcript Audio Payload Quality

## Status

CLOSED as local diagnostic implementation and analysis. No live diagnostic was run.

NODE-029 explains the NODE-028 `empty_transcript` result without enabling production gateway STT. The controlled live smoke in NODE-028 used a synthetic silent 24 kHz mono WAV, so the likely root cause is unsuitable audio payload content rather than gateway auth, gateway-to-OpenAI transport, or response parsing.

## Goal

Diagnose why the controlled live gateway/OpenAI path succeeds at transport level but returns:

```text
transcript_present=false
fallback_reason=empty_transcript
```

Primary questions:

- Is the audio payload valid speech-bearing audio or silence/near-silence?
- Is the audio format valid for the gateway/OpenAI Realtime path?
- Is chunking/finalization correct?
- Is OpenAI Realtime returning transcript events that the gateway/helper fails to parse?
- What is the minimal next fix or experiment?

## Method

This node was local-only. It inspected and updated:

```text
src/ai_secretary/stt/realtime_measurement.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/gateway_adapter_smoke.py
tests/test_realtime_measurement.py
tests/test_realtime_gateway.py
```

The node also checked current official OpenAI Realtime docs. The documented input transcription trigger is audio written with `input_audio_buffer.append` and committed with `input_audio_buffer.commit`; transcript output is reported on `conversation.item.input_audio_transcription.completed`. The existing gateway flow already sends append and commit events, so NODE-029 added diagnostics to prove whether those events and transcript-bearing event types are observed.

No Kamatera gateway process was started. No Asterisk runtime or systemd profile was modified. No caller-facing live call was run.

## Implemented Diagnostics

Audio payload diagnostics now include:

```text
audio_payload_valid
audio_duration_ms
audio_sample_rate_hz
audio_channels
audio_sample_width
audio_codec
audio_total_bytes
audio_chunk_count
audio_chunk_bytes_min
audio_chunk_bytes_max
audio_chunk_bytes_avg
audio_first_chunk_bytes
audio_last_chunk_bytes
audio_rms
audio_peak
audio_non_silent_ratio
audio_empty
audio_too_short
audio_near_silent
audio_malformed
audio_unsupported
audio_quality_classification
```

The classification is one of:

```text
valid_speech_candidate
too_short
near_silent
malformed
unsupported_format
unknown
```

Response diagnostics now include:

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
error_event_seen
input_audio_buffer_commit_sent
timeout_observed
close_status
```

The adapter smoke helper surfaces these fields in its redacted JSON report. Transcript text remains suppressed by default.

## Local Diagnostic Evidence

Focused tests added:

- A 1 second silent 24 kHz mono 16-bit PCM WAV is classified as `near_silent`, with `audio_rms=0`, `audio_peak=0`, and `audio_non_silent_ratio=0`.
- Malformed bytes are classified as `malformed`.
- Unsupported WAV shape, for example stereo 8 kHz, is classified as `unsupported_format`.
- A fake Realtime event stream records session events plus `conversation.item.input_audio_transcription.completed`, proving the gateway now exposes event-type counts and transcript-event flags.
- The gateway reports `input_audio_buffer_commit_sent=true` when the finalization event is sent.

NODE-028 already documented its live smoke audio as:

```text
temporary_audio=node028_silence_24k.wav
temporary_audio_format=mono 16-bit PCM 24000 Hz, 3 seconds
chunks_sent=15
transcript_present=false
fallback_reason=empty_transcript
```

Given the new classifier, that payload would be a valid transport-format WAV but `audio_quality_classification=near_silent`, with no speech-bearing content expected.

## Diagnosis

```text
audio_payload_valid=true
audio_duration_ms=3000 inferred from NODE-028
audio_sample_rate_hz=24000 inferred from NODE-028
audio_channels=1 inferred from NODE-028
audio_sample_width=2 inferred from NODE-028
audio_total_bytes=not_available_from_NODE_028_report
audio_chunk_count=15 inferred from chunks_sent
audio_rms=0 inferred from documented synthetic silence
audio_peak=0 inferred from documented synthetic silence
audio_non_silent_ratio=0 inferred from documented synthetic silence
audio_quality_classification=near_silent
gateway_auth=ok from NODE-028
openai_realtime_from_gateway=ok from NODE-028
chunks_sent=15 from NODE-028
transcript_event_seen=unknown for NODE-028 because old gateway did not count event types
transcript_present=false
transcript_text_logged=false
fallback_reason=empty_transcript
likely_root_cause=silent synthetic audio artifact unsuitable for transcription
```

Transport and auth were already proven in NODE-028. The Realtime request protocol is not the leading suspect for that specific result because audio was accepted, chunks were sent, OpenAI connection/session creation succeeded, and the input had no speech.

## Cleanup Verification

Because NODE-029 was local-only:

```text
live_diagnostic_run=false
gateway_started=false
gateway_stopped_after_diagnostic=not_started
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed=false
systemd_profile_changed=false
asterisk_openai_key_present_after_diagnostic=no live diagnostic run
real_secrets_committed=false
```

NODE-028 remains the latest live cleanup evidence:

```text
gateway_process_after_smoke=stopped
port_8080_after_smoke=not_listening
OPENAI_API_KEY=<absent on Asterisk>
```

## Validation

Focused STT diagnostic suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py
31 passed
```

Required NODE-029 suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
114 passed
```

Pre-commit whitespace validation:

```text
git diff --check
passed
```

## NODE-029 Result

```text
node_status=diagnostic closed
audio_payload_diagnostics_added=true
response_event_diagnostics_added=true
live_diagnostic_run=false
gateway_started=false
gateway_stopped_after_diagnostic=not_started
adapter_or_measurement_path_used=local pytest gateway/measurement diagnostics
audio_quality_classification=near_silent for NODE-028 artifact by documented method
transcript_event_seen=unknown for NODE-028, now instrumented for future runs
transcript_present=false
transcript_text_logged=false
likely_root_cause=silent synthetic WAV artifact, not a speech-bearing payload
next_node_recommendation=run a controlled non-sensitive speech WAV diagnostic through the same gateway path, then productionize only in a separate node
production_gateway_stt_enabled=false
default_runtime_behavior_changed=false
business_dialog_changed=false
systemd_profile_changed=false
asterisk_openai_key_present_after_diagnostic=no live diagnostic run
real_secrets_committed=false
```

## Known Limitations

- NODE-029 did not rerun Kamatera live diagnostics because local inspection already explained the NODE-028 silent-audio result.
- NODE-028 did not record event-type counts, so `transcript_event_seen` for that historical run remains unknown.
- The new diagnostics prove payload quality and parser visibility for future runs; they do not prove transcript quality on real speech until a non-sensitive speech candidate is sent.
- A tone fixture can satisfy amplitude checks but is not speech; the next useful live experiment should use non-sensitive spoken Russian test audio.

## Next Recommendation

Run one controlled non-caller-facing diagnostic with a short non-sensitive Russian speech WAV, keeping `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` and `STT_GATEWAY_LOG_TRANSCRIPT=false`. Expected decision point: if the speech WAV returns transcript events, close the empty-transcript issue as artifact quality; if speech is valid and transcript events are still absent, inspect Realtime session/update/request schema and event handling next.
