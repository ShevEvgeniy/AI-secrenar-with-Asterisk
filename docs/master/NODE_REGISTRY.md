# Node Registry

## Workflow Rules

- One node equals one task, one branch, and one execution cycle.
- Node branches should be focused and implementation-specific.
- `master` remains the source of truth for planning, coordination, architecture, and status.
- Node docs live under `docs/nodes/`.
- Master docs live under `docs/master/`.

## Registered Nodes

| Node | Node Doc | Branch | Status | Purpose | Result |
| --- | --- | --- | --- | --- | --- |
| `NODE-001-sales-real-transfer` | `docs/nodes/NODE-001-sales-real-transfer.md` | `feat/node-001-sales-real-transfer` | Done | Implement and validate the real transfer route `sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144`. | Live smoke passed at `598843d0fc00caa40c935f39dec123acc1b7a6c4`; ready for ff-merge. |

## Node Completion Requirements

Each completed node must report:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.
