# NODE-032I / controlled-persistent-gateway-service-install-start-smoke

Status: Phase A readiness and command planning complete, fresh gates rerun, Phase B conditionally GO only after exact approval

## Summary

NODE-032I prepares the first staged persistence live node after NODE-032H.

Phase A is readiness inspection and command planning only. No live apply, helper copy/deploy, service install, systemd unit write, user/group creation, chmod/chown, service start/stop/restart/reload/enable, firewall change, env edit, Asterisk restart, live smoke, reboot, provider power-cycle, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, GitHub write, scheduler, webhook, or automation loop occurred.

Phase B is not approved by this node. Future live apply/smoke requires the exact phrase:

```text
APPROVE NODE-032I SERVICE INSTALL/START/SMOKE
```

No other phrase is approval.

## Baseline

- NODE-032G merged via PR #9 / merge commit `a280bb2`.
- NODE-032G proved `Asterisk 92.118.85.117 -> Gateway 45.61.48.199:8080 -> OpenAI Realtime`.
- NODE-032G result: `gateway_reachable_from_asterisk=true`, `gateway_auth=ok`, `openai_realtime_from_gateway=ok`, `chunks_sent=28`, `transcript_present=true`, `transcript_text_logged=false`, `business_dialog_unchanged=true`, `transcript_used_for_dialog=false`, and `adapter_default_enabled_after_smoke=false`.
- NODE-032H merged via PR #10 / merge commit `c70f788913088c045f93bf9dd1c4856f4d32e8bf`.
- NODE-032H selected staged persistence: no immediate installed-and-enabled service, service enablement deferred, reboot/power-cycle proof deferred, and business dialog integration out of scope.

## Commands Run

