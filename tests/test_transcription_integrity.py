"""Tests for NODE-003 transcription artifact integrity."""

from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path

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
