# Node Registry

## Workflow Rules

- One node equals one task, one branch, and one execution cycle.
- Node branches should be focused and implementation-specific.
- `master` remains the source of truth for planning, coordination, architecture, and status.
- Node docs live under `docs/nodes/`.
- Master docs live under `docs/master/`.

## Registered Nodes

| Node | Node Doc | Branch | Status | Purpose | Result |
| --- | --- | --- | --- | --- | --- |
| `NODE-001-sales-real-transfer` | `docs/nodes/NODE-001-sales-real-transfer.md` | `feat/node-001-sales-real-transfer` | Done, merged | Implement and validate the real transfer route `sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144`. | Live smoke passed at `598843d0fc00caa40c935f39dec123acc1b7a6c4`; merged into `master` via `e5d1cb6892a2319fb6ebbc05e52ec2d06f98e0fd`. |
| `NODE-002-publish-hardening` | `docs/nodes/NODE-002-publish-hardening.md` | `feat/node-002-publish-hardening` | Done, merged | Harden publish failure handling so startup and per-call publish failures are resilient and diagnosable. | Validated at `4d0022f0187b866015cca2c4d921a4f109e512a5`; merged into `master`. |
| `NODE-003-transcription-integrity-and-meaningful-fallback-phrases` | `docs/nodes/NODE-003-transcription-integrity-and-meaningful-fallback-phrases.md` | `feat/node-003-transcription-integrity-and-fallback-phrases` | Done, merged | Fix transcription integrity and replace non-meaningful fallback media behavior surfaced by NODE-002. | Validated at `b5a315cb6fa41dc97c1dfb42cb6891f420ab55ad`; merged into `master`. |
| `NODE-004-restore-post-phone-transfer-flow` | `docs/nodes/NODE-004-restore-post-phone-transfer-flow.md` | `feat/node-004-restore-post-phone-transfer-flow` | Done, merged | Restore the post-PHONE invariant so successful PHONE capture immediately plays the transfer phrase and continues to `sales_real`. | Validated at `8ec82c5790cc513a9d5428abb75a90dbce9b5420`; live smoke `1777641576.42` confirmed `play_transfer_phrase -> transfer status=ok` and no generic reply pipeline after PHONE. |
| `NODE-005-latency-and-turn-based-hardening` | `docs/nodes/NODE-005-latency-and-turn-based-hardening.md` | `feat/node-005-latency-and-turn-based-hardening` | Done, merged | Reduce perceived latency inside the current turn-based architecture with stage-specific record contours, PHONE-only confirmation, varied retry prompts, TTS-safe phone confirmation, and explicit latency tracing. | Validated at `43790b1`; live smoke `1777717705.10` reached `ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer status=ok`. |
| `NODE-006-name-capture-and-normalization-hardening` | `docs/nodes/NODE-006-name-capture-and-normalization-hardening.md` | `feat/node-006-name-capture-and-normalization-hardening` | Done, merged | Improve NAME capture quality with Russian STT language/prompting, bounded lexicon normalization, and simpler prompt wording. | Validated at `c5a4311`; live smoke `1777721580.0` recognized NAME as `Иван Семёнович` and completed transfer with `status=ok`. |
| `NODE-007-intent-routing-and-department-transfer` | `docs/nodes/NODE-007-intent-routing-and-department-transfer.md` | `feat/node-007-intent-routing-and-department-transfer` | Done, merged | Detect department intent and transfer to sales, accounting, or delivery instead of always `sales_real`. | Validated at `5911c19`; live calls confirmed sales, accounting, and delivery routing with department-specific transfer phrases. |
| `NODE-008-intent-clarification-and-mandatory-data-capture` | `docs/nodes/NODE-008-intent-clarification-and-mandatory-data-capture.md` | `feat/node-008-intent-clarification-and-mandatory-data-capture` | Done, recorded | Prevent immediate transfer requests from bypassing required data collection; add bounded intent clarification and SAFE_FINISH behavior. | Validated at `6380d6e`; focused regression `tests/test_dialog_flow.py tests/test_post_phone_transfer.py` passed with `42 passed in 2.73s`. |
| `NODE-009-business-hours-and-after-hours-handoff` | `docs/nodes/NODE-009-business-hours-and-after-hours-handoff.md` | `feat/node-009-business-hours-and-after-hours-handoff` | Done, merged | Detect working hours vs non-working hours and avoid live transfer after hours while still collecting callback data. | Validated at `b0d1efbb793c1c860e4acb8d3cf8414a73b34e93`; targeted wording/static-sound follow-up passed with `21 passed`, broader focused result `56 passed`. |
| `NODE-010-callback-capture-and-persistence` | `docs/nodes/NODE-010-callback-capture-and-persistence.md` | `feat/node-010-callback-capture-and-persistence` | Done, merged | Persist bounded callback records for after-hours callback and SAFE_FINISH outcomes. | Validated at `087ea4e0f558038576f6263605c11f30bdf8797d`; targeted tests passed with `21 passed`, broader reported suite `101 passed` with 6 unrelated environment failures. |
| `NODE-011-normal-call-latency-and-silence-hardening` | `docs/nodes/NODE-011-normal-call-latency-and-silence-hardening.md` | `feat/node-011-normal-call-latency-and-silence-hardening` | Done, MVP-acceptable | Instrument stage-level latency, remove normal PHONE_CONFIRM dynamic TTS/publish delay, and harden recording silence handling without changing business contracts. | Final live smoke `1778089554.24` passed: ISSUE/name/city/phone/confirmation captured, `phone_confirm_fast_path_used`, and transfer to `sales_real` completed after `phone_confirmed=true`. Remaining short-slot pause smoothing moves to NODE-012. |

## Node Completion Requirements

Each completed node must report:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.
