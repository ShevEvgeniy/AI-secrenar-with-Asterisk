"""Asterisk sounds publishing via SSH/SCP (single source of truth)."""

from __future__ import annotations

import os
import subprocess
import time
import wave
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from ..config.settings import Settings


def build_remote_sound_id(remote_rel_path: str) -> str:
    """Build stable ARI sound id from a relative wav path."""
    rel = PurePosixPath(remote_rel_path.replace("\\", "/")).as_posix().lstrip("/")
    without_ext = PurePosixPath(rel).with_suffix("")
    return f"sound:{without_ext.as_posix()}"


def _ssh_base_args(key_path: Path) -> list[str]:
    return [
        "-i",
        str(key_path),
        "-o",
        "BatchMode=yes",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "PreferredAuthentications=publickey",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
        "-o",
        "ChallengeResponseAuthentication=no",
        "-o",
        "NumberOfPasswordPrompts=0",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ServerAliveInterval=3",
        "-o",
        "ServerAliveCountMax=1",
    ]


def _log_cmd(prefix: str, cmd: Sequence[str]) -> None:
    print(prefix, " ".join(cmd))


def _handle_ssh_error(cmd: Sequence[str], rc: int, stderr: str, stdout: str) -> None:
    err = (stderr or "").strip()
    out = (stdout or "").strip()
    combined = f"{err}\n{out}".strip()

    print("PUBLISH_SSH_RC", rc)
    print("PUBLISH_SSH_STDERR", combined[:1000])

    lowered = combined.lower()
    if "permission denied" in lowered or "password" in lowered or "authenticationmethods" in lowered:
        raise RuntimeError(
            "SSH requires password/2FA. Set sshd_config Match User tulauser: "
            "AuthenticationMethods publickey (or disable publickey,password). "
            "BatchMode blocks password prompts."
        )
    if "no such file or directory" in lowered:
        raise RuntimeError("OpenSSH client not installed or key missing: " + combined)
    raise RuntimeError("ssh/scp failed: " + combined)


def _cmd_timeout_sec() -> int:
    raw = os.getenv("PUBLISH_CMD_TIMEOUT_SEC", "6").strip()
    try:
        value = int(raw)
    except ValueError:
        return 6
    return value if value > 0 else 6


def _run_cmd(cmd: Sequence[str], label: str, cmd_timeout_sec: int | None = None) -> subprocess.CompletedProcess[str]:
    _log_cmd(label, cmd)
    timeout_sec = cmd_timeout_sec if (cmd_timeout_sec is not None and cmd_timeout_sec > 0) else _cmd_timeout_sec()
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("OpenSSH client not installed or key missing: " + str(exc)) from exc
    except subprocess.TimeoutExpired as exc:
        rendered = " ".join(str(part) for part in cmd)
        raise RuntimeError(f"Command timed out after {timeout_sec}s: {rendered}") from exc
    if result.returncode != 0:
        _handle_ssh_error(cmd, result.returncode, result.stderr, result.stdout)
    return result


def _ensure_wav_8k_mono(local_wav_path: Path) -> Path:
    """Convert WAV to 8kHz mono pcm_s16le using ffmpeg if needed."""
    try:
        with wave.open(str(local_wav_path), "rb") as wav:
            if (
                wav.getnchannels() == 1
                and wav.getframerate() == 8000
                and wav.getsampwidth() == 2
                and wav.getcomptype() == "NONE"
            ):
                return local_wav_path
    except wave.Error:
        pass

    out_path = local_wav_path.with_name(local_wav_path.stem + "_8k.wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(local_wav_path),
        "-ac",
        "1",
        "-ar",
        "8000",
        "-acodec",
        "pcm_s16le",
        str(out_path),
    ]
    _log_cmd("PUBLISH_FFMPEG_CMD:", cmd)
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("ffmpeg not found in PATH. Install ffmpeg to convert audio.") from exc
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        raise RuntimeError("ffmpeg convert failed: " + err)
    return out_path


