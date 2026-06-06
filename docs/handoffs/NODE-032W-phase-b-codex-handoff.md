# NODE-032W Phase B Codex Handoff

Node:

```text
NODE-032W / controlled-gateway-transcript-presence-smoke
```

Approval phrase:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Boundary:

```text
controlled_smoke_invocations=1
business_dialog_enablement=false
business_dialog_transcript_use=false
transcript_text_logging=false
token_output=false
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_change=false
server_env_edit=false
tls_proxy_change=false
port_443_change=false
port_8081_change=false
```

This handoff contains no real token values, transcript text, raw secret env output, logs, audio, or binary artifacts.

## Hard Gate Reconfirmation

Asterisk:

```text
ssh_reachable=true
hostname=tula
ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_env_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_python=3.12.3
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

Gateway:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=OK
service_before=inactive_disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
opt_gateway_present=true
target_listeners_443_8080_8081_before=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
```

## Helper Bundle Result

```text
local_bundle_create=ok
local_bundle_validate=ok
local_runtime_modules_ok=true
remote_temp_dir_prepared=true
remote_bundle_copied=true
remote_validate_first_attempt=failed_closed_missing_validator_script
remote_validate_fix=staged_asterisk_gateway_helper_bundle_py_into_temp_bundle
remote_bundle_validate=ok
remote_runtime_modules_ok=true
missing_runtime_modules=[]
secret_values_printed=false
transcript_text_logged=false
```

The first remote validation failed closed before token handling, service action, or smoke because the temporary helper bundle did not include its own validator script path. The validator script was copied into the temporary bundle and remote validation then passed.

## Valid Audio Result

```text
audio_create=ok
audio_validate=ok
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
frame_count=24000
format_errors=[]
```

## Safe Temp-Env Result

```text
first_create_attempt=failed_closed_missing_token_due_command_quoting
first_create_secret_values_printed=false
retry_create=ok
token_source=Gateway env piped to guard stdin only
token_values_printed=false
validate=ok
required_keys_present=true
token_present_masked=true
temp_env_mode=600
cleanup=ok
```

No token value was printed, committed, logged, or recorded.

## Gateway Service Readiness

```text
service_started_for_smoke=true
service_active=true
service_enabled_state=disabled
listener_8080=present
listener_443=absent
listener_8081=absent
ufw_8080_allow=92.118.85.117 only
log_secret_or_transcript_pattern=absent
systemctl_enable=false
reboot=false
provider_power_cycle=false
```

## Controlled Smoke Result

Exactly one Asterisk-side non-business-dialog smoke invocation ran.

```text
controlled_smoke_invocations=1
origin=Asterisk
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

NODE-032W is blocked as transcript-presence proof because the smoke did not confirm transcript text presence or transcript event/presence flags. Transport/auth/OpenAI Realtime still succeeded.

## Final State

```text
gateway_service=inactive
gateway_service_enabled=disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_asterisk_helper_env_audio_removed=true
local_temp_bundle_removed=true
log_secret_or_transcript_pattern=absent
```

Rollback:

```text
rollback_needed=service_stop_and_temp_cleanup_only
service_stop=done
temp_cleanup=done
token_rotation_needed=false
cleanup_node_required=false
```

## Next Recommendation

```text
NODE-032X / transcript-presence-audio-stimulus-or-gateway-event-diagnostics-plan
```

Purpose: decide how to elicit or diagnose transcript event/presence without transcript text logging and without business-dialog transcript use.

## Validation

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_source_test_scan=no_real_secret_values_found; masked/status/placeholders only
final_git_status=docs/handoff changes plus pre-existing untracked course_submission/, data/storage/, node014-server.tar
```
