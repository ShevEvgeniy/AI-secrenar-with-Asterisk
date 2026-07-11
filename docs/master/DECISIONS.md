# Decisions

## NODE-032BG Decision

NODE-032BG is accepted as a single controlled live smoke proving the Gateway/Auth/OpenAI Realtime path still behaves safely while dialog transcript use is disabled:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
dialog_transcript_used=false
fallback_reason=gateway_stt_dialog_use_disabled
gateway_restored_inactive_disabled=true
```

NODE-032BG is not accepted as a complete live proof of NODE-032BF policy reporting because the deployed Asterisk helper/runtime report did not include the new `business_dialog_transcript_*` fields. Business-dialog transcript use remains disabled. The next node should refresh or validate the deployed helper/runtime policy-field boundary before any enabled-use validation.

## NODE-032BH Decision

NODE-032BH is accepted as a controlled Asterisk helper/runtime reporting refresh.

Pre-refresh, the Asterisk project lacked `src/ai_secretary/telephony/transcript_policy.py`, and safe no-network adapter diagnostics returned `FIELD_MISSING` for the NODE-032BF `business_dialog_transcript_*` fields.

After copying the validated helper bundle files to `/home/tulauser/AI-secrenar-with-Asterisk-node014`, safe diagnostics exposed:

```text
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=false
business_dialog_transcript_used_for_dialog=false
business_dialog_transcript_reason=business_dialog_transcript_disabled
transcript_text_logged=false
dialog_transcript_used=false
```

No Gateway start, Gateway request, smoke, call, OpenAI request, service action, Docker mutation, firewall/env/server/app config mutation, business-dialog transcript enablement, raw token/env output, raw transcript output, transcript delta output, audio artifact, or disk image action occurred.

## Accepted

### Master-Driven Workflow

- `master` is the source-of-truth branch.
- Architecture, status, planning, and project coordination are handled through master-layer documentation.
- Implementation work must be isolated to focused node branches.
- One node equals one task, one branch, and one execution cycle.

### Documentation Layout

- Master docs live under `docs/master/`.
- Node docs live under `docs/nodes/`.

### Scope Discipline

- Do not broadly refactor.
- Do not mix multiple concerns in one node.
- Always preserve tracing and logging.

## Completed Technical Direction

NODE-001 completed the real transfer route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

The existing ARI continue transfer flow is reused. The validated runtime target is:

```text
context=from-internal
extension=sales_real
priority=1
```

Live smoke validation confirmed staged prompts, user speech transcription, transfer phrase playback, and `transfer status=ok`.

## Publish Failure Handling

NODE-002 completed publish hardening. Partial publish failures must remain explicit and diagnosable rather than silently degrading startup or call behavior.

Accepted runtime behavior:

- Startup may continue under partial system-sounds prepublish failure.
- Publish failures must include `reason` and `failed_step`.
- Per-call publish failures must remain visible in traces/logs.
- Existing transfer behavior must continue when fallback media is used.

NODE-002 validation observed SSH timeout to `92.118.85.117:22` while publishing `prompt_3` and transfer system sounds. The listener still reached `READY_WAITING_FOR_CALLS`, and transfer completed to `from-internal,sales_real,1`.

## Transcription Integrity And Fallback Phrases

NODE-003 completed transcription integrity and meaningful fallback phrase handling.

Accepted runtime behavior:

- `user_transcribed` must not be sourced from canned placeholder text.
- Transcription must be tied to the real downloaded caller audio artifact.
- Artifact identity must be traceable through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
- Stale local turn artifacts must be explicitly discarded and logged.
- If no STT backend is configured, transcription must be logged as unavailable instead of fabricated.
- Fallback media must not degrade to `demo-congrats`.
- Stage and transfer fallback paths must use controlled meaningful fallback phrases.

Real live transcription depends on `TELEPHONY_STT_BACKEND` being explicitly configured, for example `openai` or `whisper_api`.

## Turn-Based Latency And Confirmation Flow

NODE-005 completed latency and turn-based hardening for the current dialog flow.

Accepted runtime behavior:

- The current successful live path is:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- NAME prompt playback must complete before NAME recording starts.
- PHONE and PHONE_CONFIRM must work in live flow.
- PHONE_CONFIRM must speak the phone number as spoken digits, not symbolic formatting.
- Successful transfer must continue to:

```text
context=from-internal
extension=sales_real
priority=1
```

NODE-005 validation confirmed transfer with `status=ok` for live call `1777717705.10`. NAME quality still needs a separate focused follow-up in NODE-006.

## Name Capture And Normalization

NODE-006 completed NAME capture and normalization hardening without changing the overall call architecture.

Accepted runtime behavior:

- NAME transcription uses Russian language and Russian-name prompt context.
- NAME prompt wording is:

```text
Назовите, пожалуйста, ваше имя.
```

- Bounded post-STT normalization may handle Russian names, patronymics, and common conversational forms.
- NAME playback barrier remains in place so NAME recording does not start over prompt playback.
- The validated end-to-end flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

NODE-006 validation confirmed recognized NAME `Иван Семёнович` for live call `1777721580.0` and transfer with `status=ok`. Multi-department routing remains out of scope until NODE-007.
## Department Intent Routing

NODE-007 completed bounded department intent routing and department-specific transfer phrases.

Accepted runtime behavior:

- Department intent routing is deterministic and debuggable.
- Supported departments are:
  - sales;
  - accounting;
  - delivery.
- Unclear intent remains bounded and routes to the configured default department.
- The collection flow remains:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

- Final transfer phrases are department-specific:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

NODE-007 live validation confirmed sales, accounting, and delivery routing with department-specific prompts.

## Intent Clarification And Mandatory Data Capture

NODE-008 completed mandatory data gating, stage-aware immediate-transfer responses, bounded intent clarification, and terminal SAFE_FINISH behavior.

Accepted runtime behavior:

- Immediate transfer requests must not bypass required data collection.
- Mandatory data before live transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-aware responses are used when the caller asks for immediate transfer.
- `INTENT_CLARIFY` is bounded for unclear or tied department intent.
- ISSUE retries, then moves to `INTENT_CLARIFY`.
- `INTENT_CLARIFY` retries, then defaults to the configured department.
- NAME/CITY/PHONE use bounded retries, then `SAFE_FINISH`.
- PHONE_CONFIRM has its own bounded policy and must not be cut off by generic global turn limits.
- `INTENT_CLARIFY` timeout and empty outcomes are normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` is terminal/non-transfer and supports reason-based phrases for `missing_required_data`, `intent_not_resolved`, and `phone_not_confirmed`.

NODE-008 focused regression passed with `42 passed in 2.73s`.

## Business Hours And After-Hours Handoff

NODE-009 completed bounded working-hours vs after-hours behavior.

Accepted runtime behavior:

- During working hours, the existing live-transfer flow remains unchanged.
- During after hours, live transfer is skipped.
- Mandatory data collection is still enforced before after-hours completion:
  - issue;
  - name;
  - city;
  - phone;
  - `phone_confirmed=true`.
- Department-specific after-hours phrases exist for sales, accounting, and delivery.
- After-hours phrase playback must complete before hangup.
- Transfer skip must be explicit and logged in after-hours mode.
- Versioned after-hours system sounds must be used for refreshed wording:

```text
sound:ai_secretary/_system/after_hours_sales_v2
sound:ai_secretary/_system/after_hours_accounting_v2
sound:ai_secretary/_system/after_hours_delivery_v2
```

NODE-009 validation recorded `21 passed` for wording/static-sound follow-up and broader focused result `56 passed`.

## Callback Capture And Persistence

NODE-010 completed bounded local callback persistence.

Accepted runtime behavior:

- Callback persistence format is JSONL, one flat JSON object per line.
- Production path is:

```text
data/storage/callbacks/callback_records.jsonl
```

- Persisted schema includes `record_id`, `call_id`, `timestamp`, `department`, `issue`, `name`, `city`, `phone`, `outcome_type`, and `outcome_reason`.
- Records are written for:
  - `after_hours_callback`;
  - `safe_finish`.
- After-hours callback records are persisted after after-hours transfer skip and before final hangup.
- SAFE_FINISH records are persisted with available partial data and terminal reason.
- Persistence is fail-soft and must not crash call flow.
- Persistence logging includes `persistence_attempt`, `persistence_success`, and `persistence_failure`.

NODE-010 live validation confirmed callback persistence with `outcome_type=after_hours_callback`, `outcome_reason=mode_override`, and `record_id=f0cff987b252b77c`.

## Normal Call Latency And Silence Hardening

NODE-011 completed normal-call latency and silence hardening at MVP level.

Accepted runtime behavior:

- Normal working-hours flow remains:

```text
ISSUE -> INTENT_CLARIFY if needed -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Mandatory data before transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-level latency instrumentation must remain available for normal calls.
- PHONE_CONFIRM must use the static fast path when `phone_digits` are available and must not require per-call dynamic TTS/publish on the normal path.
- PHONE remains conservative and excluded from TALK_DETECT early stop with `phone_digit_safety_skip`.
- ISSUE and INTENT_CLARIFY prompt playback barriers must remain in place before recording.
- TALK_DETECT early-stop diagnostics are useful but `recording_early_stop_used` is not yet required as a closure gate for NODE-011.

NODE-011 final live smoke `1778089554.24` passed at MVP level: sales intent was matched from captured ISSUE text, required fields were collected, PHONE_CONFIRM fast path was used, and transfer to `sales_real` completed only after `phone_confirmed=true`.

Remaining short-slot pause smoothing is deliberately moved to NODE-012 and must not change PHONE digit safety, business logic, transfer/callback/after-hours contracts, or SAFE_FINISH behavior.

## Short-Slot Turn-Taking Polish

NODE-012 completed short-slot turn-taking polish for the current bounded scope.

Accepted runtime behavior:

- CITY transcript validation may accept compound region/city/address answers when a valid city or region anchor is present.
- CITY must reject English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye`.
- Caller-facing dialog remains Russian-only.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- PHONE remains conservative with `phone_digit_safety_skip`.
- Transfer still occurs only after `phone_confirmed=true` and no required fields are missing.

NODE-012 final live smoke `1778258401.18` passed for normal sales flow with compound CITY/address. Remaining pause reduction for CITY and PHONE should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike.

## Realtime Whisper STT Adapter Spike

NODE-013 completed a feature-flagged OpenAI Realtime Whisper STT adapter and metrics spike.

Accepted decision:

- Close NODE-013 as adapter/metrics spike only.
- This is not a production adoption decision.
- Default behavior remains batch STT unless `STT_STREAMING_ENABLED=true`.
- Streaming errors fall back to the existing batch Whisper path when configured.
- Metrics and events for first delta, final transcript, streamed audio duration, fallback, and batch baseline are available.

Important caveat:

- NODE-013 streams stored WAV artifacts after recording download.
- It validates the adapter, metrics, feature flag, and fallback behavior.
- It does not prove caller-perceived pause reduction in live calls.

Next proof node:

```text
NODE-014 / true-live-ari-media-streaming-stt-proof
```

## True-Live ARI Media-Path Proof

NODE-014 completed as a successful media-path proof.

Accepted decision:

- Close NODE-014 as media-path proof only.
- This is not a production STT adoption decision.
- Colocated/server-side `ari_app` near Asterisk is the proven launch shape for RTP diagnostics.
- Local sound publish is valid for server-side launch and avoids SSH back into the same server.
- `snoop_external_media_rtp` is the validated topology for receiving Asterisk RTP/PCM without moving the original caller channel into the diagnostic bridge.
- Production server-side STT strategy moved to NODE-015; implementation should move to NODE-016 as dialog-isolated diagnostics plus server-side STT measurement.

Proof evidence:

- `SYSTEM_SOUNDS_DONE ok`.
- `ARI_LISTENING http://127.0.0.1:8088/ari ai_secretary`.
- `ARI_WS_CONNECTED`.
- `stt_live_rtp_packets_received_count > 0`.
- `stt_live_pcm_chunks_created_count > 0`.
- `stt_live_rtp_diagnostics_result=rtp_packets_received`.

Boundary:

- The later dialog failure is excluded from the media-path decision because batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1` for RTP-only diagnostics.

## Production Server-Side STT Strategy

NODE-015 completed as a docs-only planning closeout.

Accepted decision:

- Use colocated/server-side `ari_app` plus the NODE-014 `snoop_external_media_rtp` topology as the production media shape.
- Use OpenAI Realtime transcription over approved server egress as the first production STT candidate.
- Use direct server egress when operationally allowed; otherwise put a controlled outbound proxy/gateway between the server and OpenAI.
- Keep batch Audio API STT as fallback/baseline during rollout.
- Defer local/offline STT as primary until the current server hardware is benchmarked.
- Make RTP diagnostics fully dialog-isolated before live STT is allowed to drive business dialog.
- Do not include PHONE in live STT adoption by default; preserve PHONE_CONFIRM fast path.

Next implementation node:

```text
NODE-016 / dialog-isolated-rtp-diagnostics-and-server-stt-measurement
```

## Dialog-Isolated RTP Diagnostics

NODE-016 completed dialog-isolated RTP/STT diagnostics.

Accepted decision:

- `STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true` separates diagnostic RTP/STT measurement from customer dialog state.
- In isolated diagnostics for `ISSUE`, `NAME`, and `CITY`, live RTP diagnostics and STT measurement may run and log timing/errors, but failed or empty diagnostic STT must not call the business dialog state machine.
- Diagnostic failures must not increment business retry counters.
- Diagnostic failures must not trigger `SAFE_FINISH`, transfer, callback, or customer-facing side effects.
- Diagnostic closeout is reported with explicit events such as `stt_live_diagnostics_result`, `stt_live_diagnostics_dialog_bypass`, and `diagnostic_call_finished`.
- Normal non-diagnostic calls remain governed by existing transfer, callback, after-hours, PHONE, PHONE_CONFIRM, CITY validation, and SAFE_FINISH contracts.

Server smoke `1778668979.22` validated `rtp_diagnostics_only` over `snoop_external_media_rtp` to advertised host `172.18.0.1`, with `429` RTP packets, `429` PCM chunks, and `diagnostic_call_finished status=ok` while dummy batch STT failed as expected.

## Server-Side Systemd Autostart Applied

NODE-018 applied the NODE-017 systemd launch shape on server `92.118.85.117`.

Accepted decision:

- Keep `ai-secretary-ari.service` enabled for reboot autostart.
- Keep the service process running as `tulauser`.
- Keep runtime non-secret config in `/etc/ai-secretary/ari-app.env`.
- Continue reading `ARI_PASSWORD` from `/home/tulauser/asterisk-config/ari.conf` at runtime instead of storing it in the env file or git.
- Keep the safe diagnostics profile until a separate production-STT node provides real OpenAI egress and secret handling.
- Use local publish through the actual Docker sounds volume path.
- On this server, keep the systemd drop-in `ExecStartPre=+/usr/bin/chmod 0711 /var/lib/docker` so `tulauser` can traverse to the Docker sounds volume after reboot while the service itself still runs unprivileged.

Server smoke `1778672473.13` validated reboot-safe `rtp_diagnostics_only` over `snoop_external_media_rtp`, with `228` RTP packets, `228` PCM chunks, `stt_live_rtp_diagnostics_result=rtp_packets_received`, and `diagnostic_call_finished status=ok`. No business `safe_finish`, `transfer`, or `callback` action occurred.

## Direct OpenAI Realtime Egress Blocked

NODE-019 proved direct OpenAI Realtime egress from server `92.118.85.117` is not viable.

Accepted decision:

- The server reached `api.openai.com/v1/realtime` but OpenAI returned `403 Forbidden` with code `unsupported_country_region_territory`.
- The rejection happened before session creation and before audio upload (`chunks_sent=0`).
- Do not store a real `OPENAI_API_KEY` on the current Asterisk server as the production plan.
- Keep `ai-secretary-ari.service` in the safe diagnostic profile.
- Use a supported-region gateway/proxy for further OpenAI Realtime measurement.

## Supported-Region OpenAI Realtime Gateway

NODE-020 defines the supported-region gateway/proxy path.

Accepted decision:

- The Asterisk server remains colocated with RTP and ARI.
- The gateway runs in an OpenAI-supported Realtime region and owns `OPENAI_API_KEY`.
- The Asterisk server authenticates to the gateway with its own gateway bearer token only.
- The first proof should be an HTTP one-shot short WAV measurement endpoint, not a production streaming relay.
- The first proof returns structured metrics and transcript presence flags, not transcript text by default.
- Later WebSocket relay work must remain feature-flagged and dialog-isolated until explicitly accepted.
- NODE-016 diagnostic isolation and NODE-018 systemd diagnostic profile must remain intact.

Next implementation node:

```text
NODE-021 / supported-region-gateway-minimal-realtime-measurement
```

## Minimal Gateway Measurement Path

NODE-021 implements the prepared one-shot gateway measurement path.

Accepted decision:

- Use the minimal gateway endpoint only for measurement until a live supported-region run passes.
- Keep `OPENAI_API_KEY` on the gateway host only.
- Let the Asterisk-side one-off client use only gateway URL/token and a short WAV.
- Return structured redacted JSON with transcript presence and timing flags.
- Do not return raw transcript text by default.
- Do not integrate the gateway path into business dialog or `ai-secretary-ari.service` by default.

Next implementation node:

```text
NODE-022 / deploy-supported-region-gateway-and-run-live-measurement
```

## Supported-Region Gateway Live Smoke Blocked

NODE-022 records the deployment path and one-off run commands, but the live smoke remained blocked.

Accepted decision:

- Do not fake gateway success when no supported-region gateway host is available.
- Keep the gateway deployment path at `/opt/ai-secretary-realtime-gateway` and gateway runtime secrets outside git, for example `/etc/ai-secretary/openai-realtime-gateway.env`.
- Keep `OPENAI_API_KEY` on the supported-region gateway only.
- Let the Asterisk-side one-off measurement use only `REALTIME_GATEWAY_URL` and `REALTIME_GATEWAY_TOKEN`.
- Leave `ai-secretary-ari.service` in the existing `rtp_diagnostics_only` profile.
- Do not enable gateway STT in business dialog until a real supported-region smoke passes and a separate adoption node accepts transcript quality and fallback behavior.

Recorded NODE-022 result:

```text
gateway_reachable=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
asterisk_server_openai_key_present=no
transcript_text_logged=false
business_dialog_changed=false
systemd_profile_changed=false
```

## Kamatera USA Gateway Live Smoke Passed

NODE-023 deployed the NODE-021 measurement gateway on Kamatera USA / New York 2 and ran one Asterisk-side gateway-mode measurement.

Accepted decision:

- Keep `OPENAI_API_KEY` on the gateway host only.
- Keep `GATEWAY_TOKEN` outside git and use it only for Asterisk-to-gateway measurement auth.
- Treat HTTP port `8080` as smoke-only, not a production exposure.
- Stop the manual gateway process after the one-off smoke because it was plain HTTP on a public IP.
- Do not enable gateway STT in business dialog by default.
- Do not change `ai-secretary-ari.service`; keep the diagnostic-safe profile until a separate adoption node explicitly changes it.

Recorded NODE-023 result:

```text
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
asterisk_server_openai_key_present=no
chunks_sent=6
transcript_present=false
transcript_text_logged=false
business_dialog_changed=false
systemd_profile_changed=false
gateway_process_stopped=true
```

## Production Gateway STT Integration Boundary

NODE-024 closes as design-only. It does not enable gateway STT and does not change the business dialog, service profile, or live servers.

Accepted decision:

- Gateway-backed STT may connect to business dialog only as a transcript-source provider before the existing `apply_turn(...)` boundary.
- Future implementation must be disabled by default.
- Dialog-driving transcript use must have its own explicit flag and remain disabled by default.
- `OPENAI_API_KEY` stays on the supported-region gateway only.
- The Asterisk server may hold only gateway URL/token in secret runtime config.
- Transcript text must not be logged by default.
- Gateway auth failure, gateway unavailable, timeout, OpenAI success with absent transcript, and low-quality transcript must not advance dialog state.
- Fallback must preserve current deterministic prompt/retry behavior and existing batch STT policy where configured.
- PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, and Russian-only caller-facing contracts remain mandatory gates.
- NODE-014 RTP topology and NODE-016 diagnostic isolation remain mandatory gates.

Next implementation node:

```text
NODE-025 / controlled-disabled-by-default-gateway-stt-adapter-implementation
```

## Controlled Gateway STT Adapter

NODE-025 implements the adapter but does not enable production gateway STT.

Accepted decision:

- The Asterisk-side gateway STT adapter is allowed only at the transcript-source boundary before `apply_turn(...)`.
- The adapter is disabled by default with `STT_GATEWAY_STT_ENABLED=false` and `STT_GATEWAY_ADAPTER_ENABLED=false`.
- Dialog-driving transcript use remains separately disabled by default with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- Asterisk-side gateway auth uses only `STT_GATEWAY_URL`/`STT_GATEWAY_TOKEN` or the existing `REALTIME_GATEWAY_URL`/`REALTIME_GATEWAY_TOKEN` aliases.
- The adapter does not require or read `OPENAI_API_KEY` on the Asterisk side.
- Transcript text is not logged by default; `STT_GATEWAY_LOG_TRANSCRIPT=false`.
- Missing config, gateway auth failure, timeout, unavailable gateway, malformed response, empty transcript, and low-quality transcript fall back to the existing batch/deterministic path without advancing dialog from the gateway result.
- Production enablement, live gateway process management, TLS/systemd hardening, and live-call validation remain separate future nodes.

Next implementation node:

```text
NODE-026 / controlled local adapter smoke / dry-run validation
```

## Controlled Local Gateway Adapter Dry-Run

NODE-026 validates the NODE-025 adapter locally and does not enable production gateway STT.

Accepted decision:

- Local validation may use pytest mocks and a localhost-only fake HTTP gateway with fake tokens and fake transcripts.
- Disabled default flags must keep the adapter inert and must not attempt a gateway network request.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` keeps gateway transcripts from driving the business dialog and falls back to the existing batch/deterministic path.
- Explicit local transcript use is allowed only when both gateway adapter and dialog-use flags are set in test/local config.
- Adapter events and ARI events must not log transcript text by default.
- `OPENAI_API_KEY` is not required for the dry-run and remains outside the Asterisk-side adapter boundary.
- Real gateway tokens, Kamatera, OpenAI, live Asterisk, live calls, SSH, service changes, and Asterisk runtime env changes remain out of scope for local dry-run validation.

Next implementation node:

```text
NODE-027 / controlled gateway adapter live smoke with explicit temporary flags
```

## Controlled Gateway Adapter Live Smoke Helper And Blocker

NODE-027 does not enable production gateway STT and does not record a successful live adapter smoke.

Accepted decision:

- A one-off CLI helper may exercise the NODE-025 adapter path with explicit temporary flags, outside the running ARI service and outside live business calls.
- The helper must require explicit smoke flags when requested, avoid `OPENAI_API_KEY` on Asterisk, redact gateway token and transcript text, and preserve the adapter defaults.
- A live adapter smoke must not be claimed unless the Kamatera gateway is started, reachable from Asterisk, and the adapter request actually runs through the gateway.
- If gateway SSH or gateway startup is unavailable, the correct result is a blocked closeout with cleanup preserved.
- NODE-027 is blocked because SSH to `45.61.48.199:22` refused connections and the gateway listener on `8080` was not reachable from Asterisk.
- No service restart, env-file edit, live call, business dialog change, or production default enablement is allowed as a workaround.

Next implementation node:

```text
NODE-028 / rerun controlled gateway adapter live smoke after gateway SSH recovery
```

## Controlled Gateway Adapter Live Smoke Retry Passed

NODE-028 closes with a successful controlled live adapter smoke, using an empty-transcript fallback result.

Accepted decision:

- The NODE-027 helper may be used as a one-off live smoke tool when it exercises the NODE-025 adapter path from the Asterisk server.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` may be used only inside the one-off helper process to force the adapter request; this does not enable production gateway STT or change the running ARI service.
- A silent synthetic WAV can prove live adapter/gateway/OpenAI transport and empty-transcript fallback, but it does not prove useful speech transcription quality.
- Gateway auth and OpenAI Realtime from the gateway are accepted as passed for NODE-028: `gateway_auth=ok`, `openai_realtime_from_gateway=ok`, `chunks_sent=15`.
- The temporary gateway process must be stopped after the smoke.
- No service restart, env-file edit, live call, business dialog change, or production default enablement is allowed as part of this smoke.
- Gateway STT remains disabled by default.

Next recommendation:

```text
Productionize the gateway only in a separate scoped node, or run a separate non-silent speech-quality adapter smoke.
```

## Empty Transcript Diagnostic

NODE-029 closes the NODE-028 empty-transcript diagnosis as local diagnostic work.

Accepted decision:

- Do not treat the NODE-028 empty transcript as proof of a gateway/OpenAI transport failure.
- NODE-028 used a synthetic silent WAV, so the leading root cause is near-silent/non-speech audio content.
- Gateway and adapter diagnostics must report audio quality and Realtime event visibility before future live speech-quality conclusions are made.
- Transcript text must remain redacted by default in gateway, adapter, helper, and docs output.
- Production gateway STT remains disabled by default.
- The next useful experiment is one controlled non-sensitive speech WAV diagnostic through the same gateway path, not a production enablement.

Next recommendation:

```text
Run a controlled non-sensitive speech WAV diagnostic with STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false and STT_GATEWAY_LOG_TRANSCRIPT=false.
```

## Controlled Speech WAV Smoke

NODE-030 closes the controlled Russian speech WAV gateway transcript smoke.

The NODE-028 empty transcript is closed as a silent/non-speech WAV artifact. Valid non-sensitive Russian speech produced transcript-bearing OpenAI Realtime events through the Kamatera gateway.

Evidence:

- `audio_quality_classification=valid_speech_candidate`
- `gateway_auth=ok`
- `openai_realtime_from_gateway=ok`
- `chunks_sent=24`
- `transcript_event_seen=true`
- `transcript_present=true`
- `transcript_text_logged=false`
- `transcript_used_for_dialog=false`

Operational boundary:

- The manual smoke helper may send one measurement request with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- In that helper mode, any transcript candidate is rejected with `fallback_reason=gateway_stt_dialog_use_disabled`.
- Normal business dialog remains unchanged: with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`, the ARI business path does not make a gateway request and falls back to the existing batch/deterministic path.
- Gateway STT remains disabled by default and must not be productionized without a separate node.

## Chat Bootstrap And PR Workflow Boundary

NODE-031A creates a docs-only bootstrap for new GPT chats and future Control Plane closeout.

Accepted decision:

- New GPT chats should start from `docs/master/CHAT_BOOTSTRAP.md`, then read the master docs and latest completed node doc.
- Future AI-secrenar nodes should use feature branch plus PR workflow.
- The intended flow is GPTChat coordinator discussion, Notion node creation/update, docs node file, Codex handoff, sync `master`, create a feature branch, scoped implementation, validation, commit, PR, review, merge, Control Plane supervised runner closeout/evidence where applicable, no-op verification, and next node.
- Existing `NODE-001` through `NODE-030` are historical commit-based nodes.
- Historical commit-based nodes should not be retrofitted through the PR-based supervised runner unless a later separate commit-based closeout design is explicitly created.
- NODE-031A does not implement `NODE-031 / productionize-gateway-runtime-boundary`.

Next technical node:

```text
NODE-031 / productionize-gateway-runtime-boundary
```

## Production Gateway Runtime Boundary

NODE-031 defines the production gateway runtime boundary as docs and safe templates only.

Accepted decision:

- Production gateway ownership, systemd/supervisor boundaries, port/listen assumptions, firewall source restriction, TLS/reverse-proxy boundaries, env-file ownership, and log redaction requirements are documented before any persistent gateway deployment.
- `OPENAI_API_KEY` must live only on the supported-region gateway, never in the Asterisk safe profile.
- `GATEWAY_TOKEN` must be stored only in secure runtime env/vault material; repository templates use placeholders only.
- Gateway STT remains disabled by default, and business dialog must not use gateway transcript text unless a later explicit node enables it.
- Transcript text must not be logged by default; measurement helper and business dialog paths remain distinct.
- NODE-031 performs no live deployment, no server action, no systemd/firewall/TLS apply, no live smoke, no Notion write, no Runtime/Evidence create, and no GitHub write.

