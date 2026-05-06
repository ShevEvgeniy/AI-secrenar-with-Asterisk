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


def test_recording_early_stop_policy_by_stage(monkeypatch) -> None:
    monkeypatch.delenv("RECORDING_EARLY_STOP_ENABLED", raising=False)

    assert ari_app._recording_early_stop_policy_for_stage(DialogStage.NAME).enabled is True
    assert ari_app._recording_early_stop_policy_for_stage(DialogStage.CITY).enabled is True
    assert ari_app._recording_early_stop_policy_for_stage(DialogStage.PHONE_CONFIRM).enabled is True
    assert ari_app._recording_early_stop_policy_for_stage(DialogStage.ISSUE).enabled is True
    intent_policy = ari_app._recording_early_stop_policy_for_stage(DialogStage.INTENT_CLARIFY)
    assert intent_policy.enabled is True
    assert intent_policy.reason == "short_slot"
    assert ari_app._talk_detect_value_for_policy(
        ari_app._recording_early_stop_policy_for_stage(DialogStage.PHONE_CONFIRM)
    ) == "300,128"
    phone_policy = ari_app._recording_early_stop_policy_for_stage(DialogStage.PHONE)
    assert phone_policy.enabled is False
    assert phone_policy.reason == "phone_digit_safety_skip"

    monkeypatch.setenv("TALK_DETECT_SET_VALUE", "1200,256")
    assert ari_app._talk_detect_value_for_policy(
        ari_app._recording_early_stop_policy_for_stage(DialogStage.NAME)
    ) == "1200,256"
    monkeypatch.delenv("TALK_DETECT_SET_VALUE", raising=False)

    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "0")
    assert ari_app._recording_early_stop_policy_for_stage(DialogStage.NAME).enabled is False


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


class _TalkDetectClient(_LatencyClient):
    def __init__(self) -> None:
        super().__init__()
        self.queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.stop_calls: list[str] = []
        self.set_variables: list[tuple[str, str, str]] = []
        self.unsubscribed = 0

    async def set_channel_variable_safe(self, channel_id: str, variable: str, value: str) -> dict[str, Any]:
        self.set_variables.append((channel_id, variable, value))
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def stop_live_recording_safe(self, name: str) -> dict[str, Any]:
        self.stop_calls.append(name)
        await self.queue.put({"type": "RecordingFinished", "recording": {"name": name}})
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def _subscribe_ws(self, *_args: Any, **_kwargs: Any) -> asyncio.Queue[dict[str, Any]]:
        self.calls.append("subscribe")
        return self.queue

    def _unsubscribe_ws(self, _queue: asyncio.Queue[dict[str, Any]]) -> None:
        self.unsubscribed += 1
        return None


class _NoSafeStopTalkClient(_TalkDetectClient):
    stop_live_recording_safe = None


class _FailStopTalkClient(_TalkDetectClient):
    async def stop_live_recording_safe(self, name: str) -> dict[str, Any]:
        self.stop_calls.append(name)
        return {"ok": False, "reason": "recording_missing", "http_status": 404, "details": {}}


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
    issue_record_idx = next(i for i, call in enumerate(client.calls) if "issue" in call)
    issue_barrier_idx = client.calls.index("playback_finished")
    assert issue_barrier_idx < issue_record_idx
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


