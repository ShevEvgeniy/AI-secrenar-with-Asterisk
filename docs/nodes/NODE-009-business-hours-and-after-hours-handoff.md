# NODE-009 Business Hours And After-Hours Handoff

## Goal

Handle working-hours vs non-working-hours behavior without weakening the mandatory data capture flow.

## Planned Scope

- Branch:

```text
feat/node-009-business-hours-and-after-hours-handoff
```

- Detect working hours vs non-working hours.
- In non-working hours, do not perform live transfer.
- Still collect:
  - issue;
  - name;
  - city;
  - phone.
- Tell the caller that the relevant department will call back in working hours.

## Out Of Scope

- Changing department intent routing beyond what is required for after-hours handoff.
- Weakening mandatory data capture before handoff.
- Broad call architecture changes.

## Success Criteria

- Working-hours calls preserve the validated live transfer behavior.
- Non-working-hours calls do not transfer live.
- Non-working-hours calls still collect required callback data.
- Caller hears a clear department-aware after-hours callback message.

## Branch Name

```text
feat/node-009-business-hours-and-after-hours-handoff
```
