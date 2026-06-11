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

NODE-032K Phase B attempted the approved controlled enable/reboot smoke:

```text
hard gates passed -> manual start -> systemctl enable -> Gateway reboot -> service auto-start verified -> token-output safety failure before smoke -> rollback
```

The service enablement and Gateway reboot proof reached active/enabled post-reboot with listener on `8080` only and UFW still restricted to `92.118.85.117`, but a malformed temporary Asterisk smoke env caused a token value to print during diagnostic inspection. The smoke did not run. Rollback disabled/stopped the service, removed temporary helper/env/audio, left no target listeners, and preserved firewall state. Token rotation and a safer temp-env creation path are required before retry.

NODE-032K security remediation rotated the exposed Gateway token without printing old or new token values. The Gateway env remains `root:gateway 640`; the service remains disabled/inactive; no target listeners exist; firewall state is unchanged. A safer temporary env creation/verification path is still required before any retry.

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
117. Preserve NODE-032K Phase A boundary: readiness and command planning only, with read-only SSH gates and no live enablement, no service start/stop/restart/reload, no `systemctl enable`, no reboot, no provider power-cycle, no firewall/env change, no helper deploy, no live smoke, and no business dialog enablement.
118. Preserve NODE-032K Phase A handoff archive: long-form sanitized handoff is stored at `docs/handoffs/NODE-032K-phase-a-codex-handoff.md`; short external playbooks should reference the repo archive.
119. Preserve NODE-032K Phase A gate result: Asterisk gates passed, Gateway staged service is present/inactive/disabled, gateway env is `root:gateway 640`, masked secrets are present, unit verifies, no `443`/`8080`/`8081` listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
120. Preserve NODE-032K Phase B partial proof and rollback: after exact approval, hard gates passed, the gateway service manually started, `systemctl enable` ran, Gateway-only reboot returned, and the service auto-started active/enabled with listener on `8080` only and UFW still source-restricted.
121. Preserve NODE-032K Phase B hard NO-GO: the controlled smoke stopped before a gateway request because a malformed temporary Asterisk env diagnostic printed a gateway token value. Do not record the value; rotate the gateway token before any retry.
122. Preserve NODE-032K rollback state: `systemctl disable` and stop were run, final service state is disabled/inactive, no target listeners remain on `443`, `8080`, or `8081`, firewall was unchanged, temporary Asterisk helper/env/audio were removed, and Asterisk still has no `OPENAI_API_KEY`.
123. Preserve NODE-032K security remediation: the exposed Gateway token was rotated on the Gateway host only, no token values were printed or recorded, Gateway env remains `root:gateway 640`, the service remains disabled/inactive, no target listeners exist, firewall is unchanged, and no smoke retry occurred.
124. Preserve NODE-032L temp-env guard: future gateway smoke temp env creation must use a newline-safe, redaction-safe guard or equivalent, read token material from stdin, reject CR/LF and literal newline material, print only masked presence/status flags, require dialog transcript use and transcript logging to remain false, and clean up the temp env after use.
125. Preserve NODE-032M Phase A boundary: readiness and retry command planning only, with local guard/helper inspection and read-only SSH gates; no live retry, service action, `systemctl` state change, reboot, provider power-cycle, firewall/env/server change, helper deploy, smoke, or business dialog enablement.
126. Preserve NODE-032M Phase A gate result: Asterisk gates pass with `OPENAI_API_KEY_ABSENT`, Gateway staged service is present/inactive/disabled, gateway env is `root:gateway 640`, masked secrets are present, unit verifies, no `443`/`8080`/`8081` listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
127. Preserve NODE-032M approval gate: Phase B requires exact phrase `APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY`; no other phrase is approval.
128. Preserve NODE-032M retry boundary: any future smoke retry must use the NODE-032L safe temp-env guard or equivalent, must never print token values or transcript text, and must clean up temporary helper/env/audio.
129. Preserve NODE-032M Phase B partial proof and rollback: after exact approval, hard gates passed, the Gateway service manually started, `systemctl enable` ran, Gateway-only reboot returned, and the service auto-started active/enabled with listener on `8080` only and UFW still source-restricted.
130. Preserve NODE-032M Phase B smoke blocker: exactly one Asterisk-side helper invocation was attempted, but it failed before Gateway request because the temporary helper bundle lacked `ai_secretary.config`; no token values or transcript text were printed.
131. Preserve NODE-032M rollback state: `systemctl disable` and stop were run, final service state is disabled/inactive, no target listeners remain on `443`, `8080`, or `8081`, firewall was unchanged, temporary Asterisk helper/env/audio were removed, and Asterisk still has no `OPENAI_API_KEY`.
132. Preserve NODE-032N helper-bundle fix: future Asterisk-side Gateway smoke retries must use an explicit minimal helper bundle manifest and preflight validator, including `ai_secretary.config`, before any helper invocation.
133. Preserve NODE-032N safety boundary: the bundle helper must not read or print token values or transcript text; token handling remains owned by the NODE-032L safe temp-env guard.
134. Preserve NODE-032N retry boundary: no live retry occurred; the next live retry requires a separate approved node, immediate hard-gate re-confirmation, complete helper bundle validation, safe temp-env create/validate/cleanup, and cleanup of temporary helper/env/audio.
135. Preserve NODE-032O Phase A boundary: readiness and smoke retry command planning only, with local guard/helper inspection and read-only SSH gates; no live retry, service action, `systemctl` state change, reboot, provider power-cycle, firewall/env/server change, helper deploy, smoke, or business dialog enablement.
136. Preserve NODE-032O Phase A gate result: Asterisk gates pass with `OPENAI_API_KEY_ABSENT`, Gateway staged service is present/inactive/disabled, gateway env is `root:gateway 640`, masked secrets are present, unit verifies, no `443`/`8080`/`8081` listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
137. Preserve NODE-032O approval gate: Phase B requires exact phrase `APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY`; no other phrase is approval.
138. Preserve NODE-032O retry boundary: Phase B may stage the complete helper bundle and run exactly one Asterisk-side non-business-dialog smoke only after approval and hard-gate re-confirmation; no `systemctl enable`, reboot, provider power-cycle, `443`, `8081`, TLS/proxy, firewall broadening, token output, transcript text logging, or business dialog enablement.
139. Preserve NODE-032O Phase B blocked result: exact approval was provided and hard gates passed, but remote staged helper-bundle validation failed closed before token handling, service start, smoke, or Gateway request because preflight import missed runtime module `httpx`.
140. Preserve NODE-032O cleanup/final state: temporary Asterisk helper/env/audio and local helper archive/bundle were removed, Gateway service remains inactive/disabled, no target listeners remain on `443`, `8080`, or `8081`, firewall is unchanged, and Asterisk still has `OPENAI_API_KEY_ABSENT`.
141. Preserve NODE-032P runtime dependency preflight: temporary helper bundle validation must check required third-party runtime modules before token handling, temp-env creation, service action, smoke, or Gateway request.
142. Preserve NODE-032P dependency policy: runtime preflight requires `httpx`, `fastapi`, and `websockets`; missing runtime modules fail closed with safe module names only; no third-party vendoring or server dependency install occurred in NODE-032P.

