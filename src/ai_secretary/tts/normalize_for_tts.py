"""Text normalization for TTS."""

from __future__ import annotations

import re


def inn_digits_to_spaced(inn_digits: str) -> str:
    """Convert INN digits to a spaced string for TTS."""
    return " ".join(list(inn_digits))


def normalize_text(text: str, inn_digits: str | None = None) -> str:
    """Normalize text before TTS synthesis."""
    normalized = " ".join(text.split())

    if inn_digits:
        spaced = inn_digits_to_spaced(inn_digits)
        if re.search(r"ИНН\s*[:=]?\s*\d+", normalized, flags=re.IGNORECASE):
            normalized = re.sub(
                r"(ИНН\s*[:=]?\s*)(\d+)",
                rf"\1{spaced}",
                normalized,
                flags=re.IGNORECASE,
            )
        else:
            normalized = f"{normalized} ИНН: {spaced}"

    return normalized
