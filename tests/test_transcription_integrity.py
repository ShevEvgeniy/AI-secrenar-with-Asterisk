"""Tests for NODE-003 transcription artifact integrity."""

from __future__ import annotations

import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import socket
import time
import wave

import pytest

from ai_secretary.config.settings import Settings
from ai_secretary.stt import live_streaming
from ai_secretary.stt.realtime_whisper import (
    RealtimeTranscriptionConfig,
    RealtimeTranscriptionResult,
    RealtimeWhisperAdapter,
)
from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, DialogStage


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key="",
        elevenlabs_api_key="",
        ari_url="http://localhost:8088/ari",
        ari_user="",
        ari_password="",
        sqlite_path=tmp_path / "db.sqlite",
        storage_dir=tmp_path / "storage",
        demo_mode="real",
        demo_audio_path=tmp_path / "in.wav",
        expected_real_phone="79000000000",
        kb_path=tmp_path / "kb.md",
        rag_top_k=3,
        asterisk_sounds_dir=Path("/var/lib/asterisk/sounds"),
        asterisk_sounds_subdir="ai_secretary",
        asterisk_ssh_host="",
        asterisk_ssh_user="",
        asterisk_ssh_key="",
        asterisk_ssh_password="",
        asterisk_docker_container="",
    )


