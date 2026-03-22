"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from ..config.settings import Settings
from ..core.runner import run_pipeline, run_pipeline_from_transcript
from ..rag.embeddings import warmup_embeddings
from ..storage.files import save_bytes, save_json
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .call_session import CallSession, CallState, DialogStage
from .dialog import apply_turn, build_turn_record, next_prompt, should_stop_dialog
from .publish_to_asterisk import publish_wav_to_asterisk


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


async def _maybe_stop_moh(client: AriClient, session: CallSession, started: bool) -> bool:
    """Stop MOH if started and log result to events."""
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


async def _play_prompt(
    client: AriClient,
    settings: Settings,
    session: CallSession,
    turn_index: int,
    prompt_text: str,
) -> bool:
    tts = SileroTTS()
    prompt_wav = tts.synthesize(prompt_text)
    prompt_path = session.artifact_dir / f"prompt_{turn_index}.wav"
    save_bytes(prompt_path, prompt_wav)

    remote_rel_path = f"{settings.asterisk_sounds_subdir}/{session.call_id}/prompt_{turn_index}.wav"
    publish_result = publish_wav_to_asterisk(prompt_path, remote_rel_path, settings)
    if not publish_result.get("ok"):
        session.transition(
            CallState.FAILED,
            action="publish_prompt",
            status="fail",
            reason="publish_failed",
            details=publish_result,
        )
        return False

    media_id = str(publish_result.get("sound_id"))
    play_result = await client.play_safe(session.channel_id, media_id)
    if not play_result["ok"]:
        if play_result.get("reason") == "channel_gone":
            session.transition(CallState.DONE, action="channel_gone", status="ok")
            return False
        session.transition(
            CallState.FAILED,
            action="prompt_playback",
            status="fail",
            reason=play_result.get("reason"),
            http_status=play_result.get("http_status"),
            media=media_id,
            sound_id=media_id,
            details=play_result.get("details"),
        )
        return False

    session.log_event(action="prompt_played", status="ok", media=media_id, sound_id=media_id)
    return True


