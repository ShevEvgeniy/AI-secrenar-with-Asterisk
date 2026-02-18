"""Tests for TTS normalization."""

from ai_secretary.tts.normalize_for_tts import inn_digits_to_spaced, normalize_text


def test_normalize_text_collapses_whitespace() -> None:
    assert normalize_text("a  b\n c") == "a b c"


def test_inn_digits_to_spaced() -> None:
    assert inn_digits_to_spaced("7701234567") == "7 7 0 1 2 3 4 5 6 7"
