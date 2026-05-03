# Master Plan

## Project Baseline

- Repository root: `C:\Projects\AI-secrenar-with-Asterisk`
- Source-of-truth branch: `master`
- Source-of-truth commit: `df69f3222cec78a5f7afe2ef09b413f7ab5f3d83`
- Source-of-truth commit message: `Use stage-specific prompts and transfer after data collection`
- Workflow model: master-driven coordination with focused node branches for implementation.

## Confirmed Capabilities

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are present in `master`.
- Transfer flow through ARI continue is present in `master`.
- Tracing and logging are required to be preserved across all node work.

## Completed Practical Gaps

NODE-001 completed and live-validated the real transfer route through the dialplan:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

NODE-002 completed and validated publish hardening:

```text
partial publish failure -> classified failure -> resilient startup and diagnosable per-call behavior
```

NODE-003 completed and validated transcription integrity plus meaningful fallback phrases:

```text
real downloaded caller audio artifact -> traceable transcription metadata -> no fabricated user_transcribed text
```

NODE-004 completed and validated post-PHONE transfer flow restoration:

```text
successful PHONE capture -> play_transfer_phrase -> transfer status=ok
```

NODE-005 completed and validated latency plus turn-based hardening:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

NODE-006 completed and validated NAME capture and normalization hardening:

```text
NAME -> language=ru and Russian-name STT prompt -> bounded normalization -> stable flow continues
```

NODE-007 completed and validated bounded department intent routing:

```text
topic intent -> sales/accounting/delivery/default -> department-specific phrase -> explicit transfer target
```

NODE-008 completed and validated mandatory data capture plus bounded intent clarification:

```text
immediate transfer request -> required data capture -> bounded clarification/default -> transfer or SAFE_FINISH
```

NODE-009 completed and validated business-hours and after-hours handoff:

```text
working hours -> live transfer; after hours -> collect required data -> department callback phrase -> hangup without transfer
```

## Execution Model

- `master` remains the source-of-truth branch.
- Architecture, status, planning, and project coordination are maintained in `docs/master/`.
- Implementation work is performed through focused node branches.
- One node equals one task, one branch, and one execution cycle.
- Avoid broad refactors.
- Do not mix multiple concerns in one node.
- Preserve tracing and logging.

## Current Action Plan

1. Treat NODE-001 through NODE-009 as complete and recorded in `master`.
2. Preserve the validated sales transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

3. Preserve the validated sales dialplan route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

4. Preserve NODE-002 publish failure classification with `reason` and `failed_step`.
5. Preserve NODE-003 transcription artifact traceability through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
6. Preserve NODE-004 post-PHONE transfer behavior so the generic reply pipeline is not taken after successful PHONE capture.
7. Preserve NODE-005 turn-taking contour, NAME playback barrier, PHONE_CONFIRM behavior, and spoken-digit confirmation prompt.
8. Preserve NODE-006 Russian NAME STT context, bounded NAME normalization, simplified NAME prompt, and overall call architecture.
9. Preserve NODE-007 bounded department routing for sales, accounting, delivery, and configured default fallback.
10. Preserve department-specific final transfer phrases.
11. Preserve NODE-008 mandatory data gate before live transfer: `name`, `city`, `phone`, and `phone_confirmed=true`.
12. Preserve bounded `INTENT_CLARIFY`, stage-local retry policy, and terminal/non-transfer `SAFE_FINISH`.
13. Preserve NODE-009 working-hours live transfer behavior and after-hours transfer skip.
14. Preserve department-specific after-hours phrases and the playback barrier before hangup.

## Next Recommended Step

```text
Open the next bounded node only after master records NODE-009 completion.
```

## Node Completion Report Format

After each node, return:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.
