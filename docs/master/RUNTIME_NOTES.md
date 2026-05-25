# Runtime Notes

## Confirmed Runtime Behavior

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are active in `master`.
- Transfer after data collection is active in `master`.
- ARI continue is the established transfer mechanism.
- Partial publish failures are now classified with `reason` and `failed_step`.
- Startup can remain resilient when system-sounds prepublish partially fails.
- `user_transcribed` is tied to real downloaded caller audio artifacts instead of canned placeholder text.
- Missing stage and transfer media use controlled meaningful fallback phrases instead of `demo-congrats`.
- Real live transcription requires `TELEPHONY_STT_BACKEND` to be explicitly configured, for example `openai` or `whisper_api`.

## Transfer Route Target

The current target route is:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
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
 same => n,Dial(PJSIP/78007074193@thermo-trunk-endpoint,60,D(ww52144))
 same => n,Hangup()
```

NODE-001 live validation completed successfully with ARI continue to:

```text
context=from-internal
extension=sales_real
priority=1
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

- During live validation, MicroSIP using the wrong Windows input device produced a false negative for dialog capture.
- Selecting the correct Windows microphone fixed live ISSUE / NAME / CITY / PHONE capture.
- The validated transfer path is merged into `master`.

## NODE-002 Runtime Notes

- During startup, `prompt_3` and transfer system sounds failed to publish because SSH to `92.118.85.117:22` timed out.
- Despite that partial prepublish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- During the live call, fallback media was used instead of missing `prompt_3` and the missing transfer phrase.
- Transfer still completed successfully to:

```text
context=from-internal
extension=sales_real
priority=1
```

## NODE-003 Runtime Notes

- NODE-003 replaced `demo-congrats` fallback use with controlled prompt/transfer fallbacks and non-demo built-ins.
- NODE-003 removed canned `user_transcribed` content from the live dialog path. Transcription events now identify the exact call id, stage, recording name, local audio path, byte size, and SHA-256. If no STT backend is configured, the event is logged as unavailable instead of fabricated.
- NODE-003 fixed the previously observed integrity problem where runtime logs showed transcribed text that did not match what the caller says they actually spoke.
- Next runtime validation should run one live smoke with a real STT backend configured.

## NODE-004 Runtime Notes

- Successful PHONE capture is now an immediate transfer boundary in the ARI dialog loop.
- Live smoke `1777640788.40` exposed an STT formatting case where the phone was transcribed as `920.032.0355`; PHONE parsing now accepts dotted numeric separators and normalizes that to `79200320355`.
- Validated live smoke `1777641576.42` confirmed ISSUE / NAME / CITY / PHONE each reached `user_transcribed=ok`.
- After PHONE in live smoke `1777641576.42`, events showed `play_transfer_phrase` followed by `transfer status=ok`.
- `pipeline_start`, `build_response`, and `reply.wav` did not occur after PHONE in the validated call.
- Expected event order after a valid PHONE transcript:

```text
user_transcribed(PHONE) -> play_transfer_phrase -> transfer(context=from-internal, extension=sales_real, priority=1)
```

- The generic response path must not run on that successful PHONE path, so `pipeline_start`, `build_response`, `publish`, and generic `playback` should be absent after valid PHONE collection.

## NODE-005 Runtime Notes

- Turn-taking contour is stabilized for the current live flow.
- NAME no longer breaks the whole flow.
- NAME playback barrier is in place.
- PHONE and PHONE_CONFIRM work in live flow.
- Confirmation prompt speaks the phone number as spoken digits.
- Live validation `1777717705.10` reached:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- Runtime transfer target remains:

```text
context=from-internal
extension=sales_real
priority=1
```

- NODE-005 solved the latency and turn-taking contour for the current flow, but NAME quality still needs improvement in NODE-006.

## NODE-006 Runtime Notes

- NAME capture quality is hardened without changing the overall call architecture.
- NAME STT explicitly uses Russian language and Russian-name prompt context.
- Bounded post-STT normalization for Russian names, patronymics, and common conversational forms is present.
- NAME prompt wording is simplified to:

```text
Назовите, пожалуйста, ваше имя.
```

- NAME playback barrier remains in place, so NAME recording no longer starts over prompt playback.
- Live validation `1777721580.0` recognized NAME as `Иван Семёнович` and reached:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

- NODE-006 does not introduce multi-department routing.

## NODE-007 Runtime Notes

- Bounded department intent routing is working for:
  - sales;
  - accounting;
  - delivery.