def _read_events(session: CallSession) -> list[dict]:
    return [
        json.loads(line)
        for line in session.events_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class _DownloadClient:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.downloads: list[tuple[str, str]] = []

    async def download_recording(self, name: str, dest_path: str) -> None:
        self.downloads.append((name, dest_path))
        Path(dest_path).write_bytes(self.payload)


def test_download_transcription_artifact_discards_stale_file_and_hashes_new_audio(tmp_path: Path) -> None:
    session = CallSession(call_id="call-1", channel_id="ch-1", artifact_dir=tmp_path / "artifacts" / "call-1")
    stale_path = session.artifact_dir / "turn_1.wav"
    stale_path.write_bytes(b"stale-audio")
    fresh_audio = b"fresh-audio"
    client = _DownloadClient(fresh_audio)

    artifact = asyncio.run(
        ari_app._download_transcription_artifact(
            client,
            session,
            DialogStage.CITY,
            1,
            "call-1_city_utt1",
            stale_path,
        )
    )

    assert stale_path.read_bytes() == fresh_audio
    assert artifact.record_name == "call-1_city_utt1"
    assert artifact.stage == DialogStage.CITY
    assert artifact.sha256 == hashlib.sha256(fresh_audio).hexdigest()

    events = _read_events(session)
    assert any(event["action"] == "discard_stale_audio_artifact" for event in events)
    download_event = next(event for event in events if event["action"] == "download_recording")
    assert download_event["details"]["record_name"] == "call-1_city_utt1"
    assert download_event["details"]["stage"] == "CITY"
    assert download_event["details"]["audio_sha256"] == artifact.sha256


def test_transcribe_audio_artifact_uses_fixture_only_when_explicitly_configured(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_2.wav"
    audio_path.write_bytes(b"name-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-2",
        channel_id="ch-2",
        stage=DialogStage.NAME,
        turn_idx=2,
        record_name="call-2_name_utt2",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )

    monkeypatch.delenv("TELEPHONY_STT_BACKEND", raising=False)
    text, details = ari_app._transcribe_audio_artifact(settings, artifact)
    assert text == ""
    assert details["reason"] == "stt_backend_not_configured"
    assert details["audio_sha256"] == artifact.sha256

    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "Меня зовут Иван.")
    text, details = ari_app._transcribe_audio_artifact(settings, artifact)
    assert text == "Меня зовут Иван."
    assert details["fixture_env"] == "TELEPHONY_STT_FIXTURE_NAME"
    assert details["record_name"] == "call-2_name_utt2"


def test_name_transcription_sets_russian_language_and_prompt(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_name.wav"
    audio_path.write_bytes(b"name-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-3",
        channel_id="ch-3",
        stage=DialogStage.NAME,
        turn_idx=2,
        record_name="call-3_name_utt2",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    calls: list[dict] = []

    class _FakeWhisperClient:
        def __init__(self, **kwargs) -> None:
            calls.append({"init": kwargs})

        def transcribe(self, audio_bytes: bytes, **kwargs) -> str:
            calls.append({"audio_bytes": audio_bytes, "transcribe": kwargs})
            return "саня"

    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")
    monkeypatch.setattr(ari_app, "WhisperAPIClient", _FakeWhisperClient)

    text, details = ari_app._transcribe_audio_artifact(settings, artifact)

    assert text == "саня"
    assert calls[1]["transcribe"]["language"] == "ru"
    assert "русская" in calls[1]["transcribe"]["prompt"].lower()
    assert "Саня" in calls[1]["transcribe"]["prompt"]
    assert details["stt_language"] == "ru"
    assert details["stt_prompt"] == ari_app.NAME_STT_PROMPT


def test_non_name_transcription_leaves_language_and_prompt_unset(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_phone.wav"
    audio_path.write_bytes(b"phone-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-4",
        channel_id="ch-4",
        stage=DialogStage.PHONE,
        turn_idx=4,
        record_name="call-4_phone_utt4",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    calls: list[dict] = []

    class _FakeWhisperClient:
        def __init__(self, **kwargs) -> None:
            calls.append({"init": kwargs})

        def transcribe(self, audio_bytes: bytes, **kwargs) -> str:
            calls.append({"audio_bytes": audio_bytes, "transcribe": kwargs})
            return "920.032.0355"

    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "openai")
    monkeypatch.setattr(ari_app, "WhisperAPIClient", _FakeWhisperClient)

    text, details = ari_app._transcribe_audio_artifact(settings, artifact)

    assert text == "920.032.0355"
    assert calls[1]["transcribe"]["language"] is None
    assert calls[1]["transcribe"]["prompt"] is None
    assert "stt_language" not in details
    assert "stt_prompt" not in details


def test_city_transcription_uses_russian_language_and_city_prompt(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_city.wav"
    audio_path.write_bytes(b"city-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-city",
        channel_id="ch-city",
        stage=DialogStage.CITY,
        turn_idx=3,
        record_name="call-city_city_utt3",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    calls: list[dict] = []

    class _FakeWhisperClient:
        def __init__(self, **kwargs) -> None:
            calls.append({"init": kwargs})

        def transcribe(self, audio_bytes: bytes, **kwargs) -> str:
            calls.append({"audio_bytes": audio_bytes, "transcribe": kwargs})
            return "Москва"

    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "openai")
    monkeypatch.setattr(ari_app, "WhisperAPIClient", _FakeWhisperClient)

    text, details = ari_app._transcribe_audio_artifact(settings, artifact)

    assert text == "Москва"
    assert calls[1]["transcribe"]["language"] == "ru"
    assert "город" in calls[1]["transcribe"]["prompt"].lower()
    assert "Москва" in calls[1]["transcribe"]["prompt"]
    assert details["stt_language"] == "ru"
    assert details["stt_prompt"] == ari_app.CITY_STT_PROMPT


def _write_pcm_wav(path: Path, *, sample_rate: int = 24000, frames: int = 4800) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(b"\x00\x00" * frames)


def test_realtime_adapter_streams_wav_and_reports_delta_metrics(tmp_path: Path) -> None:
    audio_path = tmp_path / "stream.wav"
    _write_pcm_wav(audio_path)
    sent_messages: list[dict] = []
    metrics: list[tuple[str, dict]] = []

    class _FakeWebSocket:
        def __init__(self) -> None:
            self.responses = [
                json.dumps({"type": "transcription_session.created"}),
                json.dumps({"type": "transcription_session.updated"}),
                json.dumps({"type": "conversation.item.input_audio_transcription.delta", "delta": "pri"}),
                json.dumps({"type": "conversation.item.input_audio_transcription.completed", "transcript": "privet"}),
            ]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def send(self, message: str) -> None:
            sent_messages.append(json.loads(message))

        async def recv(self) -> str:
            return self.responses.pop(0)

    connected: dict[str, object] = {}

    async def _connector(url: str, headers: dict[str, str]) -> _FakeWebSocket:
        connected["url"] = url
        connected["headers"] = headers
        return _FakeWebSocket()

    adapter = RealtimeWhisperAdapter(
        RealtimeTranscriptionConfig(api_key="key", transcription_model="gpt-realtime-whisper"),
        connector=_connector,
    )

    result = asyncio.run(
        adapter.transcribe_wav_file(audio_path, on_metric=lambda name, details: metrics.append((name, details)))
    )

    assert result.text == "privet"
    assert result.first_delta_ms is not None
    assert result.final_ms is not None
    assert connected["url"].endswith("/realtime?intent=transcription")
    assert "OpenAI-Beta" not in connected["headers"]
    config_message = sent_messages[0]
    assert config_message["type"] == "session.update"
    assert "session" in config_message
    assert "type" not in config_message["session"]
    audio_input = config_message["session"]["audio"]["input"]
    assert audio_input["format"] == {"type": "audio/pcm", "rate": 24000}
    assert audio_input["transcription"]["model"] == "gpt-realtime-whisper"
    assert audio_input["transcription"]["language"] == "ru"
    assert "type" not in audio_input["transcription"]
    assert audio_input["turn_detection"] is None
    assert audio_input["noise_reduction"] is None
    assert any(message["type"] == "input_audio_buffer.append" for message in sent_messages)
    assert any(name == "stt_stream_openai_session_config_sent" for name, _details in metrics)
    api_selected = next(details for name, details in metrics if name == "stt_stream_openai_api_selected")
    assert api_selected["stt_stream_openai_api_mode"] == "ga"
    assert api_selected["stt_stream_openai_ws_path"] == "/v1/realtime?intent=transcription"
    assert api_selected["stt_stream_openai_model_selected"] == "gpt-realtime-whisper"
    assert not any("key" in json.dumps(details).lower() for _name, details in metrics)
    assert any(name == "stt_stream_openai_session_created" for name, _details in metrics)
    assert any(name == "stt_stream_openai_session_config_ok" for name, _details in metrics)
    assert any(name == "stt_stream_openai_audio_chunk_sent" for name, _details in metrics)
    assert any(name == "stt_stream_openai_audio_chunks_sent_count" for name, _details in metrics)
    assert any(name == "stt_stream_first_delta_received" for name, _details in metrics)
    assert any(name == "stt_stream_final_received" for name, _details in metrics)


def test_realtime_adapter_logs_session_config_rejection(tmp_path: Path) -> None:
    audio_path = tmp_path / "stream.wav"
    _write_pcm_wav(audio_path)
    sent_messages: list[dict] = []
    metrics: list[tuple[str, dict]] = []

    class _RejectingWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def send(self, message: str) -> None:
            sent_messages.append(json.loads(message))

        async def recv(self) -> str:
            if not hasattr(self, "_created_sent"):
                self._created_sent = True
                return json.dumps({"type": "transcription_session.created"})
            return json.dumps(
                {
                    "type": "error",
                    "error": {
                        "type": "invalid_request_error",
                        "code": "unknown_parameter",
                        "message": "Unknown parameter: 'session.type'.",
                        "param": "session.type",
                    },
                }
            )

    async def _connector(_url: str, _headers: dict[str, str]) -> _RejectingWebSocket:
        return _RejectingWebSocket()

    adapter = RealtimeWhisperAdapter(
        RealtimeTranscriptionConfig(api_key="key", transcription_model="gpt-realtime-whisper"),
        connector=_connector,
    )

    try:
        asyncio.run(adapter.transcribe_wav_file(audio_path, on_metric=lambda name, details: metrics.append((name, details))))
    except RuntimeError as exc:
        assert "unknown_parameter" in str(exc)
    else:
        raise AssertionError("session config rejection should raise")

    assert sent_messages[0]["type"] == "session.update"
    assert "session" in sent_messages[0]
    failed = next(details for name, details in metrics if name == "stt_stream_openai_session_config_failed")
    assert failed["error"]["code"] == "unknown_parameter"


def test_realtime_adapter_logs_chunks_sent_but_no_delta() -> None:
    metrics: list[tuple[str, dict]] = []

    class _NoDeltaWebSocket:
        def __init__(self) -> None:
            self.responses = [
                json.dumps({"type": "transcription_session.created"}),
                json.dumps({"type": "transcription_session.updated"}),
            ]

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args) -> None:
            return None

        async def send(self, _message: str) -> None:
            return None

        async def recv(self) -> str:
            if self.responses:
                return self.responses.pop(0)
            await asyncio.sleep(0.05)
            raise asyncio.TimeoutError

    async def _connector(_url: str, _headers: dict[str, str]) -> _NoDeltaWebSocket:
        return _NoDeltaWebSocket()

    adapter = RealtimeWhisperAdapter(
        RealtimeTranscriptionConfig(api_key="key", transcription_model="gpt-realtime-whisper", timeout_seconds=0.05),
        connector=_connector,
    )

    try:
        asyncio.run(
            adapter.transcribe_pcm_chunks(
                [b"\x00\x00" * 120],
                total_audio_ms=5,
                on_metric=lambda name, details: metrics.append((name, details)),
            )
        )
    except TimeoutError:
        pass
    else:
        raise AssertionError("missing delta/final should time out")

    assert any(name == "stt_stream_openai_audio_chunk_sent" for name, _details in metrics)
    no_delta = next(details for name, details in metrics if name == "stt_stream_openai_no_delta_received")
    assert no_delta["stt_stream_openai_audio_chunks_sent_count"] == 1


def test_live_rtp_advertised_host_is_configurable(monkeypatch) -> None:
    monkeypatch.setenv("STT_LIVE_RTP_BIND_HOST", "0.0.0.0")
    monkeypatch.setenv("STT_LIVE_EXTERNAL_MEDIA_HOST", "192.0.2.55")

    config = live_streaming.live_streaming_config()

    assert config.bind_host == "0.0.0.0"
    assert config.advertised_host == "192.0.2.55"


def test_live_rtp_loopback_advertised_host_fails_for_remote_asterisk() -> None:
    config = replace(_live_test_config(), advertised_host="127.0.0.1")
    events: list[dict] = []

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    try:
        live_streaming._resolve_rtp_advertised_host(
            config,
            "http://192.0.2.10:8088/ari",
            _log_metric,
            DialogStage.ISSUE,
            1,
            "rec",
        )
    except live_streaming.LiveStreamingProofError as exc:
        assert exc.reason == "live_rtp_loopback_advertised_for_remote_asterisk"
    else:
        raise AssertionError("loopback advertised host should fail for remote Asterisk")

    warning = next(event for event in events if event["action"] == "stt_live_external_media_target")
    assert warning["status"] == "fail"
    assert warning["reason"] == "live_rtp_loopback_advertised_for_remote_asterisk"


def test_feature_flag_off_keeps_batch_whisper_path(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_name.wav"
    audio_path.write_bytes(b"name-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-flag-off",
        channel_id="ch-flag-off",
        stage=DialogStage.NAME,
        turn_idx=1,
        record_name="call-flag-off_name_utt1",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    session = CallSession(call_id="call-flag-off", channel_id="ch-flag-off", artifact_dir=tmp_path / "artifacts")

    monkeypatch.setenv("STT_STREAMING_ENABLED", "false")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "batch text")

    text, details = asyncio.run(ari_app._transcribe_audio_artifact_experimental(settings, session, artifact))

    events = _read_events(session)
    assert text == "batch text"
    assert details["stt_streaming_enabled"] is False
    assert "stt_batch_baseline_latency_ms" in details
    assert not any(event["action"].startswith("stt_stream_") for event in events)


def test_feature_flag_on_uses_streaming_adapter_and_logs_metrics(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_city.wav"
    audio_path.write_bytes(b"city-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-stream",
        channel_id="ch-stream",
        stage=DialogStage.CITY,
        turn_idx=2,
        record_name="call-stream_city_utt2",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    session = CallSession(call_id="call-stream", channel_id="ch-stream", artifact_dir=tmp_path / "artifacts")

    class _FakeStreamingAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_wav_file(self, _path: Path, *, on_metric):
            on_metric("stt_stream_session_started", {"stt_stream_total_audio_ms": 200})
            on_metric("stt_stream_audio_chunk_sent", {"chunk_index": 1})
            on_metric(
                "stt_stream_first_delta_received",
                {"stt_stream_latency_first_delta_ms": 37, "stt_stream_text": "mos"},
            )
            on_metric("stt_stream_final_received", {"stt_stream_latency_final_ms": 81, "stt_stream_text": "moskva"})
            return RealtimeTranscriptionResult(
                text="moskva",
                first_delta_ms=37,
                final_ms=81,
                total_audio_ms=200,
                chunks_sent=1,
                deltas=["mos"],
                model="gpt-realtime-whisper",
                language="ru",
            )

    monkeypatch.setenv("STT_STREAMING_ENABLED", "true")
    monkeypatch.setattr(ari_app, "RealtimeWhisperAdapter", _FakeStreamingAdapter)

    text, details = asyncio.run(ari_app._transcribe_audio_artifact_experimental(settings, session, artifact))

    events = _read_events(session)
    assert text == "moskva"
    assert details["stt_backend"] == "streaming"
    assert details["stt_stream_latency_first_delta_ms"] == 37
    assert any(event["action"] == "stt_stream_session_started" for event in events)
    assert any(event["action"] == "stt_stream_audio_chunk_sent" for event in events)
    assert any(event["action"] == "stt_stream_first_delta_received" for event in events)
    assert any(event["action"] == "stt_stream_final_received" for event in events)


def test_streaming_error_falls_back_to_batch_stt(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_city.wav"
    audio_path.write_bytes(b"city-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-stream-fallback",
        channel_id="ch-stream-fallback",
        stage=DialogStage.CITY,
        turn_idx=2,
        record_name="call-stream-fallback_city_utt2",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    session = CallSession(
        call_id="call-stream-fallback",
        channel_id="ch-stream-fallback",
        artifact_dir=tmp_path / "artifacts",
    )

    class _FailingStreamingAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_wav_file(self, _path: Path, *, on_metric):
            raise RuntimeError("stream down")

    monkeypatch.setenv("STT_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_STREAMING_FALLBACK_TO_BATCH", "true")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_CITY", "fallback city")
    monkeypatch.setattr(ari_app, "RealtimeWhisperAdapter", _FailingStreamingAdapter)

    text, details = asyncio.run(ari_app._transcribe_audio_artifact_experimental(settings, session, artifact))

    events = _read_events(session)
    assert text == "fallback city"
    assert details["stt_stream_fallback_to_batch"] is True
    assert details["stt_batch_baseline_latency_ms"] >= 0
    assert any(event["action"] == "stt_stream_error" for event in events)
    assert any(event["action"] == "stt_stream_fallback_to_batch" for event in events)


def test_live_streaming_feature_flag_initializes_proof_path_only_when_enabled(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-live", channel_id="ch-live", artifact_dir=tmp_path / "artifacts")
    calls: list[dict] = []

    async def _fake_start_live_proof(**kwargs):
        calls.append(kwargs)
        task = asyncio.create_task(_completed_live_result())
        return ari_app.LiveStreamingProofHandle(task=task)

    async def _completed_live_result():
        return ari_app.LiveStreamingProofResult(
            text="live text",
            first_delta_ms=25,
            final_ms=90,
            chunks_sent=2,
            audio_started_before_recording_finished=True,
            recording_finish_to_final_ms=-120,
        )

    monkeypatch.setattr(ari_app, "start_live_streaming_proof", _fake_start_live_proof)
    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "false")
    async def _run_disabled_probe():
        return await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.CITY,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: 2.0,
        )

    assert asyncio.run(_run_disabled_probe()) is None

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")

    async def _run_enabled_probe():
        handle = await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.CITY,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: 2.0,
        )
        return await ari_app._finish_live_streaming_probe_task(
            handle,
            session,
            stage=DialogStage.CITY,
            turn_idx=1,
            record_name="rec",
        )

    result = asyncio.run(_run_enabled_probe())

    assert result is not None
    assert result.text == "live text"
    assert calls[0]["stage"] == DialogStage.CITY


def test_phone_is_excluded_from_live_streaming_by_default(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-live-phone", channel_id="ch-live-phone", artifact_dir=tmp_path / "artifacts")

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    async def _run_phone_probe():
        return await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.PHONE,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: 2.0,
        )

    task = asyncio.run(_run_phone_probe())
    events = _read_events(session)
    assert task is None
    assert any(event["action"] == "stt_live_stream_probe_failed" for event in events)
    assert any(event["details"].get("stt_live_streaming_stage_allowlist") == ["CITY", "ISSUE", "NAME"] for event in events)


def test_phone_confirm_is_excluded_from_default_live_streaming_allowlist(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(
        call_id="call-live-phone-confirm",
        channel_id="ch-live-phone-confirm",
        artifact_dir=tmp_path / "artifacts",
    )

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")

    async def _run_probe():
        return await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.PHONE_CONFIRM,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: 2.0,
        )

    handle = asyncio.run(_run_probe())
    events = _read_events(session)
    skipped = next(event for event in events if event["action"] == "stt_live_stream_probe_failed")

    assert handle is None
    assert skipped["reason"] == "phone_confirm_not_in_default_live_allowlist"
    assert skipped["details"]["stt_live_streaming_stage_allowlist"] == ["CITY", "ISSUE", "NAME"]


def test_phone_confirm_can_be_enabled_explicitly_for_live_diagnostics(monkeypatch) -> None:
    monkeypatch.setenv("STT_LIVE_STREAMING_STAGE_ALLOWLIST", "ISSUE,NAME,CITY,PHONE_CONFIRM")

    config = live_streaming.live_streaming_config()

    assert live_streaming.live_streaming_stage_allowed(DialogStage.PHONE_CONFIRM, config) is True
    assert live_streaming.live_streaming_stage_allowed(DialogStage.PHONE, config) is False


def test_live_streaming_result_logs_baseline_delta_and_falls_back_to_batch(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_city.wav"
    audio_path.write_bytes(b"city-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-live-fallback",
        channel_id="ch-live-fallback",
        stage=DialogStage.CITY,
        turn_idx=2,
        record_name="call-live-fallback_city_utt2",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    session = CallSession(call_id="call-live-fallback", channel_id="ch-live-fallback", artifact_dir=tmp_path / "artifacts")
    live_result = ari_app.LiveStreamingProofResult(
        text="live city",
        first_delta_ms=30,
        final_ms=110,
        chunks_sent=3,
        audio_started_before_recording_finished=True,
        recording_finish_to_final_ms=-50,
    )

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT", "false")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_CITY", "batch city")

    text, details = asyncio.run(
        ari_app._transcribe_audio_artifact_experimental(
            settings,
            session,
            artifact,
            live_result,
            recording_finished_at=123.0,
        )
    )

    events = _read_events(session)
    assert text == "batch city"
    assert details["stt_live_streaming_use_live_transcript"] is False
    assert details["stt_live_stream_fallback_to_batch"] is True
    assert details["stt_live_stream_audio_started_before_recording_finished"] is True
    assert "stt_batch_baseline_latency_ms" in details
    assert any(event["action"] == "stt_live_vs_batch_delta_ms" for event in events)
    assert any(event["action"] == "stt_live_stream_fallback_to_batch" for event in events)


async def _completed_empty_live_diagnostics() -> ari_app.LiveStreamingProofResult:
    return ari_app.LiveStreamingProofResult(
        text="",
        first_delta_ms=None,
        final_ms=None,
        chunks_sent=0,
        audio_started_before_recording_finished=None,
        recording_finish_to_final_ms=5,
    )


def test_live_diagnostics_default_empty_batch_stt_still_uses_business_retries(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-diag-default", channel_id="ch-diag-default", artifact_dir=tmp_path / "artifacts")
    session.dialog.stage = DialogStage.NAME
    session.dialog.profile = {"name_retry_count": 2}
    client = _SnoopPreservesRecordingClient(b"batch-audio")

    async def _fake_start_live_proof(**kwargs):
        log_metric = kwargs["log_metric"]
        log_metric("stt_live_rtp_diagnostics_only_started", {}, "ok", None)
        log_metric(
            "stt_live_rtp_diagnostics_result",
            {
                "stt_live_rtp_packets_received_count": 4,
                "stt_live_pcm_chunks_created_count": 4,
                "stt_live_rtp_diagnostics_result": "rtp_packets_received",
            },
            "ok",
            None,
        )
        return ari_app.LiveStreamingProofHandle(task=asyncio.create_task(_completed_empty_live_diagnostics()))

    monkeypatch.delenv("STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED", raising=False)
    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_PROVIDER", "rtp_diagnostics_only")
    monkeypatch.setenv("STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT", "false")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "false")
    monkeypatch.setattr(
        ari_app,
        "_system_sounds_snapshot",
        lambda: {sound_id: True for sound_id in ari_app._SYSTEM_SOUND_TEXTS},
    )
    monkeypatch.setattr(ari_app, "start_live_streaming_proof", _fake_start_live_proof)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    events = _read_events(session)
    assert session.dialog.stage == DialogStage.SAFE_FINISH
    assert session.dialog.profile["name_retry_count"] == 3
    assert session.dialog.profile["safe_finish_reason"] == "name_retry_limit"
    assert any(event["action"] == "safe_finish" and event["reason"] == "name_retry_limit" for event in events)
    assert not any(event["action"] == "stt_live_diagnostics_dialog_bypass" for event in events)


@pytest.mark.parametrize(
    ("stage", "initial_profile", "retry_key"),
    [
        (DialogStage.ISSUE, {"issue_retry_count": 2}, "issue_retry_count"),
        (DialogStage.NAME, {"name_retry_count": 2}, "name_retry_count"),
        (DialogStage.CITY, {"name": "Иван", "city_retry_count": 2}, "city_retry_count"),
    ],
)
def test_rtp_diagnostics_isolated_empty_batch_stt_bypasses_business_dialog(
    monkeypatch,
    tmp_path: Path,
    stage: DialogStage,
    initial_profile: dict,
    retry_key: str,
) -> None:
    settings = _settings(tmp_path)
    session = CallSession(
        call_id=f"call-diag-isolated-{stage.value.lower()}",
        channel_id=f"ch-diag-isolated-{stage.value.lower()}",
        artifact_dir=tmp_path / "artifacts",
    )
    session.dialog.stage = stage
    session.dialog.profile = dict(initial_profile)
    client = _SnoopPreservesRecordingClient(b"batch-audio")

    async def _fake_start_live_proof(**kwargs):
        log_metric = kwargs["log_metric"]
        log_metric("stt_live_rtp_diagnostics_only_started", {}, "ok", None)
        log_metric(
            "stt_live_rtp_diagnostics_result",
            {
                "stt_live_rtp_packets_received_count": 5,
                "stt_live_pcm_chunks_created_count": 5,
                "stt_live_rtp_diagnostics_result": "rtp_packets_received",
            },
            "ok",
            None,
        )
        return ari_app.LiveStreamingProofHandle(task=asyncio.create_task(_completed_empty_live_diagnostics()))

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_PROVIDER", "rtp_diagnostics_only")
    monkeypatch.setenv("STT_LIVE_OPENAI_DISABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT", "false")
    monkeypatch.setenv("STT_LIVE_DIAGNOSTICS_DIALOG_ISOLATED", "true")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "false")
    monkeypatch.setattr(
        ari_app,
        "_system_sounds_snapshot",
        lambda: {sound_id: True for sound_id in ari_app._SYSTEM_SOUND_TEXTS},
    )
    monkeypatch.setattr(ari_app, "start_live_streaming_proof", _fake_start_live_proof)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    events = _read_events(session)
    assert session.dialog.stage == stage
    assert session.dialog.turns_done == 0
    assert session.dialog.profile == initial_profile
    assert not any(event["action"] == "dialog_decision" for event in events)
    assert not any(event["action"] == "safe_finish" for event in events)
    assert not any(event["action"] == "transfer_attempt" for event in events)
    assert (settings.storage_dir / "callbacks" / "callback_records.jsonl").exists() is False
    assert any(event["action"] == "stt_live_diagnostics_isolated_enabled" for event in events)
    assert any(event["action"] == "stt_live_rtp_diagnostics_result" for event in events)
    result = next(event for event in events if event["action"] == "stt_live_diagnostics_result")
    bypass = next(event for event in events if event["action"] == "stt_live_diagnostics_dialog_bypass")
    finished = next(event for event in events if event["action"] == "diagnostic_call_finished")
    assert result["status"] == "handled"
    assert result["reason"] == "empty_transcript"
    assert bypass["details"]["business_retry_count_preserved"] == initial_profile[retry_key]
    assert bypass["details"]["safe_finish_suppressed"] is True
    assert bypass["details"]["transfer_suppressed"] is True
    assert bypass["details"]["callback_suppressed"] is True
    assert finished["reason"] == "diagnostic_dialog_isolated"


def test_live_bridge_add_channel_http_error_logs_status_body_and_cleans_up(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-setup-test")
    session = CallSession(call_id="call-bridge-fail", channel_id="ch-bridge-fail", artifact_dir=tmp_path / "artifacts")
    cleanup_calls: list[str] = []

    class _BridgeFailClient:
        async def create_bridge_safe(self, bridge_id: str, bridge_type: str = "mixing"):
            return {
                "ok": True,
                "http_status": 200,
                "reason": "ok",
                "details": {"payload": {"id": bridge_id}, "request_path": f"/bridges/{bridge_id}"},
            }

        async def add_channel_to_bridge_safe(self, bridge_id: str, channel_id: str):
            return {
                "ok": False,
                "http_status": 409,
                "reason": "bridge_add_channel_http_error",
                "details": {
                    "body": "Channel currently recording",
                    "request_method": "POST",
                    "request_url": f"http://localhost:8088/ari/bridges/{bridge_id}/addChannel?channel={channel_id}",
                    "request_path": f"/ari/bridges/{bridge_id}/addChannel",
                    "request_query": f"channel={channel_id}",
                },
            }

        async def create_external_media_safe(self, *_args, **_kwargs):
            raise AssertionError("externalMedia should not be created after original channel add failure")

        async def destroy_bridge_safe(self, bridge_id: str):
            cleanup_calls.append(bridge_id)
            return {
                "ok": True,
                "http_status": 200,
                "reason": "ok",
                "details": {"request_path": f"/bridges/{bridge_id}"},
            }

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_TOPOLOGY", "bridge_original_external_media_rtp")

    async def _run_probe():
        handle = await ari_app._start_live_streaming_probe(
            settings,
            _BridgeFailClient(),
            "app",
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: None,
        )
        return await ari_app._finish_live_streaming_probe_task(
            handle,
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
        )

    result = asyncio.run(_run_probe())

    events = _read_events(session)
    failed = next(event for event in events if event["action"] == "stt_live_bridge_add_channel_failed")
    assert result is None
    assert failed["details"]["bridge_id"] == "live-proof-call-bridge-fail-1"
    assert failed["details"]["original_channel_id"] == "ch-bridge-fail"
    assert failed["details"]["bridge_channel_id"] == "ch-bridge-fail"
    assert failed["details"]["bridge_channel_role"] == "original"
    assert failed["details"]["ari_http_status"] == 409
    assert failed["details"]["ari_response_body"] == "Channel currently recording"
    assert failed["details"]["ari_request_path"] == "/ari/bridges/live-proof-call-bridge-fail-1/addChannel"
    assert failed["details"]["ari_request_params"] == {"channel": "ch-bridge-fail"}
    assert cleanup_calls == ["live-proof-call-bridge-fail-1"]
    assert any(event["action"] == "stt_live_bridge_cleanup_attempt" for event in events)
    assert any(event["action"] == "stt_live_bridge_cleanup_done" for event in events)
    assert any(event["action"] == "stt_live_stream_fallback_to_batch" for event in events)


class _RecordStartOrderingClient:
    def __init__(self) -> None:
        self.record_safe_called = False

    async def play_safe(self, _channel_id: str, _media: str):
        return {
            "ok": True,
            "details": {"payload": {"id": "playback-ordering"}},
        }

    async def wait_for_playback_finished(self, _app_name: str, _playback_id: str, timeout: int = 30):
        return {"type": "PlaybackFinished"}

    async def moh_start_safe(self, _channel_id: str, moh_class: str = "default"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def moh_stop_safe(self, _channel_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def record_safe(self, *_args, **_kwargs):
        self.record_safe_called = True
        return {
            "ok": False,
            "reason": "test_record_stop",
            "http_status": 599,
            "details": {"test": "stop_after_record_safe"},
        }


class _SnoopPreservesRecordingClient:
    def __init__(self, audio_payload: bytes) -> None:
        self.audio_payload = audio_payload
        self.bridge_channels: list[str] = []
        self.snoop_calls: list[tuple[str, str]] = []
        self.record_safe_called = False
        self.original_channel_bridged_before_record = False

    async def play_safe(self, _channel_id: str, _media: str):
        return {"ok": True, "details": {"payload": {"id": "playback-snoop"}}}

    async def wait_for_playback_finished(self, _app_name: str, _playback_id: str, timeout: int = 30):
        return {"type": "PlaybackFinished"}

    async def moh_start_safe(self, _channel_id: str, moh_class: str = "default"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def moh_stop_safe(self, _channel_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def create_bridge_safe(self, bridge_id: str, bridge_type: str = "mixing"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": bridge_id}}}

    async def snoop_channel_safe(self, channel_id: str, app_name: str, snoop_id: str, *, spy: str = "in", whisper: str = "none"):
        self.snoop_calls.append((channel_id, snoop_id))
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": snoop_id}}}

    async def add_channel_to_bridge_safe(self, _bridge_id: str, channel_id: str):
        self.bridge_channels.append(channel_id)
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def create_external_media_safe(self, _app_name: str, _external_host: str, *, channel_id: str | None = None, format: str = "slin16", direction: str = "both"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": channel_id}}}

    async def destroy_bridge_safe(self, _bridge_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def hangup_safe(self, _channel_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def record_safe(self, channel_id: str, record_name: str, **_kwargs):
        self.record_safe_called = True
        self.original_channel_bridged_before_record = channel_id in self.bridge_channels
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"name": record_name}}}

    async def wait_for_recording_finished(self, _app_name: str, record_name: str, **_kwargs):
        return {"type": "RecordingFinished", "recording": {"name": record_name}}

    async def download_recording(self, _name: str, dest_path: str) -> None:
        Path(dest_path).write_bytes(self.audio_payload)


class _LegacyBridgeRecordingFailedClient(_SnoopPreservesRecordingClient):
    async def snoop_channel_safe(self, *_args, **_kwargs):
        raise AssertionError("legacy bridge topology should not create a snoop channel")

    async def record_safe(self, channel_id: str, record_name: str, **_kwargs):
        self.record_safe_called = True
        self.original_channel_bridged_before_record = channel_id in self.bridge_channels
        if self.original_channel_bridged_before_record:
            return {
                "ok": False,
                "http_status": 500,
                "reason": "RecordingFailed",
                "details": {"record_name": record_name},
            }
        return await super().record_safe(channel_id, record_name, **_kwargs)


async def _pending_live_result() -> ari_app.LiveStreamingProofResult:
    await asyncio.Event().wait()
    raise AssertionError("pending live result should be cancelled")


def _event_index(events: list[dict], action: str, *, status: str | None = None) -> int:
    for idx, event in enumerate(events):
        if event["action"] == action and (status is None or event["status"] == status):
            return idx
    raise AssertionError(f"event not found: {action} status={status}")


def test_handle_call_starts_live_bridge_before_record_start(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-order", channel_id="ch-order", artifact_dir=tmp_path / "artifacts")
    client = _RecordStartOrderingClient()

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "false")
    monkeypatch.setattr(
        ari_app,
        "_system_sounds_snapshot",
        lambda: {sound_id: True for sound_id in ari_app._SYSTEM_SOUND_TEXTS},
    )

    async def _fake_start_live_proof(**kwargs):
        log_metric = kwargs["log_metric"]
        log_metric("stt_live_stream_probe_started", {}, "start", None)
        log_metric("stt_live_bridge_create_attempt", {}, "start", None)
        log_metric("stt_live_bridge_create_ok", {}, "ok", None)
        log_metric("stt_live_bridge_add_channel_attempt", {}, "start", None)
        log_metric("stt_live_bridge_add_channel_ok", {}, "ok", None)
        log_metric("stt_live_external_media_create_attempt", {}, "start", None)
        log_metric("stt_live_external_media_create_ok", {}, "ok", None)
        log_metric("stt_live_stream_media_started", {}, "ok", None)
        return ari_app.LiveStreamingProofHandle(task=asyncio.create_task(_pending_live_result()))

    monkeypatch.setattr(ari_app, "start_live_streaming_proof", _fake_start_live_proof)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    events = _read_events(session)
    barrier_idx = _event_index(events, "prompt_playback_barrier", status="ok")
    probe_idx = _event_index(events, "stt_live_stream_probe_started", status="start")
    add_ok_idx = _event_index(events, "stt_live_bridge_add_channel_ok", status="ok")
    media_idx = _event_index(events, "stt_live_stream_media_started", status="ok")
    record_start_idx = _event_index(events, "record_start", status="start")

    assert client.record_safe_called is True
    assert barrier_idx < probe_idx
    assert probe_idx < add_ok_idx
    assert add_ok_idx < media_idx
    assert media_idx < record_start_idx


def test_handle_call_live_setup_failure_before_record_start_cleans_up_and_records(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-order-fail", channel_id="ch-order-fail", artifact_dir=tmp_path / "artifacts")
    client = _RecordStartOrderingClient()

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "false")
    monkeypatch.setattr(
        ari_app,
        "_system_sounds_snapshot",
        lambda: {sound_id: True for sound_id in ari_app._SYSTEM_SOUND_TEXTS},
    )

    async def _fake_start_live_proof(**kwargs):
        log_metric = kwargs["log_metric"]
        log_metric("stt_live_stream_probe_started", {}, "start", None)
        log_metric("stt_live_bridge_create_attempt", {}, "start", None)
        log_metric("stt_live_bridge_create_ok", {}, "ok", None)
        log_metric("stt_live_bridge_add_channel_attempt", {}, "start", None)
        log_metric(
            "stt_live_bridge_add_channel_failed",
            {
                "ari_http_status": 409,
                "ari_response_body": '{"message":"Channel ch-order-fail currently recording"}',
                "ari_request_url": "http://localhost:8088/ari/bridges/live-proof-call-order-fail-1/addChannel?channel=ch-order-fail",
                "ari_request_path": "/ari/bridges/live-proof-call-order-fail-1/addChannel",
                "ari_request_query": "channel=ch-order-fail",
                "bridge_id": "live-proof-call-order-fail-1",
                "original_channel_id": "ch-order-fail",
            },
            "fail",
            "bridge_add_channel_http_error",
        )
        log_metric("stt_live_bridge_cleanup_attempt", {}, "start", None)
        log_metric("stt_live_bridge_cleanup_done", {}, "ok", None)
        raise RuntimeError("add_channel_to_bridge_safe failed: bridge_add_channel_http_error")

    monkeypatch.setattr(ari_app, "start_live_streaming_proof", _fake_start_live_proof)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    events = _read_events(session)
    cleanup_idx = _event_index(events, "stt_live_bridge_cleanup_done", status="ok")
    probe_failed_idx = _event_index(events, "stt_live_stream_probe_failed", status="handled")
    record_start_idx = _event_index(events, "record_start", status="start")
    failed = next(event for event in events if event["action"] == "stt_live_bridge_add_channel_failed")

    assert client.record_safe_called is True
    assert cleanup_idx < probe_failed_idx < record_start_idx
    assert failed["details"]["ari_http_status"] == 409
    assert failed["details"]["ari_response_body"] == '{"message":"Channel ch-order-fail currently recording"}'
    assert failed["details"]["ari_request_url"].endswith("/addChannel?channel=ch-order-fail")
    assert failed["details"]["ari_request_path"] == "/ari/bridges/live-proof-call-order-fail-1/addChannel"
    assert failed["details"]["ari_request_query"] == "channel=ch-order-fail"
    assert failed["details"]["bridge_id"] == "live-proof-call-order-fail-1"
    assert failed["details"]["original_channel_id"] == "ch-order-fail"


def test_snoop_topology_preserves_original_channel_batch_recording(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-snoop-test")
    session = CallSession(call_id="call-snoop", channel_id="ch-snoop", artifact_dir=tmp_path / "artifacts")
    client = _SnoopPreservesRecordingClient(b"batch-audio")

    class _EmptyLiveAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_pcm_chunks(self, chunks, *, total_audio_ms: int, on_metric):
            async for _chunk in chunks:
                pass
            return RealtimeTranscriptionResult(
                text="",
                first_delta_ms=None,
                final_ms=None,
                total_audio_ms=0,
                chunks_sent=0,
                model="gpt-realtime-whisper",
                language="ru",
            )

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_TOPOLOGY", "snoop_external_media_rtp")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_ISSUE", "batch issue")
    monkeypatch.setattr(live_streaming, "RealtimeWhisperAdapter", _EmptyLiveAdapter)

    record_end_perf: float | None = None

    async def _run_probe_and_batch():
        nonlocal record_end_perf
        handle = await ari_app._start_live_streaming_probe(
            settings,
            client,
            "app",
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="call-snoop_issue_utt1",
            record_started_at=1.0,
            recording_finished_at=lambda: record_end_perf,
        )
        record_result = await client.record_safe("ch-snoop", "call-snoop_issue_utt1")
        record_end_perf = 2.0
        live_result = await ari_app._finish_live_streaming_probe_task(
            handle,
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="call-snoop_issue_utt1",
        )
        audio_path = tmp_path / "turn_issue.wav"
        audio_path.write_bytes(b"batch-audio")
        artifact = ari_app.TranscriptionArtifact(
            call_id="call-snoop",
            channel_id="ch-snoop",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="call-snoop_issue_utt1",
            path=audio_path,
            size_bytes=audio_path.stat().st_size,
            sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
        )
        text, details = await ari_app._transcribe_audio_artifact_experimental(
            settings,
            session,
            artifact,
            live_result,
            recording_finished_at=record_end_perf,
        )
        return record_result, text, details

    record_result, text, details = asyncio.run(_run_probe_and_batch())

    events = _read_events(session)
    assert record_result["ok"] is True
    assert client.record_safe_called is True
    assert client.original_channel_bridged_before_record is False
    assert client.snoop_calls == [("ch-snoop", "live-proof-snoop-call-snoop-1")]
    assert "ch-snoop" not in client.bridge_channels
    assert "live-proof-snoop-call-snoop-1" in client.bridge_channels
    assert any(event["action"] == "live_media_topology_selected" for event in events)
    assert any(event["action"] == "snoop_channel_started" and event["status"] == "ok" for event in events)
    assert text == "batch issue"
    assert details["stt_live_stream_fallback_to_batch"] is True


def test_legacy_bridge_original_topology_covers_recording_failed_conflict(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-legacy-test")
    session = CallSession(call_id="call-legacy", channel_id="ch-legacy", artifact_dir=tmp_path / "artifacts")
    client = _LegacyBridgeRecordingFailedClient(b"batch-audio")

    class _UnusedLiveAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_pcm_chunks(self, *_args, **_kwargs):
            raise AssertionError("recording failure cancels the live task before adapter result is needed")

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_TOPOLOGY", "bridge_original_external_media_rtp")
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "false")
    monkeypatch.setattr(live_streaming, "RealtimeWhisperAdapter", _UnusedLiveAdapter)
    monkeypatch.setattr(
        ari_app,
        "_system_sounds_snapshot",
        lambda: {sound_id: True for sound_id in ari_app._SYSTEM_SOUND_TEXTS},
    )

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    events = _read_events(session)
    assert client.record_safe_called is True
    assert client.original_channel_bridged_before_record is True
    assert any(event["action"] == "live_media_topology_selected" for event in events)
    record_failure = next(event for event in events if event["action"] == "record_start" and event["status"] == "fail")
    assert record_failure["reason"] == "RecordingFailed"
    assert not any(event["action"] == "user_transcribed" for event in events)


class _ExplodingNormalFlowClient:
    async def play_safe(self, *_args, **_kwargs):
        raise AssertionError("externalMedia channel must not play prompts")

    async def record_safe(self, *_args, **_kwargs):
        raise AssertionError("externalMedia channel must not start recording")

    async def answer_safe(self, *_args, **_kwargs):
        raise AssertionError("dispatch guard must run before answer")


def test_external_media_handle_call_entry_is_ignored_before_dialog(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(
        call_id="live-proof-ext-call-entry-1",
        channel_id="live-proof-ext-call-entry-1",
        artifact_dir=tmp_path / "artifacts",
    )
    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")

    asyncio.run(ari_app.handle_call(_ExplodingNormalFlowClient(), settings, "app", session))

    events = _read_events(session)
    assert [event["action"] for event in events] == [
        "session_created",
        "stt_live_external_media_channel_ignored",
    ]
    ignored = events[-1]
    assert ignored["status"] == "skipped"
    assert ignored["reason"] == "external_media_channel_excluded"
    assert ignored["details"] == {"channel_id": "live-proof-ext-call-entry-1"}


def test_external_media_stasis_channel_is_identified_and_logged_without_call_setup(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    channel = {
        "id": "live-proof-ext-1778562482.0-1",
        "name": "UnicastRTP/live-proof-ext-1778562482.0-1",
    }

    assert ari_app._is_live_external_media_stasis_channel(channel) is True
    ari_app._log_external_media_channel_ignored(settings, channel)

    events_path = settings.storage_dir / "artifacts" / channel["id"] / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    ignored = next(event for event in events if event["action"] == "stt_live_external_media_channel_ignored")
    assert ignored["reason"] == "external_media_channel_excluded"
    assert ignored["details"]["channel_id"] == channel["id"]


def test_live_setup_refuses_external_media_channel(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-setup-test")
    session = CallSession(
        call_id="live-proof-ext-recursive-1",
        channel_id="live-proof-ext-recursive-1",
        artifact_dir=tmp_path / "artifacts",
    )
    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")

    async def _run_probe():
        return await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: None,
        )

    handle = asyncio.run(_run_probe())
    events = _read_events(session)

    assert handle is None
    failed = next(event for event in events if event["action"] == "stt_live_stream_probe_failed")
    assert failed["reason"] == "external_media_channel_excluded"
    assert not any("live-proof-ext-live-proof-ext" in json.dumps(event) for event in events)


def test_live_setup_fails_fast_for_missing_openai_api_key(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    session = CallSession(call_id="call-no-key", channel_id="ch-no-key", artifact_dir=tmp_path / "artifacts")
    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")

    async def _run_probe():
        return await ari_app._start_live_streaming_probe(
            settings,
            object(),
            "app",
            session,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            record_started_at=1.0,
            recording_finished_at=lambda: None,
        )

    handle = asyncio.run(_run_probe())
    events = _read_events(session)

    assert handle is None
    assert any(
        event["action"] == "stt_live_stream_probe_failed"
        and event["reason"] == "openai_api_key_missing_or_invalid"
        for event in events
    )
    assert any(
        event["action"] == "stt_live_stream_fallback_to_batch"
        and event["reason"] == "openai_api_key_missing_or_invalid"
        for event in events
    )


def test_live_adapter_exception_is_logged_and_returned_without_unretrieved_task(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-runtime-test")
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    events: list[dict] = []

    class _FakeSource:
        def __init__(self) -> None:
            self.closed = False

        async def close(self) -> None:
            self.closed = True

    class _InvalidKeyAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_pcm_chunks(self, _chunks, *, total_audio_ms: int, on_metric):
            raise RuntimeError("invalid_request_error.invalid_api_key")

    source = _FakeSource()
    monkeypatch.setattr(live_streaming, "RealtimeWhisperAdapter", _InvalidKeyAdapter)

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    result = asyncio.run(
        live_streaming._run_live_streaming_adapter(
            settings=settings,
            source=source,
            queue=queue,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            recording_finished_at=lambda: None,
            log_metric=_log_metric,
            config=live_streaming.live_streaming_config(),
        )
    )

    assert source.closed is True
    assert result.text == ""
    assert any(
        event["action"] == "stt_live_stream_error"
        and event["status"] == "handled"
        and event["reason"] == "openai_realtime_invalid_api_key"
        for event in events
    )


class _SourceSetupClient:
    async def create_bridge_safe(self, bridge_id: str, bridge_type: str = "mixing"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": bridge_id}}}

    async def snoop_channel_safe(self, channel_id: str, app_name: str, snoop_id: str, *, spy: str = "in", whisper: str = "none"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": snoop_id}}}

    async def add_channel_to_bridge_safe(self, _bridge_id: str, _channel_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def create_external_media_safe(self, _app_name: str, _external_host: str, *, channel_id: str | None = None, format: str = "slin24", direction: str = "both"):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {"payload": {"id": channel_id, "format": format}}}

    async def destroy_bridge_safe(self, _bridge_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}

    async def hangup_safe(self, _channel_id: str):
        return {"ok": True, "http_status": 200, "reason": "ok", "details": {}}


def _live_test_config() -> live_streaming.LiveStreamingProofConfig:
    return live_streaming.LiveStreamingProofConfig(
        enabled=True,
        provider="openai_realtime_whisper",
        model="gpt-realtime-whisper",
        fallback_to_batch=True,
        stage_allowlist={"ISSUE"},
        media_source="ari_external_media_rtp",
        topology="snoop_external_media_rtp",
        bind_host="127.0.0.1",
        advertised_host="127.0.0.1",
        host="127.0.0.1",
        port=0,
        sample_rate=24000,
        chunk_ms=200,
        timeout_seconds=0.2,
        use_live_transcript=False,
    )


def test_live_rtp_and_pcm_chunk_counters_are_logged() -> None:
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    events: list[dict] = []
    finished_at: float | None = None
    config = _live_test_config()

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    async def _run_source() -> None:
        nonlocal finished_at
        source = live_streaming._AriExternalMediaRtpSource(
            client=_SourceSetupClient(),
            app_name="app",
            call_id="call-rtp",
            channel_id="ch-rtp",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            config=config,
            queue=queue,
            recording_finished_at=lambda: finished_at,
            log_metric=_log_metric,
        )
        await source.start()
        assert source.sock is not None
        host, port = source.sock.getsockname()
        sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sender.sendto(b"\x80\x00\x00\x01" + b"\x00" * 8 + b"\x01\x02\x03\x04", (host, port))
            chunk = await asyncio.wait_for(queue.get(), timeout=1)
            assert chunk == b"\x01\x02\x03\x04"
            finished_at = time.perf_counter() - 1.0
            assert source.reader_task is not None
            await asyncio.wait_for(source.reader_task, timeout=1)
        finally:
            sender.close()
            await source.close()

    asyncio.run(_run_source())

    assert any(event["action"] == "stt_live_rtp_listener_started" for event in events)
    assert any(event["action"] == "stt_live_rtp_packet_received" for event in events)
    assert any(event["action"] == "stt_live_pcm_chunk_created" for event in events)
    rtp_count = next(event for event in events if event["action"] == "stt_live_rtp_packets_received_count")
    pcm_count = next(event for event in events if event["action"] == "stt_live_pcm_chunks_created_count")
    assert rtp_count["details"]["stt_live_rtp_packets_received_count"] == 1
    assert pcm_count["details"]["stt_live_pcm_chunks_created_count"] == 1


def test_live_no_rtp_packets_logs_no_audio() -> None:
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    events: list[dict] = []
    config = _live_test_config()
    finished_at = time.perf_counter() - 1.0

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    async def _run_source() -> None:
        source = live_streaming._AriExternalMediaRtpSource(
            client=_SourceSetupClient(),
            app_name="app",
            call_id="call-no-rtp",
            channel_id="ch-no-rtp",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            config=config,
            queue=queue,
            recording_finished_at=lambda: finished_at,
            log_metric=_log_metric,
        )
        await source.start()
        assert source.reader_task is not None
        await asyncio.wait_for(source.reader_task, timeout=1)
        await source.close()

    asyncio.run(_run_source())

    no_audio = next(event for event in events if event["action"] == "stt_live_openai_no_audio_received")
    assert no_audio["status"] == "handled"
    assert no_audio["reason"] == "rtp_packets_zero"
    assert no_audio["details"]["stt_live_rtp_packets_received_count"] == 0


def test_live_openai_disabled_env_selects_rtp_diagnostics_only(monkeypatch) -> None:
    monkeypatch.setenv("STT_LIVE_OPENAI_DISABLED", "true")
    monkeypatch.setenv("STT_LIVE_STREAMING_PROVIDER", "openai_realtime_whisper")

    config = live_streaming.live_streaming_config()

    assert config.provider == "rtp_diagnostics_only"
    assert config.topology == "snoop_external_media_rtp"
    assert config.stage_allowlist == {"ISSUE", "NAME", "CITY"}


def test_rtp_diagnostics_only_starts_topology_without_openai_session(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="")
    events: list[dict] = []
    config = replace(_live_test_config(), provider="rtp_diagnostics_only", timeout_seconds=0.05)
    finished_at = time.perf_counter() - 1.0

    class _ExplodingAdapter:
        def __init__(self, *_args, **_kwargs) -> None:
            raise AssertionError("RTP diagnostics-only mode must not open an OpenAI session")

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    async def _run_probe() -> live_streaming.LiveStreamingProofResult:
        handle = await live_streaming.start_live_streaming_proof(
            settings=settings,
            client=_SourceSetupClient(),
            app_name="app",
            call_id="call-rtp-diag",
            channel_id="ch-rtp-diag",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            record_started_at=None,
            recording_finished_at=lambda: finished_at,
            log_metric=_log_metric,
            config=config,
        )
        return await asyncio.wait_for(handle.task, timeout=1)

    monkeypatch.setattr(live_streaming, "RealtimeWhisperAdapter", _ExplodingAdapter)

    result = asyncio.run(_run_probe())

    actions = [event["action"] for event in events]
    assert result.text == ""
    assert "stt_live_rtp_listener_started" in actions
    assert "live_media_topology_selected" in actions
    assert "stt_live_rtp_diagnostics_only_started" in actions
    assert "stt_live_rtp_diagnostics_only_finished" in actions
    diagnostic = next(event for event in events if event["action"] == "stt_live_rtp_diagnostics_result")
    assert diagnostic["status"] == "handled"
    assert diagnostic["reason"] == "rtp_packets_zero"
    assert diagnostic["details"]["stt_live_rtp_packets_received_count"] == 0
    assert diagnostic["details"]["stt_live_pcm_chunks_created_count"] == 0
    assert not any(event["action"].startswith("stt_live_openai_session") for event in events)


def test_live_adapter_logs_ga_api_mode_path_and_model(monkeypatch, tmp_path: Path) -> None:
    settings = replace(_settings(tmp_path), openai_api_key="sk-valid-for-ga-log-test")
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    events: list[dict] = []
    finished_at = time.perf_counter() - 1.0
    config = _live_test_config()

    class _ApiSelectedAdapter:
        def __init__(self, _config) -> None:
            pass

        async def transcribe_pcm_chunks(self, chunks, *, total_audio_ms: int, on_metric):
            on_metric(
                "stt_stream_openai_api_selected",
                {
                    "stt_stream_openai_api_mode": "ga",
                    "stt_stream_openai_ws_path": "/v1/realtime?intent=transcription",
                    "stt_stream_openai_model_selected": "gpt-realtime-whisper",
                },
            )
            async for _chunk in chunks:
                pass
            return RealtimeTranscriptionResult(
                text="",
                first_delta_ms=None,
                final_ms=None,
                total_audio_ms=0,
                chunks_sent=0,
                model="gpt-realtime-whisper",
                language="ru",
            )

    class _StartedSource:
        reader_task: asyncio.Task | None

        def __init__(self) -> None:
            self.closed = False
            self.reader_task = None

        async def close(self) -> None:
            self.closed = True

    def _log_metric(action: str, details: dict, status: str, reason: str | None) -> None:
        events.append({"action": action, "details": details, "status": status, "reason": reason})

    async def _run_adapter() -> None:
        source = _StartedSource()
        await queue.put(None)
        await live_streaming._run_live_streaming_adapter(
            settings=settings,
            source=source,
            queue=queue,
            stage=DialogStage.ISSUE,
            turn_idx=1,
            record_name="rec",
            recording_finished_at=lambda: finished_at,
            log_metric=_log_metric,
            config=config,
        )

    monkeypatch.setattr(live_streaming, "RealtimeWhisperAdapter", _ApiSelectedAdapter)

    asyncio.run(_run_adapter())

    api_mode = next(event for event in events if event["action"] == "stt_live_openai_api_mode")
    ws_path = next(event for event in events if event["action"] == "stt_live_openai_ws_path")
    model = next(event for event in events if event["action"] == "stt_live_openai_model_selected")
    assert api_mode["details"]["stt_stream_openai_api_mode"] == "ga"
    assert ws_path["details"]["stt_stream_openai_ws_path"] == "/v1/realtime?intent=transcription"
    assert model["details"]["stt_stream_openai_model_selected"] == "gpt-realtime-whisper"
    assert not any("key" in json.dumps(event["details"]).lower() for event in events)


def test_live_setup_failure_still_allows_batch_fallback(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    audio_path = tmp_path / "turn_issue.wav"
    audio_path.write_bytes(b"issue-audio")
    artifact = ari_app.TranscriptionArtifact(
        call_id="call-live-setup-fallback",
        channel_id="ch-live-setup-fallback",
        stage=DialogStage.ISSUE,
        turn_idx=1,
        record_name="call-live-setup-fallback_issue_utt1",
        path=audio_path,
        size_bytes=audio_path.stat().st_size,
        sha256=hashlib.sha256(audio_path.read_bytes()).hexdigest(),
    )
    session = CallSession(
        call_id="call-live-setup-fallback",
        channel_id="ch-live-setup-fallback",
        artifact_dir=tmp_path / "artifacts",
    )

    monkeypatch.setenv("STT_LIVE_STREAMING_ENABLED", "true")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_ISSUE", "batch issue")

    text, details = asyncio.run(ari_app._transcribe_audio_artifact_experimental(settings, session, artifact, None))

    assert text == "batch issue"
    assert details["stt_streaming_enabled"] is False
    assert details["stt_batch_baseline_latency_ms"] >= 0
