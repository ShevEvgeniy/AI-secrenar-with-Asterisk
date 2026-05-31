# NODE-032U Phase A Codex Handoff

## Scope

NODE-032U prepares a valid-audio Gateway smoke retry after NODE-032T blocked on invalid synthetic audio.

Phase A is local implementation, documentation, and command planning only.

No live smoke retry, SSH, helper deploy, token handling, server temp env creation, dependency install, service action, reboot, provider power-cycle, firewall change, server env edit, business dialog enablement, Notion write, Runtime/Evidence update, scheduler, webhook, or automation occurred.

## Context

NODE-032T reached and authenticated with the Gateway from Asterisk, but the single smoke returned HTTP 400 because the generated synthetic WAV was `16000 Hz` while the Gateway requires `24000 Hz mono 16-bit PCM`.

NODE-032T final state:

```text
ai-secretary-gateway.service=inactive_disabled
target_listeners_443_8080_8081=absent
firewall=unchanged_source_restricted_to_92.118.85.117
asterisk_OPENAI_API_KEY=ABSENT
temporary_helper_env_audio_removed=true
```

## Local Findings

Inspected:

```text
scripts/asterisk_gateway_smoke_helper.py
scripts/asterisk_gateway_helper_bundle.py
tests/test_asterisk_gateway_smoke_helper.py
docs/nodes/NODE-032T-controlled-gateway-smoke-retry-after-asterisk-runtime-readiness.md
```

Findings:

```text
smoke_helper_audio_generation_before_NODE_032U=absent
node032t_16000hz_source=ad_hoc_phase_b_remote_python_snippet
gateway_required_audio=24000 Hz mono 16-bit PCM WAV
gateway_contract_source=src/ai_secretary/stt/realtime_measurement.py DEFAULT_SAMPLE_RATE=24000
helper_bundle_includes_smoke_helper=true
gateway_code_change=false
```

## Implementation Decision

Selected smallest safe fix:

```text
add_repo_owned_smoke_audio_create_validate_to=scripts/asterisk_gateway_smoke_helper.py
sample_rate_hz=24000
channels=1
sample_width=16-bit PCM
content=synthetic_tone_no_transcript_text
stereo=false
dual_channel=false
8khz=false
gateway_behavior_change=false
```

The helper now supports:

```text
python scripts/asterisk_gateway_smoke_helper.py --create-smoke-audio <path>
python scripts/asterisk_gateway_smoke_helper.py --validate-smoke-audio <path>
python scripts/asterisk_gateway_smoke_helper.py --audio <path>
```

Validation prints safe JSON only and includes no token values or transcript text.

Before delegating to the Gateway smoke module, `--audio` now validates that the WAV is exactly `24000 Hz mono 16-bit PCM` and fails closed if it is not.

## Safety Boundaries

Preserved:

```text
asterisk_OPENAI_API_KEY_refused=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG_false_required=true
STT_GATEWAY_LOG_TRANSCRIPT_false_required=true
gateway_url_token_newline_material_rejected=true
secret_values_printed=false
transcript_text_logged=false
business_dialog_unchanged=true
```

## Phase B Boundary

Future Phase B requires exact approval:

```text
APPROVE NODE-032U 24KHZ AUDIO GATEWAY SMOKE RETRY
```

Phase B must re-confirm hard gates, create/validate the 24 kHz mono 16-bit PCM smoke WAV using the helper, use the NODE-032L safe temp-env guard, use the NODE-032N/NODE-032P helper bundle and runtime preflight, run exactly one Asterisk-side non-business-dialog smoke, and clean up temporary helper/env/audio.

Hard NO-GO if the smoke audio is not exactly:

```text
sample_rate_hz=24000
channels=1
sample_width=16-bit PCM
```

Explicit exclusions:

```text
live_retry_in_phase_a=false
8khz_audio=false
stereo_audio=false
dual_channel_architecture=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
firewall_broadening=false
```

Dual-channel caller/callee audio remains a separate architecture node if needed later.

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

Commands run for Phase A validation:

```text
python -m pytest tests/test_asterisk_gateway_smoke_helper.py tests/test_asterisk_gateway_helper_bundle.py tests/test_gateway_smoke_temp_env_guard.py tests/test_gateway_stt_adapter.py
python -m pytest
git diff --check
git diff --name-only -- src tests deploy scripts pyproject.toml
git grep -n -E "<tracked secret scan pattern>" -- .
rg -n "<scoped token scan pattern>" docs/handoffs/NODE-032U-phase-a-codex-handoff.md docs/nodes/NODE-032U-controlled-gateway-smoke-retry-with-valid-24khz-audio.md docs/master scripts tests
git status --short
```

Known full-suite environmental failures if unchanged:

```text
missing src/scripts/make_demo_audio.py
missing sentence_transformers
```

No real secrets, token values, private keys, transcript text, raw secret env output, logs, audio, or binary artifacts are included in this handoff.
