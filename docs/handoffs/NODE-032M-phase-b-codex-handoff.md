# NODE-032M Phase B Codex Handoff

This handoff archives NODE-032M Phase B in sanitized form.

Do not include real secrets, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts in this file.

## Approval

Exact approval phrase was provided:

```text
APPROVE NODE-032M SAFE TEMP-ENV ENABLE/REBOOT/SMOKE RETRY
```

## Scope Boundary

NODE-032M Phase B was limited to hard-gate re-confirmation, NODE-032L safe temp-env handling, Gateway service readiness/enable/reboot proof, one Asterisk-side smoke attempt, rollback, cleanup, and documentation.

No provider power-cycle, business dialog enablement, transcript text logging, token output, `443`, `8081`, TLS/proxy change, firewall broadening, Asterisk env change, Notion write, Runtime/Evidence update, scheduler, webhook, automation, GitHub push, or PR occurred.

## Hard Gates

Asterisk gate:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service=active_enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
business_dialog_unchanged=true
```

Gateway gate:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
service_active_before=inactive
service_enabled_before=disabled
gateway_user_group=present
env_present=true
env_owner_mode=root:gateway 640
openai_api_key_presence=masked_present
gateway_token_presence=masked_present
workdir_present=true
listener_8080_before=absent
forbidden_listeners_443_8081=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
rollback_tools=available
```

No env values, token values, bearer headers, private keys, raw secret env output, transcript text, logs, audio, or binary artifacts were printed.

## Safe Temp Env

Temporary helper bundle:

```text
path=/tmp/node032m-asterisk-helper
guard=scripts/gateway_smoke_temp_env_guard.py
helper=scripts/asterisk_gateway_smoke_helper.py
safe_audio=/tmp/node032m-smoke.wav
```

Safe temp-env guard result:

```text
first_create_attempt=failed_closed_missing_stdin_token_due_command_quoting
first_create_secret_values_printed=false
create_retry=ok
validate=ok
temp_env_path=/tmp/node032m-gateway-client.env
temp_env_mode=600
token_input=stdin_pipeline_only
token_values_printed=false
transcript_text_printed=false
```

The first create attempt received no token because the token-extraction command was misquoted. The guard failed closed and printed only safe JSON. The corrected create command piped Gateway token material directly into guard stdin and printed only masked JSON.

## Service Enable / Reboot

Pre-reboot readiness:

```text
manual_start=ok
service_active_after_start=active
service_enabled_before_enable=disabled
listener_after_start=8080 only
forbidden_listeners_after_start=absent
ufw_8080_allow=92.118.85.117 only
log_sensitive_pattern=absent
```

Enable and reboot:

```text
systemctl_enable=true
service_enabled_after_enable=enabled
gateway_only_reboot=true
ssh_returned=true
post_reboot_service_active=active
post_reboot_service_enabled=enabled
post_reboot_listener=8080 only
post_reboot_forbidden_listeners_443_8081=absent
post_reboot_ufw_8080_allow=92.118.85.117 only
post_reboot_log_sensitive_pattern=absent
```

## Smoke Attempt

Exactly one Asterisk-side smoke helper invocation was attempted:

```text
controlled_smoke_attempted=true
gateway_request_reached=false
openai_realtime_from_gateway=not_run
transcript_present=not_run
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
adapter_default_enabled_after_smoke=not_run
```

Blocker:

```text
smoke_blocker=incomplete_temporary_helper_bundle_missing_ai_secretary.config
error_type=ModuleNotFoundError
missing_module=ai_secretary.config
token_values_printed=false
transcript_text_printed=false
```

The helper failed before any Gateway request because the temporary bundle included `src/ai_secretary/__init__.py`, which imports `ai_secretary.config.settings`, but the bundle did not include `ai_secretary.config`. No token value or transcript text was printed.

## Rollback / Cleanup

Rollback result:

```text
systemctl_disable=true
systemctl_stop=true
final_service_active=inactive
final_service_enabled=disabled
final_target_listeners_443_8080_8081=absent
firewall_changed=false
env_owner_mode=root:gateway 640
log_sensitive_pattern=absent
```

Asterisk cleanup:

```text
temp_env_cleanup_guard=ok
temp_env_removed=true
helper_bundle_removed=true
temp_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
```

Token rotation was not required because no token value was printed.

## Next Recommendation

```text
NODE-032N / complete-safe-asterisk-helper-bundle-and-retry-plan
```

NODE-032N should fix the helper-bundle completeness issue without printing tokens or transcript text. A future live retry must require a new exact approval phrase and immediate hard-gate re-confirmation.

