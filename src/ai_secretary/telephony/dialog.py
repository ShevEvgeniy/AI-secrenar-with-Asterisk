"""Dialog flow helpers for multi-turn telephony MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .call_session import DialogStage
from .city_lexicon import validate_city_transcript
from .routing import ALLOWED_DEPARTMENTS, classify_department_intent

PHONE_DIGIT_LENGTHS = {10, 11}
ISSUE_MAX_RETRIES = 2
INTENT_CLARIFY_MAX_RETRIES = 2
REQUIRED_STAGE_MAX_RETRIES = 3
PHONE_CONFIRM_MAX_RETRIES = 2
PHONE_CONFIRM_FAILURE_CYCLE_LIMIT = 2
PHONE_CONFIRM_SHORT_RETRY_PROMPT = "Скажите, пожалуйста, верно?"
CITY_RETRY_PROMPTS: dict[str, tuple[str, ...]] = {
    "invalid_city_transcript": (
        "Не расслышала город или регион. Повторите, пожалуйста, название города или региона.",
        "Назовите, пожалуйста, город или регион ещё раз.",
    ),
    "empty_transcript": (
        "Извините, я не услышала город. Из какого города или региона вы звоните?",
        "Повторите, пожалуйста, город или регион.",
    ),
}
NAME_JUNK_TOKENS = {"you", "yeah", "yes", "yep", "yup", "no", "ok", "okay", "test", "hello", "hi"}
NAME_MAX_RETRIES = 3
NAME_LEXICON: dict[str, str] = {
    "александр": "Александр",
    "саша": "Александр",
    "саня": "Александр",
    "александра": "Александра",
    "дмитрий": "Дмитрий",
    "димитрий": "Дмитрий",
    "дима": "Дмитрий",
    "сергей": "Сергей",
    "сережа": "Сергей",
    "серёжа": "Сергей",
    "иван": "Иван",
    "ваня": "Иван",
    "петр": "Пётр",
    "пётр": "Пётр",
    "петя": "Пётр",
    "николай": "Николай",
    "коля": "Николай",
    "михаил": "Михаил",
    "миша": "Михаил",
    "владимир": "Владимир",
    "вова": "Владимир",
    "олег": "Олег",
    "андрей": "Андрей",
    "мария": "Мария",
    "маша": "Мария",
    "екатерина": "Екатерина",
    "катя": "Екатерина",
    "анастасия": "Анастасия",
    "настя": "Анастасия",
    "ольга": "Ольга",
    "оля": "Ольга",
    "татьяна": "Татьяна",
    "таня": "Татьяна",
    "наталья": "Наталья",
    "наташа": "Наталья",
    "светлана": "Светлана",
    "света": "Светлана",
    "елена": "Елена",
    "лена": "Елена",
    "иванович": "Иванович",
    "иваныч": "Иванович",
    "ивановна": "Ивановна",
    "петрович": "Петрович",
    "петровна": "Петровна",
    "сергеевич": "Сергеевич",
    "сергеевна": "Сергеевна",
    "александрович": "Александрович",
    "александровна": "Александровна",
    "николаевич": "Николаевич",
    "николаевна": "Николаевна",
    "владимирович": "Владимирович",
    "владимировна": "Владимировна",
}
NAME_CONVERSATIONAL_PREFIXES = (
    "меня зовут",
    "мое имя",
    "моё имя",
    "это",
    "я",
)
NAME_FILLER_TOKENS = {"ну", "ээ", "э", "здравствуйте", "добрый", "день"}
NAME_STOP_TOKENS = {"спасибо", "слушаю", "говорю", "повторяю", "перезвоните"}
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
    DialogStage.ISSUE: "Здравствуйте. Меня зовут Анна. Я виртуальный секретарь. По какому вопросу вы обращаетесь?",
    DialogStage.INTENT_CLARIFY: "Уточните, пожалуйста, отдел: продажи, бухгалтерия или доставка.",
    DialogStage.NAME: "Назовите, пожалуйста, ваше имя.",
    DialogStage.CITY: "Из какого города или региона вы звоните?",
    DialogStage.PHONE: "Подскажите номер телефона для связи.",
    DialogStage.PHONE_CONFIRM: "Правильно ли я записала ваш номер?",
    DialogStage.SAFE_FINISH: "Спасибо за обращение. Сейчас не удалось надежно записать данные, поэтому я завершу звонок.",
    DialogStage.DONE: "хорошо я соединяю вас с отделом продаж.",
}

EARLY_TRANSFER_PROMPTS: dict[DialogStage, str] = {
    DialogStage.ISSUE: (
        "Хорошо, я могу вас соединить. Но сначала мне нужно записать ваши данные и передать их специалисту. "
        "Назовите, пожалуйста, ваше имя."
    ),
    DialogStage.NAME: (
        "Хорошо, я могу вас соединить. Специалисту нужно знать, как к вам обращаться. "
        "Назовите, пожалуйста, ваше имя."
    ),
    DialogStage.CITY: (
        "Хорошо, я могу вас соединить. Нужен ваш город, чтобы правильный специалист мог ответить. "
        "Из какого города или региона вы звоните?"
    ),
    DialogStage.PHONE: (
        "Хорошо, я могу вас соединить. Нужен контактный телефон, чтобы специалист мог с вами связаться. "
        "Подскажите номер телефона для связи."
    ),
}

CLARIFICATION_PROMPT = PROMPTS[DialogStage.INTENT_CLARIFY]

TRANSFER_REQUEST_PATTERNS = (
    r"\bconnect\b",
    r"\btransfer\b",
    r"\bswitch\s+me\b",
    r"соедин",
    r"переключ",
    r"перевед",
    r"нужен\s+отдел",
    r"нужна\s+бухгалтер",
    r"в\s+отдел\s+",
)


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
    early_prompt = profile.get("early_transfer_prompt")
    if isinstance(early_prompt, str) and early_prompt:
        return early_prompt
    if state == DialogStage.NAME:
        retry_prompt = profile.get("name_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.CITY:
        retry_prompt = profile.get("city_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.PHONE:
        retry_prompt = profile.get("phone_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
    if state == DialogStage.PHONE_CONFIRM:
        retry_prompt = profile.get("phone_confirm_retry_prompt")
        if isinstance(retry_prompt, str) and retry_prompt:
            return retry_prompt
        phone_text = phone_confirm_prompt_text(profile)
        if phone_text:
            return phone_text
    return PROMPTS.get(state, PROMPTS[DialogStage.DONE])


def required_fields_missing(profile: dict[str, Any]) -> list[str]:
    """Return required transfer fields that are not ready yet."""
    missing: list[str] = []
    if not profile.get("name"):
        missing.append("name")
    if not profile.get("city"):
        missing.append("city")
    if not profile.get("phone_digits"):
        missing.append("phone")
    elif profile.get("phone_confirmed") is not True:
        missing.append("phone_confirmed")
    return missing


def retry_limit_for_stage(stage: DialogStage) -> int:
    if stage == DialogStage.ISSUE:
        return ISSUE_MAX_RETRIES
    if stage == DialogStage.INTENT_CLARIFY:
        return INTENT_CLARIFY_MAX_RETRIES
    if stage == DialogStage.PHONE_CONFIRM:
        return PHONE_CONFIRM_MAX_RETRIES
    if stage in {DialogStage.NAME, DialogStage.CITY, DialogStage.PHONE}:
        return REQUIRED_STAGE_MAX_RETRIES
    return 0


def _retry_key(stage: DialogStage) -> str:
    return f"{stage.value.lower()}_retry_count"


def _stage_retry(profile: dict[str, Any], stage: DialogStage, reason: str) -> int:
    retry_count = int(profile.get(_retry_key(stage)) or 0) + 1
    retry_limit = retry_limit_for_stage(stage)
    profile[_retry_key(stage)] = retry_count
    profile["last_retry_stage"] = stage.value
    profile["last_retry_count"] = retry_count
    profile["last_retry_limit"] = retry_limit
    profile["last_retry_reason"] = reason
    return retry_count


def _clear_stage_retry(profile: dict[str, Any], stage: DialogStage) -> None:
    profile.pop(_retry_key(stage), None)


def _clear_phone_policy_retries(profile: dict[str, Any]) -> None:
    _clear_stage_retry(profile, DialogStage.PHONE)
    _clear_stage_retry(profile, DialogStage.PHONE_CONFIRM)


def _mark_phone_confirm_failure(profile: dict[str, Any], reason: str) -> int:
    failure_count = int(profile.get("phone_confirm_failure_count") or 0) + 1
    profile["phone_confirm_failure_count"] = failure_count
    profile["phone_confirm_failure_limit"] = PHONE_CONFIRM_FAILURE_CYCLE_LIMIT
    profile["phone_confirm_failure_reason"] = reason
    return failure_count


def _safe_finish(profile: dict[str, Any], reason: str, stage: DialogStage) -> tuple[DialogStage, dict[str, Any]]:
    profile["safe_finish"] = True
    profile["safe_finish_reason"] = reason
    profile["safe_finish_stage"] = stage.value
    profile["safe_finish_missing_fields"] = required_fields_missing(profile)
    return DialogStage.SAFE_FINISH, profile


def _is_empty_or_timeout(text: str) -> bool:
    return not text.strip()


def _clear_early_transfer_prompt(profile: dict[str, Any]) -> None:
    profile.pop("early_transfer_prompt", None)


def _is_transfer_requested(text: str) -> bool:
    normalized = text.strip().lower()
    if not normalized:
        return False
    if any(re.search(pattern, normalized) for pattern in TRANSFER_REQUEST_PATTERNS):
        return True
    has_department_word = any(
        keyword in normalized
        for keyword in (
            "отдел продаж",
            "продажи",
            "бухгалтер",
            "достав",
            "accounting",
            "delivery",
            "sales",
        )
    )
    return has_department_word and bool(re.search(r"\bneed\b|\bwant\b|нуж|хочу", normalized))


def _store_department_decision(profile: dict[str, Any], text: str, *, clarified: bool) -> bool:
    decision = classify_department_intent(text)
    profile["department_intent"] = decision.intent
    profile["department"] = decision.department
    profile["department_intent_reason"] = decision.reason
    profile["department_intent_scores"] = decision.scores
    if clarified:
        profile["department_clarification_result"] = decision.department
        profile["department_clarification_reason"] = decision.reason
    return decision.intent in ALLOWED_DEPARTMENTS


def _resolve_default_department(profile: dict[str, Any], reason: str) -> None:
    decision = classify_department_intent("")
    profile["department_intent"] = "unclear"
    profile["department"] = decision.department
    profile["department_intent_reason"] = reason
    profile["department_intent_scores"] = decision.scores
    profile["department_clarification_needed"] = False
    profile["department_clarified"] = False
    profile["department_clarification_result"] = decision.department
    profile["department_clarification_reason"] = reason
    profile["department_defaulted"] = True


def _mark_early_transfer_request(
    profile: dict[str, Any],
    stage: DialogStage,
    text: str,
    *,
    prompt_stage: DialogStage | None = None,
) -> None:
    profile["early_transfer_requested"] = True
    profile["early_transfer_requested_stage"] = stage.value
    profile["early_transfer_requested_text"] = text
    profile["early_transfer_missing_fields"] = required_fields_missing(profile)
    if prompt_stage in EARLY_TRANSFER_PROMPTS:
        profile["early_transfer_prompt"] = EARLY_TRANSFER_PROMPTS[prompt_stage]


def _request_department_clarification(profile: dict[str, Any], resume_stage: DialogStage) -> None:
    profile["department_clarification_needed"] = True
    profile["department_clarification_resume_stage"] = resume_stage.value
    profile["department_clarification_prompt"] = CLARIFICATION_PROMPT


def _canonicalize_name_token(token: str) -> str:
    lowered = token.lower()
    canonical = NAME_LEXICON.get(lowered)
    if canonical:
        return canonical
    return "-".join(part[:1].upper() + part[1:].lower() for part in token.split("-") if part)


def _strip_name_conversational_prefixes(text: str) -> str:
    candidate = text.strip(" .,!?:;\"'")
    lowered = candidate.lower()
    for prefix in NAME_CONVERSATIONAL_PREFIXES:
        if lowered == prefix:
            return ""
        if lowered.startswith(prefix + " "):
            return candidate[len(prefix) :].strip()
    return candidate


def normalize_name_candidate(text: str) -> str | None:
    """Return a bounded canonical Russian NAME candidate from post-STT text."""
    candidate = _strip_name_conversational_prefixes(text)
    tokens = re.findall(r"[А-ЯЁа-яёA-Za-z]+(?:-[А-ЯЁа-яёA-Za-z]+)?", candidate)
    normalized_tokens: list[str] = []
    for token in tokens:
        lowered = token.lower()
        if lowered in NAME_FILLER_TOKENS:
            continue
        if lowered in NAME_STOP_TOKENS:
            break
        normalized_tokens.append(_canonicalize_name_token(token))
        if len(normalized_tokens) == 3:
            break
    if not normalized_tokens:
        return None
    return " ".join(normalized_tokens)


def _extract_name(text: str) -> str | None:
    m = re.search(
        r"(?:меня\s+зовут|мо[её]\s+имя|это|я)\s+(.+)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return normalize_name_candidate(m.group(1))
    normalized = normalize_name_candidate(text)
    if normalized:
        words = normalized.split()
    else:
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
    retry_limit = retry_limit_for_stage(DialogStage.NAME)
    profile["name_retry_count"] = retries
    profile["name_retry_reason"] = reason
    profile["name_retry_prompt"] = prompt
    profile["name_last_retry_prompt"] = prompt
    profile["last_retry_stage"] = DialogStage.NAME.value
    profile["last_retry_count"] = retries
    profile["last_retry_limit"] = retry_limit
    profile["last_retry_reason"] = reason


def _clear_name_retry_prompt(profile: dict[str, Any]) -> None:
    profile.pop("name_retry_reason", None)
    profile.pop("name_retry_prompt", None)


def _is_name_retry_exhausted(profile: dict[str, Any]) -> bool:
    return int(profile.get("name_retry_count") or 0) >= NAME_MAX_RETRIES


def _is_name_meta_repair(text: str) -> bool:
    normalized = text.strip().lower()
    return any(re.search(pattern, normalized) for pattern in NAME_META_REPAIR_PATTERNS)


def _set_city_validation(profile: dict[str, Any], text: str) -> str | None:
    result = validate_city_transcript(text)
    profile["city_validation_raw"] = result.raw_text
    profile["city_validation_normalized"] = result.normalized_text
    profile["city_validation_reason"] = result.reason
    profile["city_validation_accepted"] = result.accepted
    profile["city_validation_lexicon_matched"] = result.lexicon_matched
    profile["city_validation_alias_matched"] = result.alias_matched
    if result.canonical:
        profile["city_validation_canonical"] = result.canonical
    else:
        profile.pop("city_validation_canonical", None)
    return result.canonical if result.accepted else None


def _set_city_retry_prompt(profile: dict[str, Any], reason: str) -> None:
    prompt_key = "empty_transcript" if reason == "empty_transcript" else "invalid_city_transcript"
    prompts = CITY_RETRY_PROMPTS[prompt_key]
    previous = profile.get("city_last_retry_prompt")
    prompt = prompts[0]
    if prompt == previous and len(prompts) > 1:
        prompt = prompts[1]
    profile["city_retry_reason"] = reason
    profile["city_retry_prompt"] = prompt
    profile["city_last_retry_prompt"] = prompt


def _clear_city_retry_prompt(profile: dict[str, Any]) -> None:
    profile.pop("city_retry_reason", None)
    profile.pop("city_retry_prompt", None)


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


def _set_phone_confirm_retry_prompt(profile: dict[str, Any], reason: str) -> None:
    profile["phone_confirm_retry_reason"] = reason
    profile["phone_confirm_retry_prompt"] = PHONE_CONFIRM_SHORT_RETRY_PROMPT


def _clear_phone_confirm_retry_prompt(profile: dict[str, Any]) -> None:
    profile.pop("phone_confirm_retry_reason", None)
    profile.pop("phone_confirm_retry_prompt", None)


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
    _clear_early_transfer_prompt(updated)

    if state == DialogStage.ISSUE and text:
        updated["issue"] = text
        transfer_requested = _is_transfer_requested(text)
        clarified = _store_department_decision(updated, text, clarified=False)
        if transfer_requested:
            _mark_early_transfer_request(updated, state, text, prompt_stage=DialogStage.ISSUE if clarified else None)
        if not clarified:
            _request_department_clarification(updated, DialogStage.NAME)
            return DialogStage.INTENT_CLARIFY, updated
        return DialogStage.NAME, updated
    if state == DialogStage.ISSUE:
        retry_count = _stage_retry(updated, state, "empty_transcript")
        if retry_count >= retry_limit_for_stage(state):
            _request_department_clarification(updated, DialogStage.NAME)
            updated["issue_defaulted_to_clarification"] = True
            return DialogStage.INTENT_CLARIFY, updated
        return DialogStage.ISSUE, updated
    if state == DialogStage.INTENT_CLARIFY:
        if _is_empty_or_timeout(text):
            retry_count = _stage_retry(updated, state, "empty_transcript")
            if retry_count >= retry_limit_for_stage(state):
                _resolve_default_department(updated, "default_after_intent_clarify_retries")
                updated.pop("department_clarification_prompt", None)
                resume_stage_name = str(updated.pop("department_clarification_resume_stage", DialogStage.NAME.value))
                resume_stage = DialogStage(resume_stage_name) if resume_stage_name in DialogStage._value2member_map_ else DialogStage.NAME
                return resume_stage, updated
            return DialogStage.INTENT_CLARIFY, updated
        if _store_department_decision(updated, text, clarified=True):
            _clear_stage_retry(updated, state)
            updated["department_clarification_needed"] = False
            updated["department_clarified"] = True
            resume_stage_name = str(updated.get("department_clarification_resume_stage") or DialogStage.NAME.value)
            resume_stage = DialogStage(resume_stage_name) if resume_stage_name in DialogStage._value2member_map_ else DialogStage.NAME
            updated.pop("department_clarification_prompt", None)
            updated.pop("department_clarification_resume_stage", None)
            if updated.get("early_transfer_requested"):
                updated["early_transfer_missing_fields"] = required_fields_missing(updated)
                prompt_stage_name = str(updated.get("early_transfer_requested_stage") or resume_stage.value)
                prompt_stage = (
                    DialogStage(prompt_stage_name)
                    if prompt_stage_name in DialogStage._value2member_map_
                    else resume_stage
                )
                if prompt_stage in EARLY_TRANSFER_PROMPTS:
                    updated["early_transfer_prompt"] = EARLY_TRANSFER_PROMPTS[prompt_stage]
            return resume_stage, updated
        retry_count = _stage_retry(updated, state, "unclear_transcript")
        if retry_count >= retry_limit_for_stage(state):
            _resolve_default_department(updated, "default_after_intent_clarify_retries")
            updated.pop("department_clarification_prompt", None)
            resume_stage_name = str(updated.pop("department_clarification_resume_stage", DialogStage.NAME.value))
            resume_stage = DialogStage(resume_stage_name) if resume_stage_name in DialogStage._value2member_map_ else DialogStage.NAME
            return resume_stage, updated
        updated["department_clarification_needed"] = True
        updated["department_clarification_result"] = "unclear"
        updated["department_clarification_prompt"] = CLARIFICATION_PROMPT
        return DialogStage.INTENT_CLARIFY, updated
    if state == DialogStage.NAME:
        if _is_transfer_requested(text):
            clarified = _store_department_decision(updated, text, clarified=False)
            _mark_early_transfer_request(updated, state, text, prompt_stage=DialogStage.NAME if clarified else None)
            if not clarified:
                _request_department_clarification(updated, DialogStage.NAME)
                return DialogStage.INTENT_CLARIFY, updated
            return DialogStage.NAME, updated
        if _is_name_meta_repair(text):
            _set_name_retry_prompt(updated, "meta_repair")
            return DialogStage.NAME, updated
        name = _extract_name(text)
        if name and _is_name_confident(name, text):
            _clear_name_retry_prompt(updated)
            _clear_stage_retry(updated, state)
            updated["name"] = name
            return DialogStage.CITY, updated
        _set_name_retry_prompt(updated, _name_retry_reason(text, name))
        if _is_name_retry_exhausted(updated):
            _clear_name_retry_prompt(updated)
            return _safe_finish(updated, "name_retry_limit", state)
        return DialogStage.NAME, updated
    if state == DialogStage.CITY:
        if _is_transfer_requested(text):
            clarified = _store_department_decision(updated, text, clarified=False)
            _mark_early_transfer_request(updated, state, text, prompt_stage=DialogStage.CITY if clarified else None)
            if not clarified:
                _request_department_clarification(updated, DialogStage.CITY)
                return DialogStage.INTENT_CLARIFY, updated
            return DialogStage.CITY, updated
        city = _set_city_validation(updated, text)
        if city:
            _clear_stage_retry(updated, state)
            _clear_city_retry_prompt(updated)
            updated.pop("city_retry_reliable_mode", None)
            updated.pop("city_retry_reliable_mode_reason", None)
            updated["city"] = city
            return DialogStage.PHONE, updated
        validation_reason = str(updated.get("city_validation_reason") or "invalid_city_transcript")
        retry_reason = "empty_transcript" if _is_empty_or_timeout(text) else validation_reason
        _set_city_retry_prompt(updated, retry_reason)
        retry_count = _stage_retry(updated, state, retry_reason)
        if retry_count >= retry_limit_for_stage(state):
            _clear_city_retry_prompt(updated)
            return _safe_finish(updated, "city_retry_limit", state)
        return DialogStage.CITY, updated
    if state == DialogStage.PHONE:
        if _is_transfer_requested(text):
            clarified = _store_department_decision(updated, text, clarified=False)
            _mark_early_transfer_request(updated, state, text, prompt_stage=DialogStage.PHONE if clarified else None)
            if not clarified:
                _request_department_clarification(updated, DialogStage.PHONE)
                return DialogStage.INTENT_CLARIFY, updated
            return DialogStage.PHONE, updated
        phone = _extract_phone(text)
        if phone:
            digits, formatted = phone
            updated["phone_digits"] = digits
            updated["phone_formatted"] = formatted
            updated["phone_spoken"] = phone_digits_to_spoken_ru(digits)
            updated["phone_confirmed"] = False
            _clear_phone_retry_prompt(updated)
            _clear_phone_confirm_retry_prompt(updated)
            _clear_phone_policy_retries(updated)
            return DialogStage.PHONE_CONFIRM, updated
        if _is_meta_repair(text):
            _set_phone_retry_prompt(updated, "meta_repair")
            retry_count = _stage_retry(updated, state, "meta_repair")
            if retry_count >= retry_limit_for_stage(state):
                return _safe_finish(updated, "phone_retry_limit", state)
            return DialogStage.PHONE, updated
        _set_phone_retry_prompt(updated, _phone_retry_reason(text))
        retry_count = _stage_retry(updated, state, "empty_transcript" if _is_empty_or_timeout(text) else _phone_retry_reason(text))
        if retry_count >= retry_limit_for_stage(state):
            return _safe_finish(updated, "phone_retry_limit", state)
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
            _clear_stage_retry(updated, state)
            return DialogStage.PHONE_CONFIRM, updated
        if _is_meta_repair(text):
            updated["phone_confirmed"] = False
            _set_phone_retry_prompt(updated, "meta_repair")
            _clear_phone_confirm_retry_prompt(updated)
            if _mark_phone_confirm_failure(updated, "meta_repair") >= PHONE_CONFIRM_FAILURE_CYCLE_LIMIT:
                return _safe_finish(updated, "phone_retry_limit", state)
            return DialogStage.PHONE, updated
        if _is_negative_confirmation(text):
            updated["phone_confirmed"] = False
            _set_phone_retry_prompt(updated, "rejected")
            _clear_phone_confirm_retry_prompt(updated)
            if _mark_phone_confirm_failure(updated, "rejected") >= PHONE_CONFIRM_FAILURE_CYCLE_LIMIT:
                return _safe_finish(updated, "phone_retry_limit", state)
            return DialogStage.PHONE, updated
        if _is_positive_confirmation(text) and updated.get("phone_digits"):
            _clear_stage_retry(updated, state)
            _clear_phone_confirm_retry_prompt(updated)
            updated.pop("phone_confirm_failure_count", None)
            updated.pop("phone_confirm_failure_limit", None)
            updated.pop("phone_confirm_failure_reason", None)
            updated["phone_confirmed"] = True
            return DialogStage.DONE, updated
        retry_count = _stage_retry(updated, state, "empty_transcript" if _is_empty_or_timeout(text) else "unclear_confirmation")
        if retry_count >= retry_limit_for_stage(state):
            updated["phone_confirmed"] = False
            _clear_phone_confirm_retry_prompt(updated)
            _set_phone_retry_prompt(updated, "unclear")
            _clear_stage_retry(updated, state)
            if _mark_phone_confirm_failure(updated, "unclear") >= PHONE_CONFIRM_FAILURE_CYCLE_LIMIT:
                return _safe_finish(updated, "phone_retry_limit", state)
            return DialogStage.PHONE, updated
        if _is_empty_or_timeout(text) and updated.get("phone_digits"):
            _set_phone_confirm_retry_prompt(updated, "empty_transcript")
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
    if state in {DialogStage.DONE, DialogStage.SAFE_FINISH}:
        return True
    if state in {DialogStage.PHONE, DialogStage.PHONE_CONFIRM}:
        return False
    return turns_done >= max_turns
