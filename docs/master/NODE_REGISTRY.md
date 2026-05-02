# Node Registry

## Workflow Rules

- One node equals one task, one branch, and one execution cycle.
- Node branches should be focused and implementation-specific.
- `master` remains the source of truth for planning, coordination, architecture, and status.
- Node docs live under `docs/nodes/`.
- Master docs live under `docs/master/`.

## Registered Nodes

| Node | Node Doc | Branch | Status | Purpose | Result |
| --- | --- | --- | --- | --- | --- |
| `NODE-001-sales-real-transfer` | `docs/nodes/NODE-001-sales-real-transfer.md` | `feat/node-001-sales-real-transfer` | Done, merged | Implement and validate the real transfer route `sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144`. | Live smoke passed at `598843d0fc00caa40c935f39dec123acc1b7a6c4`; merged into `master` via `e5d1cb6892a2319fb6ebbc05e52ec2d06f98e0fd`. |
| `NODE-002-publish-hardening` | `docs/nodes/NODE-002-publish-hardening.md` | `feat/node-002-publish-hardening` | Done, merged | Harden publish failure handling so startup and per-call publish failures are resilient and diagnosable. | Validated at `4d0022f0187b866015cca2c4d921a4f109e512a5`; merged into `master`. |
| `NODE-003-transcription-integrity-and-meaningful-fallback-phrases` | `docs/nodes/NODE-003-transcription-integrity-and-meaningful-fallback-phrases.md` | `feat/node-003-transcription-integrity-and-fallback-phrases` | Done, merged | Fix transcription integrity and replace non-meaningful fallback media behavior surfaced by NODE-002. | Validated at `b5a315cb6fa41dc97c1dfb42cb6891f420ab55ad`; merged into `master`. |
| `NODE-004-restore-post-phone-transfer-flow` | `docs/nodes/NODE-004-restore-post-phone-transfer-flow.md` | `feat/node-004-restore-post-phone-transfer-flow` | Done, merged | Restore the post-PHONE invariant so successful PHONE capture immediately plays the transfer phrase and continues to `sales_real`. | Validated at `8ec82c5790cc513a9d5428abb75a90dbce9b5420`; live smoke `1777641576.42` confirmed `play_transfer_phrase -> transfer status=ok` and no generic reply pipeline after PHONE. |
| `NODE-005-latency-and-turn-based-hardening` | `docs/nodes/NODE-005-latency-and-turn-based-hardening.md` | `feat/node-005-latency-and-turn-based-hardening` | Not ready, needs live re-smoke | Reduce perceived latency inside the current turn-based architecture with stage-specific record contours, PHONE-only confirmation, varied PHONE retry prompts, TTS-safe phone confirmation, and explicit latency tracing. | Patch 6 adds PHONE_CONFIRM PlaybackFinished barrier, guard delay, meta-repair handling, NAME guard, and fixed PHONE prompt stress re-render; local regression suite passed, but live validation is still required. |

## Node Completion Requirements

Each completed node must report:

1. Exact files changed.
2. Commit hash.
3. Short result.
4. Validation result.
5. Next recommendation.
