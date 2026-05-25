# NODE-032B / controlled-production-gateway-live-apply-and-smoke

Status: Phase A readiness/preflight only

Summary
-------

NODE-032B prepares the controlled production gateway live apply/smoke step after NODE-032 Phase A. This Phase A document records readiness checks, exact read-only preflight commands, exact Phase B live apply/smoke command plan, approval gate, rollback/cleanup, blockers, and expected evidence.

Phase A stops before live apply. It does not SSH to live servers, does not perform live apply, does not start/stop/restart/reload any service, does not change server state, and does not run live smoke.

Current baseline
----------------

- NODE-031 merged via PR #2 / merge commit `8d5ef1e`.
- NODE-032 Phase A merged via PR #3 / merge commit `ceda36b`.
- NODE-031 production gateway boundary and safe templates exist:
  - `deploy/templates/gateway.env.example`;
  - `deploy/templates/gateway-systemd.service.example`;
  - `deploy/templates/gateway-nginx-proxy.example`.
- NODE-032 Phase A documented preflight checks, masked server inspection commands, approval gate, Phase B command plan, rollback/cleanup, and blocked outcomes.
- No production gateway live apply/smoke has occurred yet.
- Gateway STT remains disabled by default outside scoped smoke.
- Business dialog must not use gateway transcript text in NODE-032B.
- Transcript text must not be logged.
- Asterisk safe profile must not contain `OPENAI_API_KEY`.
- Gateway owns OpenAI Realtime access and secrets.

Phase A readiness
-----------------

Local repo checks:

```powershell
git switch master
git pull --ff-only origin master
git status --short
git log --oneline -5
Test-Path docs\nodes\NODE-031-productionize-gateway-runtime-boundary.md
Test-Path docs\nodes\NODE-032-controlled-production-gateway-live-smoke.md
Get-ChildItem deploy\templates
git diff --name-only -- src tests deploy scripts pyproject.toml
git ls-files -- .env
git status --short -- data/storage node014-server.tar
```

Expected local result:

- `master` is current with `origin/master`.
- NODE-031 and NODE-032 docs exist.
- NODE-031 templates exist and contain placeholders only.
- No source/runtime files are changed.
- `.env` is not tracked.
- `data/storage/` and `node014-server.tar` remain untracked and untouched.

Docs/template checks:

```powershell
Select-String -Path deploy\templates\gateway.env.example -Pattern "OPENAI_API_KEY|GATEWAY_TOKEN|REPLACE|STT_GATEWAY"
Select-String -Path deploy\templates\gateway-systemd.service.example -Pattern "EnvironmentFile|ExecStart|User|Group"
Select-String -Path deploy\templates\gateway-nginx-proxy.example -Pattern "listen 443|proxy_pass|allow|deny|health"
```

Expected docs/template result:

- `gateway.env.example` contains blank or placeholder values only.
- Systemd template is explicitly example-only and must be adapted by the operator.
- Reverse proxy template contains placeholder host/cert paths and no hardcoded token.
- No real secrets are present in templates.

Server access readiness checks, read-only only:

```bash
# Operator-run only. Do not run in Phase A automation.
whoami
hostname -f
id
sudo -n true; echo "sudo_check_exit=$?"
```

Expected:

- Gateway host access path and operator identity are known.
- Asterisk host access path and operator identity are known.
- Sudo availability is known as a fact, but no mutating command is run.
- Operator confirms vault access for `OPENAI_API_KEY` and `GATEWAY_TOKEN` without printing values.

Asterisk safe profile masked checks, read-only only:

```bash
# Operator-run only on Asterisk host. Do not paste secret values into chat/logs.
printenv | grep -E '^(STT_GATEWAY|REALTIME_GATEWAY|OPENAI_API_KEY)=' | sed -E 's/=(.*)$/=<masked>/'
grep -R "OPENAI_API_KEY" /etc /home /opt 2>/dev/null | sed -E 's/(OPENAI_API_KEY=).*/\1<masked>/'
systemctl status ai-secretary-ari.service --no-pager
systemctl show ai-secretary-ari.service -p Environment --no-pager | sed -E 's/(TOKEN|KEY|SECRET)=[^ ]+/\1=<masked>/g'
```

Expected:

- `OPENAI_API_KEY` is absent from the Asterisk safe profile and Asterisk-side env files.
- Asterisk may reference gateway URL/token only through masked runtime config.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remains the expected production default.

Gateway env masked checks, read-only only:

```bash
# Operator-run only on gateway host. Do not print values.
test -f /etc/ai-secretary/gateway.env && stat -c '%U %G %a %n' /etc/ai-secretary/gateway.env
grep -E '^(OPENAI_API_KEY|GATEWAY_TOKEN|GATEWAY_BIND|STT_GATEWAY)' /etc/ai-secretary/gateway.env | sed -E 's/=(.*)$/=<masked>/'
```

Expected:

- Gateway env exists only when manually prepared by operator.
- Gateway-side `OPENAI_API_KEY` and `GATEWAY_TOKEN` values are present only on gateway/vault side and are masked in output.
- File permissions are `0600` or `0640`, owned by root/service boundary.
- Repo templates remain placeholders only.

Current service/listen/firewall read-only checks:

```bash
# Operator-run read-only examples only.
systemctl status ai-secretary-gateway.service --no-pager
systemctl is-enabled ai-secretary-gateway.service
systemctl cat ai-secretary-gateway.service --no-pager
ss -ltnp | grep -E '(:443|:8081|ai-secretary-gateway)' || true
sudo nft list ruleset
sudo iptables -S
```

Phase A rule: the commands above are inspection only. Do not run `systemctl start`, `stop`, `restart`, `reload`, `enable`, `disable`, `daemon-reload`, firewall write commands, config copy commands, gateway start/stop commands, or proxy reload commands until Phase B is explicitly approved.

Secret redaction checks:

- Do not paste real `OPENAI_API_KEY`, `GATEWAY_TOKEN`, bearer headers, `.env` contents, private keys, or vault output into chat/logs/docs.
- Logs may include `transcript_present=true/false`, timing, HTTP status, quality metrics, and redacted auth state.
- Logs must not include transcript text by default.
- Run local tracked and practical scoped token scans before any commit.

Rollback readiness checks:

- Confirm previous gateway service state is recorded before any Phase B change.
- Confirm prior systemd unit/config backup path is planned.
- Confirm firewall rollback commands are known before applying new firewall rules.
- Confirm proxy rollback command is known before any proxy reload.
- Confirm temporary file cleanup paths are known.
- Confirm token rotation and incident contacts are available.
- Confirm Asterisk safe profile verification command is ready.

Go/no-go criteria:

- Go only if templates are present, operator access is confirmed, vault values are available without exposure, current server state is safe, rollback is ready, and the exact approval phrase is provided.
- No-go if access, secrets, templates, safe Asterisk profile, firewall/proxy plan, rollback, or redaction cannot be verified.

Approval gate
-------------

Phase B must not begin until the operator explicitly provides this exact approval phrase:

```text
APPROVE NODE-032B LIVE APPLY/SMOKE
```

No other phrase is approval. Approval is scoped to one controlled production gateway apply/smoke attempt and does not authorize business dialog transcript use.

Phase B live apply/smoke plan
-----------------------------

The following is a command plan only. Do not execute in Phase A.

1. Prepare gateway env manually from vault/secure values:

```bash
sudo install -d -m 0750 -o root -g gateway /etc/ai-secretary
sudo install -m 0640 -o root -g gateway /dev/null /etc/ai-secretary/gateway.env
sudoedit /etc/ai-secretary/gateway.env
sudo grep -E '^(OPENAI_API_KEY|GATEWAY_TOKEN|GATEWAY_BIND|STT_GATEWAY)' /etc/ai-secretary/gateway.env | sed -E 's/=(.*)$/=<masked>/'
```

Required safe values:

```text
OPENAI_API_KEY=<vault>
GATEWAY_TOKEN=<gateway bearer token from vault>
GATEWAY_BIND=127.0.0.1:8081
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

2. Install/adapt systemd unit:

```bash
sudo cp /etc/systemd/system/ai-secretary-gateway.service /etc/systemd/system/ai-secretary-gateway.service.bak 2>/dev/null || true
sudo install -m 0644 /tmp/gateway-systemd.service.example /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
sudo systemctl cat ai-secretary-gateway.service
```

3. Install/adapt TLS reverse proxy config if applicable:

```bash
sudo cp /etc/nginx/sites-available/ai-secretary-gateway.conf /etc/nginx/sites-available/ai-secretary-gateway.conf.bak 2>/dev/null || true
sudo install -m 0644 /tmp/gateway-nginx-proxy.example /etc/nginx/sites-available/ai-secretary-gateway.conf
sudo nginx -t
```

4. Apply firewall restrictions:

```bash
# Operator must adapt exact firewall backend and source CIDRs.
sudo nft add rule inet filter input ip saddr <ASTERISK_CIDR> tcp dport 443 accept
sudo nft add rule inet filter input ip saddr <OPERATOR_CIDR> tcp dport 443 accept
sudo nft add rule inet filter input tcp dport 443 drop
sudo nft list ruleset
```

5. Start/reload gateway/proxy only after approval:

```bash
sudo systemctl start ai-secretary-gateway.service
sudo systemctl status ai-secretary-gateway.service --no-pager
sudo systemctl reload nginx
ss -ltnp | grep -E '(:443|:8081|ai-secretary-gateway)'
```

6. Health check:

```bash
curl --fail --silent --show-error https://gateway.example.com/health
```

If health requires auth, use a masked runtime token source and do not echo the token:

```bash
curl --fail --silent --show-error -H "Authorization: Bearer ${GATEWAY_TOKEN}" https://gateway.example.com/health
```

7. One controlled non-business-dialog smoke:

```bash
python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio <non-sensitive-russian-speech-wav> \
  --require-explicit-flags
