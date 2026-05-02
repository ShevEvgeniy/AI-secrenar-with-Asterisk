"""Tests for NODE-001 sales real transfer target."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, CallState


class _TransferClient:
    def __init__(self) -> None:
        self.play_calls: list[tuple[str, str]] = []
        self.continue_calls: list[dict[str, Any]] = []
        self.moh_stop_calls = 0

    async def moh_stop_safe(self, _channel_id: str) -> dict[str, Any]:
        self.moh_stop_calls += 1
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


def test_transfer_defaults_to_sales_real_route(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("TRANSFER_CONTEXT", raising=False)
    monkeypatch.delenv("TRANSFER_EXTEN", raising=False)
    monkeypatch.delenv("TRANSFER_PRIORITY", raising=False)
    client = _TransferClient()
    session = CallSession(call_id="call-sales-real", channel_id="ch-sales-real", artifact_dir=tmp_path)
    session.dialog.profile = {
        "issue": "Need cylinders",
        "name": "Ivan Petrov",
        "city": "Moscow",
        "phone_digits": "9200320355",
        "phone_confirmed": True,
    }

    transferred, moh_started = asyncio.run(
        ari_app._play_transfer_and_continue(
            client,
            session,
            {ari_app.TRANSFER_SOUND_ID: True},
            moh_started=True,
        )
    )

    assert transferred is True
    assert moh_started is False
    assert client.play_calls == [("ch-sales-real", ari_app.TRANSFER_SOUND_ID)]
    assert client.continue_calls == [
        {
            "channel_id": "ch-sales-real",
            "context": "from-internal",
            "extension": "sales_real",
            "priority": 1,
        }
    ]
    assert session.state == CallState.DONE
