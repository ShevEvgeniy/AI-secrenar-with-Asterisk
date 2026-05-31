# Decisions

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
