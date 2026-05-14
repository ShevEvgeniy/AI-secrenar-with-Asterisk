"""Tests for the disabled-by-default gateway STT adapter."""

from __future__ import annotations

import asyncio
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from ai_secretary.stt.gateway_adapter import GatewaySttAdapterConfig, config_from_env, transcribe_via_gateway
from ai_secretary.stt.gateway_adapter_smoke import main as gateway_adapter_smoke_main
from ai_secretary.stt.gateway_adapter_smoke import run_smoke
from ai_secretary.stt.realtime_gateway import GATEWAY_ENDPOINT
from ai_secretary.telephony import ari_app
from ai_secretary.telephony.call_session import CallSession, DialogStage


def _write_audio(path: Path) -> Path:
    path.write_bytes(b"test-audio")
    return path


def _artifact(path: Path) -> ari_app.TranscriptionArtifact:
    return ari_app.TranscriptionArtifact(
        call_id="call-gateway",
        channel_id="ch-gateway",
        stage=DialogStage.NAME,
        turn_idx=1,
        record_name="call-gateway_name_utt1",
        path=path,
        size_bytes=path.stat().st_size,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _settings(tmp_path: Path) -> object:
    return type(
        "Settings",
        (),
        {
            "openai_api_key": "",
            "ari_url": "http://127.0.0.1:8088/ari",
            "demo_mode": "real",
            "storage_dir": tmp_path,
        },
    )()


def _events(session: CallSession) -> list[dict]:
    return [json.loads(line) for line in session.events_path.read_text(encoding="utf-8").splitlines()]


class _FakeGatewayServer:
    def __init__(self, response: dict, *, status_code: int = 200, token: str = "fake-token") -> None:
        self.response = response
        self.status_code = status_code
        self.token = token
        self.requests: list[dict] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        assert self._server is not None
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def __enter__(self) -> "_FakeGatewayServer":
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                owner.requests.append(
                    {
                        "path": self.path,
                        "authorization": self.headers.get("Authorization", ""),
                        "content_type": self.headers.get("Content-Type", ""),
                        "body": body,
                    }
                )
                if self.headers.get("Authorization") != f"Bearer {owner.token}":
                    self.send_response(403)
                    payload = {"ok": False, "error_type": "gateway_auth_failed"}
                else:
                    self.send_response(owner.status_code)
                    payload = owner.response
                data = json.dumps(payload).encode("utf-8")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc: object) -> None:
        assert self._server is not None
        assert self._thread is not None
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


def test_config_is_disabled_by_default() -> None:
    config = config_from_env({})

    assert config.enabled is False
    assert config.use_transcript_for_dialog is False
    assert config.gateway_url == ""
    assert config.gateway_token == ""
    assert config.timeout_ms == 10_000
    assert config.max_retries == 0
    assert config.log_transcript is False


def test_disabled_adapter_makes_no_gateway_call(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise AssertionError("disabled adapter must not call gateway")

    result = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(enabled=False),
            post=_post,
        )
    )

    assert result.attempted is False
    assert result.accepted is False
    assert result.reason == "gateway_stt_disabled"


def test_missing_gateway_url_or_token_falls_back_without_call(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise AssertionError("incomplete config must not call gateway")

    missing_url = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_token="token",
            ),
            post=_post,
        )
    )
    missing_token = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_url="https://gateway.example.test",
            ),
            post=_post,
        )
    )

    assert missing_url.reason == "missing_gateway_url"
    assert missing_token.reason == "missing_gateway_token"
    assert missing_url.accepted is False
    assert missing_token.accepted is False


