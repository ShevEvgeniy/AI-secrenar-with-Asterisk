"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any

from ..config.settings import Settings
from ..core.runner import run_pipeline
from ..storage.files import save_bytes
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .call_session import CallSession, CallState
from .publish_to_asterisk import publish_wav_to_asterisk


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


async def handle_call(client: AriClient, settings: Settings, app_name: str, session: CallSession) -> None:
    """Handle a single call lifecycle."""
    call_id = session.call_id
    channel_id = session.channel_id
    play_test = os.getenv("PLAY_TEST", "0") == "1"

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

        session.transition(CallState.RECORDING, action="record_start", status="start")
        record_name = f"{call_id}_utt1"
        record_start = time.perf_counter()
        record_result = await client.record_safe(channel_id, record_name, max_duration_seconds=10)
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

        artifact_dir = session.artifact_dir
        artifact_dir.mkdir(parents=True, exist_ok=True)
        input_path = artifact_dir / "input.wav"

        await client.download_recording(record_name, input_path.as_posix())
        print("DOWNLOAD_OK", call_id)
        session.log_event(action="download_recording", status="ok")

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
            result = run_pipeline(
                "real",
                settings,
                audio_path_override=input_path,
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
        publish_result = publish_wav_to_asterisk(reply_path, remote_rel_path, settings)
        if not publish_result.get("ok"):
            print("PUBLISH_ERROR", call_id, remote_rel_path, publish_result.get("error"))
            session.transition(
                CallState.FAILED,
                action="publish",
                status="fail",
                reason="publish_failed",
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
