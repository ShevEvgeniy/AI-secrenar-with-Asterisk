# NODE-032G / controlled-gateway-live-smoke-with-asterisk-side-helper

## Summary

NODE-032G Phase A re-confirms live gates and prepares the controlled live smoke plan that will use the NODE-032F Asterisk-side helper. Phase A is planning/read-only only.

No live apply, helper copy/deploy, service install, systemd write, service start/stop/restart/reload, firewall change, env edit, gateway start/stop, Asterisk restart, live call, live smoke, business dialog enablement, transcript text logging, Notion write, Runtime/Evidence update, scheduler, webhook, or automation loop occurred.

Phase B is not approved by this node. Future live apply/smoke requires the exact phrase:

```text
APPROVE NODE-032G LIVE APPLY/SMOKE
```

No other phrase is approval.

## Baseline

- NODE-032F merged via PR #8 / merge commit `b633006`.
- NODE-032F added `scripts/asterisk_gateway_smoke_helper.py`.
- The helper wraps `ai_secretary.stt.gateway_adapter_smoke`.
- The helper is manual-only, fail-closed, refuses Asterisk-side `OPENAI_API_KEY`, requires `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`, does not print token values, does not print transcript text, records `transcript_text_logged=false` and `business_dialog_unchanged=true`, and adds no autostart behavior.
- NODE-032G must prove:

```text
92.118.85.117 -> 45.61.48.199:8080
```

## Local Repo Checks

Commands run:

```text
git switch master
git pull --ff-only origin master
git status --short
git switch -c feat/node-032g-controlled-gateway-live-smoke-with-asterisk-side-helper
Test-Path scripts\asterisk_gateway_smoke_helper.py
Test-Path tests\test_asterisk_gateway_smoke_helper.py
Test-Path src\ai_secretary\stt\gateway_adapter_smoke.py
rg -n "ai_secretary.stt.gateway_adapter_smoke|fail-closed|OPENAI_API_KEY must be absent|STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG|STT_GATEWAY_LOG_TRANSCRIPT|secret_values_printed|transcript_text_logged|business_dialog_unchanged|autostart_configured|persistent_server_state_created" scripts/asterisk_gateway_smoke_helper.py src/ai_secretary/stt/gateway_adapter_smoke.py tests/test_asterisk_gateway_smoke_helper.py docs/nodes/NODE-032F-prepare-asterisk-side-gateway-smoke-helper-or-approved-smoke-path.md
Get-Content scripts\asterisk_gateway_smoke_helper.py
```

Findings:

```text
helper_exists=true
helper_tests_exist=true
core_smoke_helper_exists=true
helper_wraps_existing_gateway_adapter_smoke=true
helper_manual_only=true
helper_fail_closed=true
helper_refuses_asterisk_openai_api_key=true
helper_requires_dialog_use_false=true
helper_requires_transcript_logging_false=true
safe_flags_include_transcript_text_logged=false
safe_flags_include_business_dialog_unchanged=true
autostart_added=false
persistent_server_state_created=false
```

## Asterisk Read-Only Gate

Target:

```text
92.118.85.117
```

Commands run:

```text
ssh root@92.118.85.117 "hostname"
ssh root@92.118.85.117 "uptime"
ssh root@92.118.85.117 "systemctl is-active ai-secretary-ari.service"
ssh root@92.118.85.117 "systemctl is-enabled ai-secretary-ari.service"
ssh root@92.118.85.117 "systemctl show ai-secretary-ari.service -p MainPID --value"
ssh root@92.118.85.117 "systemctl show ai-secretary-ari.service -p Environment --no-pager"
ssh root@92.118.85.117 "tr '\0' '\n' < /proc/3815/environ | grep -q '^OPENAI_API_KEY=' && echo OPENAI_API_KEY_PRESENT || echo OPENAI_API_KEY_ABSENT"
ssh root@92.118.85.117 "test -d /home/tulauser/AI-secrenar-with-Asterisk-node014 && echo repo_node014_present || echo repo_node014_absent; test -f /home/tulauser/AI-secrenar-with-Asterisk-node014/scripts/asterisk_gateway_smoke_helper.py && echo node014_helper_present || echo node014_helper_absent; test -f /home/tulauser/AI-secrenar-with-Asterisk-node014/src/ai_secretary/stt/gateway_adapter_smoke.py && echo node014_core_helper_present || echo node014_core_helper_absent"
ssh root@92.118.85.117 "test -f /home/tulauser/AI-secrenar-with-Asterisk-node014/src/ai_secretary/stt/gateway_adapter.py && echo gateway_adapter_present || echo gateway_adapter_absent"
ssh root@92.118.85.117 "test -f /home/tulauser/AI-secrenar-with-Asterisk-node014/src/ai_secretary/stt/realtime_measurement.py && echo realtime_measurement_present || echo realtime_measurement_absent"
ssh root@92.118.85.117 "test -f /home/tulauser/AI-secrenar-with-Asterisk-node014/src/ai_secretary/stt/realtime_gateway.py && echo realtime_gateway_present || echo realtime_gateway_absent"
ssh root@92.118.85.117 "cd /home/tulauser/AI-secrenar-with-Asterisk-node014 && git rev-parse --short HEAD 2>/dev/null || echo git_head_unavailable"
```

