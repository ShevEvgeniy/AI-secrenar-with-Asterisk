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
