"""Vector search helpers."""

from __future__ import annotations

from typing import List, Tuple


_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def search_top_k(query_text: str, chunks: List[str], k: int) -> Tuple[List[str], List[float]]:
    """Return top-k chunk texts and scores for a query."""
    if not chunks:
        return [], []

    model = _get_model()
    query_emb = model.encode([query_text], normalize_embeddings=True)
    chunk_embs = model.encode(chunks, normalize_embeddings=True)

    scores = (chunk_embs @ query_emb[0]).tolist()
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: x[1], reverse=True)

    top = indexed[: max(1, min(k, len(chunks)))]
    selected_chunks = [chunks[i] for i, _ in top]
    selected_scores = [float(score) for _, score in top]
    return selected_chunks, selected_scores
