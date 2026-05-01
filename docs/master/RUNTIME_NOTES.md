# Runtime Notes

## Confirmed Runtime Behavior

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are active in `master`.
- Transfer after data collection is active in `master`.
- ARI continue is the established transfer mechanism.

## Transfer Route Target

The current target route is:

```text
sales_real -> 78007074193 via thermo-trunk-endpoint -> DTMF 52144
```

The AI secretary ARI handoff target is:

```text
context: from-internal
extension: sales_real
priority: 1
```

Runtime environment defaults now point to this target. Operators may still set these explicitly:

```text
TRANSFER_CONTEXT=from-internal
TRANSFER_EXTEN=sales_real
TRANSFER_PRIORITY=1
```

Required Asterisk dialplan route:

```asterisk
[from-internal]
exten => sales_real,1,NoOp(AI secretary sales real transfer)
 same => n,Dial(PJSIP/78007074193@thermo-trunk-endpoint,60,D(52144))
 same => n,Hangup()
```

## Observability Requirements

Preserve existing tracing and logging. The transfer route node should leave enough logs to identify:

- data collection completion;
- transfer decision;
- selected transfer target;
- ARI continue handoff;
- dialplan context and extension reached;
- outbound trunk endpoint used;
- DTMF dispatch result.

## Validation Notes

The next validation pass should be narrow and practical. Prefer a focused smoke test or log-backed manual validation over a broad refactor or unrelated integration sweep.
