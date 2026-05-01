# Master Status

## Current State

- Branch: `master`
- Source-of-truth commit: `df69f3222cec78a5f7afe2ef09b413f7ab5f3d83`
- Source-of-truth commit message: `Use stage-specific prompts and transfer after data collection`
- Repository location: `C:\Projects\AI-secrenar-with-Asterisk`
- Master docs initialized: yes.
- Latest completed node branch: `feat/node-002-publish-hardening`
- Latest completed node commit: `4d0022f0187b866015cca2c4d921a4f109e512a5`

## Confirmed Working

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are already in `master`.
- Transfer flow via ARI continue is already in `master`.
- Publish pipeline remains resilient under partial publish failure.
- Publish failures now include explicit classification, including `reason` and `failed_step`.
- NODE-001 live smoke validation passed:
  - stage prompts progressed correctly;
  - user speech was transcribed for ISSUE / NAME / CITY / PHONE;
  - transfer phrase played;
  - transfer completed with `status=ok` to `from-internal,sales_real,1`.

## Completed Nodes

NODE-001 completed the real sales transfer route:

```text
sales_real -> PJSIP/78007074193@thermo-trunk-endpoint -> DTMF ww52144
```

NODE-002 completed publish hardening:

```text
publish failures -> explicit reason and failed_step -> resilient startup/per-call diagnostics
```

## Validation Notes

- A false negative occurred during live validation because MicroSIP was using the wrong Windows input device.
- Selecting the correct Windows microphone fixed live dialog capture.
- NODE-001 is merged into `master`.
- NODE-002 is merged into `master`.
- During NODE-002 validation, SSH to `92.118.85.117:22` timed out while publishing `prompt_3` and transfer system sounds.
- Despite the partial publish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- Fallback media was used during the live call for missing `prompt_3` and transfer phrase.
- Transfer still completed successfully to `from-internal,sales_real,1`.

## Open Follow-Up Issues

- Fallback media currently degrades to `demo-congrats`, which is not meaningful UX.
- `user_transcribed` content in runtime logs did not match what the caller says they actually spoke.

## Next Recommended Node

```text
NODE-003 / transcription-integrity-and-meaningful-fallback-phrases
```
