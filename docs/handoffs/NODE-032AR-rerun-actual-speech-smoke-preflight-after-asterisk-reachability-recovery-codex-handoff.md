# NODE-032AR Codex Handoff

Node:

```text
NODE-032AR / rerun-actual-speech-smoke-preflight-after-asterisk-reachability-recovery
```

Scope:

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
firewall_or_env_change=false
server_file_change=false
server_state_change=false
transcript_text_or_delta_logged=false
```

## Context

NODE-032AQ had classified the Asterisk host as unreachable:

```text
previous_blockers=asterisk_ssh_timeout,provider_control_unavailable,unknown_reachability_failure
power_on_occurred=false
```

The coordinator later collected read-only server evidence out of band and accepted it for repository documentation. Codex did not access servers for this closeout.

Additional context:

```text
selectel_disk_image_exists_as_fallback=true
disk_image_touched=false
server_started_out_of_band_by_user_provider_action=true
codex_power_action=false
```

## Coordinator Evidence

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

Asterisk status:

```text
systemctl_is_active_asterisk=inactive
systemctl_is_enabled_asterisk=not-found
systemctl_status_asterisk=Unit asterisk.service could not be found
asterisk_process_running=true
asterisk_process_user=tulauser
asterisk_process=/usr/sbin/asterisk -vvvdddf -T -W -U asterisk -p
```

AI Secretary status:

```text
ai_secretary_ari_service_active=active
ai_secretary_ari_service_enabled=enabled
ai_secretary_ari_main_pid=3805
ai_secretary_process_running=true
ai_secretary_process=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python -u -m ai_secretary.telephony.ari_app
ready_waiting_for_calls=true
system_sounds_done=true
```

Listeners and process summary:

```text
ssh_tcp_22_listening=true
tcp_7077_listening=true
udp_7077_listening=true
tcp_8088_listening=true
rtp_udp_10000_10100_listening_via_docker_proxy=true
docker_proxy_ports_present=true
```

## Interpretation

```text
asterisk_ssh_timeout_resolved=true
asterisk_systemd_unit_absent=true
asterisk_runtime_process_present=true
ai_secretary_service_ready=true
future_phase_b_preconditions_can_be_reconsidered=true
phase_b_still_requires_exact_approval_phrase=true
```

The important operational distinction is that `asterisk.service` is absent from systemd, while the Asterisk runtime process is present under `tulauser`. Future gates should not require `asterisk.service` to exist unless the architecture changes.

`ping_timeout=true` is recorded, but it is not blocking for this evidence node because TCP 22 is reachable and SSH login works.

Future approval phrase remains required and was not used:

```text
APPROVE NODE-032AP PHASE B LIVE SMOKE
```

## Safety Boundary

```text
live_smoke=false
phase_b=false
audio_generated=false
helper_deploy=false
temp_env_created=false
token_handling=false
service_action=false
firewall_or_env_change=false
server_state_change=false
transcript_text_or_delta_logged=false
disk_image_touched=false
```

No token values, transcript text, transcript deltas, actual spoken phrase, audio content, binary artifacts, raw env output, server dumps, or server logs are included in this handoff.
