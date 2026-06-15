# Codex Handoff - NODE-032BI / controlled-disabled-live-smoke-with-business-policy-fields

## Result

NODE-032BI successfully ran one controlled disabled-by-default live smoke and proved the NODE-032BF business-dialog transcript policy fields appear in live smoke diagnostics after the NODE-032BH helper/runtime refresh.

```text
node_outcome=SUCCESSFUL_DISABLED_LIVE_SMOKE_WITH_BUSINESS_POLICY_FIELDS
exactly_one_smoke_ran=true
gateway_http_status=200
openai_realtime_from_gateway=ok
business_dialog_transcript_policy_fields_visible=true
business_dialog_transcript_policy_enabled=false
business_dialog_transcript_allowed=false
business_dialog_transcript_used_for_dialog=false
dialog_transcript_used=false
```

## Preflight

```text
asterisk_reachable=true
gateway_reachable=true
asterisk_OPENAI_API_KEY_absent=true
business_dialog_transcript_policy_env_disabled=true
transcript_logging_disabled=true
gateway_service_initial_state=inactive_disabled
gateway_unit_verify_ok=true
gateway_env_present_masked_only=true
ufw_active_default_deny_source_restricted=true
target_listeners_absent_before_smoke=true
```

## Smoke Result

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
openai_event_type_counts_available=true
openai_event_type_counts_present=true
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=false
transcript_text_length_bucket=zero
diagnostic_propagation_gap=false
fallback_reason=gateway_stt_dialog_use_disabled
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

## Business Policy Field Proof

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
```

## Cleanup

```text
gateway_service_final_state=inactive_disabled
target_listeners_absent_final=true
temporary_audio_removed=true
asterisk_OPENAI_API_KEY_absent_final=true
business_dialog_transcript_policy_env_disabled_final=true
transcript_logging_disabled_final=true
```

## Validation

```text
focused_pytest=65_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
business_dialog_transcript_enablement=false
real_call_run=false
real_caller_or_customer_audio_used=false
audio_committed=false
temp_env_committed=false
server_dump_or_log_artifact_added=false
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

Do not reuse NODE-032BI approval. Any enabled business-dialog transcript-use work must be a separate approved node.
