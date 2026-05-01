# NODE-002 Publish Hardening

## Goal

Harden the publish pipeline so partial publish failures remain visible and diagnosable without causing silent or brittle startup degradation.

## Scope

- Branch:

```text
feat/node-002-publish-hardening
```

- Keep startup resilient when system-sounds prepublish partially fails.
- Classify publish failures explicitly with `reason` and `failed_step`.
- Make startup and per-call publish failures diagnosable in logs/traces.
- Preserve existing transfer behavior and tracing.

## Out Of Scope

- Replacing fallback phrase content.
- Solving transcription correctness.
- Broad refactors outside publish failure handling.
- Changes to the NODE-001 transfer route.

## Validated Result

- Publish pipeline no longer degrades into silent startup failure when publish steps partially fail.
- Startup remains resilient under partial system-sounds prepublish failure.
- Explicit failure classification is present, including `reason` and `failed_step`.
- Per-call and startup publish failures are diagnosable instead of opaque.

## Validated Runtime Observations

- During startup, `prompt_3` and transfer system sounds failed to publish because SSH to `92.118.85.117:22` timed out.
- Despite those publish failures, the listener still reached `READY_WAITING_FOR_CALLS`.
- During the live call, fallback media was used instead of missing `prompt_3` and the missing transfer phrase.
- Transfer still completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

## Validation Note

NODE-002 solved the silent and brittle degradation problem, but surfaced two follow-up issues:

1. Fallback media currently degrades to `demo-congrats`, which is not meaningful UX.
2. `user_transcribed` content in runtime logs did not match what the caller says they actually spoke, so transcription integrity is not yet trustworthy.

## Success Criteria

- Partial startup publish failure does not prevent the listener from reaching `READY_WAITING_FOR_CALLS`.
- Startup publish failures include explicit classification fields.
- Per-call publish failures include explicit classification fields.
- Runtime behavior remains observable enough to identify the failed publish step and reason.
- Existing NODE-001 transfer route remains functional.

## Branch Name

```text
feat/node-002-publish-hardening
```

## Validated Commit

```text
4d0022f0187b866015cca2c4d921a4f109e512a5
```

## Next Recommendation

Start NODE-003:

```text
NODE-003 / transcription-integrity-and-meaningful-fallback-phrases
```
