"""Tests for text artifacts."""

from dataclasses import replace

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline


def test_text_artifacts_non_empty(tmp_path) -> None:
    settings = Settings.from_env()
    settings = replace(settings, storage_dir=tmp_path / "storage")
    result = run_pipeline("synth", settings)

    summary_path = result["paths"]["summary"]
    response_path = result["paths"]["response"]
    response_tts_path = result["paths"]["response_for_tts"]

    with open(summary_path, "r", encoding="utf-8") as f:
        assert len(f.read().strip()) > 0

    with open(response_path, "r", encoding="utf-8") as f:
        assert len(f.read().strip()) > 0

    with open(response_tts_path, "r", encoding="utf-8") as f:
        assert len(f.read().strip()) > 0
