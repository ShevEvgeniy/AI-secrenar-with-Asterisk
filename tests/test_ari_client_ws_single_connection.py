"""Tests for shared ARI websocket connection reuse."""

from __future__ import annotations

import asyncio
import json

from ai_secretary.telephony.ari_client import AriClient


def test_wait_for_recording_finished_reuses_single_ws_connection(monkeypatch) -> None:
    connect_calls: list[str] = []
    messages: asyncio.Queue[str | None] = asyncio.Queue()

    class FakeWebSocket:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        def __aiter__(self):
            return self

        async def __anext__(self):
            item = await messages.get()
            if item is None:
                raise StopAsyncIteration
            return item

    async def fake_connect(url, *args, **kwargs):
        connect_calls.append(url)
        return FakeWebSocket()

    monkeypatch.setattr("ai_secretary.telephony.ari_client.websockets.connect", fake_connect)

    async def _run() -> None:
        client = AriClient(base_url="http://localhost:8088/ari", username="u", password="p")

        async def _wait_for_subscriber() -> None:
            for _ in range(50):
                if len(client._ws_subscribers) >= 1:
                    return
                await asyncio.sleep(0.01)
            raise AssertionError("subscriber was not registered in time")

        first_wait = asyncio.create_task(client.wait_for_recording_finished("app", "rec1", timeout=1.0))
        await _wait_for_subscriber()
        await messages.put(json.dumps({"type": "RecordingFinished", "recording": {"name": "rec1"}}))
        first_event = await first_wait
        assert first_event.get("type") == "RecordingFinished"

        second_wait = asyncio.create_task(client.wait_for_recording_finished("app", "rec2", timeout=1.0))
        await _wait_for_subscriber()
        await messages.put(json.dumps({"type": "RecordingFinished", "recording": {"name": "rec2"}}))
        second_event = await second_wait
        assert second_event.get("type") == "RecordingFinished"

        assert len(connect_calls) == 1

        await messages.put(None)
        await client.close_ws()

    asyncio.run(_run())
