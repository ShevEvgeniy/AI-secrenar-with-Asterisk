# NODE-032 / controlled-production-gateway-live-smoke

Status: Phase A complete draft (preflight and command plan only)

Summary
-------

NODE-032 is the first planned live apply/smoke node for the production gateway path after NODE-031. Phase A prepares the preflight checklist, approval gate, exact Phase B command plan, and rollback/cleanup plan. Phase A does not perform live apply, does not start/stop/restart/reload any service, does not change server state, and does not run a live smoke.

Current baseline
----------------

- NODE-030 proved transcript-bearing OpenAI Realtime gateway events with a controlled non-caller-facing Russian speech WAV.
- NODE-031 was merged via PR #2 at merge commit `8d5ef1e`.
- NODE-031 added production gateway boundary docs and safe placeholder templates:
  - `deploy/templates/gateway.env.example`;
  - `deploy/templates/gateway-systemd.service.example`;
  - `deploy/templates/gateway-nginx-proxy.example`.
- No NODE-031 live deployment occurred.
- Gateway STT remains disabled by default.
- Business dialog must not use gateway transcript text in NODE-032.
- Transcript text must not be logged.
- The Asterisk safe profile must not contain `OPENAI_API_KEY`.
- The supported-region gateway owns OpenAI Realtime access.

Phase A scope
-------------

Allowed:

- Inspect local repo docs/templates/runbook from NODE-031.
- Prepare Phase B live apply/smoke commands.
- Document preconditions, approval gates, rollback, cleanup, and blocked outcomes.
- Optionally run read-only server inspection commands in a later operator session only if credentials are already available and the commands cannot change state.

Forbidden:

- No live server state changes.
- No systemd apply.
- No `systemctl start`, `stop`, `restart`, or `reload`.
- No firewall apply.
- No gateway start/stop.
- No Asterisk restart.
- No live call or live smoke.
- No business dialog enablement.
- No env secret changes.
- No real tokens in files, logs, or chat.
- No `.env` commit.
- No Notion write.
- No Runtime/Evidence create or update.
- No scheduler, webhook, or automation loop.

Phase A preflight checklist
---------------------------

Local repo checks:

- Confirm branch starts from current `master`.
- Confirm NODE-031 files exist and templates are placeholder-only.
- Confirm `git status --short` shows only expected local artifacts before edits.
- Confirm no files under `src`, `tests`, or `scripts` changed.
- Confirm no runtime config changed.
- Confirm `.env` is not tracked.
- Confirm `data/storage/` and `node014-server.tar` remain untracked and untouched.

Server access checks (read-only only in Phase A):

- Confirm gateway host access path and operator identity are known.
- Confirm Asterisk host access path and operator identity are known.
- Confirm sudo availability only as a fact; do not run privileged mutating commands.
- Confirm operator has access to the vault entries for `OPENAI_API_KEY` and `GATEWAY_TOKEN` without printing values.

Asterisk safe profile masked checks (read-only only in Phase A):

```bash
# Operator-run read-only example; do not paste secret values into chat/logs.
printenv | grep -E '^(STT_GATEWAY|REALTIME_GATEWAY|OPENAI_API_KEY)=' | sed -E 's/=(.*)$/=<masked>/'
grep -R "OPENAI_API_KEY" /etc /home /opt 2>/dev/null | sed -E 's/(OPENAI_API_KEY=).*/\1<masked>/'
```

Expected:

- `OPENAI_API_KEY` is absent from the Asterisk safe profile and Asterisk-side env files.
- Asterisk may have only gateway URL/token runtime references, with token values masked.
- `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false` remains the expected production default.

Gateway env masked checks (read-only only in Phase A):

```bash
# Operator-run read-only example on gateway host; do not print values.
test -f /etc/ai-secretary/gateway.env && stat -c '%U %G %a %n' /etc/ai-secretary/gateway.env
grep -E '^(OPENAI_API_KEY|GATEWAY_TOKEN|STT_GATEWAY)' /etc/ai-secretary/gateway.env | sed -E 's/=(.*)$/=<masked>/'
```

Expected:

- Gateway env exists only when manually prepared by operator.
- `OPENAI_API_KEY` and `GATEWAY_TOKEN` are present only on the gateway/vault side.
- File permissions are `0600` or `0640`, owned by root/service boundary.
- Repo templates remain blank/placeholders.