def ensure_remote_dir(
    host: str,
    user: str,
    key_path: Path,
    remote_dir: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    """Ensure remote directory exists via ssh mkdir -p."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"mkdir -p {remote_dir}",
    ]
    _run_cmd(cmd, "PUBLISH_SSH_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def scp_upload(
    host: str,
    user: str,
    key_path: Path,
    local_path: Path,
    remote_path: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    """Upload file via scp."""
    cmd = [
        "scp",
        *_ssh_base_args(key_path),
        str(local_path),
        f"{user}@{host}:{remote_path}",
    ]
    _run_cmd(cmd, "PUBLISH_SCP_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def docker_exec_mkdir(
    host: str,
    user: str,
    key_path: Path,
    container: str,
    remote_dir: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    """Ensure directory exists inside Asterisk container."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"docker exec {container} mkdir -p {remote_dir}",
    ]
    _run_cmd(cmd, "PUBLISH_DOCKER_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def docker_cp_to_container(
    host: str,
    user: str,
    key_path: Path,
    container: str,
    host_path: str,
    container_path: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    """Copy file from host to container using docker cp via ssh."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"docker cp {host_path} {container}:{container_path}",
    ]
    _run_cmd(cmd, "PUBLISH_DOCKER_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def _remote_stat_host(
    host: str,
    user: str,
    key_path: Path,
    remote_path: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"test -f {remote_path}",
    ]
    _run_cmd(cmd, "PUBLISH_STAT_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def _remote_stat_container(
    host: str,
    user: str,
    key_path: Path,
    container: str,
    remote_path: str,
    cmd_timeout_sec: int | None = None,
) -> None:
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"docker exec {container} test -f {remote_path}",
    ]
    _run_cmd(cmd, "PUBLISH_STAT_CMD:", cmd_timeout_sec=cmd_timeout_sec)


def publish_wav_to_asterisk(
    local_wav_path: Path,
    remote_rel_path: str,
    settings: Settings,
    *,
    cmd_timeout_sec: int | None = None,
) -> dict[str, Any]:
    """Publish WAV to Asterisk and return structured result."""
    remote_wav = ""
    timings_ms: dict[str, int | None] = {
        "mkdir_ms": None,
        "scp_ms": None,
        "docker_mkdir_ms": None,
        "docker_cp_ms": None,
        "stat_ms": None,
        "total_ms": None,
    }
    total_start = time.perf_counter()
    try:
        if not settings.asterisk_ssh_key:
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": "ASTERISK_SSH_KEY is required for publishing",
                "details": {"reason": "missing_key"},
            }

        key_path = Path(settings.asterisk_ssh_key)
        if not key_path.exists():
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": f"SSH key not found: {key_path.as_posix()}",
                "details": {"reason": "key_not_found"},
            }

        if not settings.asterisk_ssh_host or not settings.asterisk_ssh_user:
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": "ASTERISK_SSH_HOST and ASTERISK_SSH_USER are required",
                "details": {"reason": "missing_ssh_target"},
            }

        remote_rel = PurePosixPath(remote_rel_path.replace("\\", "/").lstrip("/"))
        remote_dir = PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / remote_rel.parent
        remote_wav = (PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / remote_rel).as_posix()

        converted_wav = _ensure_wav_8k_mono(local_wav_path)

        step_start = time.perf_counter()
        ensure_remote_dir(
            settings.asterisk_ssh_host,
            settings.asterisk_ssh_user,
            key_path,
            remote_dir.as_posix(),
            cmd_timeout_sec=cmd_timeout_sec,
        )
        timings_ms["mkdir_ms"] = int((time.perf_counter() - step_start) * 1000)

        step_start = time.perf_counter()
        scp_upload(
            settings.asterisk_ssh_host,
            settings.asterisk_ssh_user,
            key_path,
            converted_wav,
            remote_wav,
            cmd_timeout_sec=cmd_timeout_sec,
        )
        timings_ms["scp_ms"] = int((time.perf_counter() - step_start) * 1000)

        docker_container = (settings.asterisk_docker_container or "").strip().strip('"').strip("'")
        if docker_container:
            step_start = time.perf_counter()
            docker_exec_mkdir(
                settings.asterisk_ssh_host,
                settings.asterisk_ssh_user,
                key_path,
                docker_container,
                remote_dir.as_posix(),
                cmd_timeout_sec=cmd_timeout_sec,
            )
            timings_ms["docker_mkdir_ms"] = int((time.perf_counter() - step_start) * 1000)
            step_start = time.perf_counter()
            docker_cp_to_container(
                settings.asterisk_ssh_host,
                settings.asterisk_ssh_user,
                key_path,
                docker_container,
                remote_wav,
                remote_wav,
                cmd_timeout_sec=cmd_timeout_sec,
            )
            timings_ms["docker_cp_ms"] = int((time.perf_counter() - step_start) * 1000)
            step_start = time.perf_counter()
            _remote_stat_container(
                settings.asterisk_ssh_host,
                settings.asterisk_ssh_user,
                key_path,
                docker_container,
                remote_wav,
                cmd_timeout_sec=cmd_timeout_sec,
            )
            timings_ms["stat_ms"] = int((time.perf_counter() - step_start) * 1000)
        else:
            step_start = time.perf_counter()
            _remote_stat_host(
                settings.asterisk_ssh_host,
                settings.asterisk_ssh_user,
                key_path,
                remote_wav,
                cmd_timeout_sec=cmd_timeout_sec,
            )
            timings_ms["stat_ms"] = int((time.perf_counter() - step_start) * 1000)

        sound_id = build_remote_sound_id(remote_rel.as_posix())
        timings_ms["total_ms"] = int((time.perf_counter() - total_start) * 1000)
        return {
            "ok": True,
            "sound_id": sound_id,
            "remote_path": remote_wav,
            "error": None,
            "details": {
                "docker_container": docker_container or None,
                "remote_rel_path": remote_rel.as_posix(),
                "cmd_timeout_sec": cmd_timeout_sec if (cmd_timeout_sec is not None and cmd_timeout_sec > 0) else _cmd_timeout_sec(),
                **timings_ms,
            },
        }
    except Exception as exc:
        timings_ms["total_ms"] = int((time.perf_counter() - total_start) * 1000)
        error_message = str(exc)
        return {
            "ok": False,
            "sound_id": "",
            "remote_path": remote_wav,
            "error": error_message,
            "details": {
                "exception": type(exc).__name__,
                "stderr_snippet": error_message[:400],
                "cmd_timeout_sec": cmd_timeout_sec if (cmd_timeout_sec is not None and cmd_timeout_sec > 0) else _cmd_timeout_sec(),
                **timings_ms,
            },
        }
