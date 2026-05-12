"""Tests for NODE-003 transcription artifact integrity."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
import wave

from ai_secretary.config.settings import Settings
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
                json.dumps({"type": "session.updated"}),
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

    async def _connector(_url: str, _headers: dict[str, str]) -> _FakeWebSocket:
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
    assert any(message["type"] == "session.update" for message in sent_messages)
    assert any(message["type"] == "input_audio_buffer.append" for message in sent_messages)
    assert any(name == "stt_stream_first_delta_received" for name, _details in metrics)
    assert any(name == "stt_stream_final_received" for name, _details in metrics)


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
    assert any(event["details"].get("stt_live_streaming_stage_allowlist") == ["CITY", "ISSUE", "NAME", "PHONE_CONFIRM"] for event in events)


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


def test_live_bridge_add_channel_http_error_logs_status_body_and_cleans_up(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
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

    async def record_safe(self, *_args, **_kwargs):
        self.record_safe_called = True
        return {
            "ok": False,
            "reason": "test_record_stop",
            "http_status": 599,
            "details": {"test": "stop_after_record_safe"},
        }


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