def test_talk_detect_early_stop_stores_recording_after_stable_silence(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("RECORDING_EARLY_STOP_ENABLED", "1")
    session = CallSession(call_id="call-talk-stop", channel_id="ch-talk-stop", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app.RecordingEarlyStopPolicy(
        enabled=True,
        stable_silence_ms=1,
        min_talking_ms=0,
        min_recording_ms=0,
        require_talking_started=True,
        reason="test",
    )

    async def run() -> dict[str, Any]:
        await client.queue.put({"type": "ChannelTalkingStarted", "channel": {"id": "ch-talk-stop"}})
        await client.queue.put({"type": "ChannelTalkingFinished", "channel": {"id": "ch-talk-stop"}})
        return await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-talk",
            stage=DialogStage.NAME,
            turn_idx=1,
            timeout=1,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter() - 1,
        )

    event = asyncio.run(run())
    events = _read_events(session)

    assert event["type"] == "RecordingFinished"
    assert client.stop_calls == ["rec-talk"]
    assert any(item["action"] == "channel_talking_started" for item in events)
    assert any(item["action"] == "channel_talking_finished" for item in events)
    assert any(item["action"] == "recording_early_stop_attempt" for item in events)
    used = next(item for item in events if item["action"] == "recording_early_stop_used")
    assert used["status"] == "ok"
    assert used["details"]["recording_tail_ms"] >= 0


def test_talk_detect_event_subscription_opens_before_record_start(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-subscribe", channel_id="ch-talk-subscribe", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app._recording_early_stop_policy_for_stage(DialogStage.NAME)

    async def run() -> None:
        enabled = await ari_app._maybe_enable_talk_detect(client, session, DialogStage.NAME, 1, policy)
        subscription = await ari_app._open_recording_event_subscription(
            client,
            "app",
            session,
            stage=DialogStage.NAME,
            turn_idx=1,
            record_name="rec-subscribe",
            policy=policy,
            talk_detect_enabled=enabled,
        )
        assert subscription is not None
        await client.record_safe("ch-talk-subscribe", "rec-subscribe")
        subscription.close()

    asyncio.run(run())
    events = _read_events(session)

    assert client.calls[:2] == ["subscribe", "record:rec-subscribe"]
    assert client.unsubscribed == 1
    assert any(item["action"] == "talk_detect_event_subscription_started" for item in events)


def test_talk_detect_guard_cancels_when_speech_resumes(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-resume", channel_id="ch-talk-resume", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app.RecordingEarlyStopPolicy(
        enabled=True,
        stable_silence_ms=50,
        min_talking_ms=0,
        min_recording_ms=0,
        require_talking_started=True,
        reason="test",
    )

    async def run() -> dict[str, Any]:
        await client.queue.put({"type": "ChannelTalkingStarted", "channel": {"id": "ch-talk-resume"}})
        await client.queue.put({"type": "ChannelTalkingFinished", "channel": {"id": "ch-talk-resume"}})
        await client.queue.put({"type": "ChannelTalkingStarted", "channel": {"id": "ch-talk-resume"}})
        await client.queue.put({"type": "ChannelTalkingFinished", "channel": {"id": "ch-talk-resume"}})
        return await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-resume",
            stage=DialogStage.CITY,
            turn_idx=2,
            timeout=1,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter() - 1,
        )

    event = asyncio.run(run())
    events = _read_events(session)

    assert event["type"] == "RecordingFinished"
    assert client.stop_calls == ["rec-resume"]
    assert any(
        item["action"] == "recording_early_stop_skipped" and item["reason"] == "speech_resumed_during_guard"
        for item in events
    )


def test_talk_detect_out_of_order_finished_allows_cautious_early_stop(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-order", channel_id="ch-talk-order", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app.RecordingEarlyStopPolicy(
        enabled=True,
        stable_silence_ms=1,
        min_talking_ms=150,
        min_recording_ms=0,
        require_talking_started=True,
        reason="test",
    )

    async def run() -> dict[str, Any]:
        await client.queue.put({"type": "ChannelTalkingFinished", "channel": {"id": "ch-talk-order"}})
        return await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-order",
            stage=DialogStage.CITY,
            turn_idx=2,
            timeout=1,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter() - 1,
        )

    event = asyncio.run(run())
    events = _read_events(session)

    assert event["type"] == "RecordingFinished"
    assert client.stop_calls == ["rec-order"]
    assert any(item["action"] == "talk_detect_event_order_anomaly" for item in events)
    assert any(item["action"] == "recording_early_stop_used" for item in events)


def test_talk_detect_started_without_finished_timeout_recovers_with_safe_stop(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-timeout", channel_id="ch-talk-timeout", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app.RecordingEarlyStopPolicy(
        enabled=True,
        stable_silence_ms=1000,
        min_talking_ms=0,
        min_recording_ms=0,
        require_talking_started=True,
        reason="test",
    )

    async def run() -> dict[str, Any]:
        await client.queue.put({"type": "ChannelTalkingStarted", "channel": {"id": "ch-talk-timeout"}})
        return await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-timeout",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            timeout=0.02,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter() - 1,
        )

    event = asyncio.run(run())
    events = _read_events(session)

    assert event["type"] == "RecordingFinished"
    assert event["recovered"] is True
    assert client.stop_calls == ["rec-timeout"]
    for action in (
        "talk_detect_started_without_finished",
        "talk_detect_no_finished_event",
        "record_wait_timeout_after_talking_started",
        "recording_timeout_recovery_attempt",
        "recording_timeout_recovery_used",
    ):
        assert any(item["action"] == action for item in events), action


