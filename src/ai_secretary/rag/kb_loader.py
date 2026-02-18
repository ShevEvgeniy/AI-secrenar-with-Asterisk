"""Knowledge base loader utilities."""

from __future__ import annotations

from pathlib import Path


def load_kb_text(path: Path) -> str:
    """Load knowledge base text from a file (utf-8)."""
    return path.read_text(encoding="utf-8")