Local branch and inspection:

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032i-controlled-persistent-gateway-service-install-start-smoke
git rev-parse --short HEAD
Get-Content deploy\templates\gateway-systemd.service.example
Get-Content docs\nodes\NODE-032H-production-gateway-persistence-and-reboot-strategy.md
Get-Content docs\nodes\NODE-032G-controlled-gateway-live-smoke-with-asterisk-side-helper.md
Get-Content docs\master\NODE_REGISTRY.md
Get-Content docs\master\MASTER_STATUS.md -Tail 220
rg -n "ai-secretary-gateway.service|openai-realtime-gateway.env|/opt/ai-secretary-gateway|0.0.0.0|8080|node032g-asterisk-helper|gateway_adapter_smoke|systemctl enable|NODE-032I|NODE-032H|NODE-032G" docs deploy scripts src tests
```

Read-only SSH attempts:

```text
ssh root@92.118.85.117 "<read-only Asterisk hostname/uptime/service/env checks>"
ssh root@45.61.48.199 "<read-only Gateway hostname/uptime/env/user/unit/listener/ufw checks>"
ssh -o ConnectTimeout=15 root@92.118.85.117 "<read-only Asterisk checks>"
ssh -o ConnectTimeout=15 root@45.61.48.199 "<read-only Gateway checks>"
ssh -o ConnectTimeout=20 root@92.118.85.117 "hostname; uptime"
ssh -o ConnectTimeout=20 root@45.61.48.199 "hostname; uptime"
```

One early Asterisk process-env command used unsafe local PowerShell interpolation. It failed locally before useful remote execution and did not change server state.

Rerun read-only SSH checks after the operator confirmed both SSH ports were reachable:

```text
ssh -o ConnectTimeout=20 root@92.118.85.117 'hostname; uptime; systemctl is-active ai-secretary-ari.service; systemctl is-enabled ai-secretary-ari.service; systemctl show ai-secretary-ari.service -p MainPID --value; systemctl show ai-secretary-ari.service -p Environment --no-pager'
ssh -o ConnectTimeout=20 root@92.118.85.117 '<masked process env OPENAI_API_KEY check and service unit inspection>'
ssh -o ConnectTimeout=20 root@92.118.85.117 '<masked service env OPENAI_API_KEY check and dialog gateway transcript flag check>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<historical env existence, owner/mode, and masked secret checks>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<gateway user/group and deploy path checks>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<gateway unit and backup target checks>'
ssh -o ConnectTimeout=20 root@45.61.48.199 '<listener and UFW checks>'
```

The previous timeout was likely caused by the servers being powered on while Phase A was already executing. The rerun confirmed SSH reachability.

## Local Repo Findings

```text
start_commit=c70f788
branch=feat/node-032i-controlled-persistent-gateway-service-install-start-smoke
template=deploy/templates/gateway-systemd.service.example
template_user_group=gateway:gateway
template_env_file=/etc/ai-secretary/gateway.env
template_exec=/usr/local/bin/ai-secretary-gateway --bind ${GATEWAY_BIND}
node032h_env_file=/etc/ai-secretary/openai-realtime-gateway.env
node032h_working_directory=/opt/ai-secretary-gateway
node032h_listen=0.0.0.0:8080
node032h_restart=on-failure
node032h_enable_policy=disabled_until_reboot_node
node032g_helper_strategy=/tmp/node032g-asterisk-helper
```

Exact Phase B service unit delta from the template:

- Keep `User=gateway`, `Group=gateway`, `Restart=on-failure`, and `RestartSec=5s`.
- Replace `EnvironmentFile=/etc/ai-secretary/gateway.env` with `EnvironmentFile=/etc/ai-secretary/openai-realtime-gateway.env`.
- Add `WorkingDirectory=/opt/ai-secretary-gateway`.
- Replace `ExecStart=/usr/local/bin/ai-secretary-gateway --bind ${GATEWAY_BIND}` with `ExecStart=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080`.
- Do not run `systemctl enable`.
- Do not include reboot or provider power-cycle in NODE-032I.

## Asterisk Read-Only Findings

Initial read-only SSH timed out. Rerun read-only SSH passed:

```text
target=92.118.85.117
ssh_reachable=true
hostname=tula
uptime=reachable_up_10_min_at_check
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
main_pid_observed=3810
service_environment=PYTHONUNBUFFERED only
process_env_openai_api_key=OPENAI_API_KEY_ABSENT
service_env_file=/etc/ai-secretary/ari-app.env present
service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
business_dialog_unchanged=true_readonly_no_change
```

No Asterisk env values were printed.

## Gateway Read-Only Findings

Initial read-only SSH timed out. Rerun read-only SSH passed:

```text
target=45.61.48.199
ssh_reachable=true
hostname=ai-secretary-gateway-node023
uptime=reachable_up_10_min_at_check
historical_env=/etc/ai-secretary/openai-realtime-gateway.env present
historical_env_owner_mode=root:root 600
openai_api_key_presence=OPENAI_API_KEY_PRESENT_MASKED
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
gateway_user=gateway_user_absent
gateway_group=gateway_group_absent
deploy_path=/opt/ai-secretary-gateway present root:root 755
gateway_venv_python=present
gateway_src_stt=present
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=not-found
unit=/etc/systemd/system/ai-secretary-gateway.service absent
backup_target=/etc/systemd/system/ai-secretary-gateway.service.node032i.bak absent
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_default_outgoing=allow
ufw_8080_allow=92.118.85.117 only
```

No gateway env values or token values were printed.

## Live Gate Status

Phase B is conditionally GO only after exact approval and one more immediate hard-gate re-check.

```text
exact_approval_phrase_absent=true
asterisk_ssh_fresh_gate=pass
gateway_ssh_fresh_gate=pass
asterisk_openai_api_key_absence_fresh_gate=pass
gateway_env_presence_fresh_gate=pass
gateway_secret_presence_fresh_gate=pass
gateway_user_group_fresh_gate=absent_expected_phase_b_action
env_readability_plan_requires_state_change=true
firewall_source_restriction_fresh_gate=pass
target_listener_fresh_gate=pass
rollback_target_fresh_gate=pass_absent_no_existing_unit
business_dialog_enablement_required=false
transcript_or_token_printing_required=false
```

## Service Account And Env Readability Plan

NODE-032H requires a durable non-root service runtime:

```text
runtime_user_group=gateway:gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
preferred_env_mode=root:gateway 640
not_accepted=durable_root_service
```

NODE-032I rerun confirmed `gateway:gateway` is absent and the historical env file is `root:root 600`. Phase B must choose the approved service-account/env-readability path:

1. If `gateway:gateway` is present and env is already readable by that group, proceed after masked checks.
2. If `gateway:gateway` is absent, create a locked service user/group only after exact approval.
3. If env is `root:root 600`, change it to `root:gateway 640` only after exact approval and only after recording the pre-change stat.
4. If either action is not approved, stop NO-GO.

No env value may be printed. Only masked presence checks are allowed.

## Phase B Command Set

Phase B remains blocked until the exact approval phrase is provided:

```text
APPROVE NODE-032I SERVICE INSTALL/START/SMOKE
```

Gate re-check commands:

```bash
ssh root@92.118.85.117 'hostname; uptime; systemctl is-active ai-secretary-ari.service; systemctl is-enabled ai-secretary-ari.service; pid=$(systemctl show ai-secretary-ari.service -p MainPID --value); if [ -n "$pid" ] && [ "$pid" != 0 ] && tr "\0" "\n" < /proc/$pid/environ | grep -q "^OPENAI_API_KEY="; then echo OPENAI_API_KEY_PRESENT; else echo OPENAI_API_KEY_ABSENT; fi; systemctl cat ai-secretary-ari.service --no-pager | grep -E "STT_GATEWAY|OPENAI_API_KEY|ExecStart|EnvironmentFile" || true'
ssh root@45.61.48.199 'hostname; uptime; test -f /etc/ai-secretary/openai-realtime-gateway.env && stat -c "%U %G %a %n" /etc/ai-secretary/openai-realtime-gateway.env || echo historical_env_absent; grep -q "^OPENAI_API_KEY=" /etc/ai-secretary/openai-realtime-gateway.env && echo OPENAI_API_KEY_PRESENT_MASKED || echo OPENAI_API_KEY_ABSENT; grep -q "^GATEWAY_TOKEN=" /etc/ai-secretary/openai-realtime-gateway.env && echo GATEWAY_TOKEN_PRESENT_MASKED || echo GATEWAY_TOKEN_ABSENT'
ssh root@45.61.48.199 'getent passwd gateway >/dev/null && echo gateway_user_present || echo gateway_user_absent; getent group gateway >/dev/null && echo gateway_group_present || echo gateway_group_absent; test -d /opt/ai-secretary-gateway && stat -c "%U %G %a %n" /opt/ai-secretary-gateway || echo deploy_path_absent; test -x /opt/ai-secretary-gateway/.venv/bin/python && echo gateway_venv_python_present || echo gateway_venv_python_absent'
ssh root@45.61.48.199 'systemctl is-active ai-secretary-gateway.service 2>/dev/null || echo inactive_or_absent; systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || echo not_enabled_or_absent; test -f /etc/systemd/system/ai-secretary-gateway.service && echo unit_present || echo unit_absent; test -f /etc/systemd/system/ai-secretary-gateway.service.node032i.bak && echo backup_present || echo backup_absent; ss -ltnp | grep -E ":(443|8080|8081)\b" || echo no_target_listeners_443_8080_8081; ufw status verbose'
```

Hard NO-GO if Asterisk contains `OPENAI_API_KEY`, gateway env is missing, masked secret presence fails, `8080/tcp` is not source-restricted to `92.118.85.117`, any unexpected listener exists on `443`, `8080`, or `8081`, rollback target state is unclear, business dialog must be enabled, or token values/transcript text would be printed.

Service account and env readability commands, only after exact approval and passing gates:

```bash
getent group gateway >/dev/null || groupadd --system gateway
getent passwd gateway >/dev/null || useradd --system --gid gateway --home-dir /opt/ai-secretary-gateway --shell /usr/sbin/nologin gateway
stat -c '%U %G %a %n' /etc/ai-secretary/openai-realtime-gateway.env
chown root:gateway /etc/ai-secretary/openai-realtime-gateway.env
chmod 640 /etc/ai-secretary/openai-realtime-gateway.env
stat -c '%U %G %a %n' /etc/ai-secretary/openai-realtime-gateway.env
```

Unit install and start commands, only after exact approval and passing gates:

```bash
test -f /etc/systemd/system/ai-secretary-gateway.service && cp -a /etc/systemd/system/ai-secretary-gateway.service /etc/systemd/system/ai-secretary-gateway.service.node032i.bak || true
cat >/etc/systemd/system/ai-secretary-gateway.service <<'UNIT'
[Unit]
Description=AI Secretary Gateway
After=network.target

