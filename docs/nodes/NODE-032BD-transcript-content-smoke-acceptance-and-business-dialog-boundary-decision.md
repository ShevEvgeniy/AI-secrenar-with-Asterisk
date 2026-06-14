# NODE-032BD / transcript-content-smoke-acceptance-and-business-dialog-boundary-decision

## Summary

NODE-032BD is a docs-only decision node after NODE-032BC. It accepts NODE-032BC as proof of redacted transcript-content presence for the controlled prepared actual-speech smoke path only, and it keeps the business-dialog transcript-use boundary closed.

```text
node_outcome=DOCS_ONLY_ACCEPTANCE_DECISION
accepted_scope=prepared_actual_speech_smoke_path_only
business_dialog_transcript_use_enabled=false
live_systems_touched=false
```

## Branch

```text
feat/node-032bd-transcript-content-smoke-acceptance-and-business-dialog-boundary-decision
```

## Accepted NODE-032BC Proof

NODE-032BC was one controlled prepared actual-speech transcript-content smoke through the restored helper and credential boundary.

Accepted evidence:

```text
smoke_attempt_count=1
gateway_http_status=200
gateway_auth=ok
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=28
transcript_event_seen=true
transcript_bearing_event_seen=true
transcript_text_present=true
transcript_text_length_bucket=nonzero_redacted
diagnostic_propagation_gap=false
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
gateway_final_state=inactive_disabled
target_listeners_after_stop=443_absent_8080_absent_8081_absent
```

The accepted content proof is redacted. Raw transcript text and transcript deltas were not printed, logged, or committed.

## Explicit Non-Proofs

NODE-032BC is not proof of:

```text
real_caller_or_customer_audio=false
production_call_path=false
business_dialog_transcript_use=false
transcript_semantic_accuracy=false
latency_or_sla=false
repeated_run_stability=false
load_or_error_resilience=false
production_monitoring_or_alerting=false
approval_to_enable_business_dialog_transcript_use=false
```

These remain separate boundaries. In particular, transcript content presence does not authorize using Gateway transcript content inside the business dialog.

## Decision

NODE-032BD accepts NODE-032BC as:

```text
accepted_as_transcript_content_presence_proof=true
accepted_for_prepared_actual_speech_smoke_path=true
accepted_for_business_dialog_integration=false
accepted_for_production_enablement=false
```

Business-dialog transcript use stays disabled:

```text
enable_business_dialog_transcript_use_now=false
next_live_or_runtime_work_requires_separate_approved_node=true
default_off_boundary_preserved=true
```

Before any implementation or live business-dialog use, the project needs a separate guardrail decision covering:

```text
default_disabled_configuration
explicit_enablement_boundary
fallback_behavior
redaction_and_logging_policy
semantic_accuracy_acceptance
latency_and_failure_handling
rollback_plan
operator_approval_phrase
```

## Next Recommendation

Preferred next node:

```text
NODE-032BE / controlled-business-dialog-transcript-use-design-and-guardrails
```

This should be docs/design only. It should define the controlled business-dialog transcript-use boundary and guardrails before any runtime implementation or enablement.

Deferred alternative if explicitly chosen by the coordinator:

```text
NODE-032BE / controlled-business-dialog-transcript-use-disabled-by-default-implementation
```

## Validation

```text
git_diff_check=passed
source_runtime_diff=empty
```

No pytest was required because this node is docs-only and does not change source/runtime files.

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
business_dialog_transcript_enablement=false
raw_transcript_text_added=false
transcript_delta_content_added=false
audio_artifact_added=false
log_or_server_dump_artifact_added=false
disk_image_touched=false
```

## Handoff

```text
docs/handoffs/NODE-032BD-transcript-content-smoke-acceptance-and-business-dialog-boundary-decision-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