143. Preserve NODE-032Q Phase A boundary: readiness and smoke retry command planning only, with local guard/helper/runtime-preflight inspection and read-only SSH gates; no live retry, dependency install, service action, `systemctl` state change, reboot, provider power-cycle, firewall/env/server change, helper deploy, smoke, or business dialog enablement.
144. Preserve NODE-032Q Phase A gate result: Asterisk gates pass with `OPENAI_API_KEY_ABSENT`, Gateway staged service is present/inactive/disabled, gateway env is `root:gateway 640`, masked secrets are present, unit verifies, no `443`/`8080`/`8081` listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
145. Preserve NODE-032Q approval gate: Phase B requires exact phrase `APPROVE NODE-032Q RUNTIME-PREFLIGHT SMOKE RETRY`; no other phrase is approval.
146. Preserve NODE-032Q runtime dependency policy: remote helper-bundle validation must run before token handling, temp-env creation, service action, smoke, or Gateway request; if `httpx`, `fastapi`, or `websockets` is missing, stop as NO-GO and do not install dependencies in NODE-032Q.
147. Preserve NODE-032Q Phase A NO-GO: read-only Asterisk import probes confirmed `httpx`, `fastapi`, and `websockets` are missing, so NODE-032Q Phase B must not run until a separately approved dependency-resolution or alternate-helper-strategy node resolves the blocker.
148. Preserve NODE-032R decision: choose a separate controlled Asterisk runtime dependency install/readiness node before any Gateway smoke retry, preserving the existing helper-bundle and adapter smoke evidence path.
149. Preserve NODE-032R safety boundary: no dependency install, SSH, helper deploy, live retry, service action, `systemctl` action, reboot, provider power-cycle, firewall/env/server change, token output, transcript text output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, push, or PR occurred.
150. Preserve NODE-032R separation: dependency readiness and Gateway smoke retry must not be combined unless a later node explicitly re-scopes and approves that risk; the next node should resolve `httpx`, `fastapi`, and `websockets` only, then stop.
151. Preserve NODE-032S Phase A boundary: read-only readiness and command planning only; no dependency install, pip install, apt install, server file write, venv creation, helper deploy, live retry, service action, reboot, firewall/env/server change, token output, or transcript text output occurred.
152. Preserve NODE-032S runtime finding: system Python lacks `httpx`, `fastapi`, and `websockets`, but the existing deployed project venv at `/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python` has all three modules.
153. Preserve NODE-032S target recommendation: Phase B should use the deployed project venv, re-confirm readiness after exact approval, and stop without Gateway smoke; install is expected to be unnecessary unless immediate re-check finds a missing module.
154. Preserve NODE-032S Phase B readiness: after exact approval, hard gates were re-confirmed and the selected project venv imported `httpx 0.28.1`, `fastapi 0.136.1`, and `websockets 16.0`.
155. Preserve NODE-032S Phase B no-install result: no dependency install, pip install, apt install, system Python mutation, project venv mutation, helper deploy, Gateway smoke retry, Gateway service action, reboot, firewall/env/server change, token output, or transcript text output occurred.
156. Preserve NODE-032S separation: runtime dependency readiness is complete, but Gateway smoke retry still requires a separate approved node with immediate hard-gate re-confirmation.
157. Preserve NODE-032T Phase A boundary: readiness and Gateway smoke retry planning only; no live smoke retry, helper copy/deploy, token handling, server temp env creation, dependency install, service action, `systemctl` action, reboot, firewall/env/server change, token output, or transcript text output occurred.
158. Preserve NODE-032T Phase A gate result: Asterisk gates pass with `OPENAI_API_KEY_ABSENT`, selected project venv imports `httpx 0.28.1`, `fastapi 0.136.1`, and `websockets 16.0`, Gateway unit verifies, Gateway service is inactive/disabled, no target listeners exist, and UFW restricts `8080/tcp` to `92.118.85.117`.
159. Preserve NODE-032T approval gate: Phase B requires exact phrase `APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS`; no other phrase is approval.
160. Preserve NODE-032T retry plan: Phase B must use NODE-032L safe temp-env handling, NODE-032N complete helper bundle validation, NODE-032P runtime preflight, NODE-032S selected runtime, and exactly one Asterisk-side non-business-dialog Gateway smoke only after hard-gate re-confirmation.
161. Preserve NODE-032T smoke blocker: the single Asterisk-origin smoke reached and authenticated with the Gateway, but the generated synthetic WAV was `16000 Hz`; the Gateway requires `24000 Hz mono 16-bit PCM`.
162. Preserve NODE-032U audio decision: future smoke retry audio must be repo-created or repo-validated as `24000 Hz mono 16-bit PCM WAV` before the Gateway request; `16000 Hz`, stereo, and malformed WAV inputs fail closed.
163. Preserve NODE-032U architecture boundary: no `8 kHz`, stereo, dual-channel, Gateway behavior, business dialog, service, firewall, env, dependency, reboot, or provider power-cycle change is included in Phase A.
164. Preserve NODE-032U approval gate: Phase B requires exact phrase `APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY`; no other phrase is approval.
165. Preserve NODE-032V acceptance decision: NODE-032U is accepted as successful controlled Gateway transport/auth/OpenAI Realtime smoke with valid 24 kHz audio, Gateway HTTP 200, OpenAI Realtime OK, and `chunks_sent=5`.
166. Preserve NODE-032V non-acceptance boundary: NODE-032U is not transcript-quality success, transcript-present success, transcript text correctness proof, business-dialog integration proof, production autostart proof, or dual-channel caller/bot separation proof.
167. Preserve NODE-032V separation decision: the next boundary should prove transcript event/presence behavior while keeping `transcript_text_logged=false`, `transcript_used_for_dialog=false`, and business dialog unchanged.
168. Preserve NODE-032X decision: NODE-032W remains transport/auth/OpenAI Realtime success only; transcript presence remains unproven and the next safe work must improve redacted event diagnostics before another smoke.
169. Preserve NODE-032Y diagnostic model: future smoke evidence must use safe event counts, booleans, transcript text buckets, and diagnostic classifications only; transcript text, token values, raw env output, large logs, audio artifacts, and business-dialog transcript use remain forbidden.

