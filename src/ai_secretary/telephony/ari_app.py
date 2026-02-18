"""ARI app listener entry point."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from ..config.settings import Settings
from ..core.runner import run_pipeline
from ..storage.files import save_bytes
from ..tts.silero import SileroTTS
from .ari_client import AriClient
from .publish_to_asterisk import publish_wav_to_asterisk


async def handle_call(
    client: AriClient,
    settings: Settings,
    app_name: str,
    channel_id: str,
) -> None:
    """Handle a single call lifecycle."""
    call_id = channel_id
    play_test = os.getenv("PLAY_TEST", "0") == "1"
    if play_test:
        play_test_media = "sound:demo-congrats"
        print("PLAY_TEST_START", call_id, play_test_media)
        try:
            await client.play(channel_id, play_test_media)
            print("PLAY_TEST_OK", call_id, play_test_media)
        except httpx.HTTPStatusError:
            fallback_media = "sound:tt-weasels"
            print("PLAY_TEST_START", call_id, fallback_media)
            try:
                await client.play(channel_id, fallback_media)
                print("PLAY_TEST_OK", call_id, fallback_media)
            except Exception as exc:
                print("PLAY_TEST_FAIL", call_id, repr(exc))
    else:
        print("PLAY_TEST_DISABLED", call_id)

    print("RECORD_START", call_id)

    record_name = f"{call_id}_utt1"
    await client.record(channel_id, record_name, max_duration_seconds=10)
    event = await client.wait_for_recording_finished(app_name, record_name, timeout=30)
    if event.get("type") != "RecordingFinished":
        print("RECORD_FAILED", call_id, event.get("type"))
        return

    print("RECORD_DONE", call_id)

    artifact_dir = settings.storage_dir / "artifacts" / call_id
    artifact_dir.mkdir(parents=True, exist_ok=True)
    input_path = artifact_dir / "input.wav"

    await client.download_recording(record_name, input_path.as_posix())
    print("DOWNLOAD_OK", call_id)

    moh_started = False
    try:
        try:
            await client.moh_start(channel_id, moh_class="default")
            print("MOH_START_OK", call_id)
            moh_started = True
        except httpx.HTTPStatusError as exc:
            print("MOH_START_FAIL", call_id, exc.response.status_code)
        except Exception as exc:
            print("MOH_START_FAIL", call_id, repr(exc))

        result = run_pipeline("real", settings, audio_path_override=input_path)
        print("PIPELINE_OK", call_id)
    finally:
        if moh_started:
            try:
                await client.moh_stop(channel_id)
                print("MOH_STOP_OK", call_id)
            except httpx.HTTPStatusError as exc:
                print("MOH_STOP_FAIL", call_id, exc.response.status_code)
            except Exception as exc:
                print("MOH_STOP_FAIL", call_id, repr(exc))

    response_tts_path = result["paths"].get("response_for_tts")
    if not response_tts_path:
        print("TTS_TEXT_MISSING", call_id)
        return

    tts_text = Path(response_tts_path).read_text(encoding="utf-8")
    tts = SileroTTS()
    reply_wav = tts.synthesize(tts_text)
    reply_path = artifact_dir / "reply.wav"
    save_bytes(reply_path, reply_wav)
    print("TTS_OK", call_id)

    remote_rel_path = f"{settings.asterisk_sounds_subdir}/{call_id}/reply.wav"
    try:
        publish_result = publish_wav_to_asterisk(reply_path, remote_rel_path, settings)
        if not publish_result.get("ok"):
            print(
                "PUBLISH_ERROR",
                call_id,
                remote_rel_path,
                publish_result.get("error"),
                publish_result.get("details"),
            )
            raise RuntimeError(str(publish_result.get("error")))

        media_id = str(publish_result.get("sound_id"))
        print("PUBLISH_OK", call_id, publish_result.get("remote_path"), media_id)
    except Exception as exc:
        print("PUBLISH_ERROR", call_id, remote_rel_path, repr(exc))
        raise

    try:
        await client.get_channel(channel_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print("CHANNEL_GONE_BEFORE_PLAY", call_id, channel_id)
            return
        raise

    try:
        await client.play(channel_id, media_id)
        print("PLAY_OK", call_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print("PLAY_404_CHANNEL_OR_MEDIA", call_id, channel_id, media_id)
            try:
                await client.hangup(channel_id)
            except Exception as hangup_exc:
                print("HANGUP_ERROR", call_id, repr(hangup_exc))
            return
        raise

    await asyncio.sleep(1)
    await client.hangup(channel_id)


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


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
    sessions: dict[str, dict[str, Any]] = {}

    print("ARI_LISTENING", base_url, app_name)
    try:
        async for event in client.ws_events(app_name=app_name, subscribe_all=True):
            event_type = event.get("type")
            channel = event.get("channel", {})
            channel_id = channel.get("id")

            if event_type == "StasisStart" and channel_id:
                print("STASIS_START", channel_id)
                try:
                    await client.answer(channel_id)
                    print("ANSWERED", channel_id)
                except Exception as exc:
                    print("ANSWER_FAILED", channel_id, str(exc))
                    continue

                sessions[channel_id] = {"started_at": _now_iso()}
                try:
                    await handle_call(client, settings, app_name, channel_id)
                except Exception as exc:
                    print("CALL_FLOW_ERROR", channel_id, repr(exc))

            elif event_type in {"StasisEnd", "ChannelDestroyed"} and channel_id:
                if channel_id in sessions:
                    sessions.pop(channel_id, None)
                print("STASIS_END", channel_id, event_type)

    except Exception as exc:
        print("ARI_APP_ERROR", repr(exc))


if __name__ == "__main__":
    asyncio.run(main())
    