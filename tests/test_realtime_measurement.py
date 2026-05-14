"""Tests for the standalone NODE-019 Realtime measurement path."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
import wave

from ai_secretary.stt import realtime_measurement
from ai_secretary.stt.realtime_measurement import (
    RealtimeMeasurementConfig,
    build_session_update,
    config_from_args_and_env,
    diagnose_pcm_wav_audio,
    redact_secrets,
    run_realtime_measurement,
)


def _write_pcm_wav(path: Path, *, sample_rate: int = 24000, frames: int = 4800) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)


def _events(lines: list[str]) -> list[dict]:
    return [json.loads(line) for line in lines]


def test_config_reads_openai_key_from_env_only(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    _write_pcm_wav(audio)

    fake_key = "openai-test-env-key"
    config = config_from_args_and_env(["--audio", str(audio)], {"OPENAI_API_KEY": fake_key})

    assert config.api_key == fake_key
    assert config.audio_path == audio


def test_missing_env_key_logs_error_without_connection(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    _write_pcm_wav(audio)
    lines: list[str] = []

    async def _connector(_url: str, _headers: dict[str, str]):
        raise AssertionError("missing key must not connect")

    result = asyncio.run(
        run_realtime_measurement(
            RealtimeMeasurementConfig(api_key="", audio_path=audio),
            connector=_connector,
            writer=lines.append,
        )
    )

    events = _events(lines)
    assert result.error == "missing_openai_api_key"
    assert events[0]["action"] == "realtime_error"
    assert events[0]["reason"] == "missing_openai_api_key"
    assert events[-1]["action"] == "realtime_cleanup_done"


def test_redact_secrets_in_nested_data() -> None:
    fake_bearer_key = "sk-" + "secret123456"
    fake_message_key = "sk-" + "anothersecret999"
    fake_field_key = "sk-" + "fieldsecret999"
    redacted = redact_secrets(
        {
            "Authorization": f"Bearer {fake_bearer_key}",
            "nested": {
                "message": f"failed with {fake_message_key}",
                "api_key": fake_field_key,
            },
        }
    )

    serialized = json.dumps(redacted)
    assert fake_bearer_key not in serialized
    assert fake_message_key not in serialized
    assert fake_field_key not in serialized
    assert "[REDACTED]" in serialized


def test_session_payload_matches_realtime_transcription_shape(tmp_path: Path) -> None:
    payload = build_session_update(
        RealtimeMeasurementConfig(
            api_key="openai-test-key",
            audio_path=tmp_path / "audio.wav",
            transcription_model="gpt-realtime-whisper",
            language="ru",
        )
    )

    assert payload["type"] == "session.update"
    assert payload["session"]["type"] == "transcription"
    audio_input = payload["session"]["audio"]["input"]
    assert audio_input["format"] == {"type": "audio/pcm", "rate": 24000}
    assert audio_input["transcription"] == {"model": "gpt-realtime-whisper", "language": "ru"}
    assert audio_input["turn_detection"] is None
    assert audio_input["noise_reduction"] is None


def test_audio_payload_diagnostics_detect_unsupported_and_malformed_wav(tmp_path: Path) -> None:
    unsupported = tmp_path / "unsupported.wav"
    with wave.open(str(unsupported), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00\x00\x00" * 8000)

    unsupported_diag = diagnose_pcm_wav_audio(unsupported)
    assert unsupported_diag["audio_payload_valid"] is False
    assert unsupported_diag["audio_unsupported"] is True
    assert unsupported_diag["audio_quality_classification"] == "unsupported_format"

    malformed = tmp_path / "malformed.wav"
    malformed.write_bytes(b"not-a-wav")
    malformed_diag = diagnose_pcm_wav_audio(malformed)
    assert malformed_diag["audio_payload_valid"] is False
    assert malformed_diag["audio_malformed"] is True
    assert malformed_diag["audio_quality_classification"] == "malformed"


def test_measurement_success_logs_required_events_and_no_secret(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    _write_pcm_wav(audio)
    lines: list[str] = []
    sent: list[dict] = []
    connected: dict[str, object] = {}

    class _FakeWebSocket:
        def __init__(self) -> None:
            self.responses = [
                json.dumps({"type": "session.created"}),
                json.dumps({"type": "session.updated"}),
                json.dumps({"type": "conversation.item.input_audio_transcription.delta", "delta": "pri"}),
                json.dumps({"type": "conversation.item.input_audio_transcription.completed", "transcript": "privet"}),
            ]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def send(self, message: str) -> None:
            sent.append(json.loads(message))

        async def recv(self) -> str:
            return self.responses.pop(0)

    async def _connector(url: str, headers: dict[str, str]) -> _FakeWebSocket:
        connected["url"] = url
        connected["headers"] = headers
        return _FakeWebSocket()

    result = asyncio.run(
        run_realtime_measurement(
            RealtimeMeasurementConfig(api_key="openai-test-measurement-secret", audio_path=audio),
            connector=_connector,
            writer=lines.append,
        )
    )

    actions = [event["action"] for event in _events(lines)]
    assert result.error is None
    assert result.transcript_text_present is True
    assert "realtime_connection_attempt" in actions
    assert "realtime_connection_ok" in actions
    assert "realtime_session_created" in actions
    assert "realtime_audio_send_started" in actions
    assert "realtime_first_delta_ms" in actions
    assert "realtime_final_ms" in actions
    assert "realtime_transcript_text_present" in actions
    assert "realtime_cleanup_done" in actions
    assert "realtime_error" not in actions
    assert "openai-test-measurement-secret" not in "\n".join(lines)
    assert connected["headers"] == {"Authorization": "Bearer openai-test-measurement-secret"}
    assert sent[0]["session"]["type"] == "transcription"
    assert any(message["type"] == "input_audio_buffer.append" for message in sent)
    assert sent[-1]["type"] == "input_audio_buffer.commit"


def test_measurement_error_is_redacted_and_cleanup_runs(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    _write_pcm_wav(audio)
    lines: list[str] = []
    fake_key = "sk-" + "serversecret123"

    class _RejectingWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def send(self, _message: str) -> None:
            return None

        async def recv(self) -> str:
            return json.dumps(
                {
                    "type": "error",
                    "error": {
                        "code": "invalid_api_key",
                        "message": f"bad key {fake_key}",
                    },
                }
            )

    async def _connector(_url: str, _headers: dict[str, str]) -> _RejectingWebSocket:
        return _RejectingWebSocket()

    result = asyncio.run(
        run_realtime_measurement(
            RealtimeMeasurementConfig(api_key=fake_key, audio_path=audio),
            connector=_connector,
            writer=lines.append,
        )
    )

    events = _events(lines)
    assert result.error == "openai_realtime_invalid_api_key"
    assert any(event["action"] == "realtime_connection_failed" for event in events)
    assert events[-1]["action"] == "realtime_cleanup_done"
    assert fake_key not in "\n".join(lines)


def test_measurement_module_has_no_business_dialog_side_effects() -> None:
    module_file = Path(realtime_measurement.__file__)
    source = module_file.read_text(encoding="utf-8")

    assert "ai_secretary.telephony" not in source
    assert "apply_turn" not in source
    assert "CallSession" not in source
