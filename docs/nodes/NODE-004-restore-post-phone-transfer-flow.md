# NODE-004 Restore Post-PHONE Transfer Flow

## Goal

Restore the invariant on current master:

```text
successful PHONE capture -> transfer phrase -> ARI continue to from-internal,sales_real,1
```

The generic reply pipeline must not run once PHONE has been successfully captured.

## Root Cause

The first NODE-004 patch made the transfer decision explicit only after the dialog parser reported `PHONE -> DONE` with `phone_digits`. Live smoke `1777640788.40` showed the missing runtime case: Whisper transcribed the caller's phone as `920.032.0355`. That is a valid 10-digit Russian mobile number shape, but the dialog phone regex accepted spaces, hyphens, and parentheses only, not dots.

Because the dotted phone was rejected:

```text
user_transcribed(PHONE, ok) -> no phone_digits -> max_turns reached -> pipeline_start -> build_response
```

So STT succeeded, but PHONE collection did not complete from the dialog state machine's point of view.

## Implementation

- Added an explicit successful-PHONE predicate in `src/ai_secretary/telephony/ari_app.py`.
- After `apply_turn()` moves `PHONE` to `DONE` and `phone_digits` is present, the handler now immediately plays the transfer phrase and calls ARI `continue`.
- Updated the PHONE parser in `src/ai_secretary/telephony/dialog.py` to accept dotted numeric separators emitted by STT, for example `920.032.0355`.
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
- the exact live-smoke dotted PHONE transcription `920.032.0355` is accepted;
- `phone_digits` is saved;
- `play_transfer_phrase` is logged;
- ARI `continue` targets `from-internal,sales_real,1`;
- `pipeline_start`, `build_response`, `publish`, and `playback` are absent from the successful PHONE path.

## Validation

Run:

```text
python -m pytest tests/test_post_phone_transfer.py tests/test_sales_real_transfer.py tests/test_dialog_flow.py
```

Validated live smoke:

- `call_id`: `1777641576.42`
- ISSUE / NAME / CITY / PHONE each reached `user_transcribed=ok`.
- After PHONE, events showed `play_transfer_phrase` followed by `transfer status=ok`.
- Transfer completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

- `pipeline_start`, `build_response`, and `reply.wav` did not occur after PHONE in this validated call.

## Validated Result

- Successful PHONE capture now leads to `play_transfer_phrase -> transfer`.
- The generic reply path after PHONE is no longer taken on the validated live call.
- Transfer completed successfully to `from-internal,sales_real,1`.
- The runtime root cause was the PHONE parser rejecting dotted separators from STT output.
- After patching dotted-phone normalization, live transfer flow was restored.

## Validated Commit

```text
8ec82c5790cc513a9d5428abb75a90dbce9b5420
```

## Status

READY and merged into `master`.
