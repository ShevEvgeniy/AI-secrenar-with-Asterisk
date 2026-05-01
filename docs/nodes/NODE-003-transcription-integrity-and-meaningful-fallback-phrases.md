# NODE-003 Transcription Integrity And Meaningful Fallback Phrases

## Goal

Fix the two follow-up issues surfaced by NODE-002 validation:

1. Fallback media currently degrades to `demo-congrats`, which is not meaningful UX.
2. `user_transcribed` content in runtime logs did not match what the caller says they actually spoke, so transcription integrity is not yet trustworthy.

## Scope

- Branch:

```text
feat/node-003-transcription-integrity-and-fallback-phrases
```

- Verify why runtime `user_transcribed` content can diverge from caller-reported speech.
- Preserve or improve traceability around transcription input, output, stage, and confidence where available.
- Replace non-meaningful fallback media behavior with stage-appropriate fallback phrases.
- Preserve NODE-001 transfer behavior.
- Preserve NODE-002 publish failure classification and startup resilience.

## Out Of Scope

- Broad refactors.
- Changes to the validated `sales_real` transfer route.
- Changes to trunk or DTMF behavior.
- Removing NODE-002 failure classification.

## Validation Steps

1. Run a live or controlled call where the caller speech is known.
2. Compare caller speech against `user_transcribed` log content for each stage.
3. Confirm fallback phrase selection is stage-appropriate when publish media is missing.
4. Confirm missing media no longer falls back to `demo-congrats`.
5. Confirm transfer still completes to:

```text
context=from-internal
extension=sales_real
priority=1
```

6. Confirm publish failures still include `reason` and `failed_step`.

## Success Criteria

- Runtime transcription logs are trustworthy enough to diagnose caller input.
- Stage fallback phrases are meaningful for the caller experience.
- NODE-001 transfer route remains working.
- NODE-002 publish hardening remains working.

## Branch Name

```text
feat/node-003-transcription-integrity-and-fallback-phrases
```

## Implementation Notes

- `user_transcribed` is no longer populated from canned stage text.
- Each dialog recording name now includes the call id, stage, and turn index.
- Each downloaded transcription artifact logs the local path, byte size, and SHA-256 hash.
- Existing local `turn_N.wav` files are discarded before download so stale artifacts cannot be reused silently.
- If no STT backend is configured, transcription is logged as `status=unavailable` with `reason=stt_backend_not_configured` instead of fabricating caller speech.
- Runtime STT can be enabled with `TELEPHONY_STT_BACKEND=openai` or `TELEPHONY_STT_BACKEND=whisper_api`; test fixtures use `TELEPHONY_STT_BACKEND=fixture`.
- Missing stage prompts prefer controlled `fallback_prompt_N` media, then the controlled generic fallback, then non-demo built-ins.
- Missing transfer phrase prefers controlled `fallback_transfer` media, then non-demo transfer built-ins.
