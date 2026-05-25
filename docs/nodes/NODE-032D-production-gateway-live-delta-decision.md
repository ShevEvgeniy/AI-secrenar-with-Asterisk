# NODE-032D / production-gateway-live-delta-decision

Status: Docs-only live delta decision complete

Summary
-------

NODE-032D resolves the production gateway live delta decisions that were left open by NODE-032C. This node is documentation only: no live apply, no SSH, no service start/stop/restart/reload, no firewall change, no env edit, no deploy/copy, no live call, no live smoke, no business dialog enablement, and no transcript text logging were performed.

The future live action must be a separate NODE-032E with an exact explicit approval phrase.

Baseline
--------

- NODE-031 documented the production gateway runtime boundary and safe templates.
- NODE-032 and NODE-032B documented live smoke plans and approval boundaries.
- NODE-032C performed read-only live inspection and produced NO-GO for immediate live apply/smoke.
- NODE-032C found:
  - Asterisk server reachable.
  - `ai-secretary-ari.service` active/enabled.
  - `OPENAI_API_KEY` absent from the Asterisk service process env.
  - Gateway server reachable.
  - Gateway service not installed/enabled.
  - No gateway process running.
  - `/etc/ai-secretary/gateway.env` absent.
  - Historical `/etc/ai-secretary/openai-realtime-gateway.env` present with masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence.
  - No listener on `443`, `8080`, or `8081`.
  - Gateway UFW active with default incoming deny.
  - Old `8080/tcp` allow from Asterisk remains.
- NODE-032C NO-GO blockers were env path, service unit, TLS/proxy, firewall transition, and rollback plan.

Commands run
------------

Local setup:

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032d-production-gateway-live-delta-decision
```

Local docs/template inspection:

```powershell
Get-Content docs\nodes\NODE-031-productionize-gateway-runtime-boundary.md
Get-Content docs\nodes\NODE-032-controlled-production-gateway-live-smoke.md
Get-Content docs\nodes\NODE-032B-controlled-production-gateway-live-apply-and-smoke.md
Get-Content docs\nodes\NODE-032C-live-readonly-production-gateway-readiness-inspection.md
Get-ChildItem deploy\templates
Get-Content deploy\templates\gateway.env.example
Get-Content deploy\templates\gateway-systemd.service.example
Get-Content deploy\templates\gateway-nginx-proxy.example
```

No server SSH was run in NODE-032D because NODE-032C already provided the needed read-only live facts.

Decision 1: env path
--------------------

Accepted decision for the first NODE-032E live smoke:

```text
use_env_path=/etc/ai-secretary/openai-realtime-gateway.env
do_not_create_gateway_env_for_first_smoke=true
do_not_migrate_or_symlink_env_for_first_smoke=true
```

Rationale:

- NODE-032C already verified the historical env file exists on the gateway host with restrictive `600 root:root` permissions.
- Masked checks confirmed gateway-side `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence without printing values.
- Creating `/etc/ai-secretary/gateway.env`, migrating secrets, or adding a compatibility symlink would add secret-handling and rollback risk before the first controlled smoke.
- NODE-031 templates remain the future production target, but the first live smoke should minimize change and use the already-known env path.

Deferred:

- A later production-hardening node may migrate to `/etc/ai-secretary/gateway.env` or introduce a compatibility symlink after the first smoke proves the service path.
- Any migration must include masked pre/post checks, backup/restore steps, and token exposure handling.

Decision 2: systemd unit
------------------------

Accepted decision for NODE-032E:

```text
service_name=ai-secretary-gateway.service
unit_path=/etc/systemd/system/ai-secretary-gateway.service
runtime_user=gateway
runtime_group=gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
first_smoke_listen=0.0.0.0:8080
restart_policy=on-failure
restart_sec=5s
```

NODE-032E may install/adapt:

- A systemd unit named `ai-secretary-gateway.service`.
- An `EnvironmentFile` pointing to `/etc/ai-secretary/openai-realtime-gateway.env`.
- An `ExecStart` that runs the deployed gateway from the existing gateway application path.
- Safe default env flags:
  - gateway STT disabled outside the one-off smoke helper;
  - business dialog transcript use disabled;
  - transcript text logging disabled.

