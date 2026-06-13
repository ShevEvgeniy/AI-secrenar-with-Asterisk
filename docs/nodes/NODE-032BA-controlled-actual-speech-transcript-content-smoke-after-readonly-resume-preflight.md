# NODE-032BA / controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight

## Summary

NODE-032BA received approval for one controlled actual-speech transcript-content smoke, but stopped before Gateway service start and before smoke.

Result:

```text
node_outcome=NO_GO_BEFORE_SMOKE
hard_gate_result=NO_GO
primary_blocker=asterisk_smoke_helper_absent
secondary_blocker=asterisk_gateway_token_runtime_env_absent
gateway_service_started=false
smoke_attempt_count=0
```

The approved boundary allowed one bounded smoke, but also forbade helper deploy, temp env creation, and token handling. Asterisk did not have the smoke helper or helper-bundle utility present, and no existing Gateway token runtime env was present. Therefore the node stopped before any service action or smoke.

## Branch

```text
feat/node-032ba-controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight
```

## Approval

Exact approval phrase:

```text
APPROVE NODE-032BA CONTROLLED ACTUAL SPEECH TRANSCRIPT CONTENT SMOKE
```

## Local Validation

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

Smoke path findings:

```text
asterisk_smoke_helper_present=false
asterisk_helper_bundle_present=false
existing_gateway_token_runtime_env=ABSENT
helper_deploy_allowed=false
temp_env_creation_allowed=false
token_handling_allowed=false
```

No env files were read and no raw env values were printed.

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

Gateway matched the inactive/disabled pre-smoke baseline. Because the Asterisk-side smoke path was blocked, the Gateway service was not started.

## Gateway Service Start And Listener Result

```text
gateway_service_start_attempted=false
listener_wait_attempted=false
listener_8080=not_run
listener_443=absent_before_action
listener_8081=absent_before_action
```

## Smoke Result

```text
smoke_attempt_count=0
gateway_auth_ok=not_run
openai_realtime_from_gateway_ok=not_run
chunks_sent=not_run
transcript_event_seen=not_run
transcript_present=not_run
transcript_content_match=not_available
transcript_text_logged=false
transcript_delta_logged=false
transcript_used_for_dialog=false
fallback_reason=not_run
```

No smoke attempt occurred.

## Safe Log Result

```text
safe_journal_filter_attempted=false
reason=gateway_service_not_started_and_smoke_path_blocked
```

## Stop And Final State

```text
gateway_service_stop_attempted=false
reason=gateway_service_not_started_by_node
gateway_service_final_state=inactive_disabled
gateway_runtime_process_final=absent
target_listeners_final_state=443_absent_8080_absent_8081_absent
```

## Blockers

```text
primary_blocker=asterisk_smoke_helper_absent
secondary_blocker=asterisk_gateway_token_runtime_env_absent
approval_boundary_forbids_helper_deploy=true
approval_boundary_forbids_temp_env_creation=true
approval_boundary_forbids_token_handling=true
```

## Next Recommendation

```text
NODE-032BB / restore-approved-asterisk-smoke-helper-and-token-boundary-before-transcript-smoke
```

NODE-032BB should resolve the Asterisk-side smoke helper path and safe token boundary before another transcript-content smoke is requested. It should decide whether helper deployment/update and a safe runtime token mechanism are explicitly approved, or whether a pre-existing approved smoke path can be used.

## Safety

```text
phase_b=false
repeated_smoke_loop=false
real_customer_audio=false
raw_transcript_text_committed=false
transcript_delta_committed=false
token_values_printed=false
helper_deploy=false
temp_env_created=false
gateway_http_request=false
openai_request=false
service_start=false
service_stop=false
service_restart=false
service_reload=false
service_enable=false
service_disable=false
docker_mutation=false
firewall_or_env_change=false
server_or_app_config_mutation=false
disk_image_touched=false
```

## Handoff

```text
docs/handoffs/NODE-032BA-controlled-actual-speech-transcript-content-smoke-after-readonly-resume-preflight-codex-handoff.md
```

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```
