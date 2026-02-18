"""TTS router for selecting a backend."""

from __future__ import annotations

from typing import Protocol


class TTSBackend(Protocol):
    """Protocol for TTS backends."""

    def synthesize(self, text: str) -> bytes:
        """Synthesize speech audio."""
        ...


class TTSRouter:
    """Routes TTS requests to the selected backend."""

    def __init__(self, backend: TTSBackend) -> None:
        self._backend = backend

    def synthesize(self, text: str) -> bytes:
        """Synthesize speech using the configured backend."""
        return self._backend.synthesize(text)
