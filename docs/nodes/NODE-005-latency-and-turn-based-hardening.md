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
CITY:  max_duration=7s, max_silence=3s, wait_timeout=13s
PHONE: max_duration=14s, max_silence=4s, wait_timeout=21s
PHONE_CONFIRM: max_duration=6s, max_silence=3s, wait_timeout=12s
```

The ISSUE stage remains tolerant because callers may describe the problem. NAME stays tight. CITY and PHONE were relaxed after live smoke showed that the previous patch treated short intra-utterance pauses as end-of-speech.

Patch 3 turn-taking guardrails:

- CITY requires at least 4 letters before it can advance to PHONE.
- PHONE requires a complete 10- or 11-digit captured run before it can advance to PHONE_CONFIRM.
- CITY and PHONE have longer `maxSilenceSeconds`, so short pauses inside a city name or slow phone dictation do not immediately end the turn.
- PHONE has the longest non-ISSUE profile because slow digit dictation is expected.
- Generic `reply.wav` remains blocked while structured collection is incomplete or PHONE is unconfirmed.
- Live smoke noted poor TTS stress/pronunciation on the phone prompt; this is recorded as a secondary issue and is not part of the NODE-005 acceptance gate unless prompt wording is changed later.

Patch 4 adds polite PHONE-only retry variation:

- PHONE retry prompts are selected from small controlled phrase sets.
- The same PHONE retry phrase is not repeated twice in a row for the same call profile.
- Retry wording depends on repair reason:
  - `unclear`: no usable digits were captured.
  - `incomplete`: some digits were captured, but not a complete 10- or 11-digit phone.
  - `rejected`: caller rejected the number during PHONE_CONFIRM.
- This applies only to PHONE retry/repair behavior. ISSUE, NAME, CITY, and transfer behavior are unchanged in patch 4.

Patch 5 fixes PHONE_CONFIRM TTS:

- `phone_formatted` remains in the profile for logs/debug, for example `+7 920 032-03-55`.
- PHONE_CONFIRM synthesis now uses `phone_spoken`, a TTS-safe Russian digit string, for example `девять, два, ноль, ноль, три, два, ноль, три, пять, пять`.
- The confirmation prompt fed to TTS no longer contains symbolic phone formatting such as `+7` or hyphenated groups.

Patch 6 fixes PHONE_CONFIRM sequencing and repair handling:

- PHONE_CONFIRM playback now waits for the explicit ARI `PlaybackFinished` event before recording starts.
- After playback completion, runtime applies `PHONE_CONFIRM_GUARD_DELAY_MS`, default `400 ms`.
- Playback wait uses `PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS`, default `15 s`.
- PHONE_CONFIRM response capture is expanded to `max_duration=6s`, `max_silence=3s`, `wait_timeout=12s`.
- Meta-repair phrases such as `я уже сказал`, `вы ничего не произнесли`, `что-то не так`, and `вы не так записали` return to PHONE capture with neutral repair wording.
- NAME now has a separate guard for obvious STT garbage such as `you`, empty input, or non-confident junk; those do not advance NAME to CITY.
- Fixed PHONE prompt audio is forced to re-render under `prompt_4_v2`, and built-in TTS stress preprocessing maps `связи` to `св+язи`.

Patch 7 fixes NAME retry-loop regression:

- NAME retry prompts are now reason-based (`unclear`, `junk`, `meta_repair`) and rotate without repeating the same retry phrase twice in a row.
- NAME meta-repair phrases such as `я уже сказал`, `вы не расслышали`, and `ещё раз?` keep the caller in NAME with neutral retry wording.
- Short Russian names with at least two Cyrillic letters, such as `Ян`, `Лев`, and `Оля`, are accepted.
- Obvious junk, digits, non-name punctuation, and known STT noise such as `you` remain blocked.
- NAME retries are bounded at `3`; after that the profile records `name="клиент"` and `name_unavailable=true`, then advances to CITY to avoid an infinite prompt_2 loop.

Patch 8 fixes live PHONE acceptance/repair regression:

- PHONE accepts digit runs separated by spaces, dots, commas, semicolons, parentheses, and hyphens.
- PHONE normalizes `10` digits as a local Russian mobile-style number and formats it as `+7 XXX XXX-XX-XX`.
- PHONE keeps `11` digits as captured for existing transfer behavior, but for comma/semicolon grouped STT output that starts with `9` and is exactly one digit too long, it tries a grouped repair by dropping one leading zero from the last zero-prefixed group. This converts live STT such as `920, 0.32, 0.3, 0.55` to `9200320355`.
- PHONE-stage meta-repair phrases such as `я уже продиктовал номер для связи`, `я уже назвал`, and `номер для связи` now use the `meta_repair` PHONE retry reason directly instead of falling through to generic unclear/incomplete retry.
- PHONE retry prompts are now actually played as dynamic synthesized call-specific prompts. Static `prompt_4_v2` is used only for the base PHONE prompt, not for retry/repair prompts.
- NAME rejects short English filler such as `Yep.`, `ok`, and `Hi`, while still accepting short valid Russian names.

Patch 2 adds explicit confirmation only for PHONE:

```text
PHONE plausible -> PHONE_CONFIRM -> positive confirmation -> DONE -> transfer
```

CITY remains a normal capture stage. If CITY is not confidently accepted, the flow re-asks CITY; there is no CITY confirmation substage.

PHONE now strips formatting and keeps the captured digits-only form. Plausible values enter `PHONE_CONFIRM` and ask:

```text
Правильно ли я записала ваш номер: <formatted_phone>?
```

If the caller rejects or re-dictates, the flow returns to PHONE capture or re-confirms the replacement number. While PHONE is unconfirmed, the call does not fall through to the generic `reply.wav` / received-request path.

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
- Generic pipeline work still does not run after confirmed PHONE capture.
- Generic pipeline work also does not run while PHONE is plausible but unconfirmed.
- Publish hardening and controlled fallback media remain in place.
- Transcription integrity remains tied to the downloaded audio artifact and SHA-256 metadata.
- No realtime, partial STT, streaming STT, or barge-in behavior was introduced.

## Regression Coverage

Added focused coverage proving:

- ISSUE uses a tolerant opening profile.
- NAME stays tighter than CITY and PHONE.
- CITY and PHONE use relaxed end-of-speech profiles.
- CITY has a minimum speech floor before advancing.
- PHONE has a complete digit floor before PHONE_CONFIRM.
- PHONE retry prompts vary by unclear, incomplete, and rejected-confirmation reasons without immediate repetition.
- PHONE_CONFIRM prompt construction uses spoken digit text for TTS while preserving formatted digits separately.
- PHONE_CONFIRM recording starts only after `PlaybackFinished` plus guard delay.
- NAME rejects obvious STT garbage instead of advancing to CITY.
- NAME retries are bounded and use varied reason-based repair prompts.
- PHONE retry prompts play dynamically instead of replaying fixed `prompt_4_v2`.
- Fixed PHONE system prompt is regenerated with corrected stress preprocessing for `связи`.
- Recording wait timeouts track the stage profile instead of fixed `30s`.
- The successful PHONE path transfers only after positive PHONE confirmation.
- Rejected/unconfirmed PHONE does not run the generic pipeline.
- Latency events include `dur_ms` for the hot-path stages.
- The latency report includes the new turn-based buckets.

## Validation

Run:

```text
python -m pytest tests/test_dialog_flow.py tests/test_post_phone_transfer.py tests/test_turn_latency_hardening.py tests/test_latency_report.py tests/test_ari_client_record_params.py tests/test_transcription_integrity.py
```

Focused regression validation passed.

Full-suite validation was attempted with `python -m pytest`; it failed outside the NODE-005 surface because synth pipeline tests could not open `src/scripts/make_demo_audio.py`, and one runner events test attempted a blocked Hugging Face model fetch.

## Status

READY for live smoke validation.
