"""Asterisk sounds publishing via SSH/SCP."""

from __future__ import annotations

import subprocess
from pathlib import Path, PurePosixPath
from typing import Sequence

from ..config.settings import Settings


def build_remote_sound_id(remote_rel_path: str) -> str:
    """Build ARI sound id from a relative wav path."""
    rel = PurePosixPath(remote_rel_path)
    without_ext = rel.with_suffix("")
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
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=10",
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


def _run_cmd(cmd: Sequence[str], label: str) -> None:
    _log_cmd(label, cmd)
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise RuntimeError("OpenSSH client not installed or key missing: " + str(exc)) from exc
    if result.returncode != 0:
        _handle_ssh_error(cmd, result.returncode, result.stderr, result.stdout)


def _ensure_wav_8k_mono(local_wav_path: Path) -> Path:
    """Convert WAV to 8kHz mono pcm_s16le using ffmpeg."""
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


def ensure_remote_dir(host: str, user: str, key_path: Path, remote_dir: str) -> None:
    """Ensure remote directory exists via ssh mkdir -p."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"mkdir -p {remote_dir}",
    ]
    _run_cmd(cmd, "PUBLISH_SSH_CMD:")


def scp_upload(host: str, user: str, key_path: Path, local_path: Path, remote_path: str) -> None:
    """Upload file via scp."""
    cmd = [
        "scp",
        *_ssh_base_args(key_path),
        str(local_path),
        f"{user}@{host}:{remote_path}",
    ]
    _run_cmd(cmd, "PUBLISH_SCP_CMD:")


def docker_exec_mkdir(host: str, user: str, key_path: Path, container: str, remote_dir: str) -> None:
    """Ensure directory exists inside Asterisk container."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"docker exec {container} mkdir -p {remote_dir}",
    ]
    _run_cmd(cmd, "PUBLISH_DOCKER_CMD:")


def docker_cp_to_container(
    host: str,
    user: str,
    key_path: Path,
    container: str,
    host_path: str,
    container_path: str,
) -> None:
    """Copy file from host to container using docker cp via ssh."""
    cmd = [
        "ssh",
        *_ssh_base_args(key_path),
        f"{user}@{host}",
        f"docker cp {host_path} {container}:{container_path}",
    ]
    _run_cmd(cmd, "PUBLISH_DOCKER_CMD:")


def publish_wav_to_asterisk(
    local_wav_path: Path,
    remote_rel_path: str,
    settings: Settings,
) -> str:
    """Publish a WAV file into Asterisk sounds directory over SSH/SCP."""
    if not settings.asterisk_ssh_key:
        raise RuntimeError("ASTERISK_SSH_KEY is required for scp publishing")
    key_path = Path(settings.asterisk_ssh_key)
    if not key_path.exists():
        raise RuntimeError(f"SSH key not found: {key_path.as_posix()}")
    if not settings.asterisk_ssh_host or not settings.asterisk_ssh_user:
        raise RuntimeError("ASTERISK_SSH_HOST and ASTERISK_SSH_USER are required")

    remote_dir = PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / PurePosixPath(remote_rel_path).parent
    remote_wav = PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / PurePosixPath(remote_rel_path)

    converted_wav = _ensure_wav_8k_mono(local_wav_path)

    ensure_remote_dir(
        settings.asterisk_ssh_host,
        settings.asterisk_ssh_user,
        key_path,
        remote_dir.as_posix(),
    )
    scp_upload(
        settings.asterisk_ssh_host,
        settings.asterisk_ssh_user,
        key_path,
        converted_wav,
        remote_wav.as_posix(),
    )

    if settings.asterisk_docker_container:
        docker_exec_mkdir(
            settings.asterisk_ssh_host,
            settings.asterisk_ssh_user,
            key_path,
            settings.asterisk_docker_container,
            remote_dir.as_posix(),
        )
        docker_cp_to_container(
            settings.asterisk_ssh_host,
            settings.asterisk_ssh_user,
            key_path,
            settings.asterisk_docker_container,
            remote_wav.as_posix(),
            remote_wav.as_posix(),
        )
        print("PUBLISH_DOCKER_OK", settings.asterisk_docker_container, remote_wav.as_posix())

    print("PUBLISH_SCP_OK", remote_wav.as_posix())
    return build_remote_sound_id(remote_rel_path)