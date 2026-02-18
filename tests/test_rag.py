"""Tests for RAG."""

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline


def test_rag_non_empty() -> None:
    settings = Settings.from_env()
    result = run_pipeline("synth", settings)
    assert len(result["selected_chunks"]) >= 1