Sanitized findings:

```text
hostname=tula
uptime=reachable
ai-secretary-ari.service_active=active
ai-secretary-ari.service_enabled=enabled
main_pid_observed=3815
service_environment=PYTHONUNBUFFERED only
process_env_openai_api_key=OPENAI_API_KEY_ABSENT
business_dialog_changed=false_readonly_no_change
repo_path=/home/tulauser/AI-secrenar-with-Asterisk-node014 present
node014_helper_present=false
node014_core_helper_present=false
gateway_adapter_present=false
realtime_measurement_present=true
realtime_gateway_present=false
git_head=unavailable
```

One earlier SSH command attempt had unsafe local PowerShell quoting and failed locally before useful remote checks. It did not perform a state-changing command and produced no useful gate evidence.

## Gateway Read-Only Gate

Target:

```text
45.61.48.199
```

Commands run:

```text
ssh root@45.61.48.199 "hostname"
ssh root@45.61.48.199 "uptime"
ssh root@45.61.48.199 "test -f /etc/ai-secretary/openai-realtime-gateway.env && stat -c '%U %G %a %n' /etc/ai-secretary/openai-realtime-gateway.env || echo historical_env_absent"
ssh root@45.61.48.199 "grep -q '^OPENAI_API_KEY=' /etc/ai-secretary/openai-realtime-gateway.env && echo OPENAI_API_KEY_PRESENT_MASKED || echo OPENAI_API_KEY_ABSENT; grep -q '^GATEWAY_TOKEN=' /etc/ai-secretary/openai-realtime-gateway.env && echo GATEWAY_TOKEN_PRESENT_MASKED || echo GATEWAY_TOKEN_ABSENT"
ssh root@45.61.48.199 "systemctl is-active ai-secretary-gateway.service 2>/dev/null || echo inactive_or_absent"
ssh root@45.61.48.199 "systemctl is-enabled ai-secretary-gateway.service 2>/dev/null || echo not_enabled_or_absent"
ssh root@45.61.48.199 "ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081"
ssh root@45.61.48.199 "ufw status verbose"
```

Sanitized findings:

```text
hostname=ai-secretary-gateway-node023
uptime=reachable
historical_env=/etc/ai-secretary/openai-realtime-gateway.env present root:root 600
openai_api_key_presence=OPENAI_API_KEY_PRESENT_MASKED
gateway_token_presence=GATEWAY_TOKEN_PRESENT_MASKED
ai-secretary-gateway.service_active=inactive
ai-secretary-gateway.service_enabled=not-found
target_listeners_443_8080_8081=absent
ufw_status=active
ufw_default_incoming=deny
ufw_default_outgoing=allow
ufw_8080_allow=92.118.85.117 only
```

## Live Gate Status

Passed Phase A read-only gates:

- Asterisk SSH reachable.
- Asterisk `ai-secretary-ari.service` active/enabled.
- Asterisk process env has no `OPENAI_API_KEY`.
- Gateway SSH reachable.
- Gateway historical env exists as `root:root 600`.
- Gateway masked `OPENAI_API_KEY` and `GATEWAY_TOKEN` presence checks pass.
- Gateway has no target listeners on `443`, `8080`, or `8081`.
- Gateway UFW is active and `8080/tcp` is source-restricted to `92.118.85.117`.

Not yet satisfied for live smoke:

- Exact approval phrase is absent.
- Asterisk-side helper is not yet available on `/home/tulauser/AI-secrenar-with-Asterisk-node014`.
- The deployed Asterisk path is not a usable Git checkout and lacks multiple helper dependency files.

## Helper Availability Plan For Phase B

Because `/home/tulauser/AI-secrenar-with-Asterisk-node014` is not a usable Git checkout and lacks the wrapper plus required adapter modules, Phase B should not rely on `git pull` on the Asterisk host.

Preferred Phase B helper availability method after exact approval:

1. Re-confirm all hard gates.
2. Build a local helper bundle from current `master` containing only the repo-supported helper files required for the smoke:

```text
scripts/asterisk_gateway_smoke_helper.py
src/ai_secretary/__init__.py
src/ai_secretary/stt/__init__.py
src/ai_secretary/stt/gateway_adapter_smoke.py
src/ai_secretary/stt/gateway_adapter.py
src/ai_secretary/stt/realtime_gateway.py
src/ai_secretary/stt/realtime_measurement.py
```

3. Copy the bundle only after approval to a temporary Asterisk path:

```text
/tmp/node032g-asterisk-helper
```

4. Run the helper from that temporary path only.
5. Remove the temporary helper bundle during cleanup.

