"""One-off OpenAI Realtime transcription measurement CLI.

This module is intentionally standalone. It does not import telephony dialog
code and it only reads ``OPENAI_API_KEY`` from the current process environment
when the CLI entrypoint is invoked.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
import wave

import websockets


DEFAULT_REALTIME_TRANSCRIPTION_URL = "wss://api.openai.com/v1/realtime?intent=transcription"
DEFAULT_TRANSCRIPTION_MODEL = "gpt-realtime-whisper"
DEFAULT_LANGUAGE = "ru"
DEFAULT_SAMPLE_RATE = 24000
DEFAULT_CHUNK_MS = 200
DEFAULT_TIMEOUT_SECONDS = 30.0

SECRET_VALUE_REPLACEMENT = "[REDACTED]"
SECRET_KEY_PATTERN = re.compile(r"(api[_-]?key|authorization|bearer|token|secret|password)", re.IGNORECASE)
OPENAI_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9_\-.]+", re.IGNORECASE)


@dataclass(frozen=True)
class RealtimeMeasurementConfig:
    """Safe runtime config for the standalone measurement path."""

    api_key: str
    audio_path: Path
    websocket_url: str = DEFAULT_REALTIME_TRANSCRIPTION_URL
    transcription_model: str = DEFAULT_TRANSCRIPTION_MODEL
    language: str = DEFAULT_LANGUAGE
    sample_rate: int = DEFAULT_SAMPLE_RATE
    chunk_ms: int = DEFAULT_CHUNK_MS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class RealtimeMeasurementResult:
    """Summary of a measurement run without transcript text or secrets."""

    connection_ok: bool
    session_created: bool
    transcript_text_present: bool
    first_delta_ms: int | None
    final_ms: int | None
    chunks_sent: int
    error: str | None = None


def build_session_update(config: RealtimeMeasurementConfig) -> dict[str, Any]:
    """Build the current GA transcription session payload from official docs."""
    return {
        "type": "session.update",
        "session": {
            "type": "transcription",
            "audio": {
                "input": {
                    "format": {
                        "type": "audio/pcm",
                        "rate": config.sample_rate,
                    },
                    "transcription": {
                        "model": config.transcription_model,
                        "language": config.language,
                    },
                    "turn_detection": None,
                    "noise_reduction": None,
                }
            },
        },
    }


def redact_secrets(value: Any) -> Any:
    """Recursively redact likely secrets from loggable data."""
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                redacted[key] = SECRET_VALUE_REPLACEMENT
            else:
                redacted[key] = redact_secrets(item)
        return redacted
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    if isinstance(value, str):
        return BEARER_PATTERN.sub(f"Bearer {SECRET_VALUE_REPLACEMENT}", OPENAI_KEY_PATTERN.sub(SECRET_VALUE_REPLACEMENT, value))
    return value


def emit_event(
    action: str,
    details: dict[str, Any] | None = None,
    *,
    status: str = "ok",
    reason: str | None = None,
    writer: Callable[[str], None] | None = None,
) -> None:
    """Write a single redacted JSON measurement event."""
    payload = {
        "action": action,
        "status": status,
        "details": redact_secrets(details or {}),
    }
    if reason:
        payload["reason"] = reason
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    if writer is None:
        print(line, flush=True)
    else:
        writer(line)


async def _ws_connect(url: str, headers: dict[str, str]) -> Any:
    try:
        return await websockets.connect(url, additional_headers=headers)
    except TypeError:
        return await websockets.connect(url, extra_headers=headers)


async def run_realtime_measurement(
    config: RealtimeMeasurementConfig,
    *,
    connector: Callable[[str, dict[str, str]], Awaitable[Any]] | None = None,
    writer: Callable[[str], None] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> RealtimeMeasurementResult:
    """Run the one-off Realtime transcription measurement."""
    if not config.api_key:
        emit_event(
            "realtime_error",
            {"error_type": "missing_openai_api_key", "env": "OPENAI_API_KEY"},
            status="fail",
            reason="missing_openai_api_key",
            writer=writer,
        )
        emit_event("realtime_cleanup_done", {"cleanup": "no_connection"}, writer=writer)
        return RealtimeMeasurementResult(False, False, False, None, None, 0, "missing_openai_api_key")

    connector = connector or _ws_connect
    headers = {"Authorization": f"Bearer {config.api_key}"}
    started = clock()
    first_delta_ms: int | None = None
    final_ms: int | None = None
    chunks: list[bytes] = []
    total_audio_ms = 0
    chunks_sent = 0
    transcript_text_present = False
    session_created = False

    try:
        chunks, total_audio_ms = read_pcm_wav_chunks(config.audio_path, config.sample_rate, config.chunk_ms)
        emit_event(
            "realtime_connection_attempt",
            {
                "websocket_host": _safe_ws_target(config.websocket_url),
                "model": config.transcription_model,
                "language": config.language,
                "sample_rate": config.sample_rate,
                "total_audio_ms": total_audio_ms,
            },
            status="start",
            writer=writer,
        )
        async with await connector(config.websocket_url, headers) as ws:
            emit_event("realtime_connection_ok", {"websocket_host": _safe_ws_target(config.websocket_url)}, writer=writer)
            await _wait_for_session_created(ws, writer=writer)
            session_created = True
            emit_event("realtime_session_created", {"session_event_received": True}, writer=writer)
            await ws.send(json.dumps(build_session_update(config)))
            await _wait_for_session_updated(ws, writer=writer)

            emit_event(
                "realtime_audio_send_started",
                {
                    "chunk_ms": config.chunk_ms,
                    "chunk_count": len(chunks),
                    "total_audio_ms": total_audio_ms,
                },
                status="start",
                writer=writer,
            )
            for chunk in chunks:
                await ws.send(
                    json.dumps(
                        {
                            "type": "input_audio_buffer.append",
                            "audio": base64.b64encode(chunk).decode("ascii"),
                        }
                    )
                )
                chunks_sent += 1
                await asyncio.sleep(0)
            await ws.send(json.dumps({"type": "input_audio_buffer.commit"}))

            deadline = clock() + config.timeout_seconds
            while clock() < deadline:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=max(0.1, deadline - clock()))
                except asyncio.TimeoutError:
                    break
                payload = json.loads(message)
                event_type = payload.get("type")
                if event_type == "conversation.item.input_audio_transcription.delta":
                    delta = str(payload.get("delta") or "")
                    if delta:
                        transcript_text_present = True
                        if first_delta_ms is None:
                            first_delta_ms = int((clock() - started) * 1000)
                            emit_event("realtime_first_delta_ms", {"first_delta_ms": first_delta_ms}, writer=writer)
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = str(payload.get("transcript") or "").strip()
                    transcript_text_present = transcript_text_present or bool(transcript)
                    final_ms = int((clock() - started) * 1000)
                    emit_event("realtime_final_ms", {"final_ms": final_ms}, writer=writer)
                    break
                elif event_type == "error":
                    raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
            if final_ms is None:
                raise TimeoutError("realtime transcription final event was not received")
            emit_event(
                "realtime_transcript_text_present",
                {"present": transcript_text_present},
                status="ok" if transcript_text_present else "handled",
                reason=None if transcript_text_present else "empty_transcript",
                writer=writer,
            )
            return RealtimeMeasurementResult(
                True,
                session_created,
                transcript_text_present,
                first_delta_ms,
                final_ms,
                chunks_sent,
                None,
            )
    except Exception as exc:
        emit_event(
            "realtime_connection_failed" if not session_created else "realtime_error",
            {"error_type": type(exc).__name__, "error": repr(exc)},
            status="fail",
            reason=_error_reason(exc),
            writer=writer,
        )
        return RealtimeMeasurementResult(False, session_created, transcript_text_present, first_delta_ms, final_ms, chunks_sent, _error_reason(exc))
    finally:
        emit_event("realtime_cleanup_done", {"chunks_sent": chunks_sent}, writer=writer)


def read_pcm_wav_chunks(path: Path, sample_rate: int, chunk_ms: int) -> tuple[list[bytes], int]:
    """Read a server-local mono 16-bit PCM WAV into chunks accepted by Realtime."""
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        frame_rate = handle.getframerate()
        frame_count = handle.getnframes()
        if channels != 1 or sample_width != 2 or frame_rate != sample_rate:
            raise ValueError(
                "measurement WAV must be mono 16-bit PCM at "
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


async def _wait_for_session_created(ws: Any, *, writer: Callable[[str], None] | None) -> None:
    payload = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    event_type = payload.get("type")
    if event_type in {"session.created", "transcription_session.created"}:
        return
    if event_type == "error":
        raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
    raise RuntimeError(f"unexpected realtime session create response: {event_type}")


async def _wait_for_session_updated(ws: Any, *, writer: Callable[[str], None] | None) -> None:
    _ = writer
    payload = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    event_type = payload.get("type")
    if event_type in {"session.updated", "transcription_session.updated"}:
        return
    if event_type == "error":
        raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
    raise RuntimeError(f"unexpected realtime session update response: {event_type}")


def config_from_args_and_env(argv: list[str] | None = None, environ: dict[str, str] | None = None) -> RealtimeMeasurementConfig:
    """Build config, reading OPENAI_API_KEY from process env only."""
    parser = argparse.ArgumentParser(description="Measure OpenAI Realtime transcription egress/STT from a WAV file.")
    parser.add_argument("--audio", required=True, type=Path, help="Server-local mono 16-bit PCM WAV at 24000 Hz.")
    parser.add_argument("--url", default=DEFAULT_REALTIME_TRANSCRIPTION_URL)
    parser.add_argument("--model", default=DEFAULT_TRANSCRIPTION_MODEL)
    parser.add_argument("--language", default=DEFAULT_LANGUAGE)
    parser.add_argument("--sample-rate", type=int, default=DEFAULT_SAMPLE_RATE)
    parser.add_argument("--chunk-ms", type=int, default=DEFAULT_CHUNK_MS)
    parser.add_argument("--timeout-seconds", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args(argv)
    env = environ if environ is not None else os.environ
    return RealtimeMeasurementConfig(
        api_key=env.get("OPENAI_API_KEY", ""),
        audio_path=args.audio,
        websocket_url=args.url,
        transcription_model=args.model,
        language=args.language,
        sample_rate=args.sample_rate,
        chunk_ms=args.chunk_ms,
        timeout_seconds=args.timeout_seconds,
    )


def _safe_ws_target(url: str) -> str:
    return url.replace("wss://", "").split("?", 1)[0]


def _error_reason(exc: Exception) -> str:
    text = repr(exc).lower()
    if isinstance(exc, TimeoutError) or isinstance(exc, asyncio.TimeoutError):
        return "openai_realtime_timeout"
    if "api key" in text or "invalid_api_key" in text:
        return "openai_realtime_invalid_api_key"
    if "connection" in text:
        return "openai_realtime_connection_error"
    return "openai_realtime_error"


def main(argv: list[str] | None = None) -> int:
    config = config_from_args_and_env(argv)
    result = asyncio.run(run_realtime_measurement(config))
    return 0 if result.error is None else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
