# Codex Handoff - NODE-032BN / controlled-server-power-on-readiness-preflight

## Result

NODE-032BN ran the approved read-only power-on readiness preflight after the operator confirmed both servers were powered on.

```text
node_outcome=READINESS_PASSED
operator_power_on_confirmation=true
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
final_classification=readiness_passed
```

## Scope

This node was read-only SSH inspection only.

```text
smoke=false
quote_safe_dry_run_env_check=false
gateway_request=false
gateway_start=false
gateway_stop=false
gateway_restart=false
transcript_use_flags_enabled=false
token_or_real_env_value_handling=false
service_mutation=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
live_audio_generation_or_upload=false
disk_image_touched=false
notion_write=false
runtime_evidence_write=false
```

## Asterisk Preflight

```text
asterisk_host=92.118.85.117
asterisk_ssh_reachable=true
hostname=tula
uptime_seconds=2282
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
helper_present=true
helper_executable=true
policy_module_present=true
credential_boundary_present=true
credential_boundary_nonempty=true
credential_boundary_mode=600
credential_required_keys_present=true
service_OPENAI_API_KEY_absent=true
process_OPENAI_API_KEY_absent=true
business_dialog_transcript_use_not_enabled=true
stt_gateway_dialog_use_not_enabled=true
transcript_text_logging_disabled=true
```

## Gateway Preflight

```text
gateway_host=45.61.48.199
gateway_ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_seconds=1651
gateway_service_active=inactive
gateway_service_enabled=disabled
gateway_unit_present=true
listener_443_present=false
listener_8080_present=false
listener_8081_present=false
gateway_runtime_process_present=false
ufw_active=true
ufw_default_incoming_deny=true
ufw_8080_source_restricted_to_asterisk=true
unit_envfile_declared=EnvironmentFile=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_file_present=true
gateway_env_nonempty=true
gateway_env_mode=640
gateway_env_owner_group=root:gateway
gateway_openai_key_present_masked=true
gateway_token_present_masked=true
```

The older/non-declared path `/etc/ai-secretary/gateway.env` was absent; the unit-declared env file was present. No raw env values or token values were printed.

## Validation

```text
git_diff_check=passed
source_runtime_diff=empty
pytest_run=false
pytest_skip_reason=docs_only_node
```

## Safety Scans

```text
changed_docs_secret_token_env_dump_transcript_delta_hits=0
added_line_secret_token_env_dump_transcript_delta_hits=0
audio_binary_temp_env_log_server_dump_disk_artifact_hits=0
```

## Protected Artifacts

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Next Step

Wait for coordinator review. Do not commit, push, open PR, write Notion, write Runtime/Evidence, or proceed to any smoke until explicitly directed.
