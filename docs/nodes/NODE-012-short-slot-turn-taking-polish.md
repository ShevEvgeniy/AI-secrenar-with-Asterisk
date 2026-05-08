# NODE-012 Short-Slot Turn-Taking Polish

## Goal

Smooth short-slot turn-taking around CITY and related terminal/retry paths without changing business logic, transfer targets, after-hours behavior, callback persistence, or PHONE digit safety.

## Branch

```text
feat/node-012-short-slot-turn-taking-polish
```

## Traceable Commits

```text
8299096 NODE-012 validate city transcript safely
52f4758 NODE-012 enforce Russian-only dialog invariant
bcbfbb7 NODE-012 use static city retry prompt
866cf75 NODE-012 wait for safe finish playback
05a1387 NODE-012 accept compound city location answers
61bf9eb NODE-012 use conservative city retry talk detect
```

## Validated Result

PASS for normal sales flow with compound CITY/address.

Final live smoke:

```text
CALL_ID=1778258401.18
```

Validated:

- ISSUE resolved to sales from `купить`.
- NAME captured.
- CITY accepted compound location:
  - raw: `Владимирская область, Петушки, Красноармейская улица, 141.`;
  - `city_transcript_validation status=ok`;
  - `reason=region_with_location_detail`;
  - `accepted=true`;
  - `canonical_city=Владимирская область`;
  - `location_detail=Петушки, Красноармейская улица, 141`;
  - transition `CITY -> PHONE`.
- PHONE remained conservative with `phone_digit_safety_skip`.
- PHONE_CONFIRM fast path worked with static digit sequence.
- `phone_confirmed=true` only after caller confirmation `Верно.`
- `missing_required_fields=[]` before transfer.
- Transfer to `sales_real` completed with `status=ok`.

## Also Validated

- English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye` is rejected for CITY.
- Russian-only caller-facing invariant added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase now waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- Compound city/location validator accepts region/city anchor plus detail.

## Known Remaining UX Debt

- CITY and PHONE can still have long recording windows.
- PHONE is intentionally conservative for digit safety.
- Further pause reduction should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike, not NODE-012.

## Status

Done and ready to close.

## Next Recommendation

Open the next bounded node only after master records NODE-012 completion.