async def handle_call(client: AriClient, settings: Settings, app_name: str, session: CallSession) -> None:
    """Handle a single call lifecycle."""
    call_id = session.call_id
    channel_id = session.channel_id
    play_test = os.getenv("PLAY_TEST", "0") == "1"
    record_max_duration_seconds = _env_int("RECORD_MAX_DURATION_SECONDS", 6)
    record_max_silence_seconds = _env_int("RECORD_MAX_SILENCE_SECONDS", 2)
    record_beep = _env_bool("RECORD_BEEP", default=False)

    try:
        session.transition(CallState.ASKING, action="call_flow_started", status="ok")

        if play_test:
            play_test_media = "sound:demo-congrats"
            print("PLAY_TEST_START", call_id, play_test_media)
            play_result = await client.play_safe(channel_id, play_test_media)
            if play_result["ok"]:
                print("PLAY_TEST_OK", call_id, play_test_media)
                session.log_event(action="play_test", status="ok", media=play_test_media)
            else:
                fallback_media = "sound:tt-weasels"
                print("PLAY_TEST_START", call_id, fallback_media)
                fallback_result = await client.play_safe(channel_id, fallback_media)
                if fallback_result["ok"]:
                    print("PLAY_TEST_OK", call_id, fallback_media)
                    session.log_event(action="play_test", status="ok", media=fallback_media)
                else:
                    print("PLAY_TEST_FAIL", call_id, fallback_result.get("reason"))
                    session.log_event(
                        action="play_test",
                        status="fail",
                        reason=fallback_result.get("reason"),
                        http_status=fallback_result.get("http_status"),
                        media=fallback_media,
                        details=fallback_result.get("details"),
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
                print("RECORD_FAILED", call_id, record_result.get("reason"))
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
                print("RECORD_FAILED", call_id, reason)
                session.transition(
                    CallState.FAILED,
                    action="record_wait",
                    status="fail",
                    reason=reason,
                    dur_ms=dur_ms,
                )
                return

            print("RECORD_DONE", call_id)
            session.log_event(action="record_done", status="ok", dur_ms=dur_ms)

            input_path = artifact_dir / "input.wav"
            await client.download_recording(record_name, input_path.as_posix())
            print("DOWNLOAD_OK", call_id)
            session.log_event(action="download_recording", status="ok")
            transcript_for_pipeline = ""
            profile_for_pipeline: dict[str, Any] = {}
        else:
            dialogue_lines: list[str] = []
            max_turns = 4
            while not should_stop_dialog(session.dialog.stage, session.dialog.turns_done, max_turns):
                prompt_text = next_prompt(session.dialog.stage, session.dialog.profile)
                turn_idx = session.dialog.turns_done + 1
                if not await _play_prompt(client, settings, session, turn_idx, prompt_text):
                    return

                session.transition(CallState.RECORDING, action="record_start", status="start")
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
                    session.transition(
                        CallState.FAILED,
                        action="record_wait",
                        status="fail",
                        reason=reason,
                        dur_ms=dur_ms,
                    )
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

                turn_record = build_turn_record(session.dialog.stage, prompt_text, transcript_text).to_dict()
                _append_turn(artifact_dir, turn_record)

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
        moh_started = False
        try:
            moh_result = await client.moh_start_safe(channel_id, moh_class="default")
            if moh_result["ok"]:
                print("MOH_START_OK", call_id)
                session.log_event(action="moh_start", status="ok")
                moh_started = True
            else:
                print("MOH_START_FAIL", call_id, moh_result.get("http_status"))
                session.log_event(
                    action="moh_start",
                    status="fail",
                    reason=moh_result.get("reason"),
                    http_status=moh_result.get("http_status"),
                    details=moh_result.get("details"),
                )

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
            pipeline_ms = int((time.perf_counter() - pipeline_start) * 1000)
            print("PIPELINE_OK", call_id)
            session.log_event(action="pipeline_done", status="ok", dur_ms=pipeline_ms)
        finally:
            # MOH must always stop in finally and before any playback.
            moh_started = await _maybe_stop_moh(client, session, moh_started)

        response_tts_path = result["paths"].get("response_for_tts")
        if not response_tts_path:
            print("TTS_TEXT_MISSING", call_id)
            session.transition(CallState.FAILED, action="tts_text", status="fail", reason="response_for_tts_missing")
            return

        tts_text = Path(response_tts_path).read_text(encoding="utf-8")
        tts = SileroTTS()
        tts_start = time.perf_counter()
        reply_wav = tts.synthesize(tts_text)
        reply_path = artifact_dir / "reply.wav"
        save_bytes(reply_path, reply_wav)
        print("TTS_OK", call_id)
        session.log_event(action="tts_done", status="ok", dur_ms=int((time.perf_counter() - tts_start) * 1000))

        remote_rel_path = f"{settings.asterisk_sounds_subdir}/{call_id}/reply.wav"
        publish_start = time.perf_counter()
        publish_result = publish_wav_to_asterisk(reply_path, remote_rel_path, settings)
        publish_ms = int((time.perf_counter() - publish_start) * 1000)
        if not publish_result.get("ok"):
            print("PUBLISH_ERROR", call_id, remote_rel_path, publish_result.get("error"))
            session.transition(
                CallState.FAILED,
                action="publish",
                status="fail",
                reason="publish_failed",
                dur_ms=publish_ms,
                details=publish_result,
            )
            return

        media_id = str(publish_result.get("sound_id"))
        print("PUBLISH_OK", call_id, publish_result.get("remote_path"), media_id)
        session.log_event(
            action="publish",
            status="ok",
            sound_id=media_id,
            remote_path=str(publish_result.get("remote_path") or ""),
            dur_ms=publish_ms,
            details=publish_result.get("details"),
        )

        # Safety: ensure MOH is definitely off before playback.
        moh_started = await _maybe_stop_moh(client, session, moh_started)
        session.transition(CallState.RESPONDING, action="playback_start", status="start", media=media_id)

        play_result = await client.play_safe(channel_id, media_id)
        if not play_result["ok"]:
            print("PLAY_FAIL", call_id, channel_id, media_id, play_result.get("reason"))
            session.transition(
                CallState.FAILED,
                action="playback",
                status="fail",
                reason=play_result.get("reason"),
                http_status=play_result.get("http_status"),
                media=media_id,
                sound_id=media_id,
                details=play_result.get("details"),
            )
            await client.hangup_safe(channel_id)
            return

        print("PLAY_OK", call_id)
        session.log_event(action="playback", status="ok", media=media_id, sound_id=media_id)

        await asyncio.sleep(1)
        await client.hangup_safe(channel_id)
        session.transition(CallState.DONE, action="hangup", status="ok")
    except Exception as exc:
        session.transition(CallState.FAILED, action="call_flow_exception", status="fail", reason=repr(exc))
        raise


async def main() -> None:
    """Run ARI event listener."""
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

    client = AriClient(base_url=base_url, username=username, password=password)
    sessions: dict[str, CallSession] = {}

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
                    print("ANSWER_FAILED", channel_id, answer_result.get("reason"))
                    session.transition(
                        CallState.FAILED,
                        action="answer",
                        status="fail",
                        reason=answer_result.get("reason"),
                        http_status=answer_result.get("http_status"),
                        details=answer_result.get("details"),
                    )
                    continue

                print("ANSWERED", channel_id)
                session.transition(CallState.ANSWERED, action="answer", status="ok")

                try:
                    await handle_call(client, settings, app_name, session)
                except Exception as exc:
                    print("CALL_FLOW_ERROR", channel_id, repr(exc))

            elif event_type in {"StasisEnd", "ChannelDestroyed"} and channel_id:
                session = sessions.pop(channel_id, None)
                if session is not None and session.state not in {CallState.DONE, CallState.FAILED}:
                    session.transition(CallState.DONE, action=event_type, status="ok")
                print("STASIS_END", channel_id, event_type)

    except Exception as exc:
        print("ARI_APP_ERROR", repr(exc))


if __name__ == "__main__":
    asyncio.run(main())
