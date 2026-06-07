# NODE-032AB / controlled-transcript-event-diagnostics-smoke-after-propagation-fix

## Goal

Prepare a controlled live smoke after NODE-032AA fixed the local redacted diagnostic propagation ambiguity.

Phase A is read-only gate checks and planning only. Phase B is not approved.

## Base

```text
base_master_head=43c8ec3b658cc63874ebeb4207c36ea881e62a13
latest_closed_node=NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
branch=feat/node-032ab-controlled-transcript-event-diagnostics-smoke-after-propagation-fix
```

NODE-032AA added:

```text
openai_event_type_counts_available
```

Meaning:

```text
true=the openai_event_type_counts field propagated, even if it is {}
false=the event-count field was missing/not propagated
```

## Phase A Scope

Allowed:

```text
read_only_ssh_checks=true
local_docs_updates=true
local_tests=true
```

Forbidden:

```text
live_smoke=false
test_call=false
helper_deploy=false
token_handling=false
server_temp_env_creation=false
service_start_stop_restart_reload_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
production_autostart=false
systemctl_enable=false
transcript_text_logging=false
transcript_delta_logging=false
business_dialog_transcript_use=false
audio_binary_artifact_commit=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Phase B Approval Boundary

Phase B may only proceed after this exact approval phrase:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

Any other phrase is not approval.

## Phase A Local State

```text
current_branch=feat/node-032ab-controlled-transcript-event-diagnostics-smoke-after-propagation-fix
current_head=43c8ec3b658cc63874ebeb4207c36ea881e62a13
source_runtime_diff=empty
```

Preserved untracked artifacts:

```text
course_submission/
data/storage/
node014-server.tar
```

## Asterisk Read-Only Gates

Server:

```text
host=92.118.85.117
ssh_reachable=true
hostname=tula
ssh_user=root
uptime_observed=true
```

Service:

```text
ai-secretary-ari.service=active
ai-secretary-ari.service_enabled=enabled
```

Safety:

```text
process_OPENAI_API_KEY=ABSENT
service_env_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
ari_env_metadata=root:tulauser:640
target_listeners_443_8080_8081=absent
unexpected_gateway_smoke_helper_timers=absent
root_cron_helper_autostart=absent
standard_atd_service_observed=true
```

Selected runtime:

```text
path=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
version=Python 3.12.3
```

## Gateway Read-Only Gates

Server:

```text
host=45.61.48.199
ssh_reachable=true
hostname=ai-secretary-gateway-node023
ssh_user=root
uptime_observed=true
```

Service and runtime:

```text
gateway_unit_present=true
gateway_unit_verify=OK
ai-secretary-gateway.service=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user_present=true
gateway_group_present=true
gateway_runtime_dir_present=true
```

Env metadata and masked presence:

```text
gateway_env_metadata=root:gateway:640
gateway_OPENAI_API_KEY_masked_presence=PRESENT
gateway_GATEWAY_TOKEN_masked_presence=PRESENT
```

Listener and firewall:

```text
target_listeners_443_8080_8081=absent
ufw=active
ufw_default_incoming=deny
ufw_8080_tcp=ALLOW_IN_FROM_92.118.85.117_ONLY
firewall_broadened=false
```

## Phase B Plan

If the exact approval phrase is provided later, Phase B must:

1. Re-confirm all Asterisk and Gateway hard gates immediately.
2. Use the existing safe helper-bundle strategy.
3. Use the NODE-032L safe temp-env guard for token handling.
4. Start the Gateway service only if required for smoke readiness.
5. Run exactly one controlled Asterisk-side non-business-dialog smoke.
6. Verify the NODE-032AA diagnostic propagation marker and existing redacted diagnostic fields.
7. Clean up temporary helper/env/audio artifacts.
8. Return the Gateway service to the documented final state unless separately approved otherwise.

Required smoke evidence:

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
diagnostic_propagation_gap
diagnostic_classification
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Hard NO-GO

```text
asterisk_OPENAI_API_KEY_present
business_dialog_gateway_transcript_enabled
transcript_text_logging_enabled
gateway_env_missing_or_wrong_metadata
masked_gateway_secret_presence_fails
gateway_unit_missing_or_invalid
unexpected_listener_on_443_or_8081
ufw_8080_not_source_restricted_to_92.118.85.117
token_value_would_be_printed
transcript_text_would_be_logged_or_printed
phase_b_approval_phrase_absent
```

## Phase A Result

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

## Handoff

```text
docs/handoffs/NODE-032AB-controlled-transcript-event-diagnostics-smoke-after-propagation-fix-codex-handoff.md
```

## Next Step

Wait for the exact Phase B approval phrase:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

## Phase B Result

Phase B approval was re-issued exactly:

```text
APPROVE NODE-032AB PHASE B LIVE SMOKE
```

Immediate hard gates were re-confirmed before state-changing commands:

```text
asterisk_ssh_reachable=true
asterisk_service=active_enabled
asterisk_process_OPENAI_API_KEY=ABSENT
asterisk_service_env_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
transcript_text_logging=NOT_ENABLED
asterisk_selected_runtime=Python 3.12.3
asterisk_target_listeners_443_8080_8081=absent
gateway_ssh_reachable=true
gateway_unit_verify=OK
gateway_service_before=inactive_disabled
gateway_env_metadata=root:gateway:640
gateway_masked_secrets_present=true
gateway_target_listeners_443_8080_8081_before=absent
ufw_8080_tcp=ALLOW_IN_FROM_92.118.85.117_ONLY
```

Smoke setup:

```text
helper_bundle_create=ok
helper_bundle_validate=ok
remote_helper_bundle_preflight=ok
smoke_audio_validate=24000_Hz_mono_16_bit_PCM_WAV
safe_temp_env_create_validate_cleanup=ok
token_values_printed=false
transcript_text_printed=false
gateway_service_started_for_smoke=true
gateway_service_enabled=false
systemctl_enable=false
```

Exactly one Asterisk-side non-business-dialog smoke ran.

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

NODE-032AB therefore confirms the Asterisk-to-Gateway transport/auth/OpenAI Realtime path still works, but the NODE-032AA diagnostic availability marker did not become available in the live smoke evidence.

```text
transport_auth_openai_realtime_success=true
diagnostic_propagation_fix_live_verified=false
phase_b_result=blocked_diagnostic_propagation_gap
blocker=openai_event_type_counts_available_false_in_live_smoke
```

Final safety state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted
gateway_env_metadata=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_helper_env_audio_removed=true
local_temporary_helper_bundle_removed=true
transcript_text_logged=false
transcript_used_for_dialog=false
systemctl_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_broadened=false
```

## Next Recommendation

```text
NODE-032AC / controlled-gateway-runtime-diagnostics-propagation-rollout-plan
```

NODE-032AC should determine whether the live Gateway runtime needs a controlled rollout/update of the NODE-032AA diagnostics propagation code, or whether another redacted response-field mapping issue remains between the Gateway and Asterisk smoke report.
