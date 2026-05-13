"""Asterisk sounds publishing via SSH/SCP (single source of truth)."""

from __future__ import annotations

import os
import json
import shutil
import subprocess
import time
import wave
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Sequence

from ..config.settings import Settings


class PublishStepError(RuntimeError):
    """Publish failure annotated with the step and reason for diagnostics."""

    def __init__(self, step: str, reason: str, message: str) -> None:
        super().__init__(message)
        self.step = step
        self.reason = reason


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


def _log_publish_event(action: str, details: dict[str, Any]) -> None:
    print(action, json.dumps(details, ensure_ascii=False))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _log_cmd_lifecycle(
    stage: str,
    cmd: Sequence[str],
    *,
    pid: int | None = None,
    timeout_sec: int | None = None,
    returncode: int | None = None,
    timed_out: bool | None = None,
    dur_ms: int | None = None,
    stderr: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "ts": _utc_now_iso(),
        "stage": stage.rstrip(":"),
        "argv": [str(part) for part in cmd],
        "pid": pid,
        "timeout_sec": timeout_sec,
        "returncode": returncode,
        "timed_out": timed_out,
        "dur_ms": dur_ms,
    }
    if stderr:
        payload["stderr_snippet"] = stderr[:240]
    print("PUBLISH_CMD_TRACE", payload)


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


def _classify_error(message: str, *, step: str | None = None) -> str:
    lowered = (message or "").lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    if "authenticationmethods" in lowered or "permission denied" in lowered or "password" in lowered:
        return "ssh_auth_failed"
    if "openssh client not installed" in lowered:
        return "ssh_client_missing"
    if "key missing" in lowered or "ssh key not found" in lowered:
        return "key_not_found"
    if "ffmpeg not found" in lowered:
        return "ffmpeg_missing"
    if "ffmpeg convert failed" in lowered:
        return "ffmpeg_failed"
    if "local wav not found" in lowered:
        return "local_wav_missing"
    if "local wav is empty" in lowered:
        return "local_wav_empty"
    if step == "scp_upload":
        return "scp_failed"
    if step in {"docker_mkdir", "docker_cp"}:
        return "docker_failed"
    if step in {"host_stat", "container_stat"}:
        return "remote_stat_failed"
    if step == "mkdir":
        return "ssh_mkdir_failed"
    return "publish_failed"


def _run_publish_step(step: str, func: Any, *args: Any, **kwargs: Any) -> Any:
    try:
        return func(*args, **kwargs)
    except PublishStepError:
        raise
    except Exception as exc:
        message = str(exc)
        raise PublishStepError(step, _classify_error(message, step=step), message) from exc


def _cmd_timeout_sec() -> int:
    raw = os.getenv("PUBLISH_CMD_TIMEOUT_SEC", "6").strip()
    try:
        value = int(raw)
    except ValueError:
        return 6
    return value if value > 0 else 6


def _publish_mode(settings: Settings) -> str:
    value = getattr(settings, "asterisk_publish_mode", "") or os.getenv("ASTERISK_PUBLISH_MODE", "ssh")
    mode = str(value).strip().lower()
    return mode or "ssh"


def _local_sounds_root(settings: Settings) -> Path:
    value = getattr(settings, "asterisk_local_sounds_root", None)
    if value is None or str(value) == ".":
        value = os.getenv("ASTERISK_LOCAL_SOUNDS_ROOT", "")
    return Path(str(value or ""))