## Next Recommended Step

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

NODE-032Y hardens local redacted diagnostics but does not prove live transcript presence. NODE-032Z should run one controlled Asterisk-side Gateway smoke to classify transcript-event behavior with redacted counts and booleans only, without logging transcript text and without enabling business-dialog transcript use.

## NODE-032W Phase A Plan

NODE-032W prepares the transcript-presence proof boundary without running live smoke. Phase A confirms:

- existing helper and adapter reports can expose redacted transcript event/presence flags;
- transcript text logging and business-dialog transcript use remain disabled;
- Asterisk and Gateway read-only gates pass;
- the selected Asterisk project venv remains ready;
- the Gateway service is installed but inactive/disabled, with no target listeners and UFW still restricted.

Future Phase B requires:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Phase B must run exactly one Asterisk-side non-business-dialog smoke and accept only safe transcript event/presence flags, not transcript text or business-dialog use.

## NODE-032W Phase B Result

NODE-032W Phase B ran exactly one controlled Asterisk-side non-business-dialog smoke after exact approval and hard-gate re-confirmation.

The Gateway transport/auth/OpenAI Realtime path remained good:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent=5
```

However, transcript-presence proof did not close:

```text
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
```

Next plan:

```text
NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```

NODE-032X should decide whether the next attempt needs a different approved audio stimulus, additional redacted Gateway event diagnostics, or another no-text transcript-presence strategy.

## NODE-032X Diagnostics Decision

NODE-032X is local-only and preserves NODE-032W accurately:

```text
transport_auth_openai_realtime_success=true
gateway_http_status=200
chunks_sent=5
transcript_presence_success=false
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
```

NODE-032W transport/auth/OpenAI success is not enough because it proves only reachability, auth, audio format acceptance, session creation, and chunk send. It does not prove that OpenAI emitted transcript events, that Gateway event parsing recognized them, that redacted diagnostics propagated to the Asterisk-side report, or that the stimulus was speech-like enough.

Selected next boundary:

```text
NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

