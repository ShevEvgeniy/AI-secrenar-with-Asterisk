# Master Plan

## Project Baseline

- Repository root: `C:\Projects\AI-secrenar-with-Asterisk`
- Source-of-truth branch: `master`
- Source-of-truth commit: `990dc59`
- Source-of-truth commit message: `Merge pull request #11 from ShevEvgeniy/feat/node-032i-controlled-persistent-gateway-service-install-start-smoke`
- Workflow model: master-driven coordination with focused node branches for implementation.

## Confirmed Capabilities

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are present in `master`.
- Transfer flow through ARI continue is present in `master`.
- Tracing and logging are required to be preserved across all node work.

## Completed Practical Gaps

NODE-001 completed and live-validated the real transfer route through the dialplan:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

NODE-002 completed and validated publish hardening:

```text
partial publish failure -> classified failure -> resilient startup and diagnosable per-call behavior
```

NODE-003 completed and validated transcription integrity plus meaningful fallback phrases:

```text
real downloaded caller audio artifact -> traceable transcription metadata -> no fabricated user_transcribed text
```

NODE-004 completed and validated post-PHONE transfer flow restoration:

```text
successful PHONE capture -> play_transfer_phrase -> transfer status=ok
```

NODE-005 completed and validated latency plus turn-based hardening:

```text
ISSUE -> NAME -> CITY -> PHONE -> PHONE_CONFIRM -> DONE -> play_transfer_phrase -> transfer
```

NODE-006 completed and validated NAME capture and normalization hardening:

```text
NAME -> language=ru and Russian-name STT prompt -> bounded normalization -> stable flow continues
```

NODE-007 completed and validated bounded department intent routing:

```text
topic intent -> sales/accounting/delivery/default -> department-specific phrase -> explicit transfer target
```

NODE-008 completed and validated mandatory data capture plus bounded intent clarification:

```text
immediate transfer request -> required data capture -> bounded clarification/default -> transfer or SAFE_FINISH
```

NODE-009 completed and validated business-hours and after-hours handoff:

```text
working hours -> live transfer; after hours -> collect required data -> department callback phrase -> hangup without transfer
```

NODE-010 completed and validated callback capture and persistence:

```text
after_hours_callback/safe_finish -> flat JSONL callback record -> fail-soft persistence logging
```

NODE-011 completed and validated normal-call latency and silence hardening at MVP level:

```text
latency instrumentation -> static PHONE_CONFIRM fast path -> ISSUE/INTENT capture barriers -> sales transfer preserved
```

NODE-012 completed and validated short-slot turn-taking polish:

```text
Russian-only dialog -> safe CITY validation -> static CITY retry -> SAFE_FINISH playback barrier -> compound CITY/address accepted
```

NODE-013 completed and validated a feature-flagged Realtime Whisper adapter/metrics spike:

```text
stored WAV artifact -> realtime STT adapter metrics -> fallback to batch whisper path
```

NODE-014 completed and validated the true-live ARI media-path proof:

```text
server-side ari_app -> ARI Stasis(ai_secretary) -> snoop_external_media_rtp -> RTP/PCM received on 172.18.0.1
```

NODE-015 completed the production server-side STT strategy:

```text
colocated ari_app -> approved server egress to OpenAI Realtime transcription -> batch fallback/baseline -> local STT deferred until benchmark
```

NODE-016 completed and validated dialog-isolated RTP/STT diagnostics:

```text
rtp_diagnostics_only -> snoop_external_media_rtp -> RTP/PCM measured -> dummy STT failure isolated from business dialog
```

NODE-017 completed systemd/autostart templates for the server-side `ari_app`, and NODE-018 applied them on the actual server with reboot-safe validation:

```text
systemd ai-secretary-ari -> runtime ARI password from ari.conf -> local publish -> reboot -> RTP diagnostics smoke passed
```

NODE-019 prepared direct OpenAI Realtime egress/STT measurement and proved direct egress from the current Asterisk server is not viable:

```text
api.openai.com/v1/realtime -> 403 unsupported_country_region_territory -> chunks_sent=0
```

