# NODE-032AQ / Restore Asterisk Reachability For Controlled Smoke Preflight

## Scope

NODE-032AQ is an infrastructure reachability node after NODE-032AP Phase A stopped on Asterisk SSH timeout.

```text
branch=feat/node-032aq-restore-asterisk-reachability-for-controlled-smoke-preflight
scope=asterisk_reachability_only
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
docs/handoffs/NODE-032AQ-restore-asterisk-reachability-for-controlled-smoke-preflight-codex-handoff.md
```

## Current Context

Latest merged master was confirmed:

```text
master_head=77c5b249211969147b1b3824d6475ff0d040e8b1
```

NODE-032AP Phase A stopped before Gateway checks because the first required server gate failed:

```text
phase=Phase_A_read_only_preflight_only
phase_b_recommendation=NO_GO
blocker=asterisk_ssh_timeout
asterisk_host=92.118.85.117
asterisk_port=22
gateway_checks_run=false
live_smoke=false
```

## Local Validation

Local validation passed:

```text
focused_suite=55_passed
git_diff_check=passed
source_runtime_diff=empty
```

Focused command:

```text
python -m pytest tests/test_realtime_gateway.py tests/test_gateway_stt_adapter.py tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py
```

## Reachability Procedure Result

Windows network check:

```text
target=92.118.85.117:22
tcp_22_reachable=false
tcp_check_result=timed_out_with_tcp_connect_failure
icmp_ping_result=timed_out
```

Bounded SSH probe:

```text
ssh_probe=failed
ssh_probe_result=connect_timeout
ssh_timeout_seconds=15
```

No read-only remote status commands were able to execute because SSH never became reachable.

## Power-State Control

Power-state recovery was not available from the repository or current tooling:

```text
power_state_check_available=false
power_on_available=false
power_on_occurred=false
provider_console_or_api_available=false
```

No provider power-on, reboot, power-cycle, service action, or server-state change occurred.

## Classification

Primary classification:

```text
provider_control_unavailable
```

Secondary classification:

```text
unknown_reachability_failure
```

Reason:

```text
network_port_22_timeout_observed=true
ping_timeout_observed=true
ssh_timeout_observed=true
power_state_could_not_be_checked_from_available_tools=true
```

## Blockers

```text
asterisk_ssh_reachable=false
asterisk_power_state_unknown=true
provider_power_control_unavailable=true
```

## Next Recommendation

Recommended next action:

```text
perform_out_of_band_provider_or_network_recovery_for_asterisk_host
```

After an operator externally confirms Asterisk host reachability on `92.118.85.117:22`, the next repo node should rerun read-only Asterisk and Gateway preflight gates before requesting any NODE-032AP Phase B approval.

Suggested next node:

```text
NODE-032AR / rerun-actual-speech-smoke-preflight-after-asterisk-reachability-recovery
```

## Safety Result

```text
smoke_run=false
phase_b_run=false
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
```
