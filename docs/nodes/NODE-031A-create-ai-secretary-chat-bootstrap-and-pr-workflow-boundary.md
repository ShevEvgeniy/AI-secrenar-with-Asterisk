# NODE-031A Create AI Secretary Chat Bootstrap And PR Workflow Boundary

## Status

OPEN as docs-only bootstrap and workflow boundary.

NODE-031A creates a reusable chat bootstrap for future AI-secrenar work and records the transition boundary from historical commit-based node work to future feature-branch plus PR workflow.

This node is docs-only. It does not implement `NODE-031 / productionize-gateway-runtime-boundary`.

## Goal

Create a stable onboarding document for new GPT chats and future Control Plane closeout, while preserving the historical record for `NODE-001` through `NODE-030`.

Required outcomes:

- Add `docs/master/CHAT_BOOTSTRAP.md`.
- Record project identity, local path, GitHub repo, default branch, latest known commit, latest completed node, and next planned technical node.
- Document safe runtime assumptions, non-secret server inventory, secrets policy, first-read docs, latest node doc, and forbidden actions without a scoped node.
- Document the future Control Plane PR workflow.
- Document that historical `NODE-001` through `NODE-030` remain commit-based and should not be retrofitted into PR-based supervised runner closeout unless a separate closeout design is created.

## Scope

Allowed:

- Documentation-only changes under `docs/master/` and `docs/nodes/`.
- Master-doc pointers to the new bootstrap and workflow boundary.

Forbidden:

- Source/runtime code changes.
- Server SSH.
- Asterisk restart.
- Gateway start/stop.
- Deploy.
- Env file changes.
- Live smoke.
- Notion writes.
- Runtime or Evidence create/update.
- GitHub writes except a later branch push if explicitly approved.
- Scheduler, webhook, or automation loop changes.
- Token logging.
- `.env` commit.
- Staging or committing `data/storage/`.
- Staging or committing `node014-server.tar`.
- Deleting or cleaning historical untracked artifacts.

## Baseline

Confirmed onboarding context:

```text
repo=ShevEvgeniy/AI-secrenar-with-Asterisk
local_path=C:\Projects\AI-secrenar-with-Asterisk
default_branch=master
latest_known_commit=901b5a4
latest_completed_node=NODE-030 / controlled-russian-speech-wav-gateway-transcript-smoke
current_planned_next_technical_node=NODE-031 / productionize-gateway-runtime-boundary
docs_master_exists=true
docs_nodes_exists=true
node_docs_present=NODE-001 through NODE-030
historical_workflow=commit-based
future_workflow=feature-branch-plus-PR
```

Known local untracked artifacts that must remain untouched:

```text
data/storage/
node014-server.tar
```

## Bootstrap Content Added

`docs/master/CHAT_BOOTSTRAP.md` records:

- project name;
- local path;
- GitHub repo;
- default branch;
- latest known commit;
- latest completed node;
- current planned next technical node;
- current safe runtime assumptions;
- non-secret server inventory summary;
- secrets policy summary;
- docs/master files to read first;
- latest docs/nodes file to read first;
- Control Plane workflow summary;
- future PR workflow rule;
- how a new GPT chat should continue;
- forbidden actions without a scoped node.

## Workflow Boundary

Future AI-secrenar nodes should use:

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

## Historical Boundary

Existing `NODE-001` through `NODE-030` are historical commit-based nodes.

They should not be retrofitted through the PR-based supervised runner unless a later separate commit-based closeout design is explicitly created.

## NODE-031 Boundary

The expected next technical node is:

```text
NODE-031 / productionize-gateway-runtime-boundary
```

NODE-031A does not implement NODE-031. Production gateway runtime work, TLS, systemd, firewall hardening, token rotation, deployment changes, gateway start/stop, live smoke, and runtime enablement remain out of scope.

## Validation Plan

Run:

```text
git status --short
python -m pytest
git diff --check
git grep -n -E "secret_[A-Za-z0-9]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|ntn_[A-Za-z0-9]+|Bearer [A-Za-z0-9._-]{12,}|sk-[A-Za-z0-9_-]{20,}" -- .
git status --short
```

If available, run whole-tree token and known local DB/token pattern scans without logging secret values.

## Expected Result

```text
node_status=implemented_docs_only_pending_commit
source_runtime_code_changed=false
server_action_performed=false
notion_write_performed=false
runtime_evidence_created=false
github_write_performed=false
scheduler_webhook_automation_added=false
secrets_or_real_tokens_committed=false
data_storage_staged=false
node014_server_tar_staged=false
```