- Routing remains deterministic and debuggable.
- The validated collection flow is preserved:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> transfer
```

- Routing contract:

```text
sales -> context=from-internal, extension=sales_real, priority=1
accounting -> context=from-internal, extension=accounting, priority=1
delivery -> context=from-internal, extension=delivery, priority=1
```

- Unclear intent remains bounded and routes to the configured default department.
- Final transfer phrase is department-specific:

```text
sales: Хорошо, я соединяю вас с отделом продаж.
accounting: Хорошо, я соединяю вас с бухгалтерией.
delivery: Хорошо, я соединяю вас с отделом доставки.
```

- Live validation references:
  - `1777725117.4`: sales intent -> `department=sales`, `context=from-internal`, `extension=sales_real`, `priority=1`.
  - `1777726120.10`: accounting intent -> accounting phrase resolved and played -> `department=accounting`, `context=from-internal`, `extension=accounting`, `priority=1`.
  - `1777726440.12`: delivery intent -> delivery phrase resolved and played -> `department=delivery`, `context=from-internal`, `extension=delivery`, `priority=1`.

## NODE-008 Runtime Notes

- Immediate transfer requests no longer bypass required data collection.
- Mandatory data before live transfer remains:
  - `name`;
  - `city`;
  - `phone`;
  - `phone_confirmed=true`.
- Stage-aware responses are implemented when the caller asks for immediate transfer.
- Bounded `INTENT_CLARIFY` is implemented for unclear or tied department intent.
- Bounded retry policy is implemented by stage:
  - ISSUE retries, then moves to `INTENT_CLARIFY`;
  - `INTENT_CLARIFY` retries, then defaults to the configured department;
  - NAME/CITY/PHONE use bounded retries, then `SAFE_FINISH`;
  - PHONE_CONFIRM has its own bounded policy and is not cut off by generic global turn limits.
- PHONE and PHONE_CONFIRM are effectively governed by stage-local policy rather than prematurely terminated by generic accumulated turn cutoff.
- `INTENT_CLARIFY` timeout and empty outcomes are handled as normal outcomes, not unhandled exceptions.
- `SAFE_FINISH` is terminal/non-transfer and supports reason-based spoken phrases before hangup:
  - `missing_required_data`;
  - `intent_not_resolved`;
  - `phone_not_confirmed`.

## NODE-009 Runtime Notes

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
- After-hours phrase playback completes before hangup.
- Transfer is explicitly skipped and logged in after-hours mode.
- Opening prompt is now:

```text
Здравствуйте. Меня зовут Анна. Я виртуальный секретарь. По какому вопросу вы обращаетесь?
```

- After-hours phrases now end with:

```text
Спасибо за звонок. До свидания.
```

- Versioned after-hours system sounds are used for refreshed wording:

```text
sound:ai_secretary/_system/after_hours_sales_v2
sound:ai_secretary/_system/after_hours_accounting_v2
sound:ai_secretary/_system/after_hours_delivery_v2
```

## NODE-012 Runtime Notes

- NODE-012 is closed for normal sales flow with compound CITY/address.
- CITY transcript validation accepts region/city anchor plus location detail.
- Final smoke `1778258401.18` accepted:

```text
raw=Владимирская область, Петушки, Красноармейская улица, 141.
city_transcript_validation status=ok
reason=region_with_location_detail
accepted=true
canonical_city=Владимирская область
location_detail=Петушки, Красноармейская улица, 141
transition=CITY -> PHONE
```

- English/STT filler such as `Thank you`, `you`, `ok`, `yes`, `no`, `hello`, and `goodbye` is rejected for CITY.
- Russian-only caller-facing invariant is added.
- CITY retry prompt uses static sound `prompt_city_retry` with `dynamic=false`.
- SAFE_FINISH phrase waits for real `PlaybackFinished` before hangup.
- Garbage without city/region anchor remains rejected.
- PHONE remains conservative with `phone_digit_safety_skip`.
- PHONE_CONFIRM fast path works with static digit sequence.
- Transfer to `sales_real` still requires `phone_confirmed=true`.
- Known remaining UX debt:
  - CITY and PHONE can still have long recording windows;
  - PHONE is intentionally conservative for digit safety;
  - further pause reduction should move to a new node, likely a streaming STT / `gpt-realtime-whisper` spike.

## NODE-013 Runtime Notes

- Feature-flagged OpenAI Realtime Whisper STT adapter is implemented.
- Default remains disabled:

```text
STT_STREAMING_ENABLED=false
```

- Supported spike settings include:

```text
STT_STREAMING_PROVIDER=openai_realtime_whisper
STT_STREAMING_MODEL=gpt-realtime-whisper
STT_STREAMING_LANGUAGE=ru
STT_STREAMING_FALLBACK_TO_BATCH=true
```

- Existing batch Whisper path is preserved.
- Streaming errors fall back to the existing batch path when fallback is enabled.
- Instrumentation includes:
  - `stt_stream_session_started`;
  - `stt_stream_audio_chunk_sent`;
  - `stt_stream_first_delta_received`;
  - `stt_stream_final_received`;
  - `stt_stream_error`;
  - `stt_stream_fallback_to_batch`.
- Metrics include:
  - `stt_stream_latency_first_delta_ms`;
  - `stt_stream_latency_final_ms`;
  - `stt_stream_total_audio_ms`;
  - `stt_batch_baseline_latency_ms`.
- Important caveat: current spike streams stored WAV artifacts after recording download. It validates adapter, metrics, feature flag, and fallback behavior, but does not prove caller-perceived pause reduction in live calls.

## NODE-014 Runtime Notes

- NODE-014 completed as a server-side ARI media-path proof.
- Colocated/server-side `ari_app` near Asterisk is proven for RTP diagnostics.
- Local sound publish works without SSH when launched server-side.
- Asterisk ARI connected as `Stasis(ai_secretary)` over local ARI.
- Validated topology:

```text
snoop_external_media_rtp
```

- Validated RTP target:

```text
bind=0.0.0.0
advertised_host=172.18.0.1
```

- Runtime evidence:
  - `SYSTEM_SOUNDS_DONE ok`;
  - `ARI_LISTENING http://127.0.0.1:8088/ari ai_secretary`;
  - `ARI_WS_CONNECTED`;
  - `stt_live_rtp_packets_received_count > 0`;
  - `stt_live_pcm_chunks_created_count > 0`;
  - `stt_live_rtp_diagnostics_result=rtp_packets_received`.
