# NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout

## Goal

Inventory the deployed Gateway runtime and determine whether the NODE-032AA safe diagnostics marker is absent from the live service path.

Phase A is read-only inventory and gate checks only. Phase B is not approved.

Exact Phase B approval phrase:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Any other phrase is not approval.

## Base

```text
branch=feat/node-032ad-controlled-gateway-runtime-diagnostics-propagation-rollout
base_master_head=5ab96a13606be858d4b446dba87eefece0a76d1b
latest_closed_node=NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
phase=Phase A read-only inventory
```

NODE-032AC conclusion:

```text
local_repo_realtime_gateway_adds_openai_event_type_counts_available=true
asterisk_helper_bundle_parser_current=true
live_gateway_service_uses_separate_deployed_runtime=true
live_gateway_runtime_path=/opt/ai-secretary-gateway/src
likely_root_cause=deployed_gateway_runtime_or_response_mapping_not_updated_or_reloaded
```

## Local Repo Marker Evidence

Local marker presence:

```text
src/ai_secretary/stt/realtime_gateway.py:398:"openai_event_type_counts_available": True
src/ai_secretary/stt/gateway_adapter_smoke.py:48:"openai_event_type_counts_available": diagnostics["openai_event_type_counts_available"]
src/ai_secretary/stt/gateway_adapter_smoke.py:169:"openai_event_type_counts_available": counts_available
```

Local safe hashes:

```text
src/ai_secretary/stt/realtime_gateway.py_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
src/ai_secretary/stt/gateway_adapter_smoke.py_sha256=F81AAC6BD6392D88C68B97065683702ACD645C20F5871F69D96756C6BCD1B98C
```

## Asterisk Read-Only Findings

```text
ssh_reachable=true
hostname=tula
whoami=root
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_OPENAI_API_KEY=absent
service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
ari_env_metadata=root:tulauser 640 /etc/ai-secretary/ari-app.env
target_listeners_443_8080_8081=absent
```

Notes:

```text
redacted_env_flags_checked=true
secret_values_printed=false
transcript_text_printed=false
```

The Asterisk listener inventory showed `8088`, `7077`, `22`, and local DNS/container listeners, with no `443`, `8080`, or `8081`.

## Gateway Read-Only Findings

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
whoami=root
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
systemd_analyze_verify=ok
gateway_env_metadata=root:gateway 640 /etc/ai-secretary/openai-realtime-gateway.env
gateway_OPENAI_API_KEY=masked_present
gateway_GATEWAY_TOKEN=masked_present
target_listeners_443_8080_8081=absent
ufw_active=true
ufw_default_incoming=deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
```

Gateway unit evidence:

```text
unit_path=/etc/systemd/system/ai-secretary-gateway.service
user=gateway
group=gateway
working_directory=/opt/ai-secretary-gateway
pythonpath=/opt/ai-secretary-gateway/src
env_file=/etc/ai-secretary/openai-realtime-gateway.env
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
restart=on-failure
```

The Gateway listener inventory showed only SSH and local DNS listeners, with no `443`, `8080`, or `8081`.

## Deployed Runtime Inventory

```text
gateway_root=/opt/ai-secretary-gateway
gateway_root_metadata=root:root 755
gateway_src=/opt/ai-secretary-gateway/src
gateway_src_metadata=root:root 775
deployed_realtime_gateway=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
deployed_realtime_gateway_metadata=root:root 664 15866 2026-05-13 16:19:11 +0000
deployed_gateway_adapter_smoke=/opt/ai-secretary-gateway/src/ai_secretary/stt/gateway_adapter_smoke.py
deployed_gateway_adapter_smoke_present=false
```

Marker inventory:

```text
deployed_realtime_gateway_openai_event_type_counts_available_marker=false
deployed_gateway_adapter_smoke_openai_event_type_counts_available_marker=false
```

Deployed hash:

```text
deployed_realtime_gateway_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
```

## Local vs Deployed Comparison

```text
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
deployed_realtime_gateway_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
hashes_match=false
local_marker_present=true
deployed_marker_present=false
deployed_gateway_adapter_smoke_present=false
deployed_runtime_appears_stale=true
```

Conclusion:

```text
node032ab_diagnostic_propagation_gap_explained=true
phase_b_rollout_target=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
```

The live Gateway service runtime lacks the NODE-032AA marker, so another smoke without runtime rollout would likely repeat the diagnostic propagation gap.

## Backup / Rollback Feasibility

No backup was created in Phase A.

Read-only feasibility:

```text
backup_parent=/opt/ai-secretary-gateway
backup_parent_exists=true
backup_parent_writable_as_root=true
```

Phase B should create a timestamped backup before any write, then verify backup metadata without printing secrets.

Rollback plan:

```text
stop_gateway_service_if_started
restore_previous_realtime_gateway_py_from_backup
preserve_gateway_env_values
keep_firewall_unchanged
leave_service_disabled_unless separately approved
verify_no_target_listeners_443_8080_8081_if_final_state_inactive
verify_asterisk_OPENAI_API_KEY_absent
rotate_tokens_only_if_exposure_occurs
```

## Phase B Readiness

Phase B rollout can be requested after exact approval.

Current blockers before Phase B execution:

```text
exact_phase_b_approval_phrase_absent=true
hard_gates_must_be_reconfirmed_immediately_before_any_state_change=true
```

Runtime evidence requiring Phase B:

```text
deployed_realtime_gateway_missing_openai_event_type_counts_available=true
deployed_realtime_gateway_hash_differs_from_repo=true
```

These are rollout targets, not NO-GO blockers for requesting Phase B.

## Phase B Plan

After the exact approval phrase only:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Recommended command boundary:

```text
reconfirm_asterisk_hard_gates_read_only
reconfirm_gateway_hard_gates_read_only
record_pre_change_deployed_runtime_stat_and_hash
create_timestamped_backup_of_deployed_realtime_gateway_py
copy_repo_realtime_gateway_py_to_deployed_runtime_path
preserve_owner_mode_or_set_to_documented_runtime_safe_metadata
verify_deployed_marker_present
verify_deployed_hash_matches_repo_expected_hash
verify_systemd_unit_paths_unchanged
verify_gateway_env_metadata_unchanged
verify_ufw_unchanged_and_8080_source_restricted
do_not_run_smoke_unless separately approved
document final state_and_rollback_path
```

Explicit exclusions:

```text
live_smoke
helper_deploy
token_handling
server_temp_env
systemctl_enable
dependency_install
reboot_or_power_cycle
firewall_change
server_env_edit
tls_proxy_443_8081_changes
business_dialog_enablement
transcript_text_logging
transcript_delta_logging
production_autostart
```

## Phase B Result

Approval phrase confirmed exactly:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Immediate hard gates re-confirmed before state-changing commands:

```text
asterisk_ssh_reachable=true
asterisk_service_active=active
asterisk_service_enabled=enabled
asterisk_process_OPENAI_API_KEY=absent
asterisk_service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
asterisk_target_listeners_443_8080_8081=absent
gateway_ssh_reachable=true
gateway_service_active_before=inactive
gateway_service_enabled_before=disabled
gateway_unit_verify=ok
gateway_target_listeners_443_8080_8081_before=absent
ufw_active=true
ufw_default_incoming=deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
gateway_masked_secret_presence=passed
```

Backup created before rollout:

```text
backup_dir=/opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z
backup_file=/opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z/realtime_gateway.py
backup_file_metadata=root:root 664 15866 2026-05-13 16:19:11 +0000
backup_file_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
```

Deployed files updated:

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
updated_file_only=true
```

