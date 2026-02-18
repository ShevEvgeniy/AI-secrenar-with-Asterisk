"""Local NeMo STT wrapper."""

from __future__ import annotations


class NemoLocalSTT:
    """Local STT model interface."""

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text (placeholder)."""
        _ = audio_bytes
        return ""
