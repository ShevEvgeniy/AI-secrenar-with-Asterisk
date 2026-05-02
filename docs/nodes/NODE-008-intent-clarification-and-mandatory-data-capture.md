# NODE-008 Intent Clarification And Mandatory Data Capture

## Goal

Prevent immediate transfer requests from bypassing required data collection, while keeping department routing bounded and debuggable.

## Scope

- Branch:

```text
feat/node-008-intent-clarification-and-mandatory-data-capture
```

- Require mandatory data before live transfer:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Add stage-aware responses when the caller asks for immediate transfer.
- Add bounded `INTENT_CLARIFY` for unclear or tied department intent.
- Add bounded retry policy by stage.
- Make `SAFE_FINISH` terminal/non-transfer with reason-based spoken phrases before hangup.

## Validated Result

- Immediate transfer requests no longer bypass required data collection.
- Mandatory data before live transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-aware responses are implemented when the caller asks for immediate transfer.
- Bounded `INTENT_CLARIFY` stage is implemented for unclear/tied department intent.
- Bounded retry policy is implemented by stage.
- ISSUE retries, then moves to `INTENT_CLARIFY`.
- `INTENT_CLARIFY` retries, then defaults to configured department.
- NAME/CITY/PHONE use bounded retries, then `SAFE_FINISH`.
- PHONE_CONFIRM has its own bounded policy and no longer gets cut off by generic global turn limits.
- `SAFE_FINISH` is terminal/non-transfer and uses reason-based spoken phrases before hangup.

## Implementation Notes

- PHONE and PHONE_CONFIRM are effectively governed by stage-local policy rather than being prematurely terminated by generic accumulated turn cutoff.
- `INTENT_CLARIFY` timeout/empty outcomes are handled as normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` supports reason-based phrases for:
  - `missing_required_data`;
  - `intent_not_resolved`;
  - `phone_not_confirmed`.

## Validation

Focused regression:

```text
tests/test_dialog_flow.py
tests/test_post_phone_transfer.py
```

Latest focused result:

```text
42 passed in 2.73s
```

## Validated Commit

```text
6380d6e
```

## Next Recommendation

Start NODE-009:

```text
NODE-009 / business-hours-and-after-hours-handoff
```
