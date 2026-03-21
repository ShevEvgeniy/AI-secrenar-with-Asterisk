"""Embeddings model caching and warmup helpers."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any, Sequence


DEFAULT_EMBEDDINGS_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_cached_embedder: "EmbeddingModel | None" = None
_cached_model_name: str | None = None
_init_lock = Lock()


@dataclass
class EmbeddingModel:
    """Computes embeddings for text inputs."""

    model: Any

    def embed(self, texts: Sequence[str]) -> Any:
        """Return embeddings for texts."""
        return self.model.encode(texts, normalize_embeddings=True)


def _create_sentence_transformer(model_name: str) -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def get_embedder(model_name: str = DEFAULT_EMBEDDINGS_MODEL) -> EmbeddingModel:
    """Return process-wide cached embedder."""
    global _cached_embedder
    global _cached_model_name

    if _cached_embedder is not None and _cached_model_name == model_name:
        return _cached_embedder

    with _init_lock:
        if _cached_embedder is not None and _cached_model_name == model_name:
            return _cached_embedder
        model = _create_sentence_transformer(model_name)
        _cached_embedder = EmbeddingModel(model=model)
        _cached_model_name = model_name
        return _cached_embedder


def warmup_embeddings(model_name: str = DEFAULT_EMBEDDINGS_MODEL) -> None:
    """Pre-load model and run one dummy embedding pass."""
    embedder = get_embedder(model_name=model_name)
    _ = embedder.embed(["warmup"])


def _reset_embedder_cache_for_tests() -> None:
    """Reset singleton cache for tests."""
    global _cached_embedder
    global _cached_model_name
    with _init_lock:
        _cached_embedder = None
        _cached_model_name = None
