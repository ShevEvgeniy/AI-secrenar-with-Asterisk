# NODE-032AF / controlled-gateway-runtime-measurement-dependency-rollout Handoff

Date: 2026-06-07

Branch: `feat/node-032af-controlled-gateway-runtime-measurement-dependency-rollout`

Phase: Phase A only - read-only deployed Gateway runtime dependency inventory and gate checks.

Base master HEAD: `d2bd0087dde74ba59e2f6f6b6f40533f7bfa64a3`

Future Phase B approval phrase:

```text
APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
```

## Context

NODE-032AE failed before smoke helper invocation because Gateway service readiness hit an import error:

```text
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
smoke_helper_invoked=false
gateway_request_reached=false
```

## Local Inventory

```text
path=src/ai_secretary/stt/realtime_measurement.py
sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
size=25609
symbol_diagnose_pcm_wav_audio_bytes=present
symbol_lines=244,251
```

## Asterisk Read-Only Gates

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service=active_enabled
main_pid=3797
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
target_listeners_443_8080_8081=absent
```

## Gateway Read-Only Gates

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
ai-secretary-gateway.service=inactive_disabled
unit_verify=OK
target_listeners_443_8080_8081=absent
ufw=active_default_deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
deployed_realtime_gateway_marker_openai_event_type_counts_available=present
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
```

## Deployed Dependency Inventory

```text
path=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
metadata=root:root 664 20054 2026-05-13 16:19:11 +0000
sha256=51626eda7f8c74a557398312e1d0e6e9b6fd8a008c24c6a92a9365a99f9f3bcf
symbol_diagnose_pcm_wav_audio_bytes=absent
def_diagnose_pcm_wav_audio_bytes=absent
```

Comparison:

```text
local_symbol_present=true
deployed_symbol_present=false
local_deployed_hash_match=false
deployed_runtime_dependency_stale_or_missing=true
```

## Backup / Rollback Feasibility

```text
backup_dir=/opt/ai-secretary-gateway/backups
backup_dir_exists=true
backup_dir_metadata=root:root 755
backup_created=false
```

Future rollback concept: back up the current deployed `realtime_measurement.py`, roll out only the repo version after exact approval, verify symbol/hash, and restore the backup if verification fails. Preserve Gateway env and firewall, and keep the service disabled unless hard gates show a different preexisting state.

## Phase A Decision

```text
phase_a_result=complete
phase_b_rollout_can_be_requested=true
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
blocker_for_smoke=deployed_realtime_measurement_py_lacks_required_symbol
next_action=controlled_measurement_dependency_rollout
```

Phase B should be a controlled dependency rollout, not a smoke node unless separately approved.

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

## Safety Confirmations

```text
deploy=false
server_file_copy=false
server_file_edit=false
server_backup_created=false
live_smoke=false
test_call=false
helper_deploy=false
token_handling=false
token_values_printed=false
temp_env_created=false
service_start_stop_restart_reload_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
transcript_text_logged=false
transcript_delta_logged=false
business_dialog_transcript_use=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Phase B Rollout Result

Approval phrase acknowledged exactly:

```text
APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
```

Immediate hard gates were re-confirmed before state change:

```text
asterisk_ssh_reachable=true
asterisk_service=active_enabled
asterisk_OPENAI_API_KEY_process=ABSENT
asterisk_OPENAI_API_KEY_service_env=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
gateway_ssh_reachable=true
gateway_service=inactive_disabled
gateway_unit_verify=OK
target_listeners_443_8080_8081=absent
ufw=active_default_deny_8080_from_92.118.85.117_only
gateway_env_metadata=root:gateway 640
gateway_masked_secret_presence=passed
realtime_gateway_marker_hash_valid=true
pre_rollout_realtime_measurement_symbol=absent
```

Backup:

```text
backup_dir=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z
backup_file=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z/realtime_measurement.py
backup_sha256=51626eda7f8c74a557398312e1d0e6e9b6fd8a008c24c6a92a9365a99f9f3bcf
```

Rollout:

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
updated_file_metadata=root:root 664 25609 2026-06-07 19:15:45 +0000
deployed_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
local_deployed_hash_match=true
diagnose_pcm_wav_audio_bytes=present
def_diagnose_pcm_wav_audio_bytes=present
temporary_upload_removed=true
```

Final state:

```text
service_action_performed=false
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall_unchanged=true
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
realtime_gateway_marker_present=true
realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
asterisk_OPENAI_API_KEY_process=ABSENT
asterisk_OPENAI_API_KEY_service_env=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
```

Rollback plan:

```text
restore_from=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z/realtime_measurement.py
restore_to=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
preserve_env_and_firewall=true
keep_service_disabled=true
verify_hash_symbol_and_final_listeners_after_restore=true
```

No smoke, test call, transcript logging, token output, raw env dump, business-dialog transcript use, Gateway STT default enablement, production autostart, `systemctl enable`, dependency install, reboot, power-cycle, firewall broadening, persistent env change, TLS/proxy/443/8081 change, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.