NODE-020 defines the supported-region gateway/proxy measurement path:

```text
Asterisk server -> short WAV/PCM measurement upload -> supported-region gateway -> OpenAI Realtime -> redacted metrics/result flags
```

NODE-021 implements the minimal prepared gateway measurement path:

```text
Asterisk one-off client without OPENAI_API_KEY -> authenticated raw WAV upload -> gateway-owned OPENAI_API_KEY -> OpenAI Realtime -> redacted structured JSON
```

NODE-022 records the supported-region gateway deployment/runbook and blocked live-smoke result:

```text
No supported-region host available -> no gateway request made -> no fabricated success -> exact deployment and one-off run commands ready
```

NODE-023 deploys the gateway on Kamatera USA / New York 2 and runs the live one-off measurement:

```text
Asterisk server -> Kamatera HTTP gateway on 45.61.48.199:8080 -> OpenAI Realtime -> 200 OK, chunks_sent=6, transcript_text_logged=false
```

NODE-024 defines the production integration boundary for future gateway-backed STT in business dialog:

```text
gateway STT adapter -> transcript candidate -> quality/redaction/fallback gates -> existing apply_turn(...)
```

The boundary is design-only. Gateway STT remains disabled by default and production dialog remains unchanged.

NODE-025 implements the controlled disabled-by-default gateway STT adapter:

```text
downloaded WAV artifact -> Asterisk-side gateway adapter -> supported-region gateway URL/token -> redacted transcript candidate -> existing apply_turn(...)
```

The adapter remains disabled by default, dialog transcript use remains separately disabled by default, and production behavior remains unchanged.

NODE-026 validates the controlled adapter locally without live infrastructure:

```text
downloaded WAV artifact -> local fake/mocked gateway dry-run -> redacted transcript candidate/fallback -> ARI transcript-source boundary
```

The dry-run uses pytest mocks and a localhost fake HTTP gateway with fake secrets only. Production gateway STT remains disabled by default and production behavior remains unchanged.

NODE-027 adds a manual one-off smoke helper for the controlled adapter path, but the live Kamatera adapter smoke is blocked:

```text
one-off WAV artifact -> NODE-025 gateway adapter smoke helper -> Kamatera gateway URL/token -> redacted result
```

The live run did not occur because SSH to the Kamatera gateway host refused connections and the gateway listener was not reachable on port 8080 from Asterisk. No service, persistent env, live call, business dialog, or default config change was made.

NODE-028 restored the Kamatera path and completed the controlled live adapter smoke retry:

```text
Asterisk server -> NODE-025 adapter via NODE-027 helper -> Kamatera gateway -> OpenAI Realtime -> 200 OK, chunks_sent=15, transcript_text_logged=false
```

The gateway was started temporarily, reached from Asterisk, authenticated successfully, and stopped after the smoke. The synthetic silent WAV produced `empty_transcript`, so no transcript drove dialog. Asterisk service/env stayed unchanged and gateway STT remains disabled by default.

NODE-029 diagnoses the NODE-028 empty-transcript result and adds payload/event diagnostics:

```text
silent synthetic WAV -> audio_quality_classification=near_silent -> empty_transcript likely caused by unsuitable audio content
```

The diagnostic was local-only. Gateway responses now expose redacted audio quality metrics and Realtime event-type counts for future runs. No live diagnostic was run and production gateway STT remains disabled by default.

NODE-030 completes the controlled speech WAV gateway adapter smoke:

```text
existing safe Russian system prompt WAV -> temporary 24 kHz mono PCM -> NODE-025 adapter smoke helper -> Kamatera gateway -> OpenAI Realtime -> transcript-bearing events observed
```

The speech payload was classified as `valid_speech_candidate`, gateway auth and OpenAI Realtime worked, `chunks_sent=24`, transcript events were observed, and `transcript_present=true`. Transcript text was not logged, transcript use for dialog stayed disabled, the business dialog was unchanged, the gateway was stopped after the smoke, and Asterisk still had no `OPENAI_API_KEY`.

NODE-031A creates the docs-only bootstrap and PR workflow boundary:

```text
new GPT chat bootstrap -> scoped node handoff -> feature branch -> PR -> Control Plane supervised closeout/evidence where applicable
```

This is documentation-only and does not implement `NODE-031 / productionize-gateway-runtime-boundary`.

NODE-031 defines the production gateway runtime boundary:

```text
docs/templates only -> service/systemd/firewall/TLS/env/redaction boundaries -> NODE-032 live-smoke prerequisites
```

This is not a live deployment. It adds safe placeholder templates and records rollback, cleanup, token rotation, and explicit operator-approval gates for the next live node.

NODE-032 Phase A prepares the first controlled production gateway live-smoke plan:

```text
preflight and command plan only -> no live apply -> exact approval gate -> rollback/cleanup plan
```

NODE-032B Phase A refines the readiness/preflight plan for the controlled production gateway live apply/smoke:

```text
NODE-031 templates + NODE-032 Phase A plan -> NODE-032B approval gate -> Phase B live apply/smoke command plan
```

NODE-032B Phase A is docs-only. It performs no live apply, no service start/stop/restart/reload, no server state change, and no live smoke.

NODE-032C performs read-only live readiness inspection:

```text
Asterisk read-only checks + gateway read-only checks -> masked env verification -> NO-GO until env path/service/proxy/firewall decisions are explicit
```

NODE-032C does not perform live apply, does not start/stop/restart/reload services, does not run live smoke, and does not enable business dialog transcript use.

NODE-032G completes the controlled Asterisk-side gateway live smoke:

```text
Asterisk helper -> Gateway 45.61.48.199:8080 -> OpenAI Realtime -> chunks_sent=28, transcript_present=true, transcript_text_logged=false
```

NODE-032G removed temporary service/helper/env/audio state after the smoke. No persistent gateway service remained.

NODE-032H decides staged production gateway persistence:

```text
successful smoke -> staged persistence strategy -> install/start/smoke before enable/reboot proof -> business dialog integration deferred
```

NODE-032H is docs-only and performs no live apply or server state change.

NODE-032I Phase A prepares the controlled persistent gateway service install/start/smoke plan:

```text
staged persistence plan -> exact approval gate -> install/start/smoke command set -> no enable/reboot/power-cycle
```

NODE-032I Phase A is planning/read-only only. Initial SSH reachability timed out while servers were likely powering on; rerun read-only gates passed and Phase B is conditionally GO only after exact approval plus immediate gate re-confirmation.

NODE-032I Phase B completes the controlled persistent gateway service install/start/smoke:

```text
locked gateway:gateway + root:gateway 640 env + installed disabled unit -> start -> Asterisk helper smoke -> stop service, keep unit installed disabled
```

NODE-032I does not enable the service, reboot, power-cycle, expose `443`, open `8081`, broaden firewall, or integrate the business dialog.

NODE-032J decides the enable/autostart policy for the staged gateway service:

```text
installed disabled staged artifact -> no immediate enablement -> next live node must separately approve enable/reboot/smoke
```

NODE-032J is docs-only. It keeps the staged service installed but disabled for now, rejects immediate `systemctl enable`, keeps business dialog integration out of scope, and defines NODE-032K as the controlled enablement/reboot-smoke node.

## Execution Model

- `master` remains the source-of-truth branch.
- Architecture, status, planning, and project coordination are maintained in `docs/master/`.
- Implementation work is performed through focused node branches.
- One node equals one task, one branch, and one execution cycle.
- Avoid broad refactors.
- Do not mix multiple concerns in one node.
- Preserve tracing and logging.

## Current Action Plan

1. Treat NODE-001 through NODE-023 as complete and recorded in `master`.
2. Preserve the validated sales transfer target:

```text
context=from-internal
extension=sales_real
priority=1
```

3. Preserve the validated sales dialplan route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