This method is a scoped helper deployment for the smoke only. It does not modify the production `ai-secretary-ari.service`, does not configure autostart, and does not change business dialog runtime.

If Phase B instead chooses to update the deployed application tree, that must be explicitly accepted because it is broader than the minimal helper-bundle method.

## Runtime Env Handling Plan

Avoid shell-history token exposure by using a temporary root-owned runtime env file created only after approval:

```text
/tmp/node032g-gateway-client.env
```

Required placeholder-only contents:

```text
STT_GATEWAY_STT_ENABLED=true
STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false
STT_GATEWAY_URL=http://45.61.48.199:8080
STT_GATEWAY_TOKEN=<gateway-token-from-secure-runtime>
STT_GATEWAY_TIMEOUT_MS=10000
STT_GATEWAY_LOG_TRANSCRIPT=false
```

The file must be mode `600`, must not contain `OPENAI_API_KEY`, must not be committed, and must be removed during cleanup. If any token value is printed, stop and rotate the token.

## Phase B Command Set Summary

Phase B is blocked until exact approval:

```text
APPROVE NODE-032G LIVE APPLY/SMOKE
```

Planned sequence after approval:

1. Re-run Asterisk and Gateway hard gates.
2. Prepare Gateway service only if gates pass:
   - install/adapt `ai-secretary-gateway.service`;
   - use `/etc/ai-secretary/openai-realtime-gateway.env`;
   - listen on `0.0.0.0:8080`;
   - no `443`, no `8081`, no TLS/proxy reload.
3. Start Gateway service only after unit is ready.
4. Verify:
   - `8080` listener exists;
   - no `443` or `8081` listener exists;
   - UFW still restricts `8080/tcp` to `92.118.85.117`.
5. Make the Asterisk helper bundle available at `/tmp/node032g-asterisk-helper`.
6. Create `/tmp/node032g-gateway-client.env` securely with gateway URL/token runtime material.
7. Run one Asterisk-origin smoke:

```text
cd /tmp/node032g-asterisk-helper
set -a
. /tmp/node032g-gateway-client.env
set +a
unset OPENAI_API_KEY
python scripts/asterisk_gateway_smoke_helper.py --audio <approved-non-sensitive-smoke-wav>
```

8. Capture safe flags only:
   - `gateway_reachable_from_asterisk`;
   - `gateway_auth`;
   - `openai_realtime_from_gateway`;
   - `chunks_sent`;
   - `transcript_present`;
   - `transcript_text_logged=false`;
   - `business_dialog_unchanged=true`.
9. Do not print transcript text.
10. Cleanup/rollback by default.

## Rollback And Cleanup Plan

After Phase B smoke or any failure after state change:

```text
systemctl stop ai-secretary-gateway.service
systemctl disable ai-secretary-gateway.service 2>/dev/null || true
rm -f /etc/systemd/system/ai-secretary-gateway.service
systemctl daemon-reload
rm -rf /tmp/node032g-asterisk-helper
rm -f /tmp/node032g-gateway-client.env
unset STT_GATEWAY_STT_ENABLED STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG STT_GATEWAY_URL STT_GATEWAY_TOKEN STT_GATEWAY_TIMEOUT_MS STT_GATEWAY_LOG_TRANSCRIPT REALTIME_GATEWAY_URL REALTIME_GATEWAY_TOKEN OPENAI_API_KEY
```

Post-cleanup checks:

```text
systemctl is-active ai-secretary-gateway.service 2>/dev/null || true
ss -ltnp | grep -E ':(443|8080|8081)\b' || echo no_target_listeners_443_8080_8081
ufw status verbose
verify Asterisk process env has OPENAI_API_KEY_ABSENT
verify business_dialog_changed=false
```

If a unit existed before Phase B, back it up before replacement and restore it during rollback. If any token/transcript is exposed, stop and rotate exposed tokens.

## Power-Cycle Safety

- Phase A created no server files and configured no autostart.
- Phase B helper bundle should live only under `/tmp/node032g-asterisk-helper`.
- Phase B gateway client env should live only under `/tmp/node032g-gateway-client.env` with mode `600`.
- No smoke should auto-run after reboot.
- No systemd timer, cron, scheduler, webhook, or automation loop is allowed.
- Business dialog remains unchanged after reboot/power-on.

## GO / NO-GO Recommendation

Recommendation: NO-GO for Phase B until the operator provides:

```text
APPROVE NODE-032G LIVE APPLY/SMOKE
```

Technical Phase A gates are otherwise ready for a tightly scoped Phase B attempt if re-confirmed immediately before state change and if the helper-bundle deployment is explicitly accepted as part of Phase B scope.

## Validation

Validation is recorded in the closeout report.

Known pre-existing/environmental full-suite failures remain unrelated to NODE-032G if observed:

- missing `src/scripts/make_demo_audio.py`;
- missing `sentence_transformers`.
