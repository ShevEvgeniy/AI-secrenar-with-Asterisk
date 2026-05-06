"""Regression coverage for NODE-005 turn-based latency hardening."""

from __future__ import annotations

import asyncio
import json
import time
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
        self.played_media: list[str] = []

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

    async def play_safe(self, _channel_id: str, media: str, **_kwargs: Any) -> dict[str, Any]:
        self.calls.append("play")
        self.played_media.append(media)
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
    monkeypatch.setenv("NAME_GUARD_DELAY_MS", "0")
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
            raise AssertionError("normal PHONE_CONFIRM fast path must not run dynamic TTS")

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("normal PHONE_CONFIRM fast path must not publish per-call wav")
        ),
    )

    session = CallSession(call_id="call-node-005", channel_id="ch-node-005", artifact_dir=tmp_path / "artifacts")
    client = _LatencyClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))

    assert [(call["max_duration_seconds"], call["max_silence_seconds"]) for call in client.record_calls] == [
        (8, 2),
        (6, 2),
        (7, 3),
        (14, 4),
        (6, 3),
    ]
    assert client.wait_timeouts == [13, 11, 13, 21, 12]
    name_record_idx = next(i for i, call in enumerate(client.calls) if "name" in call)
    name_barrier_idx = client.calls.index("playback_finished")
    assert name_barrier_idx < name_record_idx
    confirm_record_idx = next(i for i, call in enumerate(client.calls) if "phone_confirm" in call)
    confirm_barrier_idx = [i for i, call in enumerate(client.calls) if call == "playback_finished"][-1]
    assert confirm_barrier_idx < confirm_record_idx

    events = _read_events(session)
    for action in (
        "latency_stage_enter",
        "latency_playback_started",
        "phone_confirm_holding_prompt",
    ):
        matching = [event for event in events if event["action"] == action]
        if action == "phone_confirm_holding_prompt":
            assert not matching, action
            continue
        assert matching, action

    for action in (
        "latency_asr_done",
        "latency_decision_done",
        "latency_tts_done",
        "latency_publish_done",
        "latency_playback_finished",
        "latency_stage_done",
        "play_prompt",
        "record_done",
        "download_recording",
        "user_transcribed",
        "dialog_decision",
        "play_transfer_phrase",
        "transfer",
    ):
        matching = [event for event in events if event["action"] == action]
        if action in {"latency_tts_done", "latency_publish_done"}:
            assert not any(event["details"].get("playback_stage") == "PHONE_CONFIRM" for event in matching), action
            continue
        assert matching, action
        assert all(event["dur_ms"] is not None for event in matching), action

    record_starts = [event for event in events if event["action"] == "record_start"]
    assert record_starts[0]["details"]["max_duration_seconds"] == 8
    assert record_starts[1]["details"]["max_silence_seconds"] == 2
    assert not any(event["action"] == "pipeline_start" for event in events)

    name_barriers = [
        event for event in events if event["action"] == "name_playback_barrier" and event["status"] == "ok"
    ]
    assert name_barriers
    assert name_barriers[0]["details"]["guard_delay_ms"] == 0
    assert name_barriers[0]["details"]["dynamic"] is False

    phone_decision = next(
        event
        for event in events
        if event["action"] == "latency_decision_done" and event["details"]["stage"] == "PHONE"
    )
    assert phone_decision["details"]["to_stage"] == "PHONE_CONFIRM"
    fast_events = [event for event in events if event["action"] == "phone_confirm_fast_path_used"]
    assert len(fast_events) == 1
    assert fast_events[0]["details"]["phone_digits"] == "9200320355"
    assert fast_events[0]["details"]["dynamic_tts_required"] is False
    assert fast_events[0]["details"]["publish_required"] is False
    assert not any(event["action"] == "phone_confirm_prompt_tts" for event in events)
    assert not any(event["action"] == "phone_confirm_prompt_publish" for event in events)
    assert any(
        event["action"] == "latency_playback_started"
        and event["details"].get("stage") == "PHONE"
        and event["details"]["playback_stage"] == "PHONE_CONFIRM"
        and event["details"]["playback_kind"] == "phone_confirm_fast_path"
        for event in events
    )
    fast_media = fast_events[0]["details"]["media_sequence"]
    assert fast_media[0] == ari_app.PHONE_CONFIRM_PREFIX_SOUND_ID
    assert fast_media[-1] == ari_app.PHONE_CONFIRM_SUFFIX_SOUND_ID
    assert fast_media[1:-1] == [ari_app.PHONE_CONFIRM_DIGIT_SOUND_IDS[digit] for digit in "9200320355"]
    assert not any(event["action"] == "latency_silence_risk" for event in events)


