"""Tests for the disabled-by-default gateway STT adapter."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

from ai_secretary.stt.gateway_adapter import GatewaySttAdapterConfig, config_from_env, transcribe_via_gateway
from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, DialogStage


def _write_audio(path: Path) -> Path:
    path.write_bytes(b"test-audio")
    return path


def _artifact(path: Path) -> ari_app.TranscriptionArtifact:
    return ari_app.TranscriptionArtifact(
        call_id="call-gateway",
        channel_id="ch-gateway",
        stage=DialogStage.NAME,
        turn_idx=1,
        record_name="call-gateway_name_utt1",
        path=path,
        size_bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _settings(tmp_path: Path) -> object:
    return type(
        "Settings",
        (),
        {
            "openai_api_key": "",
            "ari_url": "http://127.0.0.1:8088/ari",
            "demo_mode": "real",
            "storage_dir": tmp_path,
        },
    )()


def _events(session: CallSession) -> list[dict]:
    return [json.loads(line) for line in session.events_path.read_text(encoding="utf-8").splitlines()]


def test_config_is_disabled_by_default() -> None:
    config = config_from_env({})

    assert config.enabled is False
    assert config.use_transcript_for_dialog is False
    assert config.gateway_url == ""
    assert config.gateway_token == ""
    assert config.timeout_ms == 10_000
    assert config.max_retries == 0
    assert config.log_transcript is False


def test_disabled_adapter_makes_no_gateway_call(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise AssertionError("disabled adapter must not call gateway")

    result = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(enabled=False),
            post=_post,
        )
    )

    assert result.attempted is False
    assert result.accepted is False
    assert result.reason == "gateway_stt_disabled"


def test_missing_gateway_url_or_token_falls_back_without_call(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise AssertionError("incomplete config must not call gateway")

    missing_url = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_token="token",
            ),
            post=_post,
        )
    )
    missing_token = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_url="https://gateway.example.test",
            ),
            post=_post,
        )
    )

    assert missing_url.reason == "missing_gateway_url"
    assert missing_token.reason == "missing_gateway_token"
    assert missing_url.accepted is False
    assert missing_token.accepted is False


def test_gateway_failures_fall_back_safely(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    config = GatewaySttAdapterConfig(
        enabled=True,
        use_transcript_for_dialog=True,
        gateway_url="https://gateway.example.test",
        gateway_token="gateway-token",
    )

    async def _auth_failed(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 401, {"ok": False, "error_type": "gateway_auth_failed", "transcript_text": "secret text"}

    async def _timeout(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise TimeoutError("timed out")

    async def _unavailable(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise OSError("connection refused")

    async def _malformed(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {"unexpected": True}

    async def _empty(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {"ok": True, "transcript_text_present": False}

    cases = [
        (_auth_failed, "gateway_auth_failed"),
        (_timeout, "gateway_timeout"),
        (_unavailable, "gateway_unavailable"),
        (_malformed, "malformed_response"),
        (_empty, "empty_transcript"),
    ]

    for post, reason in cases:
        result = asyncio.run(transcribe_via_gateway(audio_path, config=config, post=post))
        assert result.attempted is True
        assert result.accepted is False
        assert result.reason == reason
        assert result.text == ""


def test_transcript_text_not_logged_by_default(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    lines: list[dict] = []

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {
            "ok": True,
            "gateway_request_id": "gw_test",
            "transcript_text_present": True,
            "transcript_text": "секретный текст",
        }

    result = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_url="https://gateway.example.test",
                gateway_token="gateway-token",
                log_transcript=False,
            ),
            post=_post,
            log_event=lambda action, status, reason, details: lines.append(
                {"action": action, "status": status, "reason": reason, "details": details}
            ),
        )
    )

    serialized_logs = json.dumps(lines, ensure_ascii=False)
    assert result.accepted is True
    assert result.text == "секретный текст"
    assert "секретный текст" not in serialized_logs
    assert result.details["transcript_text_logged"] is False


def test_business_transcription_path_keeps_gateway_disabled_by_default(monkeypatch, tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "turn_name.wav")
    session = CallSession(call_id="call-default", channel_id="ch-default", artifact_dir=tmp_path / "artifacts")

    async def _gateway_call(*_args, **_kwargs):
        raise AssertionError("default business path must not call gateway")

    monkeypatch.setattr(ari_app, "transcribe_via_gateway", _gateway_call)
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "batch text")
    monkeypatch.delenv("STT_GATEWAY_STT_ENABLED", raising=False)
    monkeypatch.delenv("STT_GATEWAY_ADAPTER_ENABLED", raising=False)

    text, details = asyncio.run(
        ari_app._transcribe_audio_artifact_experimental(
            _settings(tmp_path),
            session,
            _artifact(audio_path),
        )
    )

    assert text == "batch text"
    assert details["stt_streaming_enabled"] is False
    assert not any(event["action"].startswith("gateway_stt_") for event in _events(session))
