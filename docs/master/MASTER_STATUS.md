# Master Status

## Current State

- Branch: `master`
- Source-of-truth commit: `df69f3222cec78a5f7afe2ef09b413f7ab5f3d83`
- Source-of-truth commit message: `Use stage-specific prompts and transfer after data collection`
- Repository location: `C:\Projects\AI-secrenar-with-Asterisk`
- Master docs initialized: yes.
- Latest completed node branch: `feat/node-007-intent-routing-and-department-transfer`
- Latest completed node commit: `5911c19`

## Confirmed Working

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are already in `master`.
- Transfer flow via ARI continue is already in `master`.
- Publish pipeline remains resilient under partial publish failure.
- Publish failures now include explicit classification, including `reason` and `failed_step`.
- `user_transcribed` is no longer sourced from canned placeholder text.
- Transcription is tied to the real downloaded caller audio artifact.
- Transcription artifact identity is traceable through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
- Stale local turn artifacts are explicitly discarded and logged.
- Fallback media no longer degrades to `demo-congrats`.
- Stage and transfer fallback paths now use controlled meaningful fallback phrases.
- Successful PHONE capture now leads to `play_transfer_phrase -> transfer`.
- The generic reply path after PHONE is no longer taken on the validated live call.
- Turn-based real-call recording now uses stage-specific contours to reduce dead air.
- PHONE now requires explicit confirmation before validated completion and transfer.
- Runtime events now trace prompt, record, download, STT, decision, transfer phrase, and transfer latency.
- Turn-taking contour is stabilized for the current flow.
- NAME no longer breaks the whole flow.
- NAME playback barrier is in place.
- PHONE and PHONE_CONFIRM work in live flow.
- Confirmation prompt now speaks the phone number as spoken digits.
- NAME capture quality is hardened without changing the overall call architecture.
- STT for NAME explicitly uses Russian language and Russian-name prompt context.
- Bounded post-STT normalization for Russian names, patronymics, and common conversational forms is present.
- NAME prompt wording is simplified to: `Назовите, пожалуйста, ваше имя.`
- Bounded department intent routing works for sales, accounting, and delivery.
- Routing remains deterministic and debuggable.
- Final transfer phrase is department-specific.
- NODE-001 live smoke validation passed:
  - stage prompts progressed correctly;
  - user speech was transcribed for ISSUE / NAME / CITY / PHONE;
  - transfer phrase played;
  - transfer completed with `status=ok` to `from-internal,sales_real,1`.

## Completed Nodes

NODE-001 completed the real sales transfer route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

NODE-002 completed publish hardening:

```text
publish failures -> explicit reason and failed_step -> resilient startup/per-call diagnostics
```

NODE-003 completed transcription integrity and meaningful fallback phrases:

```text
real caller audio artifact -> traceable transcription metadata -> no fabricated user_transcribed text
```

NODE-004 restored the post-PHONE transfer invariant:

```text
valid PHONE transcript -> phone_digits saved -> transfer phrase -> ARI continue to from-internal,sales_real,1
```

NODE-005 hardens the turn-based latency contour:

```text
ISSUE tolerant recording -> NAME playback barrier and relaxed recording -> CITY relaxed recording -> PHONE slow-dictation recording -> PHONE_CONFIRM -> explicit latency buckets
```

NODE-006 hardens NAME capture and normalization:

```text
NAME -> language=ru and Russian-name STT prompt -> bounded normalization -> stable flow continues
```

NODE-007 adds bounded department intent routing:

```text
topic intent -> sales/accounting/delivery/default -> explicit transfer target
```

## Validation Notes

- A false negative occurred during live validation because MicroSIP was using the wrong Windows input device.
- Selecting the correct Windows microphone fixed live dialog capture.
- NODE-001 is merged into `master`.
- NODE-002 is merged into `master`.
- NODE-003 is merged into `master`.
- NODE-004 is merged into `master`.
- NODE-005 is merged into `master`.
- NODE-006 is merged into `master`.
- NODE-007 is merged into `master`.
- During NODE-002 validation, SSH to `92.118.85.117:22` timed out while publishing `prompt_3` and transfer system sounds.
- Despite the partial publish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- Fallback media was used during the live call for missing `prompt_3` and transfer phrase.
- Transfer still completed successfully to `from-internal,sales_real,1`.

## Resolved Follow-Up Issues

