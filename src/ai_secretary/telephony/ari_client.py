"""Asterisk ARI client abstraction."""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx
import websockets


async def _ws_connect(url: str, headers: dict[str, str]):
    """Connect to websocket with compatible headers parameter."""
    try:
        return await websockets.connect(url, additional_headers=headers)
    except TypeError:
        return await websockets.connect(url, extra_headers=headers)


@dataclass
class AriClient:
    """Minimal ARI client wrapper."""

    base_url: str
    username: str
    password: str

    def _http_url(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        path_part = path if path.startswith("/") else f"/{path}"
        return f"{base}{path_part}"

    def _ws_base(self) -> str:
        if self.base_url.startswith("https://"):
            return "wss://" + self.base_url[len("https://") :].rstrip("/")
        if self.base_url.startswith("http://"):
            return "ws://" + self.base_url[len("http://") :].rstrip("/")
        return self.base_url.rstrip("/")

    def _auth_header(self) -> str:
        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    async def answer(self, channel_id: str) -> None:
        """Answer a channel via ARI."""
        url = self._http_url(f"/channels/{channel_id}/answer")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.post(url)
            response.raise_for_status()

    async def hangup(self, channel_id: str) -> None:
        """Hangup a channel via ARI."""
        url = self._http_url(f"/channels/{channel_id}")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.delete(url)
            response.raise_for_status()

    async def get_channel(self, channel_id: str) -> dict[str, Any]:
        """Get channel details via ARI."""
        url = self._http_url(f"/channels/{channel_id}")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def play(self, channel_id: str, media: str) -> dict[str, Any]:
        """Play media on a channel."""
        url = self._http_url(f"/channels/{channel_id}/play")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.post(url, params={"media": media})
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise httpx.HTTPStatusError(
                    f"ARI play failed: POST {url} status={exc.response.status_code}",
                    request=exc.request,
                    response=exc.response,
                ) from exc
            return response.json()

    async def moh_start(self, channel_id: str, moh_class: str = "default") -> None:
        """Start MOH on a channel."""
        url = self._http_url(f"/channels/{channel_id}/moh")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.post(url, params={"mohClass": moh_class})
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = (exc.response.text or "")[:500]
                print("MOH_START_STATUS", exc.response.status_code, body)
                raise httpx.HTTPStatusError(
                    "ARI moh_start failed",
                    request=exc.request,
                    response=exc.response,
                ) from exc

    async def moh_stop(self, channel_id: str) -> None:
        """Stop MOH on a channel."""
        url = self._http_url(f"/channels/{channel_id}/moh")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.delete(url)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                body = (exc.response.text or "")[:500]
                print("MOH_STOP_STATUS", exc.response.status_code, body)
                raise httpx.HTTPStatusError(
                    "ARI moh_stop failed",
                    request=exc.request,
                    response=exc.response,
                ) from exc

    async def record(
        self,
        channel_id: str,
        name: str,
        format: str = "wav",
        max_duration_seconds: int = 10,
        beep: bool = False,
        if_exists: str = "overwrite",
    ) -> dict[str, Any]:
        """Start recording a channel."""
        url = self._http_url(f"/channels/{channel_id}/record")
        params = {
            "name": name,
            "format": format,
            "maxDurationSeconds": str(max_duration_seconds),
            "beep": str(beep).lower(),
            "ifExists": if_exists,
        }
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=10.0) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            return response.json()

    async def wait_for_recording_finished(
        self,
        app_name: str,
        name: str,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Wait for RecordingFinished or RecordingFailed event for a recording name."""
        async def _wait() -> dict[str, Any]:
            async for event in self.ws_events(app_name=app_name, subscribe_all=True):
                event_type = event.get("type")
                recording = event.get("recording", {})
                if recording.get("name") != name:
                    continue
                if event_type in {"RecordingFinished", "RecordingFailed"}:
                    return event
            return {}

        return await asyncio.wait_for(_wait(), timeout=timeout)

    async def download_recording(self, name: str, dest_path: str) -> None:
        """Download a stored recording to a local file."""
        url = self._http_url(f"/recordings/stored/{name}/file")
        async with httpx.AsyncClient(auth=(self.username, self.password), timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            Path(dest_path).write_bytes(response.content)

    async def ws_events(self, app_name: str, subscribe_all: bool = True) -> AsyncIterator[dict[str, Any]]:
        """Yield events from ARI WebSocket."""
        ws_base = self._ws_base()
        subscribe = "true" if subscribe_all else "false"
        ws_url = f"{ws_base}/events?app={app_name}&subscribeAll={subscribe}"
        headers = {"Authorization": self._auth_header()}

        print(f"websockets_version {websockets.__version__}")
        print("ARI_WS_URL", ws_url)
        print("ARI_WS_CONNECTING")
        try:
            async with await _ws_connect(ws_url, headers) as ws:
                print("ARI_WS_CONNECTED")
                async for message in ws:
                    try:
                        payload = json.loads(message)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(payload, dict):
                        yield payload
        except Exception as exc:
            print("ARI_WS_CONNECT_ERROR", repr(exc))
            raise
