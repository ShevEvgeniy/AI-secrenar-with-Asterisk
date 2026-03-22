"""Tests for system prompt prepublish and no-silence fallback behavior."""

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


def _read_events(session: CallSession) -> list[dict]:
    lines = session.events_path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


class _FakeClient:
    def __init__(self, *, fail_media: set[str] | None = None):
        self.calls: list[str] = []
        self.fail_media = fail_media or set()

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
        if media in self.fail_media:
            return {"ok": False, "reason": "media_missing", "http_status": 404, "details": {}}
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def hangup_safe(self, *_args, **_kwargs):
        self.calls.append("hangup")
        return {"ok": True}


def test_system_sounds_publish_once_with_cache(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    settings = _settings(tmp_path)
    publishes: list[str] = []

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFfake"

    def fake_publish(_path: Path, remote_rel: str, _settings: Settings):
        time.sleep(0.03)
        publishes.append(remote_rel)
        return {"ok": True, "sound_id": "sound:" + remote_rel.removesuffix(".wav"), "remote_path": remote_rel, "error": None, "details": {}}

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(ari_app, "publish_wav_to_asterisk", fake_publish)
    monkeypatch.setattr(ari_app, "remote_file_exists", lambda *_args, **_kwargs: True)

    first = asyncio.run(ari_app.ensure_system_sounds(settings))
    second = asyncio.run(ari_app.ensure_system_sounds(settings))

    assert all(first.values())
    assert all(second.values())
    assert len(publishes) == len(ari_app._SYSTEM_SOUND_TEXTS)


def test_call_uses_system_prompt_without_per_call_publish(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    settings = _settings(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "call-prompt"
    session = CallSession(call_id="call-prompt", channel_id="ch-1", artifact_dir=artifact_dir)
    client = _FakeClient()

    response_for_tts = artifact_dir / "response_for_tts.txt"
    response_for_tts.parent.mkdir(parents=True, exist_ok=True)
    response_for_tts.write_text("ok", encoding="utf-8")

    for sid in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sid] = True
    ari_app._system_sounds_ready = True
    monkeypatch.setattr(
        ari_app,
        "run_pipeline_from_transcript",
        lambda *_args, **_kwargs: {"paths": {"response_for_tts": str(response_for_tts)}},
    )
    monkeypatch.setattr(ari_app, "should_stop_dialog", lambda _state, turns_done, _max_turns: turns_done >= 1)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFreply"

    publish_calls: list[str] = []

    def fake_publish(_path: Path, remote_rel: str, _settings: Settings):
        publish_calls.append(remote_rel)
        return {"ok": True, "sound_id": "sound:" + remote_rel.removesuffix(".wav"), "remote_path": remote_rel, "error": None, "details": {}}

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(ari_app, "publish_wav_to_asterisk", fake_publish)

    asyncio.run(ari_app.handle_call(client, settings, "app", session))

    assert any(call == f"play:{ari_app.PROMPT_1_SOUND_ID}" for call in client.calls)
    assert all("prompt_" not in path for path in publish_calls)
    assert any(path.endswith("/reply.wav") for path in publish_calls)


def test_prompt_fail_uses_builtin_fallback_and_no_immediate_hangup(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    settings = _settings(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "call-fallback"
    session = CallSession(call_id="call-fallback", channel_id="ch-2", artifact_dir=artifact_dir)
    client = _FakeClient(fail_media={"sound:demo-congrats"})

    response_for_tts = artifact_dir / "response_for_tts.txt"
    response_for_tts.parent.mkdir(parents=True, exist_ok=True)
    response_for_tts.write_text("ok", encoding="utf-8")

    # No remote system sounds available -> fallback should use builtin media.
    for sid in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sid] = False
    ari_app._system_sounds_ready = False
    monkeypatch.setattr(
        ari_app,
        "run_pipeline_from_transcript",
        lambda *_args, **_kwargs: {"paths": {"response_for_tts": str(response_for_tts)}},
    )
    monkeypatch.setattr(ari_app, "should_stop_dialog", lambda _state, turns_done, _max_turns: turns_done >= 1)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFreply"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {"ok": True, "sound_id": "sound:ai_secretary/call-fallback/reply", "remote_path": "/tmp/reply.wav", "error": None, "details": {}},
    )

    asyncio.run(ari_app.handle_call(client, settings, "app", session))
    events = _read_events(session)

    assert any(call == "play:sound:demo-congrats" for call in client.calls)
    assert not any(e["action"] == "hangup_after_prompt_fail" for e in events)
    assert any(e["action"] == "play_fallback" for e in events)
    assert any(e["action"] == "record_start" for e in events)


def test_prompt_and_fallback_fail_calls_hangup(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    settings = _settings(tmp_path)
    artifact_dir = tmp_path / "artifacts" / "call-fallback-hardfail"
    session = CallSession(call_id="call-fallback-hardfail", channel_id="ch-3", artifact_dir=artifact_dir)
    # Fail prompt and both builtin fallbacks.
    client = _FakeClient(
        fail_media={
            "sound:demo-congrats",
            "sound:tt-weasels",
        }
    )

    response_for_tts = artifact_dir / "response_for_tts.txt"
    response_for_tts.parent.mkdir(parents=True, exist_ok=True)
    response_for_tts.write_text("ok", encoding="utf-8")

    for sid in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sid] = False
    ari_app._system_sounds_ready = False
    monkeypatch.setattr(
        ari_app,
        "run_pipeline_from_transcript",
        lambda *_args, **_kwargs: {"paths": {"response_for_tts": str(response_for_tts)}},
    )
    monkeypatch.setattr(ari_app, "should_stop_dialog", lambda _state, turns_done, _max_turns: turns_done >= 1)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFreply"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {"ok": True, "sound_id": "sound:ai_secretary/call-fallback-hardfail/reply", "remote_path": "/tmp/reply.wav", "error": None, "details": {}},
    )

    asyncio.run(ari_app.handle_call(client, settings, "app", session))
    events = _read_events(session)

    assert "hangup" in client.calls
    assert any(e["action"] == "hangup_after_prompt_and_fallback_fail" for e in events)


def test_system_sounds_soft_fail_does_not_raise(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    settings = _settings(tmp_path)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFfake"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {"ok": False, "sound_id": "", "remote_path": "", "error": "boom", "details": {}},
    )
    monkeypatch.setattr(ari_app, "remote_file_exists", lambda *_args, **_kwargs: False)

    status = asyncio.run(ari_app.ensure_system_sounds(settings))
    assert isinstance(status, dict)
    assert ari_app._system_sounds_ready is False
    assert ari_app._system_sounds_last_error is not None


def test_lazy_retry_trigger_uses_create_task(monkeypatch, tmp_path):
    ari_app._reset_fallback_cache_for_tests()
    settings = _settings(tmp_path)
    monkeypatch.setenv("SYSTEM_SOUNDS_ENABLE", "1")
    monkeypatch.setenv("SYSTEM_SOUNDS_LAZY_RETRY_SEC", "60")
    ari_app._system_sounds_ready = False
    ari_app._system_sounds_last_attempt_ts = time.time() - 120

    calls = {"n": 0}

    def fake_start(_settings: Settings):
        calls["n"] += 1

    monkeypatch.setattr(ari_app, "_start_system_sounds_task", fake_start)
    ari_app._maybe_trigger_system_sounds_lazy(settings, "call-lazy-1")
    assert calls["n"] == 1

    ari_app._system_sounds_last_attempt_ts = time.time()
    ari_app._maybe_trigger_system_sounds_lazy(settings, "call-lazy-2")
    assert calls["n"] == 1
