# Master Status

## Current State

- Branch: `master`
- Source-of-truth commit: `990dc59`
- Source-of-truth commit message: `Merge pull request #11 from ShevEvgeniy/feat/node-032i-controlled-persistent-gateway-service-install-start-smoke`
- Repository location: `C:\Projects\AI-secrenar-with-Asterisk`
- Master docs initialized: yes.
- Latest completed node branch: `feat/node-032i-controlled-persistent-gateway-service-install-start-smoke`
- Latest completed node commit: `990dc59`
- Chat bootstrap: `docs/master/CHAT_BOOTSTRAP.md`
- Planned next technical node: `NODE-032J / gateway-service-enable-policy-and-autostart-decision`

## Confirmed Working

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are already in `master`.
- Transfer flow via ARI continue is already in `master`.
- Publish pipeline remains resilient under partial publish failure.
- Publish failures now include explicit classification, including `reason` and `failed_step`.
- `user_transcribed` is no longer sourced from canned placeholder text.
- Transcription is tied to the real downloaded caller audio artifact.
- Transcription artifact identity is traceable through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
- Stale local turn artifacts are explicitly discarded and logged.
- Fallback media no longer degrades to `demo-congrats`.
- Stage and transfer fallback paths now use controlled meaningful fallback phrases.
- Successful PHONE capture now leads to `play_transfer_phrase -> transfer`.
- The generic reply path after PHONE is no longer taken on the validated live call.
- Turn-based real-call recording now uses stage-specific contours to reduce dead air.
- PHONE now requires explicit confirmation before validated completion and transfer.
- Runtime events now trace prompt, record, download, STT, decision, transfer phrase, and transfer latency.
- Turn-taking contour is stabilized for the current flow.
- NAME no longer breaks the whole flow.
- NAME playback barrier is in place.
- PHONE and PHONE_CONFIRM work in live flow.
- Confirmation prompt now speaks the phone number as spoken digits.
- NAME capture quality is hardened without changing the overall call architecture.
- STT for NAME explicitly uses Russian language and Russian-name prompt context.
- Bounded post-STT normalization for Russian names, patronymics, and common conversational forms is present.
- NAME prompt wording is simplified to: `Назовите, пожалуйста, ваше имя.`
- Bounded department intent routing works for sales, accounting, and delivery.
- Routing remains deterministic and debuggable.
- Final transfer phrase is department-specific.
- Immediate transfer requests no longer bypass required data collection.
- Mandatory data before live transfer remains `name`, `city`, `phone`, and `phone_confirmed=true`.
- Stage-aware responses are implemented when the caller asks for immediate transfer.
- Bounded `INTENT_CLARIFY` is implemented for unclear or tied department intent.
- `SAFE_FINISH` is terminal/non-transfer and uses reason-based spoken phrases before hangup.
- Bounded working-hours vs after-hours behavior is implemented.
- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped and logged.
- Mandatory data collection is still enforced before after-hours completion.
- Department-specific after-hours phrases are implemented for sales, accounting, and delivery.
- After-hours phrase playback completes before hangup.
- Bounded local callback persistence is implemented.
- Callback persistence format is JSONL, one flat JSON object per line.
- Callback records persist for `after_hours_callback` and `safe_finish` trigger points.
- Callback persistence is fail-soft and does not crash call flow.
- Stage-level latency instrumentation is implemented for the normal ARI call flow.
- PHONE_CONFIRM fast path uses static/prepublished prefix, digit, and suffix sounds when `phone_digits` are available.
- Normal PHONE_CONFIRM no longer requires per-call dynamic TTS/publish.
- ISSUE and INTENT_CLARIFY have prompt playback barriers before recording.
- PHONE is explicitly excluded from TALK_DETECT early stop with `phone_digit_safety_skip`.
- CITY transcript validation accepts compound region/city/address answers with a city or region anchor.
- English/STT filler is rejected for CITY.
- Russian-only caller-facing invariant is added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Feature-flagged OpenAI Realtime Whisper STT adapter is implemented.
- Streaming STT fallback to the existing batch Whisper path is implemented.
- Streaming STT latency/event instrumentation is implemented.
- Default STT behavior remains unchanged unless `STT_STREAMING_ENABLED=true`.
- NODE-001 live smoke validation passed:
  - stage prompts progressed correctly;
  - user speech was transcribed for ISSUE / NAME / CITY / PHONE;
  - transfer phrase played;
  - transfer completed with `status=ok` to `from-internal,sales_real,1`.

## Completed Nodes

NODE-031A creates the docs-only chat bootstrap and workflow boundary:

```text
new GPT chat bootstrap -> future feature-branch plus PR workflow -> Control Plane closeout/evidence boundary
```

NODE-031A does not implement `NODE-031 / productionize-gateway-runtime-boundary`.

NODE-031 defines the production gateway runtime boundary:

```text
docs/templates only -> service ownership -> systemd/supervisor -> private listen -> restricted firewall -> TLS proxy -> secure env -> redacted logs
```

NODE-031 does not perform live deployment, live smoke, server action, Notion write, Runtime/Evidence create, GitHub write, or source/runtime behavior change.

NODE-001 completed the real sales transfer route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

NODE-002 completed publish hardening:

```text
publish failures -> explicit reason and failed_step -> resilient startup/per-call diagnostics
```

NODE-003 completed transcription integrity and meaningful fallback phrases:

```text
real caller audio artifact -> traceable transcription metadata -> no fabricated user_transcribed text
```

NODE-004 restored the post-PHONE transfer invariant:

```text
valid PHONE transcript -> phone_digits saved -> transfer phrase -> ARI continue to from-internal,sales_real,1
```

NODE-005 hardens the turn-based latency contour:

```text
ISSUE tolerant recording -> NAME playback barrier and relaxed recording -> CITY relaxed recording -> PHONE slow-dictation recording -> PHONE_CONFIRM -> explicit latency buckets
```

NODE-006 hardens NAME capture and normalization:

```text
NAME -> language=ru and Russian-name STT prompt -> bounded normalization -> stable flow continues
```

NODE-007 adds bounded department intent routing:

```text
topic intent -> sales/accounting/delivery/default -> explicit transfer target
```

NODE-008 adds mandatory data capture and bounded clarification:

```text
immediate transfer request -> collect required data -> clarify intent/default safely -> transfer only when complete
```

NODE-009 adds business-hours and after-hours handoff:

```text
working hours -> live transfer; after hours -> collect required data -> department callback phrase -> hangup without transfer
```

NODE-010 adds callback capture and persistence:

```text
after_hours_callback/safe_finish -> flat JSONL callback record -> fail-soft persistence logging
```

NODE-011 hardens normal-call latency and silence behavior:

```text
stage latency logs -> static PHONE_CONFIRM -> prompt playback barriers -> TALK_DETECT diagnostics -> MVP-acceptable transfer flow
```

NODE-012 polishes short-slot turn-taking and CITY validation:

```text
Russian-only dialog -> safe CITY validation -> static CITY retry -> SAFE_FINISH playback barrier -> compound CITY/address accepted
```

NODE-013 adds a feature-flagged streaming STT adapter and metrics spike:

```text
stored WAV artifact -> chunked realtime adapter -> metrics/fallback -> batch path preserved
```

NODE-014 proves the server-side true-live ARI media path:

```text
colocated ari_app -> Stasis(ai_secretary) -> snoop_external_media_rtp -> RTP/PCM received
```

NODE-015 closes the production server-side STT strategy:

```text
OpenAI Realtime transcription over approved server egress -> batch fallback/baseline -> local STT benchmark later -> dialog-isolated RTP diagnostics first
```

## Validation Notes

- A false negative occurred during live validation because MicroSIP was using the wrong Windows input device.
- Selecting the correct Windows microphone fixed live dialog capture.
- NODE-001 is merged into `master`.
- NODE-002 is merged into `master`.
- NODE-003 is merged into `master`.
- NODE-004 is merged into `master`.
- NODE-005 is merged into `master`.
- NODE-006 is merged into `master`.
- NODE-007 is merged into `master`.
- NODE-008 is recorded in `master`.
- NODE-009 is merged into `master`.
- NODE-010 is merged into `master`.
- NODE-011 is merged into `master` and closed as MVP-acceptable.
- NODE-012 is merged into `master` and closed.
- NODE-013 is merged into `master` and closed as adapter/metrics spike only.
- NODE-014 is complete as a successful media-path proof; production STT adoption remains out of scope.
- NODE-015 is complete as a planning closeout; no production STT implementation was made.
- During NODE-002 validation, SSH to `92.118.85.117:22` timed out while publishing `prompt_3` and transfer system sounds.
- Despite the partial publish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- Fallback media was used during the live call for missing `prompt_3` and transfer phrase.
- Transfer still completed successfully to `from-internal,sales_real,1`.

