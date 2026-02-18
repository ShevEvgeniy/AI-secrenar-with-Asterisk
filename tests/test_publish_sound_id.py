"""Tests for Asterisk sound id building."""

from ai_secretary.storage.publish_to_asterisk import build_remote_sound_id


def test_build_remote_sound_id() -> None:
    assert build_remote_sound_id("ai_secretary/call123/reply.wav") == "sound:ai_secretary/call123/reply"


def test_build_remote_sound_id_stable_normalization() -> None:
    assert build_remote_sound_id("/ai_secretary\\call123\\reply.wav") == "sound:ai_secretary/call123/reply"
