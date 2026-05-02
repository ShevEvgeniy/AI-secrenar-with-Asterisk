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

`BUSINESS_HOURS_DAYS` uses Python weekday numbers: Monday `0` through Sunday `6`. Start is inclusive and end is exclusive.

Overrides:

```text
BUSINESS_HOURS_MODE=working_hours|after_hours
DEPARTMENT_WORKING_HOURS_<DEPARTMENT>_MODE=working_hours|after_hours
DEPARTMENT_WORKING_HOURS_<DEPARTMENT>_TZ=Europe/Moscow
DEPARTMENT_WORKING_HOURS_<DEPARTMENT>_DAYS=0,1,2,3,4
DEPARTMENT_WORKING_HOURS_<DEPARTMENT>_START=09:00
DEPARTMENT_WORKING_HOURS_<DEPARTMENT>_END=18:00
AFTER_HOURS_PLAYBACK_TIMEOUT_SECONDS=20
AFTER_HOURS_GUARD_DELAY_MS=400
```

After-hours phrase mapping:

```text
sales      -> sound:ai_secretary/_system/after_hours_sales_v2
              "Отдел продаж сейчас не работает. Мы записали ваше обращение, и отдел продаж перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
accounting -> sound:ai_secretary/_system/after_hours_accounting_v2
              "Бухгалтерия сейчас не работает. Мы записали ваше обращение, и бухгалтерия перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
delivery   -> sound:ai_secretary/_system/after_hours_delivery_v2
              "Отдел доставки сейчас не работает. Мы записали ваше обращение, и отдел доставки перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
```

Opening prompt:

```text
sound:ai_secretary/_system/prompt_1
"Здравствуйте. Меня зовут Анна. Я виртуальный секретарь. По какому вопросу вы обращаетесь?"
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

## Branch Name

```text
feat/node-009-business-hours-and-after-hours-handoff
```
