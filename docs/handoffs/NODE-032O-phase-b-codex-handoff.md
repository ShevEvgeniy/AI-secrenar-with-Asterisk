# NODE-032O Phase B Codex Handoff

This archive records the sanitized Phase B result for `NODE-032O / controlled-gateway-smoke-retry-with-complete-helper-bundle`.

It intentionally excludes real secrets, token values, bearer headers, private keys, raw env output, transcript text, large logs, audio, and binary artifacts.

## Approval

Exact approval phrase was provided:

```text
APPROVE NODE-032O COMPLETE HELPER-BUNDLE SMOKE RETRY
```

## Hard Gate Re-Confirmation

Asterisk `92.118.85.117`:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
service_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=NOT_ENABLED
```

Gateway `45.61.48.199`:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
unit_present=true
unit_verify=ok
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
gateway_user=present
gateway_group=present
gateway_env_present=true
gateway_env_stat=root:gateway:640
openai_api_key_presence=masked_present
gateway_token_presence=masked_present
workdir_present=true
listener_443=absent
listener_8080=absent
listener_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
rollback_systemctl_available=true
```

## Helper Bundle Attempt

Local bundle creation first failed closed when the selected `C:\tmp` output path could not be used:

```text
action=create
ok=false
error_type=PermissionError
secret_values_printed=false
transcript_text_logged=false
```

Retrying with a workspace-local temporary path succeeded:

```text
action=create
ok=true
files_copied=smoke helper, temp-env guard, ai_secretary config, required STT adapter modules
secret_values_printed=false
transcript_text_logged=false
```

Local validation succeeded:

```text
action=validate
ok=true
required_files_present=true
preflight_import_ok=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

The shell `scp` shim did not transfer the archive, so the explicit Windows OpenSSH `scp.exe` path was used. No token values or transcript text were printed.

The validator script was copied separately to the temporary Asterisk bundle path because the helper bundle manifest contains the smoke runtime files and not the local bundle-builder script.

Remote staged validation failed closed:

```text
action=validate
ok=false
errors=["preflight import failed"]
missing_files=[]
preflight_error_type=ModuleNotFoundError
preflight_missing_module=httpx
required_files_present=true
secret_pattern_hits=[]
secret_values_printed=false
transcript_text_logged=false
```

## Blocker

The complete helper bundle still lacks the runtime dependency needed for remote preflight import:

```text
missing_module=httpx
gateway_request_reached=false
safe_temp_env_created=false
gateway_token_read=false
service_started=false
controlled_smoke_run=false
```

The smoke was blocked before safe temp-env creation, before any Gateway token was read, before service start, and before any Gateway request.

## Cleanup And Final State

Asterisk cleanup:

```text
helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
ari_active=active
ari_enabled=enabled
process_openai_api_key=OPENAI_API_KEY_ABSENT
```

Gateway final read-only state:

```text
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=disabled
listener_443=absent
listener_8080=absent
listener_8081=absent
ufw_status=active
ufw_8080_allow=92.118.85.117 only
```

Local temporary helper bundle and archive were removed after the blocked attempt.

## Safety Confirmations

```text
systemctl_enable=false
reboot=false
provider_power_cycle=false
business_dialog_enablement=false
port_443_change=false
port_8081_change=false
tls_proxy_change=false
firewall_broadened=false
asterisk_env_changed=false
token_values_printed=false
transcript_text_printed=false
notion_write=false
runtime_evidence_update=false
github_push_pr=false
scheduler_webhook_automation_added=false
```

## Next Recommendation

```text
NODE-032P / helper-bundle-runtime-dependency-preflight-and-retry-plan
```

NODE-032P should make the temporary helper bundle preflight complete for runtime dependencies such as `httpx`, or choose another safe staging shape that validates before any live retry. Token handling must remain owned by the safe temp-env guard and must not print values.
