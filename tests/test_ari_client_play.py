"""Tests for ARI client play."""

import asyncio

import httpx

from ai_secretary.telephony.ari_client import AriClient


def test_ari_client_play_builds_url_and_params(monkeypatch):
    captured = {}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

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
    asyncio.run(client.play("123", "sound:demo-congrats"))

    assert captured["url"].endswith("/channels/123/play")
    assert captured["params"] == {"media": "sound:demo-congrats"}
