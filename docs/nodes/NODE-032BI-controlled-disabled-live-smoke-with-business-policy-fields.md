# NODE-032BI / controlled-disabled-live-smoke-with-business-policy-fields

## Summary

NODE-032BI ran one approved controlled disabled-by-default live smoke after NODE-032BH refreshed the Asterisk helper/runtime reporting path.

Result:

```text
approval_phrase=APPROVE NODE-032BI CONTROLLED DISABLED LIVE SMOKE WITH BUSINESS POLICY FIELDS
node_outcome=SUCCESSFUL_DISABLED_LIVE_SMOKE_WITH_BUSINESS_POLICY_FIELDS
exactly_one_smoke_ran=true
gateway_http_status=200
openai_realtime_from_gateway=ok
business_dialog_transcript_policy_fields_visible=true
business_dialog_transcript_use_enabled=false
business_dialog_transcript_used_for_dialog=false
```

NODE-032BI did not enable business-dialog transcript use, run a real call, use real caller/customer audio, print token/env values, print transcript text, or print transcript deltas.

## Branch

```text
feat/node-032bi-controlled-disabled-live-smoke-with-business-policy-fields
```

## Context

NODE-032BG proved the disabled live path stayed safe but exposed a policy-field reporting gap. NODE-032BH refreshed the deployed Asterisk helper/runtime reporting path and proved the fields existed in a no-network diagnostic.

NODE-032BI was the follow-up live smoke to prove those `business_dialog_transcript_*` fields appear during the controlled disabled live smoke path.

## Local Validation Before Live Action

```text
starting_master_head=7373d5dbf00e782a681a69cd4ab746237742bb9c
focused_pytest_before_smoke=65_passed
protected_artifacts_untracked=true
```

## Hard-Gate Preflight

Asterisk preflight:

```text
asterisk_reachable=true
ai_secretary_process_running=true
asterisk_OPENAI_API_KEY_absent=true
helper_present=true
helper_executable=true
helper_mode=755
credential_boundary_present=true
credential_boundary_nonempty=true
credential_boundary_mode=600
credential_required_keys_present=true
policy_module_present=true
business_dialog_transcript_policy_env_disabled=true
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=false
business_dialog_transcript_used_for_dialog=false
business_dialog_transcript_reason=business_dialog_transcript_disabled
dialog_transcript_used=false
transcript_logging_disabled=true
transcript_text_logged=false
secret_values_printed=false
transcript_text_printed=false
```

Gateway preflight:

```text
gateway_reachable=true
gateway_service_active=inactive
gateway_service_enabled=disabled
gateway_unit_verify_ok=true
gateway_baseline_safe=true
gateway_listener_443_present=false
gateway_listener_8080_present=false
gateway_listener_8081_present=false
gateway_env_file_present=true
gateway_env_mode=640
gateway_env_nonempty=true
gateway_openai_key_present_masked=true
gateway_token_present_masked=true
ufw_active=true
ufw_default_incoming_deny=true
ufw_8080_source_restricted=true
secret_values_printed=false
```

Hard gates passed. Gateway was started only for smoke readiness and remained disabled:

```text
gateway_service_start=performed
gateway_service_active_after_start=active
gateway_service_enabled_after_start=disabled
gateway_listener_8080_present_after_start=true
gateway_listener_443_present_after_start=false
gateway_listener_8081_present_after_start=false
```

## Smoke

Exactly one Asterisk-side disabled smoke invocation ran with prepared synthetic 24 kHz mono 16-bit PCM audio.

Command class only:

```text
create_smoke_audio=true
validate_smoke_audio=true
single_audio_smoke_invocation=true
safe_gateway_credential_boundary_used=true
token_values_printed=false
transcript_text_printed=false
transcript_delta_printed=false
business_dialog_transcript_use_enabled=false
```

Smoke result:

```text
accepted=false
attempted=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
openai_event_type_counts={conversation.item.added:1,conversation.item.done:1,conversation.item.input_audio_transcription.completed:1,input_audio_buffer.committed:1,session.created:1,session.updated:1}
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
diagnostic_propagation_gap=false
diagnostic_classification=transcript_event_observed_empty_or_no_text
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
fallback_reason=gateway_stt_dialog_use_disabled
```

Business-dialog policy fields were visible in the live smoke diagnostics:

```text
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=false
business_dialog_transcript_used_for_dialog=false
business_dialog_transcript_reason=business_dialog_transcript_disabled
business_dialog_transcript_fail_closed=true
business_dialog_transcript_redact_logs=true
business_dialog_transcript_redaction_required=true
business_dialog_transcript_max_age_ms=30000
business_dialog_transcript_age_bucket=unknown
business_dialog_transcript_confidence_bucket=unknown
business_dialog_transcript_length_bucket=zero
dialog_transcript_used=false
transcript_text_logged=false
```

The fields were observed in safe event diagnostics without raw transcript text, transcript deltas, token values, or env values.

## Cleanup

Gateway was restored to its pre-smoke safe state:

```text
gateway_service_active_final=inactive
gateway_service_enabled_final=disabled
gateway_listener_443_present_final=false
gateway_listener_8080_present_final=false
gateway_listener_8081_present_final=false
```

Asterisk cleanup:

```text
temporary_audio_removed=true
asterisk_OPENAI_API_KEY_absent_final=true
business_dialog_transcript_policy_env_disabled_final=true
transcript_logging_disabled_final=true
secret_values_printed=false
transcript_text_printed=false
```

## Validation

```text
focused_pytest=65_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
real_call_run=false
real_caller_or_customer_audio_used=false
second_smoke_or_retry=false
business_dialog_transcript_enablement=false
business_dialog_transcript_used_for_dialog=false
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
audio_committed=false
temp_env_committed=false
server_dump_or_log_artifact_added=false
docker_mutation=false
firewall_or_env_mutation=false
server_or_app_config_mutation=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Next Recommendation

```text
NODE-032BJ / controlled-business-dialog-transcript-use-enablement-boundary-decision
```

The next node should remain separate and approval-gated. Recommended first step is a boundary/design decision for any enabled business-dialog transcript use before implementation or live validation.