- The later `NAME -> SAFE_FINISH` path in the RTP-only smoke is not a media failure. Batch STT was intentionally pointed to dummy `OPENAI_BASE_URL=http://127.0.0.1:9/v1`.
- Production STT adoption remains outside NODE-014. NODE-015 closed the strategy; NODE-016 closed dialog-isolated diagnostics.

## NODE-015 Runtime Notes

- NODE-015 is a docs-only planning closeout, not a production STT implementation.
- Recommended first production STT candidate is server-side OpenAI Realtime transcription reached from the colocated `ari_app` through approved egress.
- If direct server egress is not operationally acceptable, use a controlled outbound proxy/gateway rather than routing through Windows/VPN.
- Keep batch Audio API STT as fallback/baseline while live STT is measured.
- Defer local/offline STT until actual server hardware and real telephony latency are benchmarked.
- RTP diagnostics should become fully dialog-isolated before live STT drives business dialog, so RTP-only tests do not call dummy batch STT or create misleading SAFE_FINISH outcomes.
- PHONE remains excluded from live STT adoption by default.
- PHONE_CONFIRM fast path remains unchanged.

## NODE-016 Runtime Notes

- NODE-016 completed dialog-isolated RTP/STT diagnostics.
- Enable isolation explicitly with:

```text
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

- In isolated diagnostics for `ISSUE`, `NAME`, and `CITY`, RTP diagnostics and STT measurement may run, but diagnostic STT failure does not feed `apply_turn`.
- Diagnostic failure must not increment business retries, trigger `SAFE_FINISH`, transfer, or callback.
- Expected diagnostic closeout events:
  - `stt_live_diagnostics_result`;
  - `stt_live_diagnostics_dialog_bypass`;
  - `diagnostic_call_finished`.
- Server smoke `1778668979.22` passed with:
  - `provider=rtp_diagnostics_only`;
  - `topology=snoop_external_media_rtp`;
  - `advertised_host=172.18.0.1`;
  - `stt_live_rtp_packets_received_count=429`;
  - `stt_live_pcm_chunks_created_count=429`;
  - `stt_live_rtp_diagnostics_result=rtp_packets_received`;
  - dummy batch STT `ConnectError` isolated from business dialog;
  - `diagnostic_call_finished status=ok`;
  - `dialog_stage_at_finish=ISSUE`;
  - `turns_done=0`.
- Normal production dialog behavior remains unchanged when isolation is unset.

## NODE-018 Runtime Notes

- Server `92.118.85.117` now runs the colocated ARI app through systemd:

```text
ai-secretary-ari.service
```

- Installed runtime paths:
  - `/etc/ai-secretary/ari-app.env`;
  - `/usr/local/bin/ai-secretary-ari-wrapper`;
  - `/etc/systemd/system/ai-secretary-ari.service`;
  - `/etc/systemd/system/ai-secretary-ari.service.d/local-publish-permissions.conf`.
- The installed env file must not contain real secrets.
- `ARI_PASSWORD` is read by the wrapper from:

```text
/home/tulauser/asterisk-config/ari.conf
```

- The reboot-safe diagnostic profile is:

```text
TELEPHONY_STT_BACKEND=openai
OPENAI_API_KEY=dummy
OPENAI_BASE_URL=http://127.0.0.1:9/v1
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
ASTERISK_PUBLISH_MODE=local
STT_LIVE_RTP_BIND_HOST=0.0.0.0
STT_LIVE_EXTERNAL_MEDIA_HOST=172.18.0.1
```

- The local publish root on the server is:

```text
/var/lib/docker/volumes/40c494a6543fbb493376133cfc53ef56471bdf18819aebfb20d4ffd9bfffeeb9/_data
```

- Because Docker restores `/var/lib/docker` permissions during boot, the server uses this drop-in:

```text
[Service]
ExecStartPre=+/usr/bin/chmod 0711 /var/lib/docker
```

- Final reboot evidence:
  - `ai-secretary-ari.service enabled`;
  - `ai-secretary-ari.service active`;
  - `ExecStartPre=/usr/bin/chmod 0711 /var/lib/docker status=0/SUCCESS`;
  - `ARI_LISTENING http://127.0.0.1:8088/ari ai_secretary`;
  - `ARI_WS_CONNECTED`;
  - `SYSTEM_SOUNDS_DONE ok`;
  - `READY_WAITING_FOR_CALLS`.
- Post-reboot smoke `1778672473.13` used:

```text
docker exec asterisk /usr/sbin/asterisk -rx 'channel originate Local/501@from-internal application Echo'
```

- Smoke evidence:
  - `stt_live_rtp_packets_received_count=228`;
  - `stt_live_pcm_chunks_created_count=228`;
  - `stt_live_rtp_diagnostics_result=rtp_packets_received`;
  - `stt_live_diagnostics_dialog_bypass status=handled`;
  - `diagnostic_call_finished status=ok`;
  - `dialog_stage_at_finish=ISSUE`;
  - `turns_done=0`;
  - no business `safe_finish`, `transfer`, or `callback` action.

## NODE-021 Runtime Notes