## Resolved Follow-Up Issues

- NODE-003 fixed the integrity problem where runtime logs showed transcribed text that did not match what the caller says they actually spoke.
- If no STT backend is configured, transcription is logged as unavailable instead of fabricated.
- Fallback media now uses controlled meaningful fallback phrases instead of `demo-congrats`.
- NODE-004 prevents the generic reply pipeline from running after successful PHONE capture.
- NODE-004 fixed the runtime root cause where the PHONE parser rejected dotted separators from STT output.
- NODE-005 reduces avoidable recording tail latency for NAME, CITY, and PHONE and replaces fixed `30s` recording waits with stage-profile-based waits.
- NODE-005 extends `scripts/latency_report.py` with turn-based hot-path buckets.
- NODE-005 patch 2 applies explicit confirmation only to PHONE. CITY simply re-asks when not confidently accepted.
- NODE-005 patch 2 prevents unconfirmed PHONE from falling through to the generic reply pipeline.
- NODE-005 patch 3 responds to live turn-taking regression: CITY and PHONE end-of-speech were too aggressive, so CITY now uses `7s/3s/13s`, PHONE uses `14s/4s/21s`, and PHONE_CONFIRM uses `4s/2s/9s`.
- NODE-005 patch 3 adds minimum completion floors: CITY requires at least 4 letters, and PHONE requires a complete 10- or 11-digit run before confirmation.
- NODE-005 patch 4 varies PHONE retry prompts by reason (`unclear`, `incomplete`, `rejected`) and prevents immediate repeated retry phrasing.
- NODE-005 patch 5 fixes PHONE_CONFIRM prompt construction so TTS receives spoken digit words while formatted phone text remains available for logs/debug.
- NODE-005 patch 6 fixes PHONE_CONFIRM sequencing with an explicit `PlaybackFinished` barrier plus `400 ms` guard, expands PHONE_CONFIRM timing to `6s/3s/12s`, adds meta-repair handling, adds NAME garbage gating, and regenerates the fixed PHONE prompt as `prompt_4_v2` with `связи -> св+язи` stress preprocessing.
- NODE-005 patch 7 fixes NAME retry-loop regression with reason-based varied NAME prompts, short Russian-name tolerance, NAME meta-repair handling, and a 3-retry bound that advances with `name_unavailable=true`.
- NODE-005 patch 8 fixes PHONE-stage normalization for comma/dot grouped dictation, handles PHONE-stage meta-repair directly, makes dynamic PHONE retry prompts drive playback instead of fixed `prompt_4_v2`, and rejects short English NAME filler such as `Yep.`.
- NODE-005 patch 9 fixes NAME prompt/record overlap with an explicit `PlaybackFinished` barrier plus `400 ms` guard for base NAME and dynamic NAME retry prompts, and relaxes NAME recording to `6s/2s/11s`.
- NODE-005 live smoke confirmed the current full flow reaches `ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer`.
- NODE-006 improves NAME quality and stability but does not introduce multi-department routing.
- NODE-007 validates department routing and department-specific transfer prompts for sales, accounting, and delivery.
- NODE-008 prevents transfer from bypassing required data collection and makes SAFE_FINISH terminal/non-transfer.
- NODE-009 validates working-hours live transfer preservation and after-hours transfer skip with department-specific callback phrases.
- NODE-010 validates local callback JSONL persistence for after-hours callback and SAFE_FINISH outcomes.
- NODE-011 validates normal-call latency instrumentation, static PHONE_CONFIRM, ISSUE capture reliability, TALK_DETECT diagnostics, and preserved sales transfer semantics.
- NODE-012 validates compound CITY/address acceptance while preserving PHONE digit safety and sales transfer semantics.
- NODE-013 validates adapter, metrics, feature flag, and fallback behavior, but does not prove caller-perceived pause reduction in live calls.
- NODE-014 validates colocated/server-side `ari_app`, local sound publish, ARI `Stasis(ai_secretary)`, and `snoop_external_media_rtp` delivery of RTP/PCM chunks to server host `172.18.0.1`.
- NODE-015 recommends approved server egress to OpenAI Realtime transcription as the first production STT candidate, with batch fallback/baseline, local STT deferred until hardware benchmark, and dialog-isolated RTP diagnostics before dialog-driving live STT.
- NODE-016 validates dialog-isolated RTP/STT diagnostics: `rtp_diagnostics_only` can prove RTP/PCM and tolerate dummy batch STT failure without business retries, SAFE_FINISH, transfer, or callback.
- NODE-017 documents restart-safe systemd/autostart for the server-side `ari_app` using secret-free templates, an `/etc/ai-secretary/ari-app.env` environment file, and runtime ARI password loading from `/home/tulauser/asterisk-config/ari.conf`.
- NODE-019 validates that direct OpenAI Realtime egress from the current Asterisk server is blocked with `403 Forbidden`, OpenAI code `unsupported_country_region_territory`, before audio upload.
- NODE-020 defines the supported-region gateway/proxy measurement path, with the OpenAI key stored only on the gateway and no business dialog integration by default.
- NODE-021 implements the prepared minimal supported-region gateway measurement path and Asterisk-side gateway client mode without requiring `OPENAI_API_KEY` on the Asterisk server.
- NODE-022 records the supported-region gateway deployment path and one-off runbook, but live smoke remains blocked because no supported-region gateway host, gateway URL, or gateway token was available.
- NODE-023 deploys the gateway on Kamatera USA / New York 2 and validates a live one-off Asterisk-side gateway measurement: gateway reachable, gateway auth ok, OpenAI Realtime from gateway ok, `chunks_sent=6`, transcript text not logged, and business dialog/systemd profile unchanged.
- NODE-024 defines the future production gateway STT integration boundary: gateway transcript use may connect only at the transcript-source boundary before `apply_turn(...)`, must be disabled by default, must keep the OpenAI key gateway-only, must not log transcript text by default, and must preserve NODE-016 diagnostic isolation plus all current business contracts.
- NODE-025 implements the controlled gateway STT adapter at that boundary while keeping production gateway STT and dialog transcript use disabled by default.
- NODE-026 validates the NODE-025 adapter through a local-only dry-run with mocks and a localhost fake gateway, using fake secrets only.

## NODE-004 Live Smoke

- `call_id`: `1777641576.42`
- ISSUE / NAME / CITY / PHONE each reached `user_transcribed=ok`.
- After PHONE, events showed `play_transfer_phrase` followed by `transfer status=ok`.
- Transfer completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

- `pipeline_start`, `build_response`, and `reply.wav` did not occur after PHONE in the validated call.

## NODE-005 Validation

- Focused regression suite passed:

```text
python -m pytest tests/test_dialog_flow.py tests/test_post_phone_transfer.py tests/test_turn_latency_hardening.py tests/test_latency_report.py
```

- Full local suite attempted:

```text
python -m pytest
```

Result: 46 passed, 6 failed. Failures were outside NODE-005: missing `src/scripts/make_demo_audio.py` for synth pipeline tests, and a blocked Hugging Face model fetch in `test_events_and_artifacts_overrides_use_single_directory`.

- Live validation reference:
  - `call_id`: `1777717705.10`
  - ISSUE captured successfully.
  - NAME required one retry, then was accepted.
  - CITY captured successfully.
  - PHONE captured successfully.
  - PHONE_CONFIRM accepted positive confirmation.
  - Transfer completed with `status=ok`.

Current validated transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

## NODE-006 Validation

- `call_id`: `1777721580.0`
- ISSUE captured successfully.
- NAME captured successfully with:
  - `stt_language=ru`;
  - Russian-name STT prompt present;
  - recognized NAME: `Иван Семёнович`.
- CITY captured successfully.
- PHONE captured successfully.
- PHONE_CONFIRM accepted positive confirmation.
- Transfer completed with `status=ok`.