def test_phone_confirm_falls_back_to_dynamic_prompt_when_static_digits_unavailable(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    monkeypatch.setenv("PHONE_CONFIRM_HOLDING_PLAYBACK_TIMEOUT_SECONDS", "1")
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True
    ari_app._system_sound_status[ari_app.PHONE_CONFIRM_DIGIT_SOUND_IDS["9"]] = False

    transcripts = {
        DialogStage.ISSUE: "Need cylinders",
        DialogStage.NAME: "Ivan Petrov",
        DialogStage.CITY: "from Moscow",
        DialogStage.PHONE: "920.032.0355",
        DialogStage.PHONE_CONFIRM: "да",
    }

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        return transcripts[artifact.stage], artifact.details()

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    publish_calls: list[str] = []

    def fake_publish(_path: Path, remote_rel: str, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        publish_calls.append(remote_rel)
        return {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-node-011/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        }

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(ari_app, "publish_wav_to_asterisk", fake_publish)

    session = CallSession(call_id="call-node-011", channel_id="ch-node-011", artifact_dir=tmp_path / "artifacts")
    client = _LatencyClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)

    unavailable = [event for event in events if event["action"] == "phone_confirm_fast_path_unavailable"]
    assert unavailable
    assert ari_app.PHONE_CONFIRM_DIGIT_SOUND_IDS["9"] in unavailable[-1]["details"]["missing_static_media"]
    assert any(event["action"] == "phone_confirm_holding_prompt" and event["status"] == "ok" for event in events)
    assert any(event["action"] == "phone_confirm_prompt_tts" and event["status"] == "ok" for event in events)
    assert any(event["action"] == "phone_confirm_prompt_publish" and event["status"] == "ok" for event in events)
    assert any(path.endswith("/phone_confirm_prompt.wav") for path in publish_calls)


def test_latency_silence_risk_thresholds_are_logged(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LATENCY_SILENCE_WARN_MS", "5")
    monkeypatch.setenv("LATENCY_SILENCE_CRITICAL_MS", "10")
    session = CallSession(call_id="call-latency-risk", channel_id="ch-latency-risk", artifact_dir=tmp_path / "artifacts")

    context = {
        "stage": DialogStage.PHONE.value,
        "turn_idx": 4,
        "stage_enter_ts": "2026-05-06T00:00:00+00:00",
        "client_speech_end_perf": time.perf_counter() - 0.020,
        "next_stage": DialogStage.PHONE_CONFIRM.value,
    }
    ari_app._log_latency_playback_started(
        session,
        context,
        playback_stage=DialogStage.PHONE_CONFIRM,
        media=ari_app.PHONE_CONFIRM_HOLDING_SOUND_ID,
        sound_id=ari_app.PHONE_CONFIRM_HOLDING_SOUND_ID,
        prompt_text=ari_app.PHONE_CONFIRM_HOLDING_PHRASE,
        dynamic=False,
        playback_kind="holding",
    )

    events = _read_events(session)
    risk = next(event for event in events if event["action"] == "latency_silence_risk")
    assert risk["status"] == "critical"
    assert risk["details"]["stage"] == "PHONE"
    assert risk["details"]["playback_stage"] == "PHONE_CONFIRM"
    assert risk["details"]["speech_to_playback_start_ms"] >= 10


def test_name_retry_prompt_waits_for_playback_barrier(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("NAME_GUARD_DELAY_MS", "0")
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    class _FakeTTS:
        def synthesize(self, text: str) -> bytes:
            assert "РёРјСЏ" in text
            return b"RIFFname"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-node-005/name_retry_prompt",
            "remote_path": "/tmp/name_retry_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-node-005", channel_id="ch-node-005", artifact_dir=tmp_path / "artifacts")
    session.dialog.stage = DialogStage.NAME
    session.dialog.profile = {"name_retry_prompt": "РџРѕРґСЃРєР°Р¶РёС‚Рµ, РїРѕР¶Р°Р»СѓР№СЃС‚Р°, РІР°С€Рµ РёРјСЏ."}
    client = _LatencyClient()

    ok, _moh_started = asyncio.run(
        ari_app._play_prompt(
            client,
            _settings(tmp_path),
            "app",
            session,
            DialogStage.NAME,
            ari_app._system_sounds_snapshot(),
            False,
        )
    )

    assert ok is True
    assert client.calls == ["play", "playback_finished"]
    events = _read_events(session)
    name_barriers = [
        event for event in events if event["action"] == "name_playback_barrier" and event["status"] == "ok"
    ]
    assert name_barriers
    assert name_barriers[-1]["details"]["dynamic"] is True
    assert name_barriers[-1]["details"]["guard_delay_ms"] == 0


def test_phone_retry_prompt_plays_dynamic_prompt_instead_of_static_phone_prompt(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    class _FakeTTS:
        def synthesize(self, text: str) -> bytes:
            assert "Продиктуйте" in text
            return b"RIFFretry"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-node-005/phone_retry_prompt",
            "remote_path": "/tmp/phone_retry_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-node-005", channel_id="ch-node-005", artifact_dir=tmp_path / "artifacts")
    session.dialog.stage = DialogStage.PHONE
    session.dialog.profile = {"phone_retry_prompt": "Продиктуйте, пожалуйста, ещё раз ваш номер телефона."}
    client = _LatencyClient()

    ok, _moh_started = asyncio.run(
        ari_app._play_prompt(
            client,
            _settings(tmp_path),
            "app",
            session,
            DialogStage.PHONE,
            ari_app._system_sounds_snapshot(),
            False,
        )
    )

    assert ok is True
    assert client.played_media == ["sound:ai_secretary/call-node-005/phone_retry_prompt"]
    assert ari_app.PROMPT_4_SOUND_ID not in client.played_media

    events = _read_events(session)
    assert any(event["action"] == "dynamic_prompt_tts" and event["status"] == "ok" for event in events)
    play_events = [event for event in events if event["action"] == "play_prompt"]
    assert play_events[-1]["details"]["dynamic"] is True
    assert play_events[-1]["details"]["prompt_text"] == "Продиктуйте, пожалуйста, ещё раз ваш номер телефона."
