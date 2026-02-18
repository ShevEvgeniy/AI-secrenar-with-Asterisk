"""Tests for SSH BatchMode publishing."""

from types import SimpleNamespace

import ai_secretary.telephony.publish_to_asterisk as pub


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