def test_gateway_failures_fall_back_safely(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    config = GatewaySttAdapterConfig(
        enabled=True,
        use_transcript_for_dialog=True,
        gateway_url="https://gateway.example.test",
        gateway_token="gateway-token",
    )

    async def _auth_failed(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 401, {"ok": False, "error_type": "gateway_auth_failed", "transcript_text": "secret text"}

    async def _timeout(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise TimeoutError("timed out")

    async def _unavailable(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        raise OSError("connection refused")

    async def _malformed(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {"unexpected": True}

    async def _empty(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {"ok": True, "transcript_text_present": False}

    cases = [
        (_auth_failed, "gateway_auth_failed"),
        (_timeout, "gateway_timeout"),
        (_unavailable, "gateway_unavailable"),
        (_malformed, "malformed_response"),
        (_empty, "empty_transcript"),
    ]

    for post, reason in cases:
        result = asyncio.run(transcribe_via_gateway(audio_path, config=config, post=post))
        assert result.attempted is True
        assert result.accepted is False
        assert result.reason == reason
        assert result.text == ""


def test_local_fake_gateway_http_dry_run_accepts_without_real_secrets(tmp_path: Path, monkeypatch) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    transcript = "local fake transcript"
    lines: list[dict] = []
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with _FakeGatewayServer({"ok": True, "transcript_text_present": True, "transcript_text": transcript}) as gateway:
        config = config_from_env(
            {
                "STT_GATEWAY_STT_ENABLED": "true",
                "STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG": "true",
                "STT_GATEWAY_URL": gateway.url,
                "STT_GATEWAY_TOKEN": "fake-token",
                "STT_GATEWAY_TIMEOUT_MS": "1000",
                "STT_GATEWAY_LOG_TRANSCRIPT": "false",
            }
        )

        result = asyncio.run(
            transcribe_via_gateway(
                audio_path,
                config=config,
                context={"call_id": "local-dry-run"},
                log_event=lambda action, status, reason, details: lines.append(
                    {"action": action, "status": status, "reason": reason, "details": details}
                ),
            )
        )

    serialized_logs = json.dumps(lines, ensure_ascii=False)
    assert result.accepted is True
    assert result.attempted is True
    assert result.text == transcript
    assert result.details["transcript_text_present"] is True
    assert result.details["transcript_text_logged"] is False
    assert result.details["redaction_applied"] is True
    assert transcript not in serialized_logs
    assert len(gateway.requests) == 1
    assert gateway.requests[0]["path"].startswith(GATEWAY_ENDPOINT)
    assert gateway.requests[0]["authorization"] == "Bearer fake-token"
    assert gateway.requests[0]["body"] == b"test-audio"


def test_transcript_text_not_logged_by_default(tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    lines: list[dict] = []

    async def _post(_config: GatewaySttAdapterConfig, _audio: bytes) -> tuple[int, dict]:
        return 200, {
            "ok": True,
            "gateway_request_id": "gw_test",
            "transcript_text_present": True,
            "transcript_text": "секретный текст",
        }

    result = asyncio.run(
        transcribe_via_gateway(
            audio_path,
            config=GatewaySttAdapterConfig(
                enabled=True,
                use_transcript_for_dialog=True,
                gateway_url="https://gateway.example.test",
                gateway_token="gateway-token",
                log_transcript=False,
            ),
            post=_post,
            log_event=lambda action, status, reason, details: lines.append(
                {"action": action, "status": status, "reason": reason, "details": details}
            ),
        )
    )

    serialized_logs = json.dumps(lines, ensure_ascii=False)
    assert result.accepted is True
    assert result.text == "секретный текст"
    assert "секретный текст" not in serialized_logs
    assert result.details["transcript_text_logged"] is False


def test_business_path_gateway_flag_enabled_but_dialog_use_disabled_falls_back_to_batch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_path = _write_audio(tmp_path / "turn_name.wav")
    session = CallSession(
        call_id="call-dialog-use-disabled",
        channel_id="ch-dialog-use-disabled",
        artifact_dir=tmp_path / "artifacts",
    )
    monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
    monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
    monkeypatch.setenv("STT_GATEWAY_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "batch text")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    text, details = asyncio.run(
        ari_app._transcribe_audio_artifact_experimental(
            _settings(tmp_path),
            session,
            _artifact(audio_path),
        )
    )

    events = _events(session)
    assert text == "batch text"
    assert details["stt_gateway_fallback_to_batch"] is True
    assert details["stt_gateway_fallback_reason"] == "gateway_stt_dialog_use_disabled"
    assert any(event["action"] == "gateway_stt_fallback_to_batch" for event in events)
    assert not any(event["action"] == "gateway_stt_request_started" for event in events)


def test_smoke_can_request_gateway_without_using_transcript_for_dialog(tmp_path: Path, monkeypatch, capsys) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    transcript = "secret smoke transcript"

    with _FakeGatewayServer(
        {
            "ok": True,
            "openai_realtime_connection_ok": True,
            "chunks_sent": 6,
            "transcript_text_present": True,
            "transcript_text": transcript,
        }
    ) as gateway:
        monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
        monkeypatch.setenv("STT_GATEWAY_ADAPTER_ENABLED", "true")
        monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "false")
        monkeypatch.setenv("STT_GATEWAY_URL", gateway.url)
        monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
        monkeypatch.setenv("STT_GATEWAY_TIMEOUT_MS", "1000")
        monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        code = gateway_adapter_smoke_main(["--audio", str(audio_path), "--require-explicit-flags"])

    assert code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["adapter_smoke_exercised_node025_path"] is True
    assert payload["transcript_present"] is True
    assert payload["transcript_used_for_dialog"] is False
    assert payload["transcript_text_logged"] is False
    assert payload["fallback_reason"] == "gateway_stt_dialog_use_disabled"
    assert len(gateway.requests) == 1
    assert transcript not in serialized


def test_business_path_explicit_local_gateway_transcript_can_drive_boundary(
    monkeypatch,
    tmp_path: Path,
) -> None:
    audio_path = _write_audio(tmp_path / "turn_name.wav")
    session = CallSession(
        call_id="call-local-gateway",
        channel_id="ch-local-gateway",
        artifact_dir=tmp_path / "artifacts",
    )
    transcript = "explicit fake gateway transcript"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with _FakeGatewayServer({"ok": True, "transcript_text_present": True, "transcript_text": transcript}) as gateway:
        monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
        monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "true")
        monkeypatch.setenv("STT_GATEWAY_URL", gateway.url)
        monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
        monkeypatch.setenv("STT_GATEWAY_TIMEOUT_MS", "1000")
        monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
        monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
        monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "batch fallback text")

        text, details = asyncio.run(
            ari_app._transcribe_audio_artifact_experimental(
                _settings(tmp_path),
                session,
                _artifact(audio_path),
            )
        )

    serialized_events = json.dumps(_events(session), ensure_ascii=False)
    assert text == transcript
    assert details["stt_backend"] == "gateway_stt"
    assert details["stt_gateway_transcript_accepted"] is True
    assert "stt_gateway_fallback_to_batch" not in details
    assert transcript not in serialized_events
    assert len(gateway.requests) == 1


def test_business_transcription_path_keeps_gateway_disabled_by_default(monkeypatch, tmp_path: Path) -> None:
    audio_path = _write_audio(tmp_path / "turn_name.wav")
    session = CallSession(call_id="call-default", channel_id="ch-default", artifact_dir=tmp_path / "artifacts")

    async def _gateway_call(*_args, **_kwargs):
        raise AssertionError("default business path must not call gateway")

    monkeypatch.setattr(ari_app, "transcribe_via_gateway", _gateway_call)
    monkeypatch.setenv("TELEPHONY_STT_BACKEND", "fixture")
    monkeypatch.setenv("TELEPHONY_STT_FIXTURE_NAME", "batch text")
    monkeypatch.delenv("STT_GATEWAY_STT_ENABLED", raising=False)
    monkeypatch.delenv("STT_GATEWAY_ADAPTER_ENABLED", raising=False)

    text, details = asyncio.run(
        ari_app._transcribe_audio_artifact_experimental(
            _settings(tmp_path),
            session,
            _artifact(audio_path),
        )
    )

    assert text == "batch text"
    assert details["stt_streaming_enabled"] is False
    assert not any(event["action"].startswith("gateway_stt_") for event in _events(session))


def test_gateway_adapter_smoke_reports_redacted_metadata(tmp_path: Path, monkeypatch, capsys) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    transcript = "secret smoke transcript"

    with _FakeGatewayServer(
        {
            "ok": True,
            "openai_realtime_connection_ok": True,
            "chunks_sent": 6,
            "transcript_text_present": True,
            "transcript_text": transcript,
        }
    ) as gateway:
        monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
        monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "true")
        monkeypatch.setenv("STT_GATEWAY_URL", gateway.url)
        monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
        monkeypatch.setenv("STT_GATEWAY_TIMEOUT_MS", "1000")
        monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        code = gateway_adapter_smoke_main(["--audio", str(audio_path), "--require-explicit-flags"])

    assert code == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["adapter_enabled_temporarily"] is True
    assert payload["adapter_default_enabled_after_smoke"] is False
    assert payload["adapter_smoke_exercised_node025_path"] is True
    assert payload["gateway_reachable_from_asterisk"] is True
    assert payload["gateway_auth"] == "ok"
    assert payload["openai_realtime_from_gateway"] == "ok"
    assert payload["chunks_sent"] == 6
    assert payload["transcript_present"] is True
    assert payload["transcript_text_logged"] is False
    assert transcript not in serialized
    assert "fake-token" not in serialized


def test_gateway_adapter_smoke_requires_explicit_safe_flags(tmp_path: Path, monkeypatch, capsys) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")
    monkeypatch.delenv("STT_GATEWAY_STT_ENABLED", raising=False)
    monkeypatch.delenv("STT_GATEWAY_ADAPTER_ENABLED", raising=False)
    monkeypatch.delenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", raising=False)
    monkeypatch.delenv("STT_GATEWAY_URL", raising=False)
    monkeypatch.delenv("STT_GATEWAY_TOKEN", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    code = gateway_adapter_smoke_main(["--audio", str(audio_path), "--require-explicit-flags"])

    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "STT_GATEWAY_URL" in payload["missing_required_flags"]


def test_gateway_adapter_smoke_direct_run_can_record_empty_transcript_fallback(tmp_path: Path, monkeypatch) -> None:
    audio_path = _write_audio(tmp_path / "audio.wav")

    with _FakeGatewayServer(
        {
            "ok": True,
            "openai_realtime_connection_ok": True,
            "chunks_sent": 6,
            "transcript_text_present": False,
        }
    ) as gateway:
        monkeypatch.setenv("STT_GATEWAY_STT_ENABLED", "true")
        monkeypatch.setenv("STT_GATEWAY_USE_TRANSCRIPT_FOR_DIALOG", "true")
        monkeypatch.setenv("STT_GATEWAY_URL", gateway.url)
        monkeypatch.setenv("STT_GATEWAY_TOKEN", "fake-token")
        monkeypatch.setenv("STT_GATEWAY_TIMEOUT_MS", "1000")
        monkeypatch.setenv("STT_GATEWAY_LOG_TRANSCRIPT", "false")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        report = asyncio.run(run_smoke(audio_path))

    assert report["adapter_smoke_exercised_node025_path"] is True
    assert report["gateway_auth"] == "ok"
    assert report["openai_realtime_from_gateway"] == "ok"
    assert report["chunks_sent"] == 6
    assert report["transcript_present"] is False
    assert report["transcript_used_for_dialog"] is False
    assert report["fallback_reason"] == "empty_transcript"
