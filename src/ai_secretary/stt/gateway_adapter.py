"""Disabled-by-default Asterisk-side STT gateway adapter."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
import os
import time
from typing import Any

import httpx

from .realtime_gateway import GATEWAY_ENDPOINT
from .realtime_measurement import DEFAULT_LANGUAGE, redact_secrets
from ..telephony.transcript_policy import (
    TranscriptCandidate,
    TranscriptUsePolicy,
    evaluate_business_dialog_transcript_use,
    transcript_use_policy_from_env,
)


DEFAULT_GATEWAY_TIMEOUT_MS = 10_000
DEFAULT_GATEWAY_MAX_RETRIES = 0


@dataclass(frozen=True)
class GatewaySttAdapterConfig:
    enabled: bool = False
    use_transcript_for_dialog: bool = False
    gateway_url: str = ""
    gateway_token: str = ""
    timeout_ms: int = DEFAULT_GATEWAY_TIMEOUT_MS
    max_retries: int = DEFAULT_GATEWAY_MAX_RETRIES
    log_transcript: bool = False
    language: str = DEFAULT_LANGUAGE
    min_confidence: float | None = None
    business_dialog_transcript_policy: TranscriptUsePolicy = TranscriptUsePolicy()


@dataclass(frozen=True)
class GatewaySttAdapterResult:
    text: str
    accepted: bool
    attempted: bool
    reason: str
    details: dict[str, Any]


GatewayPost = Callable[[GatewaySttAdapterConfig, bytes], Awaitable[tuple[int, dict[str, Any]]]]


def config_from_env(environ: dict[str, str] | None = None) -> GatewaySttAdapterConfig:
    env = environ if environ is not None else os.environ
    return GatewaySttAdapterConfig(
        enabled=_env_bool(env, "STT_GATEWAY_STT_ENABLED", False)
        or _env_bool(env, "STT_GATEWAY_ADAPTER_ENABLED", False),
        use_transcript_for_dialog=_env_bool(env, "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", False),
        gateway_url=_env_first(env, "STT_GATEWAY_URL", "REALTIME_GATEWAY_URL"),
        gateway_token=_env_first(env, "STT_GATEWAY_TOKEN", "REALTIME_GATEWAY_TOKEN"),
        timeout_ms=_env_int(env, "STT_GATEWAY_TIMEOUT_MS", DEFAULT_GATEWAY_TIMEOUT_MS),
        max_retries=_env_int(env, "STT_GATEWAY_MAX_RETRIES", DEFAULT_GATEWAY_MAX_RETRIES),
        log_transcript=_env_bool(env, "STT_GATEWAY_LOG_TRANSCRIPT", False),
        language=env.get("STT_GATEWAY_LANGUAGE", DEFAULT_LANGUAGE).strip() or DEFAULT_LANGUAGE,
        min_confidence=_env_optional_float(env, "STT_GATEWAY_MIN_CONFIDENCE"),
        business_dialog_transcript_policy=transcript_use_policy_from_env(env),
    )


async def transcribe_via_gateway(
    audio_path: os.PathLike[str] | str,
    *,
    config: GatewaySttAdapterConfig | None = None,
    context: dict[str, Any] | None = None,
    post: GatewayPost | None = None,
    log_event: Callable[[str, str, str | None, dict[str, Any]], None] | None = None,
    clock: Callable[[], float] = time.perf_counter,
    allow_request_without_dialog_use: bool = False,
) -> GatewaySttAdapterResult:
    config = config or config_from_env()
    base_details = {
        **(context or {}),
        "stt_gateway_adapter_enabled": config.enabled,
        "stt_gateway_use_transcript_for_dialog": config.use_transcript_for_dialog,
        "stt_gateway_url_configured": bool(config.gateway_url),
        "stt_gateway_token_configured": bool(config.gateway_token),
        "stt_gateway_timeout_ms": config.timeout_ms,
        "stt_gateway_max_retries": config.max_retries,
        "stt_gateway_log_transcript": config.log_transcript,
        "stt_gateway_language": config.language,
        "business_dialog_transcript_policy_enabled": config.business_dialog_transcript_policy.enabled,
        "business_dialog_transcript_redact_logs": config.business_dialog_transcript_policy.redact_logs,
        "business_dialog_transcript_fail_closed": config.business_dialog_transcript_policy.fail_closed,
        "business_dialog_transcript_max_age_ms": config.business_dialog_transcript_policy.max_age_ms,
    }
    if config.business_dialog_transcript_policy.min_confidence is not None:
        base_details["business_dialog_transcript_min_confidence"] = config.business_dialog_transcript_policy.min_confidence
    if not config.enabled:
        return _result("", False, False, "gateway_stt_disabled", base_details)
    if not config.use_transcript_for_dialog and not allow_request_without_dialog_use:
        return _fallback("gateway_stt_dialog_use_disabled", base_details, log_event=log_event)
    if not config.gateway_url:
        return _fallback("missing_gateway_url", base_details, log_event=log_event)
    if not config.gateway_token:
        return _fallback("missing_gateway_token", base_details, log_event=log_event)

    audio = os.fspath(audio_path)
    audio_bytes = await asyncio.to_thread(_read_bytes, audio)
    post = post or _post_gateway_stt
    attempts = max(0, config.max_retries) + 1
    started = clock()
    last_details = {**base_details, "audio_bytes": len(audio_bytes)}

    for attempt in range(1, attempts + 1):
        request_details = {**last_details, "attempt": attempt}
        _log(log_event, "gateway_stt_request_started", "start", None, request_details)
        try:
            status_code, payload = await post(config, audio_bytes)
        except (TimeoutError, asyncio.TimeoutError, httpx.TimeoutException) as exc:
            last_details = {
                **request_details,
                "error_type": type(exc).__name__,
                "fallback_reason": "gateway_timeout",
                "total_ms": int((clock() - started) * 1000),
            }
            _log(log_event, "gateway_stt_timeout", "handled", "gateway_timeout", last_details)
            continue
        except Exception as exc:
            last_details = {
                **request_details,
                "error_type": type(exc).__name__,
                "fallback_reason": "gateway_unavailable",
                "total_ms": int((clock() - started) * 1000),
            }
            _log(log_event, "gateway_stt_gateway_unavailable", "handled", "gateway_unavailable", last_details)
            continue

        safe_payload = _safe_gateway_payload(payload, log_transcript=config.log_transcript)
        last_details = {
            **request_details,
            **safe_payload,
            "gateway_http_status": status_code,
            "gateway_reachable": True,
            "gateway_auth": "failed" if status_code in {401, 403} else "ok",
            "total_ms": int((clock() - started) * 1000),
        }
        if status_code in {401, 403}:
            _log(log_event, "gateway_stt_auth_failed", "fail", "gateway_auth_failed", last_details)
            return _fallback("gateway_auth_failed", last_details, log_event=log_event)
        if not (200 <= status_code < 300):
            _log(log_event, "gateway_stt_gateway_unavailable", "handled", "gateway_returned_error", last_details)
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("ok"), bool):
            malformed_details = {**last_details, "fallback_reason": "malformed_response"}
            _log(log_event, "gateway_stt_fallback", "handled", "malformed_response", malformed_details)
            return _result("", False, True, "malformed_response", malformed_details)
        if not payload.get("ok"):
            continue

        transcript = str(payload.get("transcript_text") or "").strip()
        transcript_age_ms = _payload_optional_int(payload, "transcript_age_ms")
        metadata_complete = bool(payload.get("transcript_metadata_complete", True))
        confidence = _payload_optional_float(payload, "confidence")
        candidate_details = {
            **last_details,
            "transcript_text_present": bool(transcript or payload.get("transcript_text_present")),
            "transcript_text_length": len(transcript),
            "transcript_text_logged": False,
            "redaction_applied": True,
            "dialog_transcript_used": False,
            "transcript_metadata_complete": metadata_complete,
        }
        _log(log_event, "gateway_stt_transcript_candidate", "ok", None, candidate_details)

        reject_reason = _transcript_reject_reason(transcript, payload, config)
        if not config.use_transcript_for_dialog:
            reject_reason = "gateway_stt_dialog_use_disabled"
        policy_decision = evaluate_business_dialog_transcript_use(
            TranscriptCandidate(
                text=transcript,
                confidence=confidence,
                age_ms=transcript_age_ms,
                metadata_complete=metadata_complete,
                redaction_active=not config.log_transcript,
            ),
            policy=config.business_dialog_transcript_policy,
        )
        candidate_details = {**candidate_details, **policy_decision.to_safe_details()}
        if not reject_reason and not policy_decision.allowed:
            reject_reason = policy_decision.reason
        if reject_reason:
            rejected_details = {**candidate_details, "fallback_reason": reject_reason}
            _log(log_event, "gateway_stt_transcript_rejected", "handled", reject_reason, rejected_details)
            return _result("", False, True, reject_reason, rejected_details)

        accepted_details = {**candidate_details, "dialog_transcript_used": True}
        _log(log_event, "gateway_stt_transcript_accepted", "ok", None, accepted_details)
        return GatewaySttAdapterResult(
            text=transcript,
            accepted=True,
            attempted=True,
            reason="gateway_transcript_accepted",
            details=accepted_details,
        )

    return _fallback(str(last_details.get("fallback_reason") or "gateway_unavailable"), last_details, log_event=log_event)


async def _post_gateway_stt(config: GatewaySttAdapterConfig, audio: bytes) -> tuple[int, dict[str, Any]]:
    headers = {"Authorization": f"Bearer {config.gateway_token}", "Content-Type": "audio/wav"}
    params = {"language": config.language, "return_transcript": "true"}
    async with httpx.AsyncClient(timeout=config.timeout_ms / 1000) as client:
        response = await client.post(_adapter_endpoint(config.gateway_url), content=audio, headers=headers, params=params)
    try:
        payload = response.json()
    except ValueError:
        payload = {"ok": False, "error_type": "gateway_non_json_response"}
    return response.status_code, payload


def _adapter_endpoint(url: str) -> str:
    value = url.strip()
    if value.endswith(GATEWAY_ENDPOINT):
        return value
    return value.rstrip("/") + GATEWAY_ENDPOINT


def _transcript_reject_reason(
    transcript: str,
    payload: dict[str, Any],
    config: GatewaySttAdapterConfig,
) -> str | None:
    if not transcript:
        return "empty_transcript"
    confidence = payload.get("confidence")
    if config.min_confidence is not None and isinstance(confidence, int | float):
        if float(confidence) < config.min_confidence:
            return "low_quality_transcript"
    return None


def _safe_gateway_payload(payload: Any, *, log_transcript: bool) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"malformed_response": True}
    safe = dict(redact_secrets(payload))
    transcript = safe.pop("transcript_text", None)
    if isinstance(transcript, str):
        stripped = transcript.strip()
        safe["transcript_text_present"] = bool(stripped) or bool(safe.get("transcript_text_present"))
        safe["transcript_text_length"] = len(stripped)
        safe["transcript_text_length_bucket"] = "nonzero_redacted" if stripped else "zero"
        safe["transcript_text_logged"] = False
    else:
        if "transcript_text_length_bucket" not in safe:
            safe["transcript_text_length_bucket"] = "unknown"
        safe["transcript_text_logged"] = False
    return safe


def _fallback(
    reason: str,
    details: dict[str, Any],
    *,
    log_event: Callable[[str, str, str | None, dict[str, Any]], None] | None,
) -> GatewaySttAdapterResult:
    fallback_details = {**details, "fallback_reason": reason, "dialog_transcript_used": False}
    _log(log_event, "gateway_stt_fallback", "handled", reason, fallback_details)
    return _result("", False, True, reason, fallback_details)


def _result(
    text: str | bool,
    accepted: bool,
    attempted: bool,
    reason: str,
    details: dict[str, Any],
) -> GatewaySttAdapterResult:
    return GatewaySttAdapterResult(
        text=text if isinstance(text, str) else "",
        accepted=accepted,
        attempted=attempted,
        reason=reason,
        details=details,
    )


def _log(
    log_event: Callable[[str, str, str | None, dict[str, Any]], None] | None,
    action: str,
    status: str,
    reason: str | None,
    details: dict[str, Any],
) -> None:
    if log_event is not None:
        log_event(action, status, reason, redact_secrets(details))


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _env_first(env: dict[str, str], *names: str) -> str:
    for name in names:
        value = env.get(name)
        if value and value.strip():
            return value.strip()
    return ""


def _env_bool(env: dict[str, str], name: str, default: bool) -> bool:
    raw = env.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(env: dict[str, str], name: str, default: int) -> int:
    raw = env.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _env_optional_float(env: dict[str, str], name: str) -> float | None:
    raw = env.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _payload_optional_float(payload: dict[str, Any], name: str) -> float | None:
    value = payload.get(name)
    if isinstance(value, int | float):
        return float(value)
    return None


def _payload_optional_int(payload: dict[str, Any], name: str, default: int | None = None) -> int | None:
    value = payload.get(name)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return default
