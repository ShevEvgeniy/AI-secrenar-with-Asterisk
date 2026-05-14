"""One-off smoke helper for the disabled-by-default gateway STT adapter."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
import json
import os
import sys
from typing import Any

from .gateway_adapter import config_from_env, transcribe_via_gateway
from .realtime_measurement import redact_secrets


def build_report(result_details: dict[str, Any], *, accepted: bool, attempted: bool, reason: str) -> dict[str, Any]:
    """Build a secret-safe NODE-027 style report from adapter result details."""
    safe_details = redact_secrets(result_details)
    transcript_present = bool(safe_details.get("transcript_text_present"))
    chunks_sent = safe_details.get("chunks_sent")
    return {
        "adapter_enabled_temporarily": bool(safe_details.get("stt_gateway_adapter_enabled")),
        "adapter_default_enabled_after_smoke": config_from_env({}).enabled,
        "adapter_smoke_exercised_node025_path": attempted,
        "gateway_reachable_from_asterisk": bool(safe_details.get("gateway_reachable")),
        "gateway_auth": safe_details.get("gateway_auth", "not_run"),
        "openai_realtime_from_gateway": _openai_status(safe_details),
        "chunks_sent": chunks_sent if isinstance(chunks_sent, int) else None,
        "audio_payload_valid": safe_details.get("audio_payload_valid"),
        "audio_duration_ms": safe_details.get("audio_duration_ms"),
        "audio_sample_rate_hz": safe_details.get("audio_sample_rate_hz"),
        "audio_channels": safe_details.get("audio_channels"),
        "audio_sample_width": safe_details.get("audio_sample_width"),
        "audio_total_bytes": safe_details.get("audio_total_bytes"),
        "audio_chunk_count": safe_details.get("audio_chunk_count"),
        "audio_rms": safe_details.get("audio_rms"),
        "audio_peak": safe_details.get("audio_peak"),
        "audio_non_silent_ratio": safe_details.get("audio_non_silent_ratio"),
        "audio_quality_classification": safe_details.get("audio_quality_classification"),
        "openai_event_type_counts": safe_details.get("openai_event_type_counts", {}),
        "transcript_event_seen": safe_details.get("transcript_event_seen"),
        "transcript_bearing_event_seen": safe_details.get("transcript_bearing_event_seen"),
        "error_event_seen": safe_details.get("error_event_seen"),
        "input_audio_buffer_commit_sent": safe_details.get("input_audio_buffer_commit_sent"),
        "timeout_observed": safe_details.get("timeout_observed"),
        "close_status": safe_details.get("close_status"),
        "transcript_present": transcript_present,
        "transcript_used_for_dialog": bool(safe_details.get("dialog_transcript_used")),
        "transcript_text_logged": bool(safe_details.get("transcript_text_logged")),
        "fallback_reason": None if accepted else reason,
        "error_type": safe_details.get("error_type"),
        "error_status": safe_details.get("gateway_http_status"),
        "error_redacted": True,
        "accepted": accepted,
        "attempted": attempted,
        "reason": reason,
        "details": safe_details,
    }


async def run_smoke(audio_path: Path) -> dict[str, Any]:
    config = config_from_env()
    events: list[dict[str, Any]] = []

    def log_event(action: str, status: str, reason: str | None, details: dict[str, Any]) -> None:
        events.append(
            {
                "action": action,
                "status": status,
                "reason": reason,
                "details": redact_secrets(details),
            }
        )

    result = await transcribe_via_gateway(
        audio_path,
        config=config,
        context={"smoke": "node027_gateway_adapter"},
        log_event=log_event,
    )
    report = build_report(
        result.details,
        accepted=result.accepted,
        attempted=result.attempted,
        reason=result.reason,
    )
    report["events"] = events
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one explicit, secret-safe smoke of the gateway STT adapter against a WAV file."
    )
    parser.add_argument("--audio", required=True, type=Path, help="Path to a WAV file to send through the adapter.")
    parser.add_argument(
        "--require-explicit-flags",
        action="store_true",
        help="Refuse to run unless adapter, dialog-use, URL, token, and transcript-redaction flags are explicit.",
    )
    args = parser.parse_args(argv)

    config = config_from_env()
    if args.require_explicit_flags:
        missing = _missing_required_flags(config)
        if missing:
            print(json.dumps({"ok": False, "missing_required_flags": missing}, ensure_ascii=False, indent=2))
            return 2

    report = asyncio.run(run_smoke(args.audio))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["adapter_smoke_exercised_node025_path"] else 2


def _missing_required_flags(config: Any) -> list[str]:
    missing: list[str] = []
    if not config.enabled:
        missing.append("STT_GATEWAY_STT_ENABLED or STT_GATEWAY_ADAPTER_ENABLED")
    if not config.use_transcript_for_dialog:
        missing.append("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true")
    if not config.gateway_url:
        missing.append("STT_GATEWAY_URL")
    if not config.gateway_token:
        missing.append("STT_GATEWAY_TOKEN")
    if config.log_transcript:
        missing.append("STT_GATEWAY_LOG_TRANSCRIPT=false")
    if os.getenv("OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY must be absent on Asterisk")
    return missing


def _openai_status(details: dict[str, Any]) -> str:
    if details.get("openai_realtime_connection_ok") is True:
        return "ok"
    if details.get("gateway_reachable") is True:
        return "failed"
    return "not_run"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
