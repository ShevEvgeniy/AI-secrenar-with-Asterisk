# Decisions

## Accepted

### Master-Driven Workflow

- `master` is the source-of-truth branch.
- Architecture, status, planning, and project coordination are handled through master-layer documentation.
- Implementation work must be isolated to focused node branches.
- One node equals one task, one branch, and one execution cycle.

### Documentation Layout

- Master docs live under `docs/master/`.
- Node docs live under `docs/nodes/`.

### Scope Discipline

- Do not broadly refactor.
- Do not mix multiple concerns in one node.
- Always preserve tracing and logging.

## Completed Technical Direction

NODE-001 completed the real transfer route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

The existing ARI continue transfer flow is reused. The validated runtime target is:

```text
context=from-internal
extension=sales_real
priority=1
```

Live smoke validation confirmed staged prompts, user speech transcription, transfer phrase playback, and `transfer status=ok`.

## Publish Failure Handling

NODE-002 completed publish hardening. Partial publish failures must remain explicit and diagnosable rather than silently degrading startup or call behavior.

Accepted runtime behavior:

- Startup may continue under partial system-sounds prepublish failure.
- Publish failures must include `reason` and `failed_step`.
- Per-call publish failures must remain visible in traces/logs.
- Existing transfer behavior must continue when fallback media is used.

NODE-002 validation observed SSH timeout to `92.118.85.117:22` while publishing `prompt_3` and transfer system sounds. The listener still reached `READY_WAITING_FOR_CALLS`, and transfer completed to `from-internal,sales_real,1`.

## Transcription Integrity And Fallback Phrases

NODE-003 completed transcription integrity and meaningful fallback phrase handling.

Accepted runtime behavior:

- `user_transcribed` must not be sourced from canned placeholder text.
- Transcription must be tied to the real downloaded caller audio artifact.
- Artifact identity must be traceable through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
- Stale local turn artifacts must be explicitly discarded and logged.
- If no STT backend is configured, transcription must be logged as unavailable instead of fabricated.
- Fallback media must not degrade to `demo-congrats`.
- Stage and transfer fallback paths must use controlled meaningful fallback phrases.

Real live transcription depends on `TELEPHONY_STT_BACKEND` being explicitly configured, for example `openai` or `whisper_api`.

## Turn-Based Latency And Confirmation Flow

NODE-005 completed latency and turn-based hardening for the current dialog flow.

Accepted runtime behavior:

- The current successful live path is:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- NAME prompt playback must complete before NAME recording starts.
- PHONE and PHONE_CONFIRM must work in live flow.
- PHONE_CONFIRM must speak the phone number as spoken digits, not symbolic formatting.
- Successful transfer must continue to:

```text
context=from-internal
extension=sales_real
priority=1
```

NODE-005 validation confirmed transfer with `status=ok` for live call `1777717705.10`. NAME quality still needs a separate focused follow-up in NODE-006.

## Name Capture And Normalization

NODE-006 completed NAME capture and normalization hardening without changing the overall call architecture.

Accepted runtime behavior:

- NAME transcription uses Russian language and Russian-name prompt context.
- NAME prompt wording is:

```text
Назовите, пожалуйста, ваше имя.
```

- Bounded post-STT normalization may handle Russian names, patronymics, and common conversational forms.
- NAME playback barrier remains in place so NAME recording does not start over prompt playback.
- The validated end-to-end flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

NODE-006 validation confirmed recognized NAME `Иван Семёнович` for live call `1777721580.0` and transfer with `status=ok`. Multi-department routing remains out of scope until NODE-007.
## Department Intent Routing

NODE-007 completed bounded department intent routing and department-specific transfer phrases.

Accepted runtime behavior:

- Department intent routing is deterministic and debuggable.
- Supported departments are:
  - sales;
  - accounting;
  - delivery.
- Unclear intent remains bounded and routes to the configured default department.
- The collection flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

- Final transfer phrases are department-specific:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

NODE-007 live validation confirmed sales, accounting, and delivery routing with department-specific prompts.

## Intent Clarification And Mandatory Data Capture

NODE-008 completed mandatory data gating, stage-aware immediate-transfer responses, bounded intent clarification, and terminal SAFE_FINISH behavior.

Accepted runtime behavior:

- Immediate transfer requests must not bypass required data collection.
- Mandatory data before live transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-aware responses are used when the caller asks for immediate transfer.
- `INTENT_CLARIFY` is bounded for unclear or tied department intent.
- ISSUE retries, then moves to `INTENT_CLARIFY`.
- `INTENT_CLARIFY` retries, then defaults to the configured department.
- NAME/CITY/PHONE use bounded retries, then `SAFE_FINISH`.
- PHONE_CONFIRM has its own bounded policy and must not be cut off by generic global turn limits.
- `INTENT_CLARIFY` timeout and empty outcomes are normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` is terminal/non-transfer and supports reason-based phrases for `missing_required_data`, `intent_not_resolved`, and `phone_not_confirmed`.

NODE-008 focused regression passed with `42 passed in 2.73s`.

## Business Hours And After-Hours Handoff

NODE-009 completed bounded working-hours vs after-hours behavior.

Accepted runtime behavior:

- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped.
- Mandatory data collection is still enforced before after-hours completion:
  - issue;
  - name;
  - city;
  - phone;
  - `phone_confirmed=true`.
- Department-specific after-hours phrases exist for sales, accounting, and delivery.
- After-hours phrase playback must complete before hangup.
- Transfer skip must be explicit and logged in after-hours mode.
- Versioned after-hours system sounds must be used for refreshed wording:

```text
sound:ai_secretary/_system/after_hours_sales_v2
sound:ai_secretary/_system/after_hours_accounting_v2
sound:ai_secretary/_system/after_hours_delivery_v2
```

NODE-009 validation recorded `21 passed` for wording/static-sound follow-up and broader focused result `56 passed`.

## Callback Capture And Persistence

NODE-010 completed bounded local callback persistence.

Accepted runtime behavior:

- Callback persistence format is JSONL, one flat JSON object per line.
- Production path is:

```text
data/storage/callbacks/callback_records.jsonl
```

- Persisted schema includes `record_id`, `call_id`, `timestamp`, `department`, `issue`, `name`, `city`, `phone`, `outcome_type`, and `outcome_reason`.
- Records are written for:
  - `after_hours_callback`;
  - `safe_finish`.
- After-hours callback records are persisted after after-hours transfer skip and before final hangup.
- SAFE_FINISH records are persisted with available partial data and terminal reason.
- Persistence is fail-soft and must not crash call flow.
- Persistence logging includes `persistence_attempt`, `persistence_success`, and `persistence_failure`.

NODE-010 live validation confirmed callback persistence with `outcome_type=after_hours_callback`, `outcome_reason=mode_override`, and `record_id=f0cff987b252b77c`.

## Normal Call Latency And Silence Hardening

NODE-011 completed normal-call latency and silence hardening at MVP level.

Accepted runtime behavior:

- Normal working-hours flow remains:

```text
ISSUE -> INTENT_CLARIFY if needed -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Mandatory data before transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-level latency instrumentation must remain available for normal calls.
- PHONE_CONFIRM must use the static fast path when `phone_digits` are available and must not require per-call dynamic TTS/publish on the normal path.
- PHONE remains conservative and excluded from TALK_DETECT early stop with `phone_digit_safety_skip`.
- ISSUE and INTENT_CLARIFY prompt playback barriers must remain in place before recording.
- TALK_DETECT early-stop diagnostics are useful but `recording_early_stop_used` is not yet required as a closure gate for NODE-011.

NODE-011 final live smoke `1778089554.24` passed at MVP level: sales intent was matched from captured ISSUE text, required fields were collected, PHONE_CONFIRM fast path was used, and transfer to `sales_real` completed only after `phone_confirmed=true`.

Remaining short-slot pause smoothing is deliberately moved to NODE-012 and must not change PHONE digit safety, business logic, transfer/callback/after-hours contracts, or SAFE_FINISH behavior.

## Short-Slot Turn-Taking Polish

NODE-012 completed short-slot turn-taking polish for the current bounded scope.

Accepted runtime behavior:

- CITY transcript validation may accept compound region/city/address answers when a valid city or region anchor is present.
- CITY must reject English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye`.
- Caller-facing dialog remains Russian-only.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- PHONE remains conservative with `phone_digit_safety_skip`.
- Transfer still occurs only after `phone_confirmed=true` and no required fields are missing.

NODE-012 final live smoke `1778258401.18` passed for normal sales flow with compound CITY/address. Remaining pause reduction for CITY and PHONE should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike.
