"""Experimental OpenAI Realtime transcription adapter.

This is intentionally a narrow spike adapter. It streams a stored WAV artifact
as chunked audio so the call flow can compare first-delta/final latency
against the existing batch Whisper path without replacing dialog decisions.
"""

from __future__ import annotations

import asyncio
import base64
from collections.abc import Awaitable, Callable
from collections.abc import AsyncIterable
from dataclasses import dataclass, field
import json
from pathlib import Path
import time
from typing import Any
import wave

import websockets


DEFAULT_REALTIME_SESSION_MODEL = "gpt-realtime"
DEFAULT_REALTIME_BASE_URL = "wss://api.openai.com/v1/realtime?intent=transcription"


@dataclass(frozen=True)
class RealtimeTranscriptionConfig:
    """Runtime config for the experimental realtime transcription path."""

    api_key: str
    transcription_model: str = "gpt-realtime-whisper"
    session_model: str = DEFAULT_REALTIME_SESSION_MODEL
    language: str = "ru"
    sample_rate: int = 24000
    base_url: str = DEFAULT_REALTIME_BASE_URL
    chunk_ms: int = 200
    timeout_seconds: float = 30.0
    prompt: str | None = None
    api_mode: str = "ga"

    @property
    def websocket_url(self) -> str:
        if "intent=transcription" in self.base_url:
            return self.base_url
        separator = "&" if "?" in self.base_url else "?"
        return f"{self.base_url}{separator}intent=transcription"


@dataclass(frozen=True)
class RealtimeTranscriptionResult:
    """Transcription result plus latency metrics emitted by the realtime path."""

    text: str
    first_delta_ms: int | None
    final_ms: int | None
    total_audio_ms: int
    chunks_sent: int
    deltas: list[str] = field(default_factory=list)
    model: str = ""
    language: str = ""

    def details(self) -> dict[str, Any]:
        return {
            "stt_stream_text": self.text,
            "stt_stream_latency_first_delta_ms": self.first_delta_ms,
            "stt_stream_latency_final_ms": self.final_ms,
            "stt_stream_total_audio_ms": self.total_audio_ms,
            "stt_stream_audio_chunks_sent": self.chunks_sent,
            "stt_stream_delta_count": len(self.deltas),
            "stt_stream_model": self.model,
            "stt_stream_language": self.language,
        }


async def _ws_connect(url: str, headers: dict[str, str]):
    try:
        return await websockets.connect(url, additional_headers=headers)
    except TypeError:
        return await websockets.connect(url, extra_headers=headers)


async def _aiter_chunks(chunks: AsyncIterable[bytes] | list[bytes]) -> AsyncIterable[bytes]:
    if hasattr(chunks, "__aiter__"):
        async for chunk in chunks:  # type: ignore[union-attr]
            yield chunk
        return
    for chunk in chunks:
        yield chunk


