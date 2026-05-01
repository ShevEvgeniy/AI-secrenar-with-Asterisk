# Runtime Notes

## Confirmed Runtime Behavior

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are active in `master`.
- Transfer after data collection is active in `master`.
- ARI continue is the established transfer mechanism.
- Partial publish failures are now classified with `reason` and `failed_step`.
- Startup can remain resilient when system-sounds prepublish partially fails.
- `user_transcribed` is tied to real downloaded caller audio artifacts instead of canned placeholder text.
- Missing stage and transfer media use controlled meaningful fallback phrases instead of `demo-congrats`.
- Real live transcription requires `TELEPHONY_STT_BACKEND` to be explicitly configured, for example `openai` or `whisper_api`.

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

## NODE-003 Runtime Notes

- NODE-003 replaced `demo-congrats` fallback use with controlled prompt/transfer fallbacks and non-demo built-ins.
- NODE-003 removed canned `user_transcribed` content from the live dialog path. Transcription events now identify the exact call id, stage, recording name, local audio path, byte size, and SHA-256. If no STT backend is configured, the event is logged as unavailable instead of fabricated.
- NODE-003 fixed the previously observed integrity problem where runtime logs showed transcribed text that did not match what the caller says they actually spoke.
- Next runtime validation should run one live smoke with a real STT backend configured.

## NODE-004 Runtime Notes

- Successful PHONE capture is now an immediate transfer boundary in the ARI dialog loop.
- Live smoke `1777640788.40` exposed an STT formatting case where the phone was transcribed as `920.032.0355`; PHONE parsing now accepts dotted numeric separators and normalizes that to `79200320355`.
- Validated live smoke `1777641576.42` confirmed ISSUE / NAME / CITY / PHONE each reached `user_transcribed=ok`.
- After PHONE in live smoke `1777641576.42`, events showed `play_transfer_phrase` followed by `transfer status=ok`.
- `pipeline_start`, `build_response`, and `reply.wav` did not occur after PHONE in the validated call.
- Expected event order after a valid PHONE transcript:

```text
user_transcribed(PHONE) -> play_transfer_phrase -> transfer(context=from-internal, extension=sales_real, priority=1)
```

- The generic response path must not run on that successful PHONE path, so `pipeline_start`, `build_response`, `publish`, and generic `playback` should be absent after valid PHONE collection.

## NODE-005 Runtime Notes

- NODE-005 keeps the current turn-based architecture and the NODE-004 post-PHONE transfer flow.
- Real-call recording is now stage-specific:

```text
ISSUE: max_duration=8s, max_silence=2s, wait_timeout=13s
NAME:  max_duration=4s, max_silence=1s, wait_timeout=8s
CITY:  max_duration=7s, max_silence=3s, wait_timeout=13s
PHONE: max_duration=14s, max_silence=4s, wait_timeout=21s
PHONE_CONFIRM: max_duration=4s, max_silence=2s, wait_timeout=9s
```

- Runtime events now include timing for prompt playback, record, download, STT, dialog decision, transfer phrase, and ARI continue transfer.
- `scripts/latency_report.py` now prints turn-based buckets: `prompt`, `record`, `download`, `stt`, `decision`, `transfer_phrase`, and `transfer`, while preserving the existing generic pipeline buckets.
- Operator overrides are available globally, by slot stages, or by exact stage. Stage-specific variables take precedence, for example `RECORD_PHONE_MAX_SILENCE_SECONDS`.
- No partial STT, streaming STT, realtime agent, or barge-in behavior was added in this node.
- NODE-005 patch 2 adds explicit confirmation only for PHONE. CITY re-asks on low-confidence input but has no confirmation substage.
- PHONE capture stores a digits-only value stripped from caller formatting, then asks `Правильно ли я записала ваш номер: <formatted_phone>?`.
- Transfer is allowed only after positive PHONE confirmation. Rejection or re-dictation returns to PHONE capture / replacement confirmation.
- If PHONE remains unconfirmed, runtime exits through `phone_unconfirmed_no_generic_pipeline` and must not run `pipeline_start`, `build_response`, `publish`, or generic `playback`.
- NODE-005 patch 3 relaxes CITY and PHONE turn-taking after live smoke showed cutoff regressions. CITY now requires at least 4 letters before advancing; PHONE requires a complete 10- or 11-digit run before `PHONE_CONFIRM`.
- PHONE now has the longest non-ISSUE end-of-speech profile to tolerate slow dictation and short intra-utterance pauses.
- Poor TTS stress/pronunciation on the phone prompt was observed during live smoke and recorded as secondary; do not mix it into the NODE-005 acceptance gate unless prompt wording changes.
- NODE-005 patch 4 varies only PHONE retry prompts. Reasons are `unclear`, `incomplete`, and `rejected`; the same PHONE retry phrase should not repeat twice in a row.
