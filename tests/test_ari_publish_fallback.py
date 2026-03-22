"""Tests for fail-fast publish and fallback behavior."""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

from ai_secretary.config.settings import Settings
from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key="",
        elevenlabs_api_key="",
        ari_url="http://localhost:8088/ari",
        ari_user="",
        ari_password="",
        sqlite_path=tmp_path / "db.sqlite",
        storage_dir=tmp_path / "storage",
        demo_mode="synth",
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


def _read_events(session: CallSession) -> list[dict]:
    lines = session.events_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


class _FakeClient:
    def __init__(self, *, fail_primary_playback: bool = False):
        self.calls: list[str] = []
        self.fail_primary_playback = fail_primary_playback

    async def record_safe(self, *args, **kwargs):
        self.calls.append("record")
        return {"ok": True}

    async def wait_for_recording_finished(self, *args, **kwargs):
        self.calls.append("record_wait")
        return {"type": "RecordingFinished"}

    async def download_recording(self, _name: str, dest_path: str):
        self.calls.append("download")
        Path(dest_path).write_bytes(b"RIFF")

    async def moh_start_safe(self, *_args, **_kwargs):
        self.calls.append("moh_start")
        return {"ok": True}

    async def moh_stop_safe(self, *_args, **_kwargs):
        self.calls.append("moh_stop")
        return {"ok": True}

    async def play_safe(self, _channel_id: str, media: str):
        self.calls.append(f"play:{media}")
        if self.fail_primary_playback and media != ari_app.FALLBACK_SOUND_ID:
            return {"ok": False, "reason": "media_missing", "http_status": 404, "details": {}}
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def hangup_safe(self, *_args, **_kwargs):
        self.calls.append("hangup")
        return {"ok": True}


def test_publish_timeout_logs_and_fallback_attempt(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PUBLISH_TOTAL_TIMEOUT_SEC", "1")
    monkeypatch.setenv("PLAY_TEST", "0")

    settings = _settings(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "call-timeout"
    session = CallSession(call_id="call-timeout", channel_id="ch-1", artifact_dir=artifact_dir)
    client = _FakeClient()

    response_for_tts = artifact_dir / "response_for_tts.txt"
    response_for_tts.parent.mkdir(parents=True, exist_ok=True)
    response_for_tts.write_text("test", encoding="utf-8")

    monkeypatch.setattr(
        ari_app,
        "run_pipeline",
        lambda *_args, **_kwargs: {"paths": {"response_for_tts": str(response_for_tts)}},
    )

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFfake"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)

    def fake_publish(_path: Path, remote_rel: str, _settings: Settings):
        if remote_rel.endswith("/_system/fallback.wav"):
            return {"ok": True, "sound_id": ari_app.FALLBACK_SOUND_ID, "remote_path": remote_rel, "error": None, "details": {}}
        time.sleep(1.2)
        return {"ok": True, "sound_id": "sound:ai_secretary/call-timeout/reply", "remote_path": remote_rel, "error": None, "details": {}}

    monkeypatch.setattr(ari_app, "publish_wav_to_asterisk", fake_publish)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))
    events = _read_events(session)

    assert any(e["action"] == "publish" and e["status"] == "fail" and e["reason"] == "publish_timeout" for e in events)
    assert any(e["action"] == "fallback_play" for e in events)


def test_moh_stop_happens_immediately_before_fallback_on_publish_fail(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")

    settings = _settings(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "call-order"
    session = CallSession(call_id="call-order", channel_id="ch-2", artifact_dir=artifact_dir)
    client = _FakeClient()

    response_for_tts = artifact_dir / "response_for_tts.txt"
    response_for_tts.parent.mkdir(parents=True, exist_ok=True)
    response_for_tts.write_text("test", encoding="utf-8")

    monkeypatch.setattr(
        ari_app,
        "run_pipeline",
        lambda *_args, **_kwargs: {"paths": {"response_for_tts": str(response_for_tts)}},
    )

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFfake"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {"ok": False, "sound_id": "", "remote_path": "", "error": "boom", "details": {}},
    )

    async def fake_ensure(_settings: Settings, _session: CallSession) -> bool:
        return True

    monkeypatch.setattr(ari_app, "ensure_fallback_sound", fake_ensure)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    idx_stop = client.calls.index("moh_stop")
    idx_fallback_play = client.calls.index(f"play:{ari_app.FALLBACK_SOUND_ID}")
    assert idx_stop < idx_fallback_play
    assert "moh_stop" not in client.calls[:idx_stop]


def test_fallback_synth_is_cached_once(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    settings = _settings(tmp_path)

    synth_calls = {"count": 0}

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            synth_calls["count"] += 1
            return b"RIFFfake"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {"ok": True, "sound_id": ari_app.FALLBACK_SOUND_ID, "remote_path": "", "error": None, "details": {}},
    )

    session1 = CallSession(call_id="c1", channel_id="ch1", artifact_dir=tmp_path / "artifacts" / "c1")
    session2 = CallSession(call_id="c2", channel_id="ch2", artifact_dir=tmp_path / "artifacts" / "c2")

    assert asyncio.run(ari_app.ensure_fallback_sound(settings, session1)) is True
    assert asyncio.run(ari_app.ensure_fallback_sound(settings, session2)) is True
    assert synth_calls["count"] == 1
