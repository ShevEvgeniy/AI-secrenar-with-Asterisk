"""Vector search helpers."""

from __future__ import annotations

from typing import List, Tuple

from .embeddings import get_embedder


def search_top_k(query_text: str, chunks: List[str], k: int) -> Tuple[List[str], List[float]]:
    """Return top-k chunk texts and scores for a query."""
    if not chunks:
        return [], []

    embedder = get_embedder()
    query_emb = embedder.embed([query_text])[0]
    chunk_embs = embedder.embed(chunks)

    scores = [float(sum(float(a) * float(b) for a, b in zip(chunk_emb, query_emb))) for chunk_emb in chunk_embs]
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)

    top = indexed[: max(1, min(k, len(chunks)))]
    selected_chunks = [chunks[i] for i, _ in top]
    selected_scores = [float(score) for _, score in top]
    return selected_chunks, selected_scores
