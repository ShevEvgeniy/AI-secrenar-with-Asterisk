"""Feature-flagged true-live STT proof helpers."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
import os
import socket
import time
from typing import Any

from ai_secretary.config.settings import Settings
from ai_secretary.stt.realtime_whisper import RealtimeTranscriptionConfig, RealtimeTranscriptionResult, RealtimeWhisperAdapter
from ai_secretary.telephony.call_session import DialogStage


DEFAULT_LIVE_STAGE_ALLOWLIST = "ISSUE,NAME,CITY,PHONE_CONFIRM"
LIVE_EXTERNAL_MEDIA_CHANNEL_PREFIX = "live-proof-ext-"
LIVE_SNOOP_CHANNEL_PREFIX = "live-proof-snoop-"


class LiveStreamingProofError(RuntimeError):
    def __init__(self, reason: str, message: str | None = None) -> None:
        super().__init__(message or reason)
        self.reason = reason


def is_live_external_media_channel(channel_id: str | None, channel_name: str | None = None) -> bool:
    values = [value for value in (channel_id, channel_name) if isinstance(value, str) and value]
    return any(
        value.startswith((LIVE_EXTERNAL_MEDIA_CHANNEL_PREFIX, LIVE_SNOOP_CHANNEL_PREFIX))
        or LIVE_EXTERNAL_MEDIA_CHANNEL_PREFIX in value
        or LIVE_SNOOP_CHANNEL_PREFIX in value
        for value in values
    )


@dataclass(frozen=True)
class LiveStreamingProofConfig:
    enabled: bool
    provider: str
    model: str
    fallback_to_batch: bool
    stage_allowlist: set[str]
    media_source: str
    topology: str
    host: str
    port: int
    sample_rate: int
    chunk_ms: int
    timeout_seconds: float
    use_live_transcript: bool


@dataclass(frozen=True)
class LiveStreamingProofResult:
    text: str
    first_delta_ms: int | None
    final_ms: int | None
    chunks_sent: int
    audio_started_before_recording_finished: bool | None
    recording_finish_to_final_ms: int | None
    live_vs_batch_delta_ms: int | None = None

    def details(self) -> dict[str, Any]:
        return {
            "stt_live_text": self.text,
            "stt_live_stream_latency_first_delta_ms": self.first_delta_ms,
            "stt_live_stream_latency_final_ms": self.final_ms,
            "stt_live_stream_audio_chunks_sent": self.chunks_sent,
            "stt_live_stream_audio_started_before_recording_finished": self.audio_started_before_recording_finished,
            "stt_live_stream_recording_finish_to_final_ms": self.recording_finish_to_final_ms,
            "stt_live_vs_batch_delta_ms": self.live_vs_batch_delta_ms,
        }


@dataclass(frozen=True)
class LiveStreamingProofHandle:
    task: asyncio.Task[LiveStreamingProofResult]


def live_streaming_config() -> LiveStreamingProofConfig:
    return LiveStreamingProofConfig(
        enabled=_env_bool("STT_LIVE_STREAMING_ENABLED", False),
        provider=os.getenv("STT_LIVE_STREAMING_PROVIDER", "openai_realtime_whisper").strip().lower(),
        model=os.getenv("STT_LIVE_STREAMING_MODEL", "gpt-realtime-whisper").strip() or "gpt-realtime-whisper",
        fallback_to_batch=_env_bool("STT_LIVE_STREAMING_FALLBACK_TO_BATCH", True),
        stage_allowlist=_stage_allowlist(),
        media_source=os.getenv("STT_LIVE_STREAMING_MEDIA_SOURCE", "ari_external_media_rtp").strip().lower(),
        topology=os.getenv("STT_LIVE_STREAMING_TOPOLOGY", "snoop_external_media_rtp").strip().lower(),
        host=os.getenv("STT_LIVE_STREAMING_RTP_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_env_int("STT_LIVE_STREAMING_RTP_PORT", 0),
        sample_rate=_env_int("STT_LIVE_STREAMING_SAMPLE_RATE", 24000),
        chunk_ms=_env_int("STT_LIVE_STREAMING_CHUNK_MS", 200),
        timeout_seconds=float(os.getenv("STT_LIVE_STREAMING_TIMEOUT_SECONDS", "12") or "12"),
        use_live_transcript=_env_bool("STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT", False),
    )


def live_streaming_stage_allowed(stage: DialogStage, config: LiveStreamingProofConfig | None = None) -> bool:
    config = config or live_streaming_config()
    return stage.value in config.stage_allowlist and stage != DialogStage.PHONE


def _openai_api_key_usable(api_key: str | None) -> bool:
    value = (api_key or "").strip()
    if not value:
        return False
    lowered = value.lower()
    placeholders = {"changeme", "change-me", "placeholder", "your-api-key", "your_openai_api_key", "test", "dummy"}
    return lowered not in placeholders and not lowered.startswith(("sk-placeholder", "sk-test", "sk-dummy"))


async def run_live_streaming_proof(
    *,
    settings: Settings,
    client: Any,
    app_name: str,
    call_id: str,
    channel_id: str,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    record_started_at: float,
    recording_finished_at: Callable[[], float | None],
    log_metric: Callable[[str, dict[str, Any], str, str | None], None],
    config: LiveStreamingProofConfig | None = None,
) -> LiveStreamingProofResult:
    handle = await start_live_streaming_proof(
        settings=settings,
        client=client,
        app_name=app_name,
        call_id=call_id,
        channel_id=channel_id,
        stage=stage,
        turn_idx=turn_idx,
        record_name=record_name,
        record_started_at=record_started_at,
        recording_finished_at=recording_finished_at,
        log_metric=log_metric,
        config=config,
    )
    return await handle.task


async def start_live_streaming_proof(
    *,
    settings: Settings,
    client: Any,
    app_name: str,
    call_id: str,
    channel_id: str,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    record_started_at: float,
    recording_finished_at: Callable[[], float | None],
    log_metric: Callable[[str, dict[str, Any], str, str | None], None],
    config: LiveStreamingProofConfig | None = None,
) -> LiveStreamingProofHandle:
    config = config or live_streaming_config()
    if not config.enabled:
        raise RuntimeError("live streaming proof is disabled")
    if config.provider != "openai_realtime_whisper":
        raise RuntimeError(f"unsupported live streaming provider: {config.provider}")
    if not live_streaming_stage_allowed(stage, config):
        raise RuntimeError(f"stage is not allowlisted for live streaming proof: {stage.value}")
    if is_live_external_media_channel(channel_id):
        raise LiveStreamingProofError("external_media_channel_excluded")
    if not _openai_api_key_usable(settings.openai_api_key):
        raise LiveStreamingProofError("openai_api_key_missing_or_invalid")

    log_metric("stt_live_stream_probe_started", _base_details(config, stage, turn_idx, record_name), "start", None)
    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    source = _AriExternalMediaRtpSource(
        client=client,
        app_name=app_name,
        call_id=call_id,
        channel_id=channel_id,
        stage=stage,
        turn_idx=turn_idx,
        record_name=record_name,
        config=config,
        queue=queue,
        recording_finished_at=recording_finished_at,
        log_metric=log_metric,
    )
    await source.start()
    log_metric("stt_live_stream_session_started", _base_details(config, stage, turn_idx, record_name), "ok", None)

    task = asyncio.create_task(
        _run_live_streaming_adapter(
            settings=settings,
            source=source,
            queue=queue,
            stage=stage,
            turn_idx=turn_idx,
            record_name=record_name,
            recording_finished_at=recording_finished_at,
            log_metric=log_metric,
            config=config,
        ),
        name=f"live-stt-proof-{call_id}-{turn_idx}",
    )
    return LiveStreamingProofHandle(task=task)


async def _run_live_streaming_adapter(
    *,
    settings: Settings,
    source: "_AriExternalMediaRtpSource",
    queue: asyncio.Queue[bytes | None],
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    recording_finished_at: Callable[[], float | None],
    log_metric: Callable[[str, dict[str, Any], str, str | None], None],
    config: LiveStreamingProofConfig,
) -> LiveStreamingProofResult:

    adapter = RealtimeWhisperAdapter(_realtime_config(settings, config))
    first_audio_at: float | None = None

    async def _chunks() -> AsyncIterator[bytes]:
        nonlocal first_audio_at
        while True:
            chunk = await queue.get()
            if chunk is None:
                return
            if first_audio_at is None:
                first_audio_at = time.perf_counter()
            yield chunk

    def _on_adapter_metric(action: str, details: dict[str, Any]) -> None:
        mapping = {
            "stt_stream_audio_chunk_sent": "stt_live_stream_audio_chunk_sent",
            "stt_stream_openai_session_config_sent": "stt_live_openai_session_config_sent",
            "stt_stream_openai_session_config_ok": "stt_live_openai_session_config_ok",
            "stt_stream_openai_session_config_failed": "stt_live_openai_session_config_failed",
            "stt_stream_openai_audio_chunk_sent": "stt_live_openai_audio_chunk_sent",
            "stt_stream_openai_audio_chunks_sent_count": "stt_live_openai_audio_chunks_sent_count",
            "stt_stream_openai_no_audio_received": "stt_live_openai_no_audio_received",
            "stt_stream_openai_no_delta_received": "stt_live_openai_no_delta_received",
            "stt_stream_first_delta_received": "stt_live_stream_first_delta_received",
            "stt_stream_final_received": "stt_live_stream_final_received",
        }
        live_action = mapping.get(action)
        if live_action:
            status = "sent" if live_action in {"stt_live_stream_audio_chunk_sent", "stt_live_openai_audio_chunk_sent"} else "ok"
            if live_action in {"stt_live_openai_session_config_failed", "stt_live_openai_no_audio_received", "stt_live_openai_no_delta_received"}:
                status = "handled"
            log_metric(live_action, {**_base_details(config, stage, turn_idx, record_name), **details}, status, None)
            if live_action == "stt_live_openai_audio_chunk_sent":
                log_metric("stt_live_stream_audio_chunk_sent", {**_base_details(config, stage, turn_idx, record_name), **details}, "sent", None)
            if live_action == "stt_live_stream_first_delta_received":
                log_metric("stt_live_openai_delta_received", {**_base_details(config, stage, turn_idx, record_name), **details}, "ok", None)
            if live_action == "stt_live_stream_final_received":
                log_metric("stt_live_openai_final_received", {**_base_details(config, stage, turn_idx, record_name), **details}, "ok", None)

    try:
        result = await asyncio.wait_for(
            adapter.transcribe_pcm_chunks(_chunks(), total_audio_ms=0, on_metric=_on_adapter_metric),
            timeout=config.timeout_seconds,
        )
    except Exception as exc:
        reason = _live_adapter_error_reason(exc)
        log_metric(
            "stt_live_stream_error",
            {
                **_base_details(config, stage, turn_idx, record_name),
                "error": repr(exc),
                "error_type": type(exc).__name__,
            },
            "handled",
            reason,
        )
        return LiveStreamingProofResult(
            text="",
            first_delta_ms=None,
            final_ms=None,
            chunks_sent=0,
            audio_started_before_recording_finished=(
                first_audio_at is not None
                and recording_finished_at() is not None
                and first_audio_at < recording_finished_at()
            ),
            recording_finish_to_final_ms=None,
        )
    finally:
        await source.close()

    recording_finished = recording_finished_at()
    final_at = time.perf_counter()
    first_delta_ms = result.first_delta_ms
    final_ms = result.final_ms
    audio_before_finish = (
        first_audio_at is not None and recording_finished is not None and first_audio_at < recording_finished
    )
    finish_to_final_ms = int((final_at - recording_finished) * 1000) if recording_finished is not None else None
    details = {
        **_base_details(config, stage, turn_idx, record_name),
        "stt_live_stream_latency_first_delta_ms": first_delta_ms,
        "stt_live_stream_latency_final_ms": final_ms,
        "stt_live_stream_audio_started_before_recording_finished": audio_before_finish,
        "stt_live_stream_recording_finish_to_final_ms": finish_to_final_ms,
        "stt_live_text": result.text,
    }
    log_metric("stt_live_stream_final_received", details, "ok", None)
    return LiveStreamingProofResult(
        text=result.text,
        first_delta_ms=first_delta_ms,
        final_ms=final_ms,
        chunks_sent=result.chunks_sent,
        audio_started_before_recording_finished=audio_before_finish,
        recording_finish_to_final_ms=finish_to_final_ms,
    )


def _live_adapter_error_reason(exc: Exception) -> str:
    message = repr(exc).lower()
    if "invalid_api_key" in message or "api key" in message:
        return "openai_realtime_invalid_api_key"
    if "connectionclosed" in type(exc).__name__.lower() or "connection closed" in message:
        return "openai_realtime_connection_closed"
    if isinstance(exc, asyncio.TimeoutError):
        return "openai_realtime_timeout"
    return "openai_realtime_error"


class _AriExternalMediaRtpSource:
    def __init__(
        self,
        *,
        client: Any,
        app_name: str,
        call_id: str,
        channel_id: str,
        stage: DialogStage,
        turn_idx: int,
        record_name: str,
        config: LiveStreamingProofConfig,
        queue: asyncio.Queue[bytes | None],
        recording_finished_at: Callable[[], float | None],
        log_metric: Callable[[str, dict[str, Any], str, str | None], None],
    ) -> None:
        self.client = client
        self.app_name = app_name
        self.call_id = call_id
        self.channel_id = channel_id
        self.stage = stage
        self.turn_idx = turn_idx
        self.record_name = record_name
        self.config = config
        self.queue = queue
        self.recording_finished_at = recording_finished_at
        self.log_metric = log_metric
        self.sock: socket.socket | None = None
        self.bridge_id = f"live-proof-{call_id}-{turn_idx}"
        self.external_channel_id = f"{LIVE_EXTERNAL_MEDIA_CHANNEL_PREFIX}{call_id}-{turn_idx}"
        self.snoop_channel_id = f"{LIVE_SNOOP_CHANNEL_PREFIX}{call_id}-{turn_idx}"
        self.reader_task: asyncio.Task[None] | None = None
        self._bridge_created = False
        self._external_media_created = False
        self._snoop_channel_created = False
        self._rtp_packets_received = 0
        self._pcm_chunks_created = 0

    async def start(self) -> None:
        if self.config.media_source != "ari_external_media_rtp":
            raise RuntimeError(f"unsupported live media source: {self.config.media_source}")
        if self.config.topology not in {"snoop_external_media_rtp", "bridge_original_external_media_rtp"}:
            topology_details = _base_details(self.config, self.stage, self.turn_idx, self.record_name)
            self.log_metric(
                "live_media_topology_failed",
                topology_details,
                "fail",
                "unsupported_live_media_topology",
            )
            raise RuntimeError(f"unsupported live media topology: {self.config.topology}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.config.host, self.config.port))
        self.sock.setblocking(False)
        host, port = self.sock.getsockname()
        details = {
            **_base_details(self.config, self.stage, self.turn_idx, self.record_name),
            "rtp_host": host,
            "rtp_port": port,
            "bridge_id": self.bridge_id,
            "external_channel_id": self.external_channel_id,
            "snoop_channel_id": self.snoop_channel_id,
        }
        self.log_metric("stt_live_rtp_listener_started", details, "ok", None)
        self.log_metric("live_media_topology_selected", details, "ok", None)
        try:
            await self._create_bridge(details)
            if self.config.topology == "snoop_external_media_rtp":
                await self._create_snoop_channel(details)
                await self._add_channel_to_bridge(
                    channel_id=self.snoop_channel_id,
                    channel_role="snoop",
                    details=details,
                )
            else:
                await self._add_channel_to_bridge(
                    channel_id=self.channel_id,
                    channel_role="original",
                    details=details,
                )
            await self._create_external_media(host, port, details)
            await self._add_channel_to_bridge(
                channel_id=self.external_channel_id,
                channel_role="external_media",
                details=details,
            )
        except Exception:
            await self.close()
            raise
        self.reader_task = asyncio.create_task(self._read_rtp(), name=f"live-stt-rtp-{self.call_id}-{self.turn_idx}")

    async def _create_bridge(self, details: dict[str, Any]) -> None:
        endpoint = f"/bridges/{self.bridge_id}"
        params = {"type": "mixing"}
        self._log_step("stt_live_bridge_create_attempt", details, "start", None, endpoint, params)
        method = getattr(self.client, "create_bridge_safe", None)
        if not callable(method):
            raise RuntimeError("ARI client lacks create_bridge_safe")
        result = await method(self.bridge_id, "mixing")
        if not result.get("ok", True):
            self._log_step(
                "stt_live_bridge_create_failed",
                {**details, **_result_details(result)},
                "fail",
                result.get("reason"),
                endpoint,
                params,
                result,
            )
            raise RuntimeError(f"create_bridge_safe failed: {result.get('reason')}")
        self._bridge_created = True
        self._log_step("stt_live_bridge_create_ok", {**details, **_result_details(result)}, "ok", None, endpoint, params, result)

    async def _create_snoop_channel(self, details: dict[str, Any]) -> None:
        endpoint = f"/channels/{self.channel_id}/snoop/{self.snoop_channel_id}"
        params = {"app": self.app_name, "spy": "in", "whisper": "none"}
        self._log_step("snoop_channel_started", details, "start", None, endpoint, params)
        method = getattr(self.client, "snoop_channel_safe", None)
        if not callable(method):
            self._log_step("snoop_channel_failed", details, "fail", "ari_client_snoop_unavailable", endpoint, params)
            self.log_metric("live_media_topology_failed", details, "fail", "ari_client_snoop_unavailable")
            raise RuntimeError("ARI client lacks snoop_channel_safe")
        result = await method(self.channel_id, self.app_name, self.snoop_channel_id, spy="in", whisper="none")
        result_details = {**details, **_result_details(result)}
        if not result.get("ok", True):
            self._log_step(
                "snoop_channel_failed",
                result_details,
                "fail",
                result.get("reason"),
                endpoint,
                params,
                result,
            )
            self.log_metric("live_media_topology_failed", result_details, "fail", result.get("reason"))
            raise RuntimeError(f"snoop_channel_safe failed: {result.get('reason')}")
        payload = result.get("details", {}).get("payload") if isinstance(result.get("details"), dict) else None
        if isinstance(payload, dict) and payload.get("id"):
            self.snoop_channel_id = str(payload["id"])
            result_details["snoop_channel_id"] = self.snoop_channel_id
        self._snoop_channel_created = True
        self._log_step("snoop_channel_started", result_details, "ok", None, endpoint, params, result)

    async def _add_channel_to_bridge(self, *, channel_id: str, channel_role: str, details: dict[str, Any]) -> None:
        endpoint = f"/bridges/{self.bridge_id}/addChannel"
        params = {"channel": channel_id}
        self._log_step(
            "stt_live_bridge_add_channel_attempt",
            {**details, "bridge_channel_id": channel_id, "bridge_channel_role": channel_role},
            "start",
            None,
            endpoint,
            params,
        )
        method = getattr(self.client, "add_channel_to_bridge_safe", None)
        if not callable(method):
            raise RuntimeError("ARI client lacks add_channel_to_bridge_safe")
        result = await method(self.bridge_id, channel_id)
        result_details = {
            **details,
            "bridge_channel_id": channel_id,
            "bridge_channel_role": channel_role,
            **_result_details(result),
        }
        if not result.get("ok", True):
            self._log_step(
                "stt_live_bridge_add_channel_failed",
                result_details,
                "fail",
                result.get("reason"),
                endpoint,
                params,
                result,
            )
            raise RuntimeError(f"add_channel_to_bridge_safe failed: {result.get('reason')}")
        self._log_step("stt_live_bridge_add_channel_ok", result_details, "ok", None, endpoint, params, result)

    async def _create_external_media(self, host: str, port: int, details: dict[str, Any]) -> None:
        endpoint = "/channels/externalMedia"
        params = {
            "app": self.app_name,
            "external_host": f"{host}:{port}",
            "channelId": self.external_channel_id,
            "format": _asterisk_slin_format(self.config.sample_rate),
            "direction": "both",
        }
        self._log_step("stt_live_external_media_create_attempt", details, "start", None, endpoint, params)
        method = getattr(self.client, "create_external_media_safe", None)
        if not callable(method):
            raise RuntimeError("ARI client lacks create_external_media_safe")
        result = await method(
            self.app_name,
            f"{host}:{port}",
            channel_id=self.external_channel_id,
            format=_asterisk_slin_format(self.config.sample_rate),
            direction="both",
        )
        result_details = {**details, **_result_details(result)}
        if not result.get("ok", True):
            self._log_step(
                "stt_live_external_media_create_failed",
                result_details,
                "fail",
                result.get("reason"),
                endpoint,
                params,
                result,
            )
            raise RuntimeError(f"create_external_media_safe failed: {result.get('reason')}")
        payload = result.get("details", {}).get("payload") if isinstance(result.get("details"), dict) else None
        if isinstance(payload, dict) and payload.get("id"):
            self.external_channel_id = str(payload["id"])
            result_details["external_media_channel_id"] = self.external_channel_id
        self._external_media_created = True
        self._log_step(
            "stt_live_external_media_create_ok",
            result_details,
            "ok",
            None,
            endpoint,
            params,
            result,
        )
        self.log_metric("stt_live_stream_media_started", result_details, "ok", None)

    def _log_step(
        self,
        action: str,
        details: dict[str, Any],
        status: str,
        reason: str | None,
        endpoint: str,
        params: dict[str, Any],
        result: dict[str, Any] | None = None,
    ) -> None:
        self.log_metric(
            action,
            {
                **details,
                "bridge_id": self.bridge_id,
                "original_channel_id": self.channel_id,
                "external_media_channel_id": self.external_channel_id,
                "snoop_channel_id": self.snoop_channel_id,
                "ari_endpoint": endpoint,
                "ari_request_params": params,
                **_http_details(result),
            },
            status,
            reason,
        )

    async def _read_rtp(self) -> None:
        assert self.sock is not None
        loop = asyncio.get_running_loop()
        deadline = time.perf_counter() + self.config.timeout_seconds
        try:
            while time.perf_counter() < deadline:
                finished_at = self.recording_finished_at()
                if finished_at is not None and time.perf_counter() - finished_at > 0.5:
                    break
                try:
                    packet = await asyncio.wait_for(loop.sock_recv(self.sock, 4096), timeout=0.2)
                except asyncio.TimeoutError:
                    continue
                self._rtp_packets_received += 1
                self.log_metric(
                    "stt_live_rtp_packet_received",
                    {
                        **_base_details(self.config, self.stage, self.turn_idx, self.record_name),
                        "packet_bytes": len(packet),
                        "stt_live_rtp_packets_received_count": self._rtp_packets_received,
                    },
                    "ok",
                    None,
                )
                payload = _rtp_payload(packet)
                if payload:
                    self._pcm_chunks_created += 1
                    self.log_metric(
                        "stt_live_pcm_chunk_created",
                        {
                            **_base_details(self.config, self.stage, self.turn_idx, self.record_name),
                            "chunk_bytes": len(payload),
                            "stt_live_pcm_chunks_created_count": self._pcm_chunks_created,
                        },
                        "ok",
                        None,
                    )
                    await self.queue.put(payload)
        finally:
            count_details = {
                **_base_details(self.config, self.stage, self.turn_idx, self.record_name),
                "stt_live_rtp_packets_received_count": self._rtp_packets_received,
                "stt_live_pcm_chunks_created_count": self._pcm_chunks_created,
            }
            self.log_metric("stt_live_rtp_packets_received_count", count_details, "ok", None)
            self.log_metric("stt_live_pcm_chunks_created_count", count_details, "ok", None)
            if self._rtp_packets_received == 0:
                self.log_metric("stt_live_openai_no_audio_received", count_details, "handled", "rtp_packets_zero")
            await self.queue.put(None)

    async def close(self) -> None:
        if self.reader_task is not None and not self.reader_task.done():
            self.reader_task.cancel()
        destroy = getattr(self.client, "destroy_bridge_safe", None)
        if callable(destroy) and self._bridge_created:
            details = _base_details(self.config, self.stage, self.turn_idx, self.record_name)
            self.log_metric(
                "stt_live_bridge_cleanup_attempt",
                {
                    **details,
                    "bridge_id": self.bridge_id,
                    "original_channel_id": self.channel_id,
                    "external_media_channel_id": self.external_channel_id,
                    "snoop_channel_id": self.snoop_channel_id,
                    "external_media_created": self._external_media_created,
                    "snoop_channel_created": self._snoop_channel_created,
                    "ari_endpoint": f"/bridges/{self.bridge_id}",
                },
                "start",
                None,
            )
            try:
                result = await destroy(self.bridge_id)
            except Exception as exc:
                result = {"ok": False, "reason": "cleanup_exception", "details": {"error": repr(exc)}}
            cleanup_details = {
                **details,
                "bridge_id": self.bridge_id,
                "original_channel_id": self.channel_id,
                "external_media_channel_id": self.external_channel_id,
                "snoop_channel_id": self.snoop_channel_id,
                "external_media_created": self._external_media_created,
                "snoop_channel_created": self._snoop_channel_created,
                "ari_endpoint": f"/bridges/{self.bridge_id}",
                **_result_details(result),
                **_http_details(result),
            }
            if result.get("ok", True):
                self.log_metric("stt_live_bridge_cleanup_done", cleanup_details, "ok", None)
                self._bridge_created = False
            else:
                self.log_metric(
                    "stt_live_bridge_cleanup_failed",
                    cleanup_details,
                    "fail",
                    result.get("reason"),
                )
        await self._cleanup_internal_channels()
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    async def _cleanup_internal_channels(self) -> None:
        hangup = getattr(self.client, "hangup_safe", None)
        if not callable(hangup):
            return
        for channel_id, created in (
            (self.external_channel_id, self._external_media_created),
            (self.snoop_channel_id, self._snoop_channel_created),
        ):
            if not created:
                continue
            with contextlib.suppress(Exception):
                await hangup(channel_id)


def _rtp_payload(packet: bytes) -> bytes:
    if len(packet) <= 12:
        return b""
    csrc_count = packet[0] & 0x0F
    header_len = 12 + (csrc_count * 4)
    if len(packet) <= header_len:
        return b""
    return packet[header_len:]


def _asterisk_slin_format(sample_rate: int) -> str:
    if sample_rate == 8000:
        return "slin"
    if sample_rate % 1000 == 0:
        return f"slin{sample_rate // 1000}"
    return "slin24"


def _result_details(result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    details = result.get("details")
    if isinstance(details, dict):
        return {"ari_result": {key: value for key, value in details.items() if key != "payload"}}
    return {}


def _http_details(result: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {}
    details = result.get("details")
    detail_map = details if isinstance(details, dict) else {}
    return {
        "ari_http_status": result.get("http_status"),
        "ari_failure_reason": result.get("reason"),
        "ari_response_body": detail_map.get("body"),
        "ari_request_method": detail_map.get("request_method"),
        "ari_request_url": detail_map.get("request_url"),
        "ari_request_path": detail_map.get("request_path"),
        "ari_request_query": detail_map.get("request_query"),
    }


def _realtime_config(settings: Settings, config: LiveStreamingProofConfig) -> RealtimeTranscriptionConfig:
    return RealtimeTranscriptionConfig(
        api_key=settings.openai_api_key,
        transcription_model=config.model,
        language="ru",
        sample_rate=config.sample_rate,
        chunk_ms=config.chunk_ms,
        timeout_seconds=config.timeout_seconds,
    )


def _base_details(config: LiveStreamingProofConfig, stage: DialogStage, turn_idx: int, record_name: str) -> dict[str, Any]:
    return {
        "stage": stage.value,
        "turn_idx": turn_idx,
        "record_name": record_name,
        "stt_live_streaming_enabled": config.enabled,
        "stt_live_streaming_provider": config.provider,
        "stt_live_streaming_model": config.model,
        "stt_live_streaming_media_source": config.media_source,
        "live_media_topology": config.topology,
    }


def _stage_allowlist() -> set[str]:
    raw = os.getenv("STT_LIVE_STREAMING_STAGE_ALLOWLIST", DEFAULT_LIVE_STAGE_ALLOWLIST)
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default
