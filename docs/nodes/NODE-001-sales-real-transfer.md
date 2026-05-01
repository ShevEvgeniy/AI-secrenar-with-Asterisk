# NODE-001 Sales Real Transfer

## Goal

Implement and validate the real sales transfer route after data collection.

The validated transfer path is:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
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

The node supports this route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

Runtime ARI continue target:

```text
context: from-internal
extension: sales_real
priority: 1
```

Runtime env, if set explicitly:

```text
TRANSFER_CONTEXT=from-internal
TRANSFER_EXTEN=sales_real
TRANSFER_PRIORITY=1
```

Asterisk dialplan snippet:

```asterisk
[from-internal]
exten => sales_real,1,NoOp(AI secretary sales real transfer)
 same => n,Dial(PJSIP/78007074193@thermo-trunk-endpoint,60,D(ww52144))
 same => n,Hangup()
```

Expected behavior:

- The post-data-collection transfer selects `sales_real`.
- ARI continue hands the channel to the intended dialplan location.
- The dialplan places the outbound call to `78007074193`.
- The outbound call uses `thermo-trunk-endpoint`.
- DTMF `ww52144` is sent at the intended step.

## Validation Steps

1. Confirm the transfer path is selected after data collection.
2. Confirm ARI continue reaches the expected dialplan context and extension.
3. Confirm the outbound dial uses `thermo-trunk-endpoint`.
4. Confirm the destination number is `78007074193`.
5. Confirm DTMF `ww52144` is emitted.
6. Confirm traces/logs show each transfer stage clearly enough for troubleshooting.

Live smoke call on extension `501`:

1. Install or confirm the `sales_real` dialplan route in `[from-internal]`.
2. Run `asterisk -rx "dialplan reload"`.
3. Start the ARI listener with the runtime env above.
4. Call `501` and provide issue, name, city/region, and phone number.
5. Confirm the transfer phrase plays.
6. Confirm the call leaves ARI through `from-internal,sales_real,1`.
7. Confirm Asterisk logs show `Dial(PJSIP/78007074193@thermo-trunk-endpoint,60,D(ww52144))`.
8. Confirm the outbound leg answers and DTMF `ww52144` is sent.

## Validated Result

- Real transfer route works via `sales_real`.
- Runtime target:

```text
context=from-internal
extension=sales_real
priority=1
```

- Live smoke confirmed:
  - prompts progressed by stage;
  - user speech was transcribed;
  - transfer phrase played;
  - transfer completed with `transfer status=ok`.

## Validation Note

A false negative during earlier live testing was caused by the wrong microphone input device selected in MicroSIP. After selecting the correct Windows microphone, live dialog capture worked normally.

## Success Criteria

- The real sales transfer reaches `78007074193`.
- The route uses `thermo-trunk-endpoint`.
- DTMF `ww52144` is sent successfully.
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
