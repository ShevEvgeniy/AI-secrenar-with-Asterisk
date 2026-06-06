# NODE-032W Phase A Codex Handoff

Node:

```text
NODE-032W / controlled-gateway-transcript-presence-smoke
```

Branch:

```text
feat/node-032w-controlled-gateway-transcript-presence-smoke
```

Purpose:

Prepare a controlled Gateway transcript-presence smoke after NODE-032U proved the Asterisk-origin Gateway transport/auth/OpenAI Realtime path with valid `24000 Hz mono 16-bit PCM` audio.

Phase A boundary:

```text
live_smoke_retry=false
helper_copy_deploy=false
token_handling=false
server_temp_env_created=false
dependency_install=false
service_action=false
systemctl_state_action=false
reboot_or_power_cycle=false
firewall_or_env_changed=false
server_state_changed=false
business_dialog_enablement=false
transcript_text_logging=false
notion_write=false
runtime_evidence_update=false
```

No real secrets, token values, private keys, transcript text, raw secret env output, logs, audio, or binary artifacts are included in this handoff.

## Context

NODE-032U proved:

```text
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
openai_session_created=true
chunks_sent=5
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
```

NODE-032V accepted NODE-032U only as successful transport/auth/OpenAI Realtime proof with valid 24 kHz audio. It did not accept NODE-032U as transcript-present success, transcript-quality success, transcript text correctness proof, business-dialog integration proof, production autostart proof, or dual-channel caller/bot separation proof.

## Local Inspection Findings

Inspected:

```text
docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md
docs/nodes/NODE-032V-gateway-smoke-result-acceptance-and-next-boundary-decision.md
scripts/asterisk_gateway_smoke_helper.py
scripts/asterisk_gateway_helper_bundle.py
scripts/gateway_smoke_temp_env_guard.py
tests/test_asterisk_gateway_smoke_helper.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/realtime_gateway.py
```

Helper capability:

```text
safe_audio_create_command=python scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <path>
safe_audio_validate_command=python scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <path>
safe_audio_required_format=24000 Hz mono 16-bit PCM WAV
safe_temp_env_guard=create_validate_cleanup_available
helper_bundle_manifest_validate_available=true
runtime_dependency_preflight_available=true
```

Transcript-presence capability:

```text
adapter_report_transcript_present_flag=true
adapter_report_transcript_event_seen_flag=true
adapter_report_transcript_bearing_event_seen_flag=true
adapter_report_transcript_text_logged_flag=true
adapter_report_transcript_used_for_dialog_flag=true
adapter_report_business_dialog_unchanged_flag=true
```

The adapter and Gateway path can expose transcript event/presence status through safe booleans. The Gateway response includes `transcript_text_present` and redacted diagnostics such as `transcript_event_seen` and `transcript_bearing_event_seen`. Transcript text is removed from safe payloads unless transcript logging and Gateway transcript return are explicitly enabled; NODE-032W must keep transcript logging disabled and business-dialog transcript use disabled.

Readiness conclusion:

```text
phase_b_can_attempt_transcript_presence_with_existing_helper=true
future_local_implementation_node_required_before_phase_b=false
required_acceptance_metric=transcript_event_or_presence_confirmed_without_text
```

## Asterisk Read-Only Gates

Commands were read-only and did not print env values.

Sanitized result:

```text
ssh_reachable=true
hostname=tula
ari_service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_env_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_present=true
selected_runtime_python=3.12.3
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

## Gateway Read-Only Gates

Commands were read-only and did not print env values.

Sanitized result:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=OK
ai-secretary-gateway.service=inactive_disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
opt_gateway_present=true
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
```

## Phase B Approval Gate

Phase B requires the exact phrase:

```text
APPROVE NODE-032W TRANSCRIPT PRESENCE SMOKE
```

Any other phrase is not approval.

## Phase B Command Shape

Phase B must immediately re-confirm hard gates before state-changing commands or token handling.

Hard gates:

```text
ssh root@92.118.85.117 "<hostname/uptime/ari-service/env-absence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/import/runtime-module checks>"
ssh root@45.61.48.199 "<gateway unit/service/user/env/listener/UFW masked checks>"
```

Helper bundle:

```text
python scripts/asterisk_gateway_helper_bundle.py create --output <local_temp_bundle_dir>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_temp_bundle_dir>
scp -r <local_temp_bundle_dir> root@92.118.85.117:<remote_temp_bundle_dir>
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>'
```

Valid audio:

```text
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <remote_temp_audio>'
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <remote_temp_audio>'
```

Safe temp env:

```text
<gateway token supplied through stdin only> | <selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

Gateway readiness only if needed:

```text
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 '<service/listener/firewall/log-redaction checks>'
```

Smoke:

```text
ssh root@92.118.85.117 '<load remote temp env without printing values; <selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --audio <remote_temp_audio>'
```

Acceptance metrics:

```text
controlled_smoke_invocations=1
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=200
openai_realtime_from_gateway=ok
chunks_sent>0
transcript_event_or_presence_confirmed=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
token_values_printed=false
transcript_text_printed=false
```

Cleanup/final state checks:

```text
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
rm -rf <remote_temp_bundle_dir> <remote_temp_audio>
rm -rf <local_temp_bundle_dir>
systemctl stop ai-secretary-gateway.service
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -ltn | grep -e :443 -e :8080 -e :8081 || true
ufw status verbose
```

## GO / NO-GO

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=approval_phrase_absent
```

Hard NO-GO:

```text
asterisk_OPENAI_API_KEY_present
business_dialog_gateway_transcript_use_enabled
selected_asterisk_project_venv_missing_or_import_checks_fail
helper_bundle_preflight_fails
runtime_dependency_preflight_fails
audio_not_exactly_24000hz_mono_16bit_pcm
safe_temp_env_guard_unavailable_or_fails
helper_cannot_report_transcript_presence_without_text
transcript_text_would_be_printed
token_would_be_printed
gateway_env_missing_or_wrong_owner_mode
masked_gateway_secret_presence_fails
gateway_service_unit_missing_or_invalid
unexpected_listener_on_443_or_8081
ufw_8080_not_source_restricted_to_92.118.85.117
rollback_plan_unclear
exact_approval_phrase_absent
```

## Validation

Result:

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_source_test_scan=no_real_secret_values_found; masked/status/placeholders/test-fixture hits only
```
