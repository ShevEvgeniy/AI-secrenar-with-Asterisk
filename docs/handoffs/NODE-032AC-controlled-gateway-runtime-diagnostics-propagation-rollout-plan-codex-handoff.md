# NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan

## Handoff

This handoff records local repository analysis and planning only. It intentionally excludes real secrets, token values, bearer headers, raw secret env output, transcript text, transcript deltas, audio, binary artifacts, and large logs.

## Base

```text
branch=feat/node-032ac-controlled-gateway-runtime-diagnostics-propagation-rollout-plan
base_master_head=43f1fb69d45e3cb775ee0afc0e237ed3776bdf74
latest_closed_node=NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix
node_scope=repo_local_planning_only
```

## NODE-032AB Result Preserved

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

Diagnostics remained blocked:

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

## Analysis Summary

Local code path that produces the marker:

```text
src/ai_secretary/stt/realtime_gateway.py
function=_build_response_diagnostics
field=openai_event_type_counts_available
value=true
```

Local code path that reports the marker:

```text
src/ai_secretary/stt/gateway_adapter_smoke.py
function=build_report
source=result.details
report_field=openai_event_type_counts_available
```

Helper bundle:

```text
script=scripts/asterisk_gateway_helper_bundle.py
includes_realtime_gateway_py=true
includes_gateway_adapter_smoke_py=true
includes_gateway_adapter_py=true
includes_temp_env_guard=true
```

Live Gateway service runtime boundary:

```text
service=ai-secretary-gateway.service
working_directory=/opt/ai-secretary-gateway
pythonpath=/opt/ai-secretary-gateway/src
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
```

Because NODE-032AB used the current repo helper bundle on Asterisk but the Gateway HTTP response still lacked `openai_event_type_counts_available`, the likely blocked boundary is the deployed Gateway runtime code or Gateway HTTP response mapping, not the Asterisk helper report parser.

## Required Questions

1. Which code path produced `openai_event_type_counts_available` locally?

```text
src/ai_secretary/stt/realtime_gateway.py::_build_response_diagnostics
```

2. Which code path was actually used by NODE-032AB live smoke?

```text
Asterisk helper/report path=current repo bundle from NODE-032AB branch
Gateway response path=deployed service runtime under /opt/ai-secretary-gateway/src
```

3. Does the live Gateway service runtime need a code rollout before the marker can appear?

```text
likely_yes
reason=helper bundle was current, but Gateway response still lacked marker
```

4. Does the helper bundle include the updated diagnostics parser/report mapping?

```text
yes
bundle_manifest_includes=src/ai_secretary/stt/gateway_adapter_smoke.py,src/ai_secretary/stt/realtime_gateway.py,src/ai_secretary/stt/gateway_adapter.py
```

5. Could the Asterisk-side report still be using an older helper/report schema?

```text
unlikely_for_NODE_032AB
reason=remote helper bundle was staged from current repo and preflighted before the smoke
remaining_risk=copy/preflight did not compare file hashes against repo; future rollout should add safe hash/version checks
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
asterisk_OPENAI_API_KEY_absent
business_dialog_gateway_transcript_not_enabled
transcript_text_logging_not_enabled
gateway_service_inactive_disabled_before_apply_or_current_state_documented
gateway_env_metadata_root_gateway_640
masked_gateway_secret_presence_passes
no_target_listeners_443_8080_8081
ufw_active_default_deny_8080_from_92.118.85.117_only
backup_or_manifest_for_current_deployed_gateway_code
rollback_commands_accepted
```

9. What are the post-deploy read-only checks?

```text
deployed_realtime_gateway_contains_openai_event_type_counts_available_marker
deployed_gateway_adapter_smoke_contains_marker_mapping_if_used
systemd_unit_still_uses_expected_workdir_pythonpath_env
service_can_start_for_readiness_only_if_approved
service_remains_disabled_unless separately approved
no_443_or_8081_listener
ufw_8080_source_restricted
log_redaction_checks_no_token_or_transcript_text
```

10. What is the rollback plan?

```text
stop_service_if_started
restore_previous_deployed_gateway_files_from_backup_or_previous_release
preserve_gateway_env_values
keep_firewall_unchanged
verify_service_inactive_disabled_if final state requires
verify_no_target_listeners
verify_asterisk_OPENAI_API_KEY_absent
rotate_tokens_if exposure occurs
```

11. What is the next smoke acceptance criterion after rollout?

```text
openai_event_type_counts_available=true
diagnostic_propagation_gap=false_when_event_counts_field_is_present_even_if_empty
token_values_printed=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent_positive
```

## Selected Next Node

```text
NODE-032AD / controlled-gateway-runtime-diagnostics-propagation-rollout
```

NODE-032AD should be a controlled runtime propagation node, not a blind smoke retry. It should inventory the deployed Gateway runtime, compare safe file/hash/version evidence against the repo, back up current deployed files, apply only the diagnostics runtime update after exact approval, verify the deployed marker exists, and leave smoke to a separate follow-up unless the operator explicitly scopes one.

Suggested approval phrase:

```text
APPROVE NODE-032AD GATEWAY RUNTIME DIAGNOSTICS ROLLOUT
```

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