NODE-032Y should harden local redacted diagnostics before any new live smoke. It should make event-count and transcript-event flags explicit enough to distinguish no transcript event, empty transcript event, transcript-bearing event with text redacted, timeout after audio commit, and missing diagnostic propagation. Known-speech stimulus and session setting changes remain deferred until diagnostics can classify the result without transcript text.

## NODE-032Y Diagnostics Hardening Result

NODE-032Y is local/repo-only and adds deterministic redacted diagnostics before another live smoke.

Future smoke reports can now distinguish:

```text
no_event_counts_available
openai_event_type_counts_present
transcript_event_seen=false
transcript_event_seen=true
transcript_bearing_event_seen=false
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_present=true
transcript_text_length_bucket=zero|nonzero_redacted|unknown
input_audio_buffer_commit_sent=true|false
timeout_observed=true|false
error_event_seen=true|false
diagnostic_propagation_gap=true|false
```

The selected next boundary is:

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

NODE-032Z should run one controlled Asterisk-side non-business-dialog smoke only after exact approval and immediate hard-gate re-confirmation. It must not log transcript text, expose tokens, enable business-dialog transcript use, or change production service/autostart state.

## NODE-032Z Phase A Plan

NODE-032Z Phase A completed read-only readiness checks and planning only. The live smoke remains unapproved.

Future Phase B requires the exact approval phrase:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Phase B must immediately re-confirm all hard gates because the servers were recently powered on after a pause. If gates pass, Phase B may run exactly one Asterisk-side non-business-dialog smoke and collect only NODE-032Y safe diagnostic fields: event counts, booleans, transcript text bucket, propagation-gap flag, and diagnostic classification.