- NODE-021 adds a measurement-only supported-region gateway skeleton. It is not part of normal `ai-secretary-ari.service` startup.
- Gateway process entrypoint:

```text
python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8443
```

- Gateway endpoint:

```text
POST /v1/stt/realtime-measurement
Authorization: Bearer <gateway token>
Content-Type: audio/wav
```

- Gateway-only runtime secrets:

```text
OPENAI_API_KEY
GATEWAY_TOKEN
```

- Asterisk-side one-off measurement uses only:

```text
REALTIME_GATEWAY_URL
REALTIME_GATEWAY_TOKEN
```

- Do not add `OPENAI_API_KEY` to the Asterisk server for this gateway plan.
- The gateway returns structured flags and timings, including `chunks_sent`, `first_delta_ms`, `final_ms`, and `transcript_text_present`.
- Transcript text is not returned by default and should not be logged by default.
- No supported-region host was available during NODE-021; live deployment and result capture move to NODE-022.

## NODE-022 Runtime Notes

- NODE-022 did not reach a supported-region gateway because no gateway host, gateway URL, or gateway token was available.
- The prepared supported-region gateway deployment path is:

```text
/opt/ai-secretary-realtime-gateway
```

- Gateway-only secret env path:

```text
/etc/ai-secretary/openai-realtime-gateway.env
```

- Gateway-only secrets remain:

```text
OPENAI_API_KEY
GATEWAY_TOKEN
```

- Asterisk-side one-off measurement remains limited to:

```text
REALTIME_GATEWAY_URL
REALTIME_GATEWAY_TOKEN
```

- Before the one-off measurement, the Asterisk server shell should show:

```text
asterisk_server_openai_key_present=no
```

- Recorded blocked live-smoke result:

```text
gateway_reachable=false
gateway_auth=not_run
openai_realtime_from_gateway=not_run
chunks_sent=not_available
transcript_present=unknown
transcript_text_logged=false
error_type=supported_region_gateway_unavailable
error_redacted=true
business_dialog_changed=false
systemd_profile_changed=false
```

- The existing `ai-secretary-ari.service` profile remains unchanged:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

## NODE-023 Runtime Notes

- NODE-023 deployed the measurement-only gateway on Kamatera USA / New York 2:

```text
host=ai-secretary-gateway-node023
public_ip=45.61.48.199
deploy_path=/opt/ai-secretary-gateway
secret_env=/etc/ai-secretary/openai-realtime-gateway.env
protocol=HTTP for smoke
port=8080
```

- Gateway-only secrets remain:

```text
OPENAI_API_KEY
GATEWAY_TOKEN
```

- The Asterisk server one-off measurement used only:

```text
gateway_url=http://45.61.48.199:8080/v1/stt/realtime-measurement
gateway_token=<redacted>
```

- Recorded live-smoke result:

```text
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
chunks_sent=6
transcript_present=false
transcript_text_logged=false
error_type=none
error_status=none
```

- The Asterisk server had no `OPENAI_API_KEY` in the measurement shell.
- Business dialog was unchanged.
- `ai-secretary-ari.service` remained active and kept:

```text
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

- The manual gateway process was stopped after smoke:

```text
gateway_listener_stopped=yes
```

- No gateway systemd service was installed in NODE-023.
- Do not leave the gateway exposed over plain HTTP for production. A productionization node should add TLS, firewall allowlisting, systemd, and token rotation/runbook before persistent use.

## NODE-024 Runtime Notes

- NODE-024 is docs-only and changed no runtime behavior.
- Gateway-backed STT for business dialog remains disabled:

```text
production_gateway_stt_enabled=false
business_dialog_changed=false
systemd_profile_changed=false
live_server_changed=false
runtime_behavior_changed=false
```

- Future gateway-backed STT may connect only at the transcript-source boundary before `apply_turn(...)`.
- Required future defaults:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
```

- `OPENAI_API_KEY` must remain gateway-only.
- Asterisk-side gateway auth must use only secret runtime gateway URL/token config.
- Transcript text must not be logged by default.
- Gateway unavailable, auth failure, timeout, OpenAI success with absent transcript, and low-quality transcript must fall back to current deterministic prompt/retry behavior without weakening PHONE, PHONE_CONFIRM, CITY, transfer, callback, after-hours, SAFE_FINISH, or Russian-only caller-facing behavior.

## NODE-025 Runtime Notes

- NODE-025 implements the Asterisk-side gateway STT adapter but leaves it disabled by default.
- Production gateway STT remains disabled:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

- Optional adapter config:

```text
STT_GATEWAY_URL=
STT_GATEWAY_TOKEN=
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_MAX_RETRIES=0
STT_GATEWAY_LANGUAGE=ru
STT_GATEWAY_MIN_CONFIDENCE=
```

- Compatibility aliases remain available:

```text
REALTIME_GATEWAY_URL
REALTIME_GATEWAY_TOKEN
```

- The adapter does not require or read `OPENAI_API_KEY` on the Asterisk side.
- If the adapter is disabled, no gateway network call is attempted.
- If enabled but config is missing, auth fails, the gateway times out, is unavailable, returns malformed JSON, returns empty transcript, or returns low-quality transcript, the call falls back to the current batch/deterministic path.
- Transcript text is not logged by default in gateway adapter events or details.
- NODE-025 did not modify live servers, did not start the Kamatera gateway, did not change `ai-secretary-ari.service`, and did not change the Asterisk runtime environment.

