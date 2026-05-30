from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "gateway_smoke_temp_env_guard.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("gateway_smoke_temp_env_guard", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_create_valid_temp_env_without_printing_token(tmp_path: Path, monkeypatch, capsys) -> None:
    guard = _load_guard()
    output_path = tmp_path / "gateway-client.env"
    token = "a" * 32
    monkeypatch.setattr(sys, "stdin", _StringInput(token + "\n"))

    code = guard.main(["create", "--output", str(output_path), "--gateway-url", "http://45.61.48.199:8080"])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 0
    assert payload["ok"] is True
    assert payload["token_present_masked"] is True
    assert payload["secret_values_printed"] is False
    assert token not in output
    content = output_path.read_text(encoding="utf-8")
    assert "STT_GATEWAY_TOKEN=" + token in content
    assert "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false" in content
    assert "STT_GATEWAY_LOG_TRANSCRIPT=false" in content


def test_create_missing_token_fails_closed_without_value(tmp_path: Path, monkeypatch, capsys) -> None:
    guard = _load_guard()
    monkeypatch.setattr(sys, "stdin", _StringInput("\n"))

    code = guard.main(["create", "--output", str(tmp_path / "env"), "--gateway-url", "http://gateway.example"])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 2
    assert payload["ok"] is False
    assert payload["secret_values_printed"] is False
    assert "STT_GATEWAY_TOKEN" in payload["error"]


def test_create_rejects_multiline_token_without_printing_value(tmp_path: Path, monkeypatch, capsys) -> None:
    guard = _load_guard()
    bad_token = "a" * 32 + "\n" + "b" * 32
    monkeypatch.setattr(sys, "stdin", _StringInput(bad_token + "\n"))

    code = guard.main(["create", "--output", str(tmp_path / "env"), "--gateway-url", "http://gateway.example"])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 2
    assert payload["ok"] is False
    assert "newline" in payload["error"]
    assert "a" * 32 not in output
    assert "b" * 32 not in output


def test_validate_detects_malformed_literal_newline_material(tmp_path: Path, capsys) -> None:
    guard = _load_guard()
    path = tmp_path / "gateway-client.env"
    path.write_text(
        "\n".join(
            [
                "STT_GATEWAY_STT_ENABLED=true",
                "STT_GATEWAY_ADAPTER_ENABLED=true",
                "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=false",
                "STT_GATEWAY_LOG_TRANSCRIPT=false",
                "STT_GATEWAY_URL=http://45.61.48.199:8080",
                "STT_GATEWAY_TOKEN=aaaaaaaaaaaaaaaa\\nSTT_GATEWAY_LOG_TRANSCRIPT=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    code = guard.main(["validate", "--path", str(path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert "STT_GATEWAY_TOKEN contains newline material" in payload["errors"]


def test_validate_requires_dialog_transcript_use_false(tmp_path: Path, capsys) -> None:
    guard = _load_guard()
    path = tmp_path / "gateway-client.env"
    env = guard.build_env("http://45.61.48.199:8080", "a" * 32)
    env["STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG"] = "true"
    guard.materialize_env(path, env)

    code = guard.main(["validate", "--path", str(path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must be false" in payload["errors"]


def test_cleanup_removes_temp_env(tmp_path: Path, capsys) -> None:
    guard = _load_guard()
    path = tmp_path / "gateway-client.env"
    guard.materialize_env(path, guard.build_env("http://45.61.48.199:8080", "a" * 32))

    code = guard.main(["cleanup", "--path", str(path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["removed"] is True
    assert payload["path_absent"] is True
    assert not path.exists()


class _StringInput:
    def __init__(self, value: str) -> None:
        self.value = value

    def read(self) -> str:
        return self.value
