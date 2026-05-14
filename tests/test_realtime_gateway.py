"""Tests for the NODE-021 supported-region gateway measurement path."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import wave
import math
import struct

from fastapi.testclient import TestClient

from ai_secretary.stt import realtime_gateway
from ai_secretary.stt.realtime_gateway import GatewaySettings, create_app, run_gateway_realtime_measurement
from ai_secretary.stt.realtime_measurement import (
    GatewayMeasurementClientConfig,
    gateway_config_from_args_and_env,
    run_gateway_measurement,
)


def _pcm_wav_bytes(path: Path, *, sample_rate: int = 24000, frames: int = 4800) -> bytes:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)
    return path.read_bytes()


def _tone_wav_bytes(path: Path, *, sample_rate: int = 24000, frames: int = 4800) -> bytes:
    samples = []
    for index in range(frames):
        value = int(8000 * math.sin(2 * math.pi * 440 * index / sample_rate))
        samples.append(struct.pack("<h", value))
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"".join(samples))
    return path.read_bytes()


class _FakeWebSocket:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = [json.dumps(response) for response in responses]
        self.sent: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    async def recv(self) -> str:
        return self.responses.pop(0)


def _settings(**overrides) -> GatewaySettings:
    values = {
        "openai_api_key": "openai-test-gateway-secret",
        "gateway_token": "gateway-test-token",
        "gateway_region_label": "test-region",
    }
    values.update(overrides)
    return GatewaySettings(**values)


def test_missing_gateway_token_rejected_without_openai_attempt() -> None:
    app = create_app(_settings(openai_api_key="sk-secret-not-returned"))
    client = TestClient(app)

    response = client.post(realtime_gateway.GATEWAY_ENDPOINT, content=b"not-a-wav")

    assert response.status_code == 401
    payload = response.json()
    assert payload["ok"] is False
    assert payload["error_code"] == "gateway_auth_failed"
    assert "sk-secret-not-returned" not in response.text


def test_openai_key_missing_on_gateway_fails_clearly(tmp_path: Path) -> None:
    audio = _pcm_wav_bytes(tmp_path / "audio.wav")

    status, payload = asyncio.run(
        run_gateway_realtime_measurement(audio, settings=_settings(openai_api_key=""), request_id="req_missing_key")
    )

    assert status == 503
    assert payload["gateway_request_id"] == "req_missing_key"
    assert payload["error_code"] == "missing_openai_api_key"
    assert payload["chunks_sent"] == 0
    assert payload["cleanup_done"] is True


def test_gateway_secret_redaction() -> None:
    payload = realtime_gateway.build_gateway_response(
        request_id="req_redact",
        settings=_settings(),
        status=502,
        error_type="RuntimeError",
        error_code="openai_auth_failed",
        error_message_redacted="Authorization: Bearer sk-secret123456 failed",
    )

    serialized = json.dumps(payload)
    assert "sk-secret123456" not in serialized
    assert "[REDACTED]" in serialized


def test_gateway_does_not_return_transcript_by_default(tmp_path: Path) -> None:
    audio = _pcm_wav_bytes(tmp_path / "audio.wav")
    fake_ws = _FakeWebSocket(
        [
            {"type": "session.created"},
            {"type": "session.updated"},
            {"type": "conversation.item.input_audio_transcription.delta", "delta": "сек"},
            {"type": "conversation.item.input_audio_transcription.completed", "transcript": "секретный текст"},
        ]
    )

    async def _connector(_url: str, _headers: dict[str, str]) -> _FakeWebSocket:
        return fake_ws

    status, payload = asyncio.run(
        run_gateway_realtime_measurement(
            audio,
            settings=_settings(allow_return_transcript=False),
            request_id="req_no_text",
            return_transcript=True,
            connector=_connector,
        )
    )

    assert status == 200
    assert payload["transcript_text_present"] is True
    assert "transcript_text" not in payload
    assert "секретный текст" not in json.dumps(payload, ensure_ascii=False)
    assert any(message["type"] == "input_audio_buffer.append" for message in fake_ws.sent)


def test_gateway_response_includes_audio_and_event_diagnostics(tmp_path: Path) -> None:
    audio = _tone_wav_bytes(tmp_path / "tone.wav")
    fake_ws = _FakeWebSocket(
        [
            {"type": "session.created"},
            {"type": "session.updated"},
            {"type": "conversation.item.input_audio_transcription.delta", "delta": "pri"},
            {"type": "conversation.item.input_audio_transcription.completed", "transcript": "privet"},
        ]
    )

    async def _connector(_url: str, _headers: dict[str, str]) -> _FakeWebSocket:
        return fake_ws

    status, payload = asyncio.run(
        run_gateway_realtime_measurement(
            audio,
            settings=_settings(),
            request_id="req_diag",
            connector=_connector,
        )
    )

    assert status == 200
    assert payload["audio_payload_valid"] is True
    assert payload["audio_duration_ms"] == 200
    assert payload["audio_sample_rate_hz"] == 24000
    assert payload["audio_channels"] == 1
    assert payload["audio_sample_width"] == 2
    assert payload["audio_total_bytes"] == len(audio)
    assert payload["audio_chunk_count"] == 1
    assert payload["audio_rms"] > 100
    assert payload["audio_peak"] > 500
    assert payload["audio_non_silent_ratio"] > 0.02
    assert payload["audio_quality_classification"] == "too_short"
    assert payload["openai_event_type_counts"]["session.created"] == 1
    assert payload["openai_event_type_counts"]["session.updated"] == 1
    assert payload["openai_event_type_counts"]["conversation.item.input_audio_transcription.completed"] == 1
    assert payload["transcript_event_seen"] is True
    assert payload["input_audio_buffer_commit_sent"] is True
    assert payload["timeout_observed"] is False


def test_gateway_audio_diagnostics_classify_silence(tmp_path: Path) -> None:
    audio = _pcm_wav_bytes(tmp_path / "silence.wav", frames=24000)
    fake_ws = _FakeWebSocket(
        [
            {"type": "session.created"},
            {"type": "session.updated"},
            {"type": "conversation.item.input_audio_transcription.completed", "transcript": ""},
        ]
    )

    async def _connector(_url: str, _headers: dict[str, str]) -> _FakeWebSocket:
        return fake_ws

    status, payload = asyncio.run(
        run_gateway_realtime_measurement(audio, settings=_settings(), request_id="req_silent", connector=_connector)
    )

    assert status == 200
    assert payload["audio_duration_ms"] == 1000
    assert payload["audio_rms"] == 0
    assert payload["audio_peak"] == 0
    assert payload["audio_non_silent_ratio"] == 0
    assert payload["audio_quality_classification"] == "near_silent"
    assert payload["transcript_event_seen"] is True
    assert payload["transcript_text_present"] is False


def test_gateway_request_schema_rejects_invalid_wav() -> None:
    status, payload = asyncio.run(
        run_gateway_realtime_measurement(b"not-a-wav", settings=_settings(), request_id="req_bad_wav")
    )

    assert status == 400
    assert payload["error_type"] == "gateway_audio_invalid"
    assert payload["error_code"] == "invalid_wav"
    assert payload["chunks_sent"] == 0


def test_openai_failure_maps_to_structured_gateway_error(tmp_path: Path) -> None:
    audio = _pcm_wav_bytes(tmp_path / "audio.wav")
    fake_key = "sk-regionsecret123"
    fake_ws = _FakeWebSocket(
        [
            {
                "type": "error",
                "error": {
                    "code": "unsupported_country_region_territory",
                    "message": f"blocked {fake_key}",
                },
            }
        ]
    )

    async def _connector(_url: str, _headers: dict[str, str]) -> _FakeWebSocket:
        return fake_ws

    status, payload = asyncio.run(
        run_gateway_realtime_measurement(
            audio,
            settings=_settings(openai_api_key=fake_key),
            request_id="req_region",
            connector=_connector,
        )
    )

    assert status == 502
    assert payload["error_code"] == "openai_region_rejected"
    assert payload["openai_realtime_connection_ok"] is True
    assert payload["openai_session_created"] is False
    assert fake_key not in json.dumps(payload)


def test_gateway_client_mode_does_not_require_openai_api_key(tmp_path: Path) -> None:
    audio_path = tmp_path / "audio.wav"
    _pcm_wav_bytes(audio_path)
    lines: list[str] = []

    async def _post(config: GatewayMeasurementClientConfig, audio: bytes) -> tuple[int, dict]:
        assert config.gateway_token == "gateway-token"
        assert audio
        return 200, {"ok": True, "gateway_request_id": "gw_client", "chunks_sent": 1}

    config = GatewayMeasurementClientConfig(
        gateway_url="https://gateway.example.test/v1/stt/realtime-measurement",
        gateway_token="gateway-token",
        audio_path=audio_path,
    )

    result = asyncio.run(run_gateway_measurement(config, post=_post, writer=lines.append))

    assert result.ok is True
    assert result.error is None
    assert "OPENAI_API_KEY" not in "\n".join(lines)


def test_gateway_config_reads_gateway_env_not_openai_key(tmp_path: Path) -> None:
    audio_path = tmp_path / "audio.wav"
    _pcm_wav_bytes(audio_path)
    config = gateway_config_from_args_and_env(
        ["--audio", str(audio_path)],
        {
            "REALTIME_GATEWAY_URL": "https://gateway.example.test/v1/stt/realtime-measurement",
            "REALTIME_GATEWAY_TOKEN": "gateway-token",
            "OPENAI_API_KEY": "must-not-be-read",
        },
    )

    assert config.gateway_url == "https://gateway.example.test/v1/stt/realtime-measurement"
    assert config.gateway_token == "gateway-token"
    assert not hasattr(config, "api_key")


def test_gateway_module_has_no_business_dialog_side_effects() -> None:
    source = Path(realtime_gateway.__file__).read_text(encoding="utf-8")

    assert "ai_secretary.telephony" not in source
    assert "apply_turn" not in source
    assert "CallSession" not in source
