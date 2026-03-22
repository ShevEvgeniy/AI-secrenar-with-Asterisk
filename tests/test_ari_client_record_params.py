"""Tests for ARI client record params."""

from __future__ import annotations

import asyncio

import httpx

from ai_secretary.telephony.ari_client import AriClient


def test_ari_client_record_builds_max_silence_and_beep(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            _ = args
            _ = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, params=None):
            captured["url"] = url
            captured["params"] = params
            request = httpx.Request("POST", url)
            return httpx.Response(200, request=request, json={"ok": True})

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = AriClient(base_url="http://localhost:8088/ari", username="u", password="p")
    asyncio.run(
        client.record(
            "123",
            "rec1",
            max_duration_seconds=6,
            max_silence_seconds=2,
            beep=True,
        )
    )

    assert str(captured["url"]).endswith("/channels/123/record")
    assert captured["params"] == {
        "name": "rec1",
        "format": "wav",
        "maxDurationSeconds": "6",
        "maxSilenceSeconds": "2",
        "beep": "true",
        "ifExists": "overwrite",
    }
