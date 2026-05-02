# NODE-006 Name Capture And Normalization Hardening

## Goal

Improve NAME capture quality without mixing in routing, transfer, or broader dialog refactors.

NODE-005 stabilized latency and turn-taking for the current flow, but live validation still showed NAME quality needs a separate focused node.

## Scope

- Branch:

```text
feat/node-006-name-capture-and-normalization-hardening
```

- Explicitly set `language="ru"` for NAME transcription where applicable.
- Add an STT prompt for Russian names.
- Add a bounded name/patronymic lexicon and post-STT normalizer.
- Simplify NAME prompt wording.
- Only if needed, test `gpt-4o-mini-transcribe` for NAME.

## Out Of Scope

- Department intent routing.
- Transfer target selection changes.
- Broad dialog refactors.
- Changes to the validated sales transfer target.
- Changes to NODE-005 PHONE/PHONE_CONFIRM behavior unless required to keep existing tests passing.

## Validation Steps

1. Run focused NAME parser and dialog tests.
2. Run the current post-PHONE transfer regression tests.
3. Run one live smoke where NAME is spoken naturally in Russian.
4. Confirm NAME is captured without breaking the flow.
5. Confirm the call still reaches:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

## Success Criteria

- NAME capture quality improves for Russian caller names.
- NAME retries remain bounded.
- The current validated NODE-005 flow remains intact.
- Transfer still completes to `from-internal,sales_real,1`.

## Branch Name

```text
feat/node-006-name-capture-and-normalization-hardening
```

## Validated Result

- NAME capture quality was hardened without changing the overall call architecture.
- STT for NAME now explicitly uses Russian language and Russian-name prompt context.
- Bounded post-STT normalization for Russian names, patronymics, and common conversational forms was added.
- NAME prompt wording was simplified to:

```text
Назовите, пожалуйста, ваше имя.
```

- NAME playback barrier remains in place, so NAME recording no longer starts over prompt playback.
- Validated end-to-end flow remains intact:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

## Live Validation

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

## Important Note

NODE-006 improves NAME quality and stability, but does not introduce multi-department routing yet.

## Validated Commit

```text
c5a4311
```

## Next Recommendation

Start NODE-007:

```text
NODE-007 / intent-routing-and-department-transfer
```
