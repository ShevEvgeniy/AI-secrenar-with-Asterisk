"""Path utilities for storage."""

from __future__ import annotations

from pathlib import Path


def ensure_dirs(path: Path) -> None:
    """Create directory if missing."""
    path.mkdir(parents=True, exist_ok=True)