[Service]
Type=simple
User=gateway
Group=gateway
WorkingDirectory=/opt/ai-secretary-gateway
EnvironmentFile=/etc/ai-secretary/openai-realtime-gateway.env
ExecStart=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl start ai-secretary-gateway.service
```

NODE-032I must not run `systemctl enable ai-secretary-gateway.service`, `reboot`, or provider power-cycle.

Health, listener, firewall, and redaction checks:

```bash
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || echo not_enabled_or_absent
ss -ltnp | grep ':8080'
ss -ltnp | grep -E ':(443|8081)\b' || echo no_443_or_8081
ufw status verbose
journalctl -u ai-secretary-gateway.service -n 80 --no-pager
```

Journald output must be reviewed for lifecycle/status/error facts only. If token values, bearer headers, env dumps, transcript text, or caller audio content appear, stop and rotate exposed tokens.

Asterisk-side smoke uses the existing NODE-032G helper-bundle strategy after exact approval:

```bash
cd /tmp/node032i-asterisk-helper
set -a
. /tmp/node032i-gateway-client.env
set +a
unset OPENAI_API_KEY
/home/tulauser/AI-secrenar-with-Asterisk-node014/.venv/bin/python scripts/asterisk_gateway_smoke_helper.py --audio /tmp/node032i-smoke.wav
```

Safe smoke evidence only: gateway reachability, auth, OpenAI Realtime status, HTTP status, chunks, transcript presence flag, `transcript_text_logged=false`, `transcript_used_for_dialog=false`, and `business_dialog_unchanged=true`.

## Rollback Commands

Run after any failure following state change, or if final state is rollback:

```bash
systemctl stop ai-secretary-gateway.service || true
systemctl disable ai-secretary-gateway.service || true
test -f /etc/systemd/system/ai-secretary-gateway.service.node032i.bak && cp -a /etc/systemd/system/ai-secretary-gateway.service.node032i.bak /etc/systemd/system/ai-secretary-gateway.service
test -f /etc/systemd/system/ai-secretary-gateway.service.node032i.bak || rm -f /etc/systemd/system/ai-secretary-gateway.service
systemctl daemon-reload
rm -rf /tmp/node032i-asterisk-helper
rm -f /tmp/node032i-gateway-client.env /tmp/node032i-smoke.wav
ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081
ufw status verbose
```

If NODE-032I changed env ownership/mode, restore the pre-change owner/group/mode recorded before mutation unless the operator explicitly approves preserving the new secure readability mode. Preserve historical env values. If any token/transcript exposure occurs, stop and rotate exposed tokens.

## GO / NO-GO Recommendation

Recommendation: conditional GO for Phase B only after the exact approval phrase is provided and the hard gates are re-confirmed immediately before state change.

Reasons:

- Fresh rerun gates passed for Asterisk SSH, Asterisk `OPENAI_API_KEY` absence, Gateway SSH, Gateway env presence, masked gateway secret presence, listener absence, and source-restricted UFW.
- Phase B still requires exact approval phrase.
- Phase B must create the absent locked `gateway:gateway` service account and change env readability from `root:root 600` to an approved restrictive service-readable mode such as `root:gateway 640`.
- Phase B must not run `systemctl enable`, reboot, provider power-cycle, broaden firewall, expose `443`, open `8081`, enable business dialog, or print token/transcript values.

NO-GO if any hard gate changes before Phase B, if exact approval is absent, or if service account/env readability actions are not approved.

## Result

```text
node_status=phase_a_readiness_and_command_planning_complete_with_rerun
phase_b_go=conditional_after_exact_approval
live_apply=false
helper_copied_or_deployed=false
service_installed_started_stopped_restarted_reloaded_enabled=false
systemd_unit_modified=false
user_group_created=false
permissions_changed=false
firewall_changed=false
env_files_edited=false
server_state_changed=false
live_smoke=false
reboot=false
provider_power_cycle=false
business_dialog_enabled=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
course_submission_staged=false
data_storage_staged=false
node014_server_tar_staged=false
```

## Phase B Controlled Service Install/Start/Smoke

Approval phrase confirmed:

```text
APPROVE NODE-032I SERVICE INSTALL/START/SMOKE
```

Phase B stayed within NODE-032I scope. Hard gates were re-run before state-changing commands. No `systemctl enable`, reboot, provider power-cycle, business dialog enablement, `443`, `8081`, TLS/proxy change, firewall broadening, Notion write, Runtime/Evidence update, GitHub push/PR, scheduler, webhook, or automation loop occurred.

### Phase B Hard Gate Re-Confirmation

Asterisk hard gate:

```text
ssh_reachable=true
hostname=tula
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
process_env_openai_api_key=OPENAI_API_KEY_ABSENT
service_env_openai_api_key=SERVICE_ENV_OPENAI_API_KEY_ABSENT
business_dialog_gateway_transcript=not_enabled
helper_autostart=false
helper_timer=false
helper_cron=false
```

Gateway hard gate:

```text
ssh_reachable=true
hostname=ai-secretary-gateway-node023
historical_env=/etc/ai-secretary/openai-realtime-gateway.env present
pre_change_env_stat=root:root:600:/etc/ai-secretary/openai-realtime-gateway.env
openai_api_key_presence=OPENAI_API_KEY_PRESENT_MASKED
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
deploy_path=/opt/ai-secretary-gateway present root:root 755
gateway_runtime_import_requires_pythonpath=true
gateway_runtime_help_with_pythonpath=ok
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_8080_allow=92.118.85.117 only
unit_absent_before_apply=true
backup_required=false
```

No secret values were printed.

### Service Account And Env Readability

The `gateway:gateway` account was absent before Phase B and was created as a locked system runtime account:

```text
gateway_user=present
gateway_group=present
interactive_login=false
```

The historical gateway env content was preserved. Only owner/group/mode changed for non-root service readability:

```text
pre_change_env_stat=root:root:600:/etc/ai-secretary/openai-realtime-gateway.env
post_change_env_stat=root:gateway:640:/etc/ai-secretary/openai-realtime-gateway.env
env_values_printed=false
```

### Service Unit Install And Start

No previous `/etc/systemd/system/ai-secretary-gateway.service` existed, so no backup was required.

Installed unit shape:

```text
unit=/etc/systemd/system/ai-secretary-gateway.service
runtime=gateway:gateway
working_directory=/opt/ai-secretary-gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
environment=PYTHONPATH=/opt/ai-secretary-gateway/src
exec=/opt/ai-secretary-gateway/.venv/bin/python -m ai_secretary.stt.realtime_gateway --host 0.0.0.0 --port 8080
restart=on-failure
daemon_reload=true
started=true
active_after_start=true
enabled_after_start=false
```

The `PYTHONPATH` entry is required because the deployed gateway uses the current src-layout tree and the venv does not import `ai_secretary` without `/opt/ai-secretary-gateway/src`.

Start verification:

```text
service_active=true
service_enabled=false
listener_8080=true
listener_443=false
listener_8081=false
ufw_8080_allow=92.118.85.117 only
health_endpoint_http_status=404
docs_endpoint_http_status=200
sensitive_log_pattern_absent=true
transcript_text_log_pattern_absent=true
```

No dedicated `/health` endpoint was available, so service/process/listener checks and the FastAPI docs endpoint were used for readiness.

### Controlled Asterisk-Side Smoke

Temporary helper bundle:

```text
path=/tmp/node032i-asterisk-helper
files=9
autostart=false
persistent_state=false
```

Temporary runtime env:

```text
path=/tmp/node032i-gateway-client.env
owner_mode=root:root 600
gateway_token=present_masked
openai_api_key=absent
```

The first attempted smoke invocation failed before the helper ran because the temporary env file had Windows line endings:

```text
pre_smoke_shell_failure=true
gateway_request_sent=false
helper_executed=false
reason=temporary_env_crlf
```

After normalizing the temporary env file, exactly one controlled gateway smoke request was run from Asterisk.

Smoke result:

```text
adapter_smoke_exercised_node025_path=true
gateway_reachable_from_asterisk=true
gateway_auth=ok
openai_realtime_from_gateway=ok
gateway_http_status=200
chunks_sent=28
transcript_present=true
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_unchanged=true
fallback_reason=gateway_stt_dialog_use_disabled
adapter_default_enabled_after_smoke=false
helper_manual_only=true
autostart_configured=false
persistent_server_state_created=false
```

The smoke printed safe redacted metadata only. It did not print token values or transcript text.

### Final State And Cleanup

NODE-032I used the maximum-safety final service state:

```text
service_unit_installed=true
service_active=false
service_enabled=false
unit_preserved_as_staged_artifact=true
env_preserved=true
env_owner_mode=root:gateway 640
listener_443=false
listener_8080=false
listener_8081=false
firewall_changed=false
ufw_8080_allow=92.118.85.117 only
```

Temporary Asterisk state was removed:

```text
helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
asterisk_openai_api_key=OPENAI_API_KEY_ABSENT
helper_autostart=false
helper_timer=false
helper_cron=false
```

Rollback path from the final installed-disabled state:

```bash
systemctl stop ai-secretary-gateway.service || true
systemctl disable ai-secretary-gateway.service || true
rm -f /etc/systemd/system/ai-secretary-gateway.service
systemctl daemon-reload
# If policy requires full pre-NODE-032I env mode restoration:
chown root:root /etc/ai-secretary/openai-realtime-gateway.env
chmod 600 /etc/ai-secretary/openai-realtime-gateway.env
ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081
ufw status verbose
```

## Phase B Result

```text
node_status=phase_b_install_start_smoke_complete
approval_phrase_confirmed=true
service_account_created=true
env_readability_changed=true
unit_installed=true
daemon_reload=true
service_started=true
service_stopped_after_smoke=true
service_enabled=false
reboot=false
provider_power_cycle=false
firewall_changed=false
live_smoke=true
business_dialog_enabled=false
transcript_text_logged=false
transcript_used_for_dialog=false
real_secrets_logged=false
temp_helper_bundle_removed=true
temp_env_removed=true
temp_audio_removed=true
```
