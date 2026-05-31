from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import wave


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "asterisk_gateway_smoke_helper.py"


def _load_helper():
    spec = importlib.util.spec_from_file_location("asterisk_gateway_smoke_helper", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_helper_fails_closed_without_runtime_env(tmp_path: Path, monkeypatch, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    audio_path.write_bytes(b"fake-wav")
    for name in (
        "STT_GATEWAY_STT_ENABLED",
        "STT_GATEWAY_ADAPTER_ENABLED",
        "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG",
        "STT_GATEWAY_URL",
        "REALTIME_GATEWAY_URL",
        "STT_GATEWAY_TOKEN",
        "REALTIME_GATEWAY_TOKEN",
        "STT_GATEWAY_LOG_TRANSCRIPT",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    code = helper.main(["--audio", str(audio_path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert payload["manual_only"] is True
    assert payload["state_changing"] is False
    assert payload["secret_values_printed"] is False
    assert payload["transcript_text_logged"] is False
    assert payload["business_dialog_unchanged"] is True
    assert "STT_GATEWAY_URL or REALTIME_GATEWAY_URL" in payload["missing_required_flags"]


def test_helper_refuses_asterisk_openai_key_without_printing_value(tmp_path: Path, monkeypatch, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    audio_path.write_bytes(b"fake-wav")
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.setenv("OPENAI_API_KEY", "not-real-openai-key")

    code = helper.main(["--audio", str(audio_path)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 2
    assert "OPENAI_API_KEY must be absent on Asterisk" in payload["missing_required_flags"]
    assert "not-real-openai-key" not in output


def test_helper_refuses_newline_material_without_printing_token(tmp_path: Path, monkeypatch, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    audio_path.write_bytes(b"fake-wav")
    bad_token = "fake-token\\nSTT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG=true"
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", bad_token)
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    code = helper.main(["--audio", str(audio_path)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 2
    assert "STT_GATEWAY_TOKEN must not contain newline material" in payload["missing_required_flags"]
    assert bad_token not in output


def test_helper_requires_business_dialog_transcript_use_to_stay_false(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    audio_path.write_bytes(b"fake-wav")
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "true")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    code = helper.main(["--audio", str(audio_path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG must remain false" in payload["missing_required_flags"]


def test_helper_delegates_to_existing_smoke_module_when_safe(tmp_path: Path, monkeypatch) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    helper.create_smoke_wav(audio_path)
    calls: list[list[str]] = []
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(helper.gateway_adapter_smoke, "main", lambda argv: calls.append(argv) or 0)

    code = helper.main(["--audio", str(audio_path)])

    assert code == 0
    assert calls == [["--audio", str(audio_path), "--require-explicit-flags"]]


def test_helper_creates_24khz_mono_16bit_pcm_smoke_audio(tmp_path: Path, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"

    code = helper.main(["--create-smoke-audio", str(audio_path)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 0
    assert payload["ok"] is True
    assert payload["secret_values_printed"] is False
    assert payload["transcript_text_logged"] is False
    with wave.open(str(audio_path), "rb") as handle:
        assert handle.getframerate() == 24000
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getcomptype() == "NONE"
        assert handle.getnframes() > 0


def test_helper_validates_audio_with_safe_json_only(tmp_path: Path, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "smoke.wav"
    helper.create_smoke_wav(audio_path)

    code = helper.main(["--validate-smoke-audio", str(audio_path)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert code == 0
    assert payload["ok"] is True
    assert payload["audio"]["sample_rate_hz"] == 24000
    assert payload["audio"]["channels"] == 1
    assert payload["audio"]["sample_width_bytes"] == 2
    assert payload["secret_values_printed"] is False
    assert payload["transcript_text_logged"] is False


def test_helper_rejects_16000_hz_audio_before_gateway_request(tmp_path: Path, monkeypatch, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "bad.wav"
    with wave.open(str(audio_path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * 16000)
    calls: list[list[str]] = []
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(helper.gateway_adapter_smoke, "main", lambda argv: calls.append(argv) or 0)

    code = helper.main(["--audio", str(audio_path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["ok"] is False
    assert payload["audio"]["sample_rate_hz"] == 16000
    assert "audio sample rate must be 24000 Hz" in payload["audio_format_errors"]
    assert payload["secret_values_printed"] is False
    assert payload["transcript_text_logged"] is False
    assert calls == []


def test_helper_rejects_stereo_audio_before_gateway_request(tmp_path: Path, monkeypatch, capsys) -> None:
    helper = _load_helper()
    audio_path = tmp_path / "stereo.wav"
    with wave.open(str(audio_path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(b"\x00\x00\x00\x00" * 24000)
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://gateway.example.test:8080")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    code = helper.main(["--audio", str(audio_path)])

    payload = json.loads(capsys.readouterr().out)
    assert code == 2
    assert payload["audio"]["channels"] == 2
    assert "audio channels must be mono" in payload["audio_format_errors"]
