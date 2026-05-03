# NODE-009 Business Hours And After-Hours Handoff

## Goal

Handle working-hours vs non-working-hours behavior without weakening the mandatory data capture flow.

## Scope

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

## Validated Result

- Bounded working-hours vs after-hours behavior is implemented.
- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped.
- Mandatory data collection is still enforced before after-hours completion:
  - issue;
  - name;
  - city;
  - phone;
  - `phone_confirmed=true`.
- Department-specific after-hours phrases are implemented for:
  - sales;
  - accounting;
  - delivery.
- After-hours phrase playback now completes before hangup.
- Transfer is explicitly skipped and logged in after-hours mode.

## UX Wording Follow-Up

Opening prompt updated to:

```text
Здравствуйте. Меня зовут Анна. Я виртуальный секретарь. По какому вопросу вы обращаетесь?
```

After-hours phrases now end with:

```text
Спасибо за звонок. До свидания.
```

## Static Sound Refresh

Versioned after-hours system sounds added:

```text
sound:ai_secretary/_system/after_hours_sales_v2
sound:ai_secretary/_system/after_hours_accounting_v2
sound:ai_secretary/_system/after_hours_delivery_v2
```

This ensures freshly published wav files are used for the updated after-hours wording.

## Implemented Contract

Business-hours modes are bounded to:

```text
working_hours
after_hours
```

Default schedule:

```text
BUSINESS_HOURS_TZ=Europe/Moscow
BUSINESS_HOURS_DAYS=0,1,2,3,4
BUSINESS_HOURS_START=09:00
BUSINESS_HOURS_END=18:00
```

After-hours transfer-skip logic:

1. Resolve required fields first. If `name`, `city`, `phone_digits`, or `phone_confirmed=true` is missing, no transfer and no after-hours completion occurs.
2. Resolve department with the existing NODE-007/NODE-008 routing logic.
3. Evaluate `business_hours_for_department(department)`.
4. If `working_hours`, play the existing department transfer phrase and call `continue_safe` unchanged.
5. If `after_hours`, play the department callback phrase and capture the returned playback id.
6. Wait for `PlaybackFinished` with `AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS`.
7. Apply `AFTER_HOURS_GUARD_DELAY_MS`.
8. Log `transfer_skipped_after_hours`, hang up with `after_hours_handoff`, and never call `continue_safe`.

Logging:

```text
department_intent
business_hours_decision
transfer_phrase_resolved
after_hours_phrase_resolved
after_hours_playback_barrier
transfer_skipped_after_hours
after_hours_handoff
```

## Validation

Focused regression:

```text
tests/test_dialog_flow.py
tests/test_department_routing.py
tests/test_post_phone_transfer.py
tests/test_sales_real_transfer.py
```

Wording/static-sound follow-up targeted result:

```text
21 passed
```

Broader focused result previously recorded:

```text
56 passed
```

## Traceable Implementation Commits

```text
bd63f42115224a5d9e75d2ca431bcc558b8e42ee
5dfb0c3d61644f52bd3acf18a87f2014fdeb8ab9
ce230c96cefb321e1e5dcabe3d9de4defa776254
b0d1efbb793c1c860e4acb8d3cf8414a73b34e93
```

## Next Recommendation

Open the next bounded node only after master records NODE-009 completion.

## Branch Name

```text
feat/node-009-business-hours-and-after-hours-handoff
```
