"""Manual Asterisk-side gateway smoke wrapper.

This script is intentionally one-shot only. It validates the runtime boundary,
then delegates to ai_secretary.stt.gateway_adapter_smoke. Runtime env may be
loaded from a KEY=VALUE file through a small allowlist parser so callers do not
need fragile nested shell quoting or shell-level env dumps.
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
SMOKE_ENV_KEYS = (
    "STT_GATEWAY_STT_ENABLED",
    "STT_GATEWAY_ADAPTER_ENABLED",
    "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG",
    "STT_GATEWAY_LOG_TRANSCRIPT",
    "STT_GATEWAY_URL",
    "STT_GATEWAY_TOKEN",
    "REALTIME_GATEWAY_URL",
    "REALTIME_GATEWAY_TOKEN",
    "BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED",
    "BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS",
    "BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED",
    "BUSINESS_DIALOG_TRANSCRIPT_MAX_AGE_MS",
    "BUSINESS_DIALOG_TRANSCRIPT_MIN_CONFIDENCE",
)
SECRET_ENV_KEYS = {
    "STT_GATEWAY_TOKEN",
    "REALTIME_GATEWAY_TOKEN",
}


def parse_env_file(path: Path) -> tuple[dict[str, str], list[str]]:
    """Parse a simple KEY=VALUE env file without shell evaluation."""
    if not path.is_file():
        return {}, ["env file missing"]
    parsed: dict[str, str] = {}
    errors: list[str] = []
    allowed = set(SMOKE_ENV_KEYS)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return {}, [f"env file unreadable: {exc.__class__.__name__}"]
    for line_no, raw_line in enumerate(lines, start=1):
        if not raw_line or raw_line.startswith("#"):
            continue
        if "=" not in raw_line:
            errors.append(f"line {line_no} is not KEY=VALUE")
            continue
        key, value = raw_line.split("=", 1)
        if key not in allowed:
            errors.append(f"{key} is not an allowed smoke env key")
            continue
        if key in parsed:
            errors.append(f"{key} duplicate")
            continue
        if _env_has_newline_material({key: value}, key):
            errors.append(f"{key} must not contain newline material")
            continue
        if any(ord(ch) < 32 for ch in value):
            errors.append(f"{key} must not contain control characters")
            continue
        parsed[key] = value
    return parsed, errors


def validate_runtime_env(environ: Mapping[str, str], *, dialog_transcript_use: str = "disabled") -> list[str]:
    """Return fail-closed validation errors without reading or printing values."""
    missing: list[str] = []
    enabled = _env_bool(environ, "STT_GATEWAY_STT_ENABLED") or _env_bool(environ, "STT_GATEWAY_ADAPTER_ENABLED")
    if not enabled:
        missing.append("STT_GATEWAY_STT_ENABLED or STT_GATEWAY_ADAPTER_ENABLED must be true")
    if dialog_transcript_use not in {"disabled", "enabled"}:
        missing.append("dialog transcript use mode must be disabled or enabled")
    expected_dialog_use = dialog_transcript_use == "enabled"
    if environ.get("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG") is None:
        missing.append(f"STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must be explicitly {str(expected_dialog_use).lower()}")
    elif _env_bool(environ, "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG") is not expected_dialog_use:
        missing.append(f"STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must be {str(expected_dialog_use).lower()}")
    if dialog_transcript_use == "enabled":
        if not _env_bool(environ, "BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED"):
            missing.append("BUSINESS_DIALOG_TRANSCRIPT_USE_ENABLED must be true")
        if not _env_bool(environ, "BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS", default=True):
            missing.append("BUSINESS_DIALOG_TRANSCRIPT_REDACT_LOGS must be true")
        if not _env_bool(environ, "BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED", default=True):
            missing.append("BUSINESS_DIALOG_TRANSCRIPT_FAIL_CLOSED must be true")
    if not _env_present(environ, "STT_GATEWAY_URL") and not _env_present(environ, "REALTIME_GATEWAY_URL"):
        missing.append("STT_GATEWAY_URL")
    if not _env_present(environ, "STT_GATEWAY_TOKEN") and not _env_present(environ, "REALTIME_GATEWAY_TOKEN"):
        missing.append("STT_GATEWAY_TOKEN")
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
        description="Run one manual Asterisk-side gateway smoke with explicit transcript-use boundaries."
    )
    parser.add_argument("--audio", type=Path, help="Path to the operator-approved smoke WAV file.")
    parser.add_argument("--create-smoke-audio", type=Path, help="Create a safe 24 kHz mono PCM smoke WAV.")
    parser.add_argument("--validate-smoke-audio", type=Path, help="Validate a smoke WAV without printing secrets.")
    parser.add_argument("--env-file", type=Path, help="Load smoke env from a KEY=VALUE allowlist file.")
    parser.add_argument(
        "--dialog-transcript-use",
        choices=("disabled", "enabled"),
        default="disabled",
        help="Require dialog transcript-use flags to be disabled or enabled.",
    )
    parser.add_argument(
        "--dry-run-env-check",
        action="store_true",
        help="Validate env loading and required flags without reading audio or calling Gateway.",
    )
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
    environ, env_errors = _runtime_env_with_optional_file(os.environ, args.env_file)
    if args.dry_run_env_check:
        errors = env_errors + validate_runtime_env(environ, dialog_transcript_use=args.dialog_transcript_use)
        print(_safe_json(_env_check_report(errors, dialog_transcript_use=args.dialog_transcript_use)))
        return 0 if not errors else 2
    if args.audio is None:
        print(_safe_json(_audio_report("missing_audio", {}, ["--audio is required"])))
        return 2

    errors = env_errors + validate_runtime_env(environ, dialog_transcript_use=args.dialog_transcript_use)
    if errors:
        print(
            _safe_json(
                {
                    "ok": False,
                    "manual_only": True,
                    "state_changing": False,
                    "missing_required_flags": errors,
                    "secret_values_printed": False,
                    "raw_env_values_printed": False,
                    "shell_environment_dump_printed": False,
                    "gateway_request_sent": False,
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

    with _temporary_environ(environ):
        return gateway_adapter_smoke.main(["--audio", str(args.audio), "--require-explicit-flags"])


def _env_present(environ: Mapping[str, str], name: str) -> bool:
    value = environ.get(name)
    return bool(value and value.strip())


def _env_bool(environ: Mapping[str, str], name: str, *, default: bool = False) -> bool:
    value = environ.get(name)
    if value is None:
        return default
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
        "raw_env_values_printed": False,
        "shell_environment_dump_printed": False,
        "gateway_request_sent": False,
        "transcript_text_logged": False,
        "transcript_used_for_dialog": False,
        "business_dialog_unchanged": True,
    }


def _env_check_report(errors: list[str], *, dialog_transcript_use: str) -> dict[str, object]:
    return {
        "ok": not errors,
        "action": "dry_run_env_check",
        "dialog_transcript_use": dialog_transcript_use,
        "missing_required_flags": errors,
        "secret_values_printed": False,
        "raw_env_values_printed": False,
        "shell_environment_dump_printed": False,
        "gateway_request_sent": False,
        "transcript_text_logged": False,
        "transcript_delta_logged": False,
    }


def _runtime_env_with_optional_file(
    base_environ: Mapping[str, str],
    env_file: Path | None,
) -> tuple[dict[str, str], list[str]]:
    environ = dict(base_environ)
    if env_file is None:
        return environ, []
    parsed, errors = parse_env_file(env_file)
    environ.update(parsed)
    return environ, errors


class _temporary_environ:
    def __init__(self, values: Mapping[str, str]) -> None:
        self._values = dict(values)
        self._previous: dict[str, str | None] = {}

    def __enter__(self) -> None:
        keys = set(SMOKE_ENV_KEYS) | {"OPENAI_API_KEY"}
        for key in keys:
            self._previous[key] = os.environ.get(key)
            if key in self._values:
                os.environ[key] = self._values[key]
            elif key in os.environ:
                del os.environ[key]

    def __exit__(self, *_exc: object) -> None:
        for key, value in self._previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _safe_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
