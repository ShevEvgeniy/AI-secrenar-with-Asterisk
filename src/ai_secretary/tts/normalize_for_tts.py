"""Text normalization for TTS."""

from __future__ import annotations

import os
import re
import threading


_STRESS_DICT_CACHE: dict[str, str] | None = None
_STRESS_DICT_PATH_CACHE: str | None = None
_STRESS_LOCK = threading.Lock()


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


def _load_stress_dict(path: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not path:
        return mapping
    if not os.path.exists(path):
        return mapping

    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key_raw, value_raw = stripped.split("=", 1)
            key = key_raw.strip().lower()
            value = value_raw.strip()
            if key and value:
                mapping[key] = value
    return mapping


def _get_stress_dict() -> dict[str, str]:
    global _STRESS_DICT_CACHE
    global _STRESS_DICT_PATH_CACHE

    path = os.getenv("TTS_STRESS_DICT_PATH", "").strip()
    if _STRESS_DICT_CACHE is not None and _STRESS_DICT_PATH_CACHE == path:
        return _STRESS_DICT_CACHE

    with _STRESS_LOCK:
        if _STRESS_DICT_CACHE is not None and _STRESS_DICT_PATH_CACHE == path:
            return _STRESS_DICT_CACHE
        _STRESS_DICT_CACHE = _load_stress_dict(path)
        _STRESS_DICT_PATH_CACHE = path
        return _STRESS_DICT_CACHE


def apply_stress_overrides(text: str) -> str:
    """Apply case-insensitive whole-word stress replacements."""
    mapping = _get_stress_dict()
    if not mapping:
        return text

    result = text
    for word, stressed in mapping.items():
        pattern = re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)
        result = pattern.sub(stressed, result)
    return result


def _reset_stress_dict_cache_for_tests() -> None:
    global _STRESS_DICT_CACHE
    global _STRESS_DICT_PATH_CACHE
    with _STRESS_LOCK:
        _STRESS_DICT_CACHE = None
        _STRESS_DICT_PATH_CACHE = None