## NODE-026 Runtime Notes

- NODE-026 adds local dry-run validation only; it changes no production runtime behavior.
- Production gateway STT remains disabled by default:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

- The dry-run method is:

```text
pytest fake/mocked gateway plus localhost-only fake HTTP gateway
```

- The fake HTTP gateway binds only to `127.0.0.1` on an ephemeral port and uses a fake bearer token.
- The local dry-run confirms that `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` prevents gateway network use and falls back to batch at the ARI boundary.
- The local dry-run confirms that explicit fake transcript use can drive the transcript-source boundary only when both gateway and dialog-use flags are enabled in local test config.
- Transcript text is not logged by default in adapter or ARI events.
- `OPENAI_API_KEY` is not required for local dry-run validation.
- No real gateway token is required for local dry-run validation.
- NODE-026 did not modify live servers, did not SSH into Kamatera or Asterisk, did not start the Kamatera gateway, did not run live calls, did not change `ai-secretary-ari.service`, and did not change the Asterisk runtime environment.

## NODE-027 Runtime Notes

- NODE-027 adds a manual one-off smoke helper:

```text
python -m ai_secretary.stt.gateway_adapter_smoke --audio <wav> --require-explicit-flags
```

- Controlled helper flags must be temporary process env only:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_ADAPTER_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
STT_GATEWAY_URL=http://45.61.48.199:8080/v1/stt/realtime-measurement
STT_GATEWAY_TOKEN=<redacted runtime secret>
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_MAX_RETRIES=0
STT_GATEWAY_LOG_TRANSCRIPT=false
STT_GATEWAY_LANGUAGE=ru
OPENAI_API_KEY=<absent on Asterisk>
```

- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` is required only because the current adapter does not make a gateway request unless dialog-use is explicitly enabled. For NODE-027 it is intended for a one-off CLI process only, not for `ai-secretary-ari.service`.
- The helper emits redacted JSON metadata and must not print transcript text or secrets by default.
- NODE-027 live smoke was blocked before adapter execution:

```text
kamatera_gateway_ssh=false
gateway_ssh_blocker=connection_refused_on_45.61.48.199_port_22
gateway_started=false
gateway_reachable_from_asterisk=false
adapter_smoke_exercised_node025_path=false
openai_realtime_from_gateway=not_run
gateway_auth=not_run
```

- Asterisk verification during the blocked attempt:

```text
ai-secretary-ari.service=active
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

- No gateway process was started, no gateway port was left listening by this node, no live call ran, no service restart occurred, no env file was edited, and no Asterisk runtime env change was persisted.
- Production gateway STT remains disabled by default:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## NODE-028 Runtime Notes

- NODE-028 completed the controlled live adapter smoke through the NODE-025 adapter path.
- The Kamatera gateway was started temporarily on `0.0.0.0:8080` and reached from the Asterisk server.
- The NODE-027 helper was run from the Asterisk server using a temporary source overlay because the protected deployment source did not contain the adapter/helper files.
- Gateway auth worked.
- OpenAI Realtime from the gateway worked.
- The helper sent a silent 24 kHz mono WAV and reported `chunks_sent=15`.
- The gateway returned HTTP `200` with `openai_realtime_connection_ok=true` and `openai_session_created=true`.
- The silent WAV produced no transcript, so the adapter fell back with `fallback_reason=empty_transcript`.
- Transcript text was not logged and no transcript was used for dialog.
- Temporary Asterisk token/source/audio files were removed after the smoke.
- The gateway process was stopped after the smoke and port `8080` was no longer listening.
- Asterisk remained on the safe diagnostic profile:

```text
ai-secretary-ari.service=active
STT_LIVE_OPENAI_DISABLED=true
STT_LIVE_STREAMING_PROVIDER=rtp_diagnostics_only
STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true
OPENAI_API_KEY=<absent>
```

- Production gateway STT remains disabled by default:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## NODE-029 Runtime Notes

- NODE-029 was local-only and did not start the Kamatera gateway.
- NODE-029 did not modify `ai-secretary-ari.service`, `/etc/ai-secretary/ari-app.env`, Asterisk runtime env, or business dialog behavior.
- The likely root cause of the NODE-028 `empty_transcript` result is the documented synthetic silent WAV, not gateway auth or transport:

```text
NODE-028 audio=24 kHz mono 16-bit PCM, 3 seconds, silent
chunks_sent=15
transcript_present=false
fallback_reason=empty_transcript
audio_quality_classification=near_silent inferred by NODE-029 classifier
```

- Future gateway responses include audio payload diagnostics:

```text
audio_duration_ms
audio_sample_rate_hz
audio_channels
audio_sample_width
audio_codec
audio_total_bytes
audio_chunk_count
audio_chunk_bytes_min/max/avg
audio_first_chunk_bytes
audio_last_chunk_bytes
audio_rms
audio_peak
audio_non_silent_ratio
audio_quality_classification
```

- Future gateway responses include redacted Realtime response diagnostics:

```text
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
error_event_seen
input_audio_buffer_commit_sent
timeout_observed
close_status
```

- Transcript text remains suppressed by default.
- Production gateway STT remains disabled by default:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## NODE-030 Runtime Notes

- NODE-030 completed exactly one controlled live adapter smoke with non-sensitive Russian speech audio.
- The speech source was an existing generated system prompt WAV, converted only as a temporary 24 kHz mono 16-bit PCM file for the smoke:

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
```

