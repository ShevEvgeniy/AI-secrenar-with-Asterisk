"""Tests for ARI bridge/externalMedia proof diagnostics."""

from __future__ import annotations

import asyncio

import httpx

from ai_secretary.telephony.ari_client import AriClient


def test_ari_client_bridge_add_channel_safe_includes_http_diagnostics(monkeypatch) -> None:
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
            request = httpx.Request("POST", url, params=params)
            return httpx.Response(409, request=request, text="Channel currently recording")

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = AriClient(base_url="http://localhost:8088/ari", username="u", password="p")
    result = asyncio.run(client.add_channel_to_bridge_safe("bridge-1", "ch-1"))

    assert result["ok"] is False
    assert result["http_status"] == 409
    assert result["reason"] == "bridge_add_channel_http_error"
    assert result["details"]["body"] == "Channel currently recording"
    assert result["details"]["request_method"] == "POST"
    assert result["details"]["request_path"] == "/ari/bridges/bridge-1/addChannel"
    assert result["details"]["request_query"] == "channel=ch-1"
    assert captured["params"] == {"channel": "ch-1"}


def test_ari_client_snoop_channel_safe_posts_expected_endpoint(monkeypatch) -> None:
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
            request = httpx.Request("POST", url, params=params)
            return httpx.Response(200, request=request, json={"id": "live-proof-snoop-ch-1-1"})

    monkeypatch.setattr(httpx, "AsyncClient", DummyClient)

    client = AriClient(base_url="http://localhost:8088/ari", username="u", password="p")
    result = asyncio.run(client.snoop_channel_safe("ch-1", "app", "live-proof-snoop-ch-1-1", spy="in", whisper="none"))

    assert result["ok"] is True
    assert result["details"]["payload"] == {"id": "live-proof-snoop-ch-1-1"}
    assert captured["url"] == "http://localhost:8088/ari/channels/ch-1/snoop/live-proof-snoop-ch-1-1"
    assert captured["params"] == {"app": "app", "spy": "in", "whisper": "none"}