class RealtimeWhisperAdapter:
    """Streams a WAV artifact to OpenAI Realtime transcription over WebSocket."""

    def __init__(
        self,
        config: RealtimeTranscriptionConfig,
        *,
        connector: Callable[[str, dict[str, str]], Awaitable[Any]] | None = None,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self.config = config
        self._connector = connector or _ws_connect
        self._clock = clock

    async def transcribe_wav_file(
        self,
        path: Path,
        *,
        on_metric: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> RealtimeTranscriptionResult:
        """Stream a WAV file and return the final transcript and latency details."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required for realtime transcription")

        chunks, total_audio_ms = _read_pcm_chunks(path, self.config.sample_rate, self.config.chunk_ms)
        return await self.transcribe_pcm_chunks(
            chunks,
            total_audio_ms=total_audio_ms,
            on_metric=on_metric,
        )

    async def transcribe_pcm_chunks(
        self,
        chunks: AsyncIterable[bytes] | list[bytes],
        *,
        total_audio_ms: int = 0,
        on_metric: Callable[[str, dict[str, Any]], None] | None = None,
    ) -> RealtimeTranscriptionResult:
        """Stream already-live mono 16-bit PCM chunks and return transcription details."""
        if not self.config.api_key:
            raise ValueError("OpenAI API key is required for realtime transcription")

        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        if self.config.api_mode != "ga":
            headers["OpenAI-Beta"] = "realtime=v1"
        started = self._clock()
        first_delta_ms: int | None = None
        final_ms: int | None = None
        deltas: list[str] = []
        final_text = ""
        chunks_sent = 0

        on_metric = on_metric or (lambda _name, _details: None)
        on_metric(
            "stt_stream_session_started",
            {
                "stt_stream_provider": "openai_realtime_whisper",
                "stt_stream_model": self.config.transcription_model,
                "stt_stream_language": self.config.language,
                "stt_stream_sample_rate": self.config.sample_rate,
                "stt_stream_total_audio_ms": total_audio_ms,
            },
        )
        on_metric(
            "stt_stream_openai_api_selected",
            {
                "stt_stream_openai_api_mode": self.config.api_mode,
                "stt_stream_openai_ws_path": self.config.websocket_url.split("api.openai.com", 1)[-1],
                "stt_stream_openai_model_selected": self.config.transcription_model,
            },
        )

        async with await self._connector(self.config.websocket_url, headers) as ws:
            await _wait_for_session_created(ws, on_metric)
            session_config = _session_update(self.config)
            await ws.send(json.dumps(session_config))
            on_metric(
                "stt_stream_openai_session_config_sent",
                {
                    "stt_stream_model": self.config.transcription_model,
                    "stt_stream_language": self.config.language,
                    "stt_stream_sample_rate": self.config.sample_rate,
                    "event_type": session_config["type"],
                },
            )
            await _wait_for_session_config_ack(ws, on_metric)
            async for chunk in _aiter_chunks(chunks):
                await ws.send(
                    json.dumps(
                        {
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(chunk).decode("ascii"),
                        }
                    )
                )
                chunks_sent += 1
                on_metric(
                    "stt_stream_audio_chunk_sent",
                    {
                        "chunk_index": chunks_sent,
                        "chunk_bytes": len(chunk),
                        "stt_stream_total_audio_ms": total_audio_ms,
                    },
                )
                on_metric(
                    "stt_stream_openai_audio_chunk_sent",
                    {
                        "chunk_index": chunks_sent,
                        "chunk_bytes": len(chunk),
                    },
                )
                await asyncio.sleep(0)
            on_metric(
                "stt_stream_openai_audio_chunks_sent_count",
                {
                    "stt_stream_openai_audio_chunks_sent_count": chunks_sent,
                    "stt_stream_total_audio_ms": total_audio_ms,
                },
            )
            if chunks_sent == 0:
                on_metric(
                    "stt_stream_openai_no_audio_received",
                    {"stt_stream_openai_audio_chunks_sent_count": 0},
                )
                return RealtimeTranscriptionResult(
                    text="",
                    first_delta_ms=None,
                    final_ms=None,
                    total_audio_ms=total_audio_ms,
                    chunks_sent=0,
                    deltas=[],
                    model=self.config.transcription_model,
                    language=self.config.language,
                )
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

            deadline = self._clock() + self.config.timeout_seconds
            while self._clock() < deadline:
                timeout = max(0.1, deadline - self._clock())
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=timeout)
                except asyncio.TimeoutError:
                    break
                payload = json.loads(message)
                event_type = payload.get("type")
                if event_type == "conversation.item.input_audio_transcription.delta":
                    delta = str(payload.get("delta") or "")
                    if not delta:
                        continue
                    deltas.append(delta)
                    if first_delta_ms is None:
                        first_delta_ms = int((self._clock() - started) * 1000)
                        on_metric(
                            "stt_stream_first_delta_received",
                            {
                                "stt_stream_latency_first_delta_ms": first_delta_ms,
                                "stt_stream_text": delta,
                            },
                        )
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    final_text = str(payload.get("transcript") or "").strip()
                    final_ms = int((self._clock() - started) * 1000)
                    on_metric(
                        "stt_stream_final_received",
                        {
                            "stt_stream_latency_final_ms": final_ms,
                            "stt_stream_text": final_text,
                        },
                    )
                    break
                elif event_type == "error":
                    raise RuntimeError(json.dumps(payload, ensure_ascii=False))
            if not final_text:
                on_metric(
                    "stt_stream_openai_no_delta_received",
                    {"stt_stream_openai_audio_chunks_sent_count": chunks_sent},
                )
                raise TimeoutError("realtime transcription timed out")

        if not final_text:
            final_text = "".join(deltas).strip()
        if chunks_sent > 0 and not deltas and not final_text:
            on_metric(
                "stt_stream_openai_no_delta_received",
                {"stt_stream_openai_audio_chunks_sent_count": chunks_sent},
            )
        return RealtimeTranscriptionResult(
            text=final_text,
            first_delta_ms=first_delta_ms,
            final_ms=final_ms,
            total_audio_ms=total_audio_ms,
            chunks_sent=chunks_sent,
            deltas=deltas,
            model=self.config.transcription_model,
            language=self.config.language,
        )


def _session_update(config: RealtimeTranscriptionConfig) -> dict[str, Any]:
    transcription: dict[str, Any] = {
        "model": config.transcription_model,
        "language": config.language,
    }
    if config.prompt:
        transcription["prompt"] = config.prompt
    if config.api_mode == "ga":
        return {
            "type": "session.update",
            "session": {
                "audio": {
                    "input": {
                        "format": {
                            "type": "audio/pcm",
                            "rate": config.sample_rate,
                        },
                        "transcription": transcription,
                        "turn_detection": None,
                        "noise_reduction": None,
                    }
                },
            },
        }
    return {
        "type": "transcription_session.update",
        "session": {
            "input_audio_format": "pcm16",
            "input_audio_transcription": transcription,
            "turn_detection": None,
            "input_audio_noise_reduction": None,
        },
    }


async def _wait_for_session_config_ack(
    ws: Any,
    on_metric: Callable[[str, dict[str, Any]], None],
) -> None:
    try:
        message = await asyncio.wait_for(ws.recv(), timeout=10)
    except asyncio.TimeoutError:
        on_metric(
            "stt_stream_openai_session_config_failed",
            {"reason": "session_config_timeout"},
        )
        raise
    payload = json.loads(message)
    event_type = payload.get("type")
    if event_type in {"transcription_session.updated", "session.updated"}:
        on_metric(
            "stt_stream_openai_session_config_ok",
            {"event_type": event_type},
        )
        return
    if event_type == "error":
        on_metric(
            "stt_stream_openai_session_config_failed",
            {
                "event_type": event_type,
                "error": payload.get("error"),
            },
        )
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    on_metric(
        "stt_stream_openai_session_config_failed",
        {"event_type": event_type, "payload": payload},
    )
    raise RuntimeError(f"unexpected realtime session config response: {event_type}")


async def _wait_for_session_created(
    ws: Any,
    on_metric: Callable[[str, dict[str, Any]], None],
) -> None:
    try:
        message = await asyncio.wait_for(ws.recv(), timeout=10)
    except asyncio.TimeoutError:
        on_metric(
            "stt_stream_openai_session_config_failed",
            {"reason": "session_create_timeout"},
        )
        raise
    payload = json.loads(message)
    event_type = payload.get("type")
    if event_type in {"transcription_session.created", "session.created"}:
        on_metric(
            "stt_stream_openai_session_created",
            {"event_type": event_type},
        )
        return
    if event_type == "error":
        on_metric(
            "stt_stream_openai_session_config_failed",
            {"event_type": event_type, "error": payload.get("error")},
        )
        raise RuntimeError(json.dumps(payload, ensure_ascii=False))
    on_metric(
        "stt_stream_openai_session_config_failed",
        {"event_type": event_type, "payload": payload},
    )
    raise RuntimeError(f"unexpected realtime session create response: {event_type}")


def _read_pcm_chunks(path: Path, sample_rate: int, chunk_ms: int) -> tuple[list[bytes], int]:
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        frame_rate = handle.getframerate()
        frame_count = handle.getnframes()
        if channels != 1 or sample_width != 2 or frame_rate != sample_rate:
            raise ValueError(
                "realtime spike requires mono 16-bit PCM WAV at "
                f"{sample_rate} Hz; got channels={channels}, sample_width={sample_width}, rate={frame_rate}"
            )
        frames_per_chunk = max(1, int(frame_rate * chunk_ms / 1000))
        chunks: list[bytes] = []
        while True:
            data = handle.readframes(frames_per_chunk)
            if not data:
                break
            chunks.append(data)
    total_audio_ms = int(frame_count / sample_rate * 1000) if sample_rate else 0
    return chunks, total_audio_ms
