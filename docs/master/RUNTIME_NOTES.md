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

- Turn-taking contour is stabilized for the current live flow.
- NAME no longer breaks the whole flow.
- NAME playback barrier is in place.
- PHONE and PHONE_CONFIRM work in live flow.
- Confirmation prompt speaks the phone number as spoken digits.
- Live validation `1777717705.10` reached:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- Runtime transfer target remains:

```text
context=from-internal
extension=sales_real
priority=1
```

- NODE-005 solved the latency and turn-taking contour for the current flow, but NAME quality still needs improvement in NODE-006.

## NODE-006 Runtime Notes

- NAME capture quality is hardened without changing the overall call architecture.
- NAME STT explicitly uses Russian language and Russian-name prompt context.
- Bounded post-STT normalization for Russian names, patronymics, and common conversational forms is present.
- NAME prompt wording is simplified to:

```text
Назовите, пожалуйста, ваше имя.
```

- NAME playback barrier remains in place, so NAME recording no longer starts over prompt playback.
- Live validation `1777721580.0` recognized NAME as `Иван Семёнович` and reached:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- NODE-006 does not introduce multi-department routing.

## NODE-007 Runtime Notes

- Bounded department intent routing is working for:
  - sales;
  - accounting;
  - delivery.
- Routing remains deterministic and debuggable.
- The validated collection flow is preserved:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

- Unclear intent remains bounded and routes to the configured default department.
- Final transfer phrase is department-specific:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

- Live validation references:
  - `1777725117.4`: sales intent -> `department=sales`, `context=from-internal`, `extension=sales_real`, `priority=1`.
  - `1777726120.10`: accounting intent -> accounting phrase resolved and played -> `department=accounting`, `context=from-internal`, `extension=accounting`, `priority=1`.
  - `1777726440.12`: delivery intent -> delivery phrase resolved and played -> `department=delivery`, `context=from-internal`, `extension=delivery`, `priority=1`.

## NODE-008 Runtime Notes

- Immediate transfer requests no longer bypass required data collection.
- Mandatory data before live transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-aware responses are implemented when the caller asks for immediate transfer.
- Bounded `INTENT_CLARIFY` is implemented for unclear or tied department intent.
- Bounded retry policy is implemented by stage:
  - ISSUE retries, then moves to `INTENT_CLARIFY`;
  - `INTENT_CLARIFY` retries, then defaults to the configured department;
  - NAME/CITY/PHONE use bounded retries, then `SAFE_FINISH`;
  - PHONE_CONFIRM has its own bounded policy and is not cut off by generic global turn limits.
- PHONE and PHONE_CONFIRM are effectively governed by stage-local policy rather than prematurely terminated by generic accumulated turn cutoff.
- `INTENT_CLARIFY` timeout and empty outcomes are handled as normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` is terminal/non-transfer and supports reason-based spoken phrases before hangup:
  - `missing_required_data`;
  - `intent_not_resolved`;
  - `phone_not_confirmed`.

## NODE-009 Runtime Notes

- Bounded working-hours vs after-hours behavior is implemented.
- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped.
- Mandatory data collection is still enforced before after-hours completion:
  - issue;
  - name;
  - city;
  - phone;
  - `phone_confirmed=true`.
- Department-specific after-hours phrases are implemented for:
  - sales;
  - accounting;
  - delivery.
- After-hours phrase playback completes before hangup.
- Transfer is explicitly skipped and logged in after-hours mode.
- Opening prompt is now:

```text
Здравствуйте. Меня зовут Анна. Я виртуальный секретарь. По какому вопросу вы обращаетесь?
```

- After-hours phrases now end with:

```text
Спасибо за звонок. До свидания.
```

- Versioned after-hours system sounds are used for refreshed wording:

```text
sound:ai_secretary/_system/after_hours_sales_v2
sound:ai_secretary/_system/after_hours_accounting_v2
sound:ai_secretary/_system/after_hours_delivery_v2
```

## NODE-010 Runtime Notes

- Bounded local callback persistence is implemented.
- Persistence format is JSONL, one flat JSON object per line.
- Production path:

```text
data/storage/callbacks/callback_records.jsonl
```

- Persisted schema includes:
  - `record_id`;
  - `call_id`;
  - `timestamp`;
  - `department`;
  - `issue`;
  - `name`;
  - `city`;
  - `phone`;
  - `outcome_type`;
  - `outcome_reason`.
- Implemented trigger points:
  - `after_hours_callback`;
  - `safe_finish`.
- After-hours callback records are persisted after after-hours transfer skip and before final hangup.
- SAFE_FINISH records are persisted with available partial data and terminal reason.
- Persistence is fail-soft and does not crash call flow.
- Logging includes:
  - `persistence_attempt`;
  - `persistence_success`;
  - `persistence_failure`.
- Live validation confirmed callback persistence succeeded with:

```text
outcome_type=after_hours_callback
outcome_reason=mode_override
record_id=f0cff987b252b77c
path=data/storage/callbacks/callback_records.jsonl
```

## NODE-005 Runtime Notes

- NODE-005 keeps the current turn-based architecture and the NODE-004 post-PHONE transfer flow.
- Real-call recording is now stage-specific:

```text
ISSUE: max_duration=8s, max_silence=2s, wait_timeout=13s
NAME:  max_duration=6s, max_silence=2s, wait_timeout=11s
CITY:  max_duration=7s, max_silence=3s, wait_timeout=13s
PHONE: max_duration=14s, max_silence=4s, wait_timeout=21s
PHONE_CONFIRM: max_duration=6s, max_silence=3s, wait_timeout=12s
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
- NODE-005 patch 5 keeps `phone_formatted` for debug/display but feeds PHONE_CONFIRM TTS with `phone_spoken`, a Russian digit-by-digit string, to avoid TTS skipping symbolic formatting such as `+7 920 032-03-55`.
- NODE-005 patch 6 adds an explicit `PlaybackFinished` barrier before PHONE_CONFIRM recording, then a default `400 ms` guard delay. `PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS` defaults to `15`.
- NODE-005 patch 6 expands PHONE_CONFIRM capture to `6s/3s/12s`, handles meta-repair phrases neutrally, adds a NAME garbage guard, and forces the fixed PHONE system prompt to `prompt_4_v2` with built-in stress preprocessing for `связи -> св+язи`.
- NODE-005 patch 7 fixes NAME retry-loop regression. NAME retries are reason-based (`unclear`, `junk`, `meta_repair`), varied without immediate repetition, tolerant of short valid Russian names, and capped at 3 retries before advancing with `name="клиент"` and `name_unavailable=true`.
- NODE-005 patch 8 fixes PHONE-stage acceptance/repair. Comma/dot grouped STT such as `920, 0.32, 0.3, 0.55` normalizes to `9200320355`, PHONE-stage meta-repair uses `meta_repair`, dynamic PHONE retry prompts are synthesized/published per call instead of replaying `prompt_4_v2`, and NAME now rejects short English filler such as `Yep.`.
- NODE-005 patch 9 adds a NAME playback barrier for both base NAME prompt and dynamic NAME retry prompts. NAME recording starts only after `PlaybackFinished` plus `NAME_GUARD_DELAY_MS`, default `400 ms`; NAME timing is now `6s/2s/11s`.
