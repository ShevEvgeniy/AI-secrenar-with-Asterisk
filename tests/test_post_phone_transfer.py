"""Regression coverage for NODE-004 post-PHONE transfer flow."""

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


class _PhoneTransferClient:
    def __init__(self) -> None:
        self.play_calls: list[str] = []
        self.continue_calls: list[dict[str, Any]] = []
        self.record_names: list[str] = []

    async def record_safe(self, _channel_id: str, record_name: str, **_kwargs: Any) -> dict[str, Any]:
        self.record_names.append(record_name)
        return {"ok": True}

    async def wait_for_recording_finished(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"type": "RecordingFinished"}

    async def download_recording(self, _name: str, dest_path: str) -> None:
        Path(dest_path).write_bytes(b"RIFFfake")

    async def moh_start_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    async def moh_stop_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"ok": True}

    async def play_safe(self, _channel_id: str, media: str) -> dict[str, Any]:
        self.play_calls.append(media)
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def continue_safe(self, channel_id: str, context: str, extension: str, priority: int) -> dict[str, Any]:
        self.continue_calls.append(
            {
                "channel_id": channel_id,
                "context": context,
                "extension": extension,
                "priority": priority,
            }
        )
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def hangup_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("hangup should not be used after successful PHONE transfer")


def test_successful_phone_capture_transfers_without_generic_pipeline(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.delenv("TRANSFER_CONTEXT", raising=False)
    monkeypatch.delenv("TRANSFER_EXTEN", raising=False)
    monkeypatch.delenv("TRANSFER_PRIORITY", raising=False)
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    transcripts = {
        DialogStage.ISSUE: "Need cylinders",
        DialogStage.NAME: "Ivan Petrov",
        DialogStage.CITY: "from Moscow",
        DialogStage.PHONE: "920.032.0355",
    }

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        return transcripts[artifact.stage], artifact.details()

    def fail_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("generic reply pipeline must not run after successful PHONE capture")

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "run_pipeline_from_transcript", fail_pipeline)

    session = CallSession(call_id="call-node-004", channel_id="ch-node-004", artifact_dir=tmp_path / "artifacts")
    client = _PhoneTransferClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)

    assert client.record_names[-1].endswith("_phone_utt4")
    assert client.play_calls[-1] == ari_app.TRANSFER_SOUND_ID
    assert client.continue_calls == [
        {
            "channel_id": "ch-node-004",
            "context": "from-internal",
            "extension": "sales_real",
            "priority": 1,
        }
    ]
    profile = json.loads((session.artifact_dir / "profile.json").read_text(encoding="utf-8"))
    assert profile["phone_digits"] == "79200320355"
    assert any(event["action"] == "play_transfer_phrase" and event["status"] == "ok" for event in events)
    assert any(event["action"] == "transfer" and event["status"] == "ok" for event in events)
    assert not any(event["action"] in {"pipeline_start", "build_response", "publish", "playback"} for event in events)
