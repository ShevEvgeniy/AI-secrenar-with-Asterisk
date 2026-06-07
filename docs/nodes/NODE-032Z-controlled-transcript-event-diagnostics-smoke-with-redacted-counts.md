# NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts

## Goal

Prepare a controlled live smoke that uses NODE-032Y redacted transcript-event diagnostics to classify transcript-event behavior without logging transcript text or enabling business-dialog transcript use.

Phase A is readiness and planning only. Phase B is not approved.

## Base

```text
master_head=b85300848c7b3a4bfe93489a34be5fe92a6f7edc
latest_closed_node=NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

NODE-032Y added safe redacted event diagnostics across the Gateway response, adapter redaction, and Asterisk-side smoke report:

```text
openai_event_type_counts
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
diagnostic_propagation_gap
diagnostic_classification
```

## Phase A Read-Only Findings

Asterisk:

```text
ssh_reachable=true
hostname=tula
whoami=root
ai-secretary-ari.service=active
ai-secretary-ari.service_enabled=enabled
listeners=22,7077,8088 plus local resolver/containerd listeners
ari_env_metadata=root:tulauser 640 /etc/ai-secretary/ari-app.env
ari_env_OPENAI_API_KEY=ABSENT
ari_process_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_version=Python 3.12.3
```

Gateway:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
whoami=root
ai-secretary-gateway.service=inactive
ai-secretary-gateway.service_enabled=disabled
target_listeners_443_8080_8081=absent
listeners=22 plus local resolver listeners
ufw=active
ufw_default_incoming=deny
ufw_8080_tcp=ALLOW IN from 92.118.85.117 only
gateway_env_metadata=root:gateway 640 /etc/ai-secretary/openai-realtime-gateway.env
```

## Phase B Approval Gate

Exact approval phrase:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Any other phrase is not approval.

## Phase B Conditional Plan

Phase B may proceed only after exact approval and immediate hard-gate re-confirmation.

Plan:

1. Re-confirm Asterisk SSH, service active/enabled, `OPENAI_API_KEY` absent from env/process, and business-dialog Gateway transcript use disabled.
2. Re-confirm Gateway SSH, service inactive/disabled unless explicitly documented otherwise, env metadata, no target listeners, and UFW `8080/tcp` restricted to `92.118.85.117`.
3. Use the existing safe helper bundle and selected Asterisk runtime.
4. Use safe temp-env handling without printing token values.
5. Run exactly one Asterisk-side non-business-dialog smoke.
6. Capture only NODE-032Y safe diagnostic fields.
7. Cleanup temporary helper/env/audio artifacts and preserve the documented final service/firewall/env state.

## Acceptance Boundary

Acceptable evidence:

```text
gateway_reachable_from_asterisk
gateway_auth
gateway_http_status
openai_realtime_from_gateway
openai_session_created
chunks_sent
openai_event_type_counts
openai_event_type_counts_present
transcript_event_seen
transcript_bearing_event_seen
transcript_text_present
transcript_text_length_bucket
input_audio_buffer_commit_sent
timeout_observed
error_event_seen
diagnostic_propagation_gap
diagnostic_classification
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
```

Forbidden evidence:

```text
token_values
raw_secret_env_output
transcript_text
transcript_delta_text
large_logs
audio_artifacts
binary_artifacts
business_dialog_profile_changes
```

## Current GO/NO-GO

```text
phase_b_recommendation=CONDITIONAL_GO
conditions=exact approval phrase plus immediate hard-gate re-confirmation
current_blockers=approval phrase absent; live gates stale until Phase B recheck
```

## Phase A Safety

```text
live_smoke=false
test_call=false
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
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Phase B Approval

Exact approval phrase was provided:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Phase B was therefore allowed only within the NODE-032Z boundary: immediate hard-gate re-confirmation, helper/temp/audio staging, one Asterisk-side non-business-dialog smoke, cleanup, and sanitized documentation.

## Phase B Hard-Gate Re-Confirmation

Asterisk:

```text
ssh_reachable=true
hostname=tula
whoami=root
ai-secretary-ari.service=active
ai-secretary-ari.service_enabled=enabled
ari_env_metadata=root:tulauser:640:/etc/ai-secretary/ari-app.env
ari_env_OPENAI_API_KEY=ABSENT
ari_process_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_version=Python 3.12.3
```

Gateway:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
whoami=root
ai-secretary-gateway.service_before=inactive
ai-secretary-gateway.service_enabled_before=disabled
gateway_unit_verify=OK
gateway_env_metadata=root:gateway:640:/etc/ai-secretary/openai-realtime-gateway.env
masked_OPENAI_API_KEY_presence=passed
masked_GATEWAY_TOKEN_presence=passed
target_listeners_443_8080_8081_before=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_tcp=ALLOW IN from 92.118.85.117 only
```

