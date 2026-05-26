# NODE-032H / production-gateway-persistence-and-reboot-strategy

Status: Docs-only decision/strategy complete

## Summary

NODE-032H decides the production gateway persistence and reboot/power-cycle strategy after NODE-032G proved the controlled Asterisk-side gateway path.

This node is documentation only. No live apply, SSH, service install/start/stop/restart/reload/enable, firewall change, env edit, gateway start, Asterisk restart, live smoke, call, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation loop occurred.

## Baseline

- NODE-032G merged via PR #9 / merge commit `a280bb2`.
- NODE-032G proved:

```text
Asterisk 92.118.85.117 -> Gateway 45.61.48.199:8080 -> OpenAI Realtime
```

- NODE-032G smoke result:
  - `gateway_reachable_from_asterisk=true`;
  - `gateway_auth=ok`;
  - `openai_realtime_from_gateway=ok`;
  - `chunks_sent=28`;
  - `transcript_present=true`;
  - `transcript_text_logged=false`;
  - `business_dialog_unchanged=true`;
  - `transcript_used_for_dialog=false`;
  - `adapter_default_enabled_after_smoke=false`.
- NODE-032G cleanup removed temporary gateway service/unit, helper bundle, runtime env file, and temp audio.
- After cleanup, no gateway unit remained, no target listener existed on `443`, `8080`, or `8081`, firewall was unchanged, historical gateway env was preserved, and Asterisk still had no `OPENAI_API_KEY`.

## Commands Run

```powershell
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032h-production-gateway-persistence-and-reboot-strategy
Get-Content docs\nodes\NODE-032G-controlled-gateway-live-smoke-with-asterisk-side-helper.md
Get-Content docs\nodes\NODE-032D-production-gateway-live-delta-decision.md
Get-Content deploy\templates\gateway-systemd.service.example
Get-Content docs\master\NODE_REGISTRY.md
Get-Content docs\master\MASTER_PLAN.md
Get-Content docs\master\MASTER_STATUS.md -Tail 170
Get-Content docs\master\DECISIONS.md -Tail 120
Get-Content docs\master\RUNTIME_NOTES.md -Tail 140
```

No server SSH was run. Local inspection was sufficient.

## Decision 1: Persistence Mode

Accepted decision: staged persistence.

```text
persistence_mode=staged_persistence
manual_only_gateway_for_now=true
installed_but_disabled_service_first=true
installed_and_enabled_service_now=false
enable_reboot_smoke_deferred=true
business_dialog_integration_deferred=true
```

Rationale:

- NODE-032G proved the Asterisk-origin gateway path but used temporary root-run service state and removed it after smoke.
- Durable service enablement should not be bundled with first persistence installation because it adds reboot/power-cycle behavior, unattended startup, and recovery obligations.
- The next live node should install/start/smoke a proper persistent service shape, then stop or leave installed-but-disabled according to the approved scope.
- A separate later node should enable the service and verify reboot/power-cycle behavior only after install/start/smoke evidence is accepted.

Rejected for now:

- Manual-only gateway forever: too fragile for production and does not address reboot recovery.
- Installed and enabled service immediately: too broad for the next step because auto-start safety, non-root runtime, env failure behavior, and reboot proof must be validated explicitly.

## Decision 2: Reboot / Power-Cycle Behavior

Desired final production behavior, after a later explicit enablement node:

```text
gateway_reboot_behavior=auto_start_only_after_enablement_node
provider_power_on_behavior=auto_start_only_after_enablement_node
missing_or_invalid_env=fail_closed_no_open_listener
asterisk_reboot_behavior=no_openai_api_key_gateway_stt_disabled_by_default
```

Before auto-start is safe:

