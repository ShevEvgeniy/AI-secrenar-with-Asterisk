"""Tests for NODE-007 bounded department routing."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, CallState, DialogStage
from ai_secretary.telephony.dialog import apply_turn
from ai_secretary.telephony.routing import classify_department_intent, route_for_department


class _TransferClient:
    def __init__(self) -> None:
        self.play_calls: list[tuple[str, str]] = []
        self.continue_calls: list[dict[str, Any]] = []

    async def moh_stop_safe(self, _channel_id: str) -> dict[str, Any]:
        return {"ok": True}

    async def play_safe(self, channel_id: str, media: str) -> dict[str, Any]:
        self.play_calls.append((channel_id, media))
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
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_CONTEXT", "from-logistics")
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_EXTEN", "delivery_real")
    monkeypatch.setenv("DEPARTMENT_ROUTE_DELIVERY_PRIORITY", "2")
    client = _TransferClient()
    session = CallSession(call_id="call-delivery", channel_id="ch-delivery", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Where is my order delivery tracking",
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


def test_unclear_intent_transfer_phrase_matches_default_department(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DEPARTMENT_INTENT_DEFAULT", "accounting")
    monkeypatch.setenv("DEPARTMENT_ROUTE_ACCOUNTING_EXTEN", "acct_real")
    client = _TransferClient()
    session = CallSession(call_id="call-unclear", channel_id="ch-unclear", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "I need help",
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
