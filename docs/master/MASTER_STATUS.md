# Master Status

## Current State

- Branch: `master`
- Source-of-truth commit: `df69f3222cec78a5f7afe2ef09b413f7ab5f3d83`
- Source-of-truth commit message: `Use stage-specific prompts and transfer after data collection`
- Repository location: `C:\Projects\AI-secrenar-with-Asterisk`
- Master docs initialized: yes.
- Latest completed node branch: `feat/node-014-true-live-ari-media-streaming-stt-proof`
- Latest completed node commit: `8879372`

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
- Immediate transfer requests no longer bypass required data collection.
- Mandatory data before live transfer remains `name`, `city`, `phone`, and `phone_confirmed=true`.
- Stage-aware responses are implemented when the caller asks for immediate transfer.
- Bounded `INTENT_CLARIFY` is implemented for unclear or tied department intent.
- `SAFE_FINISH` is terminal/non-transfer and uses reason-based spoken phrases before hangup.
- Bounded working-hours vs after-hours behavior is implemented.
- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped and logged.
- Mandatory data collection is still enforced before after-hours completion.
- Department-specific after-hours phrases are implemented for sales, accounting, and delivery.
- After-hours phrase playback completes before hangup.
- Bounded local callback persistence is implemented.
- Callback persistence format is JSONL, one flat JSON object per line.
- Callback records persist for `after_hours_callback` and `safe_finish` trigger points.
- Callback persistence is fail-soft and does not crash call flow.
- Stage-level latency instrumentation is implemented for the normal ARI call flow.
- PHONE_CONFIRM fast path uses static/prepublished prefix, digit, and suffix sounds when `phone_digits` are available.
- Normal PHONE_CONFIRM no longer requires per-call dynamic TTS/publish.
- ISSUE and INTENT_CLARIFY have prompt playback barriers before recording.
- PHONE is explicitly excluded from TALK_DETECT early stop with `phone_digit_safety_skip`.
- CITY transcript validation accepts compound region/city/address answers with a city or region anchor.
- English/STT filler is rejected for CITY.
- Russian-only caller-facing invariant is added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Feature-flagged OpenAI Realtime Whisper STT adapter is implemented.
- Streaming STT fallback to the existing batch Whisper path is implemented.
- Streaming STT latency/event instrumentation is implemented.
- Default STT behavior remains unchanged unless `STT_STREAMING_ENABLED=true`.
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

NODE-008 adds mandatory data capture and bounded clarification:

```text
immediate transfer request -> collect required data -> clarify intent/default safely -> transfer only when complete
```

NODE-009 adds business-hours and after-hours handoff:

```text
working hours -> live transfer; after hours -> collect required data -> department callback phrase -> hangup without transfer
```

NODE-010 adds callback capture and persistence:

```text
after_hours_callback/safe_finish -> flat JSONL callback record -> fail-soft persistence logging
```

NODE-011 hardens normal-call latency and silence behavior:

```text
stage latency logs -> static PHONE_CONFIRM -> prompt playback barriers -> TALK_DETECT diagnostics -> MVP-acceptable transfer flow
```

NODE-012 polishes short-slot turn-taking and CITY validation:

```text
Russian-only dialog -> safe CITY validation -> static CITY retry -> SAFE_FINISH playback barrier -> compound CITY/address accepted
```

NODE-013 adds a feature-flagged streaming STT adapter and metrics spike:

```text
stored WAV artifact -> chunked realtime adapter -> metrics/fallback -> batch path preserved
```

NODE-014 proves the server-side true-live ARI media path:

```text
colocated ari_app -> Stasis(ai_secretary) -> snoop_external_media_rtp -> RTP/PCM received
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
- NODE-008 is recorded in `master`.
- NODE-009 is merged into `master`.
- NODE-010 is merged into `master`.
- NODE-011 is merged into `master` and closed as MVP-acceptable.
- NODE-012 is merged into `master` and closed.
- NODE-013 is merged into `master` and closed as adapter/metrics spike only.
- NODE-014 is complete as a successful media-path proof; production STT adoption remains out of scope.
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
- NODE-008 prevents transfer from bypassing required data collection and makes SAFE_FINISH terminal/non-transfer.
- NODE-009 validates working-hours live transfer preservation and after-hours transfer skip with department-specific callback phrases.
- NODE-010 validates local callback JSONL persistence for after-hours callback and SAFE_FINISH outcomes.
- NODE-011 validates normal-call latency instrumentation, static PHONE_CONFIRM, ISSUE capture reliability, TALK_DETECT diagnostics, and preserved sales transfer semantics.
- NODE-012 validates compound CITY/address acceptance while preserving PHONE digit safety and sales transfer semantics.
- NODE-013 validates adapter, metrics, feature flag, and fallback behavior, but does not prove caller-perceived pause reduction in live calls.
- NODE-014 validates colocated/server-side `ari_app`, local sound publish, ARI `Stasis(ai_secretary)`, and `snoop_external_media_rtp` delivery of RTP/PCM chunks to server host `172.18.0.1`.

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

## NODE-008 Validation

Mandatory data before live transfer:

```text
name
city
phone
phone_confirmed=true
```

Focused regression:

```text
tests/test_dialog_flow.py
tests/test_post_phone_transfer.py
```

Latest focused result:

```text
42 passed in 2.73s
```

Implementation notes:

- PHONE and PHONE_CONFIRM are governed by stage-local policy rather than generic accumulated turn cutoff.
- `INTENT_CLARIFY` timeout and empty outcomes are normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` supports reason-based phrases for `missing_required_data`, `intent_not_resolved`, and `phone_not_confirmed`.

