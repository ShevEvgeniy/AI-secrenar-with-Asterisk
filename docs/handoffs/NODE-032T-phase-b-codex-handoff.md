# NODE-032T Phase B Codex Handoff

This archive records the sanitized NODE-032T Phase B execution. It intentionally excludes real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, raw logs, audio, and binary artifacts.

## Scope

```text
node=NODE-032T / controlled-gateway-smoke-retry-after-asterisk-runtime-readiness
phase=Phase B
approval_phrase=APPROVE NODE-032T GATEWAY SMOKE RETRY AFTER RUNTIME READINESS
branch=feat/node-032t-controlled-gateway-smoke-retry-after-asterisk-runtime-readiness
phase_a_checkpoint=0b66d4dd6b1be7f85ca2e05cba8d6d1da7d77381
```

Servers were stopped after Phase A and later made reachable again, so all Phase A live gates were treated as stale and re-run before helper staging, token handling, temp env creation, service action, or smoke.

## Hard Gate Reconfirmation

Asterisk `92.118.85.117`:

```text
ssh_reachable=true
hostname=tula
uptime_recorded=true
ai-secretary-ari.service=active/enabled
process_OPENAI_API_KEY=ABSENT
service_OPENAI_API_KEY=ABSENT
env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
selected_venv_PRESENT=true
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
python=3.12.3
pip=26.1.1
runtime_imports_OK=true
httpx=0.28.1
fastapi=0.136.1
websockets=16.0
```

Gateway `45.61.48.199`:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_recorded=true
gateway_unit_PRESENT=true
gateway_unit_verify=OK
gateway_service_before=inactive
gateway_service_enabled_before=disabled
gateway_user_PRESENT=true
gateway_group_PRESENT=true
gateway_env_PRESENT=true
gateway_env_meta=root:gateway:640
gateway_OPENAI_API_KEY=MASKED_PRESENT
gateway_GATEWAY_TOKEN=MASKED_PRESENT
gateway_workdir_PRESENT=true
target_listeners_443_8080_8081_before=ABSENT
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
```

One early Asterisk runtime import command had a local quoting failure before producing useful gate output. It did not change server state. The gate was rerun successfully with stdin-fed Python and sanitized output.

## Helper Bundle Result

Local helper bundle:

```text
local_create_ok=true
local_validate_ok=true
files_copied=manifest files only
runtime_modules_required=httpx,fastapi,websockets
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

Remote staged helper bundle:

```text
remote_helper_path=/tmp/node032t-asterisk-helper
remote_validator_copied=true
remote_validate_ok=true
runtime_modules_ok=true
missing_runtime_modules=[]
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

## Safe Temp Env Result

The Gateway token was supplied through a process pipe from the Gateway host to the Asterisk temp-env guard stdin only. No token value was echoed, printed, copied into docs, or displayed in chat.

```text
temp_env_path=/tmp/node032t-gateway-client.env
create_ok=true
validate_ok=true
temp_env_mode=600
token_present_masked=true
secret_values_printed=false
transcript_text_logged=false
cleanup_ok=true
temp_env_absent_after_cleanup=true
```

## Gateway Service Readiness

```text
service_started_for_smoke=true
service_active_after_start=true
service_enabled_state=disabled
listener_8080_after_start=present
listener_443_after_start=absent
listener_8081_after_start=absent
ufw_8080_allow=92.118.85.117 only
fixed_string_log_sk_literal=absent
fixed_string_log_bearer_literal=absent
fixed_string_log_env_assignment_literals=absent
fixed_string_log_transcript_text_literal=absent
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_change=false
```

The first listener check immediately after start returned absent, then a delayed recheck showed `0.0.0.0:8080` present while `443` and `8081` remained absent.

## Controlled Smoke Result

Exactly one Asterisk-side helper invocation was run.

```text
controlled_smoke_invocations=1
origin=Asterisk
selected_runtime=/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
helper=/tmp/node032t-asterisk-helper/scripts/asterisk_gateway_smoke_helper.py
gateway_reachable_from_asterisk=true
gateway_auth=ok
gateway_http_status=400
error_type=gateway_audio_invalid
error_code=invalid_wav
failure_reason=synthetic_smoke_wav_sample_rate_16000_but_gateway_requires_24000_mono_16bit_pcm
openai_realtime_from_gateway=failed
chunks_sent=0
transcript_present=false
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=false
accepted=false
```

The Gateway request was reached and authenticated, but OpenAI Realtime/session/audio streaming did not run because the Gateway rejected the synthetic WAV before audio send. No retry was run because NODE-032T allowed exactly one controlled smoke invocation.

## Cleanup And Final State

Asterisk cleanup:

```text
temp_env_absent=true
helper_bundle_absent=true
temp_audio_absent=true
asterisk_process_OPENAI_API_KEY=ABSENT
asterisk_env_file_OPENAI_API_KEY=ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
```

Gateway rollback/final state:

```text
rollback_stop_service=true
ai-secretary-gateway.service=inactive
ai-secretary-gateway.service_enabled=disabled
listener_443=absent
listener_8080=absent
listener_8081=absent
ufw_8080_allow=92.118.85.117 only
gateway_env_meta=root:gateway:640
gateway_masked_secret_presence=pass
```

Local cleanup:

```text
local_temp_bundle_path=C:\Projects\AI-secrenar-with-Asterisk\node032t-helper-bundle-temp
local_temp_bundle_removed_after_validation=true
```

## Blocker And Next Node

```text
node_result=blocked_after_single_smoke
blocker=smoke_audio_invalid_16000_hz
next_node=NODE-032U / controlled-gateway-smoke-retry-with-valid-24khz-audio
```

The next node should prepare or select a known-valid non-sensitive 24 kHz mono 16-bit PCM smoke WAV before any further live retry. It should keep the same hard gates, selected runtime, helper bundle, safe temp-env, token redaction, and cleanup boundaries.

## Validation

```text
focused_tests=31 passed
full_pytest=226 passed, 6 failed
full_pytest_failures=known_environmental
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=empty
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_scan=no_real_secret_values_found; masked/status/placeholders only
local_temp_bundle_absent=true
```

## Safety Confirmations

```text
dependency_install=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
port_443=false
port_8081=false
tls_proxy=false
firewall_broadening=false
server_env_edit=false
token_values_printed=false
transcript_text_printed=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation=false
course_submission_touched=false
data_storage_touched=false
node014_server_tar_touched=false
```