Phase B must not log transcript text, expose token values, enable business-dialog transcript use, change production autostart, broaden firewall, reboot, or perform provider power-cycle.

## NODE-032Z Phase B Result

NODE-032Z Phase B ran after exact approval:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Hard gates passed. Helper bundle validation, 24 kHz mono 16-bit PCM smoke audio validation, and safe temp-env create/validate/cleanup all completed with no token values or transcript text printed. Gateway service was started only for smoke readiness and remained disabled.

Exactly one corrected Asterisk-side non-business-dialog smoke ran. A prior malformed helper CLI invocation failed at argument parsing before any Gateway request and is recorded only as a non-smoke command error.

Smoke result:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

NODE-032Y diagnostic fields classified the result as a propagation gap:

```text
openai_event_type_counts_present=false
openai_event_type_counts={}
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

NODE-032Z therefore remains a transport/auth/OpenAI Realtime success but a blocked redacted-diagnostics smoke. The next node should fix local/Gateway diagnostic propagation before another transcript-presence retry:

```text
NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
```

## NODE-032AA Diagnostics Propagation Fix

NODE-032AA is a local implementation/docs node. It does not run live smoke or touch servers.

It adds an explicit safe field:

```text
openai_event_type_counts_available
```

This separates two cases:

```text
openai_event_type_counts_available=true and openai_event_type_counts={} means diagnostics propagated but event counts are empty
openai_event_type_counts_available=false means event-count diagnostics are missing/not propagated
```

The smoke report now keeps `diagnostic_propagation_gap=false` for empty-but-present diagnostics and reserves `diagnostic_propagation_gap=true` for missing diagnostics. It also defensively strips transcript text from smoke report details whenever transcript logging is disabled.

Next live boundary:

```text
NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix
```

NODE-032AB should run one controlled Asterisk-side non-business-dialog smoke after exact approval and hard-gate re-confirmation, checking the new availability marker plus the existing redacted diagnostic fields.

## NODE-032AB Phase A Plan

NODE-032AB Phase A completed read-only readiness and command planning only.

Fresh base:

```text
master_head=43c8ec3b658cc63874ebeb4207c36ea881e62a13
```

Phase A confirmed:

```text
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
asterisk_service=active_enabled
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
gateway_service=inactive_disabled
gateway_unit_verify=OK
gateway_env_metadata=root:gateway:640
gateway_masked_secret_presence=passed
target_listeners_443_8080_8081=absent
ufw_8080_tcp=ALLOW_IN_FROM_92.118.85.117_ONLY
```

Future Phase B may be requested only with:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

NODE-032AB Phase B, if approved, should run exactly one controlled Asterisk-side non-business-dialog smoke and verify `openai_event_type_counts_available` plus the existing redacted diagnostic fields without transcript text logging or business-dialog transcript use.

## NODE-032AB Phase B Result

NODE-032AB Phase B ran after exact approval:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

The controlled smoke again proved transport/auth/OpenAI Realtime from the Asterisk origin:

```text
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
```

However, the NODE-032AA marker did not appear as available in live smoke evidence:

```text
openai_event_type_counts_available=false
openai_event_type_counts_present=false
openai_event_type_counts={}
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

This means NODE-032AB is blocked on live diagnostic propagation, not on Gateway auth or OpenAI transport.

Next boundary:

```text
NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
```

## NODE-032AC Gateway Runtime Diagnostics Rollout Plan

NODE-032AC is repo-local planning only.

Conclusion:

```text
helper_bundle_parser_current=true
gateway_service_runtime_is_separate_deployed_tree=true
gateway_service_runtime_path=/opt/ai-secretary-gateway/src
likely_root_cause=live_gateway_runtime_not_updated_to_NODE_032AA_or_runtime_response_mapping_not_reloaded
```

The next step must be a controlled rollout/runtime propagation node, not another blind smoke retry.

Selected next node:

```text
NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
```

NODE-032AD should inventory the deployed Gateway runtime, compare safe marker/hash evidence against the repo, back up current deployed runtime files, apply only the diagnostics propagation update after exact approval, and then verify the deployed marker and runtime safety. A follow-up smoke can verify `openai_event_type_counts_available=true` after rollout unless explicitly included in NODE-032AD scope.

