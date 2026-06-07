# NODE-032AG / controlled-transcript-event-diagnostics-smoke-after-measurement-dependency-rollout

Date: 2026-06-07

Branch: `feat/node-032ag-controlled-transcript-event-diagnostics-smoke-after-measurement-dependency-rollout`

Phase: Phase B complete - controlled live smoke passed and final safe state restored.

## Goal

Confirm safe gates and deployed runtime readiness after NODE-032AF before requesting one controlled transcript-event diagnostics smoke.

Phase B is not approved in Phase A.

Future approval phrase:

```text
APPROVE NODE-032AG PHASE B LIVE SMOKE
```

## NODE-032AF Context

NODE-032AF completed the controlled Gateway runtime measurement dependency rollout without smoke.

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
backup_file=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z/realtime_measurement.py
realtime_measurement_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
diagnose_pcm_wav_audio_bytes=present
realtime_gateway_marker=openai_event_type_counts_available
realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
```

## Asterisk Read-Only Gates

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service_active=true
ai-secretary-ari.service_enabled=true
main_pid=3792
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
target_listeners_443_8080_8081=absent
selected_runtime_present=true
selected_runtime_version=3.12.3
runtime_module_httpx=present
runtime_module_fastapi=present
runtime_module_websockets=present
```

## Gateway Read-Only Gates

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
unit_verify=OK
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
```

No secret env values were printed.

## Deployed Runtime Readiness

```text
realtime_gateway_exists=true
realtime_gateway_metadata=root:root 664 21922 2026-06-07 14:05:26 +0000
openai_event_type_counts_available=present
realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
realtime_measurement_exists=true
realtime_measurement_metadata=root:root 664 25609 2026-06-07 19:15:45 +0000
diagnose_pcm_wav_audio_bytes=present
def_diagnose_pcm_wav_audio_bytes=present
realtime_measurement_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
```

## Future Phase B Scope

After exact approval only, Phase B should:

```text
reconfirm_hard_gates=true
start_gateway_service_only_for_smoke_readiness=true
run_exactly_one_asterisk_side_non_business_dialog_smoke=true
safe_stdin_only_token_handling=true
redacted_diagnostics_only=true
transcript_text_logging=false
transcript_delta_logging=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
restore_final_safe_state=true
```

Required result fields include:

```text
gateway_reachable_from_asterisk
gateway_auth
gateway_http_status
openai_realtime_from_gateway
openai_session_created
chunks_sent
openai_event_type_counts_available
openai_event_type_counts_present
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
diagnostic_propagation_gap
diagnostic_classification
transcript_text_logged
transcript_used_for_dialog
business_dialog_unchanged
adapter_default_enabled_after_smoke
```

Expected verification target:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent>0
openai_event_type_counts_available=true
diagnostic_propagation_gap=false_when_diagnostics_are_present_even_if_event_counts_empty
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
```

## Phase A Decision

```text
phase_a_result=complete
phase_b_smoke_can_be_requested=true
phase_b_condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
approval_phrase=APPROVE NODE-032AG PHASE B LIVE SMOKE
blockers=none_for_phase_b_request
```

## Validation

```text
focused_suite=50_passed
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found_existing_placeholders_status_test_fixtures_only
scoped_docs_source_tests_scan=no_real_secret_values_found_status_placeholders_test_fixtures_only
transcript_text_delta_scan=no_new_transcript_text_or_delta_content_added
audio_binary_artifact_scan=none_added
```

## Phase B Controlled Smoke Result

Approval phrase received exactly:

```text
APPROVE NODE-032AG PHASE B LIVE SMOKE
```

Immediate hard gates were re-confirmed before helper staging, token handling, temp env creation, Gateway service start, or smoke.

```text
asterisk_ssh=reachable
asterisk_service=active_enabled
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
gateway_ssh=reachable
gateway_service_before_smoke=inactive_disabled
gateway_unit_verify=OK
target_listeners_443_8080_8081_before_smoke=absent
ufw=active_default_deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_secret_presence=MASKED_PRESENT
realtime_gateway_marker_hash=valid
realtime_measurement_symbol_hash=valid
```

Exactly one Asterisk-side non-business-dialog smoke invocation ran.

```text
local_helper_bundle_validate=ok
remote_helper_bundle_validate=ok
smoke_audio=24000Hz_mono_16bit_PCM
safe_temp_env_create=ok
safe_temp_env_validate=ok
token_source=Gateway_env_piped_to_guard_stdin_only
token_values_printed=false
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
openai_event_type_counts=conversation.item.added:1,conversation.item.done:1,conversation.item.input_audio_transcription.completed:1,input_audio_buffer.committed:1,session.created:1,session.updated:1
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
accepted_reason=gateway_stt_dialog_use_disabled
```

The result verifies the deployed Gateway runtime diagnostics propagation path. It is not business-dialog integration proof, production autostart, transcript text correctness acceptance, or transcript-quality acceptance.

## Phase B Final Safe State

```text
gateway_service_final=inactive_disabled
gateway_target_listeners_443_8080_8081=absent
gateway_firewall=unchanged_source_restricted
gateway_env_metadata=root:gateway 640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
temporary_helper_env_audio_removed=true
local_temporary_helper_bundle_removed=true
smoke_invocations=1
systemctl_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
```

## Next Boundary Recommendation

```text
NODE-032AH / transcript-event-diagnostics-smoke-acceptance-and-next-boundary-decision
```

## Safety

Phase A did not run smoke, run a test call, deploy helpers, handle tokens, create temp env files, start/stop/restart/reload/enable services, install dependencies, reboot, power-cycle, change firewall, edit server env, log transcript text/deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

Phase B ran exactly one approved controlled Asterisk-side non-business-dialog smoke. No token values or transcript text were printed, committed, or logged. No business-dialog transcript use, Gateway STT default enablement, `systemctl enable`, dependency install, reboot, power-cycle, firewall broadening, persistent env change, TLS/proxy/443/8081 change, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