def _run_cmd(cmd: Sequence[str], label: str, cmd_timeout_sec: int | None = None) -> subprocess.CompletedProcess[str]:
    _log_cmd(label, cmd)
    timeout_sec = cmd_timeout_sec if (cmd_timeout_sec is not None and cmd_timeout_sec > 0) else _cmd_timeout_sec()
    started = time.perf_counter()
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        _log_cmd_lifecycle(label, cmd, pid=proc.pid, timeout_sec=timeout_sec, timed_out=False)
        stdout, stderr = proc.communicate(timeout=timeout_sec)
        result = subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)
    except FileNotFoundError as exc:
        raise RuntimeError("OpenSSH client not installed or key missing: " + str(exc)) from exc
    except subprocess.TimeoutExpired:
        if proc is not None:
            proc.kill()
            out_tail, err_tail = proc.communicate()
        else:
            out_tail, err_tail = "", ""
        _log_cmd_lifecycle(
            label,
            cmd,
            pid=(proc.pid if proc is not None else None),
            timeout_sec=timeout_sec,
            timed_out=True,
            dur_ms=int((time.perf_counter() - started) * 1000),
            stderr=err_tail,
        )
        rendered = " ".join(str(part) for part in cmd)
        err = (err_tail or out_tail or "").strip()
        if err:
            raise RuntimeError(f"Command timed out after {timeout_sec}s: {rendered}. stderr={err[:240]}")
        raise RuntimeError(f"Command timed out after {timeout_sec}s: {rendered}")
    _log_cmd_lifecycle(
        label,
        cmd,
        pid=(proc.pid if proc is not None else None),
        timeout_sec=timeout_sec,
        returncode=result.returncode,
        timed_out=False,
        dur_ms=int((time.perf_counter() - started) * 1000),
        stderr=result.stderr,
    )
    if result.returncode != 0:
        _handle_ssh_error(cmd, result.returncode, result.stderr, result.stdout)
    return result


