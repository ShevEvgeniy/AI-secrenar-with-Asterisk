# NODE-032Z Phase A Codex Handoff

## Node

```text
NODE-032Z / controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

Branch:

```text
feat/node-032z-controlled-transcript-event-diagnostics-smoke-with-redacted-counts
```

Base:

```text
master_head=b85300848c7b3a4bfe93489a34be5fe92a6f7edc
latest_closed_node=NODE-032Y / safe-transcript-event-diagnostics-with-redacted-event-counts
```

## Phase A Scope

Phase A is read-only readiness and command planning only. It does not run a live smoke.

Exact future Phase B approval phrase:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Any other phrase is not approval.

## External Precheck

Operator reported SSH reachability before Phase A:

```text
Asterisk 92.118.85.117 port 22 reachable
Gateway 45.61.48.199 port 22 reachable
```

Because servers were powered on after a pause, all live gates are treated as stale until Phase B immediately re-confirms them.

## Read-Only Gate Results

Asterisk server:

```text
host=tula
ssh_reachable=true
whoami=root
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
listener_summary=22,7077,8088 plus local resolver/containerd listeners
ari_env_metadata=root:tulauser 640 /etc/ai-secretary/ari-app.env
asterisk_env_OPENAI_API_KEY=ABSENT
asterisk_process_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_version=Python 3.12.3
```

Gateway server:

```text
host=ai-secretary-gateway-node023
ssh_reachable=true
whoami=root
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
listener_summary=22 only plus local resolver listeners
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_tcp=ALLOW IN from 92.118.85.117 only
gateway_env_metadata=root:gateway 640 /etc/ai-secretary/openai-realtime-gateway.env
```

## Phase B Readiness

Phase B is conditionally ready to request approval, with mandatory immediate hard-gate re-confirmation before any state-changing command.

Current blockers:

```text
phase_b_approval_phrase_absent=true
live_gates_stale_until_phase_b_recheck=true
```

## Phase B Plan Summary

After exact approval only:

1. Re-confirm Asterisk and Gateway hard gates.
2. Re-confirm Asterisk `OPENAI_API_KEY` absence and business dialog transcript use disabled.
3. Re-confirm Gateway service inactive/disabled, env metadata, listeners, and UFW restriction.
4. Stage helper bundle and safe temp env only if gates pass.
5. Start Gateway service only for smoke readiness if explicitly approved.
6. Run exactly one Asterisk-side non-business-dialog smoke.
7. Capture only redacted NODE-032Y diagnostics: event counts, booleans, buckets, and classification.
8. Cleanup helper/temp/audio artifacts and return Gateway service to the documented final state.

## Forbidden Evidence

Do not collect or record:

```text
token_values
raw_secret_env_output
transcript_text
transcript_delta_text
large_logs
audio_artifacts
binary_artifacts
business_dialog_profile_changes
```

## Safety Confirmation

```text
live_smoke=false
test_call=false
helper_deploy=false
token_handling=false
server_temp_env=false
service_start_stop_restart_reload_enable=false
dependency_install=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
business_dialog_enablement=false
transcript_text_logging=false
notion_write=false
runtime_evidence_update=false
scheduler_webhook_automation=false
```

## Next Step

Do not run Phase B until the exact approval phrase is provided:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

## Phase B Closeout

The exact approval phrase was later provided:

```text
APPROVE NODE-032Z PHASE B LIVE SMOKE
```

Phase B re-confirmed hard gates before state-changing commands.

Asterisk:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service=active_enabled
ari_env_metadata=root:tulauser:640:/etc/ai-secretary/ari-app.env
ari_env_OPENAI_API_KEY=ABSENT
ari_process_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_version=Python 3.12.3
```

Gateway:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_verify=OK
service_before=inactive_disabled
gateway_env_metadata=root:gateway:640:/etc/ai-secretary/openai-realtime-gateway.env
masked_gateway_OPENAI_API_KEY_presence=passed
masked_GATEWAY_TOKEN_presence=passed
target_listeners_443_8080_8081_before=absent
ufw=active_default_deny_8080_from_92.118.85.117_only
```

Helper/temp/audio:

```text
remote_helper_bundle_validate=ok
smoke_audio=24000_Hz_mono_16_bit_PCM_WAV
safe_temp_env_create_validate_cleanup=ok
token_values_printed=false
transcript_text_printed=false
```

One malformed helper CLI invocation failed at argument parsing before any Gateway request because an unsupported flag was supplied. It did not count as the controlled smoke and did not print token values or transcript text.

The corrected helper wrapper then ran exactly one Asterisk-side non-business-dialog smoke:

```text
controlled_smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
transcript_text_logged=false
transcript_used_for_dialog=false
```

NODE-032Y redacted diagnostic result:

```text
openai_event_type_counts={}
openai_event_type_counts_present=false
transcript_event_seen=null
transcript_bearing_event_seen=null
transcript_text_present=false
transcript_text_length_bucket=unknown
input_audio_buffer_commit_sent=null
timeout_observed=null
error_event_seen=null
diagnostic_propagation_gap=true
diagnostic_classification=diagnostic_propagation_gap
```

Closeout classification:

```text
transport_auth_openai_realtime_success=true
redacted_diagnostics_success=false
phase_b_result=blocked_diagnostic_propagation_gap
```

Final state:

```text
ai-secretary-gateway.service=inactive_disabled
target_listeners_443_8080_8081=absent
ufw=unchanged_source_restricted
gateway_env_metadata=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_helper_env_audio_removed=true
local_temporary_helper_bundle_removed=true
systemctl_enable=false
reboot_or_power_cycle=false
firewall_change=false
server_env_edit=false
business_dialog_enablement=false
notion_write=false
runtime_evidence_update=false
github_push_or_pr=false
```

Validation:

```text
focused_tests=47_passed
full_pytest=231_passed_6_failed_known_environmental
known_environmental_failure_1=missing src/scripts/make_demo_audio.py
known_environmental_failure_2=missing sentence_transformers
git_diff_check=pass
source_runtime_diff=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status/test-fixture hits only
scoped_docs_handoff_source_scan=no_real_secret_values_found; policy labels/status placeholders only
audio_binary_artifacts_added=false
```

Next recommendation:

```text
NODE-032AA / gateway-event-diagnostics-propagation-gap-fix
```
