# NODE-004 Restore Post-PHONE Transfer Flow

## Goal

Restore the invariant on current master:

```text
successful PHONE capture -> transfer phrase -> ARI continue to from-internal,sales_real,1
```

The generic reply pipeline must not run once PHONE has been successfully captured.

## Root Cause

The ARI dialog loop only made the transfer decision after leaving the dialog loop. That left the post-PHONE path dependent on generic loop termination behavior, so current master could fall through to the normal response pipeline after the PHONE turn instead of treating PHONE completion as an immediate transfer boundary.

## Implementation

- Added an explicit successful-PHONE predicate in `src/ai_secretary/telephony/ari_app.py`.
- After `apply_turn()` moves `PHONE` to `DONE` and `phone_digits` is present, the handler now immediately plays the transfer phrase and calls ARI `continue`.
- Kept the existing post-loop DONE transfer check as a defensive backstop.
- Preserved the existing transfer target:

```text
context: from-internal
extension: sales_real
priority: 1
```

## Regression Coverage

Added a focused handle-call regression test proving:

- the fourth turn is PHONE;
- `phone_digits` is saved;
- `play_transfer_phrase` is logged;
- ARI `continue` targets `from-internal,sales_real,1`;
- `pipeline_start`, `build_response`, `publish`, and `playback` are absent from the successful PHONE path.

## Validation

Run:

```text
python -m pytest tests/test_post_phone_transfer.py tests/test_sales_real_transfer.py tests/test_dialog_flow.py
```

## Status

READY pending final test run and commit.
