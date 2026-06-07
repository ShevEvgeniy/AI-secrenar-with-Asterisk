# NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix

## Phase A Handoff

This handoff records Phase A read-only readiness and command planning only.

Do not include real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, transcript deltas, raw logs, audio, or binary artifacts in this file.

## Base

```text
branch=feat/node-032ab-controlled-transcript-event-diagnostics-smoke-after-propagation-fix
base_master_head=43c8ec3b658cc63874ebeb4207c36ea881e62a13
latest_closed_node=NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
phase=Phase A read-only gates and planning
```

NODE-032AA added:

```text
openai_event_type_counts_available
```

The marker separates empty-but-propagated event-count diagnostics from missing/unpropagated diagnostics.

## Safety Boundary

```text
live_smoke=false
test_call=false
helper_deploy=false
token_handling=false
token_values_printed=false
server_temp_env_created=false
service_start_stop_restart_reload_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
production_autostart=false
transcript_text_logging=false
transcript_delta_logging=false
business_dialog_transcript_use=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Phase B Approval Boundary

Phase B is not approved in Phase A. The only approval phrase for a future live smoke is:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

Any other phrase is not approval.

## Local Repo Findings

```text
current_branch=feat/node-032ab-controlled-transcript-event-diagnostics-smoke-after-propagation-fix
current_head=43c8ec3b658cc63874ebeb4207c36ea881e62a13
source_runtime_diff=empty
preserved_untracked_artifacts=course_submission/,data/storage/,node014-server.tar
```

## Asterisk Read-Only Findings

Server:

```text
host=92.118.85.117
ssh_reachable=true
hostname=tula
ssh_user=root
uptime_observed=true
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_process_OPENAI_API_KEY=ABSENT
asterisk_service_env_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
ari_env_metadata=root:tulauser:640
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_python=Python 3.12.3
target_listeners_443_8080_8081=absent
```

Autostart/scheduler read-only check:

```text
unexpected_gateway_smoke_helper_timers=absent
root_cron_helper_autostart=absent
standard_atd_service_observed=true
```

`atd.service` appeared as the standard deferred execution scheduler, not as a NODE helper/smoke automation unit.

## Gateway Read-Only Findings

Server:

```text
host=45.61.48.199
ssh_reachable=true
hostname=ai-secretary-gateway-node023
ssh_user=root
uptime_observed=true
gateway_unit_present=true
gateway_unit_verify=OK
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
gateway_env_metadata=root:gateway:640
gateway_OPENAI_API_KEY_masked_presence=PRESENT
gateway_GATEWAY_TOKEN_masked_presence=PRESENT
gateway_user_present=true
gateway_group_present=true
gateway_runtime_dir_present=true
target_listeners_443_8080_8081=absent
ufw=active
ufw_default_incoming=deny
ufw_8080_tcp=ALLOW_IN_FROM_92.118.85.117_ONLY
```

## Phase B Plan Summary

If exact approval is later provided, Phase B must immediately re-confirm all hard gates before any state-changing action, then run exactly one controlled Asterisk-side non-business-dialog smoke.

Required Phase B evidence:

```text
openai_event_type_counts_available
openai_event_type_counts_present
openai_event_type_counts
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
diagnostic_propagation_gap
diagnostic_classification
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
token_values_printed=false
```

Forbidden in Phase B unless separately approved:

```text
business_dialog_enablement
transcript_text_logging
token_output
provider_power_cycle
production_autostart
systemctl_enable
firewall_broadening
443
8081
TLS_proxy_changes
notion_write
runtime_evidence_update
scheduler_webhook_automation
```

## GO/NO-GO

```text
phase_a_result=pass
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=phase_b_approval_phrase_absent
```

## Validation

```text
focused_suite=50_passed
git_diff_check=pass
source_runtime_diff=empty
```

No secrets, token values, transcript text, transcript deltas, audio, or binary artifacts were added.

## Phase B Live Smoke Result

Approval phrase:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

Immediate hard gates passed before state-changing commands:

```text
asterisk_ssh_reachable=true
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_process_OPENAI_API_KEY=ABSENT
asterisk_service_env_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
asterisk_selected_runtime=Python 3.12.3
asterisk_target_listeners_443_8080_8081=absent
gateway_ssh_reachable=true
gateway_hostname=ai-secretary-gateway-node023
gateway_unit_present=true
gateway_unit_verify=OK
gateway_service_before=inactive_disabled
gateway_env_metadata=root:gateway:640
gateway_masked_OPENAI_API_KEY_presence=passed
gateway_masked_GATEWAY_TOKEN_presence=passed
gateway_target_listeners_443_8080_8081_before=absent
ufw=active_default_deny_8080_from_92.118.85.117_only
```

Smoke mechanics:

```text
local_helper_bundle_create=ok
local_helper_bundle_validate=ok_after_absolute_path_retry
remote_helper_bundle_copy=ok_explicit_windows_openssh_scp
remote_helper_bundle_preflight=ok
smoke_audio=24000_Hz_mono_16_bit_PCM_WAV
gateway_service_started_for_smoke=true
gateway_service_enabled=false
safe_temp_env_create_validate_cleanup=ok
temp_env_mode=600
token_source=Gateway env piped to guard stdin only
token_values_printed=false
transcript_text_printed=false
controlled_smoke_invocations=1
```

Smoke result:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=false
openai_event_type_counts_present=false
openai_event_type_counts={}
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
input_audio_buffer_commit_sent=null
timeout_observed=null
error_event_seen=null
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

Phase B classification:

```text
transport_auth_openai_realtime_success=true
diagnostic_propagation_fix_live_verified=false
blocker=openai_event_type_counts_available_false_in_live_smoke
likely_next_boundary=deployed_gateway_runtime_diagnostics_mapping_or_rollout_gap
```

Final state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent_after_cleanup
firewall=unchanged_source_restricted
gateway_env_metadata=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_helper_env_audio_removed=true
local_temporary_helper_bundle_removed=true
systemctl_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_broadened=false
```

Next recommendation:

```text
NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
```