Read-only quoting retries occurred during the gate phase for env metadata and listener inspection. Both were corrected with sanitized commands; no secret values or transcript text were printed.

## Phase B Helper, Audio, And Temp Env

Helper bundle:

```text
local_bundle_create_first_attempt=failed_closed_on_C_tmp_permission
local_bundle_create_retry=ok_workspace_temp_path
local_bundle_validate=ok_with_absolute_bundle_root
remote_bundle_copy=ok_explicit_windows_openssh_scp
remote_bundle_validate=ok
runtime_modules_ok=true
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

Smoke audio:

```text
create_smoke_audio=ok
validate_smoke_audio=ok
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
secret_values_printed=false
transcript_text_logged=false
```

Safe temp env:

```text
first_create_attempt=failed_closed_missing_stdin_token_due_command_quoting
retry_create=ok_token_supplied_through_stdin_pipeline_only
validate=ok_masked_safe_json_only
cleanup=ok
token_values_printed=false
transcript_text_logged=false
```

## Phase B Service Readiness

Gateway service was started only for the approved smoke readiness window:

```text
systemctl_start=ok
service_active_during_smoke=active
service_enabled_state=disabled
listener_during_smoke=0.0.0.0:8080
target_listeners_443_8081=absent
ufw_unchanged=true
ufw_8080_tcp=ALLOW IN from 92.118.85.117 only
systemctl_enable=false
reboot_or_power_cycle=false
firewall_change=false
```

## Phase B Smoke Result

One malformed helper CLI invocation with an unsupported extra flag failed at argument parsing before any Gateway request. It did not run smoke, did not contact Gateway, and did not print token values or transcript text.

The corrected helper wrapper invocation then ran exactly one Asterisk-side non-business-dialog smoke:

```text
controlled_smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
transcript_text_logged=false
transcript_used_for_dialog=false
```

NODE-032Y redacted diagnostics:

```text
openai_event_type_counts={}
openai_event_type_counts_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
input_audio_buffer_commit_sent=null
timeout_observed=null
error_event_seen=null
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

Result:

```text
transport_auth_openai_realtime_success=true
redacted_diagnostics_success=false
phase_b_result=blocked_diagnostic_propagation_gap
```

NODE-032Z proved the controlled Asterisk-to-Gateway transport/auth/OpenAI path again, but it did not prove live transcript-event diagnostic propagation. The Gateway response still did not surface redacted OpenAI event counts or transcript-event booleans to the Asterisk-side smoke report.

## Final Cleanup And Safety State

```text
gateway_service_final=inactive
gateway_service_enabled_final=disabled
target_listeners_443_8080_8081_final=absent
ufw_final=active_default_deny_8080_from_92.118.85.117_only
asterisk_env_OPENAI_API_KEY_final=ABSENT
asterisk_process_OPENAI_API_KEY_final=ABSENT
business_dialog_gateway_transcript_final=NOT_ENABLED
asterisk_temp_helper_env_audio_removed=true
local_temp_helper_bundle_removed=true
gateway_env_metadata_preserved=root:gateway:640
token_values_printed=false
transcript_text_printed=false
transcript_text_logged=false
business_dialog_enablement=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
github_push_or_pr=false
```

## Validation

```text
focused_tests=47_passed
full_pytest=231_passed_6_failed_known_environmental
known_environmental_failure_1=missing src/scripts/make_demo_audio.py
known_environmental_failure_2=missing sentence_transformers
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status/test-fixture hits only
scoped_docs_handoff_source_scan=no_real_secret_values_found; policy labels/status placeholders only
audio_binary_artifacts_added=false
```

## Next Recommendation

```text
NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
```

NODE-032AA should inspect and fix why Gateway/OpenAI event count diagnostics are not propagating into the Asterisk-side smoke report, using local/repo changes first. It must preserve redaction, avoid transcript text logging, and keep business-dialog transcript use disabled unless a later node explicitly changes that boundary.
