"""Minimal supported-region gateway for one-off Realtime STT measurement.

This module is intentionally isolated from telephony dialog code. It owns the
gateway-side OpenAI API key and exposes a diagnostic HTTP endpoint only.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
from collections import Counter
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from io import BytesIO
import json
import os
import secrets
import time
from typing import Any
import uuid
import wave

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import JSONResponse

from .realtime_measurement import (
    DEFAULT_CHUNK_MS,
    DEFAULT_LANGUAGE,
    DEFAULT_REALTIME_TRANSCRIPTION_URL,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_TRANSCRIPTION_MODEL,
    RealtimeMeasurementConfig,
    _ws_connect,
    build_session_update,
    diagnose_pcm_wav_audio_bytes,
    redact_secrets,
)


GATEWAY_ENDPOINT = "/v1/stt/realtime-measurement"
MAX_AUDIO_SECONDS = 15
MAX_AUDIO_BYTES = 1_048_576


@dataclass(frozen=True)
class GatewaySettings:
    """Gateway runtime settings loaded on the supported-region host."""

    openai_api_key: str
    gateway_token: str
    gateway_region_label: str = "unknown"
    websocket_url: str = DEFAULT_REALTIME_TRANSCRIPTION_URL
    transcription_model: str = DEFAULT_TRANSCRIPTION_MODEL
    language: str = DEFAULT_LANGUAGE
    sample_rate: int = DEFAULT_SAMPLE_RATE
    chunk_ms: int = DEFAULT_CHUNK_MS
    openai_timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_audio_seconds: int = MAX_AUDIO_SECONDS
    max_audio_bytes: int = MAX_AUDIO_BYTES
    allow_return_transcript: bool = False


def settings_from_env(environ: dict[str, str] | None = None) -> GatewaySettings:
    env = environ if environ is not None else os.environ
    return GatewaySettings(
        openai_api_key=env.get("OPENAI_API_KEY", ""),
        gateway_token=env.get("GATEWAY_TOKEN") or env.get("STT_GATEWAY_SERVER_TOKEN", ""),
        gateway_region_label=env.get("GATEWAY_REGION_LABEL", "unknown"),
        websocket_url=env.get("OPENAI_REALTIME_URL", DEFAULT_REALTIME_TRANSCRIPTION_URL),
        transcription_model=env.get("OPENAI_REALTIME_MODEL", DEFAULT_TRANSCRIPTION_MODEL),
        language=env.get("OPENAI_REALTIME_LANGUAGE", DEFAULT_LANGUAGE),
        openai_timeout_seconds=float(env.get("OPENAI_REALTIME_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))),
        max_audio_seconds=int(env.get("STT_GATEWAY_MAX_AUDIO_SECONDS", str(MAX_AUDIO_SECONDS))),
        max_audio_bytes=int(env.get("STT_GATEWAY_MAX_AUDIO_BYTES", str(MAX_AUDIO_BYTES))),
        allow_return_transcript=env.get("STT_GATEWAY_ALLOW_RETURN_TRANSCRIPT", "false").lower() == "true",
    )


def authorize_gateway_request(authorization: str | None, expected_token: str) -> bool:
    if not expected_token or not authorization:
        return False
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return False
    token = authorization[len(prefix) :].strip()
    return bool(token) and secrets.compare_digest(token, expected_token)


def build_gateway_response(
    *,
    request_id: str,
    settings: GatewaySettings,
    status: int,
    openai_realtime_connection_ok: bool = False,
    openai_session_created: bool = False,
    audio_send_started: bool = False,
    chunks_sent: int = 0,
    first_delta_ms: int | None = None,
    final_ms: int | None = None,
    transcript_text_present: bool = False,
    error_type: str | None = None,
    error_code: str | None = None,
    error_message_redacted: str | None = None,
    cleanup_done: bool = True,
    transcript_text: str | None = None,
    audio_diagnostics: dict[str, Any] | None = None,
    response_diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ok = 200 <= status < 300
    payload: dict[str, Any] = {
        "ok": ok,
        "gateway_request_id": request_id,
        "gateway_connection_attempt": True,
        "gateway_region": settings.gateway_region_label,
        "model": settings.transcription_model,
        "openai_realtime_connection_ok": openai_realtime_connection_ok,
        "openai_session_created": openai_session_created,
        "audio_send_started": audio_send_started,
        "chunks_sent": chunks_sent,
        "first_delta_ms": first_delta_ms,
        "final_ms": final_ms,
        "transcript_text_present": transcript_text_present,
        "error_type": error_type,
        "error_code": error_code,
        "error_message_redacted": str(redact_secrets(error_message_redacted)) if error_message_redacted else None,
        "cleanup_done": cleanup_done,
    }
    if audio_diagnostics is not None:
        payload.update(redact_secrets(audio_diagnostics))
    if response_diagnostics is not None:
        payload.update(redact_secrets(response_diagnostics))
    if transcript_text is not None:
        payload["transcript_text"] = transcript_text
    return redact_secrets(payload)


async def run_gateway_realtime_measurement(
    audio: bytes,
    *,
    settings: GatewaySettings,
    request_id: str | None = None,
    language: str | None = None,
    return_transcript: bool = False,
    connector: Callable[[str, dict[str, str]], Awaitable[Any]] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> tuple[int, dict[str, Any]]:
    """Run gateway-owned OpenAI Realtime transcription and return HTTP status/payload."""
    gateway_request_id = request_id or f"gw_{uuid.uuid4().hex[:12]}"
    if not settings.openai_api_key:
        return 503, build_gateway_response(
            request_id=gateway_request_id,
            settings=settings,
            status=503,
            error_type="gateway_config_error",
            error_code="missing_openai_api_key",
            error_message_redacted="OPENAI_API_KEY is not configured on gateway",
        )
    if len(audio) > settings.max_audio_bytes:
        return 400, build_gateway_response(
            request_id=gateway_request_id,
            settings=settings,
            status=400,
            error_type="gateway_audio_invalid",
            error_code="audio_too_large",
            error_message_redacted=f"audio bytes exceed limit {settings.max_audio_bytes}",
            audio_diagnostics=diagnose_pcm_wav_audio_bytes(
                audio,
                expected_sample_rate=settings.sample_rate,
                chunk_ms=settings.chunk_ms,
            ),
        )

    chunks_sent = 0
    first_delta_ms: int | None = None
    final_ms: int | None = None
    transcript_text_present = False
    openai_realtime_connection_ok = False
    openai_session_created = False
    audio_send_started = False
    transcript_text: str | None = None
    connector = connector or _ws_connect
    started = clock()
    audio_diagnostics = diagnose_pcm_wav_audio_bytes(
        audio,
        expected_sample_rate=settings.sample_rate,
        chunk_ms=settings.chunk_ms,
    )
    event_type_counts: Counter[str] = Counter()
    input_audio_buffer_commit_sent = False
    timeout_observed = False
    response_diagnostics = _build_response_diagnostics(
        event_type_counts,
        input_audio_buffer_commit_sent=input_audio_buffer_commit_sent,
        timeout_observed=timeout_observed,
        transcript_text_present=transcript_text_present,
    )

    try:
        chunks, total_audio_ms = read_pcm_wav_chunks_from_bytes(audio, settings.sample_rate, settings.chunk_ms)
        if total_audio_ms > settings.max_audio_seconds * 1000:
            return 400, build_gateway_response(
                request_id=gateway_request_id,
                settings=settings,
                status=400,
                error_type="gateway_audio_invalid",
                error_code="audio_too_long",
                error_message_redacted=f"audio duration exceeds limit {settings.max_audio_seconds}s",
                audio_diagnostics=audio_diagnostics,
                response_diagnostics=response_diagnostics,
            )

        config = RealtimeMeasurementConfig(
            api_key=settings.openai_api_key,
            audio_path=os.devnull,
            websocket_url=settings.websocket_url,
            transcription_model=settings.transcription_model,
            language=language or settings.language,
            sample_rate=settings.sample_rate,
            chunk_ms=settings.chunk_ms,
            timeout_seconds=settings.openai_timeout_seconds,
        )
        headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
        async with await connector(settings.websocket_url, headers) as ws:
            openai_realtime_connection_ok = True
            await _wait_for_session_created(ws, event_type_counts=event_type_counts)
            openai_session_created = True
            await ws.send(json.dumps(build_session_update(config)))
            await _wait_for_session_updated(ws, event_type_counts=event_type_counts)

            audio_send_started = True
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
            input_audio_buffer_commit_sent = True

            deadline = clock() + settings.openai_timeout_seconds
            while clock() < deadline:
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=max(0.1, deadline - clock()))
                except asyncio.TimeoutError:
                    timeout_observed = True
                    break
                payload = json.loads(message)
                event_type = payload.get("type")
                _record_event_type(event_type_counts, event_type)
                if event_type == "conversation.item.input_audio_transcription.delta":
                    delta = _transcript_text_from_event(payload, event_type=event_type)
                    if delta:
                        transcript_text_present = True
                        if first_delta_ms is None:
                            first_delta_ms = int((clock() - started) * 1000)
                elif event_type == "conversation.item.input_audio_transcription.completed":
                    transcript = _transcript_text_from_event(payload, event_type=event_type)
                    transcript_text_present = transcript_text_present or bool(transcript)
                    final_ms = int((clock() - started) * 1000)
                    if return_transcript and settings.allow_return_transcript:
                        transcript_text = transcript
                    break
                elif event_type == "error":
                    raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
            response_diagnostics = _build_response_diagnostics(
                event_type_counts,
                input_audio_buffer_commit_sent=input_audio_buffer_commit_sent,
                timeout_observed=timeout_observed,
                transcript_text_present=transcript_text_present,
            )
            if final_ms is None:
                raise TimeoutError("realtime transcription final event was not received")
            return 200, build_gateway_response(
                request_id=gateway_request_id,
                settings=settings,
                status=200,
                openai_realtime_connection_ok=openai_realtime_connection_ok,
                openai_session_created=openai_session_created,
                audio_send_started=audio_send_started,
                chunks_sent=chunks_sent,
                first_delta_ms=first_delta_ms,
                final_ms=final_ms,
                transcript_text_present=transcript_text_present,
                transcript_text=transcript_text,
                audio_diagnostics=audio_diagnostics,
                response_diagnostics=response_diagnostics,
            )
    except (ValueError, wave.Error) as exc:
        return 400, build_gateway_response(
            request_id=gateway_request_id,
            settings=settings,
            status=400,
            chunks_sent=chunks_sent,
            error_type="gateway_audio_invalid",
            error_code="invalid_wav",
            error_message_redacted=str(exc),
            audio_diagnostics=audio_diagnostics,
            response_diagnostics=response_diagnostics,
        )
    except Exception as exc:
        error_code = map_openai_error(exc)
        response_diagnostics = _build_response_diagnostics(
            event_type_counts,
            input_audio_buffer_commit_sent=input_audio_buffer_commit_sent,
            timeout_observed=timeout_observed or error_code == "gateway_timeout",
            transcript_text_present=transcript_text_present,
        )
        return 502, build_gateway_response(
            request_id=gateway_request_id,
            settings=settings,
            status=502,
            openai_realtime_connection_ok=openai_realtime_connection_ok,
            openai_session_created=openai_session_created,
            audio_send_started=audio_send_started,
            chunks_sent=chunks_sent,
            first_delta_ms=first_delta_ms,
            final_ms=final_ms,
            transcript_text_present=transcript_text_present,
            error_type=type(exc).__name__,
            error_code=error_code,
            error_message_redacted=repr(exc),
            audio_diagnostics=audio_diagnostics,
            response_diagnostics=response_diagnostics,
        )


def read_pcm_wav_chunks_from_bytes(audio: bytes, sample_rate: int, chunk_ms: int) -> tuple[list[bytes], int]:
    with wave.open(BytesIO(audio), "rb") as handle:
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


def map_openai_error(exc: Exception) -> str:
    text = repr(exc).lower()
    if "unsupported_country_region_territory" in text:
        return "openai_region_rejected"
    if "invalid_api_key" in text or "api key" in text:
        return "openai_auth_failed"
    if "rate" in text or "429" in text:
        return "openai_rate_limited"
    if isinstance(exc, TimeoutError) or isinstance(exc, asyncio.TimeoutError):
        return "gateway_timeout"
    return "openai_transient"


def _record_event_type(event_type_counts: Counter[str], event_type: Any) -> None:
    if isinstance(event_type, str) and event_type:
        event_type_counts[event_type] += 1


def _transcript_text_from_event(payload: dict[str, Any], *, event_type: str) -> str:
    if event_type == "conversation.item.input_audio_transcription.delta":
        return _first_non_empty_string(payload.get("delta"), payload.get("text"))
    if event_type != "conversation.item.input_audio_transcription.completed":
        return ""

    direct = _first_non_empty_string(payload.get("transcript"))
    if direct:
        return direct

    nested_transcript = payload.get("transcript")
    if isinstance(nested_transcript, dict):
        nested_text = _first_non_empty_string(nested_transcript.get("text"), nested_transcript.get("value"))
        if nested_text:
            return nested_text

    item = payload.get("item")
    if isinstance(item, dict):
        item_text = _first_non_empty_string(item.get("transcript"))
        if item_text:
            return item_text
        content_text = _transcript_text_from_content_array(item.get("content"))
        if content_text:
            return content_text

    return _transcript_text_from_content_array(payload.get("content"))


def _transcript_text_from_content_array(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    for entry in value:
        if not isinstance(entry, dict):
            continue
        text = _first_non_empty_string(entry.get("transcript"), entry.get("text"))
        if text:
            return text
    return ""


def _first_non_empty_string(*values: Any) -> str:
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return ""


def _build_response_diagnostics(
    event_type_counts: Counter[str],
    *,
    input_audio_buffer_commit_sent: bool,
    timeout_observed: bool,
    transcript_text_present: bool,
) -> dict[str, Any]:
    event_counts = dict(sorted(event_type_counts.items()))
    event_counts_present = bool(event_counts)
    transcript_event_seen = any(
        event_type.startswith("conversation.item.input_audio_transcription.")
        for event_type in event_type_counts
    )
    transcript_bearing_event_seen = bool(
        event_type_counts.get("conversation.item.input_audio_transcription.delta")
        or event_type_counts.get("conversation.item.input_audio_transcription.completed")
    )
    error_event_seen = bool(event_type_counts.get("error"))
    transcript_text_length_bucket = _transcript_text_length_bucket(
        transcript_text_present=transcript_text_present,
        transcript_bearing_event_seen=transcript_bearing_event_seen,
    )
    return {
        "openai_event_type_counts": event_counts,
        "openai_event_type_counts_available": True,
        "openai_event_type_counts_present": event_counts_present,
        "transcript_event_seen": transcript_event_seen,
        "transcript_bearing_event_seen": transcript_bearing_event_seen,
        "transcript_text_present": transcript_text_present,
        "transcript_text_length_bucket": transcript_text_length_bucket,
        "error_event_seen": error_event_seen,
        "input_audio_buffer_commit_sent": input_audio_buffer_commit_sent,
        "timeout_observed": timeout_observed,
        "diagnostic_propagation_gap": False,
        "diagnostic_classification": _diagnostic_classification(
            event_counts_present=event_counts_present,
            transcript_event_seen=transcript_event_seen,
            transcript_bearing_event_seen=transcript_bearing_event_seen,
            transcript_text_present=transcript_text_present,
            input_audio_buffer_commit_sent=input_audio_buffer_commit_sent,
            timeout_observed=timeout_observed,
            error_event_seen=error_event_seen,
        ),
        "close_status": "not_observed",
    }


def _transcript_text_length_bucket(
    *,
    transcript_text_present: bool,
    transcript_bearing_event_seen: bool,
) -> str:
    if transcript_text_present:
        return "nonzero_redacted"
    if transcript_bearing_event_seen:
        return "zero"
    return "unknown"


def _diagnostic_classification(
    *,
    event_counts_present: bool,
    transcript_event_seen: bool,
    transcript_bearing_event_seen: bool,
    transcript_text_present: bool,
    input_audio_buffer_commit_sent: bool,
    timeout_observed: bool,
    error_event_seen: bool,
) -> str:
    if not event_counts_present:
        return "no_event_counts_available"
    if error_event_seen:
        return "openai_error_event_observed"
    if timeout_observed and input_audio_buffer_commit_sent:
        return "timeout_after_audio_commit"
    if not transcript_event_seen:
        return "no_transcript_event_observed"
    if transcript_bearing_event_seen and transcript_text_present:
        return "transcript_bearing_event_observed_text_redacted"
    if transcript_bearing_event_seen:
        return "transcript_event_observed_empty_or_no_text"
    return "unknown"


async def _wait_for_session_created(ws: Any, *, event_type_counts: Counter[str]) -> None:
    payload = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    event_type = payload.get("type")
    _record_event_type(event_type_counts, event_type)
    if event_type in {"session.created", "transcription_session.created"}:
        return
    if event_type == "error":
        raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
    raise RuntimeError(f"unexpected realtime session create response: {event_type}")


async def _wait_for_session_updated(ws: Any, *, event_type_counts: Counter[str]) -> None:
    payload = json.loads(await asyncio.wait_for(ws.recv(), timeout=10))
    event_type = payload.get("type")
    _record_event_type(event_type_counts, event_type)
    if event_type in {"session.updated", "transcription_session.updated"}:
        return
    if event_type == "error":
        raise RuntimeError(json.dumps(redact_secrets(payload), ensure_ascii=False))
    raise RuntimeError(f"unexpected realtime session update response: {event_type}")


def create_app(settings: GatewaySettings | None = None) -> Any:
    gateway_settings = settings or settings_from_env()
    app = FastAPI(title="AI Secretary OpenAI Realtime STT Gateway")

    @app.post(GATEWAY_ENDPOINT)
    async def realtime_measurement(
        request: Request,
        authorization: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
        language: str | None = Query(default=None),
        return_transcript: bool = Query(default=False),
    ) -> JSONResponse:
        request_id = x_request_id or f"gw_{uuid.uuid4().hex[:12]}"
        if not authorize_gateway_request(authorization, gateway_settings.gateway_token):
            payload = build_gateway_response(
                request_id=request_id,
                settings=gateway_settings,
                status=401,
                error_type="gateway_auth_failed",
                error_code="gateway_auth_failed",
                error_message_redacted="missing or invalid gateway bearer token",
            )
            return JSONResponse(payload, status_code=401)
        audio = await request.body()
        status, payload = await run_gateway_realtime_measurement(
            audio,
            settings=gateway_settings,
            request_id=request_id,
            language=language,
            return_transcript=return_transcript,
        )
        return JSONResponse(payload, status_code=status)

    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the supported-region OpenAI Realtime STT gateway.")
    parser.add_argument("--host", default=os.getenv("GATEWAY_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.getenv("GATEWAY_PORT", "8443")))
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError("uvicorn is required to run the realtime gateway") from exc
    uvicorn.run("ai_secretary.stt.realtime_gateway:create_app", host=args.host, port=args.port, factory=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
