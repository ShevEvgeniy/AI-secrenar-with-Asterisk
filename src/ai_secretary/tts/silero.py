"""Local Silero TTS wrapper."""

from __future__ import annotations

import io
import math
import wave


class SileroTTS:
    """Local TTS model interface."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate

    def synthesize(self, text: str) -> bytes:
        """Synthesize speech as a simple WAV placeholder."""
        duration = max(1.0, min(6.0, 0.5 + 0.08 * len(text.split())))
        freq = 440.0
        frames = int(self.sample_rate * duration)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            for i in range(frames):
                sample = int(32767 * math.sin(2 * math.pi * freq * i / self.sample_rate))
                wav.writeframesraw(sample.to_bytes(2, byteorder="little", signed=True))
        return buf.getvalue()
