# NODE-032U Phase B Codex Handoff

## Scope

NODE-032U Phase B ran the controlled Gateway smoke retry with repo-created, repo-validated `24000 Hz mono 16-bit PCM` audio.

Approval phrase:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

No dependency install, `systemctl enable`, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, stereo/dual-channel change, `443`, `8081`, TLS/proxy change, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

No token values or transcript text are included in this handoff.

## Hard Gate Reconfirmation

Asterisk `92.118.85.117`:

```text
ssh=reachable
hostname=tula
uptime_recorded=true
ai-secretary-ari.service=active_enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
selected_runtime_present=true
python_version=3.12.3
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

Gateway `45.61.48.199`:

```text
ssh=reachable
hostname=ai-secretary-gateway-node023
uptime_recorded=true
unit_present=true
unit_verify=OK
service_before=inactive_disabled
gateway_user_group=present
gateway_env=present
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
workdir_present=true
target_listeners_443_8080_8081_before=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
```

## Helper Bundle Result

```text
local_bundle_first_path=C:\tmp\node032u-helper-bundle
local_bundle_first_path_result=failed_closed_PermissionError
local_bundle_workspace_retry=ok
local_bundle_validate=ok
remote_bundle_staged=true
remote_validator_added_to_temp_bundle=true
remote_bundle_validate=ok
runtime_modules_ok=true
missing_runtime_modules=[]
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

## Valid Audio Result

Created and validated on Asterisk through `scripts/asterisk_gateway_smoke_helper.py`:

```text
audio_path=/tmp/node032u-smoke.wav
sample_rate_hz=24000
channels=1
sample_width_bytes=2
compression=NONE
frame_count=24000
audio_format_errors=[]
reject_16000hz_guard=implemented
reject_8000hz_guard=covered_by_exact_sample_rate_guard
reject_stereo_guard=implemented
stereo_dual_channel_changes=false
```

## Safe Temp Env Result

```text
token_source=Gateway env piped to guard stdin only
token_values_printed=false
temp_env_create=ok
temp_env_validate=ok
temp_env_mode=600
token_present_masked=true
temp_env_cleanup=ok
temp_env_absent_after_cleanup=true
```

## Gateway Service Readiness

```text
service_before=inactive
service_start_issued=true
service_after_start=active
service_enabled_state=disabled
listener_8080=present
listener_443=absent
listener_8081=absent
ufw_8080_allow=92.118.85.117 only
log_secret_or_transcript_text_pattern=absent
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_change=false
```

## Controlled Smoke Result

Exactly one Asterisk-side smoke invocation ran.

```text
controlled_smoke_invocations=1
origin=Asterisk
audio_format=24000 Hz mono 16-bit PCM WAV
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
accepted=false
fallback_reason=gateway_stt_dialog_use_disabled
```

`accepted=false` is expected for this non-business-dialog smoke because `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remains enforced. Transport/auth/OpenAI Realtime proof passed; the prior invalid-audio blocker is resolved.

## Final State

```text
ai-secretary-gateway.service=inactive
ai-secretary-gateway.service_enabled=disabled
target_listeners_443_8080_8081=absent
firewall=unchanged
ufw_8080_allow=92.118.85.117 only
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
temporary_helper_bundle_removed=true
temporary_env_removed=true
temporary_audio_removed=true
local_temp_bundle_removed=true
```

## Validation

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_scan=no_real_secret_values_found; masked/status fields only
```

## Next Recommendation

```text
NODE-032V / gateway-smoke-result-acceptance-and-next-boundary-decision
```

NODE-032V should decide whether the HTTP 200 / OpenAI Realtime OK / chunks sent result is sufficient for the current non-business-dialog retry objective, or whether a future node should use non-sensitive speech content to prove `transcript_present=true` while still keeping transcript text redacted and business dialog unchanged.