```

Required temporary one-off smoke env:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_ADAPTER_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
STT_GATEWAY_URL=https://gateway.example.com/v1/stt/realtime-measurement
STT_GATEWAY_TOKEN=<masked runtime token>
OPENAI_API_KEY=<absent on Asterisk>
```

8. Verify smoke invariants:

```text
gateway_reachable=true
gateway_auth=ok
openai_realtime_from_gateway=ok
transcript_text_logged=false
transcript_used_for_dialog=false
business_dialog_changed=false
asterisk_openai_key_present_after_smoke=no
```

9. Cleanup vs persistent service state decision:

- If service should remain persistent, record the explicit approval, service state, port state, firewall/proxy state, and monitoring/owner.
- If service was only for smoke, stop it and verify port closure through rollback/cleanup.
- In either case, do not enable business dialog transcript use and do not log transcript text.

Rollback and cleanup
--------------------

Rollback commands are Phase B only after approval or emergency cleanup:

```bash
sudo systemctl stop ai-secretary-gateway.service
sudo systemctl status ai-secretary-gateway.service --no-pager
test -f /etc/systemd/system/ai-secretary-gateway.service.bak && sudo cp /etc/systemd/system/ai-secretary-gateway.service.bak /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
test -f /etc/nginx/sites-available/ai-secretary-gateway.conf.bak && sudo cp /etc/nginx/sites-available/ai-secretary-gateway.conf.bak /etc/nginx/sites-available/ai-secretary-gateway.conf
sudo nginx -t
sudo systemctl reload nginx
sudo nft delete rule inet filter input handle <HANDLE>
sudo rm -f /tmp/gateway-systemd.service.example /tmp/gateway-nginx-proxy.example
unset OPENAI_API_KEY GATEWAY_TOKEN STT_GATEWAY_TOKEN REALTIME_GATEWAY_TOKEN
grep -R "OPENAI_API_KEY" /etc /home /opt 2>/dev/null | sed -E 's/(OPENAI_API_KEY=).*/\1<masked>/'
```

If any token is exposed:

- Revoke exposed `GATEWAY_TOKEN`.
- Rotate `OPENAI_API_KEY` if exposed outside gateway/vault.
- Review gateway, reverse proxy, and shell logs for exposure.
- Preserve redacted incident evidence only.

Expected evidence
-----------------

Record only redacted evidence:

- server targets;
- service state before/after;
- port/listen state before/after;
- firewall/TLS state;
- gateway env masked checks;
- Asterisk safe profile masked checks;
- gateway health result;
- smoke result;
- transcript flags without transcript text;
- business dialog unchanged;
- cleanup or persistent service state decision.

Next possible outcomes
----------------------

- Ready for explicit approval: all Phase A checks are complete and Phase B may proceed only after `APPROVE NODE-032B LIVE APPLY/SMOKE`.
- Blocked due to missing access/secrets/templates: do not begin Phase B; update this node or create a separate node for the missing prerequisite.
- Blocked due to unsafe current server state: do not begin Phase B; remediate through a separate scoped node.
- Blocked due to unresolved rollback plan: do not begin Phase B until rollback is explicit and tested as a plan.

Phase A result
--------------

NODE-032B Phase A is readiness/preflight documentation only. No live apply was performed, no service was started/stopped/restarted/reloaded, no server state changed, no live smoke was run, no business dialog behavior changed, no Notion write occurred, no Runtime/Evidence record was created, no GitHub write occurred, and no scheduler/webhook/automation mode was added.
