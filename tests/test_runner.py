"""Tests for the pipeline runner."""

import os

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline


def test_run_pipeline_synth_inn_ok() -> None:
    os.environ["DEMO_MODE"] = "synth"
    settings = Settings.from_env()
    result = run_pipeline("synth", settings)
    checks = result["checks"]
    assert checks.get("inn_check_synth") == "OK"
