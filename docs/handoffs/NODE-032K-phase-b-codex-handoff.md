# NODE-032K Phase B Codex Handoff

This handoff archives the NODE-032K Phase B attempt in sanitized form.

Do not include real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, large logs, audio, or binary artifacts in this file.

## Scope

Approved exact phrase:

```text
APPROVE NODE-032K SERVICE ENABLE/REBOOT/SMOKE
```

Approved Phase B scope was to re-confirm hard gates, manually start/check the staged gateway service, enable it, reboot the Gateway server only, verify auto-start, verify listener/firewall/log redaction, run one Asterisk-side non-business-dialog smoke, and document final state/rollback.

Forbidden items remained out of scope: provider power-cycle, business dialog enablement, transcript text logging, `443`, `8081`, TLS/proxy changes, firewall broadening, Asterisk env changes, Notion write, Runtime/Evidence update, scheduler/webhook/automation, GitHub push/PR, and token output.

## Gate Results

```text
asterisk_ssh=ok
asterisk_hostname=tula
asterisk_service=active_enabled
asterisk_process_openai_api_key=OPENAI_API_KEY_ABSENT
asterisk_service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
gateway_ssh=ok
gateway_hostname=ai-secretary-gateway-node023
gateway_unit_present=true
gateway_unit_verify=ok
gateway_service_active_before_phase_b=inactive
gateway_service_enabled_before_phase_b=disabled
gateway_user_group=gateway:gateway present
gateway_env_owner_mode=root:gateway 640
gateway_secret_presence=masked_pass
target_listeners_before_phase_b=none_on_443_8080_8081
ufw_active=true
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
rollback_tools_available=true
```

No env values were intentionally printed during gate checks.

## Apply Result Before Blocker

```text
manual_start=true
manual_start_service_active=true
manual_start_listener=8080 only
systemctl_enable=true
gateway_only_reboot=true
post_reboot_ssh_returned=true
post_reboot_service_active=true
post_reboot_service_enabled=true
post_reboot_listener=8080 only
post_reboot_listener_443=false
post_reboot_listener_8081=false
post_reboot_ufw_8080_allow=92.118.85.117 only
post_reboot_log_sensitive_pattern_absent=true
```

No provider power-cycle occurred. No firewall, env file, TLS/proxy, `443`, or `8081` change occurred.

## Hard NO-GO

During temporary Asterisk smoke env preparation, a malformed env file caused the first helper invocation to fail closed. A subsequent diagnostic intended to print only key names and masked presence instead printed a token value because the temporary env file contained literal separators rather than real newline-separated assignments.

The token value is not recorded here.

Result:

```text
hard_no_go=true
reason=token_value_printed_during_temporary_env_diagnostic
controlled_smoke_run=false
gateway_request_from_smoke=false
transcript_text_printed=false
business_dialog_enabled=false
```

Token rotation is required before any future gateway smoke or production use.

## Rollback And Cleanup

Rollback was performed immediately after the hard NO-GO:

```text
systemctl_disable=true
systemctl_stop=true
final_service_enabled=disabled
final_service_active=inactive
final_target_listeners_443_8080_8081=absent
firewall_changed=false
temporary_helper_bundle_removed=true
temporary_runtime_env_removed=true
temporary_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
```

The staged systemd unit remains installed. The final service state is disabled and inactive.

## Required Follow-Up

```text
go_no_go_for_next_node=NO-GO_until_newline_safe_temp_env_retry_plan
required=rotate_exposed_gateway_token
required=replace_temp_env_creation_with_newline-safe_method
required=verify_temp_env_keys_without_printing_values
required=reconfirm_hard_gates_before_any_retry_state_change
next_node=NODE-032L / newline-safe-gateway-smoke-temp-env-and-retry-plan
```

Provider power-cycle, business dialog integration, TLS/proxy, `443`, `8081`, and firewall broadening remain out of scope unless separately approved.

## Security Remediation Addendum

The exposed Gateway token was rotated on the Gateway host only. The old token and new token were not printed or recorded.

Sanitized result:

```text
gateway_token_rotated=true
env_owner_mode_after=root:gateway:640
gateway_token_presence_after=GATEWAY_TOKEN_PRESENT_MASKED
service_active_after=inactive
service_enabled_after=disabled
target_listeners_443_8080_8081_after=absent
ufw_changed=false
ufw_8080_allow=92.118.85.117 only
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
smoke_retry=false
systemctl_enable=false
reboot=false
provider_power_cycle=false
```

The token-rotation blocker is resolved. The temporary env creation/verification path blocker remains open before any retry.
