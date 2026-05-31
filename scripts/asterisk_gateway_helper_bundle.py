"""Build and preflight the one-shot Asterisk gateway smoke helper bundle.

The bundle is intentionally small and contains only repo source needed by the
manual smoke helper plus the newline-safe temp-env guard. It does not read,
write, or print runtime secret values.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]

BUNDLE_FILES = (
    "scripts/asterisk_gateway_smoke_helper.py",
    "scripts/gateway_smoke_temp_env_guard.py",
    "src/ai_secretary/__init__.py",
    "src/ai_secretary/config/__init__.py",
    "src/ai_secretary/config/settings.py",
    "src/ai_secretary/stt/__init__.py",
    "src/ai_secretary/stt/gateway_adapter.py",
    "src/ai_secretary/stt/gateway_adapter_smoke.py",
    "src/ai_secretary/stt/realtime_gateway.py",
    "src/ai_secretary/stt/realtime_measurement.py",
)

RUNTIME_MODULES = (
    "httpx",
    "fastapi",
    "websockets",
)

SECRET_PATTERNS = (
    re.compile(r"OPENAI_API_KEY=.*[A-Za-z0-9_-]{12,}"),
    re.compile(r"GATEWAY_TOKEN=.*[A-Za-z0-9_-]{12,}"),
    re.compile(r"STT_GATEWAY_TOKEN=.*[A-Za-z0-9_-]{12,}"),
    re.compile(r"REALTIME_GATEWAY_TOKEN=.*[A-Za-z0-9_-]{12,}"),
    re.compile(r"Bearer [A-Za-z0-9._*-]{12,}"),
    re.compile(r"sk-[A-Za-z0-9*-]{20,}"),
)


def create_bundle(output_dir: Path, *, source_root: Path = REPO_ROOT) -> dict[str, object]:
    """Copy the minimal smoke helper bundle into ``output_dir``."""
    copied: list[str] = []
    for relative in BUNDLE_FILES:
        source = source_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"bundle source missing: {relative}")
        target = output_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied.append(relative)
    return {
        "ok": True,
        "action": "create",
        "files_copied": copied,
        "secret_values_printed": False,
        "transcript_text_logged": False,
    }


def validate_bundle(bundle_root: Path) -> dict[str, object]:
    """Validate manifest files, import completeness, and secret hygiene."""
    missing = [relative for relative in BUNDLE_FILES if not (bundle_root / relative).is_file()]
    secret_hits = _scan_bundle_for_secret_patterns(bundle_root)
    runtime_result = _preflight_runtime_modules()
    import_result = (
        _preflight_import(bundle_root)
        if not missing and runtime_result["ok"]
        else _blocked_import_result(missing, runtime_result)
    )
    errors: list[str] = []
    if missing:
        errors.append("manifest files missing")
    if secret_hits:
        errors.append("secret-like patterns found")
    if not runtime_result["ok"]:
        errors.append("runtime dependencies missing")
    if not import_result["ok"]:
        errors.append("preflight import failed")
    return {
        "ok": not errors,
        "action": "validate",
        "required_files_present": not missing,
        "missing_files": missing,
        "runtime_modules_required": list(RUNTIME_MODULES),
        "runtime_modules_ok": runtime_result["ok"],
        "missing_runtime_modules": runtime_result["missing_modules"],
        "preflight_import_ok": import_result["ok"],
        "preflight_error_type": import_result["error_type"],
        "preflight_missing_module": import_result["missing_module"],
        "secret_pattern_hits": secret_hits,
        "secret_values_printed": False,
        "transcript_text_logged": False,
        "errors": errors,
    }


def manifest() -> dict[str, object]:
    return {
        "ok": True,
        "action": "manifest",
        "bundle_files": list(BUNDLE_FILES),
        "runtime_modules": list(RUNTIME_MODULES),
        "secret_values_printed": False,
        "transcript_text_logged": False,
    }


def _scan_bundle_for_secret_patterns(bundle_root: Path) -> list[str]:
    hits: list[str] = []
    for relative in BUNDLE_FILES:
        path = bundle_root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(relative)
                break
    return sorted(set(hits))


def _preflight_import(bundle_root: Path) -> dict[str, object]:
    src_root = bundle_root / "src"
    code = (
        "import importlib, json, sys; "
        "sys.path.insert(0, r'" + str(src_root) + "'); "
        "importlib.import_module('ai_secretary.config.settings'); "
        "importlib.import_module('ai_secretary.stt.gateway_adapter_smoke'); "
        "print(json.dumps({'ok': True}))"
    )
    env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-I", "-c", code],
        cwd=str(bundle_root),
        env=env,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )
    if result.returncode == 0:
        return {"ok": True, "error_type": None, "missing_module": None}
    stderr = result.stderr or ""
    missing_module = _extract_missing_module(stderr)
    return {
        "ok": False,
        "error_type": "ModuleNotFoundError" if missing_module else "ImportError",
        "missing_module": missing_module,
    }


def _preflight_runtime_modules() -> dict[str, object]:
    missing = [module for module in RUNTIME_MODULES if importlib.util.find_spec(module) is None]
    return {
        "ok": not missing,
        "missing_modules": missing,
    }


def _blocked_import_result(missing: list[str], runtime_result: dict[str, object]) -> dict[str, object]:
    missing_module = "ai_secretary.config" if any(item.startswith("src/ai_secretary/config/") for item in missing) else None
    runtime_missing = runtime_result.get("missing_modules")
    if missing_module is None and isinstance(runtime_missing, list) and runtime_missing:
        missing_module = str(runtime_missing[0])
    return {
        "ok": False,
        "error_type": "ModuleNotFoundError" if missing_module else "ManifestIncomplete",
        "missing_module": missing_module,
    }


def _extract_missing_module(stderr: str) -> str | None:
    match = re.search(r"No module named '([^']+)'", stderr)
    if match:
        return match.group(1)
    return None


def _print_report(report: dict[str, object]) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or validate the secret-safe Asterisk smoke helper bundle.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("manifest", help="Print the expected bundle manifest.")
    create = subparsers.add_parser("create", help="Create a helper bundle from the local repo.")
    create.add_argument("--output", required=True, type=Path)
    validate = subparsers.add_parser("validate", help="Preflight an existing helper bundle.")
    validate.add_argument("--bundle-root", required=True, type=Path)

    args = parser.parse_args(argv)
    try:
        if args.command == "manifest":
            report = manifest()
        elif args.command == "create":
            report = create_bundle(args.output)
        else:
            report = validate_bundle(args.bundle_root)
    except Exception as exc:
        report = {
            "ok": False,
            "action": args.command,
            "error_type": type(exc).__name__,
            "secret_values_printed": False,
            "transcript_text_logged": False,
        }
    _print_report(report)
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
