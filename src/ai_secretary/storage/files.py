"""File helpers for storage."""

from __future__ import annotations

import json
from pathlib import Path


def save_bytes(path: Path, data: bytes) -> None:
    """Write bytes to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def save_text(path: Path, text: str | None) -> None:
    """Write text to a file using UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "" if text is None else text
    path.write_text(payload, encoding="utf-8", newline="\n")


def save_json(path: Path, payload: object) -> None:
    """Write JSON to a file using UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8", newline="\n")


def read_text(path: Path) -> str:
    """Read text from a file."""
    return path.read_text(encoding="utf-8")
