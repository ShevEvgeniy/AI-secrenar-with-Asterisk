# NODE-032BF Codex Handoff

## Node

```text
NODE-032BF / disabled-by-default-business-dialog-transcript-use-implementation
```

## Branch

```text
feat/node-032bf-disabled-by-default-business-dialog-transcript-use-implementation
```

## Outcome

NODE-032BF implemented a disabled-by-default business-dialog transcript-use policy boundary with local unit tests.

```text
node_outcome=LOCAL_IMPLEMENTATION_TESTS_DOCS
live_systems_touched=false
ssh_used=false
smoke_run=false
gateway_request=false
phase_b=false
runtime_enablement=false
```

## Implementation Summary

Added:

```text
src/ai_secretary/telephony/transcript_policy.py
tests/test_business_dialog_transcript_policy.py
```

Updated:

```text
src/ai_secretary/stt/gateway_adapter.py
tests/test_gateway_stt_adapter.py
```

The new policy layer:

```text
TranscriptUsePolicy
TranscriptCandidate
TranscriptUseDecision
transcript_use_policy_from_env(...)
evaluate_business_dialog_transcript_use(...)
```

The Gateway STT adapter now requires both:

```text
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true
BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED=true
```

before a gateway transcript can be accepted for dialog. The default remains disabled.

## Feature Flags

Implemented local parsing:

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

## Fail-Closed Rules

Transcript use is rejected when:

```text
policy_disabled=true
missing_transcript=true
stale_transcript=true
low_confidence_transcript=true
incomplete_transcript_metadata=true
redaction_guard_inactive=true
```

Rejected transcripts follow safe fallback and are not used for business dialog.

## Logging And Redaction

The policy and adapter expose safe metadata only:

```text
booleans=true
length_buckets=true
confidence_buckets=true
age_buckets=true
redacted_markers=true
raw_transcript_text=false
transcript_delta_content=false
token_values=false
raw_env_values=false
```

## Tests

Focused test run:

```text
python -m pytest tests/test_business_dialog_transcript_policy.py tests/test_gateway_stt_adapter.py
```

Result:

```text
26 passed
```

Coverage includes:

```text
default_disabled_keeps_existing_behavior=true
explicit_disabled_blocks_transcript_use=true
missing_transcript_fails_closed=true
stale_transcript_fails_closed=true
low_confidence_transcript_fails_closed=true
enabled_valid_transcript_allows_policy_result_without_logging_raw_text=true
raw_transcript_not_logged=true
fallback_preserved_when_transcript_rejected=true
```

## Validation To Run

```text
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
```

If full pytest remains affected by known environmental failures, record them exactly.

## Next Recommendation

```text
NODE-032BG / controlled-business-dialog-transcript-use-live-smoke-disabled-by-default
```

NODE-032BG must be separately approved before any live validation.

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
server_dump_or_log_artifact_added=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