Current validated transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

## NODE-007 Validation

Current validated collection flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

Unclear intent remains bounded and routes to the configured default department.

Department-specific transfer phrases:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

Live validation references:

- Sales: `call_id=1777725117.4`; issue matched sales intent; transfer target `department=sales`, `context=from-internal`, `extension=sales_real`, `priority=1`.
- Accounting: `call_id=1777726120.10`; issue matched accounting intent; accounting phrase resolved and played; transfer target `department=accounting`, `context=from-internal`, `extension=accounting`, `priority=1`.
- Delivery: `call_id=1777726440.12`; issue matched delivery intent; delivery phrase resolved and played; transfer target `department=delivery`, `context=from-internal`, `extension=delivery`, `priority=1`.

## NODE-008 Validation

Mandatory data before live transfer:

```text
name
city
phone
phone_confirmed=true
```

Focused regression:

```text
tests/test_dialog_flow.py
tests/test_post_phone_transfer.py
```

Latest focused result:

```text
42 passed in 2.73s
```

Implementation notes:

- PHONE and PHONE_CONFIRM are governed by stage-local policy rather than generic accumulated turn cutoff.
- `INTENT_CLARIFY` timeout and empty outcomes are normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` supports reason-based phrases for `missing_required_data`, `intent_not_resolved`, and `phone_not_confirmed`.

## NODE-009 Validation

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

Traceable implementation commits:

```text
bd63f42115224a5d9e75d2ca431bcc558b8e42ee
5dfb0c3d61644f52bd3acf18a87f2014fdeb8ab9
ce230c96cefb321e1e5dcabe3d9de4defa776254
b0d1efbb793c1c860e4acb8d3cf8414a73b34e93
```

## NODE-010 Validation

Targeted tests:

```text
tests/test_department_routing.py
tests/test_post_phone_transfer.py
```

Targeted result:

```text
21 passed
```

Broader reported full-suite result:

```text
101 passed, 6 unrelated environment failures
```

Live validation confirmed callback persistence succeeded with:

```text
outcome_type=after_hours_callback
outcome_reason=mode_override
record_id=f0cff987b252b77c
path=data/storage/callbacks/callback_records.jsonl
```

## NODE-011 Validation

Final live smoke:

```text
call_id=1778089554.24
```

Validated:

- ISSUE captured successfully: `Я бы хотел купить сетку Манье.`
- `department_intent=sales`
- `intent_reason=matched_sales`
- matched keyword: `купить`
- name captured: `Антон Вячеславович`
- city captured: `Самара`
- phone captured and normalized: `9600614112`
- PHONE_CONFIRM fast path used with `dynamic_tts_required=false` and `publish_required=false`
- confirmation captured: `Да, верно`
- `missing_required_fields=[]`
- transfer to `sales_real` completed with `status=ok`
- transfer happened only after `phone_confirmed=true`

Focused NODE-011 regression:

```text
tests/test_turn_latency_hardening.py
```

Focused result:

```text
16 passed
```

Relevant voice/dialog regression result:

```text
66 passed
```

Broader reported full-suite result:

```text
114 passed, 6 unrelated environment failures
```

Known remaining limitation:

- NAME, CITY, and PHONE_CONFIRM still have noticeable recording-window pauses.
- `recording_early_stop_used` is not yet reliable.
- PHONE remains longer by design for digit safety.

## Next Recommended Step
## NODE-012 Validation

Final live smoke:

```text
CALL_ID=1778258401.18
```

Result:

```text
PASS for normal sales flow with compound CITY/address.
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

Also validated:

- English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye` is rejected for CITY.
- Russian-only caller-facing invariant added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- Compound city/location validator accepts region/city anchor plus detail.

Known remaining UX debt:

- CITY and PHONE can still have long recording windows.
- PHONE is intentionally conservative for digit safety.
- Further pause reduction should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike, not NODE-012.

## Next Recommended Step

```text
Completed by NODE-016 / dialog-isolated-rtp-diagnostics-and-server-stt-measurement.
```

## NODE-014 Validation

Result:

```text
PASS as successful media-path proof.
```

Final proof commit:

```text
8879372 Record NODE-014 server-side RTP proof
```

Validated:

- Colocated/server-side `ari_app` near Asterisk works.
- Local sound publish works without SSH.
- Asterisk ARI listens on `Stasis(ai_secretary)`.
- `snoop_external_media_rtp` successfully sends RTP from the Asterisk container to server host `172.18.0.1`.
- Runtime logs confirmed `stt_live_rtp_packets_received_count > 0`.
- Runtime logs confirmed `stt_live_pcm_chunks_created_count > 0`.
- Runtime logs confirmed `stt_live_rtp_diagnostics_result=rtp_packets_received`.

Boundary:

- Production STT adoption is explicitly out of scope for NODE-014.
- The later dialog failure was expected because batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1` for RTP-only diagnostics.

Uncommitted artifacts intentionally left out:

```text
data/storage/
node014-server.tar
```

## Next Recommended Step

```text
Completed by NODE-016 / dialog-isolated-rtp-diagnostics-and-server-stt-measurement.
```

## NODE-015 Validation

Result:

```text
PASS as docs-only planning closeout.
```

Decision:

- Best first production STT candidate is colocated `ari_app` using the proven `snoop_external_media_rtp` media path and OpenAI Realtime transcription over approved server egress.
- Direct server egress is acceptable if operations approves network policy and secret handling; otherwise use a controlled outbound proxy/gateway.
- Batch Audio API STT remains fallback/baseline during rollout.
- Local STT is deferred until actual server CPU/RAM/GPU and real telephony latency are benchmarked.
- RTP diagnostics should be fully dialog-isolated before production STT drives dialog, so dummy or blocked STT endpoints do not poison business validation or force misleading SAFE_FINISH.
- Production STT adoption remains a separate explicit implementation decision.

Next implementation:

```text
NODE-016 / dialog-isolated-rtp-diagnostics-and-server-stt-measurement
```

## NODE-016 Validation

Result:

```text
PASS as dialog-isolated RTP/STT diagnostics closeout.
```

Server smoke:

```text
call_id=1778668979.22
stage=ISSUE
provider=rtp_diagnostics_only
topology=snoop_external_media_rtp
advertised_host=172.18.0.1
stt_live_rtp_packets_received_count=429
stt_live_pcm_chunks_created_count=429
stt_live_rtp_diagnostics_result=rtp_packets_received
diagnostic_call_finished status=ok
```

Validated:

- Batch STT failed as expected against dummy `OPENAI_BASE_URL` / `ConnectError`.
- `stt_live_diagnostics_dialog_bypass` was emitted.
- `diagnostic_dialog_isolated=true`.
- `dialog_state_preserved=true`.
- `safe_finish_suppressed=true`.
- `transfer_suppressed=true`.
- `callback_suppressed=true`.
- Final diagnostic state stayed at `ISSUE` with `turns_done=0`.

Decision:

- Isolated RTP diagnostics can now be used on the server without poisoning normal business dialog evidence.
- Dummy or unavailable STT in diagnostics no longer causes misleading business SAFE_FINISH/retry/transfer/callback behavior.

## NODE-017 Validation

Result:

```text
PASS as docs/templates closeout.
```

Deliverables:

```text
docs/nodes/NODE-017-server-side-ari-app-systemd-autostart.md
deploy/examples/systemd/ari-app.env.example
deploy/examples/systemd/ai-secretary-ari-wrapper.sh
deploy/examples/systemd/ai-secretary-ari.service
```

Validated plan:

- Service runs as `tulauser`.
- Startup is ordered after `network-online.target` and `docker.service`.
- Restart policy is `Restart=on-failure` with `RestartSec=5`.
- Logs stay in journald.
- `PYTHONUNBUFFERED=1` and `PYTHONPATH=src` are set.
- `/etc/ai-secretary/ari-app.env` carries runtime non-secret config and diagnostic-safe placeholders.
- `ARI_PASSWORD` is read at runtime from `/home/tulauser/asterisk-config/ari.conf`.
- The safe profile keeps `STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only`, `STT_LIVE_OPENAI_DISABLED=true`, and `STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true`.
- Production OpenAI STT remains a separate scoped node.

## NODE-018 Validation

Result:

```text
PASS as server-side systemd/autostart application and reboot smoke.
```

Server:

```text
92.118.85.117
/home/tulauser/AI-secrenar-with-Asterisk-node014
```

Installed:

- `/etc/ai-secretary/ari-app.env`
- `/usr/local/bin/ai-secretary-ari-wrapper`
- `/etc/systemd/system/ai-secretary-ari.service`
- `/etc/systemd/system/ai-secretary-ari.service.d/local-publish-permissions.conf`

Final reboot validation:

```text
ai-secretary-ari.service enabled
ai-secretary-ari.service active
ExecStartPre=/usr/bin/chmod 0711 /var/lib/docker status=0/SUCCESS
ARI_LISTENING http://127.0.0.1:8088/ari ai_secretary
ARI_WS_CONNECTED
SYSTEM_SOUNDS_DONE ok
READY_WAITING_FOR_CALLS
```

Smoke:

```text
call_id=1778672473.13
provider=rtp_diagnostics_only
topology=snoop_external_media_rtp
advertised_host=172.18.0.1
stt_live_rtp_packets_received_count=228
stt_live_pcm_chunks_created_count=228
stt_live_rtp_diagnostics_result=rtp_packets_received
stt_live_diagnostics_dialog_bypass status=handled
diagnostic_call_finished status=ok
dialog_stage_at_finish=ISSUE
turns_done=0
```

Validated:

- Service starts after reboot without manual shell exports.
- Local publish remains `ASTERISK_PUBLISH_MODE=local`.
- `ARI_PASSWORD` is read at runtime from `/home/tulauser/asterisk-config/ari.conf`.
- Installed env contains only dummy OpenAI diagnostics values.
- Dummy batch STT failure against `127.0.0.1:9` was isolated.
- No business `safe_finish`, `transfer`, or `callback` action occurred during the diagnostic smoke.

## NODE-019 Validation

Result:

```text
PASS as direct-egress measurement closeout; direct OpenAI Realtime is blocked from the current server region.
```

Observed:

```text
endpoint=api.openai.com/v1/realtime
status_code=403 Forbidden
openai_error_code=unsupported_country_region_territory
chunks_sent=0
```

Validated:

- Direct egress reached OpenAI but failed before session creation.
- No audio was uploaded.
- No production STT was enabled.
- `ai-secretary-ari.service` remained in `rtp_diagnostics_only`.
- Business dialog remained unchanged.

## NODE-020 Validation

Result:

```text
PASS as supported-region gateway/proxy design and prepared measurement node.
```

Deliverables:

```text
docs/nodes/NODE-020-openai-realtime-supported-region-gateway-proxy.md
docs/stt_gateway_protocol.md
deploy/examples/gateway/openai-realtime-gateway.env.example
deploy/examples/gateway/asterisk-stt-gateway-client.env.example
```

Decision:

- Use a supported-region gateway for OpenAI Realtime measurement.
- Keep `OPENAI_API_KEY` on the gateway only.
- Start with a one-shot HTTP WAV measurement gateway.
- Return redacted metrics and transcript presence flags by default.
- Defer streaming relay and production dialog integration.
- Keep NODE-016 diagnostic isolation and NODE-018 systemd profile intact.

Next implementation:

```text
NODE-021 / supported-region-gateway-minimal-realtime-measurement
```

## NODE-021 Validation

Result:

```text
PASS as prepared gateway measurement path. Live supported-region measurement not run because no gateway host was available during this node.
```

Implemented:

- `src/ai_secretary/stt/realtime_gateway.py` minimal FastAPI gateway skeleton.
- `src/ai_secretary/stt/realtime_measurement.py` gateway client mode using gateway URL/token only.
- Raw `audio/wav` one-shot upload to `/v1/stt/realtime-measurement`.
- Gateway-owned `OPENAI_API_KEY` boundary.
- Redacted structured success/error JSON with transcript presence flags but no transcript text by default.
- Secret-free gateway and Asterisk-side env examples updated.

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests\test_realtime_measurement.py tests\test_realtime_gateway.py
```

Result:

```text
16 passed
```

Syntax validation:

```text
AST parse passed for realtime_measurement.py and realtime_gateway.py.
```

Next implementation:

```text
NODE-022 / deploy-supported-region-gateway-and-run-live-measurement
```

## NODE-022 Validation

Result:

```text
BLOCKED as live supported-region gateway smoke; PASS as exact deployment/runbook and honest redacted result capture.
```

Reason:

```text
No supported-region host, gateway URL, or gateway token was available during this node.
```

Recorded structured result:

```text
gateway_reachable=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
asterisk_server_openai_key_present=no
chunks_sent=not_available
transcript_present=unknown
transcript_text_logged=false
error_type=supported_region_gateway_unavailable
error_status=not_available
error_redacted=true
business_dialog_changed=false
systemd_profile_changed=false
```

Delivered:

- `docs/nodes/NODE-022-deploy-supported-region-gateway-and-run-live-measurement.md`
- Exact supported-region gateway deployment path: `/opt/ai-secretary-realtime-gateway`
- Exact gateway secret env path: `/etc/ai-secretary/openai-realtime-gateway.env`
- Exact Asterisk-side one-off measurement command using `REALTIME_GATEWAY_URL` and `REALTIME_GATEWAY_TOKEN` only.

Preserved:

- `OPENAI_API_KEY` was not placed on the Asterisk server by this node.
- `ai-secretary-ari.service` remains in the safe `rtp_diagnostics_only` profile.
- Business dialog is unchanged.
- Gateway STT is not enabled for production calls.

Next implementation:

```text
Provision supported-region gateway host and rerun the NODE-022 one-off gateway smoke.
```

## NODE-023 Validation

Result:

```text
PASS as live supported-region gateway smoke.
```

Gateway:

```text
host=Kamatera USA / New York 2
public_ip=45.61.48.199
deploy_path=/opt/ai-secretary-gateway
protocol=HTTP for smoke
port=8080
```

Structured result:

```text
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
asterisk_server_openai_key_present=no
chunks_sent=6
transcript_present=false
transcript_text_logged=false
error_type=none
error_status=none
error_redacted=true
business_dialog_changed=false
systemd_profile_changed=false
```

Validated:

- Gateway owned `OPENAI_API_KEY` and `GATEWAY_TOKEN` through `/etc/ai-secretary/openai-realtime-gateway.env`.
- Asterisk-side measurement used only gateway URL/token.
- OpenAI Realtime connection and transcription session creation succeeded from the gateway.
- Transcript text was not requested, returned, or logged.
- `ai-secretary-ari.service` stayed active in `rtp_diagnostics_only`.
- Gateway process was stopped after smoke because it was plain HTTP on a public IP and NODE-023 required only one measurement.

Next implementation:

```text
Productionize supported-region gateway or adopt live STT in a separate scoped node.
```

## NODE-024 Validation

Result:

```text
PASS as docs-only production integration boundary design.
```

Recorded boundary:

```text
production_gateway_stt_enabled=false
business_dialog_changed=false
systemd_profile_changed=false
live_server_changed=false
openai_key_on_asterisk=false
gateway_secret_committed=false
config_scaffolding_added=false
runtime_behavior_changed=false
```

Accepted future constraints:

- Gateway-backed STT may drive business dialog only after explicit disabled-by-default adapter implementation and a later enablement decision.
- `OPENAI_API_KEY` stays on the supported-region gateway, not on the Asterisk server.
- Asterisk-side gateway auth uses only secret runtime gateway token config.
- Transcript text is not logged by default.
- Gateway unavailable/auth failure/timeout/empty transcript/low-quality transcript falls back to the current deterministic prompt/retry behavior.
- Russian-only caller-facing behavior and PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, and SAFE_FINISH contracts remain mandatory gates.
- NODE-016 diagnostic isolation and NODE-014 RTP topology remain mandatory gates.

Next implementation:

```text
NODE-025 / controlled-disabled-by-default-gateway-stt-adapter-implementation
```

## NODE-025 Validation

Result:

```text
PASS as disabled-by-default gateway STT adapter implementation.
```

Implemented:

- `src/ai_secretary/stt/gateway_adapter.py` Asterisk-side gateway adapter using only gateway URL/token.
- Integration in `ari_app.py` before `apply_turn(...)`, behind `STT_GATEWAY_STT_ENABLED` or `STT_GATEWAY_ADAPTER_ENABLED` plus `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG`.
- Safe fallback for missing config, auth failure, timeout, unavailable gateway, malformed response, empty transcript, and low-quality transcript.
- Transcript text redaction by default.

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py
22 passed

.\.venv\Scripts\python.exe -m pytest tests/test_dialog_flow.py
45 passed

.\.venv\Scripts\python.exe -m pytest tests/test_transcription_integrity.py
38 passed
```