def _publish_wav_local(
    *,
    converted_wav: Path,
    remote_rel: PurePosixPath,
    settings: Settings,
    timings_ms: dict[str, int | None],
    total_start: float,
) -> dict[str, Any]:
    local_root = _local_sounds_root(settings)
    if str(local_root) in {"", "."}:
        raise PublishStepError(
            "config",
            "missing_local_sounds_root",
            "ASTERISK_LOCAL_SOUNDS_ROOT is required when ASTERISK_PUBLISH_MODE=local",
        )
    subdir = settings.asterisk_sounds_subdir.strip().strip("/")
    if subdir and (not remote_rel.parts or remote_rel.parts[0] != subdir):
        remote_rel = PurePosixPath(subdir) / remote_rel

    destination = local_root / Path(remote_rel.as_posix())
    _log_publish_event(
        "publish_local_attempt",
        {
            "mode": "local",
            "local_sounds_root": local_root.as_posix(),
            "remote_rel_path": remote_rel.as_posix(),
            "destination_path": destination.as_posix(),
        },
    )
    step_start = time.perf_counter()
    destination.parent.mkdir(parents=True, exist_ok=True)
    timings_ms["mkdir_ms"] = int((time.perf_counter() - step_start) * 1000)

    step_start = time.perf_counter()
    shutil.copyfile(converted_wav, destination)
    timings_ms["scp_ms"] = int((time.perf_counter() - step_start) * 1000)

    step_start = time.perf_counter()
    if not destination.is_file():
        raise PublishStepError("host_stat", "remote_stat_failed", f"Local published WAV not found: {destination.as_posix()}")
    timings_ms["stat_ms"] = int((time.perf_counter() - step_start) * 1000)

    sound_id = build_remote_sound_id(remote_rel.as_posix())
    timings_ms["total_ms"] = int((time.perf_counter() - total_start) * 1000)
    _log_publish_event(
        "publish_local_success",
        {
            "mode": "local",
            "sound_id": sound_id,
            "remote_path": destination.as_posix(),
            "remote_rel_path": remote_rel.as_posix(),
        },
    )
    return {
        "ok": True,
        "sound_id": sound_id,
        "remote_path": destination.as_posix(),
        "error": None,
        "details": {
            "publish_mode": "local",
            "local_sounds_root": local_root.as_posix(),
            "remote_rel_path": remote_rel.as_posix(),
            "cmd_timeout_sec": None,
            **timings_ms,
        },
    }


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
    publish_mode = "ssh"
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
        if not local_wav_path.exists():
            raise PublishStepError("local_wav", "local_wav_missing", f"Local WAV not found: {local_wav_path.as_posix()}")
        if local_wav_path.stat().st_size <= 0:
            raise PublishStepError("local_wav", "local_wav_empty", f"Local WAV is empty: {local_wav_path.as_posix()}")

        publish_mode = _publish_mode(settings)
        remote_rel = PurePosixPath(remote_rel_path.replace("\\", "/").lstrip("/"))
        _log_publish_event(
            "publish_mode_selected",
            {
                "mode": publish_mode,
                "remote_rel_path": remote_rel.as_posix(),
                "sounds_subdir": settings.asterisk_sounds_subdir,
            },
        )
        if publish_mode not in {"ssh", "remote", "local"}:
            raise PublishStepError("config", "unsupported_publish_mode", f"Unsupported ASTERISK_PUBLISH_MODE: {publish_mode}")

        if publish_mode == "local":
            converted_wav = _run_publish_step("convert", _ensure_wav_8k_mono, local_wav_path)
            return _publish_wav_local(
                converted_wav=converted_wav,
                remote_rel=remote_rel,
                settings=settings,
                timings_ms=timings_ms,
                total_start=total_start,
            )

        if not settings.asterisk_ssh_key:
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": "ASTERISK_SSH_KEY is required for publishing",
                "details": {"reason": "missing_key", "failed_step": "config"},
            }

        key_path = Path(settings.asterisk_ssh_key)
        try:
            key_exists = key_path.exists()
        except PermissionError as exc:
            # On Windows, ACLs may block Python stat() for key path; let ssh/scp validate access.
            key_exists = True
            print("PUBLISH_KEY_PATH_STAT_WARN", key_path.as_posix(), type(exc).__name__)
        if not key_exists:
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": f"SSH key not found: {key_path.as_posix()}",
                "details": {"reason": "key_not_found", "failed_step": "config"},
            }

        if not settings.asterisk_ssh_host or not settings.asterisk_ssh_user:
            return {
                "ok": False,
                "sound_id": "",
                "remote_path": "",
                "error": "ASTERISK_SSH_HOST and ASTERISK_SSH_USER are required",
                "details": {"reason": "missing_ssh_target", "failed_step": "config"},
            }

        remote_dir = PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / remote_rel.parent
        remote_wav = (PurePosixPath(settings.asterisk_sounds_dir.as_posix()) / remote_rel).as_posix()

        converted_wav = _run_publish_step("convert", _ensure_wav_8k_mono, local_wav_path)

        step_start = time.perf_counter()
        _run_publish_step(
            "mkdir",
            ensure_remote_dir,
            settings.asterisk_ssh_host,
            settings.asterisk_ssh_user,
            key_path,
            remote_dir.as_posix(),
            cmd_timeout_sec=cmd_timeout_sec,
        )
        timings_ms["mkdir_ms"] = int((time.perf_counter() - step_start) * 1000)

        step_start = time.perf_counter()
        _run_publish_step(
            "scp_upload",
            scp_upload,
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
            _run_publish_step(
                "docker_mkdir",
                docker_exec_mkdir,
                settings.asterisk_ssh_host,
                settings.asterisk_ssh_user,
                key_path,
                docker_container,
                remote_dir.as_posix(),
                cmd_timeout_sec=cmd_timeout_sec,
            )
            timings_ms["docker_mkdir_ms"] = int((time.perf_counter() - step_start) * 1000)
            step_start = time.perf_counter()
            _run_publish_step(
                "docker_cp",
                docker_cp_to_container,
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
            _run_publish_step(
                "container_stat",
                _remote_stat_container,
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
            _run_publish_step(
                "host_stat",
                _remote_stat_host,
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
        failed_step = exc.step if isinstance(exc, PublishStepError) else "unknown"
        reason = exc.reason if isinstance(exc, PublishStepError) else _classify_error(error_message)
        if publish_mode == "local":
            _log_publish_event(
                "publish_local_failed",
                {
                    "mode": "local",
                    "reason": reason,
                    "failed_step": failed_step,
                    "error": error_message,
                },
            )
        return {
            "ok": False,
            "sound_id": "",
            "remote_path": remote_wav,
            "error": error_message,
            "details": {
                "reason": reason,
                "failed_step": failed_step,
                "exception": type(exc).__name__,
                "stderr_snippet": error_message[:400],
                "cmd_timeout_sec": cmd_timeout_sec if (cmd_timeout_sec is not None and cmd_timeout_sec > 0) else _cmd_timeout_sec(),
                **timings_ms,
            },
        }