NODE-032E must verify before install/start:

- Whether `gateway:gateway` exists. If it does not exist, NODE-032E must either create a locked service account after explicit approval or stop as blocked.
- The unit file does not embed token values.
- The process env is checked only with masked/presence checks.
- The service logs do not print tokens, bearer headers, env values, or transcript text.

Logging/redaction expectations:

- Journald may include service lifecycle, health, HTTP status, timing, chunk counts, transcript presence flags, and error class.
- Journald must not include raw transcript text, bearer token values, `OPENAI_API_KEY` values, or full env dumps.
- Smoke evidence may record `transcript_present=true/false` and `transcript_text_logged=false`, but not transcript content.

Decision 3: TLS / reverse proxy
-------------------------------

Accepted decision for the first NODE-032E live smoke:

```text
public_tls_proxy_for_first_smoke=false
use_existing_asterisk_only_8080_path=true
expose_443=false
install_or_reload_proxy=false
```

Rationale:

- NODE-032C found no listener on `443` and no installed gateway service.
- Adding TLS/proxy before the first smoke would expand the live delta across service, proxy, certificates, and firewall at the same time.
- The gateway firewall already contains an Asterisk-only `8080/tcp` allow from `92.118.85.117`, and no service is currently listening there.
- The first NODE-032E smoke should prove only the gateway service path, auth path, OpenAI Realtime path, redaction, and business-dialog isolation.

Safety boundary:

- No public `443` exposure is authorized for NODE-032E.
- No proxy reload is authorized for NODE-032E.
- The first smoke may use the direct Asterisk-to-gateway `8080` path only if NODE-032E re-confirms the firewall allows only the Asterisk source and no broad listener exposure is present.
- Persistent production TLS/proxy setup is deferred to a later node after first-smoke evidence.

Decision 4: firewall transition
-------------------------------

Accepted decision for NODE-032E:

```text
keep_existing_8080_allow_for_first_smoke=true
do_not_remove_old_8080_allow_before_first_smoke=true
do_not_open_8081_for_first_smoke=true
do_not_open_443_for_first_smoke=true
allowed_smoke_source=92.118.85.117
```

Planned transition:

- Before live apply, NODE-032E must record the existing UFW state.
- If the old `8080/tcp` allow from `92.118.85.117` is still present and no broader `8080` allow exists, NODE-032E may use that existing allow for one controlled smoke.
- NODE-032E must not add public `8080`, public `8081`, or public `443`.
- NODE-032E must not remove the old `8080/tcp` allow until the smoke path is proven or a separate firewall cleanup/productionization node is approved.
- After smoke, NODE-032E must either stop the gateway and leave firewall unchanged or explicitly record a persistent service decision. The conservative default is stop/rollback after smoke.

Future production direction:

- A later node may move to `127.0.0.1:8081` behind a TLS reverse proxy on `443`.
- That later node should close the old `8080/tcp` allow only after replacement path and rollback are accepted.

Rollback command set
--------------------

These commands are a command-level rollback plan for future NODE-032E only. They were not run in NODE-032D.

Record before changes:

```bash
systemctl is-active ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service || true
systemctl cat ai-secretary-gateway.service --no-pager || true
ss -ltnp | grep -E '(:8080|:8081|:443)' || true
ufw status verbose
stat -c '%U %G %a %n' /etc/ai-secretary/openai-realtime-gateway.env
```

Rollback service state:

```bash
sudo systemctl stop ai-secretary-gateway.service || true
sudo systemctl disable ai-secretary-gateway.service || true
test -f /etc/systemd/system/ai-secretary-gateway.service.node032e.bak && sudo cp /etc/systemd/system/ai-secretary-gateway.service.node032e.bak /etc/systemd/system/ai-secretary-gateway.service
test -f /etc/systemd/system/ai-secretary-gateway.service.node032e.bak || sudo rm -f /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
```

Rollback proxy/firewall state:

```bash
# NODE-032E first smoke must not install/reload proxy or open 443.
# If a later node changes proxy/firewall, restore from that node's captured backup.
sudo ufw status verbose
# Do not delete the pre-existing 8080 allow unless the node explicitly added it or the operator approved firewall cleanup.
```

Rollback env/local shell state:

```bash
# Preserve /etc/ai-secretary/openai-realtime-gateway.env unless a later node explicitly edits it.
unset OPENAI_API_KEY GATEWAY_TOKEN STT_GATEWAY_TOKEN REALTIME_GATEWAY_TOKEN
```

Post-rollback verification:

```bash
systemctl is-active ai-secretary-gateway.service || true
ss -ltnp | grep -E '(:8080|:8081|:443)' || true
ufw status verbose
# Verify on Asterisk with masked checks only:
# OPENAI_API_KEY absent from ai-secretary-ari.service process env.
```

Incident cleanup:

- If any token, bearer header, env value, private key, or transcript text is printed, stop the node, revoke/rotate exposed tokens, and preserve only redacted incident evidence.
- If `OPENAI_API_KEY` appears on Asterisk, remove it from the Asterisk side, rotate the key, and do not continue smoke.
- Transcript redaction remains mandatory during rollback and incident handling.

NODE-032E minimal live scope
---------------------------

Exact approval phrase for NODE-032E:

```text
APPROVE NODE-032E LIVE APPLY/SMOKE
```

No other phrase is approval.

NODE-032E may apply only:

- Confirm current Asterisk and gateway state with read-only masked checks.
- Install/adapt `ai-secretary-gateway.service` using the historical env path.
- Start `ai-secretary-gateway.service` only after exact approval.
- Use the existing Asterisk-only `8080/tcp` firewall allow if it is still source-restricted to `92.118.85.117`.
- Run a gateway health check without printing tokens.
- Run one controlled non-business-dialog smoke from the Asterisk side or approved operator path.
- Capture redacted evidence.
- Stop/rollback the gateway after smoke unless NODE-032E explicitly records a persistent service decision.

NODE-032E must not apply:

- No business dialog transcript enablement.
- No transcript text logging.
- No live caller-facing call unless a later node explicitly scopes it.
- No `OPENAI_API_KEY` on Asterisk.
- No public `443` exposure.
- No TLS/proxy install or reload for the first smoke.
- No `8081` public exposure.
- No env migration from the historical path during first smoke.
- No broad firewall allow.
- No scheduler, webhook, automation loop, or unattended runtime mode.

Smoke type:

- One controlled non-business-dialog gateway adapter smoke.
- Use non-sensitive audio only.
- Keep `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- Keep transcript logging disabled.
- Record transcript flags only, not transcript text.

Expected NODE-032E evidence
---------------------------

Record only redacted evidence:

- Asterisk host target and service state before/after.
- Asterisk `OPENAI_API_KEY` absence from process env by masked/presence check.
- Gateway host target and service state before/after.
- Gateway env path used.
- Gateway env key presence checks with values masked.
- Gateway listen ports before/after.
- Firewall state before/after.
- Health check result.
- Smoke result.
- `transcript_present=true/false`.
- `transcript_text_logged=false`.
- `transcript_used_for_dialog=false`.
- `business_dialog_changed=false`.
- Cleanup or persistent service state decision.
- Rollback commands run if cleanup occurs.

Remaining blockers
------------------

NODE-032D resolves the decision blockers from NODE-032C for a minimal first smoke. NODE-032E must still re-confirm these live facts immediately before apply:

- SSH access remains stable.
- Historical env file still exists with restrictive permissions.
- Gateway service is still absent or safely replaceable.
- Existing `8080/tcp` allow remains source-restricted to `92.118.85.117`.
- No unexpected listener exists on `443`, `8080`, or `8081`.
- Rollback commands are accepted by the operator before start.
- Exact approval phrase is provided.

Result
------

```text
node_status=docs_only_decision_complete
live_apply=false
ssh_used=false
service_started_stopped_restarted_reloaded=false
server_state_changed=false
live_smoke=false
source_runtime_behavior_changed=false
business_dialog_changed=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
data_storage_staged=false
node014_server_tar_staged=false
```
