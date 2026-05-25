# NODE-031 / productionize-gateway-runtime-boundary

Status: Draft (implementation docs & templates)

Summary
-------

This node defines the production runtime boundary, deployment templates, validation checklist, rollback procedure, and operational controls for the supported-region OpenAI Realtime gateway used by AI-secrenar-with-Asterisk. This node does NOT perform any live deployment or start/stop any services.

Scope boundary: NODE-031 is documentation and safe placeholder templates only. It performs no server SSH, no systemd apply, no firewall apply, no gateway start/stop, no Asterisk restart, no live smoke, no Notion write, no Runtime/Evidence create, no GitHub write, and no scheduler/webhook/automation enablement.

Goals
-----

- Define service ownership and supervised process boundaries for a production gateway host.
- Define the network/TLS/reverse-proxy boundary and firewall assumptions.
- Define the secret boundary and rotation/compromise actions.
- Provide safe placeholder deployment templates for operator use.
- Provide a validation checklist and rollback/cleanup steps for operators.

Non-goals
---------

- Do not change source/runtime behavior.
- Do not enable gateway STT or business dialog transcript use.
- Do not place `OPENAI_API_KEY` on the Asterisk safe profile.
- Do not commit real `.env` files, tokens, host credentials, or private keys.
- Do not perform live deployment; the first live apply/smoke is reserved for `NODE-032 / controlled-production-gateway-live-smoke`.

1. Production gateway runtime boundary
-------------------------------------

- Service ownership: Gateway service is owned by the infra/ops team. The service owner is responsible for secret rotation, firewall policy, TLS certificate management, and incident response.
- Systemd / supervised process boundary: Gateway must run under a systemd service (or equivalent supervisor) on the gateway host. The repo contains only an example unit template; operators must adapt and install manually.
- Port / listen boundary: The gateway should listen on a private bind address and port behind a reverse proxy. Public exposure must be via TLS-terminating reverse proxy only. Use a non-default ephemeral application port (example: `127.0.0.1:8081` internally) and expose through a reverse proxy on `443`.
- Local / private exposure assumptions: The gateway process must not be exposed directly on a public interface. Local-only admin endpoints (health, metrics) must be bound to localhost or protected by the reverse proxy with mTLS/bearer auth.
- Firewall source restriction: Only the required sources should reach the gateway reverse-proxy: Asterisk server IP(s), operator management IPs, and monitoring probes. Default-deny inbound policy; allow only explicit CIDRs.
- TLS / reverse proxy boundary: TLS must be terminated at a hardened reverse proxy (e.g., nginx, Caddy, haproxy) with modern ciphers, OCSP stapling, and automatic cert renewal. The reverse proxy must forward a single internal connection to the gateway app over local loopback or private network.
- Env file ownership and permissions: Runtime env files (e.g., `/etc/ai-secretary/gateway.env`) must be owned by a dedicated unix account (e.g., `gateway`), readable only by root and the service account (mode `0640` or `0600` where appropriate). Do not store secrets in world-readable files.
- Log redaction requirements: All application logs must redact transcript text by default. Logs may contain presence flags, token counts, timing and quality metrics, but raw `transcript` text must be omitted or redacted unless an explicit, audited, and timeboxed operator action enables transcript logging.

2. Secret boundary
------------------

- `OPENAI_API_KEY` must live only on the gateway host and in secure OS-level secret storage (env file owned by root/service user, or a secrets manager). It MUST NOT be present in the Asterisk safe profile or any Asterisk-side env file.
- `GATEWAY_TOKEN` (Asterisk -> Gateway bearer) must be treated as a server-side secret and stored only on the gateway and in operator vaults. The Asterisk client uses only the token at runtime; no long-term `OPENAI_API_KEY` on Asterisk.
- Repo templates must use placeholders only (e.g., `OPENAI_API_KEY=REPLACE_ME`, `GATEWAY_TOKEN=REPLACE_ME`). Do NOT commit actual tokens or `.env` files with real secrets.
- Token rotation procedure:
  - Generate a new token in the operator vault.
  - Pause accepting new measurement requests (optional maintenance window).
  - Deploy the new token to the gateway env file and reload/restart the gateway service (operator action).
  - Update Asterisk runtime token (via safe profile or operator inventory) and restart the Asterisk gateway client if required.
  - Verify successful auth from Asterisk with a one-off authenticated health probe.
  - Revoke the old token from the vault after confirmation.
