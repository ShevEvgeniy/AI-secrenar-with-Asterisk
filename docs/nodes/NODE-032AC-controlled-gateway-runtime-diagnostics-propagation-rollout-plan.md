# NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan

## Goal

Analyze and document the controlled rollout boundary required to propagate the NODE-032AA diagnostics change into the live Gateway runtime path.

NODE-032AC is repo-local planning only. It is not a live-smoke node and not a deploy node.

## Base

```text
base_master_head=43f1fb69d45e3cb775ee0afc0e237ed3776bdf74
latest_closed_node=NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix
branch=feat/node-032ac-controlled-gateway-runtime-diagnostics-propagation-rollout-plan
```

## NODE-032AB Result

NODE-032AB ran one controlled Asterisk-side non-business-dialog smoke after exact approval:

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
adapter_default_enabled_after_smoke=false
```

The diagnostic marker added in NODE-032AA did not appear in live smoke evidence:

```text
openai_event_type_counts_available=false
openai_event_type_counts_present=false
openai_event_type_counts={}
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

Interpretation:

```text
transport_auth_openai_realtime_success=true
diagnostic_propagation_fix_live_verified=false
transcript_presence_success=false
business_dialog_integration_success=false
production_autostart_success=false
```

## Local Code Path

The local Gateway code produces the marker in:

```text
src/ai_secretary/stt/realtime_gateway.py
function=_build_response_diagnostics
field=openai_event_type_counts_available
value=true
```

The marker is included in Gateway responses produced by `build_gateway_response(...)`.

The Asterisk-side smoke report reads diagnostics from Gateway result details in:

```text
src/ai_secretary/stt/gateway_adapter_smoke.py
function=build_report
```

Report behavior:

```text
openai_event_type_counts_available=true when result.details contains openai_event_type_counts as a dict
openai_event_type_counts_available=false when the field is missing/not propagated
diagnostic_propagation_gap=true when diagnostics are missing/not propagated
```

## Helper Bundle Path

The helper bundle manifest includes the current repo files needed for the Asterisk-side smoke and report parser:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/gateway_smoke_temp_env_guard.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
```

Therefore, the NODE-032AB Asterisk-side helper/report parser was expected to use current repo code. The live Gateway response still lacked the marker, so the most likely gap is not the Asterisk report schema.

## Live Gateway Runtime Path

The persistent Gateway service path documented in prior nodes is:

```text
service=ai-secretary-gateway.service
unit=/etc/systemd/system/ai-secretary-gateway.service
working_directory=/opt/ai-secretary-gateway
pythonpath=/opt/ai-secretary-gateway/src
env_file=/etc/ai-secretary/openai-realtime-gateway.env
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
```

NODE-032AB started the Gateway service only for smoke readiness. That service executes the deployed Gateway runtime under `/opt/ai-secretary-gateway/src`, not the temporary Asterisk helper bundle.

## Root Cause Assessment

Likely root cause:

```text
deployed_gateway_runtime_does_not_include_NODE_032AA_diagnostics_marker=true
```

Alternative still possible:

```text
gateway_runtime_has_marker_but_response_mapping_or_runtime_reload_boundary_failed=true
```

Rejected as primary cause:

```text
asterisk_helper_schema_stale=false
```

Reason: NODE-032AB staged a current repo helper bundle on Asterisk, and that bundle includes `gateway_adapter_smoke.py` with the updated diagnostic report mapping.

## Required Analysis Questions

1. Which code path produced `openai_event_type_counts_available` locally?

```text
src/ai_secretary/stt/realtime_gateway.py::_build_response_diagnostics
```

2. Which code path was actually used by NODE-032AB live smoke?

```text
Gateway HTTP response=deployed Gateway service under /opt/ai-secretary-gateway/src
Asterisk smoke parser=current repo helper bundle staged under temporary Asterisk path
```

3. Does the live Gateway service runtime need a code rollout before the marker can appear?

```text
likely_yes
```

4. Does the helper bundle include the updated diagnostics parser/report mapping?

```text
yes
```

5. Could the Asterisk-side report still be using an older helper/report schema?

```text
unlikely_for_NODE_032AB
future_preflight_should_add_hash_or_version_checks=true
```

6. Is the Gateway HTTP response contract documented with `openai_event_type_counts_available`?

```text
yes
doc=docs/stt_gateway_protocol.md
```

7. What exact future node should safely roll out runtime changes?

```text
NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
```

8. What are the pre-deploy gates?

```text
asterisk_ssh_reachable
gateway_ssh_reachable
asterisk_OPENAI_API_KEY_absent_in_service_and_process_env
business_dialog_gateway_transcript_not_enabled
transcript_text_logging_not_enabled
gateway_service_state_recorded
gateway_env_metadata_root_gateway_640
masked_gateway_secret_presence_passes
no_unexpected_listeners_on_443_8080_8081_before_apply
ufw_active_default_deny_8080_from_92.118.85.117_only
deployed_runtime_inventory_collected_without_secret_values
backup_plan_ready
rollback_commands_accepted
```

9. What are the post-deploy read-only checks?

```text
deployed_realtime_gateway_py_contains_openai_event_type_counts_available
deployed_gateway_adapter_smoke_py_contains_marker_mapping_if_used
systemd_unit_still_points_to_expected_workdir_pythonpath_env
service_state_matches_scope
no_unexpected_443_or_8081_listener
ufw_8080_still_source_restricted
logs_do_not_contain_token_values_or_transcript_text
```

10. What is the rollback plan?

```text
stop_service_if_started
restore_previous_deployed_gateway_files_from_backup
preserve_gateway_env_values
keep_firewall_unchanged
verify_service_inactive_disabled_if_final_state_requires
verify_no_target_listeners
verify_asterisk_OPENAI_API_KEY_absent
rotate_tokens_if_exposure_occurs
```

11. What is the next smoke acceptance criterion after rollout?

```text
openai_event_type_counts_available=true
diagnostic_propagation_gap=false_when_openai_event_type_counts_field_is_present_even_if_empty
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent_positive
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
token_values_printed=false
```

## Next Node

Selected next node:

```text
NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
```

Suggested approval phrase:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

NODE-032AD must not be a blind smoke retry. It should:

1. Run Phase A read-only inventory of the deployed Gateway runtime.
2. Compare safe deployed file hashes or marker checks with the repo.
3. Back up current deployed Gateway runtime files before any write.
4. Apply only the diagnostics runtime update after exact approval.
5. Re-check the systemd unit path, env metadata, UFW, and listener safety.
6. Leave business-dialog transcript use disabled.
7. Leave transcript text logging disabled.
8. Avoid smoke unless explicitly scoped; a follow-up smoke node can verify the marker after rollout.

## Validation

```text
focused_suite=50_passed
full_suite=234_passed_6_failed
full_suite_known_environmental_failures=missing_src_scripts_make_demo_audio_py,missing_sentence_transformers
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found_existing_placeholders_status_test_fixtures_only
scoped_docs_handoff_source_test_scan=no_real_secret_values_found_status_placeholders_only
audio_binary_artifact_scan=none_added
```

## Safety

NODE-032AC performed:

```text
live_smoke=false
ssh=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_env_server_change=false
business_dialog_enablement=false
transcript_text_logging=false
transcript_delta_logging=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Handoff

```text
docs/handoffs/NODE-032AC-controlled-gateway-runtime-diagnostics-propagation-rollout-plan-codex-handoff.md
```
