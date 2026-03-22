"""Tests for TTS stress overrides."""

from __future__ import annotations

from pathlib import Path

from ai_secretary.tts.normalize_for_tts import apply_stress_overrides, _reset_stress_dict_cache_for_tests


def test_apply_stress_overrides_case_insensitive_and_word_boundaries(tmp_path: Path, monkeypatch) -> None:
    dict_path = tmp_path / "stress.txt"
    dict_path.write_text("замок=за+мок\nАнна=А+нна\n", encoding="utf-8")
    monkeypatch.setenv("TTS_STRESS_DICT_PATH", str(dict_path))
    _reset_stress_dict_cache_for_tests()

    text = "Замок подзамок ЗАМОК и анна."
    out = apply_stress_overrides(text)

    assert out == "за+мок подзамок за+мок и А+нна."


def test_apply_stress_overrides_missing_dict_returns_same_text(monkeypatch) -> None:
    monkeypatch.setenv("TTS_STRESS_DICT_PATH", "")
    _reset_stress_dict_cache_for_tests()
    text = "Привет мир"
    assert apply_stress_overrides(text) == text
