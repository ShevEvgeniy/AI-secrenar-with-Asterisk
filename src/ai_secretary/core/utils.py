"""Small helpers shared across modules."""

from __future__ import annotations

from typing import Iterable


def join_lines(lines: Iterable[str]) -> str:
    """Join lines into a single string with newlines."""
    return "\n".join(lines)
