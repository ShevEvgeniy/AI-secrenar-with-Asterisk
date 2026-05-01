# Master Status

## Current State

- Branch: `master`
- Source-of-truth commit: `df69f3222cec78a5f7afe2ef09b413f7ab5f3d83`
- Source-of-truth commit message: `Use stage-specific prompts and transfer after data collection`
- Repository location: `C:\Projects\AI-secrenar-with-Asterisk`
- Master docs initialized: yes.
- Latest completed node branch: `feat/node-003-transcription-integrity-and-fallback-phrases`
- Latest completed node commit: `b5a315cb6fa41dc97c1dfb42cb6891f420ab55ad`

## Confirmed Working

- System sounds prepublish works.
- Publish/playback pipeline works.
- Stage-specific prompts are already in `master`.
- Transfer flow via ARI continue is already in `master`.
- Publish pipeline remains resilient under partial publish failure.
- Publish failures now include explicit classification, including `reason` and `failed_step`.
- `user_transcribed` is no longer sourced from canned placeholder text.
- Transcription is tied to the real downloaded caller audio artifact.
- Transcription artifact identity is traceable through `call_id`, `stage`, `turn_idx`, `audio_path`, `audio_size_bytes`, and `audio_sha256`.
- Stale local turn artifacts are explicitly discarded and logged.
- Fallback media no longer degrades to `demo-congrats`.
- Stage and transfer fallback paths now use controlled meaningful fallback phrases.
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

NODE-003 completed transcription integrity and meaningful fallback phrases:

```text
real caller audio artifact -> traceable transcription metadata -> no fabricated user_transcribed text
```

NODE-004 restored the post-PHONE transfer invariant:

```text
valid PHONE transcript -> phone_digits saved -> transfer phrase -> ARI continue to from-internal,sales_real,1
```

## Validation Notes

- A false negative occurred during live validation because MicroSIP was using the wrong Windows input device.
- Selecting the correct Windows microphone fixed live dialog capture.
- NODE-001 is merged into `master`.
- NODE-002 is merged into `master`.
- NODE-003 is merged into `master`.
- During NODE-002 validation, SSH to `92.118.85.117:22` timed out while publishing `prompt_3` and transfer system sounds.
- Despite the partial publish failure, the listener reached `READY_WAITING_FOR_CALLS`.
- Fallback media was used during the live call for missing `prompt_3` and transfer phrase.
- Transfer still completed successfully to `from-internal,sales_real,1`.

## Resolved Follow-Up Issues

- NODE-003 fixed the integrity problem where runtime logs showed transcribed text that did not match what the caller says they actually spoke.
- If no STT backend is configured, transcription is logged as unavailable instead of fabricated.
- Fallback media now uses controlled meaningful fallback phrases instead of `demo-congrats`.
- NODE-004 prevents the generic reply pipeline from running after successful PHONE capture.

## Next Recommended Step

```text
Run one live smoke with a real STT backend configured.
```

Real live transcription depends on `TELEPHONY_STT_BACKEND` being explicitly configured, for example `openai` or `whisper_api`.