Next implementation node:

```text
NODE-032 / controlled-production-gateway-live-smoke
```

## Controlled Production Gateway Live Smoke

NODE-032 Phase A prepares the first live production gateway apply/smoke plan but does not execute it.

Accepted decision:

- Phase A is documentation and preflight planning only.
- No service may be started, stopped, restarted, reloaded, enabled, disabled, or changed during Phase A.
- Phase B requires the exact operator approval phrase `APPROVE NODE-032 LIVE APPLY/SMOKE`.
- Phase B may run at most one controlled non-business-dialog smoke with transcript logging disabled and `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- `OPENAI_API_KEY` must remain gateway-only; the Asterisk safe profile must not contain it.
- If access, secrets, templates, rollback readiness, or current server state is unsafe, NODE-032 must remain blocked before live apply.

## Controlled Production Gateway Live Apply/Smoke Readiness

NODE-032B Phase A prepares readiness/preflight for the first controlled production gateway live apply/smoke but does not execute it.

Accepted decision:

- Phase A is documentation and command planning only.
- No service may be started, stopped, restarted, reloaded, enabled, disabled, or changed during Phase A.
- No live apply, server state change, gateway/proxy change, firewall apply, live smoke, or business dialog transcript use is allowed during Phase A.
- Phase B requires the exact operator approval phrase `APPROVE NODE-032B LIVE APPLY/SMOKE`.
- No other phrase is approval.
- Phase B may run at most one controlled non-business-dialog smoke with transcript logging disabled and `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- The Asterisk safe profile must not contain `OPENAI_API_KEY`; gateway owns OpenAI Realtime access and secrets.
- If access, secrets, templates, rollback readiness, or current server state is unsafe, NODE-032B must remain blocked before live apply.

## Live Read-Only Production Gateway Readiness Inspection

NODE-032C performs read-only live readiness inspection for the production gateway path.

Accepted decision:

- Read-only SSH inspection may verify host reachability, service status, process/listen state, firewall state, file metadata, masked env key presence, and sanitized journals.
- Do not print real token values, env values, bearer headers, private keys, or transcript text.
- Asterisk is acceptable only if `OPENAI_API_KEY` is absent from the safe service/process env.
- Gateway masked secret presence is acceptable only on the gateway/vault side.
- NODE-032C result is NO-GO for immediate NODE-032D live apply/smoke because env path, service unit, TLS/proxy, firewall transition, and rollback plan still require explicit operator decisions.
- Future live apply/smoke still requires the exact NODE-032B approval phrase `APPROVE NODE-032B LIVE APPLY/SMOKE`.

## Production Gateway Live Delta Decision

NODE-032D resolves the live delta decisions required before a future controlled first smoke.

Accepted decision:

- First live smoke keeps the historical gateway env path `/etc/ai-secretary/openai-realtime-gateway.env`.
- Do not migrate to `/etc/ai-secretary/gateway.env` and do not create a symlink during the first smoke.
- Future live apply may install/adapt `ai-secretary-gateway.service` at `/etc/systemd/system/ai-secretary-gateway.service`.
- The service should run as `gateway:gateway`, use the historical env path, bind for the first smoke on the existing Asterisk-only `8080` path, and use `Restart=on-failure`.
- No public TLS/proxy setup is required for the first smoke.
- Do not expose `443` and do not open `8081` during the first smoke.
- Keep the old `8080/tcp` allow from `92.118.85.117` for first smoke if NODE-032E re-confirms it is still source-restricted.
- Do not remove the old `8080/tcp` allow until a replacement path is proven or a separate cleanup/productionization node approves it.
- Stop/rollback the gateway after smoke unless NODE-032E explicitly records a persistent service decision.
- Business dialog transcript use remains disabled, and transcript text remains redacted.
- The Asterisk safe profile must still contain no `OPENAI_API_KEY`.

Future NODE-032E approval gate:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

No other phrase is approval.

## NODE-032E Phase A Live Gate Re-Confirmation

NODE-032E Phase A re-confirms the live gates before any controlled production gateway live apply/smoke.

Accepted decision:

- Phase A remains read-only inspection and documentation only.
- Asterisk is acceptable for Phase B planning because SSH works, `ai-secretary-ari.service` is active/enabled, and `OPENAI_API_KEY` is absent from the service process env.
- Gateway is acceptable for Phase B planning because SSH works, `/etc/ai-secretary/openai-realtime-gateway.env` exists as `root:root 600`, and masked checks show required gateway secret presence without values.
- `/etc/ai-secretary/gateway.env` remains not required for the first smoke.
- `ai-secretary-gateway.service` is not currently enabled/installed as a usable service and may be installed/adapted only in Phase B after exact approval.
- No unexpected listener exists on `443`, `8080`, or `8081`.
- UFW keeps `8080/tcp` source-restricted to `92.118.85.117`.
- No public TLS/proxy, no `443`, no proxy reload, and no `8081` opening are allowed for first smoke.
- Phase B is NO-GO now because the exact approval phrase is absent.
- Phase B must re-run live gate checks immediately before apply.

Future Phase B still requires:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

No other phrase is approval.

## NODE-032E Phase B Hard-Gate NO-GO

NODE-032E Phase B received the exact approval phrase and re-ran hard gates before any state-changing action.

Accepted decision:

- Stop before live apply because the required Asterisk-side smoke helper/path could not be identified safely.
- The deployed Asterisk repo path exists, but `src/ai_secretary/stt/gateway_adapter_smoke.py` is absent there.
- Deploying or copying the local helper to Asterisk would be source/runtime deployment outside the approved live apply scope.
- Running the smoke from a non-Asterisk source would not prove the source-restricted `8080/tcp` path from `92.118.85.117`.
- Do not install the gateway service until the smoke path blocker is resolved.
- No service install/start, daemon reload, firewall change, env edit, live smoke, or rollback action was performed.

Next decision required:

- A separate node must prepare or approve the Asterisk-side smoke helper/path before retrying live apply/smoke.

## NODE-032F Asterisk-Side Smoke Helper Path

NODE-032F prepares the Asterisk-side helper/path for the next controlled live smoke.

Accepted decision:

- Reuse the existing tested core helper `ai_secretary.stt.gateway_adapter_smoke`.
- Add `scripts/asterisk_gateway_smoke_helper.py` as the explicit Asterisk-side manual wrapper for future live use.
- The wrapper is manual-only and must not be configured as a service, cron job, timer, webhook, scheduler, or automation loop.
- The wrapper requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` and `STT_GATEWAY_LOG_TRANSCRIPT=false`.
- The wrapper refuses to run if `OPENAI_API_KEY` exists on Asterisk.
- The wrapper may use only gateway URL/token runtime material supplied by a future live node through secure one-off env or an explicitly approved temporary secure runtime file.
- The wrapper must never print token values or transcript text.
- The wrapper records safe flags/metrics only, including `transcript_text_logged=false` and `business_dialog_unchanged=true`.
- The next live smoke must run this helper from the Asterisk host to prove the source-restricted `92.118.85.117 -> 45.61.48.199:8080` path.

Next live node:

```text
NODE-032G / controlled-gateway-live-smoke-with-asterisk-side-helper
```

## NODE-032G Phase A Live Gate And Helper Availability Plan

NODE-032G Phase A re-confirms gates and plans the future live smoke with the NODE-032F helper.

Accepted decision:

- Phase A remains read-only plus documentation only.
- The exact approval phrase for Phase B is `APPROVE NODE-032G LIVE APPLY/SMOKE`; no other phrase is approval.
- Asterisk is acceptable for Phase B planning because SSH works, `ai-secretary-ari.service` is active/enabled, and `OPENAI_API_KEY` is absent from process env.
- Gateway is acceptable for Phase B planning because the historical env file exists as `root:root 600`, masked secret presence checks pass, no target listener exists on `443`, `8080`, or `8081`, and UFW restricts `8080/tcp` to `92.118.85.117`.
- The deployed Asterisk `node014` path is not a usable Git checkout and lacks the NODE-032F helper plus required adapter modules.
- Phase B should use a temporary helper bundle at `/tmp/node032g-asterisk-helper` instead of assuming `git pull` on the Asterisk host.
- Phase B should use a temporary root-owned `600` runtime env file at `/tmp/node032g-gateway-client.env` or an equally secure operator-injected runtime secret path to avoid shell-history token exposure.
- No helper autostart, persistent helper state, scheduler, webhook, cron, timer, or automation loop is allowed.
- Business dialog must remain unchanged and transcript text must remain redacted.

## NODE-032G Phase B Live Smoke Result

NODE-032G Phase B received exact approval and completed the controlled Asterisk-origin gateway smoke.

Accepted result:

- The temporary helper bundle was deployed only to `/tmp/node032g-asterisk-helper`.
- The temporary runtime env file was deployed only to `/tmp/node032g-gateway-client.env` with `root:root 600`.
- The gateway service was installed and started temporarily, using `/etc/ai-secretary/openai-realtime-gateway.env`, `0.0.0.0:8080`, and `Restart=on-failure`.
- No `443`, `8081`, TLS/proxy, or firewall broadening occurred.
- The smoke ran from Asterisk and proved `92.118.85.117 -> 45.61.48.199:8080`.
- Gateway auth succeeded, OpenAI Realtime from gateway succeeded, and `chunks_sent=28`.
- `transcript_present=true`, `transcript_text_logged=false`, and `business_dialog_unchanged=true`.
- The helper rejected transcript use for dialog with `fallback_reason=gateway_stt_dialog_use_disabled`.
- Temporary gateway service/unit, helper bundle, runtime env file, and temp audio were removed during cleanup.
- Asterisk still had no `OPENAI_API_KEY`.
- No helper autostart, scheduler, webhook, timer, cron, or automation loop was added.

## NODE-032H Production Gateway Persistence And Reboot Strategy

NODE-032H decides persistence strategy after the successful NODE-032G smoke.

Accepted decision:

- Use staged persistence, not immediate always-on production enablement.
- The next live node may install/adapt and start `ai-secretary-gateway.service` only after exact approval and immediate gate re-confirmation.
- Service enablement and reboot/power-cycle proof remain separate controlled work unless explicitly included with an exact approval phrase.
- The durable service target is:
  - service name `ai-secretary-gateway.service`;
  - unit path `/etc/systemd/system/ai-secretary-gateway.service`;
  - runtime `gateway:gateway`;
  - env file `/etc/ai-secretary/openai-realtime-gateway.env`;
  - working directory `/opt/ai-secretary-gateway`;
  - listen `0.0.0.0:8080`;
  - restart policy `on-failure`.
- Running the durable production service as root is not accepted.
- The historical env file must be made safely readable by the non-root gateway service before persistent start, preferably `root:gateway 640` after approval.
- `0.0.0.0:8080` is acceptable only while UFW restricts `8080/tcp` to Asterisk `92.118.85.117`.
- Do not expose `443` or `8081` in this stage unless a separate node approves it.
- Gateway owns OpenAI Realtime secrets; Asterisk must not contain `OPENAI_API_KEY`.
- Durable service behavior must not depend on shell exports after reboot.
- Missing or invalid env must fail closed without opening a useful gateway listener.
- Logs may include lifecycle, status, timing, chunks, and transcript presence flags, but must not include token values, bearer headers, env dumps, transcript text, or caller audio content.
- Business dialog integration remains out of scope until gateway persistence and reboot/power-cycle behavior are proven.

Next live node:

```text
NODE-032I / controlled-persistent-gateway-service-and-reboot-smoke
```

## NODE-032I Phase A Persistent Gateway Service Install/Start/Smoke Plan

NODE-032I Phase A prepares the staged persistence live node after NODE-032H.

Accepted decision:

- Phase A is readiness inspection and command planning only.
- The exact approval phrase for Phase B is `APPROVE NODE-032I SERVICE INSTALL/START/SMOKE`; no other phrase is approval.
- Do not install or modify systemd units during Phase A.
- Do not create `gateway:gateway`, change env file ownership/mode, start/stop/restart/reload/enable services, change firewall, edit env files, copy helper bundles, run live smoke, reboot, provider power-cycle, or enable business dialog during Phase A.
- Local template delta for Phase B is known: adapt `deploy/templates/gateway-systemd.service.example` from `/etc/ai-secretary/gateway.env` and `/usr/local/bin/ai-secretary-gateway --bind ${GATEWAY_BIND}` to `/etc/ai-secretary/openai-realtime-gateway.env`, `/opt/ai-secretary-gateway`, and `/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080`.
- Phase B must not run `systemctl enable`, reboot, provider power-cycle, expose `443`, open `8081`, broaden firewall, or enable business dialog.
- Initial read-only SSH checks timed out while the servers were likely still powering on; after operator confirmation, fresh rerun SSH checks passed for both Asterisk `92.118.85.117` and Gateway `45.61.48.199`.
- Rerun gates confirmed Asterisk active/enabled with no `OPENAI_API_KEY` in process/service env, Gateway historical env present as `root:root 600` with masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence, no target listeners on `443`, `8080`, or `8081`, and UFW `8080/tcp` restricted to `92.118.85.117`.
- Rerun gates confirmed `gateway:gateway` is absent, so Phase B must create the locked service account and adjust env readability only after exact approval.
- Phase B is conditionally GO only after exact approval is present and all hard gates are re-confirmed immediately before state change.

## NODE-032I Phase B Persistent Gateway Service Result

NODE-032I Phase B received exact approval and completed the controlled persistent gateway service install/start/smoke.

Accepted result:

- Exact approval phrase was `APPROVE NODE-032I SERVICE INSTALL/START/SMOKE`.
- Hard gates passed before state change.
- A locked `gateway:gateway` service account was created.
- `/etc/ai-secretary/openai-realtime-gateway.env` changed from `root:root 600` to `root:gateway 640`; env values were preserved and not printed.
- `ai-secretary-gateway.service` was installed at `/etc/systemd/system/ai-secretary-gateway.service`, using `gateway:gateway`, `/etc/ai-secretary/openai-realtime-gateway.env`, `/opt/ai-secretary-gateway`, `0.0.0.0:8080`, and `Restart=on-failure`.
- The deployed src-layout required `PYTHONPATH=/opt/ai-secretary-gateway/src` in the unit.
- The service was started, verified active, verified disabled/not enabled, and verified listening on `8080` only.
- UFW remained source-restricted: `8080/tcp` allowed only from `92.118.85.117`.
- One Asterisk-side controlled smoke reached the gateway, authenticated, reached OpenAI Realtime, returned HTTP 200, sent `28` chunks, and kept `transcript_text_logged=false`, `transcript_used_for_dialog=false`, and `business_dialog_unchanged=true`.
- Final maximum-safety state: service unit installed as the staged artifact, service stopped, service disabled, no target listeners on `443`, `8080`, or `8081`, firewall unchanged, temp helper/env/audio removed, and Asterisk still had no `OPENAI_API_KEY`.
- No `systemctl enable`, reboot, provider power-cycle, `443`, `8081`, TLS/proxy change, firewall broadening, business dialog enablement, scheduler, webhook, automation loop, Notion write, Runtime/Evidence update, GitHub push/PR, token value logging, or transcript text logging occurred.

## NODE-032J Gateway Service Enable Policy And Autostart Decision

NODE-032J decides what to do with the staged gateway service artifact left by NODE-032I.

Accepted decision:

- Keep the NODE-032I staged service artifact installed but stopped and disabled for now.
- Do not run immediate `systemctl enable`.
- Do not combine service enablement with business dialog transcript use.
- Proceed toward autostart only through a separate controlled enablement/reboot-smoke node.
- Do not include provider power-cycle in the next node unless separately scoped.
- Do not perform cleanup/rollback now because NODE-032I left a useful staged artifact: installed unit, stopped/disabled service, no target listeners, unchanged firewall, preserved env, and successful manual start/smoke evidence.

Current staged truth:

```text
service_unit_installed=true
service_active=false
service_enabled=false
runtime_user_group=gateway:gateway
env_owner_mode=root:gateway 640
listen_policy=0.0.0.0:8080 only with UFW restricted to 92.118.85.117
reboot_power_cycle_proof=false
business_dialog_integration=false
```

Future enablement gates before `systemctl enable`:

- Asterisk reachable.
- Asterisk has `OPENAI_API_KEY_ABSENT`.
- Business dialog gateway transcript use disabled.
- Gateway reachable.
- Env readable by the service runtime.
- Masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence passes.
- Service unit present and valid.
- Service can start manually.
- Service is disabled before enablement.
- No unexpected listeners on `443`, `8080`, or `8081`.
- UFW `8080/tcp` remains restricted to `92.118.85.117`.
- Rollback commands accepted.
- No token values or transcript text printed.

Future exact approval phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

No other phrase is approval.

Next live node:

```text
NODE-032K / controlled-gateway-service-enable-and-reboot-smoke
```

NODE-032K expected scope:

- Re-confirm gates.
- Start service manually if needed and verify readiness.
- Run `systemctl enable ai-secretary-gateway.service`.
- Reboot the Gateway server.
- Verify SSH returns.
- Verify service auto-starts.
- Verify listener/firewall/log redaction.
- Run one Asterisk-side smoke.
- Document final state and rollback path.

Out of scope for NODE-032K unless separately approved:

- Provider power-cycle.
- Business dialog enablement.
- TLS/proxy.
- `443`.
- `8081`.
- Firewall broadening.

Remaining blockers:

```text
enable_reboot_proof=false
node032k_exact_approval_phrase_provided=false
provider_power_cycle=separately_scoped
business_dialog_integration=out_of_scope
```

## NODE-032K Phase A Enable/Reboot Smoke Readiness

NODE-032K Phase A prepares the controlled Gateway service enablement and reboot smoke.

Accepted decision:

- Phase A is read-only readiness and command planning only.
- Create a sanitized long-form handoff archive under `docs/handoffs/`.
- Do not run live enablement, `systemctl enable`, reboot, provider power-cycle, service start/stop/restart/reload, firewall change, env edit, helper deploy, live smoke, or business dialog enablement during Phase A.
- Phase B requires exact approval phrase `APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE`; no other phrase is approval.
- Phase B must re-confirm all hard gates before any state change.
- Phase B may manually start/check the service, enable it, reboot the Gateway server, verify auto-start, verify listener/firewall/log redaction, and run one Asterisk-side smoke.
- Provider power-cycle, business dialog enablement, TLS/proxy, `443`, `8081`, and firewall broadening remain out of scope unless separately approved.

Phase A read-only gate result:

```text
asterisk_openai_api_key=absent_from_process_and_service_env
business_dialog_gateway_transcript=not_enabled
gateway_unit_present=true
gateway_unit_valid=true
gateway_service_active=inactive
gateway_service_enabled=disabled
gateway_user_group=gateway:gateway present
gateway_env_owner_mode=root:gateway 640
gateway_secret_presence=masked_pass
gateway_target_listeners_443_8080_8081=absent
gateway_ufw_8080=92.118.85.117 only
rollback_commands_available=true
```

Phase B remains blocked because:

```text
exact_approval_phrase_absent=true
```

## NODE-032K Phase B Enable/Reboot Attempt Hard NO-GO

NODE-032K Phase B received the exact approval phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Accepted result:

- Hard gates passed before state change.
- The staged gateway service manually started successfully.
- `systemctl enable ai-secretary-gateway.service` ran.
- Gateway-only reboot completed and SSH returned.
- The service auto-started after reboot and was active/enabled.
- Listener after reboot was `8080` only; no `443` or `8081`.
- UFW remained active with `8080/tcp` allowed only from `92.118.85.117`.
- No provider power-cycle, firewall broadening, TLS/proxy change, `443`, `8081`, Asterisk env change, or business dialog enablement occurred.

Hard NO-GO:

- A malformed temporary Asterisk smoke env caused a gateway token value to print during diagnostic inspection.
- The value is not recorded in repo docs.
- The controlled smoke did not run after the token-output failure.
- Transcript text was not printed.

Rollback decision:

- Disable and stop `ai-secretary-gateway.service`.
- Leave the staged unit installed.
- Verify final service state disabled/inactive.
- Verify no target listeners on `443`, `8080`, or `8081`.
- Keep firewall unchanged.
- Remove temporary Asterisk helper/env/audio.
- Verify Asterisk still has `OPENAI_API_KEY_ABSENT`.

Required before retry:

- Rotate the exposed gateway token.
- Replace the temporary Asterisk env creation/verification path with a newline-safe method that never prints values.
- Re-confirm all hard gates before any further state change.

## NODE-032K Security Remediation

Accepted result:

- The exposed Gateway token was rotated on the Gateway host only.
- Old and new token values were not printed or recorded.
- `/etc/ai-secretary/openai-realtime-gateway.env` remains `root:gateway 640`.
- Masked `GATEWAY_TOKEN` presence passed after rotation.
- `ai-secretary-gateway.service` remains disabled and inactive.
- No target listeners exist on `443`, `8080`, or `8081`.
- UFW remained unchanged and `8080/tcp` remains allowed only from `92.118.85.117`.
- Asterisk still has `OPENAI_API_KEY_ABSENT`.
- No smoke retry, service enablement, service start, reboot, provider power-cycle, firewall change, Asterisk env change, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

Remaining before retry:

- Replace the temporary Asterisk env creation/verification path with a newline-safe method that never prints values.
- Re-confirm all hard gates before any further state change.
- Next node recommendation: `NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan`.

## NODE-032L Newline-Safe Temp Env Guard

Accepted decision:

- Use `scripts/gateway_smoke_temp_env_guard.py` as the repo-supported temporary env creation, validation, and cleanup mechanism for future Asterisk-side Gateway smoke helper bundles.
- Token material must be read from stdin and never printed.
- The guard must reject missing token material, CR/LF token material, literal newline material, malformed URL/env values, transcript-dialog use enabled, transcript logging enabled, and missing explicit adapter enablement.
- The guard may print only masked/safe status such as `token_present_masked=true`, `secret_values_printed=false`, and `transcript_text_logged=false`.
- Temporary env files are written atomically with mode `0600` and must be cleaned up after a future smoke.
- `scripts/asterisk_gateway_smoke_helper.py` also rejects gateway URL/token env values containing newline material before any gateway request.
- NODE-032L does not authorize a live retry.

Next live node:

```text
NODE-032M / controlled-gateway-enable-reboot-smoke-retry-with-safe-temp-env
```

## NODE-032M Safe Temp-Env Retry Phase A

NODE-032M Phase A prepares the controlled retry of the Gateway enable/reboot/smoke path after NODE-032K and NODE-032L.

Accepted Phase A result:

- Local guard/helper inspection passed.
- Read-only Asterisk gates passed.
- Read-only Gateway gates passed.
- No live retry, service action, `systemctl` state change, reboot, provider power-cycle, firewall/env/server state change, helper deploy, live smoke, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.
- No token values or transcript text were printed or recorded.

Future Phase B requires exact approval phrase:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

Phase B decision boundary:

- Re-run all hard gates immediately before any state change.
- Use `scripts/gateway_smoke_temp_env_guard.py` or equivalent for temp env create/validate/cleanup.
- Supply Gateway token material through stdin only.
- Print only masked/safe validation status.
- Run at most one Asterisk-side smoke.
- Clean up temporary helper/env/audio.
- Do not provider power-cycle, enable business dialog, expose `443` or `8081`, change TLS/proxy, broaden firewall, print token values, or print transcript text.

Current recommendation:

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
```

## NODE-032M Phase B Safe Temp-Env Retry Attempt

NODE-032M Phase B received the exact approval phrase:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

Accepted result:

- Hard gates passed before state change.
- NODE-032L guard created and validated a temporary Asterisk smoke env with token material supplied through stdin only.
- The first guard create attempt failed closed because stdin token material was absent due command quoting; it printed safe JSON only.
- Gateway service manually started successfully.
- `systemctl enable ai-secretary-gateway.service` ran.
- Gateway-only reboot completed and SSH returned.
- Service auto-started after reboot and was active/enabled.
- Listener after reboot was `8080` only; no `443` or `8081`.
- UFW remained active with `8080/tcp` allowed only from `92.118.85.117`.
- No provider power-cycle, firewall broadening, TLS/proxy change, `443`, `8081`, Asterisk env change, or business dialog enablement occurred.

Hard blocker:

- Exactly one Asterisk-side smoke helper invocation was attempted.
- The helper failed before any Gateway request because the temporary helper bundle was incomplete.
- Missing module: `ai_secretary.config`.
- No token values or transcript text were printed.

Rollback decision:

- Disable and stop `ai-secretary-gateway.service`.
- Leave the staged unit installed.
- Verify final service state disabled/inactive.
- Verify no target listeners on `443`, `8080`, or `8081`.
- Keep firewall unchanged.
- Remove temporary Asterisk helper/env/audio.
- Verify Asterisk still has `OPENAI_API_KEY_ABSENT`.

Next recommendation:

```text
NODE-032N / complete-safe-asterisk-helper-bundle-and-retry-plan
```

## NODE-032N Complete Safe Asterisk Helper Bundle

NODE-032N fixes the NODE-032M local helper-bundle blocker without running a live retry.

Decision:

- Keep the existing package import behavior.
- Add an explicit minimal helper-bundle manifest and local preflight validator.
- Include `ai_secretary.config` in the future temporary bundle because `src/ai_secretary/__init__.py` imports `ai_secretary.config.settings`.
- Require the NODE-032L safe temp-env guard for token material handling.
- Print only safe JSON fields from bundle create/validate operations.

Implementation:

```text
scripts/asterisk_gateway_helper_bundle.py
tests/test_asterisk_gateway_helper_bundle.py
docs/handoffs/NODE-032N-codex-handoff.md
docs/nodes/NODE-032N-complete-safe-asterisk-helper-bundle-and-retry-plan.md
```

Safety:

- The bundle helper does not read Gateway tokens.
- The bundle helper does not print token values.
- The bundle helper does not print transcript text.
- Asterisk-side `OPENAI_API_KEY` refusal remains in the smoke helper.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remains required.

Next recommendation:

```text
NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle
```

## NODE-032O Phase A Complete Helper-Bundle Smoke Retry Readiness

NODE-032O Phase A prepares the controlled Gateway smoke retry using both NODE-032L and NODE-032N safety fixes.

Accepted Phase A result:

- Local safe temp-env guard inspection passed.
- Local helper bundle manifest/preflight inspection passed.
- Read-only Asterisk gates passed.
- Read-only Gateway gates passed.
- No live retry, service action, `systemctl` state change, reboot, provider power-cycle, firewall/env/server state change, helper deploy, live smoke, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.
- No token values or transcript text were printed or recorded.

Future Phase B requires exact approval phrase:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Phase B decision boundary:

- Re-run all hard gates immediately before any state-changing command.
- Use `scripts/asterisk_gateway_helper_bundle.py` to create and validate the complete helper bundle.
- Use `scripts/gateway_smoke_temp_env_guard.py` for temp env create/validate/cleanup.
- Supply Gateway token material through stdin only.
- Run at most one Asterisk-side non-business-dialog smoke.
- Clean up temporary helper/env/audio.
- Do not run `systemctl enable`, reboot, provider power-cycle, enable business dialog, expose `443` or `8081`, change TLS/proxy, broaden firewall, print token values, or print transcript text.