- The one-off helper used explicit temporary env only:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_ADAPTER_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_URL=http://45.61.48.199:8080/v1/stt/realtime-measurement
STT_GATEWAY_TOKEN=<redacted runtime secret>
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_MAX_RETRIES=0
STT_GATEWAY_LOG_TRANSCRIPT=false
STT_GATEWAY_LANGUAGE=ru
OPENAI_API_KEY=<absent on Asterisk>
```

- Live smoke result:

```text
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

- OpenAI event diagnostics:

```text
session.created=1
session.updated=1
input_audio_buffer.committed=1
conversation.item.input_audio_transcription.delta=22
conversation.item.input_audio_transcription.completed=1
conversation.item.added=1
conversation.item.done=1
```

- NODE-030 confirms the NODE-028 empty transcript was caused by silent/non-speech audio, not gateway auth, OpenAI transport, or response parsing.
- The temporary gateway process was stopped after the smoke and port `8080` was no longer listening.
- Temporary Asterisk token/source/audio files were removed after the smoke.
- `ai-secretary-ari.service` remained active in the safe diagnostic profile.
- Asterisk process env still had no `OPENAI_API_KEY`.
- Production gateway STT remains disabled by default:

```text
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

## NODE-031A Runtime Notes

- NODE-031A is docs-only.
- No source/runtime code was changed.
- No server SSH was performed.
- No Asterisk restart was performed.
- No gateway was started or stopped.
- No deploy was performed.
- No env file was changed.
- No live smoke was run.
- No Notion write was performed.
- No Runtime or Evidence record was created.
- No GitHub write was performed.
- No scheduler, webhook, or automation mode was added.
- No secrets or real tokens were intentionally logged or committed.
- `data/storage/` and `node014-server.tar` remain historical untracked artifacts and must not be staged, committed, deleted, or cleaned by this node.

## NODE-031 Runtime Notes

- NODE-031 is docs/templates-only and changes no production runtime behavior.
- Safe placeholder templates live under `deploy/templates/`:
  - `gateway.env.example`;
  - `gateway-systemd.service.example`;
  - `gateway-nginx-proxy.example`.
- Production gateway runtime boundary:
  - gateway service ownership belongs to infra/ops;
  - systemd or equivalent supervision is required before persistent production use;
  - the app should bind on loopback or private IP, with public exposure only through TLS reverse proxy;
  - firewall policy must default-deny and allow only Asterisk, operator, and monitoring source CIDRs;
  - env files must be owned by root/service account and readable only by the service boundary;
  - logs must redact transcript text by default.
- Secret boundary:
  - `OPENAI_API_KEY` lives on the gateway only, not in the Asterisk safe profile;
  - `GATEWAY_TOKEN` lives only in secure server env/vault material;
  - repository templates use placeholders only;
  - exposed tokens require immediate revocation, rotation, log review, and incident response.
- Dialog/STT boundary:
  - gateway STT remains disabled by default;
  - business dialog must not use gateway transcript unless a later explicit node enables it;
  - measurement helper and business dialog paths remain distinct.
- NODE-032 must be the first live apply/smoke node and must require explicit operator approval.
- No server action, Notion write, Runtime/Evidence create, GitHub write, live smoke, or scheduler/webhook/automation mode was performed by NODE-031.

## NODE-032 Phase A Runtime Notes

- NODE-032 Phase A changes no runtime behavior.
- Phase A does not SSH to live servers, does not apply systemd or firewall changes, does not start/stop/restart/reload services, and does not run live smoke.
- Phase A records the exact approval gate:

```text
APPROVE NODE-032 LIVE APPLY/SMOKE
```

- Planned Phase B smoke remains non-business-dialog:
  - `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`;
  - `STT_GATEWAY_LOG_TRANSCRIPT=false`;
  - transcript text must not be logged;
  - Asterisk must have no `OPENAI_API_KEY`.
- Phase B must verify gateway reachability, gateway auth, OpenAI Realtime from gateway, `transcript_text_logged=false`, `transcript_used_for_dialog=false`, unchanged business dialog, and no Asterisk-side `OPENAI_API_KEY`.

## NODE-032B Phase A Runtime Notes

- NODE-032B Phase A changes no runtime behavior.
- Phase A does not SSH to live servers, does not apply systemd or firewall changes, does not start/stop/restart/reload services, does not reload proxy config, and does not run live smoke.
- Phase A records the exact approval gate:

```text
APPROVE NODE-032B LIVE APPLY/SMOKE
```

- No other phrase is approval.
- Planned Phase B smoke remains non-business-dialog:
  - `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`;
  - `STT_GATEWAY_LOG_TRANSCRIPT=false`;
  - transcript text must not be logged;
  - Asterisk must have no `OPENAI_API_KEY`.
- Phase B must verify gateway reachability, gateway auth, OpenAI Realtime from gateway, `transcript_text_logged=false`, `transcript_used_for_dialog=false`, unchanged business dialog, no Asterisk-side `OPENAI_API_KEY`, and cleanup or persistent service state decision.
- If access, secrets, templates, current server state, redaction, or rollback readiness is unsafe, NODE-032B must remain blocked before live apply.

## NODE-032C Runtime Notes

- NODE-032C performed read-only live readiness inspection.
- Asterisk host `92.118.85.117`:
  - SSH reachable;
  - hostname `localhost`;
  - uptime observed as `up 8 minutes`;
  - `ai-secretary-ari.service` active and enabled;
  - `/etc/ai-secretary/ari-app.env` metadata `root:tulauser 0640`;
  - `OPENAI_API_KEY_ABSENT` from service process env;
  - recent sanitized journal showed system sounds published and `READY_WAITING_FOR_CALLS`.
- Gateway host `45.61.48.199`:
  - SSH reachable;
  - hostname `ai-secretary-gateway-node023`;
  - uptime observed as `up 8 minutes`;
  - `ai-secretary-gateway.service` inactive/not found;
  - gateway process not running;
  - `/etc/ai-secretary/gateway.env` absent;
  - `/etc/ai-secretary/openai-realtime-gateway.env` present as `root:root 0600`;
  - masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` key presence verified without values;
  - no `443`, `8080`, or `8081` gateway target ports listening;
  - UFW active with default deny incoming and old `8080/tcp` allow from `92.118.85.117`.