- Action required if token is exposed: Immediately revoke the token from the operator vault, rotate to a new token, examine logs for suspicious activity, and follow incident response checklist (see Rollback/Cleanup below).

3. Dialog / STT boundary
------------------------

- Gateway STT remains disabled by default. Production gateway may offer STT measurement or streaming, but business dialog must not read or use transcript text unless an explicit, audited node enables it.
- Business dialog must not use gateway transcript unless a later explicit node enables it. The default runtime flag is `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`.
- Transcript text must not be logged by default. Logs may record `transcript_present=true/false` and redacted metrics only.
- Measurement helpers and business dialog paths must remain distinct: provide distinct endpoints and feature flags for diagnostic measurement vs. dialog-driving STT.

4. Live deployment prerequisites (operator checklist)
--------------------------------------------------

- Confirm server access (OS user with sudo) and inventory of gateway host IP.
- Confirm current safe runtime (Asterisk does not contain `OPENAI_API_KEY`).
- Prepare env file manually on gateway host (`/etc/ai-secretary/gateway.env`) using operator vault secrets; do not place secrets in repo.
- Review firewall plan: allow only Asterisk IP(s) to reach gateway reverse proxy and only operator IPs to reach admin endpoints.
- Review TLS / reverse proxy plan and certificate management (ACME or operator-supplied certs).
- Prepare rollback plan and incident contact list.
- Confirm there are no real secrets in chat/logs/docs to be published.
- Schedule NODE-032 as the first live apply/smoke node (explicit operator approval required).

5. Rollback / cleanup
---------------------

Operator rollback steps (manual):

1. Stop gateway service: `sudo systemctl stop ai-secretary-gateway.service` (operator only).
2. Restore previous systemd unit or service file if the operator replaced it.
3. Close or restrict any opened public ports on the reverse proxy or firewall.
4. Remove any temporary files used during deployment and delete `/tmp`-stage artifacts.
5. Clear local env staging (do not commit env files to repo).
6. Verify Asterisk runtime config: ensure Asterisk safe profile contains no `OPENAI_API_KEY`.
7. Preserve transcript redaction: confirm logs do not contain raw transcript text.
8. If token compromise suspected: rotate tokens and revoke old tokens.

6. Health-check and validation commands (examples)
------------------------------------------------

- Local gateway health (on gateway host):

  - `curl --silent --fail -H "Authorization: Bearer $GATEWAY_TOKEN" https://127.0.0.1:8443/health` (operator to adapt to proxy and bind address)

- Auth test from Asterisk host (dry-run, token-only call):

  - `curl -X POST -H "Authorization: Bearer $GATEWAY_TOKEN" -F "file=@/path/to/test.wav" https://gateway.example.com/api/v1/measure` (do not include real tokens in scripts)

- Verify Asterisk has no `OPENAI_API_KEY`:

  - On Asterisk host: `grep -n "OPENAI_API_KEY" -R /etc /home /opt || true`

7. Token rotation / compromise procedure (concise)
-------------------------------------------------

- Rotate tokens via vault; update gateway env file; reload gateway service; update Asterisk client token; verify; revoke old token.
- If `OPENAI_API_KEY` is accidentally placed on any non-gateway host, immediately remove it, rotate the key in OpenAI via operator portal, and audit logs.

8. Future live-smoke prerequisites (for NODE-032)
-------------------------------------------------

- NODE-032 must be the first node to perform any live apply or smoke. It must require explicit operator approval and an operator-run checklist execution.
- NODE-032 prerequisites:
  - Confirmed writable operator vault entries for `GATEWAY_TOKEN` and `OPENAI_API_KEY`.
  - TLS and reverse proxy in place.
  - Firewall rules applied and tested.
  - Production health-check endpoints responding.
  - Asterisk-side client configured to use gateway token only (no `OPENAI_API_KEY`).
  - Rollback plan rehearsed and approved.

9. Documentation and templating guidance
---------------------------------------

- Repo contains safe examples and placeholders only. Operators must copy templates to the gateway host and replace placeholders from a vault.
- Do NOT check real env files, tokens, or private keys into version control.
- `deploy/templates/gateway.env.example`, `deploy/templates/gateway-systemd.service.example`, and `deploy/templates/gateway-nginx-proxy.example` are examples only and are not executable deployment instructions.

Appendix: operator-friendly deploy templates are available under `deploy/templates/`.