Current recommendation:

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
```

## NODE-032O Phase B Complete Helper-Bundle Smoke Retry Blocked

NODE-032O Phase B received the exact approval phrase:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Accepted result:

- Hard gates passed before any state-changing command.
- Local helper bundle create/validate succeeded after one safe local path failure.
- Remote staged helper bundle validation failed closed before token handling, service start, smoke, or any Gateway request.
- The remote preflight missing module was `httpx`.
- No Gateway token was read or printed.
- No transcript text was printed.
- No service action, `systemctl enable`, reboot, provider power-cycle, firewall change, env file edit, Asterisk env change, TLS/proxy change, `443`, `8081`, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

Final state:

```text
ai-secretary-gateway.service=inactive_disabled
target_listeners_443_8080_8081=absent
ufw_8080_allow=92.118.85.117 only
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
temporary_helper_bundle_removed=true
temporary_env_removed=true
temporary_audio_removed=true
```

Next recommendation:

```text
NODE-032P / helper-bundle-runtime-dependency-preflight-and-retry-plan
```

## NODE-032P Helper Bundle Runtime Dependency Preflight

NODE-032P fixes the NODE-032O local helper-bundle preflight gap without running a live retry.

Decision:

- Keep the explicit minimal helper-bundle manifest.
- Add a runtime dependency manifest/preflight to `scripts/asterisk_gateway_helper_bundle.py`.
- Do not vendor third-party packages into the helper bundle.
- Do not install dependencies on servers in this node.
- Validate runtime dependencies before future token handling, temp-env creation, service start, smoke, or Gateway request.

Runtime modules:

```text
httpx
fastapi
websockets
```

Accepted behavior:

```text
missing_runtime_dependency_fails_closed=true
missing_runtime_modules_reported_as_safe_names_only=true
safe_json_only=true
gateway_token_read=false
token_values_printed=false
transcript_text_printed=false
```

Next recommendation:

```text
NODE-032Q / controlled-gateway-smoke-retry-with-runtime-dependency-preflight
```

If future remote preflight finds runtime dependencies missing on Asterisk, the retry must stop or move dependency installation into a separately approved node.

## NODE-032Q Runtime-Preflight Smoke Retry Readiness

NODE-032Q Phase A keeps the smoke retry blocked until exact approval and immediate hard-gate re-confirmation.

Decision:

- Use all three safety layers before any future smoke: NODE-032L safe temp-env guard, NODE-032N complete helper bundle, and NODE-032P runtime dependency preflight.
- Require exact approval phrase `APPROVE NODE-032Q RUNTIME-PREFLIGHT SMOKE RETRY`.
- Run remote helper-bundle validation before token handling, temp-env creation, service action, smoke, or Gateway request.
- If remote validation reports missing `httpx`, `fastapi`, or `websockets`, stop as NO-GO.
- Do not install dependencies in NODE-032Q; dependency installation requires a separately approved node.
- Do not run `systemctl enable`, reboot, provider power-cycle, open `443`/`8081`, broaden firewall, enable business dialog transcript use, print token values, or print transcript text.

Phase A gates:

```text
asterisk_openai_api_key=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
asterisk_runtime_modules_missing=httpx,fastapi,websockets
gateway_service=inactive_disabled
gateway_env_meta=root:gateway:640
gateway_masked_secret_presence=pass
target_listeners_443_8080_8081=absent
ufw_8080_allow=92.118.85.117 only
```

Decision update:

- NODE-032Q Phase B is NO-GO while Asterisk lacks `httpx`, `fastapi`, and `websockets`.
- Dependency installation remains out of scope for NODE-032Q.
- Next work should be separately approved dependency resolution or an alternate helper strategy.

## NODE-032R Asterisk Runtime Dependency Resolution Decision

NODE-032R is a local docs-only decision node. No SSH, live retry, helper deploy, dependency install, service action, `systemctl` action, reboot, provider power-cycle, firewall/env/server change, token output, transcript text output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

Decision:

- Choose a separate controlled Asterisk runtime dependency install/readiness node before any Gateway smoke retry.
- Preserve the existing NODE-032L safe temp-env guard, NODE-032N helper bundle, and NODE-032P runtime preflight path.
- Do not switch to a reduced-evidence helper or non-Asterisk-origin smoke as the primary path.
- Do not combine dependency install/readiness with Gateway smoke retry unless a later node explicitly re-scopes and approves it.

Options rejected or deferred:

- Existing Asterisk-side Python env: deferred unless a future read-only inspection identifies a specific safe env with the required modules.
- Alternate stdlib/curl helper: deferred as fallback because it requires local implementation/tests and may weaken evidence parity.
- Different smoke boundary: rejected as a replacement because non-Asterisk-origin smoke does not prove the source-restricted Asterisk-to-Gateway route.

Next node:

```text
NODE-032S / controlled-asterisk-runtime-dependency-install-readiness
```

Suggested approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

## NODE-032S Phase A Runtime Dependency Readiness

NODE-032S Phase A is read-only readiness and command planning only. No dependency install, `pip install`, `apt install`, server package change, venv creation, server file write, helper deploy, live retry, Gateway service action, `systemctl` state-changing action, reboot, provider power-cycle, firewall/env/server change, token output, transcript text output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, or PR occurred.

Decision:

- Use `/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python` as the recommended target runtime for Phase B readiness.
- Prefer readiness verification over installation because the project venv already has `httpx`, `fastapi`, and `websockets`.
- Keep Gateway smoke retry separate from NODE-032S.
- Do not modify system Python.
- Install only into the project venv if exact approval is provided and immediate Phase B re-check finds a required module missing.

Read-only finding:

```text
system_python3_modules=httpx:missing,fastapi:missing,websockets:missing
project_venv_modules=httpx:present,fastapi:present,websockets:present
project_venv_versions=httpx:0.28.1,fastapi:0.136.1,websockets:16.0
```

Future approval phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

Phase B expected action:

```text
verify_project_venv_readiness_and_stop
gateway_smoke_retry=false
```

## NODE-032S Phase B Runtime Dependency Readiness Decision

NODE-032S Phase B was approved with the exact phrase:

```text
APPROVE NODE-032S ASTERISK RUNTIME DEPENDENCY INSTALL/READINESS
```

Decision:

- Treat Asterisk runtime dependency readiness as confirmed for the selected deployed project venv.
- Do not install dependencies because the immediate Phase B re-check passed.
- Do not mutate system Python.
- Do not combine dependency readiness with Gateway smoke retry.

Readiness evidence:

```text
target_python=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python_version=3.12.3
pip_version=26.1.1
imports_ok=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
dependency_install_occurred=false
```

Safety boundary:

```text
gateway_smoke_retry=false
helper_copy_deploy=false
gateway_service_action=false
reboot_or_power_cycle=false
firewall_or_env_changed=false
server_env_edit=false
token_values_printed=false
transcript_text_logged=false
```

Next node:

```text
NODE-032T / controlled-gateway-smoke-retry-after-asterisk-runtime-readiness
```

## NODE-032T Phase A Gateway Smoke Retry Readiness Decision

NODE-032T Phase A is read-only readiness and smoke retry command planning only. No live smoke retry, helper copy/deploy, token handling, server temp env creation, dependency install, Gateway service action, `systemctl` action, reboot, provider power-cycle, firewall/env/server change, token output, transcript text output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, or PR occurred.

Decision:

- Proceed toward Gateway smoke retry only through Phase B with exact approval.
- Use NODE-032S selected runtime for remote validation and helper execution.
- Preserve NODE-032L safe temp-env guard, NODE-032N helper-bundle validation, and NODE-032P runtime dependency preflight.
- Keep Gateway smoke retry separate from dependency readiness and service enablement/reboot work.

Read-only finding:

```text
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_imports=httpx:0.28.1,fastapi:0.136.1,websockets:16.0
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
gateway_unit_verify=OK
gateway_service=inactive_disabled
gateway_env_meta=root:gateway:640
target_listeners_443_8080_8081=absent
ufw_8080_allow=92.118.85.117 only
```

Future approval phrase:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=approval_phrase_absent
```

## NODE-032AG Phase A Decision

NODE-032AG should proceed to one controlled transcript-event diagnostics smoke only after exact approval and immediate hard-gate re-confirmation.

Evidence:

```text
asterisk_safety_gates=passed
gateway_safety_gates=passed
realtime_gateway_marker_hash_valid=true
realtime_measurement_symbol_hash_valid=true
gateway_service=inactive_disabled
```

Decision:

```text
phase_b_smoke_can_be_requested=true
phase_b_approval_phrase=APPROVE NODE-032AG PHASE B LIVE SMOKE
phase_b_scope=one_controlled_asterisk_side_non_business_dialog_smoke
token_output=false
transcript_text_or_delta_logging=false
business_dialog_transcript_use=false
```

## NODE-032AG Phase B Smoke Decision

NODE-032AG Phase B was approved and completed exactly one controlled Asterisk-side non-business-dialog smoke after immediate hard-gate re-confirmation.

Decision:

- Accept NODE-032AG as successful deployed Gateway diagnostics propagation proof.
- The smoke proves Gateway reachability/auth, OpenAI Realtime session creation, audio chunk send, and redacted event-count propagation from the deployed runtime.
- Do not treat it as business-dialog integration, production autostart, transcript text correctness, or transcript-quality acceptance.

Evidence:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Next boundary:

```text
NODE-032AH / transcript-event-diagnostics-smoke-acceptance-and-next-boundary-decision
```

## NODE-032AH Acceptance Decision

Decision:

- Accept NODE-032AG as successful deployed Gateway diagnostics propagation proof.
- Treat `transcript_event_seen=true` and `transcript_bearing_event_seen=true` as proof that transcript-bearing events are reaching the redacted diagnostic path.
- Treat `diagnostic_propagation_gap=false` as closure of the deployed diagnostics propagation gap.
- Do not accept NODE-032AG as proof of transcript text correctness, non-empty transcript content, business-dialog integration, production autostart, full live-call/caller path, dual-channel recording, or safe transcript use in dialog.

Evidence:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_text_present=false
transcript_text_length_bucket=zero
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Next boundary:

```text
NODE-032AI / controlled-transcript-content-stimulus-quality-plan
```

## NODE-032AF Phase A Decision

NODE-032AF confirms the NODE-032AE service readiness blocker is a deployed Gateway runtime dependency mismatch.

Evidence:

```text
updated_deployed_realtime_gateway_py_marker=openai_event_type_counts_available
updated_deployed_realtime_gateway_py_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
required_symbol=diagnose_pcm_wav_audio_bytes
local_realtime_measurement_symbol=present
deployed_realtime_measurement_symbol=absent
local_deployed_realtime_measurement_hash_match=false
```

Decision:

```text
phase_b_rollout_can_be_requested=true
phase_b_scope=controlled_realtime_measurement_py_rollout_only
phase_b_approval_phrase=APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
smoke_in_phase_b=false_unless_separately_approved
```

Rejected for NODE-032AF Phase A:

```text
deploy_without_exact_approval=false
service_restart_in_phase_a=false
smoke_in_phase_a=false
token_handling_in_phase_a=false
```

## NODE-032AF Phase B Rollout Decision

NODE-032AF Phase B was approved and completed as a controlled Gateway runtime dependency rollout only.

```text
updated_dependency=realtime_measurement.py
backup_created=true
backup_dir=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z
diagnose_pcm_wav_audio_bytes_after_rollout=present
local_deployed_hash_match=true
service_action=false
smoke=false
```

The next boundary should verify Gateway readiness/smoke after the dependency rollout, using a separate exact approval gate. NODE-032AF deliberately did not combine dependency rollout with smoke.

## NODE-032Z Redacted Diagnostics Smoke Decision

1. Accept NODE-032Z Phase B as a successful controlled transport/auth/OpenAI Realtime smoke, not as transcript-event diagnostic success.
2. Preserve the exact Phase B approval phrase used: `APPROVE NODE-032Z PHASE B LIVE SMOKE`.
3. Record that hard gates passed before state-changing commands: Asterisk stayed `OPENAI_API_KEY_ABSENT`, business-dialog Gateway transcript use stayed not enabled, Gateway unit verified, Gateway env remained `root:gateway 640`, no target listeners existed before apply, and UFW remained source-restricted to `92.118.85.117`.
4. Record that helper bundle validation, valid 24 kHz mono 16-bit PCM audio validation, and safe temp-env create/validate/cleanup completed without token output or transcript text output.
5. Record that one malformed helper CLI command failed at argument parsing before any Gateway request; it is not counted as the controlled smoke.
6. Record the single corrected smoke result: Gateway reachable/auth OK, HTTP `200`, OpenAI Realtime OK, session created, and `chunks_sent=5`.
7. Preserve the business-dialog boundary: `transcript_text_logged=false`, `transcript_used_for_dialog=false`, and `business_dialog_unchanged=true`.
8. Record NODE-032Y diagnostic outcome as blocked: `openai_event_type_counts_present=false`, empty event counts, transcript-event flags null, `diagnostic_propagation_gap=true`, and `diagnostic_classification=diagnostic_propagation_gap`.
9. Preserve final safety state: Gateway service inactive/disabled, no target listeners on `443`, `8080`, or `8081`, firewall unchanged/source-restricted, Asterisk still has no `OPENAI_API_KEY`, and temporary helper/env/audio artifacts were removed.
10. Select next boundary: `NODE-032AA / gateway-event-diagnostics-propagation-gap-fix`.

## NODE-032AA Diagnostics Availability Marker Decision

1. Preserve NODE-032Z as a blocked diagnostic-propagation closeout, not a transcript-event success.
2. Add `openai_event_type_counts_available` as the safe field-availability marker.
3. Keep `openai_event_type_counts_present` as a value/content marker indicating whether event-count entries exist.
4. Treat `openai_event_type_counts_available=true` with `openai_event_type_counts={}` as propagated-but-empty diagnostics, not as a propagation gap.
5. Treat missing event-count diagnostics as `diagnostic_propagation_gap=true`.
6. Defensively strip `transcript_text` from Asterisk-side smoke reports whenever transcript logging is disabled.
7. Preserve business-dialog boundaries: `transcript_used_for_dialog=false`, transcript logging disabled, and business dialog unchanged.
8. Select next boundary: `NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix`.

## NODE-032Z Phase A Readiness Decision

Decision:

- Treat all live gates as stale because servers were powered on after a pause.
- Phase A may only document read-only state and plan Phase B.
- Phase B is conditional GO only after exact approval and immediate hard-gate re-confirmation.
- Future smoke evidence must use NODE-032Y redacted diagnostics only.