- NODE-003 fixed the integrity problem where runtime logs showed transcribed text that did not match what the caller says they actually spoke.
- If no STT backend is configured, transcription is logged as unavailable instead of fabricated.
- Fallback media now uses controlled meaningful fallback phrases instead of `demo-congrats`.
- NODE-004 prevents the generic reply pipeline from running after successful PHONE capture.
- NODE-004 fixed the runtime root cause where the PHONE parser rejected dotted separators from STT output.
- NODE-005 reduces avoidable recording tail latency for NAME, CITY, and PHONE and replaces fixed `30s` recording waits with stage-profile-based waits.
- NODE-005 extends `scripts/latency_report.py` with turn-based hot-path buckets.
- NODE-005 patch 2 applies explicit confirmation only to PHONE. CITY simply re-asks when not confidently accepted.
- NODE-005 patch 2 prevents unconfirmed PHONE from falling through to the generic reply pipeline.
- NODE-005 patch 3 responds to live turn-taking regression: CITY and PHONE end-of-speech were too aggressive, so CITY now uses `7s/3s/13s`, PHONE uses `14s/4s/21s`, and PHONE_CONFIRM uses `4s/2s/9s`.
- NODE-005 patch 3 adds minimum completion floors: CITY requires at least 4 letters, and PHONE requires a complete 10- or 11-digit run before confirmation.
- NODE-005 patch 4 varies PHONE retry prompts by reason (`unclear`, `incomplete`, `rejected`) and prevents immediate repeated retry phrasing.
- NODE-005 patch 5 fixes PHONE_CONFIRM prompt construction so TTS receives spoken digit words while formatted phone text remains available for logs/debug.
- NODE-005 patch 6 fixes PHONE_CONFIRM sequencing with an explicit `PlaybackFinished` barrier plus `400 ms` guard, expands PHONE_CONFIRM timing to `6s/3s/12s`, adds meta-repair handling, adds NAME garbage gating, and regenerates the fixed PHONE prompt as `prompt_4_v2` with `связи -> св+язи` stress preprocessing.
- NODE-005 patch 7 fixes NAME retry-loop regression with reason-based varied NAME prompts, short Russian-name tolerance, NAME meta-repair handling, and a 3-retry bound that advances with `name_unavailable=true`.
- NODE-005 patch 8 fixes PHONE-stage normalization for comma/dot grouped dictation, handles PHONE-stage meta-repair directly, makes dynamic PHONE retry prompts drive playback instead of fixed `prompt_4_v2`, and rejects short English NAME filler such as `Yep.`.
- NODE-005 patch 9 fixes NAME prompt/record overlap with an explicit `PlaybackFinished` barrier plus `400 ms` guard for base NAME and dynamic NAME retry prompts, and relaxes NAME recording to `6s/2s/11s`.
- NODE-005 live smoke confirmed the current full flow reaches `ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer`.
- NODE-006 improves NAME quality and stability but does not introduce multi-department routing.
- NODE-007 validates department routing and department-specific transfer prompts for sales, accounting, and delivery.

## NODE-004 Live Smoke

- `call_id`: `1777641576.42`
- ISSUE / NAME / CITY / PHONE each reached `user_transcribed=ok`.
- After PHONE, events showed `play_transfer_phrase` followed by `transfer status=ok`.
- Transfer completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

- `pipeline_start`, `build_response`, and `reply.wav` did not occur after PHONE in the validated call.

## NODE-005 Validation

- Focused regression suite passed:

```text
python -m pytest tests/test_dialog_flow.py tests/test_post_phone_transfer.py tests/test_turn_latency_hardening.py tests/test_latency_report.py
```

- Full local suite attempted:

```text
python -m pytest
```

Result: 46 passed, 6 failed. Failures were outside NODE-005: missing `src/scripts/make_demo_audio.py` for synth pipeline tests, and a blocked Hugging Face model fetch in `test_events_and_artifacts_overrides_use_single_directory`.

- Live validation reference:
  - `call_id`: `1777717705.10`
  - ISSUE captured successfully.
  - NAME required one retry, then was accepted.
  - CITY captured successfully.
  - PHONE captured successfully.
  - PHONE_CONFIRM accepted positive confirmation.
  - Transfer completed with `status=ok`.

Current validated transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

## NODE-006 Validation

- `call_id`: `1777721580.0`
- ISSUE captured successfully.
- NAME captured successfully with:
  - `stt_language=ru`;
  - Russian-name STT prompt present;
  - recognized NAME: `Иван Семёнович`.
- CITY captured successfully.
- PHONE captured successfully.
- PHONE_CONFIRM accepted positive confirmation.
- Transfer completed with `status=ok`.

Current validated transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

## NODE-007 Validation

Current validated collection flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

Unclear intent remains bounded and routes to the configured default department.

Department-specific transfer phrases:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

Live validation references:

- Sales: `call_id=1777725117.4`; issue matched sales intent; transfer target `department=sales`, `context=from-internal`, `extension=sales_real`, `priority=1`.
- Accounting: `call_id=1777726120.10`; issue matched accounting intent; accounting phrase resolved and played; transfer target `department=accounting`, `context=from-internal`, `extension=accounting`, `priority=1`.
- Delivery: `call_id=1777726440.12`; issue matched delivery intent; delivery phrase resolved and played; transfer target `department=delivery`, `context=from-internal`, `extension=delivery`, `priority=1`.

## Next Recommended Step

```text
Open the next bounded node only after master records NODE-007 completion.
```
