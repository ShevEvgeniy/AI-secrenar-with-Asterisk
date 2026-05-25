# NODE-032E / controlled-production-gateway-live-apply-and-smoke

Status: Phase A live gate re-confirmation complete

Summary
-------

NODE-032E Phase A re-confirms the live gates required before the first controlled production gateway live apply/smoke. Phase A is read-only inspection and documentation only.

No live apply, service install, systemd unit write, service start/stop/restart/reload, firewall change, env edit, deploy/copy, gateway start/stop, Asterisk restart, live call, live smoke, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation loop occurred.

Phase B must not begin unless the operator later provides this exact phrase:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

No other phrase is approval.

Baseline
--------

- NODE-032D decided that the first NODE-032E smoke keeps the historical gateway env path `/etc/ai-secretary/openai-realtime-gateway.env`.
- No migration or symlink to `/etc/ai-secretary/gateway.env` is allowed during the first smoke.
- Future service name: `ai-secretary-gateway.service`.
- Future unit path: `/etc/systemd/system/ai-secretary-gateway.service`.
- Runtime: `gateway:gateway`.
- First-smoke listen: `0.0.0.0:8080`.
- Restart policy: `on-failure`.
- No public TLS/proxy, no `443`, and no proxy reload for the first smoke.
- Do not open `8081`.
- Keep the existing Asterisk-only `8080/tcp` allow from `92.118.85.117` if re-confirmed source-restricted.
- One controlled non-business-dialog smoke only in future Phase B.
- Transcript text must remain redacted.
- Business dialog must remain unchanged.
- Cleanup default is stop/rollback unless persistent service state is explicitly decided.

Commands run
------------

