# NODE-001 Sales Real Transfer

## Goal

Implement and validate the real sales transfer route after data collection.

The target transfer path is:

```text
sales_real -> 78007074193 via thermo-trunk-endpoint -> DTMF 52144
```

## Scope

- Create the focused implementation branch:

```text
feat/node-001-sales-real-transfer
```

- Wire or adjust only the dialplan behavior needed for the real sales transfer route.
- Reuse the existing transfer flow via ARI continue.
- Preserve existing tracing and logging.
- Validate the transfer route with a narrow smoke test or equivalent log-backed manual test.

## Out Of Scope

- Broad refactors.
- Changes to stage-specific prompts.
- Changes to the publish/playback pipeline.
- Changes to system sounds prepublish behavior.
- Changes to unrelated dialplan routes.
- Changes to application code outside what is required for this specific transfer route.

## Required Dialplan Route

The node must support this route:

```text
sales_real -> 78007074193 via thermo-trunk-endpoint -> DTMF 52144
```

Expected behavior:

- The post-data-collection transfer selects `sales_real`.
- ARI continue hands the channel to the intended dialplan location.
- The dialplan places the outbound call to `78007074193`.
- The outbound call uses `thermo-trunk-endpoint`.
- DTMF `52144` is sent at the intended step.

## Validation Steps

1. Confirm the transfer path is selected after data collection.
2. Confirm ARI continue reaches the expected dialplan context and extension.
3. Confirm the outbound dial uses `thermo-trunk-endpoint`.
4. Confirm the destination number is `78007074193`.
5. Confirm DTMF `52144` is emitted.
6. Confirm traces/logs show each transfer stage clearly enough for troubleshooting.

## Success Criteria

- The real sales transfer reaches `78007074193`.
- The route uses `thermo-trunk-endpoint`.
- DTMF `52144` is sent successfully.
- Existing working behavior remains unchanged:
  - system sounds prepublish;
  - publish/playback pipeline;
  - stage-specific prompts;
  - ARI continue transfer flow.
- Validation results are recorded in the node completion report.

## Branch Name

```text
feat/node-001-sales-real-transfer
```