Approval phrase:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Phase A observed no blocking readiness issue beyond missing approval and stale-gate recheck requirement. Asterisk is reachable with `ai-secretary-ari.service` active/enabled, no Asterisk `OPENAI_API_KEY` in env/process, and business-dialog Gateway transcript use not enabled. Gateway is reachable with `ai-secretary-gateway.service` inactive/disabled, no target listeners, UFW active/restricted, and env metadata `root:gateway 640`.

## NODE-032Y Redacted Diagnostic Model Decision

Decision:

- Keep transcript text suppressed by default.
- Add event-count and transcript-event booleans at the Gateway response boundary.
- Convert any transcript text observation into safe booleans and `transcript_text_length_bucket`.
- Treat missing Asterisk-side event diagnostics as `diagnostic_propagation_gap` instead of leaving transcript-event fields ambiguous.
- Do not change business-dialog behavior, Gateway default enablement, production service state, or autostart.

Safe classifications:

```text
no_event_counts_available
no_transcript_event_observed
transcript_event_observed_empty_or_no_text
transcript_bearing_event_observed_text_redacted
timeout_after_audio_commit
openai_error_event_observed
diagnostic_propagation_gap
unknown
```

Rejected in NODE-032Y:

- logging transcript text or transcript deltas;
- using transcript text for dialog;
- changing Gateway session settings for live smoke;
- changing audio stimulus strategy;
- running live smoke or touching servers.

Next node:

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

## NODE-032W Transcript-Presence Smoke Readiness Decision

168. Preserve NODE-032W Phase A boundary: readiness and transcript-presence smoke planning only; no live smoke retry, helper copy/deploy, token handling, server temp env creation, dependency install, service action, `systemctl` state action, reboot, provider power-cycle, firewall/env/server change, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.
169. Preserve NODE-032W helper finding: existing Gateway adapter smoke reports include safe redacted transcript event/presence flags (`transcript_present`, `transcript_event_seen`, `transcript_bearing_event_seen`) while keeping transcript text unprinted when transcript logging remains disabled.
170. Preserve NODE-032W Phase A gate result: Asterisk gates pass with `OPENAI_API_KEY_ABSENT`, business-dialog Gateway transcript use not enabled, selected project venv imports `httpx 0.28.1`, `fastapi 0.136.1`, and `websockets 16.0`; Gateway unit verifies, service is inactive/disabled, env is `root:gateway 640`, masked secrets are present, no target listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
171. Preserve NODE-032W approval gate: Phase B requires exact phrase `APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE`; no other phrase is approval.
172. Preserve NODE-032W acceptance boundary: Phase B may prove transcript event/presence flags only and must keep transcript text logging disabled, business-dialog transcript use disabled, token output absent, and business dialog unchanged.
173. Preserve NODE-032W Phase B result: after exact approval and hard-gate re-confirmation, exactly one Asterisk-side non-business-dialog smoke ran with valid 24 kHz mono PCM audio and safe temp-env handling. Gateway transport/auth/OpenAI Realtime succeeded (`gateway_http_status=200`, `openai_realtime_from_gateway=ok`, `chunks_sent=5`), but transcript presence was not confirmed (`transcript_present=false`, `transcript_event_seen=null`, `transcript_bearing_event_seen=null`).
174. Preserve NODE-032W blocker: close NODE-032W as blocked for transcript-presence proof; do not retry inside NODE-032W. No token values or transcript text were printed, committed, or logged.
175. Preserve NODE-032W final state: Gateway service is inactive/disabled, no target listeners exist on `443`, `8080`, or `8081`, firewall remains source-restricted, Asterisk still has `OPENAI_API_KEY_ABSENT`, business dialog Gateway transcript use remains not enabled, and temporary helper/env/audio were removed.
176. Preserve NODE-032W next boundary: `NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan`.

177. Preserve NODE-032X local-only boundary: no live smoke, SSH, helper deploy, token handling, server temp env creation, service action, dependency install, reboot, provider power-cycle, firewall/env/server change, transcript text logging, business-dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, or automation is allowed in NODE-032X.
178. Preserve NODE-032X diagnostic decision: NODE-032W transport/auth/OpenAI Realtime success (`gateway_http_status=200`, `chunks_sent=5`) is not transcript-presence success because `transcript_present=false`, `transcript_event_seen=null`, and `transcript_bearing_event_seen=null`.
179. Preserve NODE-032X hypothesis ranking: insufficient redacted diagnostics is the primary next failure mode; speech-like audio stimulus length/content is secondary; event parser alias coverage and session settings remain possible but unproven.
180. Preserve NODE-032X selected next boundary: `NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts`.
181. Preserve NODE-032X evidence policy: the next node may collect event type counts, boolean transcript-event flags, audio diagnostics, timing, chunks, and HTTP status, but must not collect raw transcript text, transcript deltas, token values, raw secret env output, large logs, audio files, binary artifacts, or business-dialog profile changes.

## NODE-032U Phase B Valid Audio Smoke Decision

NODE-032U Phase B was approved with:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

Decision and result:

- Treat the NODE-032T invalid-audio blocker as resolved.
- Keep `24000 Hz mono 16-bit PCM WAV` as the smoke audio contract.
- Do not introduce `8 kHz`, stereo, or dual-channel architecture changes in this node.
- Keep business dialog transcript use disabled.
- Treat HTTP 200, Gateway auth OK, OpenAI Realtime OK, and chunks sent as successful transport/auth/Realtime proof for the valid-audio retry.
- Do not treat `accepted=false` as a dialog failure because `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remained enforced.

Evidence:

```text
audio_format=24000 Hz mono 16-bit PCM WAV
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent=5
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

Final state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged
asterisk_OPENAI_API_KEY=ABSENT
```

Next node:

```text
NODE-032V / gateway-smoke-result-acceptance-and-next-boundary-decision
```

## NODE-032V Gateway Smoke Acceptance Decision

NODE-032V is a local repo/docs decision node. No SSH, live smoke retry, helper deploy, token handling, temp env creation, service action, dependency install, `systemctl` action, reboot, provider power-cycle, firewall/env/server change, business-dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, or PR occurred.

Decision:

- Accept NODE-032U as successful controlled Gateway transport/auth/OpenAI Realtime smoke with valid `24000 Hz mono 16-bit PCM WAV` audio.
- Do not accept NODE-032U as transcript-quality success, transcript-present success, transcript text correctness proof, business-dialog integration proof, production autostart proof, or dual-channel caller/bot separation proof.
- Treat `accepted=false` with `gateway_stt_dialog_use_disabled` as expected for this non-business-dialog smoke because `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remained enforced.
- Keep smoke retry, transcript-present proof, business-dialog integration, production autostart, and dual-channel architecture as separate boundaries.

Accepted evidence:

```text
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

Options considered:

- Final Gateway transport/auth/OpenAI Realtime acceptance: accepted for this boundary.
- Controlled transcript-presence smoke: selected as next boundary.
- Direct business-dialog integration design: deferred until transcript-present behavior is proven separately.
- Production persistence/autostart: deferred because service autostart is useful but not the immediate STT acceptance blocker.
- Dual-channel recording/caller-bot separation: deferred to a separate architecture node.

Next node:

```text
NODE-032W / controlled-gateway-transcript-presence-smoke
```

## NODE-032AB Phase A Readiness Decision

Decision:

- Keep NODE-032AB Phase A read-only.
- Do not run smoke, deploy helper bundles, handle tokens, create temp env files, start/stop services, install dependencies, reboot, change firewall/env/server state, enable business-dialog transcript use, or log transcript text.
- Treat Phase B as conditional GO only after the exact approval phrase and immediate hard-gate re-confirmation.

Approval phrase:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

Phase A gate summary:

```text
asterisk_service=active_enabled
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
gateway_service=inactive_disabled
gateway_env_metadata=root:gateway:640
target_listeners_443_8080_8081=absent
ufw_8080_tcp=ALLOW_IN_FROM_92.118.85.117_ONLY
```

Future Phase B should prove whether the NODE-032AA `openai_event_type_counts_available` marker propagates in live smoke evidence, while keeping transcript text and business-dialog transcript use disabled.

## NODE-032AB Phase B Decision

Decision:

- Accept NODE-032AB as another successful Asterisk-origin Gateway transport/auth/OpenAI Realtime smoke.
- Do not accept NODE-032AB as live diagnostic propagation success.
- Keep transcript text logging disabled and business-dialog transcript use disabled.
- Keep Gateway service disabled/inactive after cleanup.
- Move the next boundary to a controlled Gateway runtime diagnostics propagation rollout/mapping plan.

Evidence:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent=5
openai_event_type_counts_available=false
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

Next node:

```text
NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
```

## NODE-032AC Runtime Propagation Decision

Decision:

- Treat NODE-032AB as transport/auth/OpenAI Realtime success but live diagnostics propagation failure.
- Do not run another smoke until the deployed Gateway runtime boundary is addressed.
- Select a controlled Gateway runtime diagnostics propagation rollout as the next boundary.

Reasoning:

```text
current_repo_realtime_gateway_adds_openai_event_type_counts_available=true
current_repo_helper_bundle_includes_updated_parser=true
live_gateway_service_uses=/opt/ai-secretary-gateway/src
node032ab_live_response_openai_event_type_counts_available=false
```

Selected next node:

```text
NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
```

Suggested approval phrase:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Rejected for immediate next step:

```text
blind_smoke_retry
business_dialog_enablement
transcript_text_logging
production_autostart
firewall_or_tls_changes
```

## NODE-032AD Phase A Runtime Rollout Decision

Decision:

- Treat NODE-032AD Phase A as read-only evidence that the live Gateway runtime is stale relative to the repo diagnostics marker.
- Allow Phase B rollout to be requested only with exact approval and immediate hard-gate re-confirmation.
- Keep smoke verification separate unless explicitly scoped after rollout.

Evidence:

```text
local_realtime_gateway_marker_present=true
deployed_realtime_gateway_marker_present=false
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
deployed_realtime_gateway_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
gateway_service_runtime_path=/opt/ai-secretary-gateway/src
gateway_service_state=inactive_disabled
```

Phase B approval phrase:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Rejected in Phase A:

```text
deploy
backup_creation
live_smoke
service_action
token_handling
firewall_change
business_dialog_enablement
transcript_text_or_delta_logging
```

## NODE-032AD Phase B Runtime Rollout Decision

Decision:

- Apply only the Gateway runtime diagnostics propagation file required for the safe event-count marker.
- Do not run smoke in NODE-032AD.
- Keep Gateway service inactive and disabled after rollout.
- Use a separate follow-up smoke node to verify runtime marker propagation over HTTP/OpenAI Realtime.

Result:

```text
backup_dir=/opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
openai_event_type_counts_available_marker_present=true
local_deployed_hash_match=true
service_action=false
firewall_unchanged=true
```

Next node:

```text
NODE-032AE / controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout
```

## NODE-032AE Blocked Smoke Decision

Decision:

- Treat NODE-032AE as blocked before smoke, not as failed Gateway/OpenAI smoke.
- Do not retry smoke until the deployed Gateway runtime dependency set is complete.
- Select a controlled rollout node for the missing `realtime_measurement.py` dependency.

Evidence:

```text
smoke_helper_invoked=false
gateway_request_reached=false
gateway_service_readiness_failed=true
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
```

Next node:

```text
NODE-032AF / controlled-gateway-runtime-measurement-dependency-rollout
```

## NODE-032T Phase B Gateway Smoke Retry Decision

NODE-032T Phase B was approved with:

```text
APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
```

Decision and result:

- Treat Phase A live gates as stale because the servers were stopped and later made reachable again.
- Re-run Asterisk and Gateway hard gates before staging helpers, handling token material, creating temp env, starting the Gateway service, or smoking.
- Use the NODE-032S selected runtime, NODE-032N complete helper bundle, NODE-032P runtime preflight, and NODE-032L safe temp-env guard.
- Run exactly one Asterisk-side non-business-dialog smoke.
- Do not retry inside NODE-032T after the single smoke invocation.

Outcome:

```text
hard_gates_reconfirmed=true
helper_bundle_validate=ok
safe_temp_env_create_validate_cleanup=ok
token_values_printed=false
gateway_service_started_for_smoke=true
systemctl_enable=false
controlled_smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=400
blocker=invalid_wav_sample_rate_16000_expected_24000
transcript_text_logged=false
business_dialog_unchanged=true
```

Final safety state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
```

Next node:

```text
NODE-032U / controlled-gateway-smoke-retry-with-valid-24khz-audio
```

## NODE-032U Phase A Valid Smoke Audio Decision

NODE-032U Phase A is local implementation and command planning only. No live smoke retry, SSH, helper copy/deploy, token handling, server temp env creation, dependency install, service action, `systemctl` action, reboot, provider power-cycle, firewall/env/server change, token output, transcript text output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, commit, or PR occurred.

Decision:

- Generate or validate future smoke WAV input through `scripts/asterisk_gateway_smoke_helper.py`.
- Require `24000 Hz mono 16-bit PCM WAV` before any Gateway request.
- Fail closed on `16000 Hz`, stereo, malformed, missing, empty, or non-PCM WAV input.
- Do not change Gateway behavior or accept a different audio contract in this node.
- Defer any `8 kHz`, stereo, or dual-channel caller/callee architecture decision to a separate future node.

Commands added for future retry planning:

```text
python scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <path>
python scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <path>
python scripts/asterisk_gateway_smoke_helper.py --audio <path>
```

Safety boundary:

```text
OPENAI_API_KEY_on_Asterisk=refused
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false required
STT_GATEWAY_LOG_TRANSCRIPT=false required
secret_values_printed=false
transcript_text_logged=false
business_dialog_unchanged=true
```