4. Preserve NODE-002 publish failure classification with `reason` and `failed_step`.
5. Preserve NODE-003 transcription artifact traceability through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
6. Preserve NODE-004 post-PHONE transfer behavior so the generic reply pipeline is not taken after successful PHONE capture.
7. Preserve NODE-005 turn-taking contour, NAME playback barrier, PHONE_CONFIRM behavior, and spoken-digit confirmation prompt.
8. Preserve NODE-006 Russian NAME STT context, bounded NAME normalization, simplified NAME prompt, and overall call architecture.
9. Preserve NODE-007 bounded department routing for sales, accounting, delivery, and configured default fallback.
10. Preserve department-specific final transfer phrases.
11. Preserve NODE-008 mandatory data gate before live transfer: `name`, `city`, `phone`, and `phone_confirmed=true`.
12. Preserve bounded `INTENT_CLARIFY`, stage-local retry policy, and terminal/non-transfer `SAFE_FINISH`.
13. Preserve NODE-009 working-hours live transfer behavior and after-hours transfer skip.
14. Preserve department-specific after-hours phrases and the playback barrier before hangup.
15. Preserve NODE-010 callback persistence at `data/storage/callbacks/callback_records.jsonl`.
16. Preserve fail-soft persistence logging for `persistence_attempt`, `persistence_success`, and `persistence_failure`.
17. Preserve NODE-011 stage-level latency instrumentation and `latency_silence_risk` diagnostics.
18. Preserve NODE-011 static PHONE_CONFIRM fast path when `phone_digits` are available.
19. Preserve NODE-011 PHONE early-stop exclusion with `phone_digit_safety_skip`.
20. Preserve NODE-011 ISSUE and INTENT_CLARIFY prompt playback barriers before recording.
21. Preserve NODE-012 CITY transcript validation, including compound region/city/address handling.
22. Preserve NODE-012 Russian-only caller-facing invariant and static CITY retry prompt.
23. Preserve NODE-012 SAFE_FINISH playback barrier before hangup.
24. Preserve NODE-013 feature flag, fallback behavior, and STT stream latency/event metrics.
25. Treat NODE-013 as adapter/metrics spike only, not production adoption.
26. Preserve NODE-014 local sound publish mode for colocated/server-side launch.
27. Preserve NODE-014 `snoop_external_media_rtp` diagnostics path and RTP/PCM metrics.
28. Treat NODE-014 as media-path proof only, not production STT adoption.
29. Treat NODE-015 as planning closeout only, not production STT implementation.
30. Preserve NODE-015 decision that RTP diagnostics should be dialog-isolated before live STT drives the business dialog.
31. Preserve NODE-016 `STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED=true` behavior so RTP/STT diagnostics do not advance business dialog, increment retries, trigger SAFE_FINISH, transfer, or callback.
32. Preserve NODE-016 smoke result: server call `1778668979.22` received `429` RTP packets and `429` PCM chunks and ended with `diagnostic_call_finished status=ok`.
33. Preserve NODE-018 server autostart: `ai-secretary-ari.service` is enabled and active after reboot, reads `ARI_PASSWORD` from `ari.conf`, and reaches `ARI_WS_CONNECTED` plus `READY_WAITING_FOR_CALLS` without manual exports.
34. Preserve NODE-018 local publish permissions for the colocated service, including the server-side systemd drop-in that runs `ExecStartPre=+/usr/bin/chmod 0711 /var/lib/docker` before starting as `tulauser`.
35. Preserve NODE-018 smoke result: server call `1778672473.13` received `228` RTP packets and `228` PCM chunks and ended with `diagnostic_call_finished status=ok`.
36. Preserve NODE-019 direct OpenAI Realtime result: direct server egress reached OpenAI but failed with `403 Forbidden`, `unsupported_country_region_territory`, before audio upload.
37. Preserve NODE-020 gateway boundary: `OPENAI_API_KEY` lives on the supported-region gateway, not on the Asterisk server.
38. Preserve NODE-020 first-proof scope: one-shot short WAV/PCM measurement with redacted metrics, no transcript text by default, and no business dialog integration.
39. Preserve NODE-021 gateway/client boundary: the Asterisk-side measurement mode uses gateway URL/token only and does not require or read `OPENAI_API_KEY`.
40. Preserve NODE-021 prepared-only result as superseded by the NODE-023 live supported-region measurement.
41. Preserve NODE-022 blocked-smoke result: no supported-region host, gateway URL, or gateway token was available, so gateway reachability, gateway auth, and OpenAI Realtime from gateway remain `not_run`.
42. Preserve NODE-022 runtime boundary: no OpenAI key on the Asterisk server, no business dialog integration, and no `ai-secretary-ari.service` diagnostic profile change.
43. Preserve NODE-023 live-smoke result: Kamatera USA gateway reachable, gateway auth ok, OpenAI Realtime from gateway ok, `chunks_sent=6`, `transcript_present=false`, and transcript text not logged.
44. Preserve NODE-023 operational conclusion: the manual HTTP gateway process was stopped after smoke; code and host-only secrets remain on the gateway, but no gateway systemd service was installed.
45. Preserve NODE-024 production integration boundary: gateway-backed STT may connect to business dialog only at the transcript-source boundary before `apply_turn(...)`, only behind disabled-by-default flags, and only after transcript quality/redaction/fallback gates pass.
46. Preserve NODE-024 secret boundary: `OPENAI_API_KEY` stays gateway-only; Asterisk may use only gateway URL/token from secret runtime config; transcript text is not logged by default.
47. Preserve NODE-024 failure policy: gateway unavailable, auth failure, timeout, OpenAI success with absent transcript, or low-quality transcript falls back to current deterministic prompt/retry behavior without weakening business contracts.
48. Preserve NODE-025 implementation boundary: the gateway adapter may run only when explicitly enabled and may drive dialog only when `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true`.
49. Preserve NODE-025 default safety: `STT_GATEWAY_STT_ENABLED=false`, `STT_GATEWAY_ADAPTER_ENABLED=false`, `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`, and `STT_GATEWAY_LOG_TRANSCRIPT=false`.
50. Preserve NODE-025 Asterisk secret boundary: no `OPENAI_API_KEY` is needed or read by the adapter; Asterisk uses only gateway URL/token runtime config.
51. Preserve NODE-026 local dry-run evidence: adapter validation may use mocks or a localhost-only fake HTTP gateway with fake tokens/transcripts, but must not require live Kamatera, OpenAI, Asterisk, live calls, real gateway tokens, or `OPENAI_API_KEY`.
52. Preserve NODE-026 dialog boundary: `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` keeps gateway transcripts from affecting `apply_turn(...)`; explicit transcript use remains non-default and must be validated only under local/test config until a later live-smoke node.
53. Preserve NODE-026 redaction evidence: transcript text is not logged by default in adapter or ARI events.
54. Preserve NODE-027 blocked-smoke truth: the Kamatera gateway adapter live smoke was not completed because SSH to `45.61.48.199:22` refused connections and port `8080` was unreachable from Asterisk.
55. Preserve NODE-027 helper boundary: `ai_secretary.stt.gateway_adapter_smoke` is a manual one-off CLI helper only, requires explicit flags for controlled smoke mode, redacts secrets/transcript text, refuses Asterisk-side `OPENAI_API_KEY`, and does not change production runtime behavior.
56. Preserve NODE-027 runtime result: no Kamatera gateway process was started, no live call ran, no `ai-secretary-ari.service` or Asterisk runtime env change was made, and production gateway STT remains disabled by default.
57. Preserve NODE-028 live-smoke result: Kamatera gateway reachable from Asterisk, gateway auth ok, OpenAI Realtime from gateway ok, `chunks_sent=15`, `transcript_present=false`, `fallback_reason=empty_transcript`, and transcript text not logged.
58. Preserve NODE-028 cleanup result: the temporary gateway listener was stopped, `ai-secretary-ari.service` remained active in the diagnostic-safe profile, Asterisk runtime env was unchanged, `OPENAI_API_KEY` remained absent on Asterisk, and production gateway STT remains disabled by default.
59. Preserve NODE-029 diagnostic result: NODE-028 used a silent synthetic WAV, so `empty_transcript` is most likely caused by near-silent/non-speech audio content.
60. Preserve NODE-029 instrumentation: gateway/measurement diagnostics include audio duration, format, chunk stats, RMS, peak, non-silent ratio, quality classification, Realtime event-type counts, transcript-event flags, commit-sent flag, timeout flag, and transcript text redaction by default.
61. Preserve NODE-030 live-smoke result: valid non-sensitive Russian speech produced transcript-bearing Realtime events and `transcript_present=true`; the prior NODE-028 empty transcript is closed as a silent/non-speech audio artifact.
62. Preserve NODE-030 helper boundary: only the manual smoke helper may request a gateway measurement while `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`; normal business dialog still makes no gateway request and no transcript may drive dialog unless dialog use is explicitly enabled.
63. Preserve NODE-030 cleanup result: the temporary Kamatera gateway was stopped, port `8080` was no longer listening, Asterisk runtime env and `ai-secretary-ari.service` were unchanged, and `OPENAI_API_KEY` remained absent on Asterisk.
64. Preserve NODE-031A workflow boundary: future AI-secrenar nodes should use feature branch plus PR workflow so Control Plane supervised runner closeout/evidence can apply where applicable.
65. Preserve NODE-031A historical boundary: existing `NODE-001` through `NODE-030` are commit-based historical nodes and should not be retrofitted through the PR-based supervised runner without a separate commit-based closeout design.
66. Preserve NODE-031 production gateway boundary: service ownership, supervised process boundary, loopback/private listen, restricted firewall sources, TLS reverse proxy, secure env ownership, and transcript log redaction are prerequisites for persistent gateway use.
67. Preserve NODE-031 secret boundary: `OPENAI_API_KEY` is gateway-only, `GATEWAY_TOKEN` is secure-runtime only, repo templates are placeholders only, and exposed tokens require rotation and incident response.
68. Preserve NODE-031 dialog boundary: gateway STT remains disabled by default, business dialog must not use gateway transcript text, and measurement helper paths remain distinct from business dialog paths unless a later explicit node changes this.
69. Preserve NODE-032 Phase A boundary: preflight and command planning only, no live apply, no service state change, no live smoke, and no business dialog transcript use.
70. Preserve NODE-032 approval gate: Phase B requires exact operator approval phrase `APPROVE NODE-032 LIVE APPLY/SMOKE`.
71. Preserve NODE-032B Phase A boundary: readiness/preflight and command planning only, no live apply, no service start/stop/restart/reload, no server state change, no live smoke, and no business dialog transcript use.
72. Preserve NODE-032B approval gate: Phase B requires exact operator approval phrase `APPROVE NODE-032B LIVE APPLY/SMOKE`; no other phrase is approval.
73. Preserve NODE-032B evidence boundary: expected evidence must be redacted and may include server targets, service state before/after, port/listen state before/after, firewall/TLS state, masked gateway env checks, masked Asterisk safe profile checks, health result, smoke result, transcript flags without transcript text, business dialog unchanged, and cleanup/persistent state decision.
74. Preserve NODE-032C read-only finding: Asterisk SSH works, `ai-secretary-ari.service` is active/enabled, and `OPENAI_API_KEY` is absent from the service process env.
75. Preserve NODE-032C gateway finding: gateway SSH works, historical env file `/etc/ai-secretary/openai-realtime-gateway.env` exists with masked `OPENAI_API_KEY` and `GATEWAY_TOKEN`, but `/etc/ai-secretary/gateway.env` is absent.
76. Preserve NODE-032C gateway service/listen finding: `ai-secretary-gateway.service` is not installed/enabled, no gateway process is running, and no `443`, `8080`, or `8081` gateway target port is listening.
77. Preserve NODE-032C firewall finding: UFW is active with deny incoming/allow outgoing, SSH open, and old `8080/tcp` allow from `92.118.85.117`.
78. Preserve NODE-032C recommendation: NO-GO for immediate NODE-032D live apply/smoke until env path, service unit, TLS/proxy, firewall transition, and rollback plan are explicitly resolved.
79. Preserve NODE-032D env path decision: first live smoke uses historical `/etc/ai-secretary/openai-realtime-gateway.env`; do not migrate to `/etc/ai-secretary/gateway.env` or create a symlink during first smoke.
80. Preserve NODE-032D service decision: future live apply may install/adapt `ai-secretary-gateway.service` at `/etc/systemd/system/ai-secretary-gateway.service`, run as `gateway:gateway`, use the historical env path, and use `on-failure` restart policy.
81. Preserve NODE-032D first-smoke network decision: no public TLS/proxy, no `443`, and no `8081` exposure for the first smoke; use the existing Asterisk-only `8080/tcp` path if re-confirmed source-restricted to `92.118.85.117`.
82. Preserve NODE-032D firewall transition decision: keep the old `8080/tcp` allow for first smoke, do not remove it before replacement path proof, and do not broaden firewall exposure.
83. Preserve NODE-032D rollback decision: stop/disable/remove only NODE-032E-installed service state, restore backed up unit state, leave historical env preserved, verify Asterisk has no `OPENAI_API_KEY`, and rotate tokens if any secret exposure occurs.
84. Preserve NODE-032D approval gate: future NODE-032E requires exact phrase `APPROVE NODE-032E LIVE APPLY/SMOKE`; no other phrase is approval.
85. Preserve NODE-032E Phase A gate finding: Asterisk SSH works, `ai-secretary-ari.service` is active/enabled, and `OPENAI_API_KEY` is absent from the Asterisk service process env.
86. Preserve NODE-032E Phase A gateway finding: historical env file `/etc/ai-secretary/openai-realtime-gateway.env` exists as `root:root 600`, with masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence.
87. Preserve NODE-032E Phase A service/listener finding: `ai-secretary-gateway.service` is inactive/absent/not enabled, no gateway process is running, and no `443`, `8080`, or `8081` target listener exists.
88. Preserve NODE-032E Phase A firewall finding: UFW is active with default incoming deny and existing `8080/tcp` allow from `92.118.85.117`.
89. Preserve NODE-032E Phase A recommendation: Phase B is NO-GO now because exact approval phrase is absent, even though technical gates are ready for a tightly scoped attempt if re-confirmed.
90. Preserve NODE-032E Phase B result: exact approval phrase was provided, hard gates were re-run, and live apply stopped before state change because the deployed Asterisk repo lacks the safe `gateway_adapter_smoke` helper path.
91. Preserve NODE-032E Phase B boundary: no systemd unit was written, no service was installed or started, no daemon reload ran, no firewall/env change occurred, no live smoke ran, and server state remained unchanged.
92. Preserve NODE-032E next blocker: a future node must prepare or approve an Asterisk-side safe gateway smoke helper/path before retrying live apply/smoke.
93. Preserve NODE-032F helper path: `scripts/asterisk_gateway_smoke_helper.py` is the approved manual Asterisk-side wrapper for the next live smoke path.
94. Preserve NODE-032F safety boundary: the helper refuses Asterisk-side `OPENAI_API_KEY`, requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`, requires transcript logging disabled, does not configure autostart, and creates no persistent server state.
95. Preserve NODE-032F proof boundary: the helper must run from the Asterisk host to prove `92.118.85.117 -> 45.61.48.199:8080`; workstation-origin smoke is not acceptable for that proof.
96. Preserve NODE-032G Phase A finding: live gates pass read-only, but Phase B is NO-GO until exact approval phrase `APPROVE NODE-032G LIVE APPLY/SMOKE`.
97. Preserve NODE-032G helper availability finding: `/home/tulauser/AI-secrenar-with-Asterisk-node014` exists but lacks the NODE-032F wrapper and required adapter modules, so Phase B should use an explicitly approved temporary helper bundle rather than assume `git pull`.
98. Preserve NODE-032G Phase B boundary: helper bundle deployment, gateway service start, runtime env file creation, and one Asterisk-origin smoke may occur only after exact approval and immediate hard-gate re-confirmation.
99. Preserve NODE-032G live-smoke result: Asterisk-origin helper smoke reached the gateway on `45.61.48.199:8080`, authenticated successfully, reached OpenAI Realtime from the gateway, sent `28` chunks, observed `transcript_present=true`, kept `transcript_text_logged=false`, and kept `business_dialog_unchanged=true`.
100. Preserve NODE-032G cleanup result: temporary gateway service/unit, helper bundle, runtime env file, and temp audio were removed; no `443`/`8081`/TLS/proxy/firewall broadening occurred; Asterisk still had no `OPENAI_API_KEY`.
101. Preserve NODE-032H persistence decision: use staged persistence, not immediate auto-enabled production service.
102. Preserve NODE-032H systemd policy: future durable gateway service is `ai-secretary-gateway.service` at `/etc/systemd/system/ai-secretary-gateway.service`, running as `gateway:gateway`, using `/etc/ai-secretary/openai-realtime-gateway.env`, `/opt/ai-secretary-gateway`, `0.0.0.0:8080`, and `Restart=on-failure`.
103. Preserve NODE-032H enablement boundary: install/start/smoke may be a next live node, but `systemctl enable` and reboot/power-cycle proof require explicit approval and may be separate controlled work.
104. Preserve NODE-032H firewall/listen policy: `0.0.0.0:8080` is acceptable only with UFW source restriction to `92.118.85.117`; do not expose `443` or `8081` in this stage and do not broaden firewall.
105. Preserve NODE-032H secrets/env policy: gateway owns OpenAI Realtime secrets, Asterisk must not contain `OPENAI_API_KEY`, durable service must not depend on shell exports, and exposed tokens require rotation.
106. Preserve NODE-032H business-dialog boundary: business dialog integration remains out of scope until gateway persistence and reboot behavior are proven.
107. Preserve NODE-032I Phase A boundary: readiness and command planning only, no live apply, no service install/start/stop/restart/reload/enable, no user/group creation, no chmod/chown, no firewall/env change, no helper deploy, no live smoke, no reboot/power-cycle, and no business dialog enablement.
108. Preserve NODE-032I approval gate: Phase B requires exact phrase `APPROVE NODE-032I SERVICE INSTALL/START/SMOKE`; no other phrase is approval.
109. Preserve NODE-032I rerun result: initial read-only SSH timed out, then rerun gates passed for Asterisk/Gateway reachability, Asterisk `OPENAI_API_KEY` absence, Gateway masked secret presence, listener absence, and UFW source restriction.
110. Preserve NODE-032I Phase B scope: install/adapt and start `ai-secretary-gateway.service` only after exact approval and hard gates, keep `systemctl enable`, reboot, and provider power-cycle out of scope.
111. Preserve NODE-032I Phase B service result: `gateway:gateway` exists, gateway env is `root:gateway 640`, `ai-secretary-gateway.service` is installed at `/etc/systemd/system/ai-secretary-gateway.service`, and the final service state is stopped and disabled.
112. Preserve NODE-032I Phase B smoke result: Asterisk-origin helper smoke reached the gateway, gateway auth was ok, OpenAI Realtime from gateway was ok, HTTP status was 200, `chunks_sent=28`, `transcript_present=true`, `transcript_text_logged=false`, `transcript_used_for_dialog=false`, and `business_dialog_unchanged=true`.
113. Preserve NODE-032I final safety boundary: no `systemctl enable`, no reboot/power-cycle, no `443`, no `8081`, no firewall broadening, no business dialog enablement, and temporary Asterisk helper/env/audio removed.
114. Preserve NODE-032J decision: keep the NODE-032I staged service artifact installed but stopped/disabled until a separate controlled enablement/reboot-smoke node receives exact approval.
115. Preserve NODE-032J approval gate for the next live node: `APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE`; no other phrase is approval.
116. Preserve NODE-032J scope boundary: NODE-032K may prove service enablement and reboot auto-start, but provider power-cycle, business dialog enablement, TLS/proxy, `443`, `8081`, and firewall broadening remain out of scope unless separately approved.

## Next Recommended Step

```text
NODE-032J docs-only closeout / PR review, then NODE-032K only after exact approval
```

NODE-032J decides to proceed toward autostart only through a separate controlled enablement/reboot smoke node. NODE-032K must re-confirm gates, manually prove service readiness, enable the service, reboot the Gateway server, verify auto-start/listener/firewall/log redaction, run one Asterisk-side smoke, and keep business dialog integration out of scope.

## Node Completion Report Format

After each node, return:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.