## NODE-032AD Controlled Gateway Runtime Diagnostics Propagation Rollout

NODE-032AD Phase A completed read-only inventory only.

Confirmed:

```text
gateway_service_runtime=/opt/ai-secretary-gateway/src
deployed_realtime_gateway_marker_present=false
deployed_realtime_gateway_hash_matches_repo=false
deployed_runtime_appears_stale=true
backup_parent_exists=true
backup_parent_writable_as_root=true
```

Plan for Phase B after exact approval:

```text
approval_phrase=APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
reconfirm_all_hard_gates
backup_current_deployed_realtime_gateway_py
roll_out_repo_realtime_gateway_py_to_deployed_runtime_path_only
verify_marker_and_hash
preserve_env_and_firewall
avoid_smoke_unless separately scoped
document rollback_path
```

NODE-032AD Phase B completed the controlled runtime rollout without smoke.

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
marker_present_after_rollout=true
local_deployed_hash_match=true
service_action=false
gateway_final_state=inactive_disabled
firewall_unchanged=true
```

Next planned boundary:

```text
NODE-032AE / controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout
```

NODE-032AE attempted the next smoke boundary after exact approval, but Gateway service readiness failed before the smoke helper invocation.

```text
blocker=deployed_runtime_dependency_gap
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
smoke_helper_invoked=false
gateway_request_reached=false
```

Next planned boundary:

```text
NODE-032AF / controlled-gateway-runtime-measurement-dependency-rollout
```

## Node Completion Report Format

After each node, return:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.

## NODE-032AG Controlled Transcript Event Diagnostics Smoke Readiness

NODE-032AG Phase A completed read-only smoke readiness checks after NODE-032AF.

Confirmed:

```text
asterisk_safety_gates=passed
gateway_safety_gates=passed
gateway_service=inactive_disabled
realtime_gateway_marker_and_hash=valid
realtime_measurement_symbol_and_hash=valid
```

Plan for Phase B after exact approval:

```text
approval_phrase=APPROVE NODE-032AG PHASE B LIVE SMOKE
reconfirm_all_hard_gates
start_gateway_service_only_for_smoke_readiness
run_exactly_one_asterisk_side_non_business_dialog_smoke
collect_redacted_diagnostics_only
restore_final_safe_state
```

NODE-032AG Phase B completed the approved controlled Asterisk-side non-business-dialog smoke.

```text
approval_phrase=APPROVE NODE-032AG PHASE B LIVE SMOKE
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
business_dialog_unchanged=true
final_gateway_service=inactive_disabled
```

Next planned boundary:

```text
NODE-032AH / transcript-event-diagnostics-smoke-acceptance-and-next-boundary-decision
```

## NODE-032AH Transcript Event Diagnostics Smoke Acceptance

NODE-032AH accepts NODE-032AG as successful deployed Gateway diagnostics propagation proof.

Accepted proof:

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
```

Remaining limitation:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
```

Next planned boundary:

```text
NODE-032AI / controlled-transcript-content-stimulus-quality-plan
```

## NODE-032AF Controlled Gateway Runtime Measurement Dependency Rollout

NODE-032AF Phase A completed read-only inventory of the deployed Gateway measurement dependency.

Confirmed:

```text
deployed_realtime_gateway_marker_present=true
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
deployed_realtime_measurement_symbol_diagnose_pcm_wav_audio_bytes=absent
local_realtime_measurement_symbol_diagnose_pcm_wav_audio_bytes=present
deployed_runtime_dependency_stale_or_missing=true
backup_dir_exists=true
```

Plan for Phase B after exact approval:

```text
approval_phrase=APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
reconfirm_all_hard_gates
backup_current_deployed_realtime_measurement_py
roll_out_repo_realtime_measurement_py_to_deployed_runtime_path_only
verify_symbol_and_hash
preserve_env_and_firewall
avoid_smoke_unless_separately_scoped
document_rollback_path
```

NODE-032AF Phase B completed the controlled measurement dependency rollout without smoke.

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
backup_dir=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z
deployed_realtime_measurement_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
diagnose_pcm_wav_audio_bytes=present
service_action=false
gateway_final_state=inactive_disabled
firewall_unchanged=true
smoke_ran=false
```

Next planned boundary:

```text
NODE-032AG / controlled-gateway-diagnostics-marker-smoke-after-measurement-rollout
```
## NODE-032AI Plan Update

NODE-032AI records the next safe planning boundary after NODE-032AH accepted NODE-032AG as deployed Gateway diagnostics propagation proof.

Decision:

```text
diagnostics_propagation_proof=accepted
transport_auth_openai_realtime_path=accepted
transcript_text_content_proof=not_accepted
remaining_issue=empty_or_zero_transcript_content
```

The next smoke should not be repeated unchanged. Before another live smoke, prepare a safer stimulus/content plan that defines:

```text
longer_speech_duration
clearer_speech_like_waveform
avoid_clipping
avoid_silence_dominant_segments
24000_hz_mono_16_bit_pcm_validation
duration_rms_peak_non_silent_ratio_diagnostics
redacted_success_metrics_only
```

Next node:

```text
NODE-032AJ / controlled-transcript-content-stimulus-preparation
```
## NODE-032AJ Plan Update

NODE-032AJ prepares the next safe transcript-content smoke boundary without running a smoke or creating audio artifacts.

Stimulus strategy:

```text
speech_duration_longer_than_NODE_032AG
clear_speech_like_waveform
not_silence_dominant
not_clipped
24000_hz_mono_16_bit_pcm
duration_rms_peak_non_silent_ratio_reported=true
no_real_caller_audio=true
no_sensitive_audio=true
no_committed_audio_binary_artifacts=true
```

The next smoke should use redacted evidence only:

```text
transcript_text_length_bucket=nonzero_bucket
actual_transcript_text_redacted=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

Next node:

```text
NODE-032AK / controlled-transcript-content-smoke-with-prepared-stimulus
```
## NODE-032AK Phase A Plan Update

NODE-032AK Phase A completed read-only readiness for a future controlled transcript-content smoke with prepared stimulus.

Phase B is not approved yet. It requires:

```text
APPROVE NODE-032AK PHASE B LIVE SMOKE
```

Phase B, if approved, should run one controlled non-business-dialog smoke using:

```text
non_sensitive_generated_speech_like_stimulus
speech_duration_longer_than_NODE_032AG
audio_format=24000_hz_mono_16_bit_pcm
duration_rms_peak_non_silent_ratio_reported_before_smoke=true
actual_transcript_text_redacted=true
```

Expected target:

```text
transcript_text_length_bucket=nonzero_bucket
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
token_values_printed=false
```
## NODE-032AK Phase B Plan Result

NODE-032AK Phase B ran exactly one controlled Asterisk-side non-business-dialog smoke after the exact approval phrase.

Transport/auth/runtime diagnostics passed:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=20
openai_event_type_counts_available=true
diagnostic_propagation_gap=false
transcript_event_seen=true
transcript_bearing_event_seen=true
```

Transcript content remained blocked:

```text
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_classification=transcript_event_observed_empty_or_no_text
```

Next recommended planning boundary:

```text
NODE-032AL / transcript-content-empty-after-prepared-stimulus-analysis
```
## NODE-032AL Plan Result

NODE-032AL completed local repo analysis of the NODE-032AK empty transcript-content result. It did not run another smoke or touch live systems.

The remaining issue is classified as:

```text
transport_auth_runtime_diagnostics_blocker=false
diagnostic_propagation_gap=false
transcript_content_empty_after_prepared_stimulus=true
```

Primary next hypotheses:

```text
audio_semantics_not_real_speech_despite_signal_metrics
provider_completed_empty_event_expected_under_current_input
session_transcription_settings_suboptimal_for_synthetic_stimulus
language_or_model_context_issue
```

Next recommended local boundary:

```text
NODE-032AM / transcript-content-empty-local-schema-and-stimulus-analysis
```
## NODE-032AM Plan Result

NODE-032AM completed local schema/stimulus analysis without source/runtime changes or live access.

Current parser assumptions:

```text
delta_event=conversation.item.input_audio_transcription.delta
delta_text_field=payload.delta
completed_event=conversation.item.input_audio_transcription.completed
completed_text_field=payload.transcript
alternate_or_nested_text_fields_read=none
```

The next safe boundary should be local implementation/tests/specs, not a live smoke:

```text
NODE-032AN / transcript-event-schema-fixtures-and-nonzero-bucket-local-proof
```