Future approval phrase:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=approval_phrase_absent
```
## NODE-032AI Transcript Content Stimulus Quality Decision

Date: 2026-06-08

Decision:

```text
accept_NODE_032AG_as_deployed_diagnostics_propagation_proof=true
accept_NODE_032AG_as_transcript_text_content_proof=false
remaining_issue=empty_or_zero_transcript_content
```

NODE-032AG proved Gateway/Auth/OpenAI Realtime transport, session creation, `chunks_sent=5`, transcript-bearing event observation, and redacted diagnostic propagation with `diagnostic_propagation_gap=false`.

NODE-032AI does not treat the remaining `transcript_text_present=false` and `transcript_text_length_bucket=zero` evidence as a transport/auth/runtime propagation failure.

Hypotheses to investigate later:

```text
smoke_audio_too_short
speech_stimulus_not_clear_or_speech_like_enough
audio_clipped_or_silence_dominant
commit_timing_or_buffer_window_too_short
session_transcription_settings_need_review
language_or_prompt_context_not_optimal
provider_transcription_completed_empty_despite_event
```

Selected next boundary:

```text
NODE-032AJ / controlled-transcript-content-stimulus-preparation
```

Rejected for NODE-032AI:

```text
repeat_same_live_smoke_unchanged
business_dialog_integration
production_autostart
real_customer_call
dual_channel_recording_proof
transcript_text_logging
using_transcript_for_dialog
```
## NODE-032AJ Stimulus Preparation Decision

Date: 2026-06-09

Decision:

```text
prepare_stimulus_strategy_before_next_smoke=true
create_or_commit_audio_artifact=false
run_live_smoke=false
next_boundary=NODE-032AK / controlled-transcript-content-smoke-with-prepared-stimulus
```

The next controlled smoke should use a longer, clearer, non-sensitive, non-silence-dominant, non-clipped `24000 Hz mono 16-bit PCM` stimulus and report pre-smoke audio diagnostics:

```text
duration
rms
peak
non_silent_ratio
```

Accepted metrics for the later smoke remain redacted:

```text
transcript_text_length_bucket=nonzero_bucket
actual_transcript_text_redacted=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
token_values_printed=false
```

Rejected for NODE-032AJ:

```text
business_dialog_integration
production_autostart
real_customer_call
dual_channel_recording_proof
transcript_text_logging
using_transcript_for_dialog
customer_audio
committed_audio_artifacts
```
## NODE-032AK Phase A Readiness Decision

Date: 2026-06-09

Decision:

```text
phase_a_read_only_gates_passed=true
phase_b_recommendation=CONDITIONAL_GO
phase_b_approval_required=true
approval_phrase=APPROVE NODE-032AK PHASE B LIVE SMOKE
```

Phase A confirms repo helpers are present, local focused tests pass, source/runtime diff is empty, Asterisk read-only safety gates pass, and Gateway read-only safety gates pass.

Phase B remains blocked until exact approval and immediate hard-gate re-confirmation. Phase B must not log transcript text/deltas, print tokens, use transcript for dialog, deploy helper persistence, enable services, broaden firewall, or commit audio/binary artifacts.
## NODE-032AK Controlled Smoke Decision

Date: 2026-06-09

Decision:

```text
phase_b_approval_received=true
exact_approval_phrase=APPROVE NODE-032AK PHASE B LIVE SMOKE
exactly_one_controlled_smoke_ran=true
accept_as_transport_auth_runtime_diagnostics=true
accept_as_transcript_content_success=false
```

NODE-032AK proved the Asterisk-to-Gateway transport/auth/OpenAI Realtime diagnostics path again with a longer prepared stimulus:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
```

NODE-032AK does not prove transcript content success:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

Next boundary:

```text
NODE-032AL / transcript-content-empty-after-prepared-stimulus-analysis
```
## NODE-032AL Transcript Content Analysis Decision

Date: 2026-06-09

Decision:

```text
accept_NODE_032AK_transport_auth_runtime_diagnostics=true
accept_NODE_032AK_transcript_event_observed=true
accept_NODE_032AK_transcript_content_success=false
remaining_problem=transcript_content_empty_after_prepared_stimulus
```

NODE-032AL rejects transport/auth/runtime diagnostics and diagnostic propagation as the current blocker because NODE-032AK recorded HTTP 200, OpenAI Realtime OK, session creation, `chunks_sent=20`, transcript event evidence, and `diagnostic_propagation_gap=false`.

The most likely next investigation boundary is local schema/stimulus/settings analysis before any future live smoke:

```text
next_boundary=NODE-032AM / transcript-content-empty-local-schema-and-stimulus-analysis
```

Rejected in NODE-032AL:

```text
live_smoke_retry
ssh_or_server_change
token_handling
temp_env_creation
service_action
firewall_or_env_change
transcript_text_or_delta_logging
audio_artifact_creation
business_dialog_integration
```
## NODE-032AM Schema And Stimulus Analysis Decision

Date: 2026-06-09

Decision:

```text
accept_current_supported_event_fields_as_locally_tested=true
accept_redaction_bucket_false_zero_as_unlikely=true
accept_alternate_provider_event_shape_gap_as_open=true
accept_actual_linguistic_stimulus_proof_gap_as_open=true
live_smoke_retry_now=false
```

Current supported fields:

```text
delta_text_field=payload.delta
completed_text_field=payload.transcript
nested_transcript_fields_read=none
```

Selected next boundary:

```text
NODE-032AN / transcript-event-schema-fixtures-and-nonzero-bucket-local-proof
```

Rationale:

```text
local_fixtures_before_live_retry=true
prove_nonzero_bucket_without_real_transcript_text=true
document_safe_actual_speech_stimulus_requirements=true
```
## NODE-032AN Fixture Proof Decision

Date: 2026-06-09

Decision:

```text
implement_selected_alternate_schema_fixture_support=true
preserve_redaction_and_bucket_safety=true
late_delta_after_completed_event_deferred=true
live_smoke_retry_now=false
```

Accepted local proof:

```text
nonzero_placeholder_text_maps_to_nonzero_redacted_bucket=true
empty_completed_event_maps_to_zero_bucket=true
smoke_report_preserves_zero_bucket_classification=true
placeholder_values_not_serialized_in_reports=true
```

Next boundary:

```text
NODE-032AO / safe-actual-speech-stimulus-and-session-settings-plan
```
## NODE-032AO Safe Stimulus And Session Settings Decision

Date: 2026-06-09

Decision:

```text
accept_transport_auth_runtime_diagnostics_as_proven=true
accept_diagnostic_propagation_as_proven=true
accept_local_nonzero_bucket_mapping_as_proven=true
accept_current_live_transcript_content_success=false
live_smoke_retry_now=false
```

Selected next strategy:

```text
safe_actual_speech_stimulus_required=true
stimulus_label=SAFE_RU_SHORT_COMMAND
actual_spoken_text_committed=false
audio_committed=false
keep_current_session_settings_for_first_next_smoke=true
```

Rejected now:

```text
business_dialog_integration
production_autostart
real_customer_audio
committed_audio_fixture
transcript_text_or_delta_logging
multiple_smoke_retries
session_setting_changes_before_actual_speech_proof
```

Next boundary:

```text
NODE-032AP / controlled-actual-speech-transcript-content-smoke
approval_phrase=APPROVE NODE-032AP PHASE B LIVE SMOKE
```
## NODE-032AP Phase A Gate Decision

Date: 2026-06-09

Decision:

```text
phase_b_go=false
reason=asterisk_ssh_timeout
live_smoke_run=false
audio_generated=false
helper_deploy=false
token_handling=false
service_action=false
server_state_change=false
```

The future actual-speech smoke remains the selected boundary, but it is not approved or runnable while the Asterisk SSH gate is unavailable.

Required future approval phrase remains:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```
## NODE-032AQ Reachability Decision

Date: 2026-06-09

Decision:

```text
phase_b_go=false
reason=asterisk_ssh_still_unreachable
classification=provider_control_unavailable
secondary_classification=unknown_reachability_failure
power_on_occurred=false
live_smoke_run=false
server_state_change=false
```

Accepted conclusion:

```text
repo_or_ssh_only_recovery_not_possible=true
out_of_band_provider_or_network_recovery_required=true
```

NODE-032AP Phase B remains blocked until Asterisk SSH reachability is restored and read-only hard gates pass.

## NODE-032AR Read-Only Reachability Evidence Decision

Date: 2026-06-11

Decision:

```text
asterisk_ssh_timeout_resolved=true
phase_b_go=false
live_smoke_run=false
server_state_change=false
source=coordinator_collected_read_only_evidence
```

The coordinator evidence shows TCP 22 reachable and SSH login OK on host `tula`. Ping still timed out, but that is not blocking because SSH over TCP 22 works. `asterisk.service` is absent from systemd, but the Asterisk runtime process is present under `tulauser`; future gates should treat process readiness as the relevant observed runtime condition unless the architecture changes.

`ai-secretary-ari.service` is active/enabled and the app is ready for calls according to the supplied evidence. NODE-032AR does not approve live smoke; any Phase B still requires the exact approval phrase and immediate hard-gate re-check.

The Selectel disk image exists as fallback and was not touched. The Asterisk server was started out of band by user/provider action before this node; Codex performed no power, SSH, smoke, deploy, token, temp-env, service, firewall, env, or server mutation action.

## NODE-032AS Gateway Hard-Gate Decision

Date: 2026-06-11

Decision:

```text
phase_b_go=false
reason=gateway_ssh_unreachable_or_powered_off
gateway_tcp_22_reachable=false
gateway_ssh_attempted=false
gateway_power_on_occurred=false
provider_controls_used=false
live_smoke_run=false
server_state_change=false
```

Asterisk recovery evidence from NODE-032AR can be considered recovered, but future Phase B cannot proceed while the Gateway hard gate is unavailable. The next step is out-of-band Gateway start/recovery followed by read-only Gateway preflight.

## NODE-032AT Gateway Recovery Read-Only Decision

Date: 2026-06-11

Decision:

```text
gateway_tcp_22_recovered=true
gateway_ssh_recovered=true
phase_b_go=false
reason=full_gateway_hard_gate_not_yet_satisfied
live_smoke_run=false
gateway_mutation=false
server_state_change=false
```

Gateway host-level SSH recovery is proven. Phase B remains not approved because the bounded read-only status did not observe a Gateway app process, matching running service, or target listener, and this node did not perform the full unit/env/firewall/masked-secret hard-gate set.

Next decision boundary:

```text
NODE_032AU_full_gateway_readonly_hard_gate_after_kamatera_recovery
```

## NODE-032AU Full Gateway Hard-Gate Decision

Date: 2026-06-11

Decision:

```text
gateway_tcp_22_recovered=true
gateway_ssh_recovered=true
phase_b_go=false
reason=gateway_service_installed_disabled_without_runtime_or_listener
live_smoke_run=false
gateway_mutation=false
docker_mutation=false
server_state_change=false
```

The full read-only inventory found a disabled `ai-secretary-gateway.service` unit file but no running Gateway app process, no Docker runtime candidate, and no target listener on `443`, `8080`, or `8081`. This clears host reachability but not service readiness.

Next decision boundary:

```text
NODE-032AV / controlled-gateway-service-readiness-recovery-plan
```

## NODE-032AV Gateway Service Readiness Recovery Decision

Date: 2026-06-11

Decision:

```text
docs_only=true
phase_b_go=false
live_action_run=false
selected_next_boundary=controlled_gateway_service_readiness_recovery_live_action
approval_phrase=APPROVE NODE-032AW GATEWAY SERVICE READINESS RECOVERY
```

NODE-032AV selects a narrow service-readiness recovery node before any smoke is retried. The future node may only start the already-installed Gateway service after exact approval and immediate hard-gate re-check, then verify active state, expected `8080` listener, no `443`/`8081`, unchanged firewall, safe logs, and rollback to inactive/disabled.

Deferred boundaries:

```text
gateway_smoke=false
helper_deploy=false
token_handling=false
temp_env_creation=false
openai_requests=false
business_dialog_integration=false
production_autostart=false
docker_mutation=false
firewall_or_env_change=false
```

Next decision boundary:

```text
NODE-032AW / controlled-gateway-service-readiness-recovery-live-action
```

## NODE-032AW Gateway Service Readiness Recovery Decision

Date: 2026-06-11

Decision:

```text
approval_phrase=APPROVE NODE-032AW GATEWAY SERVICE READINESS RECOVERY
service_start_allowed=true
service_stop_allowed=true
smoke_allowed=false
phase_b=false
hard_gate_result=NO_GO
reason=service_active_but_8080_listener_not_observed_in_immediate_check
final_state_restored=true
```

The approved live-action boundary was respected. `ai-secretary-gateway.service` started and became active while remaining disabled, and the Gateway runtime process appeared with `--port 8080`. The immediate listener inventory did not show an `8080` listener, and the safe log filter had a quoting error, so service readiness is not accepted.

No smoke, call, Gateway HTTP request, token handling, temp env creation, helper deploy, OpenAI request, service enable/disable/restart/reload, Docker mutation, firewall/env/server/app config change, audio generation/upload, or disk image action occurred.

Next decision boundary:

```text
NODE-032AX / gateway-service-readiness-listener-and-log-preflight-fix
```

## NODE-032AX Gateway Listener And Log Preflight Decision

Date: 2026-06-11

Decision:

```text
docs_only=true
live_action_run=false
node_032aw_readiness_accepted=false
selected_next_boundary=controlled_gateway_listener_and_log_readiness_check
approval_phrase=APPROVE NODE-032AY GATEWAY LISTENER AND LOG READINESS CHECK
```

NODE-032AX accepts that NODE-032AW proved service startability and process creation, but not listener readiness. The future readiness procedure must use a bounded wait for the `8080` listener and a quote-safe journal filter before any smoke is reconsidered.

Corrective procedure:

```text
listener_wait=ten_one_second_iterations_for_8080
safe_journal_filter=simple_journalctl_pipe_to_grep
redaction_marker=REDACTED_TOKEN_LIKE_LOG_LINE
stop_if_8080_absent_after_wait=true
stop_if_safe_log_filter_unavailable=true
```

Deferred boundaries:

```text
smoke=false
calls=false
phase_b=false
gateway_request=false
token_handling=false
temp_env_creation=false
helper_deploy=false
openai_requests=false
docker_mutation=false
firewall_or_env_change=false
service_enablement=false
```

Next decision boundary:

```text
NODE-032AY / controlled-gateway-listener-and-log-readiness-check
```

## NODE-032AY Gateway Listener And Log Readiness Decision

Date: 2026-06-11

Decision:

```text
approval_phrase=APPROVE NODE-032AY GATEWAY LISTENER AND LOG READINESS CHECK
service_start_allowed=true
service_stop_allowed=true
smoke_allowed=false
phase_b=false
hard_gate_result=GO_FOR_SERVICE_READINESS_ONLY
final_state_restored=true
```

NODE-032AY accepts the narrow service-readiness proof: the Gateway service can start, remains disabled, spawns the expected runtime process, exposes `8080` after a bounded wait, avoids `443` and `8081`, produces safe redacted readiness log evidence, and restores to inactive/disabled.

Deferred boundaries:

```text
gateway_smoke=false
gateway_request=false
openai_requests=false
token_handling=false
temp_env_creation=false
helper_deploy=false
business_dialog_integration=false
production_autostart=false
service_enablement=false
docker_mutation=false
firewall_or_env_change=false
```

Next decision boundary:

```text
NODE-032AZ / controlled-actual-speech-transcript-content-smoke-after-gateway-readiness
```

## NODE-032AZ Resume Preflight Decision

Date: 2026-06-13

Decision:

```text
readonly_preflight_complete=true
asterisk_reachable=true
gateway_reachable=true
gateway_pre_smoke_baseline=PASS
smoke_allowed_in_node=false
node_032ba_may_be_opened=true
```

NODE-032AZ confirms the post-pause infrastructure state is suitable for opening the next separately approved smoke node. Asterisk is reachable with `ai-secretary-ari.service` active/enabled and ready, while Gateway is reachable but inactive/disabled with no target listeners and no Gateway runtime process.

Deferred boundaries:

```text
smoke=false
calls=false
phase_b=false
gateway_request=false
token_handling=false
temp_env_creation=false
helper_deploy=false
openai_requests=false
service_action=false
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_mutation=false
```

Next decision boundary:

```text
NODE-032BA / controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight
```

## NODE-032BA Smoke Blocker Decision

Date: 2026-06-13

Decision:

```text
approval_phrase=APPROVE NODE-032BA CONTROLLED ACTUAL SPEECH TRANSCRIPT CONTENT SMOKE
hard_gate_result=NO_GO
smoke_attempt_count=0
gateway_service_started=false
reason=asterisk_smoke_helper_absent_and_token_boundary_absent
```

NODE-032BA did not proceed to service start or smoke because the required Asterisk-side smoke helper was absent and no existing Gateway token runtime env was present. The approved scope forbade helper deploy, temp env creation, and token handling, so there was no safe in-scope way to run the smoke.

Deferred boundaries:

```text
smoke=false
gateway_request=false
openai_request=false
helper_deploy=false
temp_env_creation=false
token_handling=false
service_action=false
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_mutation=false
```

Next decision boundary:

```text
NODE-032BB / restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

