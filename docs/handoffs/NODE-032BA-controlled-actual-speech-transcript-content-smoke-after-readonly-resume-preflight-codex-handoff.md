# NODE-032BA Codex Handoff

## Node

```text
NODE-032BA / controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight
```

## Branch

```text
feat/node-032ba-controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight
```

## Approval

The exact approval phrase was present:

```text
APPROVE NODE-032BA CONTROLLED ACTUAL SPEECH TRANSCRIPT CONTENT SMOKE
```

## Outcome

NODE-032BA stopped before Gateway service start and before smoke.

```text
node_outcome=NO_GO_BEFORE_SMOKE
primary_blocker=asterisk_smoke_helper_absent
secondary_blocker=asterisk_gateway_token_runtime_env_absent
reason=approved_boundary_forbids_helper_deploy_temp_env_creation_and_token_handling
gateway_service_started=false
smoke_attempt_count=0
```

The node did not start the Gateway service because the Asterisk-side smoke path was not available inside the approved boundary.

## Local Baseline Validation

```text
focused_pytest=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

## Asterisk Pre-State

```text
asterisk_ssh=ok
hostname=tula
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
asterisk_process_running=true
ai_secretary_process_running=true
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript_flag=NOT_ENABLED
transcript_text_logging_flag=NOT_ENABLED
project_repo_present=true
project_venv_present=true
runtime_modules_ok=true
target_listeners_443_8080_8081=ABSENT
```

Blocked smoke path:

```text
asterisk_smoke_helper_present=false
asterisk_helper_bundle_present=false
existing_gateway_token_runtime_env=ABSENT
helper_deploy_allowed=false
temp_env_creation_allowed=false
token_handling_allowed=false
```

No env files were read and no raw environment values were printed.

## Gateway Read-Only State

```text
gateway_ssh=ok
hostname=ai-secretary-gateway-node023
ai_secretary_gateway_service_active=inactive
ai_secretary_gateway_service_enabled=disabled
target_listeners_443_8080_8081=ABSENT
gateway_runtime_process=ABSENT
docker_containers=NONE
gateway_unit_exists=true
realtime_gateway_marker_openai_event_type_counts_available=PRESENT
realtime_measurement_symbol_diagnose_pcm_wav_audio_bytes=PRESENT
```

Gateway remained in the expected inactive/disabled pre-smoke baseline.

## Service And Smoke Result

```text
gateway_service_start_attempted=false
listener_wait_attempted=false
safe_journal_filter_attempted=false
smoke_attempt_count=0
gateway_http_request=false
openai_request=false
audio_generated=false
audio_uploaded=false
helper_deploy=false
temp_env_created=false
token_values_printed=false
transcript_text_logged=false
transcript_delta_logged=false
```

Because no smoke ran, transcript-content metrics are not available:

```text
gateway_auth_ok=not_run
openai_realtime_from_gateway_ok=not_run
chunks_sent=not_run
transcript_event_seen=not_run
transcript_present=not_run
transcript_content_match=not_available
fallback_reason=not_run
```

## Final State

```text
gateway_service_final_state=inactive_disabled
gateway_runtime_process_final=absent
target_listeners_final_state=443_absent_8080_absent_8081_absent
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_mutation=false
disk_image_touched=false
```

## Next Recommendation

```text
NODE-032BB / restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

NODE-032BB should decide whether to approve a helper deployment/update and a safe runtime token boundary, or to identify an already-present Asterisk-side smoke path that does not require temp env creation. It should not run smoke unless separately approved.

## Safety Confirmation

```text
phase_b=false
repeated_smoke_loop=false
real_customer_audio=false
raw_transcript_text_committed=false
transcript_delta_committed=false
token_values_printed=false
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_mutation=false
disk_image_touched=false
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
