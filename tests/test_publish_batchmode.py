"""Tests for SSH BatchMode publishing."""

from pathlib import Path
from types import SimpleNamespace

import ai_secretary.storage.publish_to_asterisk as pub
from ai_secretary.config.settings import Settings


def _settings(
    tmp_path: Path,
    docker_container: str = "",
    *,
    publish_mode: str = "ssh",
    local_sounds_root: Path | None = None,
) -> Settings:
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
        asterisk_publish_mode=publish_mode,
        asterisk_local_sounds_root=local_sounds_root or Path(""),
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

    def fake_run_cmd(cmd, _label, cmd_timeout_sec=None):
        calls.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(pub, "_run_cmd", fake_run_cmd)

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
    assert result["details"]["reason"] == "missing_key"
    assert result["details"]["failed_step"] == "config"


def test_local_publish_mode_does_not_require_ssh_key(monkeypatch, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")
    sounds_root = tmp_path / "asterisk_sounds"
    settings = _settings(tmp_path, publish_mode="local", local_sounds_root=sounds_root)
    object.__setattr__(settings, "asterisk_ssh_key", "")
    object.__setattr__(settings, "asterisk_ssh_host", "")
    object.__setattr__(settings, "asterisk_ssh_user", "")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", settings)

    assert result["ok"] is True
    assert result["sound_id"] == "sound:ai_secretary/call/reply"
    assert Path(result["remote_path"]) == sounds_root / "ai_secretary" / "call" / "reply.wav"
    assert (sounds_root / "ai_secretary" / "call" / "reply.wav").read_bytes() == b"RIFF"
    assert result["details"]["publish_mode"] == "local"


def test_local_publish_mode_creates_missing_directories(monkeypatch, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")
    sounds_root = tmp_path / "missing" / "sounds"
    settings = _settings(tmp_path, publish_mode="local", local_sounds_root=sounds_root)
    object.__setattr__(settings, "asterisk_ssh_key", "")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/_system/prompt_1.wav", settings)

    assert result["ok"] is True
    assert (sounds_root / "ai_secretary" / "_system" / "prompt_1.wav").is_file()
    assert result["sound_id"] == "sound:ai_secretary/_system/prompt_1"


def test_local_publish_mode_prepends_sounds_subdir_when_needed(monkeypatch, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")
    sounds_root = tmp_path / "sounds"
    settings = _settings(tmp_path, publish_mode="local", local_sounds_root=sounds_root)

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "call/reply.wav", settings)

    assert result["ok"] is True
    assert Path(result["remote_path"]) == sounds_root / "ai_secretary" / "call" / "reply.wav"
    assert result["sound_id"] == "sound:ai_secretary/call/reply"


def test_local_publish_mode_missing_root_fails_fast(monkeypatch, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")
    settings = _settings(tmp_path, publish_mode="local")
    object.__setattr__(settings, "asterisk_ssh_key", "")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", settings)

    assert result["ok"] is False
    assert "ASTERISK_LOCAL_SOUNDS_ROOT" in result["error"]
    assert result["details"]["reason"] == "missing_local_sounds_root"
    assert result["details"]["failed_step"] == "config"


def test_local_publish_mode_logs_selected_attempt_success(monkeypatch, capsys, tmp_path):
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")
    settings = _settings(tmp_path, publish_mode="local", local_sounds_root=tmp_path / "sounds")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", settings)

    assert result["ok"] is True
    output = capsys.readouterr().out
    assert "publish_mode_selected" in output
    assert "publish_local_attempt" in output
    assert "publish_local_success" in output


def test_publish_subprocess_timeout(monkeypatch, tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setenv("PUBLISH_CMD_TIMEOUT_SEC", "1")
    monkeypatch.setattr(
        pub,
        "ensure_remote_dir",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Command timed out after 1s: ssh ...")),
    )
    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", _settings(tmp_path))

    assert result["ok"] is False
    assert "timed out" in result["error"].lower()
    assert result["details"]["reason"] == "timeout"
    assert result["details"]["failed_step"] == "mkdir"


def test_publish_classifies_local_wav_missing(tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")

    result = pub.publish_wav_to_asterisk(tmp_path / "missing.wav", "ai_secretary/call/reply.wav", _settings(tmp_path))

    assert result["ok"] is False
    assert result["details"]["reason"] == "local_wav_missing"
    assert result["details"]["failed_step"] == "local_wav"


def test_publish_classifies_scp_failure(monkeypatch, tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)
    monkeypatch.setattr(pub, "ensure_remote_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        pub,
        "scp_upload",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("scp failed: lost connection")),
    )

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", _settings(tmp_path))

    assert result["ok"] is False
    assert result["details"]["reason"] == "scp_failed"
    assert result["details"]["failed_step"] == "scp_upload"


def test_publish_classifies_docker_partial_failure(monkeypatch, tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)
    monkeypatch.setattr(pub, "ensure_remote_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(pub, "scp_upload", lambda *args, **kwargs: None)
    monkeypatch.setattr(pub, "docker_exec_mkdir", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        pub,
        "docker_cp_to_container",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("docker cp failed")),
    )

    result = pub.publish_wav_to_asterisk(
        local_wav,
        "ai_secretary/call/reply.wav",
        _settings(tmp_path, docker_container="asterisk"),
    )

    assert result["ok"] is False
    assert result["details"]["reason"] == "docker_failed"
    assert result["details"]["failed_step"] == "docker_cp"


def test_publish_classifies_remote_stat_failure(monkeypatch, tmp_path):
    key_path = tmp_path / "id_rsa"
    key_path.write_text("dummy", encoding="utf-8")
    local_wav = tmp_path / "reply.wav"
    local_wav.write_bytes(b"RIFF")

    monkeypatch.setattr(pub, "_ensure_wav_8k_mono", lambda p: p)
    monkeypatch.setattr(pub, "ensure_remote_dir", lambda *args, **kwargs: None)
    monkeypatch.setattr(pub, "scp_upload", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        pub,
        "_remote_stat_host",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("test -f failed")),
    )

    result = pub.publish_wav_to_asterisk(local_wav, "ai_secretary/call/reply.wav", _settings(tmp_path))

    assert result["ok"] is False
    assert result["details"]["reason"] == "remote_stat_failed"
    assert result["details"]["failed_step"] == "host_stat"
