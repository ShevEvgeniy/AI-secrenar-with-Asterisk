"""Regression coverage for NODE-004 post-PHONE transfer flow."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

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
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {"payload": {"id": f"play-{len(self.play_calls)}"}}}

    async def wait_for_playback_finished(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"type": "PlaybackFinished"}

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


class _UnconfirmedPhoneClient(_PhoneTransferClient):
    def __init__(self) -> None:
        super().__init__()
        self.hangups = 0
        self.call_order: list[str] = []

    async def play_safe(self, channel_id: str, media: str) -> dict[str, Any]:
        self.call_order.append("play")
        result = await super().play_safe(channel_id, media)
        result["details"]["payload"]["state"] = "queued"
        return result

    async def wait_for_playback_finished(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.call_order.append("wait")
        return {"type": "PlaybackFinished"}

    async def continue_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("unconfirmed PHONE must not transfer")

    async def hangup_safe(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.call_order.append("hangup")
        self.hangups += 1
        return {"ok": True}


class _SafeFinishTimeoutClient(_UnconfirmedPhoneClient):
    async def wait_for_playback_finished(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        self.call_order.append("wait")
        raise TimeoutError()


class _IntentClarifyTimeoutClient(_PhoneTransferClient):
    async def wait_for_recording_finished(self, _app_name: str, record_name: str, **_kwargs: Any) -> dict[str, Any]:
        if "_intent_clarify_" in record_name:
            raise TimeoutError()
        return {"type": "RecordingFinished"}


def test_successful_phone_capture_transfers_without_generic_pipeline(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    monkeypatch.delenv("TRANSFER_CONTEXT", raising=False)
    monkeypatch.delenv("TRANSFER_EXTEN", raising=False)
    monkeypatch.delenv("TRANSFER_PRIORITY", raising=False)
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    transcripts = {
        DialogStage.ISSUE: "Need cylinders",
        DialogStage.NAME: "Ivan Petrov",
        DialogStage.CITY: "Москва",
        DialogStage.PHONE: "920.032.0355",
        DialogStage.PHONE_CONFIRM: "да",
    }

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        return transcripts[artifact.stage], artifact.details()

    def fail_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("generic reply pipeline must not run after successful PHONE capture")

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "run_pipeline_from_transcript", fail_pipeline)

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-node-004/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-node-004", channel_id="ch-node-004", artifact_dir=tmp_path / "artifacts")
    client = _PhoneTransferClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)

    assert client.record_names[-2].endswith("_phone_utt4")
    assert client.record_names[-1].endswith("_phone_confirm_utt5")
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
    assert profile["phone_digits"] == "9200320355"
    assert profile["phone_confirmed"] is True
    assert any(event["action"] == "play_transfer_phrase" and event["status"] == "ok" for event in events)
    assert any(event["action"] == "transfer" and event["status"] == "ok" for event in events)
    assert not any(event["action"] in {"pipeline_start", "build_response", "publish", "playback"} for event in events)


def test_phone_confirm_runs_after_phone_capture_at_global_turn_limit(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    transcripts = {
        DialogStage.PHONE: "920.032.0355",
        DialogStage.PHONE_CONFIRM: "\u0434\u0430",
    }
    stage_counts: dict[DialogStage, int] = {}

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        stage_counts[artifact.stage] = stage_counts.get(artifact.stage, 0) + 1
        assert stage_counts[artifact.stage] <= 1
        return transcripts[artifact.stage], artifact.details()

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-phone-limit/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-phone-limit", channel_id="ch-phone-limit", artifact_dir=tmp_path / "artifacts")
    session.dialog.stage = DialogStage.PHONE
    session.dialog.turns_done = 7
    session.dialog.profile = {
        "issue": "Need cylinders",
        "department": "sales",
        "name": "Ivan Petrov",
        "city": "Moscow",
    }
    client = _PhoneTransferClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)

    assert any(record_name.endswith("_phone_utt8") for record_name in client.record_names)
    assert any(record_name.endswith("_phone_confirm_utt9") for record_name in client.record_names)
    assert any(
        event["action"] == "dialog_decision"
        and event["details"]["from_stage"] == "PHONE"
        and event["details"]["to_stage"] == "PHONE_CONFIRM"
        for event in events
    )
    assert not any(event["action"] == "safe_finish" for event in events)
    assert client.continue_calls
    assert client.play_calls[-1] == ari_app.TRANSFER_SOUND_ID


def test_unconfirmed_phone_does_not_fall_through_to_generic_pipeline(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    stage_counts: dict[DialogStage, int] = {}

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        stage_counts[artifact.stage] = stage_counts.get(artifact.stage, 0) + 1
        transcripts = {
            DialogStage.ISSUE: "Need cylinders",
            DialogStage.NAME: "Ivan Petrov",
            DialogStage.CITY: "Москва",
            DialogStage.PHONE: "920.032.0355" if stage_counts[artifact.stage] == 1 else "",
            DialogStage.PHONE_CONFIRM: "нет",
        }
        return transcripts[artifact.stage], artifact.details()

    def fail_pipeline(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise AssertionError("generic reply pipeline must not run while PHONE is unconfirmed")

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "run_pipeline_from_transcript", fail_pipeline)
    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-unconfirmed/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-unconfirmed", channel_id="ch-unconfirmed", artifact_dir=tmp_path / "artifacts")
    client = _UnconfirmedPhoneClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)

    assert client.hangups == 1
    assert any(event["action"] == "safe_finish" and event["reason"] == "phone_retry_limit" for event in events)
    phrase_events = [event for event in events if event["action"] == "safe_finish_phrase_resolved"]
    assert phrase_events
    assert phrase_events[-1]["details"]["safe_finish_reason"] == "phone_retry_limit"
    assert phrase_events[-1]["details"]["phrase_key"] == "phone_not_confirmed"
    assert "\u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430" in phrase_events[-1]["details"]["phrase_text"]
    assert phrase_events[-1]["media"] == ari_app.SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID
    assert phrase_events[-1]["sound_id"] == ari_app.SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID
    assert any(
        event["action"] == "safe_finish_phrase_played"
        and event["status"] == "ok"
        and event["media"] == ari_app.SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID
        for event in events
    )
    started_idx = next(i for i, event in enumerate(events) if event["action"] == "safe_finish_phrase_playback_started")
    finished_idx = next(i for i, event in enumerate(events) if event["action"] == "safe_finish_phrase_playback_finished")
    played_idx = next(i for i, event in enumerate(events) if event["action"] == "safe_finish_phrase_played")
    assert started_idx < finished_idx < played_idx
    assert events[started_idx]["details"]["payload"]["state"] == "queued"
    assert events[finished_idx]["status"] == "ok"
    assert events[played_idx]["status"] == "ok"
    assert client.call_order[-3:] == ["play", "wait", "hangup"]
    assert client.play_calls[-1] == ari_app.SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID
    assert client.continue_calls == []
    assert not any(event["action"] in {"pipeline_start", "build_response", "publish", "playback"} for event in events)
    records_path = tmp_path / "storage" / "callbacks" / "callback_records.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["call_id"] == "call-unconfirmed"
    assert records[0]["department"] == "sales"
    assert records[0]["issue"] == "Need cylinders"
    assert records[0]["name"] == "Ivan Petrov"
    assert records[0]["city"] == "Москва"
    assert records[0]["phone"] == "9200320355"
    assert records[0]["outcome_type"] == "safe_finish"
    assert records[0]["outcome_reason"] == "phone_retry_limit"
    assert records[0]["record_id"]
    assert records[0]["timestamp"]
    success = next(event for event in events if event["action"] == "persistence_success")
    assert success["details"]["outcome_type"] == "safe_finish"
    assert success["details"]["record_id"] == records[0]["record_id"]


def test_safe_finish_phrase_resolution_falls_back_to_baseline_when_reason_unknown() -> None:
    phrase_key, phrase_text, sound_id, media, available = ari_app._resolve_safe_finish_phrase(
        "unknown_safe_finish_reason",
        {ari_app.SAFE_FINISH_BASELINE_SOUND_ID: True},
    )

    assert phrase_key == "baseline"
    assert phrase_text == ari_app.SAFE_FINISH_BASELINE_PHRASE
    assert sound_id == ari_app.SAFE_FINISH_BASELINE_SOUND_ID
    assert media == ari_app.SAFE_FINISH_BASELINE_SOUND_ID
    assert available is True


def test_safe_finish_phrase_timeout_is_logged_without_successful_completion(tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    session = CallSession(call_id="call-safe-timeout", channel_id="ch-safe-timeout", artifact_dir=tmp_path / "artifacts")
    client = _SafeFinishTimeoutClient()

    played, _moh_started = asyncio.run(
        ari_app._play_safe_finish_phrase(
            client,
            _settings(tmp_path),
            "app",
            session,
            {ari_app.SAFE_FINISH_MISSING_REQUIRED_SOUND_ID: True},
            False,
            "city_retry_limit",
        )
    )
    events = _read_events(session)

    assert played is True
    assert client.call_order == ["play", "wait"]
    assert any(event["action"] == "safe_finish_phrase_playback_started" for event in events)
    assert any(
        event["action"] == "safe_finish_phrase_playback_timeout"
        and event["status"] == "handled"
        for event in events
    )
    assert not any(
        event["action"] == "safe_finish_phrase_playback_finished"
        and event["status"] == "ok"
        for event in events
    )
    assert not any(
        event["action"] == "safe_finish_phrase_played"
        and event["status"] == "ok"
        for event in events
    )


@pytest.mark.parametrize(
    ("reason", "phrase_key", "sound_id", "phrase_fragment"),
    [
        (
            "name_retry_limit",
            "missing_required_data",
            ari_app.SAFE_FINISH_MISSING_REQUIRED_SOUND_ID,
            "\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 "
            "\u0434\u0430\u043d\u043d\u044b\u0435",
        ),
        (
            "intent_not_resolved",
            "intent_not_resolved",
            ari_app.SAFE_FINISH_INTENT_NOT_RESOLVED_SOUND_ID,
            "\u043d\u0443\u0436\u043d\u044b\u0439 \u043e\u0442\u0434\u0435\u043b",
        ),
        (
            "phone_retry_limit",
            "phone_not_confirmed",
            ari_app.SAFE_FINISH_PHONE_NOT_CONFIRMED_SOUND_ID,
            "\u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430",
        ),
    ],
)
def test_safe_finish_phrase_resolution_uses_required_reason_variants(
    reason: str,
    phrase_key: str,
    sound_id: str,
    phrase_fragment: str,
) -> None:
    resolved = ari_app._resolve_safe_finish_phrase(reason, {sound_id: True})

    assert resolved == (phrase_key, ari_app.SAFE_FINISH_PHRASES[phrase_key], sound_id, sound_id, True)
    assert phrase_fragment in resolved[1]


def test_intent_clarify_recording_timeout_defaults_without_call_flow_exception(monkeypatch, tmp_path: Path) -> None:
    ari_app._reset_fallback_cache_for_tests()
    monkeypatch.setenv("PLAY_TEST", "0")
    monkeypatch.setenv("PHONE_CONFIRM_GUARD_DELAY_MS", "0")
    monkeypatch.delenv("DEPARTMENT_INTENT_DEFAULT", raising=False)
    for sound_id in ari_app._SYSTEM_SOUND_TEXTS:
        ari_app._system_sound_status[sound_id] = True

    transcripts = {
        DialogStage.ISSUE: "I need help",
        DialogStage.NAME: "Ivan Petrov",
        DialogStage.CITY: "Москва",
        DialogStage.PHONE: "920.032.0355",
        DialogStage.PHONE_CONFIRM: "да",
    }

    def fake_transcribe(_settings: Settings, artifact: ari_app.TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
        return transcripts.get(artifact.stage, ""), artifact.details()

    class _FakeTTS:
        def synthesize(self, _text: str) -> bytes:
            return b"RIFFconfirm"

    monkeypatch.setattr(ari_app, "_transcribe_audio_artifact", fake_transcribe)
    monkeypatch.setattr(ari_app, "SileroTTS", _FakeTTS)
    monkeypatch.setattr(
        ari_app,
        "publish_wav_to_asterisk",
        lambda *_args, **_kwargs: {
            "ok": True,
            "sound_id": "sound:ai_secretary/call-clarify-timeout/phone_confirm_prompt",
            "remote_path": "/tmp/phone_confirm_prompt.wav",
            "error": None,
            "details": {},
        },
    )

    session = CallSession(call_id="call-clarify-timeout", channel_id="ch-clarify-timeout", artifact_dir=tmp_path / "artifacts")
    client = _IntentClarifyTimeoutClient()

    asyncio.run(ari_app.handle_call(client, _settings(tmp_path), "app", session))
    events = _read_events(session)
    profile = json.loads((session.artifact_dir / "profile.json").read_text(encoding="utf-8"))

    assert profile["department"] == "sales"
    assert profile["department_defaulted"] is True
    assert client.continue_calls
    assert not any(event["action"] == "call_flow_exception" for event in events)
    handled_timeout = [event for event in events if event["action"] == "record_wait" and event["reason"] == "timeout"]
    assert len(handled_timeout) == 2
    decision = [event for event in events if event["action"] == "dialog_decision" and event["details"]["from_stage"] == "INTENT_CLARIFY"][-1]
    assert decision["details"]["retry_count"] == 2
    assert decision["details"]["retry_limit"] == 2
    assert decision["details"]["default_resolution"] is True
