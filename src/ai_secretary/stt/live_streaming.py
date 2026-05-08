"""Feature-flagged true-live STT proof helpers."""

from __future__ import annotations

import asyncio
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


@dataclass(frozen=True)
class LiveStreamingProofConfig:
    enabled: bool
    provider: str
    model: str
    fallback_to_batch: bool
    stage_allowlist: set[str]
    media_source: str
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


def live_streaming_config() -> LiveStreamingProofConfig:
    return LiveStreamingProofConfig(
        enabled=_env_bool("STT_LIVE_STREAMING_ENABLED", False),
        provider=os.getenv("STT_LIVE_STREAMING_PROVIDER", "openai_realtime_whisper").strip().lower(),
        model=os.getenv("STT_LIVE_STREAMING_MODEL", "gpt-realtime-whisper").strip() or "gpt-realtime-whisper",
        fallback_to_batch=_env_bool("STT_LIVE_STREAMING_FALLBACK_TO_BATCH", True),
        stage_allowlist=_stage_allowlist(),
        media_source=os.getenv("STT_LIVE_STREAMING_MEDIA_SOURCE", "ari_external_media_rtp").strip().lower(),
        host=os.getenv("STT_LIVE_STREAMING_RTP_HOST", "127.0.0.1").strip() or "127.0.0.1",
        port=_env_int("STT_LIVE_STREAMING_RTP_PORT", 0),
        sample_rate=_env_int("STT_LIVE_STREAMING_SAMPLE_RATE", 16000),
        chunk_ms=_env_int("STT_LIVE_STREAMING_CHUNK_MS", 200),
        timeout_seconds=float(os.getenv("STT_LIVE_STREAMING_TIMEOUT_SECONDS", "12") or "12"),
        use_live_transcript=_env_bool("STT_LIVE_STREAMING_USE_LIVE_TRANSCRIPT", False),
    )


def live_streaming_stage_allowed(stage: DialogStage, config: LiveStreamingProofConfig | None = None) -> bool:
    config = config or live_streaming_config()
    return stage.value in config.stage_allowlist and stage != DialogStage.PHONE


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
    config = config or live_streaming_config()
    if not config.enabled:
        raise RuntimeError("live streaming proof is disabled")
    if config.provider != "openai_realtime_whisper":
        raise RuntimeError(f"unsupported live streaming provider: {config.provider}")
    if not live_streaming_stage_allowed(stage, config):
        raise RuntimeError(f"stage is not allowlisted for live streaming proof: {stage.value}")

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
                log_metric("stt_live_stream_media_started", _base_details(config, stage, turn_idx, record_name), "ok", None)
            yield chunk

    def _on_adapter_metric(action: str, details: dict[str, Any]) -> None:
        mapping = {
            "stt_stream_audio_chunk_sent": "stt_live_stream_audio_chunk_sent",
            "stt_stream_first_delta_received": "stt_live_stream_first_delta_received",
            "stt_stream_final_received": "stt_live_stream_final_received",
        }
        live_action = mapping.get(action)
        if live_action:
            status = "sent" if live_action == "stt_live_stream_audio_chunk_sent" else "ok"
            log_metric(live_action, {**_base_details(config, stage, turn_idx, record_name), **details}, status, None)

    try:
        result = await asyncio.wait_for(
            adapter.transcribe_pcm_chunks(_chunks(), total_audio_ms=0, on_metric=_on_adapter_metric),
            timeout=config.timeout_seconds,
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
        self.external_channel_id = f"live-proof-ext-{call_id}-{turn_idx}"
        self.reader_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self.config.media_source != "ari_external_media_rtp":
            raise RuntimeError(f"unsupported live media source: {self.config.media_source}")
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
        }
        for name, args in (
            ("create_bridge_safe", (self.bridge_id, "mixing")),
            ("add_channel_to_bridge_safe", (self.bridge_id, self.channel_id)),
            (
                "create_external_media_safe",
                (self.app_name, f"{host}:{port}"),
            ),
            ("add_channel_to_bridge_safe", (self.bridge_id, self.external_channel_id)),
        ):
            method = getattr(self.client, name, None)
            if not callable(method):
                raise RuntimeError(f"ARI client lacks {name}")
            if name == "create_external_media_safe":
                result = await method(*args, channel_id=self.external_channel_id, format="slin16", direction="both")
            else:
                result = await method(*args)
            if not result.get("ok", True):
                raise RuntimeError(f"{name} failed: {result.get('reason')}")
        self.log_metric("stt_live_stream_media_started", details, "ok", None)
        self.reader_task = asyncio.create_task(self._read_rtp(), name=f"live-stt-rtp-{self.call_id}-{self.turn_idx}")

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
                payload = _rtp_payload(packet)
                if payload:
                    await self.queue.put(payload)
        finally:
            await self.queue.put(None)

    async def close(self) -> None:
        if self.reader_task is not None and not self.reader_task.done():
            self.reader_task.cancel()
        destroy = getattr(self.client, "destroy_bridge_safe", None)
        if callable(destroy):
            await destroy(self.bridge_id)
        if self.sock is not None:
            self.sock.close()


def _rtp_payload(packet: bytes) -> bytes:
    if len(packet) <= 12:
        return b""
    csrc_count = packet[0] & 0x0F
    header_len = 12 + (csrc_count * 4)
    if len(packet) <= header_len:
        return b""
    return packet[header_len:]


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
