"""Tests for publish ffmpeg skip optimization."""

from __future__ import annotations

import wave
from pathlib import Path

import ai_secretary.storage.publish_to_asterisk as pub


def _write_pcm16_mono_8k(path: Path) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b"\x00\x00" * 80)


def test_ensure_wav_8k_mono_skips_ffmpeg(monkeypatch, tmp_path: Path) -> None:
    in_wav = tmp_path / "in.wav"
    _write_pcm16_mono_8k(in_wav)

    def _fail_run(*args, **kwargs):
        _ = args
        _ = kwargs
        raise AssertionError("ffmpeg should not be called for 8k mono pcm_s16le wav")

    monkeypatch.setattr(pub.subprocess, "run", _fail_run)

    out = pub._ensure_wav_8k_mono(in_wav)
    assert out == in_wav
