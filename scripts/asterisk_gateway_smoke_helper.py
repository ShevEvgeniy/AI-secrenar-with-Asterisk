"""Manual Asterisk-side gateway smoke wrapper.

This script is intentionally one-shot only. It validates the runtime boundary,
then delegates to ai_secretary.stt.gateway_adapter_smoke with transcript logging
disabled and business-dialog transcript use disabled.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ai_secretary.stt import gateway_adapter_smoke  # noqa: E402


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one manual Asterisk-side gateway smoke without business-dialog transcript use."
    )
    parser.add_argument("--audio", required=True, type=Path, help="Path to the operator-approved smoke WAV file.")
    args = parser.parse_args(argv)

    errors = validate_runtime_env(os.environ)
    if errors:
        print(
            json.dumps(
                {
                    "ok": False,
                    "manual_only": True,
                    "state_changing": False,
                    "missing_required_flags": errors,
                    "secret_values_printed": False,
                    "transcript_text_logged": False,
                    "business_dialog_unchanged": True,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