- `ai-secretary-gateway.service` must run as a non-root service account.
- The service must read only `/etc/ai-secretary/openai-realtime-gateway.env`.
- The env file must be `root:gateway 640` or another explicitly approved restrictive mode compatible with the service user.
- Unit startup must fail closed if required gateway secrets are absent.
- Startup failure must not expose token values or transcript text in logs.
- Firewall must remain source-restricted to Asterisk `92.118.85.117`.
- No listener may appear on `443` or `8081` unless a separate node approves those ports.
- Business dialog transcript use must remain disabled unless a later business-dialog node explicitly changes it.

Recovery checks after reboot/power-cycle:

```text
systemctl is-active ai-secretary-gateway.service
systemctl is-enabled ai-secretary-gateway.service
ss -ltnp | grep ':8080'
ss -ltnp | grep -E ':(443|8081)' || echo no_443_or_8081
ufw status verbose
masked env presence checks only
journal redaction spot-check without transcript text or tokens
verify Asterisk process env has OPENAI_API_KEY_ABSENT
```

## Decision 3: Systemd Policy

Accepted future service policy:

```text
service_name=ai-secretary-gateway.service
unit_path=/etc/systemd/system/ai-secretary-gateway.service
runtime_user=gateway
runtime_group=gateway
env_file=/etc/ai-secretary/openai-realtime-gateway.env
working_directory=/opt/ai-secretary-gateway
listen=0.0.0.0:8080
restart=on-failure
restart_sec=5s
enable_policy=disabled_until_reboot_node
```

NODE-032I may install/adapt and start the service after exact approval, but should leave it disabled unless the node explicitly scopes enablement. If the `gateway:gateway` account is absent, NODE-032I must either create a locked service account as an approved scoped action or stop NO-GO.

The historical env file currently being `root:root 600` is not compatible with a non-root service. NODE-032I must decide and apply one safe env-read approach before persistent non-root start:

- preferred: `root:gateway 640` with the locked `gateway` user in group `gateway`;
- fallback: a root-owned wrapper that reads env and drops privileges only if explicitly reviewed;
- not accepted: running the durable production service as root.

Logging policy:

- Allowed: lifecycle status, health result, request ID, HTTP status, timing, chunk counts, transcript presence flags, error class.
- Forbidden: token values, bearer headers, full env dumps, raw transcript text, caller audio content.

Failure behavior:

- Missing/invalid env must fail the service before opening the gateway listener.
- Auth failures must return safe errors and redact credentials.
- Repeated failure may restart under `on-failure`, but must not create unbounded logs containing sensitive material.

## Decision 4: Firewall / Listen Policy

Accepted policy for the next persistence stage:

```text
listen_0_0_0_0_8080=acceptable_only_with_source_restricted_firewall
required_source=92.118.85.117
expose_443=false
open_8081=false
keep_existing_8080_allow=true
firewall_broadening=false
```

`0.0.0.0:8080` remains acceptable only while UFW allows `8080/tcp` from `92.118.85.117` and does not allow public `8080`. NODE-032I must re-confirm source restriction immediately before start and after start.

Do not expose `443` or `8081` in NODE-032I. TLS/proxy and loopback/private listener redesign may be a later node, after persistent service behavior is proven.

Post-reboot firewall/listener checks:

```text
ufw status verbose
ss -ltnp | grep ':8080'
ss -ltnp | grep -E ':(443|8081)' || echo no_443_or_8081
```

## Decision 5: Secrets / Env Policy

Accepted policy:

- Gateway owns OpenAI Realtime secrets.
- Asterisk must not contain `OPENAI_API_KEY`.
- Asterisk may use only gateway URL/token runtime material for scoped helper smokes.
- Durable gateway service must not depend on shell exports after reboot.
- Env file values must never be printed, committed, pasted into chat, or logged.
- Repo docs/templates must use placeholders only.
- Token rotation is mandatory if any token, bearer header, env value, or transcript text is exposed.

Gateway env:

```text
gateway_env=/etc/ai-secretary/openai-realtime-gateway.env
required_values=OPENAI_API_KEY,GATEWAY_TOKEN
value_checks=masked_presence_only
repo_commit=false
```

Asterisk env:

```text
openai_api_key_on_asterisk=false
business_dialog_gateway_use_default=false
transcript_logging_default=false
```