Local setup:

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032e-controlled-production-gateway-live-apply-and-smoke
```

Asterisk read-only inspection:

```powershell
@'<read-only masked Asterisk inspection script>'@ | C:\Windows\System32\OpenSSH\ssh.exe root@92.118.85.117 bash
```

The Asterisk inspection script ran only:

- `hostname -f`
- `uptime -p`
- `systemctl is-active ai-secretary-ari.service`
- `systemctl is-enabled ai-secretary-ari.service`
- `systemctl status ai-secretary-ari.service --no-pager`
- `systemctl show ai-secretary-ari.service -p Environment --no-pager` with masking
- `stat` on `/etc/ai-secretary/ari-app.env`
- masked grep for gateway/STT/OpenAI keys
- process-env presence check for `OPENAI_API_KEY`
- `ss -ltnp`
- sanitized `journalctl` tail

Gateway read-only inspection:

```powershell
@'<read-only masked gateway inspection script>'@ | C:\Windows\System32\OpenSSH\ssh.exe root@45.61.48.199 bash
```

The gateway inspection script ran only:

- `hostname -f`
- `uptime -p`
- `stat` on `/etc/ai-secretary/openai-realtime-gateway.env`
- existence check for `/etc/ai-secretary/gateway.env`
- masked presence checks for `OPENAI_API_KEY` and `GATEWAY_TOKEN`
- `systemctl is-active`, `is-enabled`, `status`, and `cat` for `ai-secretary-gateway.service`
- process listing with masking
- `ss -ltnp`
- `ufw status verbose`
- existence check for `/etc/systemd/system`
- backup target plan echo

No state-changing command was run. No secret values were printed.

Asterisk gate findings
----------------------

Target: `92.118.85.117`

Sanitized findings:

```text
ssh_readonly_reachability=ok
hostname=localhost
uptime=up 1 hour, 8 minutes
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
main_process=python -u -m ai_secretary.telephony.ari_app
ari_env_file=/etc/ai-secretary/ari-app.env
ari_env_owner=root
ari_env_group=tulauser
ari_env_mode=640
service_environment_masked=PYTHONUNBUFFERED
process_env_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_change=not_performed
```

Observed Asterisk listeners:

```text
127.0.0.1:38745
0.0.0.0:7077
0.0.0.0:8088
0.0.0.0:22
127.0.0.54:53
127.0.0.53%lo:53
[::]:7077
[::]:8088
[::]:22
```

Sanitized journal summary:

```text
SYSTEM_SOUNDS_ITEM entries succeeded.
SYSTEM_SOUNDS_DONE ok.
SYSTEM_SOUNDS_BG_OK.
READY_WAITING_FOR_CALLS.
No transcript text or token values printed by NODE-032E.
```

Gate result:

```text
asterisk_access=pass
asterisk_service_state=pass
asterisk_openai_api_key_absent=pass
asterisk_business_dialog_unchanged=pass
```

Gateway gate findings
---------------------

Target: `45.61.48.199`

Sanitized findings:

```text
ssh_readonly_reachability=ok
hostname=ai-secretary-gateway-node023
uptime=up 1 hour, 8 minutes
historical_env_path=/etc/ai-secretary/openai-realtime-gateway.env
historical_env_owner=root
historical_env_group=root
historical_env_mode=600
planned_gateway_env_path=/etc/ai-secretary/gateway.env absent
planned_gateway_env_required_for_first_smoke=false
openai_api_key_presence=OPENAI_API_KEY_PRESENT_MASKED
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
ai-secretary-gateway.service_active=inactive_or_absent
ai-secretary-gateway.service_enabled=not-found
gateway_process_found=false
systemd_unit_dir_present=true
unit_absent_backup_not_required_before_install=true
rollback_plan_status=commands_documented_not_executed
```

Gate result:

```text
gateway_access=pass
historical_env_exists=pass
historical_env_permissions=pass
masked_openai_key_presence=pass
masked_gateway_token_presence=pass
planned_gateway_env_not_required=pass
service_replaceability=pass
```

Firewall and listener findings
------------------------------

Gateway listeners observed:

```text
127.0.0.54:53
0.0.0.0:22
127.0.0.53%lo:53
[::]:22
```

Gateway target listener result:

```text
listener_443=false
listener_8080=false
listener_8081=false
unexpected_target_listener=false
```

UFW sanitized result:

```text
ufw_status=active
default_incoming=deny
default_outgoing=allow
22/tcp=ALLOW Anywhere
8080/tcp=ALLOW from 92.118.85.117
22/tcp_v6=ALLOW Anywhere (v6)
```

Gate result:

```text
no_unexpected_listener=pass
ufw_active=pass
ufw_8080_source_restricted_to_asterisk=pass
do_not_open_8081=preserved
do_not_open_443=preserved
```

Rollback readiness findings
---------------------------

Read-only findings:

```text
systemd_unit_dir_present=true
current_gateway_unit_absent=true
backup_required_before_overwrite=false_for_absent_unit
backup_target_if_unit_exists=/etc/systemd/system/ai-secretary-gateway.service.node032e.bak
historical_env_preserve_required=true
pre_existing_8080_firewall_allow_preserve_required=true
rollback_commands_documented=true
rollback_commands_executed=false
```

Rollback readiness is acceptable for planning, but Phase B must re-confirm and accept the rollback commands immediately before any live apply.

Phase B command set
-------------------

The following is a command set for future Phase B only. It was not run in Phase A.

Approval gate:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

Pre-apply read-only checks:

```bash
hostname -f
uptime -p
stat -c '%U %G %a %n' /etc/ai-secretary/openai-realtime-gateway.env
awk -F= '/^OPENAI_API_KEY=/{found=1} END{print found?"OPENAI_API_KEY_PRESENT_MASKED":"OPENAI_API_KEY_ABSENT"}' /etc/ai-secretary/openai-realtime-gateway.env
awk -F= '/^GATEWAY_TOKEN=/{found=1} END{print found?"GATEWAY_TOKEN_PRESENT_MASKED":"GATEWAY_TOKEN_ABSENT"}' /etc/ai-secretary/openai-realtime-gateway.env
systemctl is-active ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service || true
ss -ltnp | grep -E '(:443|:8080|:8081)' || true
ufw status verbose
```

Prepare backup and install unit after approval only:

```bash
test -f /etc/systemd/system/ai-secretary-gateway.service && sudo cp /etc/systemd/system/ai-secretary-gateway.service /etc/systemd/system/ai-secretary-gateway.service.node032e.bak || true
sudo install -m 0644 /tmp/ai-secretary-gateway.service.node032e /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
sudo systemctl cat ai-secretary-gateway.service --no-pager
```

The unit must use:

```text
service_name=ai-secretary-gateway.service
env_file=/etc/ai-secretary/openai-realtime-gateway.env
runtime_user_group=gateway:gateway
listen=0.0.0.0:8080
restart_policy=on-failure
```

Start service after approval only:

```bash
sudo systemctl start ai-secretary-gateway.service
systemctl --no-pager --full status ai-secretary-gateway.service
ss -ltnp | grep -E '(:8080|ai-secretary-gateway)' || true
```

Health and one controlled non-business-dialog smoke after approval only:

```bash
# Use masked token source only; do not echo token values.
curl --fail --silent --show-error http://45.61.48.199:8080/health

