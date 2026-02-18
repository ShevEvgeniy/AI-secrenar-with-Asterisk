"""Tests for SSH BatchMode publishing."""

from pathlib import Path
from types import SimpleNamespace

import ai_secretary.storage.publish_to_asterisk as pub
from ai_secretary.config.settings import Settings


def _settings(tmp_path: Path, docker_container: str = "") -> Settings:
    return Settings(
        openai_api_key="",
        elevenlabs_api_key="",
        ari_url="http://localhost:8088/ari",
        ari_user="",
        ari_password="",
        sqlite_path=tmp_path / "db.sqlite",
        storage_dir=tmp_path,
        demo_mode="real",
        demo_audio_path=tmp_path / "in.wav",
        expected_real_phone="79000000000",
        kb_path=tmp_path / "kb.md",
        rag_top_k=3,
        asterisk_sounds_dir=Path("/var/lib/asterisk/sounds"),
        asterisk_sounds_subdir="ai_secretary",
        asterisk_ssh_host="host",
        asterisk_ssh_user="user",
        asterisk_ssh_key=str(tmp_path / "id_rsa"),
        asterisk_ssh_password="",
        asterisk_docker_container=docker_container,
    )


def test_scp_permission_denied(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=255, stdout="", stderr="Permission denied (password).")

    monkeypatch.setattr(pub.subprocess, "run", fake_run)

    try:
        pub._handle_ssh_error(["scp"], 255, "Permission denied (password).", "")
    except RuntimeError as exc:
        assert "AuthenticationMethods publickey" in str(exc)
    else:
        assert False, "Expected RuntimeError"


def test_scp_ok(monkeypatch, tmp_path):
    calls = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(pub.subprocess, "run", fake_run)

    pub.ensure_remote_dir("host", "user", tmp_path / "k", "/var/lib/asterisk/sounds/x")
    pub.scp_upload("host", "user", tmp_path / "k", tmp_path / "a.wav", "/var/lib/asterisk/sounds/x/a.wav")

    assert len(calls) == 2


def test_publish_returns_structured_ok(monkeypatch, tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)
    monkeypatch.setattr(pub, "ensure_remote_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(pub, "scp_upload", lambda *args, **kwargs: None)
    monkeypatch.setattr(pub, "_remote_stat_host", lambda *args, **kwargs: None)

    result = pub.publish_wav_to_asterisk(
        local_wav,
        "ai_secretary/call123/reply.wav",
        _settings(tmp_path),
    )

    assert result["ok"] is True
    assert result["sound_id"] == "sound:ai_secretary/call123/reply"
    assert result["remote_path"].endswith("/ai_secretary/call123/reply.wav")
    assert result["error"] is None


def test_publish_returns_structured_error(monkeypatch, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    settings = _settings(tmp_path)
    object.__setattr__(settings, "asterisk_ssh_key", "")

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", settings)

    assert result["ok"] is False
    assert result["sound_id"] == ""
    assert result["error"]
