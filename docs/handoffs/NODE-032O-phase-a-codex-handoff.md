# NODE-032O Phase A Codex Handoff

## Boundary

NODE-032O Phase A is read-only readiness plus smoke retry command planning only.

No live retry, service start/stop/restart/reload/enable, `systemctl` state-changing action, reboot, provider power-cycle, firewall change, server env edit, helper copy/deploy, live smoke, business dialog enablement, transcript text logging, token output, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

This handoff contains no real secrets, token values, bearer headers, private keys, raw secret env output, logs, audio, binary artifacts, or transcript text.

## Context

NODE-032O prepares the first retry after:

```text
NODE-032L safe temp-env guard
NODE-032N complete helper bundle manifest/preflight
```

NODE-032M proved Gateway enable/reboot/autostart but did not complete smoke because the temporary Asterisk helper bundle lacked `ai_secretary.config`. NODE-032N fixed that local bundle completeness blocker.

## Local Findings

Safe temp-env guard:

```text
script=scripts/gateway_smoke_temp_env_guard.py
commands=create,validate,cleanup
token_input=stdin_only
safe_json_only=true
temp_env_mode=0600
newline_material_rejected=true
```

Complete helper bundle:

```text
script=scripts/asterisk_gateway_helper_bundle.py
commands=manifest,create,validate
includes_smoke_helper=true
includes_temp_env_guard=true
includes_ai_secretary_config=true
includes_required_stt_adapter_modules=true
preflight_import_validator=true
secret_values_printed=false
transcript_text_logged=false
```

## Read-Only Asterisk Gate

```text
ssh_reachable=true
hostname=tula
uptime_observed=true
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
business_dialog_unchanged=true
```

## Read-Only Gateway Gate

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime_observed=true
unit_present=true
unit_verify=ok
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_owner_mode=root:gateway 640
openai_api_key_presence=masked_present
gateway_token_presence=masked_present
workdir_present=true
listener_443=absent
listener_8080=absent
listener_8081=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
rollback_systemctl_available=true
```

## Future Phase B Approval

Exact phrase required:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

Any other phrase is not approval.

## Phase B Plan Summary

Phase B must:

- re-confirm all hard gates before any state-changing command;
- create and validate the complete helper bundle;
- stage the complete bundle to a temporary Asterisk path only after approval;
- create/validate/cleanup the runtime temp env with NODE-032L guard;
- supply Gateway token through stdin only;
- start the Gateway service only if needed for smoke readiness;
- run exactly one Asterisk-side non-business-dialog smoke;
- record only safe flags and metrics;
- clean up temporary helper/env/audio;
- keep firewall unchanged.

Explicit exclusions:

```text
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
token_output=false
transcript_text_logging=false
port_443=false
port_8081=false
tls_proxy_change=false
firewall_broadening=false
```

## GO / NO-GO

```text
phase_b_go=conditional_after_exact_approval_and_immediate_hard_gate_recheck
current_blocker=exact_approval_phrase_absent
technical_readiness=pass
```

Hard NO-GO if any gate fails, helper bundle preflight fails, safe temp-env guard validation fails, token or transcript text would be printed, rollback is unclear, or the exact approval phrase is absent.