NODE-032AN should add placeholder-safe local fixtures for alternate provider event shapes and prove non-zero bucket mapping without logging transcript text.
## NODE-032AN Plan Result

NODE-032AN implemented placeholder-safe local parser fixtures and tests for selected transcript event schema shapes.

Covered:

```text
top_level_delta
top_level_completed_transcript
nested_completed_transcript_text_or_value
item_transcript
content_array_transcript_or_text
alternate_delta_text
```

Deferred:

```text
late_delta_after_completed_event
```

Next recommended boundary:

```text
NODE-032AO / safe-actual-speech-stimulus-and-session-settings-plan
```
## NODE-032AO Plan Result

NODE-032AO completed the local safe stimulus and session settings plan before any new live transcript-content smoke.

The next live attempt should isolate the stimulus variable:

```text
stimulus_label=SAFE_RU_SHORT_COMMAND
expected_language=ru
expected_content_bucket=nonempty_linguistic
format=24000_hz_mono_16_bit_pcm_wav
actual_spoken_text_not_recorded=true
audio_not_committed=true
```

Current session settings should be kept for the first next smoke unless immediate Phase A gates fail:

```text
model=gpt-realtime-whisper
language=ru
sample_rate=24000
chunk_ms=200
turn_detection=unchanged
noise_reduction=unchanged
prompt_or_context=unchanged
```

Next recommended boundary:

```text
NODE-032AP / controlled-actual-speech-transcript-content-smoke
```

Future exact approval phrase:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```
## NODE-032AP Phase A Result

NODE-032AP began the controlled actual-speech transcript-content smoke boundary with Phase A read-only preflight only.

Local readiness passed:

```text
focused_suite=55_passed
source_runtime_diff=empty
```

Server readiness did not pass because the first required server gate failed:

```text
asterisk_ssh_reachable=false
blocker=asterisk_ssh_timeout_to_92_118_85_117_port_22
gateway_checks=not_run_after_asterisk_gate_failure
phase_b_recommendation=NO_GO
```

Future Phase B remains blocked until Asterisk SSH reachability is restored, all hard gates pass, and the exact approval phrase is provided:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```
## NODE-032AQ Reachability Result

NODE-032AQ attempted repository-local validation and Asterisk reachability recovery/classification only.

Local readiness passed:

```text
focused_suite=55_passed
source_runtime_diff=empty
```

Asterisk remained unreachable:

```text
tcp_22_reachable=false
ping_reachable=false
ssh_reachable=false
power_state_check_available=false
power_on_available=false
```

No power-on occurred because no provider power-control mechanism was available in the repo or active tooling. The next action is out-of-band provider or network recovery, then another read-only preflight before NODE-032AP Phase B can be requested.

## NODE-032AR Reachability Evidence Result

NODE-032AR records coordinator-collected read-only evidence after out-of-band Asterisk reachability recovered.

Recovered evidence:

```text
tcp_22_reachable=true
ssh_login=ok
ping_timeout=true
host=tula
os=Ubuntu 24.04.3 LTS
kernel=6.8.0-53-generic
uptime_at_check=12_min
```

Runtime interpretation:

```text
asterisk_systemd_unit_absent=true
asterisk_runtime_process_present=true
ai_secretary_service_ready=true
future_phase_b_preconditions_can_be_reconsidered=true
```

NODE-032AR did not run smoke, generate audio, deploy helpers, handle tokens, create temp env files, perform service actions, or mutate firewall/env/server state. Any live smoke still requires exact approval and immediate hard-gate re-check.

The Selectel disk image exists as a fallback and was not touched. The Asterisk server was started out of band by user/provider action before NODE-032AR documentation; Codex performed no power action.

## NODE-032AS Gateway Hard-Gate Preflight Result

NODE-032AS checked the Gateway hard gate after Asterisk recovery evidence was recorded.

Result:

```text
gateway_host=45.61.48.199
gateway_tcp_22_reachable=false
gateway_ssh_attempted=false
phase_b_hard_gate=NO_GO
blocker=gateway_ssh_unreachable_or_powered_off
```

The Gateway was known from coordinator context as not started, and the local TCP 22 check timed out. No Gateway power-on or provider-control action occurred.

Next recommendation:

```text
out_of_band_gateway_start_or_recovery_then_rerun_read_only_gateway_preflight
```
