"""STT router for selecting a backend."""

from __future__ import annotations

from typing import Protocol


class STTBackend(Protocol):
    """Protocol for STT backends."""

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio bytes to text."""
        ...


class STTRouter:
    """Routes STT requests to the selected backend."""

    def __init__(self, backend: STTBackend) -> None:
        self._backend = backend

    def transcribe(self, audio_bytes: bytes) -> str:
        """Transcribe audio using the configured backend."""
        return self._backend.transcribe(audio_bytes)
