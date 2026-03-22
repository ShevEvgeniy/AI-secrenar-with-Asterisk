"""Local Silero TTS wrapper."""

from __future__ import annotations

import io
import os
import threading
import wave
from typing import Any

import numpy as np
import torch


_MODEL_CACHE: tuple[Any, str] | None = None
_MODEL_LOCK = threading.Lock()


def _env_sample_rate() -> int:
    raw = os.getenv("SILERO_SAMPLE_RATE", "48000").strip()
    try:
        value = int(raw)
    except ValueError:
        value = 48000
    return value if value > 0 else 48000


def _load_model(language: str, speaker_model: str) -> tuple[Any, str]:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    with _MODEL_LOCK:
        if _MODEL_CACHE is not None:
            return _MODEL_CACHE
        torch_home = os.getenv("TORCH_HOME", "").strip()
        if torch_home:
            os.environ["TORCH_HOME"] = torch_home
        model, example_text = torch.hub.load(
            "snakers4/silero-models",
            "silero_tts",
            language=language,
            speaker=speaker_model,
            trust_repo=True,
        )
        _MODEL_CACHE = (model, example_text)
        return _MODEL_CACHE


def _to_float_numpy(audio: Any) -> np.ndarray:
    if torch.is_tensor(audio):
        arr = audio.detach().cpu().numpy()
    else:
        arr = np.asarray(audio)

    arr = np.asarray(arr, dtype=np.float32).reshape(-1)
    if arr.size == 0:
        return np.zeros(1, dtype=np.float32)
    return np.clip(arr, -1.0, 1.0)


def _wav_bytes_from_float_mono(audio: np.ndarray, sample_rate: int) -> bytes:
    pcm = (audio * 32767.0).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return buf.getvalue()


class SileroTTS:
    """Local TTS model interface."""

    def __init__(self, sample_rate: int | None = None) -> None:
        self.language = os.getenv("SILERO_LANGUAGE", "ru").strip() or "ru"
        self.speaker_model = os.getenv("SILERO_SPEAKER_MODEL", "v4_ru").strip() or "v4_ru"
        self.sample_rate = sample_rate if sample_rate is not None else _env_sample_rate()
        self.speaker_name = os.getenv("SILERO_SPEAKER_NAME", "").strip() or None

    def synthesize(self, text: str) -> bytes:
        """Synthesize speech and return WAV bytes."""
        model, _ = _load_model(self.language, self.speaker_model)
        kwargs: dict[str, Any] = {
            "text": text,
            "sample_rate": self.sample_rate,
            "put_accent": True,
            "put_yo": True,
        }
        if self.speaker_name:
            kwargs["speaker"] = self.speaker_name

        audio = model.apply_tts(**kwargs)
        audio_np = _to_float_numpy(audio)
        return _wav_bytes_from_float_mono(audio_np, self.sample_rate)


def _reset_silero_cache_for_tests() -> None:
    """Reset module cache for tests."""
    global _MODEL_CACHE
    with _MODEL_LOCK:
        _MODEL_CACHE = None
