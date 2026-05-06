# NODE-011 Normal Call Latency And Silence Hardening

## Goal

Reduce UX-risk silent gaps in the normal working-hours ARI voice flow without changing business logic, routing, transfer targets, after-hours behavior, callback persistence, or SAFE_FINISH semantics.

## Scope

- Branch:

```text
feat/node-011-normal-call-latency-and-silence-hardening
```

- Add stage-level latency instrumentation for the normal call loop.
- Diagnose long silent gaps between caller speech and bot playback.
- Remove the dynamic TTS/publish delay before normal PHONE_CONFIRM.
- Add bounded silence-risk diagnostics.
- Add safe TALK_DETECT capability and early-stop attempts for short stages.
- Preserve PHONE reliability by keeping PHONE conservative and excluded from early stop.
- Improve ISSUE and INTENT_CLARIFY capture reliability with prompt playback barriers.

## Implemented

- Stage-level latency events for:
  - ASR;
  - dialog decision;
  - TTS;
  - publish;
  - playback start;
  - playback finish;
  - stage completion;
  - silence-risk detection.
- Structured events include:
  - `latency_stage_enter`;
  - `latency_asr_done`;
  - `latency_decision_done`;
  - `latency_tts_done`;
  - `latency_publish_done`;
  - `latency_playback_started`;
  - `latency_stage_done`;
  - `latency_silence_risk`.
- Static PHONE_CONFIRM fast path:
  - static prefix sound;
  - static digit sounds;
  - static suffix sound;
  - no per-call dynamic TTS/publish for normal confirmation when `phone_digits` are available.
- Fast-path diagnostics:
  - `phone_confirm_fast_path_used`;
  - `phone_confirm_fast_path_unavailable`.
- TALK_DETECT capability:
  - `TALK_DETECT(set)` enable attempts;
  - stage-specific early-stop policies;
  - safe recording stop/store through live recording stop;
  - no cancel/delete path.
- PHONE safety:
  - PHONE remains excluded from early stop with `phone_digit_safety_skip`;
  - existing PHONE max duration and silence windows remain the safety boundary for slow/grouped/dotted dictation.
- Prompt playback barriers:
  - ISSUE waits for prompt playback completion plus guard before recording;
  - INTENT_CLARIFY waits for prompt playback completion plus guard before recording;
  - NAME barrier behavior remains preserved.
- TALK_DETECT diagnostics:
  - `talk_detect_enable_attempt`;
  - `talk_detect_enabled`;
  - `talk_detect_unavailable`;
  - `talk_detect_event_subscription_started`;
  - `channel_talking_started`;
  - `channel_talking_finished`;
  - `talk_detect_event_order_anomaly`;
  - `talk_detect_started_without_finished`;
  - `talk_detect_no_finished_event`;
  - `record_wait_timeout_after_talking_started`;
  - `recording_timeout_recovery_attempt`;
  - `recording_timeout_recovery_used`;
  - `recording_timeout_recovery_failed`.

## Preserved Contracts

- Current working-hours collection flow remains:

```text
ISSUE -> INTENT_CLARIFY if needed -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE
```

- Mandatory data before live transfer remains:

```text
name
city
phone
phone_confirmed=true
```

- Supported departments remain:
  - sales;
  - accounting;
  - delivery.
- Transfer targets are unchanged.
- Transfer still happens only after `phone_confirmed=true`.
- No automatic `8 -> 7` phone conversion was added.
- After-hours transfer skip and callback persistence are unchanged.
- SAFE_FINISH behavior is unchanged.
- Runtime callback output under `data/storage/` remains untracked runtime data.

## Live Validation

Final smoke:

```text
CALL_ID=1778089554.24
```

Validated result:

- ISSUE captured successfully: `Я бы хотел купить сетку Манье.`
- `department_intent=sales`
- `intent_reason=matched_sales`
- matched keyword: `купить`
- name captured: `Антон Вячеславович`
- city captured: `Самара`
- phone captured and normalized: `9600614112`
- PHONE_CONFIRM fast path used.
- `dynamic_tts_required=false`
- `publish_required=false`
- confirmation captured: `Да, верно`
- `missing_required_fields=[]`
- transfer to `sales_real` completed with `status=ok`
- transfer happened only after `phone_confirmed=true`

Decision:

```text
Done / MVP-acceptable
```

## Known Remaining Limitation

- NAME, CITY, and PHONE_CONFIRM can still have noticeable recording-window pauses.
- `recording_early_stop_used` is not yet reliable enough to treat as the primary turn-taking mechanism.
- PHONE remains longer by design for digit safety.

These are intentionally moved out of NODE-011 and into a separate follow-up node.

## Validation

Focused NODE-011 regression:

```text
tests/test_turn_latency_hardening.py
```

Focused result:

```text
16 passed
```

Relevant voice/dialog regression:

```text
tests/test_post_phone_transfer.py
tests/test_department_routing.py
tests/test_dialog_flow.py
tests/test_ari_publish_fallback.py
tests/test_sales_real_transfer.py
tests/test_ari_client_record_params.py
tests/test_ari_client_ws_single_connection.py
```

Relevant result:

```text
66 passed
```

Broader reported full-suite result:

```text
114 passed, 6 unrelated environment failures
```

Known unrelated failures:

- missing `src/scripts/make_demo_audio.py`;
- blocked/unavailable HuggingFace model fetch path.

## Traceable Implementation Commits

```text
452409b NODE-011 add call latency instrumentation
fb5eaaf NODE-011 use static phone confirmation playback
e8acace NODE-011 add talk-detect recording early stop
f14cd1a NODE-011 fix talk-detect recording event delivery
0f313c8 NODE-011 harden talk-detect capture ordering
```

## Next Recommendation

Open a separate bounded UX polish node:

```text
NODE-012 / short-slot-turn-taking-polish
```

NODE-012 should tune only NAME, CITY, and PHONE_CONFIRM short-slot turn-taking. It must not change PHONE digit safety, business logic, transfer targets, after-hours behavior, callback persistence, or SAFE_FINISH contracts.
