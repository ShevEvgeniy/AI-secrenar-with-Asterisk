# NODE-010 Callback Capture And Persistence

## Goal

Persist bounded callback records for after-hours callback and SAFE_FINISH outcomes without changing the live-transfer architecture.

## Scope

- Branch:

```text
feat/node-010-callback-capture-and-persistence
```

- Add local callback persistence.
- Use JSONL with one flat JSON object per line.
- Persist after-hours callback outcomes.
- Persist SAFE_FINISH outcomes with available partial data.
- Keep persistence fail-soft so call flow does not crash.
- Add persistence logging.

## Production Path

```text
data/storage/callbacks/callback_records.jsonl
```

## Persisted Schema

```text
record_id
call_id
timestamp
department
issue
name
city
phone
outcome_type
outcome_reason
```

## Trigger Points

```text
after_hours_callback
safe_finish
```

## Validated Result

- Bounded local callback persistence is implemented.
- Persistence format is JSONL, one flat JSON object per line.
- After-hours callback records are persisted after after-hours transfer skip and before final hangup.
- SAFE_FINISH records are persisted with available partial data and terminal reason.
- Persistence is fail-soft and does not crash call flow.
- Logging includes:
  - `persistence_attempt`;
  - `persistence_success`;
  - `persistence_failure`.

## Live Validation

Live validation confirmed:

- after-hours flow completed correctly;
- after-hours phrase playback completed before hangup;
- transfer was skipped in after-hours mode;
- callback persistence succeeded with:

```text
outcome_type=after_hours_callback
outcome_reason=mode_override
record_id=f0cff987b252b77c
path=data/storage/callbacks/callback_records.jsonl
```

## Validation

Targeted tests:

```text
tests/test_department_routing.py
tests/test_post_phone_transfer.py
```

Targeted result:

```text
21 passed
```

Broader reported full-suite result:

```text
101 passed, 6 unrelated environment failures
```

## Traceable Implementation Commit

```text
087ea4e0f558038576f6263605c11f30bdf8797d
```

## Next Recommendation

Open the next bounded node only after master records NODE-010 completion on remote master.
