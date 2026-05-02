"""Whisper API client wrapper."""

from __future__ import annotations

import httpx


class WhisperAPIClient:
    """Client for remote Whisper-based STT."""

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-1",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        *,
        language: str | None = None,
        prompt: str | None = None,
    ) -> str:
        """Transcribe audio bytes to text."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required for Whisper transcription")
        data = {"model": self.model}
        if language:
            data["language"] = language
        if prompt:
            data["prompt"] = prompt
        response = httpx.post(
            f"{self.base_url}/audio/transcriptions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            data=data,
            files={"file": (filename, audio_bytes, "audio/wav")},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("text")
        return text.strip() if isinstance(text, str) else ""
