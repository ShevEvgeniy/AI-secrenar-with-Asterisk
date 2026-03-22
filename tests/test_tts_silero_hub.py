"""Tests for Silero torch.hub TTS integration."""

from __future__ import annotations

import numpy as np

from ai_secretary.tts import silero
from ai_secretary.tts.silero import SileroTTS


def test_silero_hub_synthesize_wav_and_cache(monkeypatch) -> None:
    calls = {"count": 0}

    class FakeModel:
        def apply_tts(self, **kwargs):
            _ = kwargs
            return np.array([0.0, 0.1, -0.1, 0.2], dtype=np.float32)

    def fake_load(*args, **kwargs):
        _ = args
        _ = kwargs
        calls["count"] += 1
        return FakeModel(), "example"

    silero._reset_silero_cache_for_tests()
    monkeypatch.setattr(silero.torch.hub, "load", fake_load)

    tts = SileroTTS(sample_rate=48000)
    wav1 = tts.synthesize("Привет")
    wav2 = tts.synthesize("Мир")

    assert wav1.startswith(b"RIFF")
    assert b"WAVE" in wav1
    assert wav2.startswith(b"RIFF")
    assert b"WAVE" in wav2
    assert calls["count"] == 1

    silero._reset_silero_cache_for_tests()
