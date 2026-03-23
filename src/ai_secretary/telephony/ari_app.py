"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config.settings import Settings
from ..core.runner import run_pipeline, run_pipeline_from_transcript
from ..rag.embeddings import warmup_embeddings
from ..storage.files import save_bytes, save_json
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .call_session import CallSession, CallState, DialogStage
from .dialog import PROMPTS, apply_turn, build_turn_record, next_prompt, should_stop_dialog
from .publish_to_asterisk import publish_wav_to_asterisk

PROMPT_1_SOUND_ID = "sound:ai_secretary/_system/prompt_1"
PROMPT_2_SOUND_ID = "sound:ai_secretary/_system/prompt_2"
FALLBACK_SOUND_ID = "sound:ai_secretary/_system/fallback"
TRANSFER_SOUND_ID = "sound:ai_secretary/_system/transfer"
BUILTIN_FALLBACK_MEDIA = ("sound:demo-congrats", "sound:tt-weasels")

_SYSTEM_SOUND_TEXTS: dict[str, str] = {
    PROMPT_1_SOUND_ID: PROMPTS[DialogStage.ISSUE],
    PROMPT_2_SOUND_ID: PROMPTS[DialogStage.NAME],
    FALLBACK_SOUND_ID: "Одну секунду, пожалуйста.",
    TRANSFER_SOUND_ID: PROMPTS[DialogStage.DONE],
}
_system_sound_status: dict[str, bool] = {sound_id: False for sound_id in _SYSTEM_SOUND_TEXTS}
_system_sounds_done = False
_system_sounds_lock: asyncio.Lock | None = None
_system_sounds_task: asyncio.Task[dict[str, bool]] | None = None


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _publish_total_timeout_sec() -> int:
    value = _env_int("PUBLISH_TOTAL_TIMEOUT_SEC", 8)
    return value if value > 0 else 8


def _system_sounds_publish_timeout_sec() -> int:
    value = _env_int("SYSTEM_SOUNDS_PUBLISH_TIMEOUT_SEC", 20)
    return value if value > 0 else 20


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


def _publish_fail_reason(message: str) -> str:
    lowered = (message or "").lower()
    if "timed out" in lowered or "timeout" in lowered:
        return "timeout"
    return "publish_failed"


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
        tts = SileroTTS()
        timeout_sec = _system_sounds_publish_timeout_sec()

        cmd_timeout_sec = max(1, timeout_sec - 2)
        for sound_id, text in _SYSTEM_SOUND_TEXTS.items():
            item_start = time.perf_counter()
            file_name = sound_id.split("/")[-1] + ".wav"
            local_path = local_dir / file_name
            try:
                if not local_path.exists():
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
                reason = None if ok else _publish_fail_reason(str(result.get("error") or ""))
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
    candidates.extend(BUILTIN_FALLBACK_MEDIA)

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
    if stage in {DialogStage.NAME, DialogStage.CITY, DialogStage.PHONE} and system_sounds.get(PROMPT_2_SOUND_ID, False):
        return PROMPT_2_SOUND_ID
    return BUILTIN_FALLBACK_MEDIA[0]


async def _play_prompt(
    client: AriClient,
    session: CallSession,
    stage: DialogStage,
    system_sounds: dict[str, bool],
    moh_started: bool,
) -> tuple[bool, bool]:
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


def _transcribe_placeholder(stage: DialogStage) -> str:
    if stage == DialogStage.ISSUE:
        return "Хочу уточнить условия поставки оборудования."
    if stage == DialogStage.NAME:
        return "Меня зовут Иван Петров."
    if stage == DialogStage.CITY:
        return "Я из Казани."
    return "Мой телефон 9 903 678 46 53."


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
            max_turns = 4
            while not should_stop_dialog(session.dialog.stage, session.dialog.turns_done, max_turns):
                should_continue, moh_started = await _play_prompt(
                    client,
                    session,
                    session.dialog.stage,
                    system_sounds,
                    moh_started,
                )
                if not should_continue:
                    return
                moh_started = await _maybe_stop_moh(client, session, moh_started)

                session.transition(CallState.RECORDING, action="record_start", status="start")
                turn_idx = session.dialog.turns_done + 1
                record_name = f"{call_id}_utt{turn_idx}"
                record_start = time.perf_counter()
                record_result = await client.record_safe(
                    channel_id,
                    record_name,
                    max_duration_seconds=record_max_duration_seconds,
                    max_silence_seconds=record_max_silence_seconds,
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

                event = await client.wait_for_recording_finished(app_name, record_name, timeout=30)
                dur_ms = int((time.perf_counter() - record_start) * 1000)
                if event.get("type") != "RecordingFinished":
                    reason = event.get("type") or "recording_event_missing"
                    session.transition(CallState.FAILED, action="record_wait", status="fail", reason=reason, dur_ms=dur_ms)
                    return
                session.log_event(action="record_done", status="ok", dur_ms=dur_ms)

                turn_audio = artifact_dir / f"turn_{turn_idx}.wav"
                await client.download_recording(record_name, turn_audio.as_posix())
                session.log_event(action="download_recording", status="ok")

                transcript_text = _transcribe_placeholder(session.dialog.stage)
                session.log_event(
                    action="user_transcribed",
                    status="ok",
                    details={"state": session.dialog.stage.value, "text": transcript_text},
                )
                prompt_text = next_prompt(session.dialog.stage, session.dialog.profile)
                _append_turn(artifact_dir, build_turn_record(session.dialog.stage, prompt_text, transcript_text).to_dict())

                new_stage, new_profile = apply_turn(session.dialog.stage, session.dialog.profile, transcript_text)
                session.dialog.stage = new_stage
                session.dialog.profile = new_profile
                session.dialog.turns_done += 1
                session.dialog.transcripts.append(transcript_text)
                _save_profile(artifact_dir, session.dialog.profile)
                dialogue_lines.append(f"Секретарь: {prompt_text}")
                dialogue_lines.append(f"Клиент: {transcript_text}")

            transcript_for_pipeline = "\n".join(dialogue_lines)
            profile_for_pipeline = dict(session.dialog.profile)

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
        try:
            publish_result = await asyncio.wait_for(
                asyncio.to_thread(publish_wav_to_asterisk, reply_path, remote_rel_path, settings),
                timeout=_publish_total_timeout_sec(),
            )
        except asyncio.TimeoutError:
            session.log_event(action="publish", status="fail", reason="publish_timeout", dur_ms=int((time.perf_counter() - publish_start) * 1000))
            _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
            await client.hangup_safe(channel_id)
            session.transition(CallState.FAILED, action="hangup_after_publish_fail", status="ok")
            return

        publish_ms = int((time.perf_counter() - publish_start) * 1000)
        if not publish_result.get("ok"):
            session.log_event(action="publish", status="fail", reason="publish_failed", dur_ms=publish_ms, details=publish_result)
            _played, moh_started = await _play_fallback(client, session, system_sounds, moh_started)
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
