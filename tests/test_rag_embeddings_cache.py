"""Tests for RAG embeddings model cache."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline
from ai_secretary.rag import embeddings


def test_embeddings_model_loaded_once_across_pipeline_calls(tmp_path: Path, monkeypatch) -> None:
    calls = {"count": 0}

    class FakeSentenceTransformer:
        def encode(self, texts, normalize_embeddings=True):
            _ = normalize_embeddings
            return [[float(len(text)), 1.0, 0.5] for text in texts]

    def fake_ctor(model_name: str):
        _ = model_name
        calls["count"] += 1
        return FakeSentenceTransformer()

    monkeypatch.setattr(embeddings, "_create_sentence_transformer", fake_ctor)
    embeddings._reset_embedder_cache_for_tests()

    settings = replace(Settings.from_env(), storage_dir=tmp_path / "storage")
    input_path = tmp_path / "input.wav"
    input_path.write_bytes(b"fake-wav")

    run_pipeline("real", settings, audio_path_override=input_path)
    run_pipeline("real", settings, audio_path_override=input_path)

    assert calls["count"] == 1

    embeddings._reset_embedder_cache_for_tests()
