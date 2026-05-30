"""Create, validate, and clean up a secret-safe gateway smoke env file.

The script is intended for one-shot Asterisk-side smoke helper bundles. It reads
the gateway token from stdin, rejects malformed values, and prints only safe
presence/status flags.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Mapping


REQUIRED_KEYS = (
    "STT_GATEWAY_STT_ENABLED",
    "STT_GATEWAY_ADAPTER_ENABLED",
    "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG",
    "STT_GATEWAY_LOG_TRANSCRIPT",
    "STT_GATEWAY_URL",
    "STT_GATEWAY_TOKEN",
)
TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9._~+=:@/-]{16,512}$")


def build_env(gateway_url: str, gateway_token: str) -> dict[str, str]:
    """Return the future smoke env after fail-closed validation."""
    errors = validate_secret_value("STT_GATEWAY_TOKEN", gateway_token)
    errors.extend(validate_plain_value("STT_GATEWAY_URL", gateway_url))
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "STT_GATEWAY_STT_ENABLED": "true",
        "STT_GATEWAY_ADAPTER_ENABLED": "true",
        "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG": "false",
        "STT_GATEWAY_LOG_TRANSCRIPT": "false",
        "STT_GATEWAY_URL": gateway_url,
        "STT_GATEWAY_TOKEN": gateway_token,
    }


def materialize_env(path: Path, env: Mapping[str, str]) -> None:
    """Write env atomically with owner-readable permissions only."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={env[key]}" for key in REQUIRED_KEYS]
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("\n".join(lines))
            handle.write("\n")
        os.chmod(tmp_path, 0o600)
        os.replace(tmp_path, path)
        os.chmod(path, 0o600)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def validate_env_file(path: Path) -> list[str]:
    """Validate shape and required flags without returning secret values."""
    if not path.exists():
        return ["env file missing"]
    parsed: dict[str, str] = {}
    duplicates: set[str] = set()
    for line_no, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line or raw_line.startswith("#"):
            continue
        if "=" not in raw_line:
            return [f"line {line_no} is not KEY=VALUE"]
        key, value = raw_line.split("=", 1)
        if key in parsed:
            duplicates.add(key)
        parsed[key] = value
    errors: list[str] = []
    if duplicates:
        errors.append("duplicate keys present")
    for key in REQUIRED_KEYS:
        if key not in parsed or not parsed[key].strip():
            errors.append(f"{key} missing")
    if parsed.get("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG") != "false":
        errors.append("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must be false")
    if parsed.get("STT_GATEWAY_LOG_TRANSCRIPT") != "false":
        errors.append("STT_GATEWAY_LOG_TRANSCRIPT must be false")
    if parsed.get("STT_GATEWAY_STT_ENABLED") != "true" and parsed.get("STT_GATEWAY_ADAPTER_ENABLED") != "true":
        errors.append("gateway adapter must be enabled explicitly")
    for key, value in parsed.items():
        validator = validate_secret_value if key.endswith("TOKEN") else validate_plain_value
        errors.extend(validator(key, value))
    return errors


def cleanup_env(path: Path) -> bool:
    if path.exists():
        path.unlink()
        return True
    return False


def read_token_from_stdin() -> str:
    raw = sys.stdin.read()
    token = raw.rstrip("\r\n")
    if "\r" in token or "\n" in token:
        raise ValueError("STT_GATEWAY_TOKEN contains newline characters")
    return token


def validate_secret_value(name: str, value: str) -> list[str]:
    errors = validate_plain_value(name, value)
    if value and not TOKEN_PATTERN.fullmatch(value):
        errors.append(f"{name} has invalid characters or length")
    return errors


def validate_plain_value(name: str, value: str) -> list[str]:
    errors: list[str] = []
    if not value or not value.strip():
        errors.append(f"{name} missing")
    if "\r" in value or "\n" in value or "\\r" in value or "\\n" in value:
        errors.append(f"{name} contains newline material")
    if any(ord(ch) < 32 for ch in value):
        errors.append(f"{name} contains control characters")
    return errors


def _safe_report(**extra: object) -> str:
    payload = {
        "ok": extra.pop("ok"),
        "secret_values_printed": False,
        "transcript_text_logged": False,
        **extra,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage a one-shot gateway smoke temp env without printing secrets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a temp env from a token read on stdin.")
    create.add_argument("--output", required=True, type=Path)
    create.add_argument("--gateway-url", required=True)

    validate = subparsers.add_parser("validate", help="Validate a temp env without printing values.")
    validate.add_argument("--path", required=True, type=Path)

    cleanup = subparsers.add_parser("cleanup", help="Remove a temp env.")
    cleanup.add_argument("--path", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "create":
        try:
            token = read_token_from_stdin()
            env = build_env(args.gateway_url, token)
            materialize_env(args.output, env)
            errors = validate_env_file(args.output)
        except Exception as exc:
            print(_safe_report(ok=False, action="create", error=str(exc)))
            return 2
        print(
            _safe_report(
                ok=not errors,
                action="create",
                env_written=not errors,
                token_present_masked=not errors,
                errors=errors,
            )
        )
        return 0 if not errors else 2
    if args.command == "validate":
        errors = validate_env_file(args.path)
        print(
            _safe_report(
                ok=not errors,
                action="validate",
                token_present_masked=not errors,
                required_keys_present=not errors,
                errors=errors,
            )
        )
        return 0 if not errors else 2
    removed = cleanup_env(args.path)
    print(_safe_report(ok=True, action="cleanup", removed=removed, path_absent=not args.path.exists()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