- NODE-032C recommendation: NO-GO for immediate NODE-032D live apply/smoke until env path, service unit, TLS/proxy, firewall transition, and rollback plan are explicitly resolved.
- No live apply, service start/stop/restart/reload, live smoke, live call, business dialog enablement, Notion write, Runtime/Evidence create, GitHub write, scheduler, webhook, or automation mode was performed.

## NODE-010 Runtime Notes

- Bounded local callback persistence is implemented.
- Persistence format is JSONL, one flat JSON object per line.
- Production path:

```text
data/storage/callbacks/callback_records.jsonl
```

- Persisted schema includes:
  - `record_id`;
  - `call_id`;
  - `timestamp`;
  - `department`;
  - `issue`;
  - `name`;
  - `city`;
  - `phone`;
  - `outcome_type`;
  - `outcome_reason`.
- Implemented trigger points:
  - `after_hours_callback`;
  - `safe_finish`.
- After-hours callback records are persisted after after-hours transfer skip and before final hangup.
- SAFE_FINISH records are persisted with available partial data and terminal reason.
- Persistence is fail-soft and does not crash call flow.
- Logging includes:
  - `persistence_attempt`;
  - `persistence_success`;
  - `persistence_failure`.
- Live validation confirmed callback persistence succeeded with:

```text
outcome_type=after_hours_callback
outcome_reason=mode_override
record_id=f0cff987b252b77c
path=data/storage/callbacks/callback_records.jsonl
```

## NODE-011 Runtime Notes

- Stage-level latency instrumentation is implemented for the normal ARI call loop.
- Latency events cover ASR, dialog decision, TTS, publish, playback start/finish, stage completion, and silence-risk detection.
- `latency_silence_risk` uses warning and critical thresholds to identify dead-air risk by `call_id` and stage.
- Normal PHONE_CONFIRM uses the static fast path when `phone_digits` are available:
  - static prefix;
  - static digit sounds;
  - static suffix.
- Normal PHONE_CONFIRM fast path logs `phone_confirm_fast_path_used` and avoids per-call dynamic TTS/publish with:

```text
dynamic_tts_required=false
publish_required=false
```

- PHONE remains excluded from TALK_DETECT early stop with `phone_digit_safety_skip`.
- ISSUE and INTENT_CLARIFY wait for prompt playback completion plus guard before recording begins.
- TALK_DETECT diagnostics are present for enablement, event order anomalies, missing finished events, and timeout recovery attempts.
- Final live smoke `1778089554.24` validated the MVP normal working-hours sales flow:
  - ISSUE captured: `Я бы хотел купить сетку Манье.`
  - intent matched sales by keyword `купить`;
  - name captured: `Антон Вячеславович`;
  - city captured: `Самара`;
  - phone normalized: `9600614112`;
  - confirmation captured: `Да, верно`;
  - transfer to `sales_real` completed with `status=ok` after `phone_confirmed=true`.
- Known limitation for follow-up: NAME, CITY, and PHONE_CONFIRM can still have noticeable recording-window pauses; short-slot smoothing belongs to NODE-012.

## NODE-005 Runtime Notes

- NODE-005 keeps the current turn-based architecture and the NODE-004 post-PHONE transfer flow.
- Real-call recording is now stage-specific:

```text
ISSUE: max_duration=8s, max_silence=2s, wait_timeout=13s
NAME:  max_duration=6s, max_silence=2s, wait_timeout=11s
CITY:  max_duration=7s, max_silence=3s, wait_timeout=13s
PHONE: max_duration=14s, max_silence=4s, wait_timeout=21s
PHONE_CONFIRM: max_duration=6s, max_silence=3s, wait_timeout=12s
```

