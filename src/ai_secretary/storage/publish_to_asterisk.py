"""Asterisk sounds publishing via SSH."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

import paramiko

from ..config.settings import Settings


def build_remote_sound_id(remote_rel_path: str) -> str:
    """Build ARI sound id from a relative wav path."""
    rel = PurePosixPath(remote_rel_path)
    without_ext = rel.with_suffix("")
    return f"sound:{without_ext.as_posix()}"


def publish_wav_to_asterisk(
    local_wav_path: Path,
    remote_rel_path: str,
    settings: Settings,
) -> str:
    """Publish a WAV file into Asterisk sounds directory over SSH."""
    remote_dir = PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / PurePosixPath(remote_rel_path).parent
    remote_path = remote_dir / PurePosixPath(remote_rel_path).name

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if settings.asterisk_ssh_key:
        key = paramiko.RSAKey.from_private_key_file(settings.asterisk_ssh_key)
        client.connect(
            settings.asterisk_ssh_host,
            username=settings.asterisk_ssh_user,
            pkey=key,
        )
    else:
        client.connect(
            settings.asterisk_ssh_host,
            username=settings.asterisk_ssh_user,
            password=settings.asterisk_ssh_password or None,
        )

    try:
        mkdir_cmd = f"mkdir -p '{remote_dir.as_posix()}'"
        client.exec_command(mkdir_cmd)

        sftp = client.open_sftp()
        try:
            sftp.put(local_wav_path.as_posix(), remote_path.as_posix())
        finally:
            sftp.close()
    finally:
        client.close()

    return build_remote_sound_id(remote_rel_path)
