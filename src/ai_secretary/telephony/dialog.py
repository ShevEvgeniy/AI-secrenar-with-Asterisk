"""Dialog flow helpers for multi-turn telephony MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .call_session import DialogStage

MIN_CITY_LETTERS = 4
PHONE_DIGIT_LENGTHS = {10, 11}
PHONE_RETRY_PROMPTS: dict[str, tuple[str, ...]] = {
    "unclear": (
        "Возможно, я плохо расслышала. Продиктуйте, пожалуйста, номер ещё раз.",
        "Продиктуйте, пожалуйста, ещё раз ваш номер телефона.",
    ),
    "incomplete": (
        "Похоже, номер записался не полностью. Назовите его, пожалуйста, ещё раз.",
        "Не совсем корректно я записала номер. Будьте добры, продиктуйте его ещё раз.",
    ),
    "rejected": (
        "Спасибо, тогда продиктуйте номер ещё раз полностью.",
        "Хорошо, продиктуйте, пожалуйста, номер ещё раз.",
    ),
}

PROMPTS: dict[DialogStage, str] = {
    DialogStage.ISSUE: "Здравствуйте! Я Анна, виртуальный секретарь. По какому вопросу вы обращаетесь?",
    DialogStage.NAME: "Как я могу к вам обращаться?",
    DialogStage.CITY: "Из какого города или региона вы звоните?",
    DialogStage.PHONE: "Подскажите номер телефона для связи.",
    DialogStage.PHONE_CONFIRM: "Правильно ли я записала ваш номер?",
    DialogStage.DONE: "хорошо я соединяю вас с отделом продаж.",
}


@dataclass(frozen=True)
class TurnRecord:
    """One dialog turn for turns.jsonl."""

    state: str
    prompt_text: str
    transcript_text: str
    timestamp: str

    def to_dict(self) -> dict[str, str]:
        return {
            "state": self.state,
            "prompt_text": self.prompt_text,
            "transcript_text": self.transcript_text,
            "timestamp": self.timestamp,
        }


def next_prompt(state: DialogStage, profile: dict[str, Any]) -> str:
    """Return prompt text for current state."""
    if state == DialogStage.PHONE:
        retry_prompt = profile.get("phone_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.PHONE_CONFIRM:
        formatted_phone = profile.get("phone_formatted") or profile.get("phone_digits") or ""
        if formatted_phone:
            return f"Правильно ли я записала ваш номер: {formatted_phone}?"
    return PROMPTS.get(state, PROMPTS[DialogStage.DONE])


def _extract_name(text: str) -> str | None:
    m = re.search(r"(?:меня зовут|это)\s+([А-ЯЁA-Z][а-яёa-z-]+(?:\s+[А-ЯЁA-Z][а-яёa-z-]+)?)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    words = [w.strip(".,!?") for w in text.split() if w.strip(".,!?")]
    if not words:
        return None
    if len(words) >= 2:
        return f"{words[0]} {words[1]}"
    return words[0]


def _extract_city(text: str) -> str | None:
    m = re.search(r"(?:из|с)\s+([А-ЯЁA-Z][а-яёa-z-]+(?:\s+[А-ЯЁA-Z][а-яёa-z-]+)?)", text, flags=re.IGNORECASE)
    if m:
        return m.group(1).strip()
    candidate = text.strip()
    if not candidate or not re.search(r"[А-ЯЁA-Zа-яёa-z]", candidate):
        return None
    letters = re.findall(r"[А-ЯЁA-Zа-яёa-z]", candidate)
    if len(letters) < MIN_CITY_LETTERS:
        return None
    return candidate


def _digits_only_phone(text: str) -> str | None:
    m = re.search(r"(\+?\d[\d\s().\-]{8,}\d)", text)
    if not m:
        return None
    digits = "".join(ch for ch in m.group(1) if ch.isdigit())
    if not digits or len(digits) not in PHONE_DIGIT_LENGTHS:
        return None
    return digits


def _phone_retry_reason(text: str) -> str:
    digits = "".join(ch for ch in text if ch.isdigit())
    return "incomplete" if digits else "unclear"


def _set_phone_retry_prompt(profile: dict[str, Any], reason: str) -> None:
    prompts = PHONE_RETRY_PROMPTS[reason]
    previous = profile.get("phone_last_retry_prompt")
    prompt = prompts[0]
    if prompt == previous and len(prompts) > 1:
        prompt = prompts[1]
    profile["phone_retry_reason"] = reason
    profile["phone_retry_prompt"] = prompt
    profile["phone_last_retry_prompt"] = prompt


def _clear_phone_retry_prompt(profile: dict[str, Any]) -> None:
    profile.pop("phone_retry_reason", None)
    profile.pop("phone_retry_prompt", None)


def _format_phone_for_confirmation(digits: str) -> str:
    display_digits = digits
    if len(digits) == 10:
        return f"+7 {digits[0:3]} {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    if len(digits) == 11:
        return f"+{digits[0]} {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return display_digits


def _extract_phone(text: str) -> tuple[str, str] | None:
    digits = _digits_only_phone(text)
    if digits is None:
        return None
    return digits, _format_phone_for_confirmation(digits)


def _is_positive_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    return bool(re.search(r"\b(да|верно|правильно|угу|ага|подтверждаю|всё верно|все верно)\b", normalized))


def _is_negative_confirmation(text: str) -> bool:
    normalized = text.strip().lower()
    return bool(re.search(r"\b(нет|не верно|неверно|неправильно|ошибка|ошиблась|другой|заново)\b", normalized))


def apply_turn(state: DialogStage, profile: dict[str, Any], transcript_text: str) -> tuple[DialogStage, dict[str, Any]]:
    """Update profile and next state from one transcript."""
    updated = dict(profile)
    text = transcript_text.strip()

    if state == DialogStage.ISSUE and text:
        updated["issue"] = text
        return DialogStage.NAME, updated
    if state == DialogStage.ISSUE:
        return DialogStage.ISSUE, updated
    if state == DialogStage.NAME:
        name = _extract_name(text)
        if name:
            updated["name"] = name
            return DialogStage.CITY, updated
        return DialogStage.NAME, updated
    if state == DialogStage.CITY:
        city = _extract_city(text)
        if city:
            updated["city"] = city
            return DialogStage.PHONE, updated
        return DialogStage.CITY, updated
    if state == DialogStage.PHONE:
        phone = _extract_phone(text)
        if phone:
            digits, formatted = phone
            updated["phone_digits"] = digits
            updated["phone_formatted"] = formatted
            updated["phone_confirmed"] = False
            _clear_phone_retry_prompt(updated)
            return DialogStage.PHONE_CONFIRM, updated
        _set_phone_retry_prompt(updated, _phone_retry_reason(text))
        return DialogStage.PHONE, updated
    if state == DialogStage.PHONE_CONFIRM:
        phone = _extract_phone(text)
        if phone:
            digits, formatted = phone
            updated["phone_digits"] = digits
            updated["phone_formatted"] = formatted
            updated["phone_confirmed"] = False
            _clear_phone_retry_prompt(updated)
            return DialogStage.PHONE_CONFIRM, updated
        if _is_negative_confirmation(text):
            updated["phone_confirmed"] = False
            _set_phone_retry_prompt(updated, "rejected")
            return DialogStage.PHONE, updated
        if _is_positive_confirmation(text) and updated.get("phone_digits"):
            updated["phone_confirmed"] = True
            return DialogStage.DONE, updated
        return DialogStage.PHONE_CONFIRM, updated
    return DialogStage.DONE, updated


def build_turn_record(state: DialogStage, prompt_text: str, transcript_text: str) -> TurnRecord:
    return TurnRecord(
        state=state.value,
        prompt_text=prompt_text,
        transcript_text=transcript_text,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def should_stop_dialog(state: DialogStage, turns_done: int, max_turns: int) -> bool:
    return state == DialogStage.DONE or turns_done >= max_turns
