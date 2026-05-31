# NODE-032U / controlled-gateway-smoke-retry-with-valid-24khz-audio

## Purpose

Fix the NODE-032T audio blocker by preparing a repo-owned, validation-gated smoke WAV path that produces `24000 Hz mono 16-bit PCM` audio before any future Asterisk-side Gateway smoke retry.

Phase A is local implementation, documentation, and command planning only. It does not run live smoke retry.

Handoff archive:

```text
docs/handoffs/NODE-032U-phase-a-codex-handoff.md
```

## Approval Gate

Future Phase B requires the exact phrase:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

Any other phrase is not approval.

## Context

NODE-032T Phase B ran exactly one Asterisk-side smoke. The Gateway was reachable and auth succeeded, but the Gateway returned HTTP 400 because the synthetic WAV was `16000 Hz`. The Gateway requires `24000 Hz mono 16-bit PCM`.

NODE-032T final state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
gateway_env_meta=root:gateway:640
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
```

## Phase A Local Findings

Inspected:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/asterisk_gateway_helper_bundle.py
tests/test_asterisk_gateway_smoke_helper.py
docs/nodes/NODE-032T-controlled-gateway-smoke-retry-after-asterisk-runtime-readiness.md
```

Findings:

```text
smoke_helper_previously_generated_audio=false
node032t_bad_audio_source=phase_b_ad_hoc_remote_python_snippet
bad_audio_sample_rate_hz=16000
required_audio=24000 Hz mono 16-bit PCM WAV
gateway_contract_source=src/ai_secretary/stt/realtime_measurement.py
helper_bundle_already_contains_smoke_helper=true
```

## Phase A Implementation

Updated `scripts/asterisk_gateway_smoke_helper.py` to own safe smoke audio creation and validation:

```text
create_command=python scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <path>
validate_command=python scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <path>
smoke_command=python scripts/asterisk_gateway_smoke_helper.py --audio <path>
sample_rate_hz=24000
channels=1
sample_width=16-bit PCM
codec=PCM WAV
synthetic_content=non_transcript_tone
```

The `--audio` path now validates audio locally before delegating to `ai_secretary.stt.gateway_adapter_smoke`. Invalid `16000 Hz`, stereo, non-PCM, malformed, missing, or empty audio fails closed before a Gateway request.

Safety preserved:

```text
OPENAI_API_KEY_on_Asterisk=refused
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false required
STT_GATEWAY_LOG_TRANSCRIPT=false required
gateway_url_token_newline_material=rejected
secret_values_printed=false
transcript_text_logged=false
business_dialog_unchanged=true
```

No Gateway code, service config, runtime env, firewall, dependency, or business dialog behavior changed.

## Audio Policy

Decision:

```text
node032u_audio_format=24000 Hz mono 16-bit PCM WAV
use_8khz=false
use_16000hz=false
use_stereo=false
use_dual_channel=false
gateway_change=false
```

Rationale:

- `24000 Hz mono 16-bit PCM` matches the current Gateway/Realtime measurement contract.
- NODE-032T already proved the Gateway rejects `16000 Hz`.
- Stereo or dual-channel audio would change the architecture and is out of scope.
- Future caller/callee dual-channel handling, if needed, should be a separate architecture node.

## Phase B Plan

Phase B may proceed only after the exact approval phrase and immediate hard-gate re-confirmation.

Approval:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

Hard gate re-checks:

```text
ssh root@92.118.85.117 "<hostname/uptime/ari-service/env-absence/business-dialog checks>"
ssh root@92.118.85.117 "<selected venv Python/pip/import/runtime-module checks>"
ssh root@45.61.48.199 "<gateway unit/service/user/env/listener/UFW masked checks>"
```

Selected Asterisk runtime:

```text
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python
```

Helper bundle:

```text
python scripts/asterisk_gateway_helper_bundle.py create --output <local_temp_bundle_dir>
python scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <local_temp_bundle_dir>
scp -r <local_temp_bundle_dir> root@92.118.85.117:<remote_temp_bundle_dir>
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_helper_bundle.py validate --bundle-root <remote_temp_bundle_dir>'
```

Valid audio create/validate:

```text
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <remote_temp_audio>'
ssh root@92.118.85.117 '<selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <remote_temp_audio>'
```

Safe temp-env guard:

```text
<gateway token supplied through stdin only> | <selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py create --output <remote_temp_env> --gateway-url http://45.61.48.199:8080
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py validate --path <remote_temp_env>
<selected_runtime> <remote_temp_bundle_dir>/scripts/gateway_smoke_temp_env_guard.py cleanup --path <remote_temp_env>
```

Gateway readiness if needed:

```text
ssh root@45.61.48.199 'systemctl start ai-secretary-gateway.service'
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service'
ssh root@45.61.48.199 '<listener/firewall/log-redaction checks>'
```

Do not run `systemctl enable`.

Smoke:

```text
ssh root@92.118.85.117 '<load remote temp env without printing values; <selected_runtime> <remote_temp_bundle_dir>/scripts/asterisk_gateway_smoke_helper.py --audio <remote_temp_audio>'
```

Smoke boundary:

```text
smoke_count=1
origin=Asterisk
business_dialog_enablement=false
transcript_text_logging=false
token_output=false
expected_audio=24000 Hz mono 16-bit PCM
```

Cleanup and final state:

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

Expected final target state:

```text
gateway_service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted
asterisk_OPENAI_API_KEY=ABSENT
business_dialog=unchanged
```

## GO / NO-GO

Current recommendation:

```text
phase_b_recommendation=CONDITIONAL_GO
condition=exact_approval_phrase_and_immediate_hard_gate_reconfirmation
current_blocker=approval_phrase_absent
```

Hard NO-GO if:

- Asterisk contains `OPENAI_API_KEY`.
- Business dialog Gateway transcript use is enabled.
- Selected project venv is missing or import checks fail.
- Runtime dependency preflight fails.
- Safe temp-env guard is unavailable or fails validation.
- Helper bundle preflight fails.
- Smoke audio is not exactly `24000 Hz mono 16-bit PCM`.
- Token would be printed by any command.
- Transcript text would be printed.
- Gateway env is missing or not `root:gateway 640`.
- Masked Gateway secret presence fails.
- Gateway service unit is missing or invalid.
- Unexpected listener exists on `443` or `8081`.
- UFW `8080/tcp` is not source-restricted to `92.118.85.117`.
- Rollback plan is unclear.
- Exact approval phrase is absent.

## Validation

Phase A validation result:

```text
focused_tests=35 passed
full_pytest=230 passed, 6 failed
known_environmental_failures=missing src/scripts/make_demo_audio.py; missing sentence_transformers
git_diff_check=pass
source_runtime_diff_check=scripts/asterisk_gateway_smoke_helper.py; tests/test_asterisk_gateway_smoke_helper.py
tracked_secret_scan=no_real_secret_values_found; existing placeholders/status-field/test-fixture hits only
scoped_docs_handoff_source_test_scan=no_real_secret_values_found; status-field hits only
```

Validation commands:

```text
git status --short
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032U-phase-a-codex-handoff.md docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md docs/master scripts tests
git status --short
```

Known full-suite environmental failures, if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```
