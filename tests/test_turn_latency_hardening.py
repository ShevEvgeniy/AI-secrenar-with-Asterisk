"""Regression coverage for NODE-005 turn-based latency hardening."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ai_secretary.config.settings import Settings
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
        asterisk_ssh_host="host",
        asterisk_ssh_user="user",
        asterisk_ssh_key=str(tmp_path / "id_rsa"),
        asterisk_ssh_password="",
        asterisk_docker_container="",
    )


def _read_events(session: CallSession) -> list[dict[str, Any]]:
    return [json.loads(line) for line in session.events_path.read_text(encoding="utf-8").splitlines()]


class _LatencyClient:
    def __init__(self) -> None:
        self.record_calls: list[dict[str, Any]] = []
        self.wait_timeouts: list[float] = []
        self.calls: list[str] = []

    async def record_safe(self, _channel_id: str, record_name: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(f"record:{record_name}")
        self.record_calls.append({"record_name": record_name, **kwargs})
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def wait_for_recording_finished(self, *_args: Any, **kwargs: Any) -> dict[str, Any]:
        self.wait_timeouts.append(kwargs["timeout"])
        return {"type": "RecordingFinished"}

    async def download_recording(self, _name: str, dest_path: str) -> None:
        Path(dest_path).write_bytes(b"RIFFfake")

    async def moh_start_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def moh_stop_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def play_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.calls.append("play")
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {"payload": {"id": f"play-{len(self.calls)}"}}}

    async def wait_for_playback_finished(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.calls.append("playback_finished")
        return {"type": "PlaybackFinished"}

    async def continue_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def hangup_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("successful PHONE path should transfer without hangup")


def test_turn_loop_uses_stage_record_profiles_and_traces_latency(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    for name in (
        "RECORD_MAX_DURATION_SECONDS",
        "RECORD_MAX_SILENCE_SECONDS",
        "RECORD_WAIT_TIMEOUT_SECONDS",
        "RECORD_SLOT_MAX_DURATION_SECONDS",
        "RECORD_SLOT_MAX_SILENCE_SECONDS",
        "RECORD_SLOT_WAIT_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    transcripts = {
        DialogStage.ISSUE: "Need cylinders",
        DialogStage.NAME: "Ivan Petrov",
        DialogStage.CITY: "from Moscow",
        DialogStage.PHONE: "920.032.0355",
        DialogStage.PHONE_CONFIRM: "да",
    }

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        return transcripts[artifact.stage], artifact.details()

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-node-005/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-node-005", channel_id="ch-node-005", artifact_dir=tmp_path / "artifacts")
    client = _LatencyClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))

    assert [(call["max_duration_seconds"], call["max_silence_seconds"]) for call in client.record_calls] == [
        (8, 2),
        (4, 1),
        (7, 3),
        (14, 4),
        (6, 3),
    ]
    assert client.wait_timeouts == [13, 8, 13, 21, 12]
    confirm_record_idx = next(i for i, call in enumerate(client.calls) if "phone_confirm" in call)
    barrier_idx = client.calls.index("playback_finished")
    assert barrier_idx < confirm_record_idx

    events = _read_events(session)
    for action in (
        "play_prompt",
        "record_done",
        "download_recording",
        "user_transcribed",
        "dialog_decision",
        "play_transfer_phrase",
        "transfer",
    ):
        matching = [event for event in events if event["action"] == action]
        assert matching, action
        assert all(event["dur_ms"] is not None for event in matching), action

    record_starts = [event for event in events if event["action"] == "record_start"]
    assert record_starts[0]["details"]["max_duration_seconds"] == 8
    assert record_starts[1]["details"]["max_silence_seconds"] == 1
    assert not any(event["action"] == "pipeline_start" for event in events)