Preserved:

- Production gateway STT remains disabled.
- Business dialog is unchanged by default.
- `ai-secretary-ari.service` was not changed.
- No live server was modified.
- Kamatera gateway was not started.
- Asterisk runtime env was not changed.
- `OPENAI_API_KEY` is not required on Asterisk.
- No gateway secret was committed.

Next implementation:

```text
NODE-026 / controlled local adapter smoke / dry-run validation
```

## NODE-026 Validation

Result:

```text
PASS as controlled local adapter smoke / dry-run validation.
```

Dry-run method:

```text
pytest fake/mocked gateway plus localhost-only fake HTTP gateway
```

Validated:

- Gateway STT remains disabled by default.
- Disabled flags make no gateway call.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` prevents gateway network use and falls back to batch at the ARI boundary.
- Explicit local dry-run config reads fake gateway URL/token from env.
- Local fake gateway auth success can produce `transcript_text_present=true`.
- Explicit local transcript use can drive the transcript-source boundary only when both gateway and dialog-use flags are enabled.
- Empty transcript, malformed response, timeout, unavailable gateway, and auth failure fall back safely.
- Transcript text is not logged by default.
- No `OPENAI_API_KEY` or real gateway token is required.
- No live servers were modified, Kamatera gateway was not started, and no live calls were run.

Focused NODE-026 smoke:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
9 passed
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
108 passed
```

Next implementation:

```text
NODE-027 / controlled gateway adapter live smoke with explicit temporary flags
```

## NODE-027 Validation

Result:

```text
BLOCKED as controlled live smoke; safe one-off adapter smoke helper added.
```

Implemented:

- `src/ai_secretary/stt/gateway_adapter_smoke.py` manual CLI helper for the NODE-025 adapter path.
- Redacted JSON smoke report fields for gateway reachability, auth, OpenAI Realtime status, `chunks_sent`, transcript presence, transcript logging, fallback reason, and default-disabled verification.
- Focused fake-gateway tests proving helper redaction, explicit flag requirements, empty-transcript fallback reporting, and default-disabled behavior.

Live attempt:

```text
kamatera_gateway_ssh=false
kamatera_gateway_ssh_blocker=connection_refused_on_45.61.48.199_port_22
gateway_started=false
gateway_reachable_from_asterisk=false
adapter_enabled_temporarily=false
adapter_smoke_exercised_node025_path=false
openai_realtime_from_gateway=not_run
gateway_auth=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=gateway_not_started
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_after_smoke=not_verified_by_ssh_port_8080_unreachable
live_call_run=false
real_secrets_committed=false
```

Asterisk runtime remained in the diagnostic-safe profile:

```text
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Focused helper validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
12 passed
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
111 passed
```

Next implementation:

```text
NODE-028 / rerun controlled gateway adapter live smoke after gateway SSH recovery
```

## NODE-028 Validation

Result:

```text
PASS as controlled live adapter smoke with empty-transcript fallback and cleanup preserved.
```

Live adapter smoke:

```text
kamatera_ssh_restored=true
gateway_started=true
gateway_reachable_from_asterisk=true
adapter_enabled_temporarily=true
adapter_smoke_exercised_node025_path=true
openai_realtime_from_gateway=ok
gateway_auth=ok
chunks_sent=15
transcript_present=false
transcript_used_for_dialog=false
transcript_text_logged=false
fallback_reason=empty_transcript
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_after_smoke=stopped
live_call_run=false
real_secrets_committed=false
```

Cleanup note:

```text
Gateway process pid=1170 was stopped after the helper smoke.
Port 8080 was no longer listening after cleanup.
Temporary Asterisk source/audio/token files were removed.
```

Asterisk runtime remained in the diagnostic-safe profile:

```text
ai-secretary-ari.service=active
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

Required focused suite:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_dialog_flow.py tests/test_transcription_integrity.py
111 passed
```

Next recommendation:

```text
Productionize the gateway only in a separate scoped node, or run a separate non-silent speech-quality adapter smoke.
```

## NODE-029 Validation

Result:

```text
PASS as local diagnostic closeout; no live diagnostic was run.
```

Implemented:

- Audio payload diagnostics for duration, sample rate, channels, sample width, codec, byte/chunk stats, RMS, peak, non-silent ratio, and quality classification.
- Realtime response diagnostics for event-type counts, transcript-event visibility, error-event visibility, commit-sent status, timeout status, and close status.
- Adapter smoke report propagation of the new redacted diagnostic fields.

Diagnosis:

```text
NODE-028 used a synthetic silent 24 kHz mono WAV.
audio_quality_classification=near_silent
likely_root_cause=silent synthetic audio artifact unsuitable for transcription
gateway_auth=ok from NODE-028
openai_realtime_from_gateway=ok from NODE-028
transcript_present=false
transcript_text_logged=false
```

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_realtime_measurement.py tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py
31 passed
```

Next recommendation:

```text
Run one controlled non-sensitive speech WAV diagnostic through the same gateway path before investigating deeper Realtime protocol changes.
```

## NODE-030 Validation

Result:

```text
PASS as controlled live Russian speech WAV gateway adapter smoke.
```

Implemented:

- Manual smoke helper can perform a measurement request while `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- Normal ARI business behavior remains unchanged: dialog-use disabled still prevents gateway network use in the business path.
- Added focused fake-gateway coverage proving transcript presence can be measured without logging text or using it for dialog.

Live adapter smoke:

```text
speech_wav_source=existing_safe_fixture
real_caller_audio_used=false
audio_payload_valid=true
audio_duration_ms=4662
audio_sample_rate_hz=24000
audio_channels=1
audio_sample_width_or_codec=2 / pcm
audio_total_bytes=223878
audio_chunk_count=24
audio_rms=2666.07
audio_peak=29521
audio_non_silent_ratio=0.5535
audio_quality_classification=valid_speech_candidate
gateway_started=true
gateway_reachable_from_asterisk=true
adapter_smoke_exercised_node025_path=true
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=24
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_present=true
transcript_text_logged=false
transcript_used_for_dialog=false
fallback_reason=gateway_stt_dialog_use_disabled
error_status=200
```

OpenAI event diagnostics:

```text
session.created=1
session.updated=1
input_audio_buffer.committed=1
conversation.item.input_audio_transcription.delta=22
conversation.item.input_audio_transcription.completed=1
conversation.item.added=1
conversation.item.done=1
```

Cleanup:

```text
gateway_process_after_smoke=stopped
port_8080_after_smoke=not_listening
asterisk_to_gateway_after_cleanup=connection_refused
temporary_token_file_after_smoke=absent
ai-secretary-ari.service=active
asterisk_openai_key_present_after_smoke=no
business_dialog_changed=false
systemd_profile_changed=false
live_call_run=false
```

Interpretation:

```text
NODE-028 empty_transcript was caused by silent/non-speech audio.
Valid speech-bearing Russian WAVs produce transcript-bearing Realtime events through the Kamatera gateway.
```

