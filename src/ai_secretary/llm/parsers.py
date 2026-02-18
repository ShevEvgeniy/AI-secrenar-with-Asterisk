"""Parsers for LLM outputs."""

from __future__ import annotations

import re
from typing import Any


def parse_summary(text: str) -> str:
    """Parse summary output text (placeholder)."""
    return text.strip()


def parse_response(text: str) -> str:
    """Parse response output text (placeholder)."""
    return text.strip()


def normalize_ru_phone(phone_raw: str) -> dict[str, str | None]:
    """Normalize a Russian phone string into digits, e164, and pretty formats."""
    digits = "".join(ch for ch in phone_raw if ch.isdigit())
    if len(digits) == 10 and digits.startswith("9"):
        digits = f"7{digits}"
    elif len(digits) == 11 and digits.startswith("9"):
        digits = f"7{digits[1:]}"
    elif len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"

    e164 = None
    pretty = None
    if len(digits) == 11 and digits.startswith("7"):
        e164 = f"+{digits}"
        pretty = f"+7 {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

    return {"digits": digits, "e164": e164, "pretty": pretty}


def _extract_system_field(text: str, field: str) -> str | None:
    """Extract a field value from UPDATE_PROFILE_FIELD system command."""
    pattern = rf"UPDATE_PROFILE_FIELD:{field}=([^\]]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return match.group(1).strip()


def _extract_inn(text: str) -> tuple[str | None, str | None]:
    """Extract INN digits and optional error message."""
    raw = _extract_system_field(text, "inn")
    if raw is None:
        match = re.search(r"ИНН\s*[:=]?\s*([\d\s-]{10,12})", text, flags=re.IGNORECASE)
        raw = match.group(1) if match else None

    if raw is None:
        return None, None

    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) not in (10, 12):
        return None, f"invalid inn length: {len(digits)}"
    return digits, None


def _extract_phone(text: str) -> str | None:
    """Extract a phone candidate string from text."""
    raw = _extract_system_field(text, "phone")
    if raw is not None:
        return raw
    match = re.search(r"(\+?\d[\d\s()\-]{8,}\d)", text)
    return match.group(1) if match else None


def parse_update_profile_fields(text: str) -> dict[str, Any]:
    """Extract profile fields from text and normalize phone/INN if present."""
    profile: dict[str, Any] = {}

    phone_raw = _extract_phone(text)
    if phone_raw:
        normalized = normalize_ru_phone(phone_raw)
        profile["phone_digits"] = normalized["digits"]
        profile["phone_e164"] = normalized["e164"]
        profile["phone_pretty"] = normalized["pretty"]

    inn_digits, inn_error = _extract_inn(text)
    if inn_digits is not None:
        profile["inn_digits"] = inn_digits
    else:
        profile["inn_digits"] = None
    if inn_error:
        profile["inn_error"] = inn_error

    return profile
