"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config.settings import Settings
from ..core.runner import run_pipeline, run_pipeline_from_transcript
from ..rag.embeddings import warmup_embeddings
from ..stt.whisper_api import WhisperAPIClient
from ..storage.files import save_bytes, save_json
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .call_session import CallSession, CallState, DialogStage
from .dialog import PROMPTS, apply_turn, build_turn_record, next_prompt, should_stop_dialog
from .publish_to_asterisk import publish_wav_to_asterisk

PROMPT_1_SOUND_ID = "sound:ai_secretary/_system/prompt_1"
PROMPT_2_SOUND_ID = "sound:ai_secretary/_system/prompt_2"
PROMPT_3_SOUND_ID = "sound:ai_secretary/_system/prompt_3"
PROMPT_4_SOUND_ID = "sound:ai_secretary/_system/prompt_4"
FALLBACK_SOUND_ID = "sound:ai_secretary/_system/fallback"
TRANSFER_SOUND_ID = "sound:ai_secretary/_system/transfer"
PROMPT_FALLBACK_SOUND_IDS: dict[DialogStage, str] = {
    DialogStage.ISSUE: "sound:ai_secretary/_system/fallback_prompt_1",
    DialogStage.NAME: "sound:ai_secretary/_system/fallback_prompt_2",
    DialogStage.CITY: "sound:ai_secretary/_system/fallback_prompt_3",
    DialogStage.PHONE: "sound:ai_secretary/_system/fallback_prompt_4",
}
TRANSFER_FALLBACK_SOUND_ID = "sound:ai_secretary/_system/fallback_transfer"
DEFAULT_TRANSFER_CONTEXT = "from-internal"
DEFAULT_TRANSFER_EXTEN = "sales_real"
DEFAULT_TRANSFER_PRIORITY = 1
DEFAULT_RECORD_WAIT_PAD_SECONDS = 3
BUILTIN_GENERAL_FALLBACK_MEDIA = ("sound:please-try-again", "sound:pls-try-call-later")
BUILTIN_PROMPT_FALLBACK_MEDIA: dict[DialogStage, str] = {
    DialogStage.ISSUE: "sound:please-try-again",
    DialogStage.NAME: "sound:please-try-again",
    DialogStage.CITY: "sound:please-try-again",
    DialogStage.PHONE: "sound:please-try-again",
}
BUILTIN_TRANSFER_FALLBACK_MEDIA = ("sound:pls-wait-connect-call", "sound:please-hold-while-try")

_SYSTEM_SOUND_TEXTS: dict[str, str] = {
    PROMPT_1_SOUND_ID: PROMPTS[DialogStage.ISSUE],
    PROMPT_2_SOUND_ID: PROMPTS[DialogStage.NAME],
    PROMPT_3_SOUND_ID: PROMPTS[DialogStage.CITY],
    PROMPT_4_SOUND_ID: PROMPTS[DialogStage.PHONE],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.ISSUE]: PROMPTS[DialogStage.ISSUE],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.NAME]: PROMPTS[DialogStage.NAME],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.CITY]: PROMPTS[DialogStage.CITY],
    PROMPT_FALLBACK_SOUND_IDS[DialogStage.PHONE]: PROMPTS[DialogStage.PHONE],
    FALLBACK_SOUND_ID: "Одну секунду, пожалуйста.",
    TRANSFER_SOUND_ID: PROMPTS[DialogStage.DONE],
    TRANSFER_FALLBACK_SOUND_ID: PROMPTS[DialogStage.DONE],
}
_system_sound_status: dict[str, bool] = {sound_id: False for sound_id in _SYSTEM_SOUND_TEXTS}
_system_sounds_done = False
_system_sounds_lock: asyncio.Lock | None = None
_system_sounds_task: asyncio.Task[dict[str, bool]] | None = None


@dataclass(frozen=True)
class TranscriptionArtifact:
    """The exact audio artifact passed to transcription."""

    call_id: str
    channel_id: str
    stage: DialogStage
    turn_idx: int
    record_name: str
    path: Path
    size_bytes: int
    sha256: str

    def details(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "channel_id": self.channel_id,
            "stage": self.stage.value,
            "turn_idx": self.turn_idx,
            "record_name": self.record_name,
            "audio_path": str(self.path.as_posix()),
            "audio_size_bytes": self.size_bytes,
            "audio_sha256": self.sha256,
        }