## Decision 6: Health / Observability

Minimal health and observability for NODE-032I:

- `systemctl is-active ai-secretary-gateway.service`.
- `systemctl is-enabled ai-secretary-gateway.service` recorded as disabled unless enablement is explicitly approved.
- `ss` confirms `8080` listener only after service start.
- `ss` confirms no `443` or `8081` listener.
- UFW confirms `8080/tcp` source-restricted to `92.118.85.117`.
- Masked env presence checks pass.
- Gateway health endpoint may be used if available; otherwise service/process/listener checks are acceptable.
- Journald tail may be inspected only for redacted lifecycle/error facts.
- `transcript_text_logged=false` remains required.
- `business_dialog_unchanged=true` remains required.

If a dedicated `/health` endpoint is missing, adding one may be a separate implementation node; NODE-032I should not broaden scope just to add code.

## Rollback Strategy

Command-level rollback for future live nodes:

```bash
sudo systemctl stop ai-secretary-gateway.service || true
sudo systemctl disable ai-secretary-gateway.service || true
test -f /etc/systemd/system/ai-secretary-gateway.service.node032i.bak && sudo cp /etc/systemd/system/ai-secretary-gateway.service.node032i.bak /etc/systemd/system/ai-secretary-gateway.service
test -f /etc/systemd/system/ai-secretary-gateway.service.node032i.bak || sudo rm -f /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
```

Env/firewall rollback:

```bash
# Preserve /etc/ai-secretary/openai-realtime-gateway.env unless the live node explicitly changed ownership/mode.
# If ownership/mode is changed, restore from the pre-change stat captured by that node.
sudo ufw status verbose
# Keep existing 8080 allow unless the live node explicitly changed it or operator approved cleanup.
```

Post-rollback verification:

```bash
systemctl is-active ai-secretary-gateway.service || true
systemctl is-enabled ai-secretary-gateway.service || true
ss -ltnp | grep -E ':(443|8080|8081)' || echo no_target_listeners_443_8080_8081
ufw status verbose
# Verify Asterisk OPENAI_API_KEY_ABSENT with masked process-env check only.
```

If any secret exposure occurs, stop, rotate exposed tokens, and record only redacted incident evidence.

## Next Live Node Recommendation

Next recommended node:

```text
NODE-032I / controlled-persistent-gateway-service-and-reboot-smoke
```

Recommended NODE-032I scope:

- Re-confirm live gates.
- Install/adapt `ai-secretary-gateway.service` with non-root runtime.
- Resolve env file ownership/mode for non-root read without printing values.
- Start service and run one Asterisk-origin helper smoke.
- Leave service disabled unless enablement is explicitly approved in NODE-032I.
- Stop/rollback or preserve installed-disabled state according to exact approval.
- Do not enable business dialog transcript use.
- Do not expose `443` or `8081`.
- Do not broaden firewall.

Reboot/power-cycle verification should be a separate controlled step unless NODE-032I explicitly includes exact approval for enablement and reboot/power-cycle proof.

## Remaining Blockers

- `gateway:gateway` service account must be present or created in a future approved live node.
- Historical env file ownership/mode must be adjusted or safely mediated for non-root service read.
- Durable unit path must be installed and reviewed before enablement.
- Firewall source restriction must be re-confirmed immediately before any persistent start.
- Reboot/power-cycle proof remains unperformed.
- Business dialog integration remains out of scope until gateway persistence is proven.

## Result

```text
node_status=docs_only_strategy_complete
live_apply=false
ssh_used=false
server_state_changed=false
service_installed_started_stopped_restarted_reloaded_enabled=false
firewall_changed=false
env_files_edited=false
live_smoke=false
business_dialog_enabled=false
notion_write=false
runtime_evidence_create=false
github_write=false
scheduler_webhook_automation_added=false
real_secrets_logged=false
transcript_text_logged=false
data_storage_staged=false
node014_server_tar_staged=false
```
