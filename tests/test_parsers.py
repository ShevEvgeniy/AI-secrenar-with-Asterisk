"""Tests for LLM parsers."""

from ai_secretary.llm.parsers import (
    normalize_ru_phone,
    parse_response,
    parse_summary,
    parse_update_profile_fields,
)


def test_parse_summary_strips() -> None:
    assert parse_summary("  hi ") == "hi"


def test_parse_response_strips() -> None:
    assert parse_response("  ok ") == "ok"


def test_normalize_ru_phone_from_10_digits() -> None:
    normalized = normalize_ru_phone("9036784653")
    assert normalized["digits"] == "79036784653"


def test_normalize_ru_phone_from_8_prefix() -> None:
    normalized = normalize_ru_phone("8 903 678 46 53")
    assert normalized["digits"] == "79036784653"


def test_normalize_ru_phone_from_plus7() -> None:
    normalized = normalize_ru_phone("+7 903 678 46 53")
    assert normalized["digits"] == "79036784653"


def test_parse_update_profile_fields_extracts_inn() -> None:
    text = "[SYSTEM_COMMAND]UPDATE_PROFILE_FIELD:inn=7701234567[/SYSTEM_COMMAND]"
    profile = parse_update_profile_fields(text)
    assert profile["inn_digits"] == "7701234567"
