"""Manual Asterisk-side gateway smoke wrapper.

This script is intentionally one-shot only. It validates the runtime boundary,
then delegates to ai_secretary.stt.gateway_adapter_smoke with transcript logging
disabled and business-dialog transcript use disabled.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import struct
import sys
from typing import Mapping
import wave


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ai_secretary.stt import gateway_adapter_smoke  # noqa: E402


SMOKE_WAV_SAMPLE_RATE_HZ = 24000
SMOKE_WAV_CHANNELS = 1
SMOKE_WAV_SAMPLE_WIDTH_BYTES = 2
SMOKE_WAV_DURATION_SECONDS = 1.0
SMOKE_WAV_FREQUENCY_HZ = 440


def validate_runtime_env(environ: Mapping[str, str]) -> list[str]:
    """Return fail-closed validation errors without reading or printing values."""
    missing: list[str] = []
    enabled = _env_bool(environ, "STT_GATEWAY_STT_ENABLED") or _env_bool(environ, "STT_GATEWAY_ADAPTER_ENABLED")
    if not enabled:
        missing.append("STT_GATEWAY_STT_ENABLED or STT_GATEWAY_ADAPTER_ENABLED must be true")
    if environ.get("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG") is None:
        missing.append("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must be explicitly false")
    elif _env_bool(environ, "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG"):
        missing.append("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must remain false")
    if not _env_present(environ, "STT_GATEWAY_URL") and not _env_present(environ, "REALTIME_GATEWAY_URL"):
        missing.append("STT_GATEWAY_URL or REALTIME_GATEWAY_URL")
    if not _env_present(environ, "STT_GATEWAY_TOKEN") and not _env_present(environ, "REALTIME_GATEWAY_TOKEN"):
        missing.append("STT_GATEWAY_TOKEN or REALTIME_GATEWAY_TOKEN")
    if _env_bool(environ, "STT_GATEWAY_LOG_TRANSCRIPT"):
        missing.append("STT_GATEWAY_LOG_TRANSCRIPT must be false")
    if _env_present(environ, "OPENAI_API_KEY"):
        missing.append("OPENAI_API_KEY must be absent on Asterisk")
    for name in (
        "STT_GATEWAY_URL",
        "REALTIME_GATEWAY_URL",
        "STT_GATEWAY_TOKEN",
        "REALTIME_GATEWAY_TOKEN",
    ):
        if _env_has_newline_material(environ, name):
            missing.append(f"{name} must not contain newline material")
    return missing


def create_smoke_wav(path: Path, *, duration_seconds: float = SMOKE_WAV_DURATION_SECONDS) -> None:
    """Create a non-transcript synthetic 24 kHz mono 16-bit PCM WAV."""
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(SMOKE_WAV_SAMPLE_RATE_HZ * duration_seconds)
    frames = bytearray()
    for index in range(frame_count):
        sample = int(
            0.20
            * 32767
            * math.sin(2 * math.pi * SMOKE_WAV_FREQUENCY_HZ * index / SMOKE_WAV_SAMPLE_RATE_HZ)
        )
        frames.extend(struct.pack("<h", sample))

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(SMOKE_WAV_CHANNELS)
        handle.setsampwidth(SMOKE_WAV_SAMPLE_WIDTH_BYTES)
        handle.setframerate(SMOKE_WAV_SAMPLE_RATE_HZ)
        handle.writeframes(bytes(frames))


def inspect_smoke_wav(path: Path) -> tuple[dict[str, object], list[str]]:
    metadata: dict[str, object] = {
        "audio_path": str(path),
        "required_sample_rate_hz": SMOKE_WAV_SAMPLE_RATE_HZ,
        "required_channels": SMOKE_WAV_CHANNELS,
        "required_sample_width_bytes": SMOKE_WAV_SAMPLE_WIDTH_BYTES,
    }
    if not path.is_file():
        return metadata, ["audio file missing"]
    try:
        with wave.open(str(path), "rb") as handle:
            metadata.update(
                {
                    "sample_rate_hz": handle.getframerate(),
                    "channels": handle.getnchannels(),
                    "sample_width_bytes": handle.getsampwidth(),
                    "frame_count": handle.getnframes(),
                    "compression": handle.getcomptype(),
                }
            )
    except (EOFError, wave.Error) as exc:
        return metadata, [f"audio WAV malformed: {exc.__class__.__name__}"]

    errors: list[str] = []
    if metadata["sample_rate_hz"] != SMOKE_WAV_SAMPLE_RATE_HZ:
        errors.append("audio sample rate must be 24000 Hz")
    if metadata["channels"] != SMOKE_WAV_CHANNELS:
        errors.append("audio channels must be mono")
    if metadata["sample_width_bytes"] != SMOKE_WAV_SAMPLE_WIDTH_BYTES:
        errors.append("audio sample width must be 16-bit PCM")
    if metadata["compression"] != "NONE":
        errors.append("audio compression must be PCM")
    if int(metadata["frame_count"]) <= 0:
        errors.append("audio frame count must be positive")
    return metadata, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one manual Asterisk-side gateway smoke without business-dialog transcript use."
    )
    parser.add_argument("--audio", type=Path, help="Path to the operator-approved smoke WAV file.")
    parser.add_argument("--create-smoke-audio", type=Path, help="Create a safe 24 kHz mono PCM smoke WAV.")
    parser.add_argument("--validate-smoke-audio", type=Path, help="Validate a smoke WAV without printing secrets.")
    args = parser.parse_args(argv)

    if args.create_smoke_audio and args.validate_smoke_audio:
        print(_safe_json(_audio_report("invalid_audio_action", {}, ["choose only one audio action"])))
        return 2
    if args.create_smoke_audio:
        try:
            create_smoke_wav(args.create_smoke_audio)
            metadata, errors = inspect_smoke_wav(args.create_smoke_audio)
        except (OSError, ValueError) as exc:
            metadata = {"audio_path": str(args.create_smoke_audio)}
            errors = [f"audio create failed: {exc.__class__.__name__}"]
        print(_safe_json(_audio_report("create_smoke_audio", metadata, errors)))
        return 0 if not errors else 2
    if args.validate_smoke_audio:
        metadata, errors = inspect_smoke_wav(args.validate_smoke_audio)
        print(_safe_json(_audio_report("validate_smoke_audio", metadata, errors)))
        return 0 if not errors else 2
    if args.audio is None:
        print(_safe_json(_audio_report("missing_audio", {}, ["--audio is required"])))
        return 2

    errors = validate_runtime_env(os.environ)
    if errors:
        print(
            _safe_json(
                {
                    "ok": False,
                    "manual_only": True,
                    "state_changing": False,
                    "missing_required_flags": errors,
                    "secret_values_printed": False,
                    "transcript_text_logged": False,
                    "business_dialog_unchanged": True,
                }
            )
        )
        return 2

    metadata, audio_errors = inspect_smoke_wav(args.audio)
    if audio_errors:
        print(_safe_json(_audio_report("validate_before_smoke", metadata, audio_errors)))
        return 2

    return gateway_adapter_smoke.main(["--audio", str(args.audio), "--require-explicit-flags"])


def _env_present(environ: Mapping[str, str], name: str) -> bool:
    value = environ.get(name)
    return bool(value and value.strip())


def _env_bool(environ: Mapping[str, str], name: str) -> bool:
    value = environ.get(name, "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_has_newline_material(environ: Mapping[str, str], name: str) -> bool:
    value = environ.get(name, "")
    return "\r" in value or "\n" in value or "\\r" in value or "\\n" in value


def _audio_report(action: str, metadata: Mapping[str, object], errors: list[str]) -> dict[str, object]:
    return {
        "ok": not errors,
        "action": action,
        "manual_only": True,
        "state_changing": False,
        "audio": dict(metadata),
        "audio_format_errors": errors,
        "secret_values_printed": False,
        "transcript_text_logged": False,
        "transcript_used_for_dialog": False,
        "business_dialog_unchanged": True,
    }


def _safe_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
