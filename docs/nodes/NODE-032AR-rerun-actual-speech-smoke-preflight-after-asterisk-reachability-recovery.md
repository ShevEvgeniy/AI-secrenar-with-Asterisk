# NODE-032AR / Rerun Actual Speech Smoke Preflight After Asterisk Reachability Recovery

## Scope

NODE-032AR records coordinator-collected read-only Asterisk preflight evidence after NODE-032AQ classified the Asterisk host as unreachable.

```text
repository_docs_only=true
coordinator_collected_read_only_server_evidence=true
live_smoke=false
phase_b=false
audio_generated=false
audio_uploaded=false
temp_env_created=false
helper_deploy=false
token_handling=false
service_action=false
dependency_install=false
reboot_or_power_cycle=false
firewall_or_env_change=false
server_file_change=false
server_state_change=false
transcript_text_or_delta_logging=false
business_dialog_integration=false
```

Handoff archive:

```text
docs/handoffs/NODE-032AR-rerun-actual-speech-smoke-preflight-after-asterisk-reachability-recovery-codex-handoff.md
```

## Input Evidence

The coordinator supplied read-only evidence. Codex did not access the server again for this documentation update.

Fallback and recovery context:

```text
selectel_disk_image_exists_as_fallback=true
disk_image_touched=false
server_started_out_of_band_by_user_provider_action=true
codex_power_action=false
```

Reachability and host:

```text
tcp_22_reachable=true
ssh_login=ok
ping_timeout=true
host=tula
os=Ubuntu 24.04.3 LTS
kernel=6.8.0-53-generic
uptime_at_check=12_min
user=root
```

## Asterisk Status

```text
systemctl_is_active_asterisk=inactive
systemctl_is_enabled_asterisk=not-found
systemctl_status_asterisk=Unit asterisk.service could not be found
asterisk_process_running=true
asterisk_process_user=tulauser
asterisk_process=/usr/sbin/asterisk -vvvdddf -T -W -U asterisk -p
```

Interpretation:

```text
asterisk_systemd_unit_absent=true
asterisk_runtime_process_present=true
```

The absent `asterisk.service` unit is recorded as observed state, not a blocker by itself, because the runtime process is present.

## AI Secretary Status

```text
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
ai_secretary_ari_main_pid=3805
ai_secretary_process_running=true
ai_secretary_process=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -u -m ai_secretary.telephony.ari_app
ready_waiting_for_calls=true
system_sounds_done=true
```

Interpretation:

```text
ai_secretary_service_ready=true
```

## Listener And Process Summary

```text
ssh_tcp_22_listening=true
tcp_7077_listening=true
udp_7077_listening=true
tcp_8088_listening=true
rtp_udp_10000_10100_listening_via_docker_proxy=true
docker_proxy_ports_present=true
```

## NODE-032AQ Blocker Reassessment

```text
asterisk_ssh_timeout_resolved=true
provider_control_unavailable_still_recorded_for_NODE_032AQ=true
power_on_occurred=false
power_state_remains_not_managed_by_repo_tooling=true
future_phase_b_preconditions_can_be_reconsidered=true
phase_b_still_requires_exact_approval_phrase=true
```

NODE-032AR does not approve or run Phase B. It only records that the prior Asterisk SSH timeout is resolved according to coordinator evidence.

`ping_timeout=true` remains recorded, but it is not blocking because TCP 22 is reachable and SSH login works.

## Future Boundary

Future NODE-032AP Phase B or successor live smoke work remains blocked until:

```text
exact_approval_phrase_present=true
immediate_hard_gates_rechecked=true
no_token_output=true
no_transcript_text_or_delta_logging=true
business_dialog_transcript_use_disabled=true
```

The known approval phrase for the original NODE-032AP Phase B remains:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```

## Safety Result

```text
live_smoke=false
phase_b=false
call_run=false
audio_generated=false
audio_uploaded=false
helper_deploy=false
temp_env_created=false
token_handling=false
token_values_printed=false
app_env_changed=false
firewall_changed=false
service_config_changed=false
service_action=false
server_state_changed=false
transcript_text_logged=false
transcript_delta_logged=false
audio_or_binary_artifact_added=false
server_dump_or_log_artifact_added=false
disk_image_touched=false
```

## Validation

Local validation for this docs-only node:

```text
focused_suite=55_passed
git_diff_check=passed
source_runtime_diff=empty
```
