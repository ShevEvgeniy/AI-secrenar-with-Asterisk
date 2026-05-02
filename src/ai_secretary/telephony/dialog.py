"""Dialog flow helpers for multi-turn telephony MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .call_session import DialogStage

MIN_CITY_LETTERS = 4
PHONE_DIGIT_LENGTHS = {10, 11}
NAME_JUNK_TOKENS = {"you", "yeah", "yes", "yep", "yup", "no", "ok", "okay", "test", "hello", "hi"}
NAME_MAX_RETRIES = 3
NAME_META_REPAIR_PATTERNS = (
    r"я уже сказал",
    r"я уже сказала",
    r"вы не расслышали",
    r"не расслышали",
    r"еще раз\??",
    r"ещё раз\??",
)
NAME_RETRY_PROMPTS: dict[str, tuple[str, ...]] = {
    "unclear": (
        "Извините, я не расслышала имя. Как я могу к вам обращаться?",
        "Повторите, пожалуйста, как к вам обращаться.",
    ),
    "junk": (
        "Не совсем расслышала имя. Представьтесь, пожалуйста, ещё раз.",
        "Подскажите, пожалуйста, ваше имя.",
    ),
    "meta_repair": (
        "Да, возможно, я плохо расслышала. Повторите, пожалуйста, как к вам обращаться.",
        "Хорошо, давайте уточним имя. Как я могу к вам обращаться?",
    ),
}
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
    "meta_repair": (
        "Да, возможно, я плохо расслышала. Продиктуйте, пожалуйста, номер ещё раз полностью.",
        "Похоже, я записала номер не совсем корректно. Назовите его ещё раз, пожалуйста.",
        "Хорошо, давайте уточним номер. Продиктуйте его ещё раз полностью.",
    ),
}
RU_DIGIT_WORDS = {
    "0": "ноль",
    "1": "один",
    "2": "два",
    "3": "три",
    "4": "четыре",
    "5": "пять",
    "6": "шесть",
    "7": "семь",
    "8": "восемь",
    "9": "девять",
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
    if state == DialogStage.NAME:
        retry_prompt = profile.get("name_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.PHONE:
        retry_prompt = profile.get("phone_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.PHONE_CONFIRM:
        phone_text = phone_confirm_prompt_text(profile)
        if phone_text:
            return phone_text
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


def _is_name_confident(name: str, source_text: str) -> bool:
    cleaned = name.strip(" .,!?:;\"'")
    letters = re.findall(r"[А-ЯЁA-Zа-яёa-z]", cleaned)
    if len(letters) < 2 or len(letters) > 40:
        return False
    lowered = cleaned.lower()
    if lowered in NAME_JUNK_TOKENS or any(ch.isdigit() for ch in cleaned):
        return False
    if re.search(r"[^А-ЯЁA-Zа-яёa-z\-\s]", cleaned):
        return False
    if re.search(r"[А-ЯЁа-яё]", source_text):
        return True
    if " " not in cleaned and len(letters) < 4:
        return False
    return bool(re.match(r"^[A-Z][a-z-]+(?:\s+[A-Z][a-z-]+)?$", cleaned))


def _name_retry_reason(text: str, name: str | None) -> str:
    if _is_name_meta_repair(text):
        return "meta_repair"
    if not text or not name:
        return "unclear"
    return "junk"


def _set_name_retry_prompt(profile: dict[str, Any], reason: str) -> None:
    prompts = NAME_RETRY_PROMPTS[reason]
    previous = profile.get("name_last_retry_prompt")
    prompt = prompts[0]
    if prompt == previous and len(prompts) > 1:
        prompt = prompts[1]
    retries = int(profile.get("name_retry_count") or 0) + 1
    profile["name_retry_count"] = retries
    profile["name_retry_reason"] = reason
    profile["name_retry_prompt"] = prompt
    profile["name_last_retry_prompt"] = prompt


def _clear_name_retry_prompt(profile: dict[str, Any]) -> None:
    profile.pop("name_retry_reason", None)
    profile.pop("name_retry_prompt", None)


def _is_name_retry_exhausted(profile: dict[str, Any]) -> bool:
    return int(profile.get("name_retry_count") or 0) >= NAME_MAX_RETRIES


def _is_name_meta_repair(text: str) -> bool:
    normalized = text.strip().lower()
    return any(re.search(pattern, normalized) for pattern in NAME_META_REPAIR_PATTERNS)


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


def _valid_phone_digits(digits: str) -> str | None:
    if digits and len(digits) in PHONE_DIGIT_LENGTHS:
        return digits
    return None


def _compact_grouped_phone_variant(candidate: str) -> str | None:
    digit_groups = ["".join(ch for ch in part if ch.isdigit()) for part in re.split(r"[,;]", candidate)]
    digit_groups = [group for group in digit_groups if group]
    if len(digit_groups) < 2:
        return None

    raw_digits = "".join(digit_groups)
    if len(raw_digits) != 11 or not raw_digits.startswith("9"):
        return None

    for idx in range(len(digit_groups) - 1, 0, -1):
        group = digit_groups[idx]
        if len(group) > 1 and group.startswith("0"):
            compacted_groups = list(digit_groups)
            compacted_groups[idx] = group[1:]
            compacted = "".join(compacted_groups)
            if len(compacted) == 10:
                return compacted
    return None


def _digits_only_phone(text: str) -> str | None:
    m = re.search(r"(\+?\d[\d\s().,\-;]{8,}\d)", text)
    if not m:
        return None
    candidate = m.group(1)
    compacted = _compact_grouped_phone_variant(candidate)
    if compacted:
        return compacted
    digits = "".join(ch for ch in candidate if ch.isdigit())
    return _valid_phone_digits(digits)


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


def phone_digits_to_spoken_ru(digits: str) -> str:
    """Return TTS-safe Russian digit words for a phone number."""
    return ", ".join(RU_DIGIT_WORDS[digit] for digit in digits if digit in RU_DIGIT_WORDS)


def phone_confirm_prompt_text(profile: dict[str, Any]) -> str:
    digits = str(profile.get("phone_digits") or "")
    if digits:
        spoken_phone = profile.get("phone_spoken") or phone_digits_to_spoken_ru(digits)
        if spoken_phone:
            return f"Правильно ли я записала ваш номер: {spoken_phone}?"
    formatted_phone = profile.get("phone_formatted") or ""
    if formatted_phone:
        return f"Правильно ли я записала ваш номер: {formatted_phone}?"
    return ""


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


def _is_meta_repair(text: str) -> bool:
    normalized = text.strip().lower()
    patterns = (
        r"я уже сказал",
        r"вы ничего не произнесли",
        r"что-то не так",
        r"что то не так",
        r"вы не так записали",
        r"не так записали",
        r"плохо расслыш",
        r"уже продиктовал",
        r"уже продиктовала",
        r"уже назвал",
        r"уже назвала",
        r"номер для связи",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


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
        if _is_name_meta_repair(text):
            _set_name_retry_prompt(updated, "meta_repair")
            return DialogStage.NAME, updated
        name = _extract_name(text)
        if name and _is_name_confident(name, text):
            _clear_name_retry_prompt(updated)
            updated["name"] = name
            return DialogStage.CITY, updated
        _set_name_retry_prompt(updated, _name_retry_reason(text, name))
        if _is_name_retry_exhausted(updated):
            updated["name"] = "клиент"
            updated["name_unavailable"] = True
            _clear_name_retry_prompt(updated)
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
            updated["phone_spoken"] = phone_digits_to_spoken_ru(digits)
            updated["phone_confirmed"] = False
            _clear_phone_retry_prompt(updated)
            return DialogStage.PHONE_CONFIRM, updated
        if _is_meta_repair(text):
            _set_phone_retry_prompt(updated, "meta_repair")
            return DialogStage.PHONE, updated
        _set_phone_retry_prompt(updated, _phone_retry_reason(text))
        return DialogStage.PHONE, updated
    if state == DialogStage.PHONE_CONFIRM:
        phone = _extract_phone(text)
        if phone:
            digits, formatted = phone
            updated["phone_digits"] = digits
            updated["phone_formatted"] = formatted
            updated["phone_spoken"] = phone_digits_to_spoken_ru(digits)
            updated["phone_confirmed"] = False
            _clear_phone_retry_prompt(updated)
            return DialogStage.PHONE_CONFIRM, updated
        if _is_meta_repair(text):
            updated["phone_confirmed"] = False
            _set_phone_retry_prompt(updated, "meta_repair")
            return DialogStage.PHONE, updated
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
