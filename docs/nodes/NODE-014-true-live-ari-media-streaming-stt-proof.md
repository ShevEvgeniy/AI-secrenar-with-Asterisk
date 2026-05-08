# NODE-014 True Live ARI Media Streaming STT Proof

## Goal

Test live ARI media into streaming STT while the caller is still speaking.

## Context

NODE-013 implemented a feature-flagged Realtime Whisper adapter, metrics, fallback behavior, and tests, but it streams stored WAV artifacts after recording download. That does not prove caller-perceived pause reduction in live calls.

## Planned Scope

- Branch:

```text
feat/node-014-true-live-ari-media-streaming-stt-proof
```

- Feed live ARI media into streaming STT before normal recording completion.
- Measure first partial/delta latency while the caller is still speaking.
- Compare caller-perceived pause against the existing record-download-batch-STT path.
- Preserve existing dialog state machine, required data gates, PHONE safety, transfer targets, after-hours behavior, callback persistence, and SAFE_FINISH contracts.
- Keep feature flags and fallback behavior from NODE-013.

## Out Of Scope

- Production adoption decision.
- Replacing the batch STT path globally.
- Business logic or routing changes.
- PHONE digit-safety weakening.

## Success Criteria

- Live ARI media reaches streaming STT while the caller is still speaking.
- Metrics distinguish true-live streaming from stored-WAV replay.
- The result clearly states whether caller-perceived pause reduction is observed.
- Failure falls back or disables safely without breaking the existing call flow.

## Branch Name

```text
feat/node-014-true-live-ari-media-streaming-stt-proof
```