def test_talk_detect_timeout_recovery_failure_preserves_timeout(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-timeout-fail", channel_id="ch-talk-timeout-fail", artifact_dir=tmp_path / "artifacts")
    client = _FailStopTalkClient()
    policy = ari_app.RecordingEarlyStopPolicy(
        enabled=True,
        stable_silence_ms=1000,
        min_talking_ms=0,
        min_recording_ms=0,
        require_talking_started=True,
        reason="test",
    )

    async def run() -> None:
        await client.queue.put({"type": "ChannelTalkingStarted", "channel": {"id": "ch-talk-timeout-fail"}})
        await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-timeout-fail",
            stage=DialogStage.ISSUE,
            turn_idx=1,
            timeout=0.02,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter() - 1,
        )

    try:
        asyncio.run(run())
    except (TimeoutError, asyncio.TimeoutError):
        pass
    events = _read_events(session)

    assert client.stop_calls == ["rec-timeout-fail"]
    assert any(item["action"] == "recording_timeout_recovery_failed" for item in events)


def test_talk_detect_unavailable_falls_back_to_recording_wait(tmp_path: Path) -> None:
    session = CallSession(call_id="call-talk-unavailable", channel_id="ch-talk-unavailable", artifact_dir=tmp_path / "artifacts")
    client = _LatencyClient()
    policy = ari_app._recording_early_stop_policy_for_stage(DialogStage.NAME)

    enabled = asyncio.run(ari_app._maybe_enable_talk_detect(client, session, DialogStage.NAME, 1, policy))
    event = asyncio.run(
        ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-unavailable",
            stage=DialogStage.NAME,
            turn_idx=1,
            timeout=1,
            policy=policy,
            talk_detect_enabled=enabled,
            record_start=time.perf_counter(),
        )
    )
    events = _read_events(session)

    assert enabled is False
    assert event["type"] == "RecordingFinished"
    assert any(item["action"] == "talk_detect_unavailable" for item in events)


def test_recording_safe_stop_unavailable_skips_early_stop(tmp_path: Path) -> None:
    session = CallSession(call_id="call-no-stop", channel_id="ch-no-stop", artifact_dir=tmp_path / "artifacts")
    client = _NoSafeStopTalkClient()
    policy = ari_app.RecordingEarlyStopPolicy(True, 1, 0, 0, True, reason="test")

    async def run() -> dict[str, Any]:
        await client.queue.put({"type": "RecordingFinished", "recording": {"name": "rec-no-stop"}})
        return await ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-no-stop",
            stage=DialogStage.NAME,
            turn_idx=1,
            timeout=1,
            policy=policy,
            talk_detect_enabled=True,
            record_start=time.perf_counter(),
        )

    event = asyncio.run(run())
    events = _read_events(session)

    assert event["type"] == "RecordingFinished"
    assert any(item["action"] == "recording_stop_method_selected" and item["status"] == "fail" for item in events)
    assert any(item["action"] == "recording_early_stop_skipped" and item["reason"] == "safe_stop_unavailable" for item in events)


def test_phone_policy_skips_unsafe_intra_number_early_stop(tmp_path: Path) -> None:
    session = CallSession(call_id="call-phone-policy", channel_id="ch-phone-policy", artifact_dir=tmp_path / "artifacts")
    client = _TalkDetectClient()
    policy = ari_app._recording_early_stop_policy_for_stage(DialogStage.PHONE)

    enabled = asyncio.run(ari_app._maybe_enable_talk_detect(client, session, DialogStage.PHONE, 4, policy))
    event = asyncio.run(
        ari_app._wait_for_recording_with_optional_early_stop(
            client,
            "app",
            session,
            record_name="rec-phone",
            stage=DialogStage.PHONE,
            turn_idx=4,
            timeout=1,
            policy=policy,
            talk_detect_enabled=enabled,
            record_start=time.perf_counter(),
        )
    )
    events = _read_events(session)

    assert enabled is False
    assert event["type"] == "RecordingFinished"
    assert client.stop_calls == []
    assert any(
        item["action"] == "recording_early_stop_skipped" and item["reason"] == "phone_digit_safety_skip"
        for item in events
    )


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


def test_intent_clarify_prompt_waits_for_playback_barrier(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("INTENT_CLARIFY_GUARD_DELAY_MS", "0")
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    session = CallSession(call_id="call-intent-barrier", channel_id="ch-intent-barrier", artifact_dir=tmp_path / "artifacts")
    session.dialog.stage = DialogStage.INTENT_CLARIFY
    client = _LatencyClient()

    ok, _moh_started = asyncio.run(
        ari_app._play_prompt(
            client,
            _settings(tmp_path),
            "app",
            session,
            DialogStage.INTENT_CLARIFY,
            ari_app._system_sounds_snapshot(),
            False,
        )
    )

    assert ok is True
    assert client.calls == ["play", "playback_finished"]
    events = _read_events(session)
    barriers = [event for event in events if event["action"] == "prompt_playback_barrier" and event["status"] == "ok"]
    assert barriers
    assert barriers[-1]["details"]["stage"] == DialogStage.INTENT_CLARIFY.value
    assert barriers[-1]["details"]["guard_delay_ms"] == 0


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
