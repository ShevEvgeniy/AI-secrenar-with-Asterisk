# Runtime Notes

## Confirmed Runtime Behavior

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are active in `master`.
- Transfer after data collection is active in `master`.
- ARI continue is the established transfer mechanism.
- Partial publish failures are now classified with `reason` and `failed_step`.
- Startup can remain resilient when system-sounds prepublish partially fails.

## Transfer Route Target

The current target route is:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

The AI secretary ARI handoff target is:

```text
context: from-internal
extension: sales_real
priority: 1
```

Runtime environment defaults now point to this target. Operators may still set these explicitly:

```text
TRANSFER_CONTEXT=from-internal
TRANSFER_EXTEN=sales_real
TRANSFER_PRIORITY=1
```

Required Asterisk dialplan route:

```asterisk
[from-internal]
exten => sales_real,1,NoOp(AI secretary sales real transfer)
 same => n,Dial(PJSIP/78007074193@thermo-trunk-endpoint,60,D(ww52144))
 same => n,Hangup()
```

NODE-001 live validation completed successfully with ARI continue to:

```text
context=from-internal
extension=sales_real
priority=1
```

## Observability Requirements

Preserve existing tracing and logging. The transfer route node should leave enough logs to identify:

- data collection completion;
- transfer decision;
- selected transfer target;
- ARI continue handoff;
- dialplan context and extension reached;
- outbound trunk endpoint used;
- DTMF dispatch result.

## Validation Notes

- During live validation, MicroSIP using the wrong Windows input device produced a false negative for dialog capture.
- Selecting the correct Windows microphone fixed live ISSUE / NAME / CITY / PHONE capture.
- The validated transfer path is merged into `master`.

## NODE-002 Runtime Notes

- During startup, `prompt_3` and transfer system sounds failed to publish because SSH to `92.118.85.117:22` timed out.
- Despite that partial prepublish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- During the live call, fallback media was used instead of missing `prompt_3` and the missing transfer phrase.
- Transfer still completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

## Open Runtime Follow-Ups

- NODE-003 replaced `demo-congrats` fallback use with controlled prompt/transfer fallbacks and non-demo built-ins.
- NODE-003 removed canned `user_transcribed` content from the live dialog path. Transcription events now identify the exact call id, stage, recording name, local audio path, byte size, and SHA-256. If no STT backend is configured, the event is logged as unavailable instead of fabricated.
