"""Embeddings model interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class EmbeddingModel:
    """Computes embeddings for text inputs."""

    model_name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return embeddings for texts (placeholder)."""
        _ = texts
        return []
