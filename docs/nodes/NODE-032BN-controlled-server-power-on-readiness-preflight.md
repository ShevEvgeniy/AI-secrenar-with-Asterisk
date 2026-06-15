# NODE-032BN / controlled-server-power-on-readiness-preflight

## Summary

NODE-032BN ran a read-only power-on readiness preflight for Asterisk and Kamatera Gateway after NODE-032BM stopped because the Gateway host had not been powered on.

Result:

```text
node_outcome=READINESS_PASSED
operator_power_on_confirmation=true
asterisk_power_confirmed_by_operator=true
kamatera_gateway_power_confirmed_by_operator=true
asterisk_ssh_reachable=true
gateway_ssh_reachable=true
readiness_passed=true
final_classification=readiness_passed
```

This node is not a smoke retry, not quote-safe env dry-run validation, and not transcript-use proof.

## Branch

```text
feat/node-032bn-controlled-server-power-on-readiness-preflight
```

## Base

```text
starting_master_head=ff5f9f6ede930afd17c9678cabe598f31f81b684
```

## Operator Confirmation

Operator confirmation received:

```text
Asterisk включён.
Kamatera Gateway включён.
Можно делать read-only preflight.
```

## Exact Live/Server Actions Performed

Only SSH read-only inspection was performed.

```text
ssh_read_only_asterisk=true
ssh_read_only_gateway=true
gateway_start=false
gateway_stop=false
gateway_restart=false
quote_safe_dry_run_env_check=false
smoke=false
gateway_request=false
transcript_use_flags_enabled=false
token_or_real_env_value_handling=false
service_mutation=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
live_audio_generation_or_upload=false
disk_image_touched=false
```

## Asterisk Read-Only Preflight

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

No token values, raw env values, Authorization headers, raw transcript text, transcript deltas, or shell environment dumps were printed.

## Gateway Read-Only Preflight

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
```

Unit-declared env metadata:

```text
unit_environmentfile_lines=1
unit_envfile_declared=EnvironmentFile=/etc/ai-secretary/openai-realtime-gateway.env
gateway_env_file_present=true
gateway_env_nonempty=true
gateway_env_mode=640
gateway_env_owner_group=root:gateway
gateway_openai_key_present_masked=true
gateway_token_present_masked=true
```

An initial check of the older/non-declared path `/etc/ai-secretary/gateway.env` returned absent. The systemd unit declares `/etc/ai-secretary/openai-realtime-gateway.env`, which is present and has masked secret presence checks only.

## Mutation Result

```text
mutation_occurred=false
service_action=false
gateway_started=false
gateway_stopped=false
gateway_restarted=false
docker_mutation=false
firewall_mutation=false
server_or_app_config_mutation=false
env_file_mutation=false
audio_generated_or_uploaded=false
disk_image_touched=false
```

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

Protected local artifacts remained untracked and untouched:

```text
course_submission/
data/storage/
node014-server.tar
```

## Non-Proofs

NODE-032BN does not prove:

```text
smoke_success=false
quote_safe_dry_run_env_check_success=false
gateway_request_success=false
enabled_live_dialog_use_proven=false
business_dialog_transcript_use_proven=false
```

## Final Classification

```text
final_classification=readiness_passed
```
