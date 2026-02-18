"""Tests for ARI client MOH methods."""

import asyncio

import httpx

from ai_secretary.telephony.ari_client import AriClient


def test_ari_client_moh_calls(monkeypatch):
    captured = {"post": [], "delete": []}

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, params=None):
            captured["post"].append((url, params))
            request = httpx.Request("POST", url)
            return httpx.Response(200, request=request, json={"ok": True})

        async def delete(self, url):
            captured["delete"].append(url)
            request = httpx.Request("DELETE", url)
            return httpx.Response(200, request=request, json={"ok": True})

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = AriClient(base_url="http://localhost:8088/ari", username="u", password="p")
    asyncio.run(client.moh_start("321", moh_class="default"))
    asyncio.run(client.moh_stop("321"))

    assert captured["post"][0][0].endswith("/channels/321/moh")
    assert captured["post"][0][1] == {"mohClass": "default"}
    assert captured["delete"][0].endswith("/channels/321/moh")
