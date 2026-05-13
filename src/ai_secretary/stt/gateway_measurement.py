"""NODE-021 measurement-only supported-region STT gateway helpers.

This module deliberately contains no HTTP framework dependency and no imports from
business dialog or telephony runtime code. It owns the gateway-side measurement
contract: validate one short 24 kHz mono PCM WAV, run an OpenAI Realtime
measurement from the supported-region gateway, and return redacted structured
metrics.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import hmac
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import uuid
import wave

from ai_secretary.stt.realtime_measurement import (
    DEFAULT_CHUNK_MS,
    DEFAULT_LANGUAGE,
    DEFAULT_REALTIME_TRANSCRIPTION_URL,
    DEFAULT_SAMPLE_RATE,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_TRANSCRIPTION_MODEL,
    RealtimeMeasurementConfig,
    RealtimeMeasurementResult,
    run_realtime_measurement,
)

SECRET_VALUE_REPLACEMENT = "[REDACTED]"
DEFAULT_MAX_AUDIO_SECONDS = 15
DEFAULT_MAX_AUDIO_BYTES = 1_048_576
SECRET_KEY_PATTERN = re.compile(r"(api[_-]?key|authorization|bearer|token|secret|password)", re.IGNORECASE)
OPENAI_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_\-]{8,}")
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9_\-.]+", re.IGNORECASE)

ERROR_RETRYABLE: dict[str, bool] = {
    "gateway_auth_failed": False,
    "gateway_audio_invalid": False,
    "gateway_timeout": True,
    "openai_region_rejected": False,
    "openai_auth_failed": False,
    "openai_rate_limited": True,
    "openai_transient": True,
    "openai_transcription_empty": False,
    "gateway_internal_error": True,
}


@dataclass(frozen=True)
class GatewayConfig:
    """Gateway-side measurement configuration read from gateway env/secret storage."""

    openai_api_key: str
    gateway_token: str
    gateway_region: str = "unknown"
    realtime_url: str = DEFAULT_REALTIME_TRANSCRIPTION_URL
    model: str = DEFAULT_TRANSCRIPTION_MODEL
    language: str = DEFAULT_LANGUAGE
    sample_rate: int = DEFAULT_SAMPLE_RATE
    chunk_ms: int = DEFAULT_CHUNK_MS
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_audio_seconds: int = DEFAULT_MAX_AUDIO_SECONDS
    max_audio_bytes: int = DEFAULT_MAX_AUDIO_BYTES
    return_transcript_default: bool = False


@dataclass(frozen=True)
class GatewayRequest:
    """One-shot measurement request accepted by the supported-region gateway."""

    audio_wav: bytes
    gateway_request_id: str
    call_id: str | None = None
    stage: str | None = None
    language: str | None = None
    return_transcript: bool = False


@dataclass(frozen=True)
class GatewayAudioInfo:
    format: str
    encoding: str
    sample_rate_hz: int
    channels: int
    duration_ms: int
    bytes_received: int
    chunk_count: int


GatewayRunner = Callable[[RealtimeMeasurementConfig], Awaitable[RealtimeMeasurementResult]]


def config_from_env(environ: dict[str, str] | None = None) -> GatewayConfig:
    """Build gateway config. OPENAI_API_KEY is gateway-side only."""
    env = environ if environ is not None else os.environ
    return GatewayConfig(
        openai_api_key=env.get("OPENAI_API_KEY", ""),
        gateway_token=env.get("STT_GATEWAY_SERVER_TOKEN", ""),
        gateway_region=env.get("GATEWAY_REGION_LABEL", "unknown"),
        realtime_url=env.get("OPENAI_REALTIME_URL", DEFAULT_REALTIME_TRANSCRIPTION_URL),
        model=env.get("OPENAI_REALTIME_MODEL", DEFAULT_TRANSCRIPTION_MODEL),
        language=env.get("OPENAI_REALTIME_LANGUAGE", DEFAULT_LANGUAGE),
        timeout_seconds=float(env.get("OPENAI_REALTIME_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS)),
        max_audio_seconds=int(env.get("STT_GATEWAY_MAX_AUDIO_SECONDS", DEFAULT_MAX_AUDIO_SECONDS)),
        max_audio_bytes=int(env.get("STT_GATEWAY_MAX_AUDIO_BYTES", DEFAULT_MAX_AUDIO_BYTES)),
        return_transcript_default=_env_bool(env.get("STT_GATEWAY_RETURN_TRANSCRIPT_DEFAULT", "false")),
    )


def make_gateway_request_id(prefix: str = "gw") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def validate_gateway_authorization(authorization: str | None, expected_token: str) -> bool:
    """Validate ``Authorization: Bearer`` using constant-time comparison."""
    if not authorization or not expected_token:
        return False
    parts = authorization.split()
    return len(parts) == 2 and parts[0].lower() == "bearer" and hmac.compare_digest(parts[1], expected_token)


def validate_wav_audio(
    audio_wav: bytes,
    *,
    sample_rate: int,
    max_seconds: int,
    max_bytes: int,
    chunk_ms: int = DEFAULT_CHUNK_MS,
) -> GatewayAudioInfo:
    """Validate first-proof WAV constraints before contacting OpenAI."""
    if not audio_wav:
        raise ValueError("audio is empty")
    if len(audio_wav) > max_bytes:
        raise ValueError(f"audio is too large: bytes={len(audio_wav)} limit={max_bytes}")
    try:
        with wave.open(BytesIO(audio_wav), "rb") as handle:
            channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            frame_rate = handle.getframerate()
            frame_count = handle.getnframes()
    except wave.Error as exc:
        raise ValueError(f"invalid WAV audio: {exc}") from exc

    duration_ms = int(frame_count / frame_rate * 1000) if frame_rate else 0
    if channels != 1 or sample_width != 2 or frame_rate != sample_rate:
        raise ValueError(
            "measurement WAV must be mono 16-bit PCM at "
            f"{sample_rate} Hz; got channels={channels}, sample_width={sample_width}, rate={frame_rate}"
        )
    if duration_ms > max_seconds * 1000:
        raise ValueError(f"audio duration is too long: duration_ms={duration_ms} limit_ms={max_seconds * 1000}")
    frames_per_chunk = max(1, int(frame_rate * chunk_ms / 1000))
    chunk_count = (frame_count + frames_per_chunk - 1) // frames_per_chunk if frame_count else 0
    return GatewayAudioInfo(
        format="wav",
        encoding="pcm_s16le",
        sample_rate_hz=frame_rate,
        channels=channels,
        duration_ms=duration_ms,
        bytes_received=len(audio_wav),
        chunk_count=chunk_count,
    )


async def run_gateway_realtime_measurement(
    request: GatewayRequest,
    config: GatewayConfig,
    *,
    runner: GatewayRunner | None = None,
) -> dict[str, Any]:
    """Run one measurement from the gateway and return redacted JSON-ready metrics."""
    audio_info: GatewayAudioInfo | None = None
    cleanup_done = False
    try:
        audio_info = validate_wav_audio(
            request.audio_wav,
            sample_rate=config.sample_rate,
            max_seconds=config.max_audio_seconds,
            max_bytes=config.max_audio_bytes,
            chunk_ms=config.chunk_ms,
        )
        if not config.openai_api_key:
            return build_gateway_response(
                request=request,
                config=config,
                audio_info=audio_info,
                realtime_result=None,
                cleanup_done=True,
                error_type="config",
                error_code="openai_auth_failed",
                error_message="Gateway OpenAI credential is missing",
            )

        runner = runner or run_realtime_measurement
        with tempfile.NamedTemporaryFile(prefix="stt-gateway-", suffix=".wav", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(request.audio_wav)
        try:
            result = await runner(
                RealtimeMeasurementConfig(
                    api_key=config.openai_api_key,
                    audio_path=temp_path,
                    websocket_url=config.realtime_url,
                    transcription_model=config.model,
                    language=request.language or config.language,
                    sample_rate=config.sample_rate,
                    chunk_ms=config.chunk_ms,
                    timeout_seconds=config.timeout_seconds,
                )
            )
        finally:
            temp_path.unlink(missing_ok=True)
            cleanup_done = True

        if result.error:
            return build_gateway_response(
                request=request,
                config=config,
                audio_info=audio_info,
                realtime_result=result,
                cleanup_done=cleanup_done,
                error_type="openai",
                error_code=map_realtime_error(result.error),
                error_message=result.error,
            )
        if not result.transcript_text_present:
            return build_gateway_response(
                request=request,
                config=config,
                audio_info=audio_info,
                realtime_result=result,
                cleanup_done=cleanup_done,
                error_type="openai",
                error_code="openai_transcription_empty",
                error_message="Realtime completed without transcript text",
            )
        return build_gateway_response(
            request=request,
            config=config,
            audio_info=audio_info,
            realtime_result=result,
            cleanup_done=cleanup_done,
        )
    except ValueError as exc:
        return build_gateway_response(
            request=request,
            config=config,
            audio_info=audio_info,
            realtime_result=None,
            cleanup_done=True,
            error_type="gateway",
            error_code="gateway_audio_invalid",
            error_message=str(exc),
        )
    except Exception as exc:
        return build_gateway_response(
            request=request,
            config=config,
            audio_info=audio_info,
            realtime_result=None,
            cleanup_done=cleanup_done,
            error_type="gateway",
            error_code="gateway_internal_error",
            error_message=repr(exc),
        )


def run_gateway_realtime_measurement_sync(request: GatewayRequest, config: GatewayConfig) -> dict[str, Any]:
    return asyncio.run(run_gateway_realtime_measurement(request, config))


def build_gateway_response(
    *,
    request: GatewayRequest,
    config: GatewayConfig,
    audio_info: GatewayAudioInfo | None,
    realtime_result: RealtimeMeasurementResult | None,
    cleanup_done: bool,
    error_type: str | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> dict[str, Any]:
    """Build the NODE-021 structured metrics response without transcript text."""
    chunks_sent = realtime_result.chunks_sent if realtime_result else 0
    response = {
        "ok": error_code is None,
        "gateway_request_id": request.gateway_request_id,
        "gateway_region": config.gateway_region,
        "call_id_present": bool(request.call_id),
        "stage": request.stage,
        "model": config.model,
        "audio": _audio_payload(audio_info, chunks_sent),
        "openai_realtime_connection_ok": bool(realtime_result and realtime_result.connection_ok),
        "openai_realtime_connection_failed": bool(error_code and not (realtime_result and realtime_result.connection_ok)),
        "openai_session_created": bool(realtime_result and realtime_result.session_created),
        "openai_session_failed": bool(error_code and not (realtime_result and realtime_result.session_created)),
        "audio_send_started": chunks_sent > 0,
        "chunks_sent": chunks_sent,
        "first_delta_ms": realtime_result.first_delta_ms if realtime_result else None,
        "final_ms": realtime_result.final_ms if realtime_result else None,
        "transcript_text_present": bool(realtime_result and realtime_result.transcript_text_present),
        "transcript_text_returned": False,
        "error_type": error_type,
        "error_code": error_code,
        "error_message_redacted": redact_secret_text(error_message) if error_message else None,
        "retryable": ERROR_RETRYABLE.get(error_code, False) if error_code else False,
        "cleanup_done": cleanup_done,
    }
    return redact_response(response)


def map_realtime_error(reason: str) -> str:
    lowered = reason.lower()
    if "unsupported_country_region_territory" in lowered or "region" in lowered:
        return "openai_region_rejected"
    if "invalid_api_key" in lowered or "missing_openai_api_key" in lowered or "auth" in lowered:
        return "openai_auth_failed"
    if "rate" in lowered and "limit" in lowered:
        return "openai_rate_limited"
    if "timeout" in lowered:
        return "gateway_timeout"
    return "openai_transient"


def emit_gateway_event(action: str, details: dict[str, Any], *, writer: Callable[[str], None] | None = None) -> None:
    """Write one redacted gateway JSON event."""
    line = json.dumps({"action": action, "details": redact_response(details)}, ensure_ascii=False, sort_keys=True)
    if writer is None:
        print(line, flush=True)
    else:
        writer(line)


def redact_response(value: Any) -> Any:
    """Recursively redact likely secrets from JSON-ready data."""
    if isinstance(value, dict):
        redacted: dict[Any, Any] = {}
        for key, item in value.items():
            if SECRET_KEY_PATTERN.search(str(key)):
                redacted[key] = SECRET_VALUE_REPLACEMENT
            else:
                redacted[key] = redact_response(item)
        return redacted
    if isinstance(value, list):
        return [redact_response(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_response(item) for item in value)
    if isinstance(value, str):
        return redact_secret_text(value)
    return value


def redact_secret_text(text: str) -> str:
    text = BEARER_PATTERN.sub(f"Bearer {SECRET_VALUE_REPLACEMENT}", OPENAI_KEY_PATTERN.sub(SECRET_VALUE_REPLACEMENT, text))
    return text.replace("OPENAI_API_KEY", SECRET_VALUE_REPLACEMENT).replace("STT_GATEWAY_SERVER_TOKEN", SECRET_VALUE_REPLACEMENT).replace("STT_GATEWAY_TOKEN", SECRET_VALUE_REPLACEMENT)


def _audio_payload(audio_info: GatewayAudioInfo | None, chunks_sent: int) -> dict[str, Any]:
    if audio_info is None:
        return {
            "format": None,
            "encoding": None,
            "sample_rate_hz": None,
            "channels": None,
            "duration_ms": None,
            "bytes_received": 0,
            "chunks_sent": chunks_sent,
        }
    return {
        "format": audio_info.format,
        "encoding": audio_info.encoding,
        "sample_rate_hz": audio_info.sample_rate_hz,
        "channels": audio_info.channels,
        "duration_ms": audio_info.duration_ms,
        "bytes_received": audio_info.bytes_received,
        "chunks_sent": chunks_sent,
    }


def _env_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
