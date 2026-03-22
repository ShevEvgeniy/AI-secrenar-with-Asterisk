"""Thin wrapper for backward-compatible telephony imports."""

from __future__ import annotations

from ..storage.publish_to_asterisk import build_remote_sound_id, publish_wav_to_asterisk, remote_file_exists

__all__ = ["build_remote_sound_id", "publish_wav_to_asterisk", "remote_file_exists"]