Focused helper validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_gateway_stt_adapter.py
13 passed
```

Next recommendation:

```text
Productionize the gateway only in a separate scoped node if the project is ready.
```

## NODE-031 Validation

Result:

```text
PASS as docs/templates-only production gateway runtime boundary draft.
```

Delivered:

```text
docs/nodes/NODE-031-productionize-gateway-runtime-boundary.md
deploy/templates/gateway.env.example
deploy/templates/gateway-systemd.service.example
deploy/templates/gateway-nginx-proxy.example
```

Recorded boundary:

```text
live_deployment=false
server_action=false
source_runtime_behavior_changed=false
gateway_stt_enabled=false
business_dialog_changed=false
openai_key_on_asterisk=false
real_secrets_committed=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
```

Validated content:

- Service ownership, systemd/supervision, private listen, firewall allowlisting, TLS/reverse proxy, env permissions, and log redaction are required before persistent production gateway use.
- `OPENAI_API_KEY` remains gateway-only; `GATEWAY_TOKEN` remains secure-runtime only; templates contain placeholders only.
- Gateway STT remains disabled by default and business dialog must not use gateway transcript text unless a later explicit node enables it.
- Rollback covers stopping the gateway service, restoring previous systemd state, closing/restricting ports, removing temporary files, clearing local env, verifying Asterisk has no `OPENAI_API_KEY`, and preserving transcript redaction.

Next recommendation:

```text
NODE-032 / controlled-production-gateway-live-smoke
```

## NODE-032 Phase A

Result:

```text
PASS as preflight and live command plan only.
```

Delivered:

```text
docs/nodes/NODE-032-controlled-production-gateway-live-smoke.md
```

Recorded boundary:

```text
phase_a_only=true
live_apply=false
service_state_changed=false
live_smoke=false
source_runtime_behavior_changed=false
business_dialog_changed=false
openai_key_on_asterisk=false
real_secrets_committed=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
```

Phase A records the exact approval gate:

```text
APPROVE NODE-032 LIVE APPLY/SMOKE
```

Next recommendation:

```text
NODE-032 Phase B / controlled-production-gateway-live-smoke
```

## NODE-032B Phase A

Result:

```text
PASS as readiness/preflight and command plan only.
```

Delivered:

```text
docs/nodes/NODE-032B-controlled-production-gateway-live-apply-and-smoke.md
```

Recorded boundary:

```text
phase_a_only=true
live_apply=false
service_state_changed=false
live_smoke=false
source_runtime_behavior_changed=false
business_dialog_changed=false
openai_key_on_asterisk=false
real_secrets_committed=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
```

NODE-032B Phase A records the exact approval gate:

```text
APPROVE NODE-032B LIVE APPLY/SMOKE
```

No other phrase is approval.

Next recommendation:

```text
NODE-032B Phase B only after exact explicit approval.
```

## NODE-032C Read-Only Inspection

Result:

```text
NO-GO for immediate NODE-032D live apply/smoke.
```

Delivered:

```text
docs/nodes/NODE-032C-live-readonly-production-gateway-readiness-inspection.md
```

Read-only findings:

```text
asterisk_ssh=ok
asterisk_service=active_enabled
asterisk_openai_api_key=absent_from_process_env
gateway_ssh=ok
gateway_service=not_installed_not_enabled
gateway_process=not_running
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env present 600 root:root
gateway_env_openai_key_present=masked
gateway_env_token_present=masked
gateway_listen_443=false
gateway_listen_8080=false
gateway_listen_8081=false
gateway_firewall=ufw active deny incoming allow outgoing
gateway_firewall_8080=allowed from 92.118.85.117
```

Blockers:

- Decide env path: historical `/etc/ai-secretary/openai-realtime-gateway.env` vs planned `/etc/ai-secretary/gateway.env`.
- Install/adapt gateway systemd unit only in an approved future node.
- Install/adapt TLS reverse proxy only in an approved future node.
- Resolve firewall transition from old `8080/tcp` allow to production TLS/proxy plan.
- Prepare rollback commands before any live apply.

Boundary:

```text
live_apply=false
service_started_stopped_restarted_reloaded=false
live_smoke=false
business_dialog_changed=false
real_secrets_logged=false
transcript_text_logged=false
```

## NODE-032D Live Delta Decision

Result:

```text
docs_only_decision_complete=true
live_apply=false
ssh_used=false
service_started_stopped_restarted_reloaded=false
server_state_changed=false
live_smoke=false
business_dialog_changed=false
real_secrets_logged=false
transcript_text_logged=false
```

Accepted live delta for the next node:

```text
first_smoke_env_path=/etc/ai-secretary/openai-realtime-gateway.env
service_name=ai-secretary-gateway.service
unit_path=/etc/systemd/system/ai-secretary-gateway.service
runtime_user_group=gateway:gateway
first_smoke_listen=0.0.0.0:8080
public_tls_proxy_for_first_smoke=false
expose_443=false
open_8081=false
keep_existing_8080_allow_for_first_smoke=true
allowed_smoke_source=92.118.85.117
cleanup_default=stop_rollback_after_smoke
```

Approval gate for future NODE-032E:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

No other phrase is approval.

Next recommendation:

```text
NODE-032E / controlled production gateway first smoke using accepted live delta.
```

## NODE-032E Phase A Live Gate Re-Confirmation / Phase B Hard-Gate NO-GO

Result:

```text
phase_a_live_gate_reconfirmation_complete=true
live_apply=false
service_installed=false
service_started_stopped_restarted_reloaded=false
firewall_changed=false
env_files_edited=false
server_state_changed=false
live_smoke=false
real_secrets_logged=false
transcript_text_logged=false
```

Gate findings:

```text
asterisk_ssh=ok
asterisk_service=active_enabled
asterisk_openai_api_key=absent_from_process_env
gateway_ssh=ok
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env present 600 root:root
gateway_env_openai_key_present=masked
gateway_env_token_present=masked
gateway_service=inactive_or_absent_not_enabled
gateway_listen_443=false
gateway_listen_8080=false
gateway_listen_8081=false
gateway_firewall=ufw active deny incoming allow outgoing
gateway_firewall_8080=allowed from 92.118.85.117
```

Recommendation:

```text
NO-GO for Phase B now because exact approval phrase is absent.
```

Technical gates are ready for a tightly scoped Phase B attempt if re-confirmed immediately before apply and if the operator later provides:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

Phase B update after exact approval:

```text
approval_phrase_confirmed=true
phase_b_no_go=true
reason=required_smoke_helper_path_not_identified_safely_on_asterisk
service_installed=false
systemd_unit_written=false
daemon_reload=false
gateway_service_started=false
firewall_changed=false
env_files_edited=false
live_smoke=false
```

Hard-gate re-confirmation:

```text
asterisk_service=active_enabled
asterisk_openai_api_key=absent_from_process_env
asterisk_smoke_helper=absent
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env present 600 root:root
gateway_secret_presence=masked_pass
gateway_user=absent
gateway_group=absent
gateway_deploy_path=/opt/ai-secretary-gateway present
gateway_unit=absent
gateway_service=inactive_or_absent_not_enabled
gateway_listen_443=false
gateway_listen_8080=false
gateway_listen_8081=false
gateway_firewall_8080=allowed from 92.118.85.117 only
```

Next recommendation:

```text
NODE-032F / prepare-asterisk-side-gateway-smoke-helper-or-approved-smoke-path
```

## NODE-032F Asterisk-Side Gateway Smoke Helper Preparation

Result:

```text
helper_path_prepared=true
selected_helper=scripts/asterisk_gateway_smoke_helper.py
core_helper_reused=ai_secretary.stt.gateway_adapter_smoke
live_deploy=false
ssh=false
server_state_changed=false
service_installed_started_stopped_restarted_reloaded=false
firewall_changed=false
server_env_edited=false
live_smoke=false
business_dialog_enabled=false
real_secrets_logged=false
transcript_text_logged=false
```

Helper boundary:

```text
manual_only=true
requires_asterisk_origin=true
requires_openai_api_key_absent=true
requires_stt_gateway_use_transcript_for_dialog=false
requires_stt_gateway_log_transcript=false
records_business_dialog_unchanged=true
autostart_configured=false
persistent_server_state_created=false
```

Future live command path:

```text
cd /home/tulauser/AI-secrenar-with-Asterisk-node014
python scripts/asterisk_gateway_smoke_helper.py --audio <approved-non-sensitive-smoke-wav>
```

Next recommendation:

```text
NODE-032G / controlled-gateway-live-smoke-with-asterisk-side-helper
```

## NODE-032G Phase A Gate Re-Confirmation And Live Command Planning

Result:

```text
phase_a_gate_reconfirmation_complete=true
live_apply=false
helper_copied_or_deployed=false
service_installed_started_stopped_restarted_reloaded=false
firewall_changed=false
env_files_edited=false
server_state_changed=false
live_smoke=false
business_dialog_enabled=false
real_secrets_logged=false
transcript_text_logged=false
```

Read-only gate findings:

```text
asterisk_ssh=ok
asterisk_service=active_enabled
asterisk_openai_api_key=absent_from_process_env
asterisk_node014_repo_present=true
asterisk_node014_helper_present=false
asterisk_node014_core_helper_present=false
asterisk_node014_git_head=unavailable
gateway_ssh=ok
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env present 600 root:root
gateway_secret_presence=masked_pass
gateway_service=inactive_not_enabled
gateway_listen_443=false
gateway_listen_8080=false
gateway_listen_8081=false
gateway_firewall_8080=allowed from 92.118.85.117 only
```

Phase B helper availability plan:

```text
deploy_temporary_helper_bundle=/tmp/node032g-asterisk-helper
runtime_env_file=/tmp/node032g-gateway-client.env
helper_autostart=false
helper_persistent_state=false
business_dialog_changed=false
```

Phase B remains NO-GO until exact approval:

```text
APPROVE NODE-032G LIVE APPLY/SMOKE
```

Phase B result after exact approval:

```text
approval_phrase_confirmed=true
phase_b_live_smoke_complete=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
openai_realtime_from_gateway=ok
gateway_http_status=200
chunks_sent=28
transcript_present=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
fallback_reason=gateway_stt_dialog_use_disabled
```

Cleanup/final state:

```text
gateway_service=inactive_or_absent_after_cleanup
gateway_unit=absent_after_cleanup
gateway_target_listeners_443_8080_8081=absent
firewall_broadened=false
helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
helper_autostart=false
scheduler_webhook_automation_added=false
```

## NODE-032H Production Gateway Persistence And Reboot Strategy

Result:

```text
docs_only_strategy_complete=true
live_apply=false
ssh=false
server_state_changed=false
service_installed_started_stopped_restarted_reloaded_enabled=false
firewall_changed=false
env_files_edited=false
live_smoke=false
business_dialog_enabled=false
real_secrets_logged=false
transcript_text_logged=false
```

Persistence decision:

```text
persistence_mode=staged_persistence
manual_only_gateway_for_now=true
installed_but_disabled_service_first=true
installed_and_enabled_service_now=false
enable_reboot_smoke_deferred=true
```

Future service policy:

```text
service_name=ai-secretary-gateway.service
unit_path=/etc/systemd/system/ai-secretary-gateway.service
runtime_user_group=gateway:gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
working_directory=/opt/ai-secretary-gateway
listen=0.0.0.0:8080
restart=on-failure
enable_policy=disabled_until_reboot_node
```

Network and safety policy:

```text
listen_8080=acceptable_only_with_source_restricted_firewall
required_source=92.118.85.117
open_443=false
open_8081=false
firewall_broadened=false
asterisk_openai_api_key=false
business_dialog_integration_deferred=true
```

Next recommendation:

```text
NODE-032I / controlled-persistent-gateway-service-and-reboot-smoke
```

## NODE-032I Phase A Persistent Gateway Service Install/Start/Smoke Planning

Result:

```text
phase_a_readiness_and_command_planning_complete=true
phase_b_go=conditional_after_exact_approval
live_apply=false
helper_copied_or_deployed=false
service_installed_started_stopped_restarted_reloaded_enabled=false
systemd_unit_modified=false
user_group_created=false
permissions_changed=false
firewall_changed=false
env_files_edited=false
server_state_changed=false
live_smoke=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
real_secrets_logged=false
transcript_text_logged=false
```

Read-only gate findings:

```text
initial_asterisk_ssh=fresh_check_timeout
initial_gateway_ssh=fresh_check_timeout
rerun_asterisk_ssh=ok
rerun_gateway_ssh=ok
asterisk_service=active_enabled
asterisk_openai_api_key_absence=process_and_service_env_absent
business_dialog_gateway_transcript=not_enabled
gateway_env_presence=present
gateway_env_owner_mode=root:root 600
gateway_secret_presence=masked_pass
gateway_user_group=absent
gateway_deploy_path=/opt/ai-secretary-gateway present root:root 755
gateway_unit=absent
gateway_backup_target=absent
gateway_target_listeners_443_8080_8081=absent
gateway_firewall_8080_source_restriction=92.118.85.117_only
```

Phase B is conditionally GO only after exact approval and immediate hard-gate re-confirmation:

```text
APPROVE NODE-032I SERVICE INSTALL/START/SMOKE
```

Phase B plan:

```text
service=ai-secretary-gateway.service
unit=/etc/systemd/system/ai-secretary-gateway.service
runtime=gateway:gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
working_directory=/opt/ai-secretary-gateway
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
restart=on-failure
enable=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
```

Phase B result after exact approval:

```text
approval_phrase_confirmed=true
hard_gates_passed=true
gateway_user_group=created_locked_system_account
gateway_env_pre=root:root 600
gateway_env_post=root:gateway 640
unit_installed=true
unit_backup_required=false
daemon_reload=true
service_started=true
service_active_after_start=true
service_enabled=false
listener_8080_after_start=true
listener_443=false
listener_8081=false
ufw_8080_allow=92.118.85.117 only
health_endpoint=404_not_available
docs_endpoint=200
controlled_smoke=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
openai_realtime_from_gateway=ok
gateway_http_status=200
chunks_sent=28
transcript_present=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Final state:

