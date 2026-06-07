# NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout

## Handoff

This handoff records Phase A read-only runtime inventory and rollout planning only. It excludes real secrets, token values, raw secret env output, transcript text, transcript deltas, audio, binary artifacts, large logs, Notion writes, and Runtime/Evidence updates.

## Base

```text
branch=feat/node-032ad-controlled-gateway-runtime-diagnostics-propagation-rollout
base_master_head=5ab96a13606be858d4b446dba87eefece0a76d1b
latest_closed_node=NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
phase=Phase A read-only inventory
phase_b_approval_phrase=APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

## Local Repo Evidence

```text
local_realtime_gateway_marker_present=true
local_realtime_gateway_marker_line=src/ai_secretary/stt/realtime_gateway.py:398
local_gateway_adapter_smoke_marker_present=true
local_gateway_adapter_smoke_marker_lines=src/ai_secretary/stt/gateway_adapter_smoke.py:48,169
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
local_gateway_adapter_smoke_sha256=F81AAC6BD6392D88C68B97065683702ACD645C20F5871F69D96756C6BCD1B98C
```

## Asterisk Read-Only Gates

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

Safe redacted env inspection printed only non-secret settings and redacted key/token-like fields. No token values were printed.

## Gateway Read-Only Gates

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
whoami=root
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
systemd_unit_verify=ok
gateway_env_metadata=root:gateway 640 /etc/ai-secretary/openai-realtime-gateway.env
gateway_OPENAI_API_KEY=masked_present
gateway_GATEWAY_TOKEN=masked_present
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_tcp=allowed_only_from_92.118.85.117
```

Gateway unit evidence:

```text
unit=/etc/systemd/system/ai-secretary-gateway.service
user=gateway
group=gateway
working_directory=/opt/ai-secretary-gateway
pythonpath=/opt/ai-secretary-gateway/src
env_file=/etc/ai-secretary/openai-realtime-gateway.env
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
restart=on-failure
```

## Deployed Runtime Inventory

```text
gateway_root=/opt/ai-secretary-gateway
gateway_root_metadata=root:root 755
gateway_src=/opt/ai-secretary-gateway/src
gateway_src_metadata=root:root 775
deployed_realtime_gateway=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
deployed_realtime_gateway_metadata=root:root 664 15866 2026-05-13 16:19:11 +0000
deployed_realtime_gateway_marker_present=false
deployed_realtime_gateway_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
deployed_gateway_adapter_smoke_present=false
deployed_gateway_adapter_smoke_marker_present=false
```

Comparison:

```text
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
deployed_realtime_gateway_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
hashes_match=false
deployed_runtime_appears_stale=true
node032ab_diagnostic_gap_explained=true
```

## Backup / Rollback Feasibility

No backup was created in Phase A.

Read-only feasibility:

```text
backup_parent=/opt/ai-secretary-gateway
backup_parent_exists=true
backup_parent_writable_as_root=true
```

Phase B should create a timestamped backup of the deployed runtime file(s) before any write, then verify backup metadata without printing secrets.

Rollback plan:

```text
stop_service_if_started
restore_previous_deployed_realtime_gateway_py_from_backup
preserve_gateway_env_values
keep_firewall_unchanged
verify_service_inactive_disabled_if_final_state_requires
verify_no_target_listeners_443_8080_8081
verify_asterisk_OPENAI_API_KEY_absent
rotate_tokens_only_if_exposure_occurs
```

## Phase B Readiness

Phase B rollout can be requested after the exact approval phrase.

Current blockers:

```text
phase_b_approval_phrase_absent=true
deployed_realtime_gateway_missing_marker=true
deployed_realtime_gateway_hash_differs_from_repo=true
```

These blockers are the reason for NODE-032AD Phase B, not a NO-GO against requesting it. Hard gates must be re-run immediately before any state-changing command.

## Phase B Boundary

Allowed only after exact approval:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Recommended Phase B scope:

```text
reconfirm_asterisk_and_gateway_hard_gates
backup_current_deployed_realtime_gateway_py
deploy_repo_realtime_gateway_py_to_gateway_runtime_path_only
preserve_env_file_and_values
do_not_enable_service
start_service_only_if explicitly approved for readiness within Phase B
verify_deployed_marker_presence
verify_hash_matches_expected_repo_file
verify_unit_paths_unchanged
verify_firewall_unchanged
verify_no_secret_or_transcript_text_output
document final state and rollback path
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
transcript_text_or_delta_logging
```

## Phase B Result

Approval phrase confirmed exactly:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

Immediate hard gates re-confirmed before rollout:

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

Backup created:

```text
backup_dir=/opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z
backup_file=/opt/ai-secretary-gateway/backups/node032ad-20260607T140434Z/realtime_gateway.py
backup_file_metadata=root:root 664 15866 2026-05-13 16:19:11 +0000
backup_file_sha256=6b9eecd32ab15eb1a35344663ea67f589ad6fb86db663717e2819d4cec731199
```

Rollout applied:

```text
updated_file=/opt/ai-secretary-gateway/src/ai_secretary/stt/realtime_gateway.py
updated_file_metadata=root:root 664 21922 2026-06-07 14:05:26 +0000
deployed_realtime_gateway_sha256=a1ba9d06be574f7559bd5e8805359385c15de21d587bf009a345c24a52373a85
local_realtime_gateway_sha256=A1BA9D06BE574F7559BD5E8805359385C15DE21D587BF009A345C24A52373A85
local_deployed_hash_match=true
openai_event_type_counts_available_marker_present=true
marker_line=398
temporary_upload_removed=true
```

Service action:

```text
service_start_stop_restart_reload_enable=false
systemctl_enable=false
live_smoke=false
```

Final state:

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
business_dialog_enablement=false
transcript_text_logging=false
transcript_delta_logging=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```
