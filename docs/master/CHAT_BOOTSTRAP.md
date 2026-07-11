# AI-secrenar Chat Bootstrap

## Project Identity

- Project name: `AI-secrenar-with-Asterisk`
- Local path: `C:\Projects\AI-secrenar-with-Asterisk`
- GitHub repo: `ShevEvgeniy/AI-secrenar-with-Asterisk`
- Default branch: `master`
- Latest known commit: `901b5a4` (`Close NODE-030 speech gateway smoke`)
- Latest completed node: `NODE-030 / controlled-russian-speech-wav-gateway-transcript-smoke`
- Current planned next technical node: `NODE-031 / productionize-gateway-runtime-boundary`

## Safe Runtime Assumptions

- Production gateway STT remains disabled by default.
- Normal business dialog does not use gateway transcripts unless a scoped node explicitly enables and validates that behavior.
- `STT_GATEWAY_STT_ENABLED=false`, `STT_GATEWAY_ADAPTER_ENABLED=false`, `STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false`, and `STT_GATEWAY_LOG_TRANSCRIPT=false` remain the safe defaults.
- `ai-secretary-ari.service` remains in the diagnostic-safe runtime profile unless a scoped node changes it.
- `OPENAI_API_KEY` must not be placed on the Asterisk server.
- Transcript text is not logged by default.
- Business dialog, live calls, deploys, service restarts, gateway start/stop, scheduler/webhook/automation loops, and env-file edits require an explicit scoped node.

## Non-Secret Server Inventory Summary

- Asterisk server: documented in prior node evidence as the server running the colocated `ari_app` and `ai-secretary-ari.service`.
- Kamatera supported-region gateway: USA / New York 2, public IP `45.61.48.199`, prior smoke deploy path `/opt/ai-secretary-gateway`.
- Gateway smoke endpoint used historically: `http://45.61.48.199:8080/v1/stt/realtime-measurement`.
- The historical gateway listener was temporary HTTP for controlled smoke only and was stopped after NODE-030.
- No persistent production gateway runtime is documented as installed by NODE-030.

## Secrets Policy Summary

- Never commit `.env` files, gateway tokens, OpenAI keys, GitHub tokens, Notion tokens, SSH private keys, passwords, or raw runtime secrets.
- Keep `OPENAI_API_KEY` gateway-side only.
- Asterisk-side gateway auth may use only gateway URL/token from secret runtime config.
- Redact tokens and transcript text in docs, logs, and reports by default.
- Do not log `Bearer ...`, `sk-...`, `ghp_...`, `github_pat_...`, `ntn_...`, or other real tokens.
- Do not stage or commit `data/storage/` or `node014-server.tar`.

## Read First

Read these master docs first:

1. `docs/master/MASTER_STATUS.md`
2. `docs/master/MASTER_PLAN.md`
3. `docs/master/DECISIONS.md`
4. `docs/master/NODE_REGISTRY.md`
5. `docs/master/RUNTIME_NOTES.md`
6. `docs/master/CHAT_BOOTSTRAP.md`

Read this latest node doc first:

- `docs/nodes/NODE-030-controlled-russian-speech-wav-gateway-transcript-smoke.md`

Then read the active node doc for the current scoped task.

## Control Plane Workflow Summary

Future AI-secrenar work should be coordinated through Control Plane with explicit scoped nodes. The expected flow is:

1. GPTChat coordinator discussion.
2. Notion node creation/update.
3. `docs/nodes` node file.
4. Codex handoff.
5. `git switch master`.
6. `git pull --ff-only origin master`.
7. `git switch -c feat/node-XXX-...`.
8. Scoped implementation.
9. Validation.
10. Commit.
11. PR.
12. Review.
13. Merge.
14. Control Plane supervised runner closeout/evidence where applicable.
15. No-op verification.
16. Next node.

## Future PR Workflow Rule

Future AI-secrenar nodes should use feature branch plus PR workflow so the Control Plane supervised runner can close nodes and evidence after merge where applicable.

Existing `NODE-001` through `NODE-030` are historical commit-based nodes. Do not retrofit them through the PR-based supervised runner unless a later separate commit-based closeout design is explicitly created.

## How A New GPT Chat Should Continue

1. Start from `C:\Projects\AI-secrenar-with-Asterisk`.
2. Read the master docs listed above.
3. Read the latest completed node doc, currently `NODE-030`.
4. Confirm `master` is current with `origin/master`.
5. Create a new feature branch for the scoped node.
6. Implement only the scoped node.
7. Validate and report exact evidence.
8. Do not create commits, PRs, Notion writes, Runtime records, or Evidence records unless the handoff explicitly asks for them.

## Forbidden Actions Without A Scoped Node

- Source/runtime code changes.
- Server SSH.
- Asterisk restart.
- Gateway start/stop.
- Deploy.
- Env file changes.
- Live smoke.
- Notion writes.
- Runtime or Evidence create/update.
- GitHub writes.
- Scheduler, webhook, or automation loop changes.
- Token logging.
- `.env` commit.
- Staging or committing `data/storage/`.
- Staging or committing `node014-server.tar`.
- Deleting or cleaning historical untracked artifacts.

## AI-Secretary Pause Pointer

AI-secretary is paused. Resume from NODE-032BQ checkpoint and open a separate temporary-enabled-credential-boundary design node before any live work.