```text
service_unit_installed=true
service_active=false
service_enabled=false
target_listeners_443_8080_8081=absent
firewall_changed=false
env_preserved=true
env_owner_mode=root:gateway 640
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
temp_helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation_added=false
```

## NODE-032J Gateway Service Enable Policy And Autostart Decision

Result:

```text
docs_only_decision_complete=true
live_apply=false
ssh=false
server_state_changed=false
service_started_stopped_restarted_reloaded_enabled=false
systemctl_enable=false
firewall_changed=false
env_files_edited=false
live_smoke=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
real_secrets_logged=false
transcript_text_logged=false
```

Current staged service truth from NODE-032I:

```text
unit_installed=true
unit=/etc/systemd/system/ai-secretary-gateway.service
service_active=false
service_enabled=false
runtime_user_group=gateway:gateway
env_owner_mode=root:gateway 640
working_directory=/opt/ai-secretary-gateway
listen=0.0.0.0:8080
restart=on-failure
pythonpath=/opt/ai-secretary-gateway/src
target_listeners_443_8080_8081=absent
firewall_changed=false
reboot_power_cycle_proof=false
business_dialog_integration=false
```

Enable/autostart decision:

```text
policy=separate_controlled_enablement_reboot_smoke
keep_staged_service_installed=true
keep_service_disabled_until_next_exact_approval=true
cleanup_now=false
enable_now=false
business_dialog_integration_now=false
provider_power_cycle_in_next_node=false_unless_separately_scoped
```

Future NODE-032K approval gate:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Next recommendation:

```text
NODE-032K / controlled-gateway-service-enable-and-reboot-smoke
```

Remaining blockers:

```text
enable_reboot_proof=false
node032k_exact_approval_phrase_provided=false
provider_power_cycle=separately_scoped
business_dialog_integration=out_of_scope
```

## NODE-032K Phase A Controlled Gateway Service Enable And Reboot Smoke Planning

Result:

```text
phase_a_readiness_and_command_planning_complete=true
handoff_archive=docs/handoffs/NODE-032K-phase-a-codex-handoff.md
live_enablement=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
service_started_stopped_restarted_reloaded=false
firewall_changed=false
env_files_edited=false
helper_copied_or_deployed=false
live_smoke=false
business_dialog_enabled=false
server_state_changed=false
real_secrets_logged=false
transcript_text_logged=false
```

Read-only gate findings:

```text
asterisk_ssh=ok
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_process_openai_api_key=OPENAI_API_KEY_ABSENT
asterisk_service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
gateway_ssh=ok
gateway_hostname=ai-secretary-gateway-node023
gateway_unit=/etc/systemd/system/ai-secretary-gateway.service present
gateway_unit_verify=ok
gateway_service=inactive
gateway_service_enabled=disabled
gateway_user_group=gateway:gateway present
gateway_env_owner_mode=root:gateway 640
gateway_secret_presence=masked_pass
gateway_deploy_path=/opt/ai-secretary-gateway present
gateway_target_listeners_443_8080_8081=absent
gateway_ufw=active
gateway_ufw_8080=92.118.85.117 only
rollback_tools=systemctl_ss_ufw_available
```

Phase B is conditionally GO only after exact approval and immediate hard-gate re-confirmation:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Planned Phase B sequence:

```text
reconfirm_gates=true
manual_start_and_health_check=true
systemctl_enable=true_after_exact_approval
gateway_reboot=true_after_exact_approval
post_reboot_autostart_check=true
listener_firewall_log_redaction_check=true
one_asterisk_side_smoke=true
provider_power_cycle=false
business_dialog_enablement=false
open_443=false
open_8081=false
tls_proxy_change=false
firewall_broadening=false
```

## NODE-032K Phase B Enable/Reboot Attempt Hard NO-GO

Result:

```text
approval_phrase_confirmed=true
phase_b_result=NO-GO
hard_gates_passed=true
manual_start=true
systemctl_enable=true
gateway_only_reboot=true
post_reboot_autostart_verified=true
controlled_smoke=false
rollback_performed=true
final_service_active=false
final_service_enabled=false
target_listeners_443_8080_8081=absent
firewall_changed=false
provider_power_cycle=false
business_dialog_enabled=false
```

Blocker:

```text
token_value_printed_during_temporary_env_diagnostic=true
transcript_text_printed=false
required_before_retry=rotate_gateway_token
required_before_retry=fix_temp_env_creation_and_verification_path
next_node=NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
```

The Gateway service successfully enabled and auto-started after a Gateway-only reboot, but the Asterisk-side smoke was stopped before a gateway request after token-output safety failed. The exposed token value is not recorded in repo docs. Temporary helper/env/audio were removed from Asterisk, Asterisk still has no `OPENAI_API_KEY`, and the gateway service was disabled/stopped as rollback.

Security remediation:

```text
gateway_token_rotated=true
token_values_printed=false
token_values_recorded=false
env_owner_mode=root:gateway 640
gateway_token_presence=masked_pass
service_active=false
service_enabled=false
target_listeners_443_8080_8081=absent
firewall_changed=false
smoke_retry=false
next_node=NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
```

## NODE-032L Newline-Safe Gateway Smoke Temp Env Guard

Result:

```text
local_implementation_docs_complete=true
new_guard=scripts/gateway_smoke_temp_env_guard.py
helper_hardened=scripts/asterisk_gateway_smoke_helper.py
handoff_archive=docs/handoffs/NODE-032L-codex-handoff.md
live_smoke=false
ssh=false
service_action=false
reboot=false
provider_power_cycle=false
firewall_changed=false
server_env_edited=false
server_state_changed=false
token_values_printed=false
transcript_text_printed=false
```

Safe temp-env behavior:

```text
token_source=stdin_only
newline_safe=true
missing_token_fails_closed=true
cr_lf_token_fails_closed=true
literal_newline_material_fails_closed=true
dialog_transcript_use_required_false=true
transcript_logging_required_false=true
asterisk_openai_api_key_refused=true
temp_env_mode=0600
cleanup_supported=true
```

Next recommendation:

```text
NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
```

## NODE-032M Phase A Safe Temp-Env Retry Readiness

Result:

```text
phase_a_readiness_complete=true
branch=feat/node-032m-controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
handoff_archive=docs/handoffs/NODE-032M-phase-a-codex-handoff.md
live_retry=false
service_action=false
systemctl_state_change=false
reboot=false
provider_power_cycle=false
firewall_changed=false
server_env_edited=false
server_state_changed=false
token_values_printed=false
transcript_text_printed=false
```

Local readiness:

```text
guard=scripts/gateway_smoke_temp_env_guard.py
guard_create_validate_cleanup=true
guard_token_stdin_only=true
guard_masked_json_only=true
guard_cr_lf_rejected=true
helper_newline_material_rejected=true
helper_asterisk_openai_api_key_refused=true
```

Read-only gates:

```text
asterisk_ssh=true
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
gateway_ssh=true
gateway_hostname=ai-secretary-gateway-node023
gateway_unit=present_verify_ok
gateway_service=inactive_disabled
gateway_env_owner_mode=root:gateway 640
gateway_secret_presence=masked_pass
gateway_target_listeners_443_8080_8081=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
rollback_tools=available
```

Phase B approval gate:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

Phase B recommendation:

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
```

## NODE-032M Phase B Safe Temp-Env Enable/Reboot Retry Attempt

Result:

```text
approval_phrase_confirmed=true
systemctl_enable=true
gateway_only_reboot=true
post_reboot_autostart_verified=true
controlled_smoke_attempted=true
controlled_smoke_completed=false
rollback_performed=true
token_values_printed=false
transcript_text_printed=false
provider_power_cycle=false
business_dialog_enabled=false
firewall_changed=false
```

Service proof:

```text
manual_start=ok
service_enabled_after_enable=enabled
post_reboot_service_active=active
post_reboot_service_enabled=enabled
post_reboot_listener=8080 only
post_reboot_forbidden_listeners_443_8081=absent
post_reboot_ufw_8080_allow=92.118.85.117 only
post_reboot_log_sensitive_pattern=absent
```

Safe temp-env:

```text
guard_create=ok_after_one_fail_closed_missing_stdin_attempt
guard_validate=ok
guard_cleanup=ok
temp_env_mode=600
token_input=stdin_pipeline_only
secret_values_printed=false
```

Smoke blocker:

```text
gateway_request_reached=false
smoke_blocker=incomplete_temporary_helper_bundle_missing_ai_secretary.config
error_type=ModuleNotFoundError
missing_module=ai_secretary.config
next_node=NODE-032N / complete-safe-asterisk-helper-bundle-and-retry-plan
```

Final state:

```text
final_service_active=inactive
final_service_enabled=disabled
final_target_listeners_443_8080_8081=absent
firewall_changed=false
env_owner_mode=root:gateway 640
temp_helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
```

## NODE-032N Complete Safe Asterisk Helper Bundle

Result:

```text
node_type=local_repo_implementation_docs
live_retry=false
ssh_used=false
server_state_changed=false
service_action=false
reboot_or_power_cycle=false
firewall_or_env_changed=false
token_values_printed=false
transcript_text_printed=false
```

NODE-032M blocker addressed:

```text
previous_blocker=incomplete_temporary_helper_bundle_missing_ai_secretary.config
root_cause=src/ai_secretary/__init__.py imports ai_secretary.config.settings
selected_fix=explicit_minimal_bundle_manifest_and_preflight_validator
```

Added helper bundle support:

```text
script=scripts/asterisk_gateway_helper_bundle.py
manifest_command=python scripts/asterisk_gateway_helper_bundle.py manifest
create_command=python scripts/asterisk_gateway_helper_bundle.py create --output <bundle-root>
validate_command=python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <bundle-root>
handoff_archive=docs/handoffs/NODE-032N-codex-handoff.md
```

Bundle completeness behavior:

```text
includes_ai_secretary_config=true
preflight_import_validates_gateway_adapter_smoke=true
missing_ai_secretary_config_caught_before_live_retry=true
safe_temp_env_guard_required=true
secret_values_printed=false
transcript_text_logged=false
```

Next recommendation:

```text
NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle
```

## NODE-032O Phase A Complete Helper-Bundle Smoke Retry Readiness

Result:

```text
node_type=phase_a_readiness_command_planning
live_retry=false
service_action=false
systemctl_state_change=false
reboot_or_power_cycle=false
firewall_or_env_changed=false
helper_copy_deploy=false
token_values_printed=false
transcript_text_printed=false
```

Handoff archive:

```text
docs/handoffs/NODE-032O-phase-a-codex-handoff.md
```

Local tooling readiness:

```text
safe_temp_env_guard=scripts/gateway_smoke_temp_env_guard.py
safe_temp_env_commands=create,validate,cleanup
helper_bundle_tool=scripts/asterisk_gateway_helper_bundle.py
helper_bundle_commands=manifest,create,validate
helper_bundle_includes_ai_secretary_config=true
helper_bundle_preflight_validator=true
```

Asterisk read-only gate:

```text
ssh_reachable=true
hostname=tula
ari_service_active=active
ari_service_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
```

Gateway read-only gate:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
gateway_service_active=inactive
gateway_service_enabled=disabled
gateway_user_group=present
gateway_env_owner_mode=root:gateway 640
masked_secret_presence=pass
workdir_present=true
target_listeners_443_8080_8081=absent
ufw_8080_allow=92.118.85.117 only
```

Phase B approval gate:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Phase B recommendation:

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
technical_readiness=pass
```