Current service/listen/firewall read-only checks:

```bash
# Operator-run read-only examples only.
systemctl status ai-secretary-gateway.service --no-pager
systemctl is-enabled ai-secretary-gateway.service
ss -ltnp | grep -E '(:443|:8081|ai-secretary-gateway)' || true
sudo nft list ruleset
sudo iptables -S
```

Phase A rule: commands above are inspection only. Do not run `systemctl start`, `stop`, `restart`, `reload`, `enable`, `disable`, `daemon-reload`, firewall write commands, or config copy commands until Phase B is explicitly approved.

Secret redaction checks:

- Do not paste real `OPENAI_API_KEY`, `GATEWAY_TOKEN`, bearer headers, `.env` contents, private keys, or vault output into chat/logs/docs.
- Logs may include `transcript_present=true/false`, timing, HTTP status, and redacted auth state.
- Logs must not include transcript text by default.

Rollback readiness checks:

- Confirm previous gateway service state is known before any Phase B change.
- Confirm prior systemd unit/config backup path is planned.
- Confirm firewall rollback commands are ready before applying new firewall rules.
- Confirm temporary file cleanup paths are known.
- Confirm token rotation procedure and incident contact are available.

Approval gate
-------------

Phase B must not begin until the operator provides this exact approval phrase:

```text
APPROVE NODE-032 LIVE APPLY/SMOKE
```

Any other wording is not sufficient. Approval must be timeboxed to one controlled apply/smoke attempt and must not authorize business dialog transcript enablement.

Phase B command plan
--------------------

The following is a command plan only. Do not execute in Phase A.

1. Prepare gateway env manually on the gateway host:

```bash
sudo install -d -m 0750 -o root -g gateway /etc/ai-secretary
sudo install -m 0640 -o root -g gateway /dev/null /etc/ai-secretary/gateway.env
sudoedit /etc/ai-secretary/gateway.env
sudo grep -E '^(OPENAI_API_KEY|GATEWAY_TOKEN|GATEWAY_BIND|STT_GATEWAY)' /etc/ai-secretary/gateway.env | sed -E 's/=(.*)$/=<masked>/'
```

Required env values:

```text
OPENAI_API_KEY=<gateway-only vault value>
GATEWAY_TOKEN=<gateway bearer token from vault>
GATEWAY_BIND=127.0.0.1:8081
STT_GATEWAY_STT_ENABLED=false
STT_GATEWAY_ADAPTER_ENABLED=false
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_LOG_TRANSCRIPT=false
```

2. Install/adapt systemd unit from template:

```bash
sudo install -m 0644 /tmp/gateway-systemd.service.example /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
sudo systemctl cat ai-secretary-gateway.service
```

3. Install/adapt TLS reverse proxy config if applicable:

```bash
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

5. Start/reload gateway and reverse proxy:

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

7. One controlled smoke:

```bash
python -m ai_secretary.stt.gateway_adapter_smoke \
  --audio <non-sensitive-russian-speech-wav> \
  --require-explicit-flags
```

Required temporary process env for the one-off smoke:

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

9. Cleanup or persistent service state decision:

- If the service is intended to remain persistent, record approval and service state.
- If the service was only for smoke, stop it and verify port closure as part of rollback/cleanup.
- In either case, preserve transcript redaction and do not enable business dialog transcript use.

Rollback and cleanup plan
-------------------------

Rollback commands are for Phase B only after explicit approval or emergency cleanup:

```bash
sudo systemctl stop ai-secretary-gateway.service
sudo systemctl status ai-secretary-gateway.service --no-pager
sudo cp /etc/systemd/system/ai-secretary-gateway.service.bak /etc/systemd/system/ai-secretary-gateway.service
sudo systemctl daemon-reload
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

Next possible outcomes
----------------------

- Phase A ready for approval: local docs/templates are ready, access/preconditions can be verified by operator, and Phase B may proceed only after `APPROVE NODE-032 LIVE APPLY/SMOKE`.
- Blocked due to missing access/secrets/templates: do not begin Phase B; update this node with the missing prerequisite.
- Blocked due to unsafe current server state: do not begin Phase B; remediate or create a separate scoped node.

Phase A result
--------------

Phase A produced documentation and command planning only. No live apply was performed, no service was started/stopped/restarted/reloaded, no server state changed, and no live smoke was run.
