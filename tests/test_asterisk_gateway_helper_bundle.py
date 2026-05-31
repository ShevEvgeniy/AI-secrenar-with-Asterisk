from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "asterisk_gateway_helper_bundle.py"


def _load_bundle_helper():
    spec = importlib.util.spec_from_file_location("asterisk_gateway_helper_bundle", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bundle_create_includes_required_import_dependencies(tmp_path: Path) -> None:
    helper = _load_bundle_helper()
    bundle_root = tmp_path / "bundle"

    report = helper.create_bundle(bundle_root)

    assert report["ok"] is True
    assert (bundle_root / "src/ai_secretary/config/__init__.py").is_file()
    assert (bundle_root / "src/ai_secretary/config/settings.py").is_file()
    assert (bundle_root / "src/ai_secretary/stt/gateway_adapter_smoke.py").is_file()
    assert (bundle_root / "scripts/gateway_smoke_temp_env_guard.py").is_file()


def test_bundle_preflight_validates_complete_bundle(tmp_path: Path) -> None:
    helper = _load_bundle_helper()
    bundle_root = tmp_path / "bundle"
    helper.create_bundle(bundle_root)

    report = helper.validate_bundle(bundle_root)

    assert report["ok"] is True
    assert report["required_files_present"] is True
    assert report["runtime_modules_ok"] is True
    assert report["missing_runtime_modules"] == []
    assert report["preflight_import_ok"] is True
    assert report["secret_values_printed"] is False
    assert report["transcript_text_logged"] is False


def test_bundle_preflight_catches_missing_ai_secretary_config(tmp_path: Path) -> None:
    helper = _load_bundle_helper()
    bundle_root = tmp_path / "bundle"
    helper.create_bundle(bundle_root)
    shutil.rmtree(bundle_root / "src/ai_secretary/config")

    report = helper.validate_bundle(bundle_root)

    assert report["ok"] is False
    assert report["preflight_import_ok"] is False
    assert report["preflight_error_type"] == "ModuleNotFoundError"
    assert report["preflight_missing_module"] == "ai_secretary.config"
    assert "src/ai_secretary/config/settings.py" in report["missing_files"]


def test_runtime_dependency_manifest_includes_httpx() -> None:
    helper = _load_bundle_helper()

    report = helper.manifest()

    assert "httpx" in report["runtime_modules"]
    assert "fastapi" in report["runtime_modules"]
    assert "websockets" in report["runtime_modules"]
    assert report["secret_values_printed"] is False


def test_bundle_preflight_fails_closed_when_httpx_missing(tmp_path: Path, monkeypatch) -> None:
    helper = _load_bundle_helper()
    bundle_root = tmp_path / "bundle"
    helper.create_bundle(bundle_root)
    monkeypatch.setattr(helper, "RUNTIME_MODULES", ("httpx",))

    def missing_runtime_modules() -> dict[str, object]:
        return {"ok": False, "missing_modules": ["httpx"]}

    monkeypatch.setattr(helper, "_preflight_runtime_modules", missing_runtime_modules)

    report = helper.validate_bundle(bundle_root)

    assert report["ok"] is False
    assert report["runtime_modules_ok"] is False
    assert report["missing_runtime_modules"] == ["httpx"]
    assert report["preflight_import_ok"] is False
    assert report["preflight_missing_module"] == "httpx"
    assert report["secret_values_printed"] is False
    assert report["transcript_text_logged"] is False


def test_bundle_reports_do_not_print_token_values(tmp_path: Path, capsys) -> None:
    helper = _load_bundle_helper()
    bundle_root = tmp_path / "bundle"
    token_value = "gateway-token-that-must-not-appear"

    code = helper.main(["create", "--output", str(bundle_root)])
    output = capsys.readouterr().out
    payload = json.loads(output)

    assert code == 0
    assert payload["secret_values_printed"] is False
    assert token_value not in output


def test_manifest_keeps_safe_temp_env_guard_required() -> None:
    helper = _load_bundle_helper()

    report = helper.manifest()

    assert "scripts/gateway_smoke_temp_env_guard.py" in report["bundle_files"]
    assert "scripts/asterisk_gateway_smoke_helper.py" in report["bundle_files"]
    assert "httpx" in report["runtime_modules"]
    assert report["secret_values_printed"] is False
    assert report["transcript_text_logged"] is False
