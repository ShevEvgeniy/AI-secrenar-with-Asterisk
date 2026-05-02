# NODE-007 Intent Routing And Department Transfer

## Goal

Route callers to the proper department based on topic intent instead of always transferring to `sales_real`.

## Scope

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
- Keep unclear intent bounded by routing to the configured default department.
- Use department-specific final transfer phrases.

## Out Of Scope

- NAME capture hardening.
- PHONE_CONFIRM behavior changes.
- Broad transfer refactors outside bounded department routing.

## Validated Result

- Bounded department intent routing works for:
  - sales;
  - accounting;
  - delivery.
- Routing remains deterministic and debuggable.
- Current validated collection flow is preserved:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Current routing contract resolves explicit targets:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

- Unclear intent remains bounded and routes to the configured default department.

## Department-Specific Transfer Phrases

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

## Live Validation

Sales routing:

- `call_id`: `1777725117.4`
- Issue matched sales intent.
- Transfer target:

```text
department=sales
context=from-internal
extension=sales_real
priority=1
```

Accounting routing:

- `call_id`: `1777726120.10`
- Issue matched accounting intent.
- Department-specific accounting phrase was resolved and played.
- Transfer target:

```text
department=accounting
context=from-internal
extension=accounting
priority=1
```

Delivery routing:

- `call_id`: `1777726440.12`
- Issue matched delivery intent.
- Department-specific delivery phrase was resolved and played.
- Transfer target:

```text
department=delivery
context=from-internal
extension=delivery
priority=1
```

## Important Note

Department routing and department-specific transfer prompts are now validated in live flow for sales, accounting, and delivery.

## Validated Commit

```text
5911c19
```

## Next Recommendation

Open the next bounded node only after master records NODE-007 completion.

## Branch Name

```text
feat/node-007-intent-routing-and-department-transfer
```