- Runtime events now include timing for prompt playback, record, download, STT, dialog decision, transfer phrase, and ARI continue transfer.
- `scripts/latency_report.py` now prints turn-based buckets: `prompt`, `record`, `download`, `stt`, `decision`, `transfer_phrase`, and `transfer`, while preserving the existing generic pipeline buckets.
- Operator overrides are available globally, by slot stages, or by exact stage. Stage-specific variables take precedence, for example `RECORD_PHONE_MAX_SILENCE_SECONDS`.
- No partial STT, streaming STT, realtime agent, or barge-in behavior was added in this node.
- NODE-005 patch 2 adds explicit confirmation only for PHONE. CITY re-asks on low-confidence input but has no confirmation substage.
- PHONE capture stores a digits-only value stripped from caller formatting, then asks `Правильно ли я записала ваш номер: <formatted_phone>?`.
- Transfer is allowed only after positive PHONE confirmation. Rejection or re-dictation returns to PHONE capture / replacement confirmation.
- If PHONE remains unconfirmed, runtime exits through `phone_unconfirmed_no_generic_pipeline` and must not run `pipeline_start`, `build_response`, `publish`, or generic `playback`.
- NODE-005 patch 3 relaxes CITY and PHONE turn-taking after live smoke showed cutoff regressions. CITY now requires at least 4 letters before advancing; PHONE requires a complete 10- or 11-digit run before `PHONE_CONFIRM`.
- PHONE now has the longest non-ISSUE end-of-speech profile to tolerate slow dictation and short intra-utterance pauses.
- Poor TTS stress/pronunciation on the phone prompt was observed during live smoke and recorded as secondary; do not mix it into the NODE-005 acceptance gate unless prompt wording changes.
- NODE-005 patch 4 varies only PHONE retry prompts. Reasons are `unclear`, `incomplete`, and `rejected`; the same PHONE retry phrase should not repeat twice in a row.
- NODE-005 patch 5 keeps `phone_formatted` for debug/display but feeds PHONE_CONFIRM TTS with `phone_spoken`, a Russian digit-by-digit string, to avoid TTS skipping symbolic formatting such as `+7 920 032-03-55`.
- NODE-005 patch 6 adds an explicit `PlaybackFinished` barrier before PHONE_CONFIRM recording, then a default `400 ms` guard delay. `PHONE_CONFIRM_PLAYBACK_TIMEOUT_SECONDS` defaults to `15`.
- NODE-005 patch 6 expands PHONE_CONFIRM capture to `6s/3s/12s`, handles meta-repair phrases neutrally, adds a NAME garbage guard, and forces the fixed PHONE system prompt to `prompt_4_v2` with built-in stress preprocessing for `связи -> св+язи`.
- NODE-005 patch 7 fixes NAME retry-loop regression. NAME retries are reason-based (`unclear`, `junk`, `meta_repair`), varied without immediate repetition, tolerant of short valid Russian names, and capped at 3 retries before advancing with `name="клиент"` and `name_unavailable=true`.
- NODE-005 patch 8 fixes PHONE-stage acceptance/repair. Comma/dot grouped STT such as `920, 0.32, 0.3, 0.55` normalizes to `9200320355`, PHONE-stage meta-repair uses `meta_repair`, dynamic PHONE retry prompts are synthesized/published per call instead of replaying `prompt_4_v2`, and NAME now rejects short English filler such as `Yep.`.
- NODE-005 patch 9 adds a NAME playback barrier for both base NAME prompt and dynamic NAME retry prompts. NAME recording starts only after `PlaybackFinished` plus `NAME_GUARD_DELAY_MS`, default `400 ms`; NAME timing is now `6s/2s/11s`.

## NODE-032D Runtime Notes

- NODE-032D is docs-only and performs no runtime action.
- First future live smoke uses the historical gateway env path:

```text
/etc/ai-secretary/openai-realtime-gateway.env
```

- First future live smoke should not migrate secrets to `/etc/ai-secretary/gateway.env` and should not create a compatibility symlink.
- Future NODE-032E may install/adapt:

```text
service=ai-secretary-gateway.service
unit=/etc/systemd/system/ai-secretary-gateway.service
runtime_user_group=gateway:gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
first_smoke_port=8080
```

- First future live smoke should avoid public TLS/proxy exposure: do not expose `443`, do not open `8081`, and do not reload a proxy.
- Use the existing Asterisk-only `8080/tcp` firewall path only if NODE-032E re-confirms it is restricted to `92.118.85.117`.
- Keep business dialog transcript use disabled with `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- Keep transcript text logging disabled.
- The Asterisk safe profile must continue to have no `OPENAI_API_KEY`.
- Conservative cleanup default after first smoke: stop/rollback gateway service unless NODE-032E explicitly records a persistent service decision.
- Future NODE-032E exact approval phrase:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

- No other phrase is approval.

## NODE-032E Phase A Runtime Notes

- NODE-032E Phase A ran read-only live gate re-confirmation only.
- Asterisk gate:
  - SSH reachable;
  - `ai-secretary-ari.service` active/enabled;
  - `OPENAI_API_KEY` absent from service process env;
  - business dialog unchanged.
- Gateway gate:
  - SSH reachable;
  - historical env file `/etc/ai-secretary/openai-realtime-gateway.env` present as `root:root 600`;
  - masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence verified without values;
  - `/etc/ai-secretary/gateway.env` remains not required for first smoke;
  - `ai-secretary-gateway.service` inactive/absent/not enabled;
  - no target listener on `443`, `8080`, or `8081`.
- Firewall gate:

```text
ufw_status=active
default_incoming=deny
8080/tcp=ALLOW from 92.118.85.117
```

- Phase B remains NO-GO until a later exact approval phrase is provided:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

- Phase B must re-confirm all gates immediately before apply and stop if any gate changes.