python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio <non-sensitive-russian-speech-wav> \
  --require-explicit-flags
```

Required Phase B invariants:

```text
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_changed=false
asterisk_openai_key_present=false
public_tls_proxy_changed=false
firewall_changed=false
```

Phase B must not:

- Open `443`.
- Open `8081`.
- Reload a proxy.
- Edit env files.
- Migrate or symlink `/etc/ai-secretary/gateway.env`.
- Enable business dialog transcript use.
- Log transcript text.
- Run a live caller-facing call.
- Add scheduler, webhook, or automation mode.

Rollback commands
-----------------

Rollback commands for future Phase B only. They were not run in Phase A.

```bash
sudo systemctl stop ai-secretary-gateway.service || true
sudo systemctl disable ai-secretary-gateway.service || true
test -f /etc/systemd/system/ai-secretary-gateway.service.node032e.bak && sudo cp /etc/systemd/system/ai-secretary-gateway.service.node032e.bak /etc/systemd/system/ai-secretary-gateway.service
test -f /etc/systemd/system/ai-secretary-gateway.service.node032e.bak || sudo rm -f /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
ss -ltnp | grep -E '(:443|:8080|:8081)' || true
ufw status verbose
unset OPENAI_API_KEY GATEWAY_TOKEN STT_GATEWAY_TOKEN REALTIME_GATEWAY_TOKEN
```

Rollback rules:

- Preserve `/etc/ai-secretary/openai-realtime-gateway.env` unless a later node explicitly edits it.
- Leave the pre-existing `8080/tcp` allow from `92.118.85.117` unless NODE-032E explicitly changes it or operator approves firewall cleanup.
- Verify the Asterisk service process env still has `OPENAI_API_KEY` absent.
- If any secret value is exposed, stop and rotate exposed tokens before continuing.

GO/NO-GO for Phase B
--------------------

Technical gate status:

```text
asterisk_gate=pass
gateway_env_gate=pass
gateway_service_gate=pass
listener_gate=pass
firewall_gate=pass
rollback_plan_gate=pass_with_reconfirm_required
secret_redaction_gate=pass
```

Approval gate status:

```text
exact_approval_phrase_present=false
```

Recommendation:

```text
NO-GO for Phase B now.
```

Reason:

- Technical gates are ready for a tightly scoped Phase B attempt.
- Phase B remains blocked because the operator has not provided the exact approval phrase in a later approval turn.
- Phase B must re-run the read-only checks immediately before apply and stop if any gate changes.

Blockers
--------

Current blocker:

- Exact Phase B approval phrase is absent.

Re-confirm immediately before Phase B:

- Asterisk access still works.
- Gateway access still works.
- Asterisk process env still has `OPENAI_API_KEY` absent.
- Historical env file still exists with safe permissions.
- Masked gateway secret presence still passes.
- `ai-secretary-gateway.service` is still absent or safely replaceable.
- No unexpected listener exists on `443`, `8080`, or `8081`.
- UFW still restricts `8080/tcp` to `92.118.85.117`.
- Rollback commands are accepted.
- No secret values are printed.

Phase A result
--------------

```text
node_status=phase_a_live_gate_reconfirmation_complete
live_apply=false
service_installed=false
service_started_stopped_restarted_reloaded=false
firewall_changed=false
env_files_edited=false
server_state_changed=false
live_smoke=false
source_runtime_behavior_changed=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
data_storage_staged=false
node014_server_tar_staged=false
```
