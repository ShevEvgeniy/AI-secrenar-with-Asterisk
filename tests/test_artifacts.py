"""Tests for artifact saving."""

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline


def test_artifacts_non_empty() -> None:
    settings = Settings.from_env()
    result = run_pipeline("synth", settings)
    summary_path = result["paths"]["summary"]
    response_path = result["paths"]["response"]

    with open(summary_path, "r", encoding="utf-8") as f:
        assert len(f.read().strip()) > 0

    with open(response_path, "r", encoding="utf-8") as f:
        assert len(f.read().strip()) > 0
