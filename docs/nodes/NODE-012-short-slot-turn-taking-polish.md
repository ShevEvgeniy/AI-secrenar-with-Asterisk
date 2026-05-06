# NODE-012 Short-Slot Turn-Taking Polish

## Goal

Smooth remaining short-slot recording-window pauses for NAME, CITY, and PHONE_CONFIRM without changing business logic or validated transfer contracts.

## Context

NODE-011 closed the critical normal-call latency/silence blocker for the current MVP contour. Remaining pauses are noticeable but no longer block MVP acceptance.

Known remaining limitation from NODE-011:

- NAME, CITY, and PHONE_CONFIRM still have noticeable recording-window pauses.
- `recording_early_stop_used` is not yet reliable.
- PHONE remains longer by design for digit safety.

## Planned Scope

- Branch:

```text
feat/node-012-short-slot-turn-taking-polish
```

- Tune only NAME, CITY, and PHONE_CONFIRM short-slot turn-taking.
- Improve reliability of early-stop behavior where safe.
- Preserve stage-level latency instrumentation and diagnostics from NODE-011.
- Keep PHONE conservative for digit safety.

## Out Of Scope

- PHONE digit timing changes that weaken slow-dictation safety.
- Business logic changes.
- Transfer target changes.
- Department routing changes.
- After-hours behavior changes.
- Callback persistence changes.
- SAFE_FINISH contract changes.

## Success Criteria

- NAME, CITY, and PHONE_CONFIRM feel less silent after caller speech.
- `recording_early_stop_used` or equivalent diagnostics are reliable enough to explain the observed behavior.
- PHONE remains safe for digit capture.
- Required data collection and `phone_confirmed=true` gate remain intact.
- Transfer still occurs only after required data and phone confirmation are complete.

## Branch Name

```text
feat/node-012-short-slot-turn-taking-polish
```