@dataclass(frozen=True)
class RecordProfile:
    """Per-stage recording contour for the turn-based dialog."""

    max_duration_seconds: int
    max_silence_seconds: int
    wait_timeout_seconds: int

    def details(self) -> dict[str, int]:
        return {
            "max_duration_seconds": self.max_duration_seconds,
            "max_silence_seconds": self.max_silence_seconds,
            "wait_timeout_seconds": self.wait_timeout_seconds,
        }


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _env_int_optional(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    try:
        value = int(raw.strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def _stage_env_int(stage: DialogStage, suffix: str, default: int) -> int:
    stage_name = stage.value.upper()
    for name in (
        f"RECORD_{stage_name}_{suffix}",
        f"RECORD_SLOT_{suffix}",
        f"RECORD_{suffix}",
    ):
        value = _env_int_optional(name)
        if value is not None:
            return value
    return default


def _record_profile_for_stage(stage: DialogStage) -> RecordProfile:
    """Return stage-specific turn-recording limits without changing architecture."""
    defaults = {
        DialogStage.ISSUE: (8, 2),
        DialogStage.NAME: (4, 1),
        DialogStage.CITY: (4, 1),
        DialogStage.PHONE: (5, 1),
        DialogStage.PHONE_CONFIRM: (3, 1),
    }
    default_duration, default_silence = defaults.get(stage, (4, 1))
    max_duration = _stage_env_int(stage, "MAX_DURATION_SECONDS", default_duration)
    max_silence = _stage_env_int(stage, "MAX_SILENCE_SECONDS", default_silence)
    wait_pad = _stage_env_int(stage, "WAIT_PAD_SECONDS", DEFAULT_RECORD_WAIT_PAD_SECONDS)
    wait_timeout = _stage_env_int(stage, "WAIT_TIMEOUT_SECONDS", max(3, max_duration + max_silence + wait_pad))
    return RecordProfile(
        max_duration_seconds=max_duration,
        max_silence_seconds=max_silence,
        wait_timeout_seconds=wait_timeout,
    )


def _publish_total_timeout_sec() -> int:
    value = _env_int("PUBLISH_TOTAL_TIMEOUT_SEC", 35)
    return value if value > 0 else 35


def _system_sounds_publish_timeout_sec() -> int:
    value = _env_int("SYSTEM_SOUNDS_PUBLISH_TIMEOUT_SEC", 45)
    return value if value > 0 else 45


def _system_lock_get() -> asyncio.Lock:
    global _system_sounds_lock
    if _system_sounds_lock is None:
        _system_sounds_lock = asyncio.Lock()
    return _system_sounds_lock


def _system_rel_path(sound_id: str) -> str:
    return sound_id.replace("sound:", "") + ".wav"


def _append_system_diag(payload: dict[str, Any]) -> None:
    path = Path("tmp/diag/system_sounds_publish.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _append_system_event(payload: dict[str, Any]) -> None:
    path = Path("tmp/diag/events.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _publish_fail_reason(message: str, details: dict[str, Any] | None = None) -> str:
    reason = (details or {}).get("reason")
    if isinstance(reason, str) and reason:
        return reason
    lowered = (message or "").lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    return "publish_failed"


def _publish_result_reason(result: dict[str, Any]) -> str:
    return _publish_fail_reason(str(result.get("error") or ""), result.get("details") or {})


async def _play_publish_failure_fallback(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
    *,
    reason: str,
    publish_details: dict[str, Any],
) -> tuple[bool, bool]:
    played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
    session.log_event(
        action="publish_fallback",
        status="ok" if played else "fail",
        reason=None if played else "fallback_play_failed",
        details={
            "publish_reason": reason,
            "publish_details": publish_details,
        },
    )
    return played, moh_started


async def ensure_system_sounds(settings: Settings) -> dict[str, bool]:
    """Generate and publish static system sounds once per process."""
    global _system_sounds_done
    if _system_sounds_done:
        return dict(_system_sound_status)

    lock = _system_lock_get()
    async with lock:
        if _system_sounds_done:
            return dict(_system_sound_status)

        print("SYSTEM_SOUNDS_START")
        started = time.perf_counter()
        details: dict[str, dict[str, Any]] = {}
        local_dir = settings.storage_dir / "_system"
        local_dir.mkdir(parents=True, exist_ok=True)
        tts: SileroTTS | None = None
        timeout_sec = _system_sounds_publish_timeout_sec()

        cmd_timeout_sec = max(1, timeout_sec - 5)
        for sound_id, text in _SYSTEM_SOUND_TEXTS.items():
            item_start = time.perf_counter()
            file_name = sound_id.split("/")[-1] + ".wav"
            local_path = local_dir / file_name
            try:
                if not local_path.exists():
                    if tts is None:
                        tts = SileroTTS()
                    wav = await asyncio.to_thread(tts.synthesize, text)
                    save_bytes(local_path, wav)
                remote_rel = _system_rel_path(sound_id)
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        publish_wav_to_asterisk,
                        local_path,
                        remote_rel,
                        settings,
                        cmd_timeout_sec=cmd_timeout_sec,
                    ),
                    timeout=timeout_sec,
                )
                ok = bool(result.get("ok"))
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = ok
                reason = None if ok else _publish_result_reason(result)
                details[sound_id] = {
                    "ok": ok,
                    "dur_ms": dur_ms,
                    "error": result.get("error"),
                    "publish_result": result,
                }
                event_payload = {
                    "ts": _now_iso(),
                    "action": "system_sound_publish",
                    "status": "ok" if ok else "fail",
                    "sound_id": sound_id,
                    "remote_path": str(result.get("remote_path") or ""),
                    "dur_ms": dur_ms,
                    "reason": reason,
                    "details": result.get("details") or {},
                }
                if not ok:
                    event_payload["details"] = {
                        **event_payload["details"],
                        "error": result.get("error"),
                        "stderr_snippet": str(result.get("error") or "")[:400],
                    }
                _append_system_event(event_payload)
                print("SYSTEM_SOUNDS_ITEM", sound_id, "ok" if ok else "fail", json.dumps(result, ensure_ascii=False))
            except asyncio.TimeoutError:
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = False
                details[sound_id] = {
                    "ok": False,
                    "dur_ms": dur_ms,
                    "error": "publish_timeout",
                }
                print("SYSTEM_SOUNDS_ITEM_TIMEOUT", sound_id)
                _append_system_event(
                    {
                        "ts": _now_iso(),
                        "action": "system_sound_publish",
                        "status": "fail",
                        "sound_id": sound_id,
                        "remote_path": _system_rel_path(sound_id),
                        "dur_ms": dur_ms,
                        "reason": "timeout",
                        "details": {"stderr_snippet": "outer_timeout", "timeout_sec": timeout_sec},
                    }
                )
            except Exception as exc:
                dur_ms = int((time.perf_counter() - item_start) * 1000)
                _system_sound_status[sound_id] = False
                details[sound_id] = {
                    "ok": False,
                    "dur_ms": dur_ms,
                    "error": repr(exc),
                }
                print("SYSTEM_SOUNDS_ITEM_FAIL", sound_id, repr(exc))
                _append_system_event(
                    {
                        "ts": _now_iso(),
                        "action": "system_sound_publish",
                        "status": "fail",
                        "sound_id": sound_id,
                        "remote_path": _system_rel_path(sound_id),
                        "dur_ms": dur_ms,
                        "reason": _publish_fail_reason(str(exc)),
                        "details": {"stderr_snippet": str(exc)[:400]},
                    }
                )

        total_ms = int((time.perf_counter() - started) * 1000)
        _system_sounds_done = True
        payload = {
            "action": "system_sounds_publish_total",
            "status": "ok" if all(_system_sound_status.values()) else "fail",
            "dur_ms": total_ms,
            "details": {"sounds": dict(_system_sound_status), "items": details},
        }
        _append_system_diag(payload)
        _append_system_event({"ts": _now_iso(), **payload})
        print("SYSTEM_SOUNDS_DONE", payload["status"], total_ms, dict(_system_sound_status))
        return dict(_system_sound_status)


def _start_system_sounds_task(settings: Settings) -> None:
    global _system_sounds_task
    if _system_sounds_task is None or _system_sounds_task.done():
        print("SYSTEM_SOUNDS_BG_START")
        _system_sounds_task = asyncio.create_task(ensure_system_sounds(settings), name="system-sounds-publish")
        def _on_done(task: asyncio.Task[dict[str, bool]]) -> None:
            try:
                status = task.result()
                print("SYSTEM_SOUNDS_BG_OK", status)
            except Exception as exc:
                print("SYSTEM_SOUNDS_BG_FAIL", repr(exc))
            finally:
                print("READY_WAITING_FOR_CALLS")

        _system_sounds_task.add_done_callback(_on_done)


def _system_sounds_snapshot() -> dict[str, bool]:
    return dict(_system_sound_status)


async def _maybe_start_moh(client: AriClient, session: CallSession, started: bool, action: str) -> bool:
    if started:
        return True
    result = await client.moh_start_safe(session.channel_id, moh_class="default")
    if result["ok"]:
        print("MOH_START_OK", session.call_id)
        session.log_event(action=action, status="ok")
        return True
    print("MOH_START_FAIL", session.call_id, result.get("http_status"))
    session.log_event(
        action=action,
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        details=result.get("details"),
    )
    return False


async def _maybe_stop_moh(client: AriClient, session: CallSession, started: bool) -> bool:
    if not started:
        return False
    result = await client.moh_stop_safe(session.channel_id)
    if result["ok"]:
        print("MOH_STOP_OK", session.call_id)
        session.log_event(action="moh_stop", status="ok")
    else:
        print("MOH_STOP_FAIL", session.call_id, result.get("http_status"))
        session.log_event(
            action="moh_stop",
            status="fail",
            reason=result.get("reason"),
            http_status=result.get("http_status"),
            details=result.get("details"),
        )
    return False


async def _play_fallback(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
) -> tuple[bool, bool]:
    candidates: list[str] = []
    if system_sounds.get(FALLBACK_SOUND_ID, False):
        candidates.append(FALLBACK_SOUND_ID)
    candidates.extend(BUILTIN_GENERAL_FALLBACK_MEDIA)

    fallback_played = False
    for media in candidates:
        started = time.perf_counter()
        moh_started = await _maybe_stop_moh(client, session, moh_started)
        result = await client.play_safe(session.channel_id, media)
        dur_ms = int((time.perf_counter() - started) * 1000)
        if result["ok"]:
            session.log_event(action="play_fallback", status="ok", media=media, sound_id=media, dur_ms=dur_ms)
            fallback_played = True
            break
        session.log_event(
            action="play_fallback",
            status="fail",
            reason=result.get("reason"),
            http_status=result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details=result.get("details"),
        )
        if result.get("reason") != "channel_gone":
            moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_after_fallback_fail")
        else:
            return False, moh_started

    return fallback_played, moh_started


def _prompt_media_for_stage(stage: DialogStage, system_sounds: dict[str, bool]) -> str:
    if stage == DialogStage.ISSUE and system_sounds.get(PROMPT_1_SOUND_ID, False):
        return PROMPT_1_SOUND_ID
    if stage == DialogStage.NAME and system_sounds.get(PROMPT_2_SOUND_ID, False):
        return PROMPT_2_SOUND_ID
    if stage == DialogStage.CITY and system_sounds.get(PROMPT_3_SOUND_ID, False):
        return PROMPT_3_SOUND_ID
    if stage == DialogStage.PHONE and system_sounds.get(PROMPT_4_SOUND_ID, False):
        return PROMPT_4_SOUND_ID
    fallback_sound_id = PROMPT_FALLBACK_SOUND_IDS.get(stage)
    if fallback_sound_id and system_sounds.get(fallback_sound_id, False):
        return fallback_sound_id
    if system_sounds.get(FALLBACK_SOUND_ID, False):
        return FALLBACK_SOUND_ID
    return BUILTIN_PROMPT_FALLBACK_MEDIA.get(stage, BUILTIN_GENERAL_FALLBACK_MEDIA[0])


async def _play_transfer_and_continue(
    client: AriClient,
    session: CallSession,
    system_sounds: dict[str, bool],
    moh_started: bool,
) -> tuple[bool, bool]:
    if system_sounds.get(TRANSFER_SOUND_ID, False):
        media = TRANSFER_SOUND_ID
    elif system_sounds.get(TRANSFER_FALLBACK_SOUND_ID, False):
        media = TRANSFER_FALLBACK_SOUND_ID
    else:
        media = BUILTIN_TRANSFER_FALLBACK_MEDIA[0]
    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    play_result = await client.play_safe(session.channel_id, media)
    dur_ms = int((time.perf_counter() - started) * 1000)
    if not play_result["ok"]:
        session.log_event(
            action="play_transfer_phrase",
            status="fail",
            reason=play_result.get("reason"),
            http_status=play_result.get("http_status"),
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details=play_result.get("details"),
        )
        return False, moh_started

    session.log_event(action="play_transfer_phrase", status="ok", media=media, sound_id=media, dur_ms=dur_ms)
    transfer_context = os.getenv("TRANSFER_CONTEXT", DEFAULT_TRANSFER_CONTEXT).strip() or DEFAULT_TRANSFER_CONTEXT
    transfer_exten = os.getenv("TRANSFER_EXTEN", DEFAULT_TRANSFER_EXTEN).strip() or DEFAULT_TRANSFER_EXTEN
    transfer_priority = _env_int("TRANSFER_PRIORITY", DEFAULT_TRANSFER_PRIORITY)
    transfer_start = time.perf_counter()
    cont_result = await client.continue_safe(
        session.channel_id,
        context=transfer_context,
        extension=transfer_exten,
        priority=transfer_priority,
    )
    transfer_ms = int((time.perf_counter() - transfer_start) * 1000)
    if cont_result["ok"]:
        session.transition(
            CallState.DONE,
            action="transfer",
            status="ok",
            dur_ms=transfer_ms,
            details={
                "context": transfer_context,
                "extension": transfer_exten,
                "priority": transfer_priority,
            },
        )
        return True, moh_started

    session.transition(
        CallState.FAILED,
        action="transfer",
        status="fail",
        reason=cont_result.get("reason"),
        http_status=cont_result.get("http_status"),
        dur_ms=transfer_ms,
        details=cont_result.get("details"),
    )
    return False, moh_started


async def _play_phone_confirmation_prompt(
    client: AriClient,
    settings: Settings,
    session: CallSession,
    moh_started: bool,
) -> tuple[bool, bool]:
    prompt_text = next_prompt(DialogStage.PHONE_CONFIRM, session.dialog.profile)
    started = time.perf_counter()
    prompt_path = session.artifact_dir / "phone_confirm_prompt.wav"
    tts_start = time.perf_counter()
    try:
        tts = SileroTTS()
        wav = await asyncio.to_thread(tts.synthesize, prompt_text)
        save_bytes(prompt_path, wav)
    except Exception as exc:
        session.log_event(
            action="phone_confirm_prompt_tts",
            status="fail",
            reason=repr(exc),
            dur_ms=int((time.perf_counter() - tts_start) * 1000),
            details={"prompt_text": prompt_text},
        )
        return False, moh_started
    session.log_event(
        action="phone_confirm_prompt_tts",
        status="ok",
        dur_ms=int((time.perf_counter() - tts_start) * 1000),
        details={"prompt_text": prompt_text},
    )

    remote_rel_path = f"{settings.asterisk_sounds_subdir}/{session.call_id}/phone_confirm_prompt.wav"
    publish_start = time.perf_counter()
    publish_timeout_sec = _publish_total_timeout_sec()
    publish_cmd_timeout_sec = _env_int("PUBLISH_CMD_TIMEOUT_SEC", 15)
    try:
        publish_result = await asyncio.wait_for(
            asyncio.to_thread(
                publish_wav_to_asterisk,
                prompt_path,
                remote_rel_path,
                settings,
                cmd_timeout_sec=publish_cmd_timeout_sec,
            ),
            timeout=publish_timeout_sec,
        )
    except asyncio.TimeoutError:
        session.log_event(
            action="phone_confirm_prompt_publish",
            status="fail",
            reason="publish_timeout",
            dur_ms=int((time.perf_counter() - publish_start) * 1000),
            details={"remote_rel_path": remote_rel_path},
        )
        return False, moh_started

    publish_ms = int((time.perf_counter() - publish_start) * 1000)
    if not publish_result.get("ok"):
        session.log_event(
            action="phone_confirm_prompt_publish",
            status="fail",
            reason=_publish_result_reason(publish_result),
            dur_ms=publish_ms,
            details=publish_result,
        )
        return False, moh_started

    media = str(publish_result.get("sound_id"))
    session.log_event(
        action="phone_confirm_prompt_publish",
        status="ok",
        sound_id=media,
        remote_path=str(publish_result.get("remote_path") or ""),
        dur_ms=publish_ms,
        details=publish_result.get("details"),
    )

    moh_started = await _maybe_stop_moh(client, session, moh_started)
    play_result = await client.play_safe(session.channel_id, media)
    dur_ms = int((time.perf_counter() - started) * 1000)
    if play_result["ok"]:
        session.log_event(
            action="play_prompt",
            status="ok",
            media=media,
            sound_id=media,
            dur_ms=dur_ms,
            details={"stage": DialogStage.PHONE_CONFIRM.value, "prompt_text": prompt_text},
        )
        return True, moh_started

    session.log_event(
        action="play_prompt",
        status="fail",
        reason=play_result.get("reason"),
        http_status=play_result.get("http_status"),
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details={**(play_result.get("details") or {}), "stage": DialogStage.PHONE_CONFIRM.value},
    )
    return False, moh_started


async def _play_prompt(
    client: AriClient,
    settings: Settings,
    session: CallSession,
    stage: DialogStage,
    system_sounds: dict[str, bool],
    moh_started: bool,
) -> tuple[bool, bool]:
    if stage == DialogStage.PHONE_CONFIRM:
        return await _play_phone_confirmation_prompt(client, settings, session, moh_started)

    media = _prompt_media_for_stage(stage, system_sounds)
    started = time.perf_counter()
    moh_started = await _maybe_stop_moh(client, session, moh_started)
    result = await client.play_safe(session.channel_id, media)
    dur_ms = int((time.perf_counter() - started) * 1000)

    if result["ok"]:
        session.log_event(action="play_prompt", status="ok", media=media, sound_id=media, dur_ms=dur_ms)
        return True, moh_started

    session.log_event(
        action="play_prompt",
        status="fail",
        reason=result.get("reason"),
        http_status=result.get("http_status"),
        media=media,
        sound_id=media,
        dur_ms=dur_ms,
        details=result.get("details"),
    )
    if result.get("reason") == "channel_gone":
        session.transition(CallState.DONE, action="channel_gone", status="ok")
        return False, moh_started

    moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_after_prompt_fail")
    _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
    # Continue dialog even after prompt failure/fallback attempt to avoid immediate silent drop.
    return True, moh_started


def _append_turn(artifact_dir: Path, payload: dict[str, Any]) -> None:
    turns_path = artifact_dir / "turns.jsonl"
    with turns_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _save_profile(artifact_dir: Path, profile: dict[str, Any]) -> None:
    save_json(artifact_dir / "profile.json", profile)


def _is_successful_phone_capture(
    previous_stage: DialogStage,
    next_stage: DialogStage,
    profile: dict[str, Any],
) -> bool:
    return (
        previous_stage == DialogStage.PHONE_CONFIRM
        and next_stage == DialogStage.DONE
        and bool(profile.get("phone_digits"))
        and profile.get("phone_confirmed") is True
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def _download_transcription_artifact(
    client: AriClient,
    session: CallSession,
    stage: DialogStage,
    turn_idx: int,
    record_name: str,
    dest_path: Path,
) -> TranscriptionArtifact:
    if dest_path.exists():
        dest_path.unlink()
        session.log_event(
            action="discard_stale_audio_artifact",
            status="ok",
            details={
                "stage": stage.value,
                "turn_idx": turn_idx,
                "record_name": record_name,
                "audio_path": str(dest_path.as_posix()),
            },
        )

    download_start = time.perf_counter()
    await client.download_recording(record_name, dest_path.as_posix())
    if not dest_path.exists():
        raise FileNotFoundError(f"recording download did not create {dest_path}")
    size_bytes = dest_path.stat().st_size
    if size_bytes <= 0:
        raise ValueError(f"recording download is empty: {dest_path}")

    artifact = TranscriptionArtifact(
        call_id=session.call_id,
        channel_id=session.channel_id,
        stage=stage,
        turn_idx=turn_idx,
        record_name=record_name,
        path=dest_path,
        size_bytes=size_bytes,
        sha256=_file_sha256(dest_path),
    )
    session.log_event(
        action="download_recording",
        status="ok",
        dur_ms=int((time.perf_counter() - download_start) * 1000),
        details=artifact.details(),
    )
    return artifact


def _transcribe_audio_artifact(_settings: Settings, artifact: TranscriptionArtifact) -> tuple[str, dict[str, Any]]:
    """Transcribe the artifact without fabricating speech when no STT backend is configured."""
    backend = os.getenv("TELEPHONY_STT_BACKEND", "").strip().lower()
    details = artifact.details()
    details["stt_backend"] = backend or "none"

    if backend in {"", "none", "disabled"}:
        details["reason"] = "stt_backend_not_configured"
        return "", details

    if backend == "fixture":
        fixture_env = f"TELEPHONY_STT_FIXTURE_{artifact.stage.value}"
        details["fixture_env"] = fixture_env
        return os.getenv(fixture_env, "").strip(), details

    if backend in {"openai", "whisper", "whisper_api"}:
        model = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1").strip() or "whisper-1"
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
        try:
            audio_bytes = artifact.path.read_bytes()
            client = WhisperAPIClient(api_key=_settings.openai_api_key, model=model, base_url=base_url)
            text = client.transcribe(audio_bytes, filename=artifact.path.name)
        except Exception as exc:
            details["reason"] = "stt_transcribe_failed"
            details["error"] = repr(exc)
            return "", details
        details["stt_model"] = model
        return text, details

    details["reason"] = "unsupported_stt_backend"
    return "", details


async def handle_call(
    client: AriClient,
    settings: Settings,
    app_name: str,
    session: CallSession,
    moh_started: bool = False,
) -> None:
    call_id = session.call_id
    channel_id = session.channel_id
    play_test = os.getenv("PLAY_TEST", "0") == "1"
    record_max_duration_seconds = _env_int("RECORD_MAX_DURATION_SECONDS", 6)
    record_max_silence_seconds = _env_int("RECORD_MAX_SILENCE_SECONDS", 2)
    record_beep = os.getenv("RECORD_BEEP", "0").strip().lower() in {"1", "true", "yes", "on"}

    try:
        session.transition(CallState.ASKING, action="call_flow_started", status="ok")
        system_sounds = _system_sounds_snapshot()

        if play_test:
            play_test_media = "sound:demo-congrats"
            print("PLAY_TEST_START", call_id, play_test_media)
            play_result = await client.play_safe(channel_id, play_test_media)
            if play_result["ok"]:
                print("PLAY_TEST_OK", call_id, play_test_media)
                session.log_event(action="play_test", status="ok", media=play_test_media)
            else:
                print("PLAY_TEST_FAIL", call_id, play_result.get("reason"))
                session.log_event(
                    action="play_test",
                    status="fail",
                    reason=play_result.get("reason"),
                    http_status=play_result.get("http_status"),
                    media=play_test_media,
                    details=play_result.get("details"),
                )
        else:
            print("PLAY_TEST_DISABLED", call_id)
            session.log_event(action="play_test_disabled", status="ok")

        artifact_dir = session.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)

        if settings.demo_mode == "synth":
            session.transition(CallState.RECORDING, action="record_start", status="start")
            record_name = f"{call_id}_utt1"
            record_start = time.perf_counter()
            record_result = await client.record_safe(
                channel_id,
                record_name,
                max_duration_seconds=record_max_duration_seconds,
                max_silence_seconds=record_max_silence_seconds,
                beep=record_beep,
            )
            if not record_result["ok"]:
                session.transition(
                    CallState.FAILED,
                    action="record_start",
                    status="fail",
                    reason=record_result.get("reason"),
                    http_status=record_result.get("http_status"),
                    details=record_result.get("details"),
                )
                return

            event = await client.wait_for_recording_finished(app_name, record_name, timeout=30)
            dur_ms = int((time.perf_counter() - record_start) * 1000)
            if event.get("type") != "RecordingFinished":
                reason = event.get("type") or "recording_event_missing"
                session.transition(CallState.FAILED, action="record_wait", status="fail", reason=reason, dur_ms=dur_ms)
                return
            session.log_event(action="record_done", status="ok", dur_ms=dur_ms)

            input_path = artifact_dir / "input.wav"
            await client.download_recording(record_name, input_path.as_posix())
            session.log_event(action="download_recording", status="ok")
            transcript_for_pipeline = ""
            profile_for_pipeline: dict[str, Any] = {}
        else:
            dialogue_lines: list[str] = []
            max_turns = 8
            while not should_stop_dialog(session.dialog.stage, session.dialog.turns_done, max_turns):
                should_continue, moh_started = await _play_prompt(
                    client,
                    settings,
                    session,
                    session.dialog.stage,
                    system_sounds,
                    moh_started,
                )
                if not should_continue:
                    return
                moh_started = await _maybe_stop_moh(client, session, moh_started)

                turn_idx = session.dialog.turns_done + 1
                stage = session.dialog.stage
                record_profile = _record_profile_for_stage(stage)
                session.transition(
                    CallState.RECORDING,
                    action="record_start",
                    status="start",
                    details={
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        **record_profile.details(),
                    },
                )
                record_name = f"{call_id}_{stage.value.lower()}_utt{turn_idx}"
                record_start = time.perf_counter()
                record_result = await client.record_safe(
                    channel_id,
                    record_name,
                    max_duration_seconds=record_profile.max_duration_seconds,
                    max_silence_seconds=record_profile.max_silence_seconds,
                    beep=record_beep,
                )
                if not record_result["ok"]:
                    if record_result.get("reason") == "channel_gone":
                        session.transition(CallState.DONE, action="channel_gone", status="ok")
                        return
                    session.transition(
                        CallState.FAILED,
                        action="record_start",
                        status="fail",
                        reason=record_result.get("reason"),
                        http_status=record_result.get("http_status"),
                        details=record_result.get("details"),
                    )
                    return

                event = await client.wait_for_recording_finished(
                    app_name,
                    record_name,
                    timeout=record_profile.wait_timeout_seconds,
                )
                dur_ms = int((time.perf_counter() - record_start) * 1000)
                if event.get("type") != "RecordingFinished":
                    reason = event.get("type") or "recording_event_missing"
                    session.transition(
                        CallState.FAILED,
                        action="record_wait",
                        status="fail",
                        reason=reason,
                        dur_ms=dur_ms,
                        details={"stage": stage.value, "turn_idx": turn_idx, **record_profile.details()},
                    )
                    return
                session.log_event(
                    action="record_done",
                    status="ok",
                    dur_ms=dur_ms,
                    details={
                        "stage": stage.value,
                        "turn_idx": turn_idx,
                        "record_name": record_name,
                        **record_profile.details(),
                    },
                )

                turn_audio = artifact_dir / f"turn_{turn_idx}.wav"
                try:
                    artifact = await _download_transcription_artifact(
                        client,
                        session,
                        stage,
                        turn_idx,
                        record_name,
                        turn_audio,
                    )
                except Exception as exc:
                    session.transition(
                        CallState.FAILED,
                        action="download_recording",
                        status="fail",
                        reason=repr(exc),
                        details={"stage": stage.value, "turn_idx": turn_idx, "record_name": record_name},
                    )
                    return

                stt_start = time.perf_counter()
                transcript_text, transcript_details = await asyncio.to_thread(
                    _transcribe_audio_artifact,
                    settings,
                    artifact,
                )
                stt_ms = int((time.perf_counter() - stt_start) * 1000)
                transcript_status = "ok" if transcript_text else "unavailable"
                session.log_event(
                    action="user_transcribed",
                    status=transcript_status,
                    reason=None if transcript_text else transcript_details.get("reason", "empty_transcript"),
                    dur_ms=stt_ms,
                    details={**transcript_details, "text": transcript_text},
                )
                prompt_text = next_prompt(stage, session.dialog.profile)
                _append_turn(artifact_dir, build_turn_record(stage, prompt_text, transcript_text).to_dict())

                decision_start = time.perf_counter()
                new_stage, new_profile = apply_turn(stage, session.dialog.profile, transcript_text)
                decision_ms = int((time.perf_counter() - decision_start) * 1000)
                session.log_event(
                    action="dialog_decision",
                    status="ok",
                    dur_ms=decision_ms,
                    details={
                        "from_stage": stage.value,
                        "to_stage": new_stage.value,
                        "turn_idx": turn_idx,
                        "profile_fields": sorted(new_profile.keys()),
                    },
                )
                session.dialog.stage = new_stage
                session.dialog.profile = new_profile
                session.dialog.turns_done += 1
                session.dialog.transcripts.append(transcript_text)
                _save_profile(artifact_dir, session.dialog.profile)
                dialogue_lines.append(f"Секретарь: {prompt_text}")
                dialogue_lines.append(f"Клиент: {transcript_text}")

                if _is_successful_phone_capture(stage, new_stage, session.dialog.profile):
                    transferred, moh_started = await _play_transfer_and_continue(
                        client,
                        session,
                        system_sounds,
                        moh_started,
                    )
                    if transferred:
                        return
                    _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                    await client.hangup_safe(channel_id)
                    return

            transcript_for_pipeline = "\n".join(dialogue_lines)
            profile_for_pipeline = dict(session.dialog.profile)
            if session.dialog.stage == DialogStage.DONE:
                transferred, moh_started = await _play_transfer_and_continue(client, session, system_sounds, moh_started)
                if transferred:
                    return
                _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                await client.hangup_safe(channel_id)
                return
            if session.dialog.stage in {DialogStage.PHONE, DialogStage.PHONE_CONFIRM}:
                session.transition(
                    CallState.FAILED,
                    action="phone_unconfirmed_no_generic_pipeline",
                    status="fail",
                    reason="phone_not_confirmed",
                    details={
                        "stage": session.dialog.stage.value,
                        "turns_done": session.dialog.turns_done,
                    },
                )
                _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
                await client.hangup_safe(channel_id)
                return

        session.transition(CallState.THINKING, action="pipeline_start", status="start")
        moh_started = await _maybe_start_moh(client, session, moh_started, action="moh_start_thinking")

        pipeline_start = time.perf_counter()
        if settings.demo_mode == "synth":
            result = run_pipeline(
                "real",
                settings,
                audio_path_override=input_path,
                call_id_override=session.call_id,
                artifact_dir_override=session.artifact_dir,
                events_path_override=session.events_path,
                channel_id=session.channel_id,
            )
        else:
            result = run_pipeline_from_transcript(
                "real",
                settings,
                transcript_text=transcript_for_pipeline,
                profile_override=profile_for_pipeline,
                call_id_override=session.call_id,
                artifact_dir_override=session.artifact_dir,
                events_path_override=session.events_path,
                channel_id=session.channel_id,
            )
        session.log_event(action="pipeline_done", status="ok", dur_ms=int((time.perf_counter() - pipeline_start) * 1000))

        response_tts_path = result["paths"].get("response_for_tts")
        if not response_tts_path:
            session.transition(CallState.FAILED, action="tts_text", status="fail", reason="response_for_tts_missing")
            return

        tts_text = Path(response_tts_path).read_text(encoding="utf-8")
        tts = SileroTTS()
        tts_start = time.perf_counter()
        reply_wav = tts.synthesize(tts_text)
        reply_path = artifact_dir / "reply.wav"
        save_bytes(reply_path, reply_wav)
        session.log_event(action="tts_done", status="ok", dur_ms=int((time.perf_counter() - tts_start) * 1000))

        remote_rel_path = f"{settings.asterisk_sounds_subdir}/{call_id}/reply.wav"
        publish_start = time.perf_counter()
        publish_timeout_sec = _publish_total_timeout_sec()
        publish_cmd_timeout_sec = _env_int("PUBLISH_CMD_TIMEOUT_SEC", 15)
        try:
            publish_result = await asyncio.wait_for(
                asyncio.to_thread(
                    publish_wav_to_asterisk,
                    reply_path,
                    remote_rel_path,
                    settings,
                    cmd_timeout_sec=publish_cmd_timeout_sec,
                ),
                timeout=publish_timeout_sec,
            )
        except asyncio.TimeoutError:
            session.log_event(
                action="publish",
                status="fail",
                reason="publish_timeout",
                dur_ms=int((time.perf_counter() - publish_start) * 1000),
                details={
                    "remote_rel_path": remote_rel_path,
                    "publish_timeout_sec": publish_timeout_sec,
                    "publish_cmd_timeout_sec": publish_cmd_timeout_sec,
                    "docker_container": bool(settings.asterisk_docker_container),
                },
            )
            fallback_details = {
                "remote_rel_path": remote_rel_path,
                "publish_timeout_sec": publish_timeout_sec,
                "publish_cmd_timeout_sec": publish_cmd_timeout_sec,
                "docker_container": bool(settings.asterisk_docker_container),
            }
            _played, moh_started = await _play_publish_failure_fallback(
                client,
                session,
                system_sounds,
                moh_started,
                reason="publish_timeout",
                publish_details=fallback_details,
            )
            session.transition(
                CallState.FAILED,
                action="publish_timeout_fallback_no_immediate_hangup",
                status="ok",
            )
            return

        publish_ms = int((time.perf_counter() - publish_start) * 1000)
        if not publish_result.get("ok"):
            reason = _publish_result_reason(publish_result)
            session.log_event(action="publish", status="fail", reason=reason, dur_ms=publish_ms, details=publish_result)
            _played, moh_started = await _play_publish_failure_fallback(
                client,
                session,
                system_sounds,
                moh_started,
                reason=reason,
                publish_details=publish_result,
            )
            await client.hangup_safe(channel_id)
            session.transition(CallState.FAILED, action="hangup_after_publish_fail", status="ok")
            return

        media_id = str(publish_result.get("sound_id"))
        session.log_event(
            action="publish",
            status="ok",
            sound_id=media_id,
            remote_path=str(publish_result.get("remote_path") or ""),
            dur_ms=publish_ms,
            details=publish_result.get("details"),
        )

        moh_started = await _maybe_stop_moh(client, session, moh_started)
        session.transition(CallState.RESPONDING, action="playback_start", status="start", media=media_id)

        play_result = await client.play_safe(channel_id, media_id)
        if not play_result["ok"]:
            session.log_event(
                action="playback",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media_id,
                sound_id=media_id,
                details=play_result.get("details"),
            )
            _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
            await client.hangup_safe(channel_id)
            session.transition(
                CallState.FAILED,
                action="playback_failed",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media_id,
                sound_id=media_id,
                details=play_result.get("details"),
            )
            return

        session.log_event(action="playback", status="ok", media=media_id, sound_id=media_id)
        await asyncio.sleep(1)
        await client.hangup_safe(channel_id)
        session.transition(CallState.DONE, action="hangup", status="ok")
    except Exception as exc:
        session.transition(CallState.FAILED, action="call_flow_exception", status="fail", reason=repr(exc))
        raise
    finally:
        await _maybe_stop_moh(client, session, moh_started)


async def main() -> None:
    settings = Settings.from_env()
    if os.getenv("WARMUP", "0") == "1":
        try:
            warmup_embeddings()
            print("WARMUP_EMBEDDINGS_OK")
        except Exception as exc:
            print("WARMUP_EMBEDDINGS_FAIL", repr(exc))

    base_url = os.getenv("ARI_URL", "http://localhost:8088/ari")
    username = os.getenv("ARI_USER", "")
    password = os.getenv("ARI_PASSWORD", "")
    app_name = os.getenv("ARI_APP_NAME", "")
    if not app_name:
        print("ARI_APP_NAME is required")
        return

    _start_system_sounds_task(settings)

    client = AriClient(base_url=base_url, username=username, password=password)
    sessions: dict[str, CallSession] = {}
    call_tasks: dict[str, asyncio.Task[None]] = {}

    print("ARI_LISTENING", base_url, app_name)
    try:
        async for event in client.ws_events(app_name=app_name, subscribe_all=True):
            event_type = event.get("type")
            channel = event.get("channel", {})
            channel_id = channel.get("id")

            if event_type == "StasisStart" and channel_id:
                call_id = channel_id
                artifact_dir = settings.storage_dir / "artifacts" / call_id
                session = CallSession(call_id=call_id, channel_id=channel_id, artifact_dir=artifact_dir)
                sessions[channel_id] = session
                print("STASIS_START", channel_id)

                answer_result = await client.answer_safe(channel_id)
                if not answer_result["ok"]:
                    session.transition(
                        CallState.FAILED,
                        action="answer",
                        status="fail",
                        reason=answer_result.get("reason"),
                        http_status=answer_result.get("http_status"),
                        details=answer_result.get("details"),
                    )
                    continue
                session.transition(CallState.ANSWERED, action="answer", status="ok")

                moh_started = await _maybe_start_moh(client, session, False, action="moh_start_after_answer")

                async def _run_call(sess: CallSession, started: bool) -> None:
                    try:
                        await handle_call(client, settings, app_name, sess, moh_started=started)
                    except Exception as exc:
                        print("CALL_FLOW_ERROR", sess.channel_id, repr(exc))

                task = asyncio.create_task(_run_call(session, moh_started), name=f"call-{channel_id}")
                call_tasks[channel_id] = task
                task.add_done_callback(lambda _t, ch=channel_id: call_tasks.pop(ch, None))

            elif event_type in {"StasisEnd", "ChannelDestroyed"} and channel_id:
                session = sessions.pop(channel_id, None)
                if session is not None and session.state not in {CallState.DONE, CallState.FAILED}:
                    session.transition(CallState.DONE, action=event_type, status="ok")
                print("STASIS_END", channel_id, event_type)
    except Exception as exc:
        print("ARI_APP_ERROR", repr(exc))
    finally:
        if call_tasks:
            await asyncio.gather(*call_tasks.values(), return_exceptions=True)
        if _system_sounds_task is not None:
            await asyncio.gather(_system_sounds_task, return_exceptions=True)


def _reset_fallback_cache_for_tests() -> None:
    global _system_sounds_done, _system_sounds_lock, _system_sounds_task
    _system_sounds_done = False
    _system_sounds_lock = None
    _system_sounds_task = None
    for sound_id in _system_sound_status:
        _system_sound_status[sound_id] = False


if __name__ == "__main__":
    asyncio.run(main())