Post-rollout deployed evidence:

```text
updated_file_metadata=root:root 664 21922 2026-06-07 14:05:26 +0000
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
local_deployed_hash_match=true
openai_event_type_counts_available_marker_present=true
marker_line=398
temporary_upload_removed=true
```

Service action:

```text
service_started=false
service_stopped=false
service_restarted=false
service_reloaded=false
service_enabled=false
live_smoke=false
```

Final safety state:

```text
gateway_service_active=inactive
gateway_service_enabled=disabled
gateway_target_listeners_443_8080_8081=absent
ufw_unchanged=true
ufw_8080_tcp=allowed_only_from_92.118.85.117
gateway_env_metadata=root:gateway 640
asterisk_process_OPENAI_API_KEY=absent
asterisk_service_env_OPENAI_API_KEY=absent
business_dialog_gateway_transcript_flag=not_enabled
transcript_text_logging_flag=not_enabled
```

Rollback path:

```text
cp -a /opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z/realtime_gateway.py /opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
preserve_gateway_env_values
keep_firewall_unchanged
leave_service_disabled_unless_separately_approved
verify_no_target_listeners_if_service_inactive
verify_asterisk_OPENAI_API_KEY_absent
rotate_tokens_only_if_exposure_occurs
```

Next recommended node:

```text
NODE-032AE / controlled-gateway-diagnostics-marker-smoke-after-runtime-rollout
```

## Next Smoke Acceptance After Rollout

A later smoke node, after runtime rollout, should require:

```text
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent_positive=true
openai_event_type_counts_available=true
diagnostic_propagation_gap=false_when_openai_event_type_counts_field_is_present_even_if_empty
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
token_values_printed=false
```

It should not require transcript-quality success, business-dialog integration, or production autostart.

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

## Handoff

```text
docs/handoffs/NODE-032AD-controlled-gateway-runtime-diagnostics-propagation-rollout-codex-handoff.md
```

## Safety

NODE-032AD Phase A performed:

```text
deploy=false
server_file_edit=false
server_backup_created=false
live_smoke=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_start_stop_restart_reload_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
tls_proxy_change=false
business_dialog_enablement=false
transcript_text_logging=false
transcript_delta_logging=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
