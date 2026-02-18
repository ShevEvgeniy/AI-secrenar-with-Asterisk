"""Chunking utilities for knowledge base text."""

from __future__ import annotations

from typing import List


def chunk_by_paragraphs(text: str) -> List[str]:
    """Split text by blank lines into paragraphs."""
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if len(chunks) < 1:
        return []
    return chunks
