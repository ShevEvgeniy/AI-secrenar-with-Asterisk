"""Tests for NODE-007 bounded department routing."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, CallState, DialogStage
from ai_secretary.telephony.dialog import apply_turn
from ai_secretary.telephony.routing import business_hours_for_department, classify_department_intent, route_for_department


class _TransferClient:
    def __init__(self) -> None:
        self.play_calls: list[tuple[str, str]] = []
        self.continue_calls: list[dict[str, Any]] = []
        self.hangup_calls: list[str] = []
        self.playback_waits: list[dict[str, Any]] = []
        self.call_order: list[str] = []

    async def moh_stop_safe(self, _channel_id: str) -> dict[str, Any]:
        return {"ok": True}

    async def play_safe(self, channel_id: str, media: str) -> dict[str, Any]:
        self.play_calls.append((channel_id, media))
        self.call_order.append("play")
        return {
            "ok": True,
            "reason": "ok",
            "http_status": 200,
            "details": {"payload": {"id": f"playback-{len(self.play_calls)}"}},
        }

    async def wait_for_playback_finished(self, app_name: str, playback_id: str, timeout: int) -> dict[str, Any]:
        self.playback_waits.append({"app_name": app_name, "playback_id": playback_id, "timeout": timeout})
        self.call_order.append("wait")
        return {"type": "PlaybackFinished"}

    async def continue_safe(self, channel_id: str, context: str, extension: str, priority: int) -> dict[str, Any]:
        self.call_order.append("continue")
        self.continue_calls.append(
            {
                "channel_id": channel_id,
                "context": context,
                "extension": extension,
                "priority": priority,
            }
        )
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}

    async def hangup_safe(self, channel_id: str) -> dict[str, Any]:
        self.call_order.append("hangup")
        self.hangup_calls.append(channel_id)
        return {"ok": True, "reason": "ok", "http_status": 200, "details": {}}


def _events(session: CallSession) -> list[dict[str, Any]]:
    return [json.loads(line) for line in session.events_path.read_text(encoding="utf-8").splitlines()]


def test_department_intent_keyword_mapping() -> None:
    cases = {
        "Need a price quote for cylinders": "sales",
        "Please connect me about invoice payment documents": "accounting",
        "Where is my order delivery tracking": "delivery",
    }

    for issue, expected in cases.items():
        decision = classify_department_intent(issue)
        assert decision.intent == expected
        assert decision.department == expected
        assert decision.reason == f"matched_{expected}"


def test_department_transfer_phrase_mapping_is_bounded() -> None:
    assert ari_app.TRANSFER_PHRASES == {
        "sales": "Хорошо, я соединяю вас с отделом продаж.",
        "accounting": "Хорошо, я соединяю вас с бухгалтерией.",
        "delivery": "Хорошо, я соединяю вас с отделом доставки.",
    }
    assert ari_app.TRANSFER_SOUND_IDS == {
        "sales": ari_app.TRANSFER_SOUND_ID,
        "accounting": ari_app.TRANSFER_ACCOUNTING_SOUND_ID,
        "delivery": ari_app.TRANSFER_DELIVERY_SOUND_ID,
    }


def test_after_hours_phrase_mapping_is_bounded() -> None:
    assert ari_app.AFTER_HOURS_SOUND_IDS == {
        "sales": "sound:ai_secretary/_system/after_hours_sales_v2",
        "accounting": "sound:ai_secretary/_system/after_hours_accounting_v2",
        "delivery": "sound:ai_secretary/_system/after_hours_delivery_v2",
    }
    assert ari_app.AFTER_HOURS_SALES_SOUND_ID == "sound:ai_secretary/_system/after_hours_sales_v2"
    assert ari_app.AFTER_HOURS_ACCOUNTING_SOUND_ID == "sound:ai_secretary/_system/after_hours_accounting_v2"
    assert ari_app.AFTER_HOURS_DELIVERY_SOUND_ID == "sound:ai_secretary/_system/after_hours_delivery_v2"
    assert ari_app.AFTER_HOURS_PHRASES == {
        "sales": (
            "Отдел продаж сейчас не работает. Мы записали ваше обращение, и отдел продаж "
            "перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
        ),
        "accounting": (
            "Бухгалтерия сейчас не работает. Мы записали ваше обращение, и бухгалтерия "
            "перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
        ),
        "delivery": (
            "Отдел доставки сейчас не работает. Мы записали ваше обращение, и отдел доставки "
            "перезвонит вам в рабочее время. Спасибо за звонок. До свидания."
        ),
    }


def test_business_hours_contract_supports_schedule_and_override(monkeypatch) -> None:
    monkeypatch.delenv("BUSINESS_HOURS_MODE", raising=False)
    monkeypatch.setenv("BUSINESS_HOURS_TZ", "Europe/Moscow")
    moscow_tz = timezone(timedelta(hours=3))
    monday_10 = datetime(2026, 5, 4, 10, 0, tzinfo=moscow_tz)
    saturday_10 = datetime(2026, 5, 2, 10, 0, tzinfo=moscow_tz)

    working = business_hours_for_department("sales", now=monday_10)
    after = business_hours_for_department("sales", now=saturday_10)

    assert working.mode == "working_hours"
    assert working.reason == "within_schedule"
    assert working.start == "09:00"
    assert working.end == "18:00"
    assert working.days == (0, 1, 2, 3, 4)
    assert after.mode == "after_hours"
    assert after.reason == "outside_schedule"

    monkeypatch.setenv("DEPARTMENT_WORKING_HOURS_SALES_MODE", "after_hours")
    forced = business_hours_for_department("sales", now=monday_10)
    assert forced.mode == "after_hours"
    assert forced.reason == "mode_override"


def test_unclear_department_intent_explicitly_defaults_to_sales(monkeypatch) -> None:
    monkeypatch.delenv("DEPARTMENT_INTENT_DEFAULT", raising=False)

    decision = classify_department_intent("I need help")

    assert decision.intent == "unclear"
    assert decision.department == "sales"
    assert decision.reason == "unclear_default_sales"
    assert decision.target.extension == "sales_real"


def test_department_routes_use_explicit_config_contract(monkeypatch) -> None:
    monkeypatch.setenv("DEPARTMENT_ROUTE_ACCOUNTING_CONTEXT", "from-company")
    monkeypatch.setenv("DEPARTMENT_ROUTE_ACCOUNTING_EXTEN", "acct_real")
    monkeypatch.setenv("DEPARTMENT_ROUTE_ACCOUNTING_PRIORITY", "3")

    target = route_for_department("accounting")

    assert target.to_dict() == {
        "department": "accounting",
        "context": "from-company",
        "extension": "acct_real",
        "priority": 3,
    }


def test_issue_turn_persists_department_intent_artifact_fields() -> None:
    state, profile = apply_turn(DialogStage.ISSUE, {}, "Invoice payment question")

    assert state == DialogStage.NAME
    assert profile["department_intent"] == "accounting"
    assert profile["department"] == "accounting"
    assert profile["department_intent_reason"] == "matched_accounting"
    assert profile["department_intent_scores"]["accounting"] > 0


def test_transfer_uses_detected_department_target_and_logs_decision(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BUSINESS_HOURS_MODE", "working_hours")
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_CONTEXT", "from-logistics")
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_EXTEN", "delivery_real")
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_PRIORITY", "2")
    client = _TransferClient()
    session = CallSession(call_id="call-delivery", channel_id="ch-delivery", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Where is my order delivery tracking",
        "name": "Ivan Petrov",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
    }

    transferred, moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.TRANSFER_DELIVERY_SOUND_ID: True},
            moh_started=True,
        )
    )

    assert transferred is True
    assert moh_started is False
    assert client.play_calls == [("ch-delivery", ari_app.TRANSFER_DELIVERY_SOUND_ID)]
    assert client.continue_calls == [
        {
            "channel_id": "ch-delivery",
            "context": "from-logistics",
            "extension": "delivery_real",
            "priority": 2,
        }
    ]
    assert session.state == CallState.DONE
    events = _events(session)
    intent_event = next(event for event in events if event["action"] == "department_intent")
    assert intent_event["details"]["intent"] == "delivery"
    assert intent_event["details"]["target"] == {
        "department": "delivery",
        "context": "from-logistics",
        "extension": "delivery_real",
        "priority": 2,
    }
    phrase_event = next(event for event in events if event["action"] == "transfer_phrase_resolved")
    assert phrase_event["details"]["phrase_text"] == "Хорошо, я соединяю вас с отделом доставки."
    assert phrase_event["details"]["department_sound_id"] == ari_app.TRANSFER_DELIVERY_SOUND_ID
    assert phrase_event["details"]["resolved_sound_id"] == ari_app.TRANSFER_DELIVERY_SOUND_ID
    transfer_event = next(event for event in events if event["action"] == "transfer")
    assert transfer_event["details"]["department"] == "delivery"
    hours_event = next(event for event in events if event["action"] == "business_hours_decision")
    assert hours_event["details"]["mode"] == "working_hours"
    assert phrase_event["details"]["business_hours_mode"] == "working_hours"


def test_transfer_is_blocked_without_mandatory_name_city_and_confirmed_phone(tmp_path: Path) -> None:
    client = _TransferClient()
    session = CallSession(call_id="call-missing", channel_id="ch-missing", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Need cylinders",
        "phone_digits": "9200320355",
        "phone_confirmed": False,
        "early_transfer_requested": True,
    }

    transferred, _moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(client, session, {ari_app.TRANSFER_SOUND_ID: True}, moh_started=False)
    )

    assert transferred is False
    assert client.play_calls == []
    assert client.continue_calls == []
    events = _events(session)
    blocked = next(event for event in events if event["action"] == "transfer_blocked_missing_required_data")
    assert blocked["details"]["missing_required_fields"] == ["name", "city", "phone_confirmed"]
    assert blocked["details"]["early_transfer_requested"] is True


def test_after_hours_skips_transfer_after_required_data(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BUSINESS_HOURS_MODE", "after_hours")
    monkeypatch.setenv("AFTER_HOURS_GUARD_DELAY_MS", "0")
    client = _TransferClient()
    session = CallSession(call_id="call-after-hours", channel_id="ch-after-hours", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Invoice payment question",
        "name": "Ivan Petrov",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
        "department": "accounting",
        "department_intent": "accounting",
    }

    handled, moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.AFTER_HOURS_ACCOUNTING_SOUND_ID: True, ari_app.TRANSFER_ACCOUNTING_SOUND_ID: True},
            moh_started=True,
            app_name="app",
        )
    )

    assert handled is True
    assert moh_started is False
    assert client.play_calls == [("ch-after-hours", ari_app.AFTER_HOURS_ACCOUNTING_SOUND_ID)]
    assert client.playback_waits == [{"app_name": "app", "playback_id": "playback-1", "timeout": 20}]
    assert client.call_order == ["play", "wait", "hangup"]
    assert client.continue_calls == []
    assert client.hangup_calls == ["ch-after-hours"]
    assert session.state == CallState.DONE
    events = _events(session)
    hours_event = next(event for event in events if event["action"] == "business_hours_decision")
    assert hours_event["details"]["mode"] == "after_hours"
    phrase_event = next(event for event in events if event["action"] == "after_hours_phrase_resolved")
    assert phrase_event["details"]["department"] == "accounting"
    assert phrase_event["details"]["department_sound_id"] == ari_app.AFTER_HOURS_ACCOUNTING_SOUND_ID
    assert "\u0431\u0443\u0445\u0433\u0430\u043b\u0442\u0435\u0440\u0438\u044f" in phrase_event["details"]["phrase_text"].lower()
    barrier_event = next(event for event in events if event["action"] == "after_hours_playback_barrier")
    assert barrier_event["status"] == "ok"
    assert barrier_event["details"]["playback_id"] == "playback-1"
    assert barrier_event["details"]["timeout_seconds"] == 20
    assert barrier_event["details"]["guard_delay_ms"] == 0
    skipped = next(event for event in events if event["action"] == "transfer_skipped_after_hours")
    assert skipped["details"]["transfer_skipped"] is True
    assert skipped["details"]["business_hours_mode"] == "after_hours"
    assert skipped["details"]["after_hours_playback_completed"] is True
    assert not any(event["action"] == "transfer" for event in events)
    handoff = next(event for event in events if event["action"] == "after_hours_handoff")
    assert handoff["details"]["after_hours_playback_completed"] is True
    records_path = tmp_path / "callbacks" / "callback_records.jsonl"
    records = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["call_id"] == "call-after-hours"
    assert records[0]["department"] == "accounting"
    assert records[0]["issue"] == "Invoice payment question"
    assert records[0]["name"] == "Ivan Petrov"
    assert records[0]["city"] == "Moscow"
    assert records[0]["phone"] == "9200320355"
    assert records[0]["outcome_type"] == "after_hours_callback"
    assert records[0]["outcome_reason"] == "mode_override"
    assert records[0]["record_id"]
    assert records[0]["timestamp"]
    assert any(event["action"] == "persistence_attempt" for event in events)
    success = next(event for event in events if event["action"] == "persistence_success")
    assert success["details"]["path"].endswith("callbacks/callback_records.jsonl")
    assert success["details"]["record_id"] == records[0]["record_id"]


def test_after_hours_persistence_failure_is_fail_soft(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BUSINESS_HOURS_MODE", "after_hours")
    monkeypatch.setenv("AFTER_HOURS_GUARD_DELAY_MS", "0")
    monkeypatch.setattr(
        ari_app,
        "append_callback_record",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk unavailable")),
    )
    client = _TransferClient()
    session = CallSession(call_id="call-after-hours-fail-soft", channel_id="ch-after-hours-fail-soft", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Invoice payment question",
        "name": "Ivan Petrov",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
        "department": "accounting",
    }

    handled, _moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.AFTER_HOURS_ACCOUNTING_SOUND_ID: True},
            moh_started=False,
            app_name="app",
        )
    )

    assert handled is True
    assert client.call_order == ["play", "wait", "hangup"]
    assert session.state == CallState.DONE
    events = _events(session)
    assert any(event["action"] == "persistence_failure" for event in events)
    assert any(event["action"] == "after_hours_handoff" and event["status"] == "ok" for event in events)


def test_after_hours_completion_is_blocked_until_required_data(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BUSINESS_HOURS_MODE", "after_hours")
    client = _TransferClient()
    session = CallSession(call_id="call-after-hours-missing", channel_id="ch-after-hours-missing", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Need delivery tracking",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
        "department": "delivery",
    }

    handled, _moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.AFTER_HOURS_DELIVERY_SOUND_ID: True},
            moh_started=False,
        )
    )

    assert handled is False
    assert client.play_calls == []
    assert client.continue_calls == []
    assert client.hangup_calls == []
    events = _events(session)
    blocked = next(event for event in events if event["action"] == "transfer_blocked_missing_required_data")
    assert blocked["details"]["missing_required_fields"] == ["name"]
    assert not any(event["action"] == "after_hours_phrase_resolved" for event in events)


def test_unclear_intent_transfer_phrase_matches_default_department(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DEPARTMENT_INTENT_DEFAULT", "accounting")
    monkeypatch.setenv("DEPARTMENT_ROUTE_ACCOUNTING_EXTEN", "acct_real")
    client = _TransferClient()
    session = CallSession(call_id="call-unclear", channel_id="ch-unclear", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "I need help",
        "name": "Ivan Petrov",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
    }

    transferred, _moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.TRANSFER_ACCOUNTING_SOUND_ID: True},
            moh_started=False,
        )
    )

    assert transferred is True
    assert client.play_calls == [("ch-unclear", ari_app.TRANSFER_ACCOUNTING_SOUND_ID)]
    assert client.continue_calls[0]["extension"] == "acct_real"
    events = _events(session)
    phrase_event = next(event for event in events if event["action"] == "transfer_phrase_resolved")
    assert phrase_event["details"]["intent"] == "unclear"
    assert phrase_event["details"]["department"] == "accounting"
    assert phrase_event["details"]["phrase_text"] == "Хорошо, я соединяю вас с бухгалтерией."
