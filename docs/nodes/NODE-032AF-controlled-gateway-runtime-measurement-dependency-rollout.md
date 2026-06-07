# NODE-032AF / controlled-gateway-runtime-measurement-dependency-rollout

Date: 2026-06-07

Branch: `feat/node-032af-controlled-gateway-runtime-measurement-dependency-rollout`

Phase: Phase A - read-only deployed Gateway runtime dependency inventory and gate checks.

## Goal

Inventory the deployed Gateway `realtime_measurement.py` dependency after NODE-032AE failed service readiness with an import error, then decide whether a controlled dependency rollout can be requested.

Phase B is not approved in this node.

Future approval phrase:

```text
APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
```

## NODE-032AE Context

NODE-032AE confirmed deployed `realtime_gateway.py` had the diagnostics marker and expected hash, but Gateway service readiness failed before smoke helper invocation.

```text
missing_symbol=diagnose_pcm_wav_audio_bytes
missing_symbol_module=ai_secretary.stt.realtime_measurement
smoke_helper_invoked=false
gateway_request_reached=false
smoke_ran=false
```

## Local Dependency Inventory

```text
path=src/ai_secretary/stt/realtime_measurement.py
sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
size=25609
symbol_diagnose_pcm_wav_audio_bytes=present
symbol_reference_line=244
symbol_definition_line=251
```

## Asterisk Read-Only Gates

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service_active=true
ai-secretary-ari.service_enabled=true
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
deployed_realtime_gateway_marker_openai_event_type_counts_available=present
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
```

No secret env values were printed.

## Deployed Measurement Dependency Inventory

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

Conclusion: the deployed Gateway `realtime_gateway.py` matches the NODE-032AD rollout hash and contains `openai_event_type_counts_available`, but its deployed `realtime_measurement.py` dependency is stale relative to the repo and lacks the symbol required by the updated Gateway runtime.

## Backup / Rollback Feasibility

```text
backup_dir=/opt/ai-secretary-gateway/backups
backup_dir_exists=true
backup_dir_metadata=root:root 755
backup_created=false
```

Future Phase B rollback concept:

```text
backup_current_deployed_realtime_measurement_py
roll_out_only_repo_realtime_measurement_py
verify_symbol_presence
verify_deployed_hash_matches_repo
restore_backup_if_verification_fails
preserve_gateway_env
preserve_firewall
keep_service_disabled_unless_preexisting_state_differs
```

## Phase A Decision

```text
phase_a_result=complete
phase_b_rollout_can_be_requested=true
phase_b_condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
primary_blocker=deployed_realtime_measurement_py_lacks_diagnose_pcm_wav_audio_bytes
```

Phase B should be a controlled Gateway runtime measurement dependency rollout, not a live smoke. Smoke remains a later boundary after the deployed dependency is updated and verified.

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

## Safety

Phase A did not deploy, copy files, edit server files, create backups, run smoke, run test calls, deploy helper bundles, handle tokens, create temp env files, start/stop/restart/reload/enable services, install dependencies, reboot, power-cycle, change firewall, edit env files, change server state, log transcript text/deltas, enable business-dialog transcript use, write Notion, update Runtime/Evidence, or add scheduler/webhook/automation.

Known untracked local artifacts remain untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Phase B Rollout

Approval phrase acknowledged exactly:

```text
APPROVE NODE-032AF GATEWAY MEASUREMENT DEPENDENCY ROLLOUT
```

Immediate hard-gate re-check:

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
realtime_gateway_marker_present=true
realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
pre_rollout_realtime_measurement_symbol=absent
```

Backup:

```text
backup_dir=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z
backup_file=/opt/ai-secretary-gateway/backups/node032af-20260607T191545Z/realtime_measurement.py
backup_sha256=51626eda7f8c74a557398312e1d0e6e9b6fd8a008c24c6a92a9365a99f9f3bcf
```

Rollout result:

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_measurement.py
updated_file_metadata=root:root 664 25609 2026-06-07 19:15:45 +0000
deployed_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
expected_local_sha256=9848ccd75730ded3d649fb34bbd308554dce18ceb438ed4a63fac77e51d8fb90
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
realtime_gateway_marker_hash_still_valid=true
asterisk_OPENAI_API_KEY=ABSENT
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

NODE-032AF Phase B was not a smoke node. No smoke ran.
