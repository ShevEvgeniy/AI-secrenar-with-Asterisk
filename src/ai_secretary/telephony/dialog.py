"""Dialog flow helpers for multi-turn telephony MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..llm.parsers import normalize_ru_phone
from .call_session import DialogStage


PROMPTS: dict[DialogStage, str] = {
    DialogStage.ISSUE: "Здравствуйте! Я Анна, виртуальный секретарь. По какому вопросу вы обращаетесь?",
    DialogStage.NAME: "Как я могу к вам обращаться?",
    DialogStage.CITY: "Из какого города или региона вы звоните?",
    DialogStage.PHONE: "Подскажите номер телефона для связи.",
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
    _ = profile
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
    return text.strip() or None


def _extract_phone(text: str) -> str | None:
    m = re.search(r"(\+?\d[\d\s()\-]{8,}\d)", text)
    if not m:
        return None
    normalized = normalize_ru_phone(m.group(1))
    digits = normalized.get("digits")
    if not digits or len(digits) != 11 or not digits.startswith("7"):
        return None
    return digits


def apply_turn(state: DialogStage, profile: dict[str, Any], transcript_text: str) -> tuple[DialogStage, dict[str, Any]]:
    """Update profile and next state from one transcript."""
    updated = dict(profile)
    text = transcript_text.strip()

    if state == DialogStage.ISSUE and text:
        updated["issue"] = text
        return DialogStage.NAME, updated
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
            updated["phone_digits"] = phone
            return DialogStage.DONE, updated
        return DialogStage.PHONE, updated
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
