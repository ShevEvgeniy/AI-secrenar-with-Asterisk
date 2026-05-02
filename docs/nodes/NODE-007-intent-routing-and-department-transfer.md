# NODE-007 Intent Routing And Department Transfer

## Goal

Route callers to the proper department based on topic intent instead of always transferring to `sales_real`.

## Planned Scope

- Branch:

```text
feat/node-007-intent-routing-and-department-transfer
```

- Detect department intent from the caller topic.
- Map intent to:
  - sales;
  - accounting;
  - delivery.
- Transfer to the proper extension/context for the selected department.
- Preserve tracing for selected intent, selected department, transfer target, and transfer result.

## Out Of Scope

- NAME capture hardening.
- PHONE_CONFIRM behavior changes.
- Broad transfer refactors before department targets are explicitly defined.

## Dependency

Start after NODE-006 unless master planning changes the priority.

## Branch Name

```text
feat/node-007-intent-routing-and-department-transfer
```
