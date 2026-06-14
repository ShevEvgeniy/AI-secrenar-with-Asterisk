# NODE-032BF / disabled-by-default-business-dialog-transcript-use-implementation

## Summary

NODE-032BF implements a disabled-by-default business-dialog transcript-use policy boundary.

The implementation is local source/tests/docs only. It does not run smoke, access servers, deploy helpers, handle tokens, create temp env files, make OpenAI requests, mutate Docker, change services, or enable business-dialog transcript use in real runtime.

```text
node_outcome=LOCAL_IMPLEMENTATION_TESTS_DOCS
business_dialog_transcript_default_enabled=false
live_systems_touched=false
runtime_enablement=false
```

## Branch

```text
feat/node-032bf-disabled-by-default-business-dialog-transcript-use-implementation
```

## Implementation

Added a pure business-dialog transcript policy module:

```text
src/ai_secretary/telephony/transcript_policy.py
```

The policy defines:

```text
TranscriptUsePolicy
TranscriptCandidate
TranscriptUseDecision
transcript_use_policy_from_env(...)
evaluate_business_dialog_transcript_use(...)
```

The policy returns safe metadata only. It does not return raw transcript text or transcript deltas in decision details.

Updated the Gateway STT adapter:

```text
src/ai_secretary/stt/gateway_adapter.py
```

The adapter now reads the business-dialog transcript policy from environment and requires the policy to allow use before an accepted gateway transcript can drive dialog. The existing `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true` gate remains necessary but is no longer sufficient by itself.

## Feature Flags

Implemented local parsing for the NODE-032BE flag names:

```text
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=false
BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
```

Defaults:

```text
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=false
BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS=true
BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED=true
BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS=30000
```

## Fail-Closed Behavior

Transcript use is rejected when:

```text
policy_disabled=true
transcript_missing=true
transcript_stale=true
confidence_below_threshold=true
metadata_incomplete=true
redaction_guard_inactive=true
```

Policy decisions expose only safe fields:

```text
enabled
allowed
reason
length_bucket
confidence_bucket
age_bucket
redaction_required
used_for_dialog
```

## Logging And Redaction

The adapter continues to strip raw transcript text from logs/details and now reports `transcript_text_logged=false` even when a transcript is present. Safe metadata remains available through booleans and buckets.

```text
raw_transcript_text_logged=false
transcript_delta_logged=false
token_values_logged=false
raw_env_values_logged=false
```

## Tests

Added:

```text
tests/test_business_dialog_transcript_policy.py
```

Updated:

```text
tests/test_gateway_stt_adapter.py
```

Test coverage includes:

```text
default_disabled_keeps_existing_behavior=true
explicit_disabled_blocks_transcript_use=true
missing_transcript_fails_closed=true
stale_transcript_fails_closed=true
low_confidence_transcript_fails_closed=true
incomplete_metadata_fails_closed=true
redaction_guard_inactive_fails_closed=true
enabled_valid_transcript_allows_policy_result_without_logging_raw_text=true
fallback_preserved_when_transcript_rejected=true
business_path_requires_business_dialog_policy_opt_in=true
```

## Validation

Focused validation run:

```text
python -m pytest tests/test_business_dialog_transcript_policy.py tests/test_gateway_stt_adapter.py
```

Result:

```text
26 passed
```

Full validation and final diff checks are recorded in the handoff.

## Source/Runtime Diff

Expected changed source/test files:

```text
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/telephony/transcript_policy.py
tests/test_business_dialog_transcript_policy.py
tests/test_gateway_stt_adapter.py
```

No deploy, scripts, or runtime configuration changes were made.

## Next Recommendation

Future live validation remains separate:

```text
NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default
```

NODE-032BG must remain separately approved and must prove the disabled-by-default behavior under controlled live conditions before any broader runtime use.

## Safety

```text
ssh_used=false
provider_controls_used=false
gateway_power_action=false
smoke=false
call_run=false
phase_b=false
gateway_request=false
helper_deploy=false
token_handling=false
temp_env_created=false
openai_request=false
service_action=false
docker_mutation=false
firewall_or_env_mutation=false
server_or_app_config_mutation=false
business_dialog_transcript_runtime_enablement=false
raw_transcript_text_added=false
transcript_delta_content_added=false
audio_artifact_added=false
log_or_server_dump_artifact_added=false
disk_image_touched=false
```

## Handoff

```text
docs/handoffs/NODE-032BF-disabled-by-default-business-dialog-transcript-use-implementation-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
