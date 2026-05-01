# Decisions

## Accepted

### Master-Driven Workflow

- `master` is the source-of-truth branch.
- Architecture, status, planning, and project coordination are handled through master-layer documentation.
- Implementation work must be isolated to focused node branches.
- One node equals one task, one branch, and one execution cycle.

### Documentation Layout

- Master docs live under `docs/master/`.
- Node docs live under `docs/nodes/`.

### Scope Discipline

- Do not broadly refactor.
- Do not mix multiple concerns in one node.
- Always preserve tracing and logging.

## Current Technical Direction

The next implementation focus is the real transfer route:

```text
sales_real -> 78007074193 via thermo-trunk-endpoint -> DTMF 52144
```

The existing ARI continue transfer flow should be reused. The node should only add or adjust the dialplan/trunk/DTMF behavior necessary to make the real route work.