## NODE-009 Validation

Focused regression:

```text
tests/test_dialog_flow.py
tests/test_department_routing.py
tests/test_post_phone_transfer.py
tests/test_sales_real_transfer.py
```

Wording/static-sound follow-up targeted result:

```text
21 passed
```

Broader focused result previously recorded:

```text
56 passed
```

Traceable implementation commits:

```text
bd63f42115224a5d9e75d2ca431bcc558b8e42ee
5dfb0c3d61644f52bd3acf18a87f2014fdeb8ab9
ce230c96cefb321e1e5dcabe3d9de4defa776254
b0d1efbb793c1c860e4acb8d3cf8414a73b34e93
```

## NODE-010 Validation

Targeted tests:

```text
tests/test_department_routing.py
tests/test_post_phone_transfer.py
```

Targeted result:

```text
21 passed
```

Broader reported full-suite result:

```text
101 passed, 6 unrelated environment failures
```

Live validation confirmed callback persistence succeeded with:

```text
outcome_type=after_hours_callback
outcome_reason=mode_override
record_id=f0cff987b252b77c
path=data/storage/callbacks/callback_records.jsonl
```

## NODE-011 Validation

Final live smoke:

```text
call_id=1778089554.24
```

Validated:

- ISSUE captured successfully: `Я бы хотел купить сетку Манье.`
- `department_intent=sales`
- `intent_reason=matched_sales`
- matched keyword: `купить`
- name captured: `Антон Вячеславович`
- city captured: `Самара`
- phone captured and normalized: `9600614112`
- PHONE_CONFIRM fast path used with `dynamic_tts_required=false` and `publish_required=false`
- confirmation captured: `Да, верно`
- `missing_required_fields=[]`
- transfer to `sales_real` completed with `status=ok`
- transfer happened only after `phone_confirmed=true`

Focused NODE-011 regression:

```text
tests/test_turn_latency_hardening.py
```

Focused result:

```text
16 passed
```

Relevant voice/dialog regression result:

```text
66 passed
```

Broader reported full-suite result:

```text
114 passed, 6 unrelated environment failures
```

Known remaining limitation:

- NAME, CITY, and PHONE_CONFIRM still have noticeable recording-window pauses.
- `recording_early_stop_used` is not yet reliable.
- PHONE remains longer by design for digit safety.

## Next Recommended Step
## NODE-012 Validation

Final live smoke:

```text
CALL_ID=1778258401.18
```

Result:

```text
PASS for normal sales flow with compound CITY/address.
```

Validated:

- ISSUE resolved to sales from `купить`.
- NAME captured.
- CITY accepted compound location:
  - raw: `Владимирская область, Петушки, Красноармейская улица, 141.`;
  - `city_transcript_validation status=ok`;
  - `reason=region_with_location_detail`;
  - `accepted=true`;
  - `canonical_city=Владимирская область`;
  - `location_detail=Петушки, Красноармейская улица, 141`;
  - transition `CITY -> PHONE`.
- PHONE remained conservative with `phone_digit_safety_skip`.
- PHONE_CONFIRM fast path worked with static digit sequence.
- `phone_confirmed=true` only after caller confirmation `Верно.`
- `missing_required_fields=[]` before transfer.
- Transfer to `sales_real` completed with `status=ok`.

Also validated:

- English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye` is rejected for CITY.
- Russian-only caller-facing invariant added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- Compound city/location validator accepts region/city anchor plus detail.

Known remaining UX debt:

- CITY and PHONE can still have long recording windows.
- PHONE is intentionally conservative for digit safety.
- Further pause reduction should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike, not NODE-012.

## Next Recommended Step

```text
Open NODE-015 / production-server-side-stt-strategy.
```

## NODE-014 Validation

Result:

```text
PASS as successful media-path proof.
```

Final proof commit:

```text
8879372 Record NODE-014 server-side RTP proof
```

Validated:

- Colocated/server-side `ari_app` near Asterisk works.
- Local sound publish works without SSH.
- Asterisk ARI listens on `Stasis(ai_secretary)`.
- `snoop_external_media_rtp` successfully sends RTP from the Asterisk container to server host `172.18.0.1`.
- Runtime logs confirmed `stt_live_rtp_packets_received_count > 0`.
- Runtime logs confirmed `stt_live_pcm_chunks_created_count > 0`.
- Runtime logs confirmed `stt_live_rtp_diagnostics_result=rtp_packets_received`.

Boundary:

- Production STT adoption is explicitly out of scope for NODE-014.
- The later dialog failure was expected because batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1` for RTP-only diagnostics.

Uncommitted artifacts intentionally left out:

```text
data/storage/
node014-server.tar
```

## Next Recommended Step

```text
Open NODE-015 / production-server-side-stt-strategy.
```