## NODE-032BB Restore Boundary Decision

Date: 2026-06-13

Decision:

```text
approval_phrase=APPROVE NODE-032BB RESTORE SMOKE HELPER AND TOKEN BOUNDARY ONLY
restore_helper=true
restore_credential_boundary=true
run_smoke=false
gateway_request=false
phase_b=false
```

NODE-032BB accepted the narrow restore boundary only. The approved repo-supported smoke helper bundle was restored to the Asterisk project path, and the Asterisk-side credential boundary was created through the existing safe temp-env guard with Gateway token material piped to stdin only.

Safety decisions:

```text
token_values_printed=false
raw_env_printed=false
transcript_text_logged=false
transcript_delta_logged=false
business_dialog_config_mutation=false
docker_mutation=false
firewall_mutation=false
service_enable_disable_restart_reload=false
```

Next decision boundary:

```text
NODE-032BC / controlled-actual-speech-transcript-content-smoke-after-helper-and-token-boundary-restore
```

NODE-032BC requires fresh exact smoke approval and immediate hard-gate re-check.

## NODE-032BC Transcript Content Smoke Decision

Date: 2026-06-13

Decision:

```text
approval_phrase=APPROVE NODE-032BC CONTROLLED TRANSCRIPT CONTENT SMOKE ONLY
run_one_smoke=true
smoke_attempt_count=1
accept_redacted_transcript_content_proof=true
phase_b=false
repeated_smoke_loop=false
```

NODE-032BC proves the restored helper and credential-boundary path can run a controlled Asterisk-origin Gateway transcript-content smoke with Gateway HTTP 200, OpenAI Realtime OK, event diagnostics present, transcript event flags true, and `transcript_text_length_bucket=nonzero_redacted`.

Non-accepted boundaries:

```text
raw_transcript_text_correctness=false
business_dialog_integration=false
production_autostart=false
live_customer_call=false
dual_channel_recording=false
```

Safety:

```text
raw_transcript_text_printed=false
transcript_delta_printed=false
token_values_printed=false
raw_env_printed=false
business_dialog_config_mutation=false
docker_mutation=false
firewall_or_env_mutation=false
service_enable_disable_restart_reload=false
disk_image_touched=false
```

Next decision boundary:

```text
NODE-032BD / transcript-content-smoke-acceptance-and-business-dialog-boundary-decision
```

## NODE-032BD Acceptance And Business Dialog Boundary Decision

Date: 2026-06-14

Decision:

```text
accept_NODE_032BC_as_transcript_content_presence_proof=true
accepted_scope=prepared_actual_speech_smoke_path_only
enable_business_dialog_transcript_use_now=false
next_live_or_runtime_work_requires_separate_approved_node=true
preferred_next_node=NODE-032BE / controlled-business-dialog-transcript-use-design-and-guardrails
```

NODE-032BC is accepted as proof that the restored helper and credential boundary can produce redacted nonzero transcript-content presence in one controlled prepared actual-speech smoke.

It is not accepted as proof of semantic transcript accuracy, production call handling, real customer audio, business-dialog transcript use, latency/SLA, repeated-run stability, load/error resilience, or production monitoring/alerting.

The business-dialog transcript-use boundary remains closed until a separate design/guardrails node defines default-off configuration, explicit approval, fallback behavior, redaction/logging, acceptance criteria, and rollback.

## NODE-032BE Business Dialog Transcript Use Guardrails Decision

Date: 2026-06-14

Decision:

```text
business_dialog_transcript_use_remains_disabled=true
future_flags_design_only=true
separate_implementation_node_required=true
separate_live_validation_node_required=true
preferred_next_node=NODE-032BF / disabled-by-default-business-dialog-transcript-use-implementation
future_live_node=NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default
```

Reserved design-only flags:

```text
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=false
BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
```

Logging decision:

```text
raw_transcript_text_logging=false
transcript_delta_logging=false
token_value_logging=false
raw_env_value_logging=false
diagnostic_outputs_only=true
```

NODE-032BE does not implement runtime behavior, enable business-dialog transcript use, run smoke, access servers, handle tokens, create temp env files, or change service/firewall/env/server/app state.

## NODE-032BF Disabled-By-Default Transcript Use Implementation Decision

Date: 2026-06-14

Decision:

```text
implement_disabled_by_default_business_dialog_transcript_policy=true
default_enabled=false
adapter_requires_business_policy_opt_in=true
raw_transcript_logging=false
future_live_validation_required=true
next_node=NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default
```

The implementation adds a pure local policy boundary and adapter enforcement. `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` is no longer sufficient by itself for accepted business-dialog transcript use; `BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true` must also allow the transcript candidate.

The policy fails closed for missing, stale, low-confidence, incomplete-metadata, or redaction-guard-inactive transcripts and preserves fallback behavior.

NODE-032BF did not run smoke, access servers, send Gateway/OpenAI requests, handle tokens, create temp env files, deploy helpers, change services, mutate Docker, change firewall/env/server/app config, enable runtime transcript use, generate audio, or touch the disk image.

## NODE-032BI Disabled Live Smoke Policy Field Decision

Date: 2026-06-15

Decision:

```text
accept_disabled_live_smoke_policy_field_proof=true
business_dialog_transcript_policy_fields_visible_in_live_smoke=true
business_dialog_transcript_use_remains_disabled=true
enabled_business_dialog_transcript_use_requires_separate_node=true
next_node=NODE-032BJ / controlled-business-dialog-transcript-use-enablement-boundary-decision
```

NODE-032BI is accepted as proof that the disabled live smoke path exposes the `business_dialog_transcript_*` policy fields after the NODE-032BH refresh.

It does not approve business-dialog transcript use enablement, production call-path use, real caller/customer audio, raw transcript logging, transcript delta logging, token/env output, service enablement, Docker mutation, firewall/env/server/app config mutation, or any disk image action.

## NODE-032BJ Enabled Transcript Use Validation Design Decision

Date: 2026-06-15

Decision:

```text
repo_only_design_for_enabled_validation=true
enable_business_dialog_transcript_use_now=false
live_validation_performed=false
enabled_live_dialog_use_proven=false
future_enabled_validation_requires_separate_approval=true
next_node=NODE-032BK / controlled-enabled-business-dialog-transcript-use-live-smoke
```

The future enabled-validation node must use temporary explicit flags only:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
```

NODE-032BJ requires fail-closed behavior, redacted logs, no raw transcript text, no transcript deltas, no token/env output, one-smoke limit, Gateway restore, temporary-flag cleanup, and separate approval before any live enabled smoke.

## NODE-032BK Approval Gate And Blocker Decision

Date: 2026-06-15

Decision:

```text
open_enabled_live_smoke_node=true
approval_phrase_received=true
live_preflight_completed=true
hard_gates_passed=true
enabled_smoke_invocation_attempted_once=true
gateway_request_sent=false
enabled_live_dialog_use_proven=false
classification=blocked_command_quoting_env_dump_missing_gateway_flags
```

NODE-032BK must not run a second smoke without coordinator review and new explicit approval. The next decision should address a quote-safe env-loading and enabled adapter smoke command path.

The exact approval phrase used for NODE-032BK was:

```text
APPROVE NODE-032BK CONTROLLED ENABLED LIVE SMOKE
```

No Gateway request, real call, real caller/customer audio, token value output, Authorization header output, transcript text output, transcript delta output, Docker mutation, firewall broadening, persistent transcript-use enablement, or disk image action occurred.

## NODE-032BL Quote-Safe Env Loading Decision

Date: 2026-06-15

Decision:

```text
implement_quote_safe_helper_env_file_loading=true
avoid_ad_hoc_inline_shell_source=true
missing_required_flags_by_name_only=true
shell_environment_dump_printed=false
gateway_request_sent=false
enabled_live_dialog_use_proven=false
next_node=NODE-032BM / controlled-enabled-live-smoke-retry-with-safe-env-loader
```

NODE-032BL chooses a helper-owned env-file parser and explicit dialog transcript-use mode instead of remote shell `source`/`set -a` command construction. Future live retry still requires separate exact approval.

## NODE-032BM Safe Env Loader Retry Gate Decision

Date: 2026-06-15

Decision:

```text
prepare_enabled_live_smoke_retry_package=true
use_NODE_032BL_quote_safe_env_loader=true
live_approval_received=false
enabled_live_dialog_use_proven=false
classification=blocked_pending_exact_live_approval
```

Phase 2 decision after exact approval:

```text
approval_phrase_received=true
read_only_live_preflight_allowed=true
asterisk_read_only_gates_passed=true
gateway_ssh_reachable=false
hard_gate_result=NO_GO
smoke_count=0
enabled_live_dialog_use_proven=false
classification=blocked_pending_kamatera_gateway_power_on
```

No live action is approved until this exact phrase is received in a separate coordinator message:

```text
APPROVE NODE-032BM CONTROLLED ENABLED LIVE SMOKE WITH SAFE ENV LOADER
```

The future retry must use helper-owned `--env-file`, `--dialog-transcript-use enabled`, and `--dry-run-env-check` before smoke. It must not use shell `source`, `set -a`, nested shell quoting, shell environment dumps, token/env value output, Authorization header output, raw transcript text, or transcript deltas.

NODE-032BM Phase 2 stopped before dry-run env validation and before smoke because Gateway SSH timed out. Coordinator later clarified that Kamatera/Gateway had not yet been powered on, so the timeout is now classified as `blocked_pending_kamatera_gateway_power_on` rather than an unexplained Gateway failure. It did not start Gateway, run smoke, send a Gateway request, enable transcript-use flags, handle tokens or real env values, mutate service/Docker/firewall/env/server/app config, generate/upload live audio, touch the disk image, write Notion, or write Runtime/Evidence.

## NODE-032BN Server Power-On Readiness Decision

Date: 2026-06-15

Decision:

```text
accept_operator_power_on_confirmation=true
run_read_only_power_on_preflight=true
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
gateway_ready_for_future_approval_gated_checks=true
final_classification=readiness_passed
```

NODE-032BN confirms the prior NODE-032BM Gateway SSH timeout was resolved after operator power-on. It does not approve smoke, quote-safe dry-run env validation, Gateway start, Gateway request, transcript-use enablement, token/env value handling, service/Docker/firewall/env/server/app mutation, live audio action, disk image action, Notion write, or Runtime/Evidence write.

## NODE-032BO Enabled Retry Planning Decision

Date: 2026-06-29

Decision:

```text
prepare_next_enabled_live_smoke_retry_plan=true
phase1_repo_planning_only=true
server_power_on_requested=false
live_server_action=false
enabled_live_dialog_use_proven=false
final_classification=phase1_repo_planning_ready_pending_server_power_on
```

Future live work requires a fresh coordinator instruction, explicit operator power-on confirmations for Asterisk and Gateway, read-only quick preflight, quote-safe dry-run env check, Gateway start only after all hard gates pass, exactly one controlled enabled smoke, safe diagnostics only, cleanup/rollback, and coordinator review.

## Pause AI-Secretary at Reproducible Checkpoint

Date: 2026-07-11

Decision: pause AI-secrenar-with-Asterisk after the two-day viability sprint. Core transport, redaction, and helper boundaries are technically viable; the remaining blocker is narrow, but continuation requires a controlled temporary credential-boundary mutation and a later separately approved live smoke. Operations Control Plane Closed Loop becomes the higher-priority development direction, while this complete resume package is preserved.

Constraints: no persistent transcript-use enablement, no inherited live approval, servers remain off, and future work begins with a separate temporary credential-boundary node.
