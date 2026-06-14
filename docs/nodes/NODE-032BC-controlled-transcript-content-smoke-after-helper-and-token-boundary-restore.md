# NODE-032BC / controlled-transcript-content-smoke-after-helper-and-token-boundary-restore

## Summary

NODE-032BC ran exactly one controlled Asterisk-side transcript-content smoke after NODE-032BB restored the helper and credential boundary.

Result:

```text
approval_phrase=APPROVE NODE-032BC CONTROLLED TRANSCRIPT CONTENT SMOKE ONLY
node_outcome=SUCCESSFUL_REDACTED_TRANSCRIPT_CONTENT_SMOKE
hard_gate_result=GO
smoke_attempt_count=1
gateway_request=true
phase_b=false
repeated_smoke_loop=false
```

The smoke reached Gateway/Auth/OpenAI Realtime and observed redacted nonzero transcript-content presence while keeping transcript text and transcript deltas out of logs/docs.

## Branch

```text
feat/node-032bc-controlled-transcript-content-smoke-after-helper-and-token-boundary-restore
```

## Context

NODE-032BB restored the two NODE-032BA blockers:

```text
helper_restore=PASS
credential_boundary_restore=PASS
helper_present=true
helper_executable=true
credential_boundary_present=true
credential_boundary_mode=600
credential_value_printed=false
business_dialog_transcript_use=disabled
transcript_text_logging=disabled
```

NODE-032BC approval allowed one bounded smoke only. It did not authorize Phase B, repeated attempts, helper deploy, credential-boundary recreation, business-dialog transcript use, transcript text logging, Docker mutation, firewall/env/server/app config mutation, service enable/disable/restart/reload, or disk image action.

## Pre-State

Asterisk:

```text
asterisk_ssh=ok
hostname=tula
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_process_running=true
ai_secretary_process_running=true
service_OPENAI_API_KEY=ABSENT
process_OPENAI_API_KEY=ABSENT
business_dialog_transcript_use=disabled
transcript_text_logging=disabled
```

Helper and credential boundary:

```text
helper_present=true
helper_owner=tulauser:tulauser
helper_mode=755
helper_executable=true
credential_boundary_present=true
credential_boundary_owner=tulauser:tulauser
credential_boundary_mode=600
credential_value_printed=false
raw_env_printed=false
```

Gateway:

```text
gateway_ssh=ok
hostname=ai-secretary-gateway-node023
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
gateway_runtime_process=absent
listener_443=absent
listener_8080=absent
listener_8081=absent
```

## Gateway Service Readiness

NODE-032BC started the Gateway service only for the approved smoke window.

```text
gateway_service_start=performed
gateway_service_active_after_start=active
gateway_service_enabled_after_start=disabled
listener_8080=present
listener_443=absent
listener_8081=absent
```

The printed `listener_8080_seen` shell variables were blank because local quoting stripped remote shell variables. The authoritative post-start `ss -lntup` output showed `0.0.0.0:8080` under the Gateway Python process, so the listener gate passed.

## Stimulus

The smoke used an ephemeral Asterisk-side conversion of the existing safe system prompt into the required format. No audio was uploaded or committed.

Format validation:

```text
audio_path=/tmp/node032bc-smoke.wav
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
frame_count=132300
audio_format_errors=[]
```

Audio diagnostics:

```text
audio_duration_ms=5512
audio_chunk_count=28
audio_total_bytes=264678
audio_rms=2588.37
audio_peak=25573
audio_non_silent_ratio=0.5161
audio_quality_classification=valid_speech_candidate
real_customer_audio=false
actual_audio_content_logged=false
```

## Smoke Result

Exactly one Asterisk-side smoke invocation ran:

```text
smoke_attempt_count=1
adapter_smoke_exercised_node025_path=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=28
input_audio_buffer_commit_sent=true
timeout_observed=false
error_event_seen=false
```

Redacted event diagnostics:

```text
openai_event_type_counts_available=true
openai_event_type_counts_present=true
openai_event_type_counts={conversation.item.added:1,conversation.item.done:1,conversation.item.input_audio_transcription.completed:1,conversation.item.input_audio_transcription.delta:25,input_audio_buffer.committed:1,session.created:1,session.updated:1}
transcript_event_seen=true
transcript_bearing_event_seen=true
diagnostic_propagation_gap=false
diagnostic_classification=transcript_bearing_event_observed_text_redacted
```

Transcript-content result:

```text
transcript_text_present=true
transcript_text_length=0
transcript_text_length_bucket=nonzero_redacted
transcript_hash_or_redacted_marker=redacted
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

`transcript_text_length=0` is the helper's safe redacted field. The accepted content proof is the redacted bucket and presence flags; raw transcript text was not printed, logged, or committed.

## Safe Logs

The allowed Gateway journal filter ran after the smoke.

```text
safe_log_filter_ran=true
safe_log_filter_result=passed_no_token_or_transcript_text
current_node_log_summary=started_server_process;uvicorn_8080;POST_200
```

Historical lines from earlier nodes were present in the bounded journal window. No raw token, raw env, Authorization/Bearer material, transcript text, or transcript delta content was observed in the safe-log output.

## Cleanup And Final State

Gateway was stopped because NODE-032BC started it.

```text
gateway_service_stop=performed
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
gateway_runtime_process=absent
listener_443=absent
listener_8080=absent
listener_8081=absent
temporary_audio_removed=true
credential_boundary_still_present=true
service_OPENAI_API_KEY=ABSENT
process_OPENAI_API_KEY=ABSENT
```

## Local Validation

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Safety

```text
phase_b=false
repeated_smoke_loop=false
second_smoke_attempt=false
real_customer_audio=false
raw_token_values_printed=false
raw_env_values_printed=false
raw_transcript_text_printed=false
transcript_delta_printed=false
audio_uploaded=false
audio_committed=false
server_dump_committed=false
temp_env_created=false
helper_deploy=false
credential_boundary_restore_or_recreate=false
business_dialog_config_mutation=false
docker_mutation=false
firewall_or_env_mutation=false
service_enable_disable_restart_reload=false
apt_update_or_upgrade=false
disk_image_touched=false
```

## Next Recommendation

```text
NODE-032BD / transcript-content-smoke-acceptance-and-business-dialog-boundary-decision
```

NODE-032BD should decide how to accept NODE-032BC's redacted transcript-content proof and choose the next separate boundary. NODE-032BC approval must not be reused.

## Handoff

```text
docs/handoffs/NODE-032BC-controlled-transcript-content-smoke-after-helper-and-token-boundary-restore-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
