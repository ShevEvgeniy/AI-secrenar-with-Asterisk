"""Whisper API client wrapper."""

from __future__ import annotations


class WhisperAPIClient:
    """Client for remote Whisper-based STT."""

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text (placeholder)."""
        _ = audio_bytes
        return ""
