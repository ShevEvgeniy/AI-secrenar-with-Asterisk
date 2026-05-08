"""Deterministic Russian city/region validation for CITY slot capture."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CityValidationResult:
    raw_text: str
    normalized_text: str
    accepted: bool
    canonical: str | None
    reason: str
    lexicon_matched: bool = False
    alias_matched: bool = False
    location_detail: str | None = None


_CITY_ALIASES: dict[str, str] = {
    "питер": "Санкт-Петербург",
    "спб": "Санкт-Петербург",
    "санкт петербург": "Санкт-Петербург",
}

_CITY_CANONICAL_NAMES = (
    # Federal cities and common large cities.
    "Москва",
    "Санкт-Петербург",
    "Севастополь",
    "Самара",
    "Нижний Тагил",
    "Нижний Новгород",
    "Ростов-на-Дону",
    "Екатеринбург",
    "Краснодар",
    "Казань",
    "Новосибирск",
    "Омск",
    "Челябинск",
    "Уфа",
    "Пермь",
    "Волгоград",
    "Воронеж",
    "Красноярск",
    "Саратов",
    "Тюмень",
    "Тольятти",
    "Ижевск",
    "Барнаул",
    "Ульяновск",
    "Иркутск",
    "Хабаровск",
    "Ярославль",
    "Владивосток",
    "Махачкала",
    "Томск",
    "Оренбург",
    "Кемерово",
    "Новокузнецк",
    "Рязань",
    "Астрахань",
    "Пенза",
    "Липецк",
    "Киров",
    "Чебоксары",
    "Калининград",
    "Тула",
    "Курск",
    "Ставрополь",
    "Улан-Удэ",
    "Тверь",
    "Магнитогорск",
    "Иваново",
    "Брянск",
    "Белгород",
    "Сочи",
    "Сургут",
    "Владимир",
    "Архангельск",
    "Чита",
    "Калуга",
    "Смоленск",
    "Волжский",
    "Якутск",
    "Саранск",
    "Череповец",
    "Курган",
    "Вологда",
    "Орёл",
    "Владикавказ",
    "Грозный",
    "Мурманск",
    "Тамбов",
    "Петрозаводск",
    "Нальчик",
    "Кострома",
    "Новороссийск",
    "Йошкар-Ола",
    "Таганрог",
    "Комсомольск-на-Амуре",
    "Сыктывкар",
    "Нижневартовск",
    "Шахты",
    "Дзержинск",
    "Орск",
    "Братск",
    "Ангарск",
    "Энгельс",
    "Благовещенск",
    "Старый Оскол",
    "Великий Новгород",
    "Псков",
    "Бийск",
    "Прокопьевск",
    "Южно-Сахалинск",
    "Балаково",
    "Рыбинск",
    "Армавир",
    "Северодвинск",
    "Абакан",
    "Петропавловск-Камчатский",
    "Норильск",
    "Сызрань",
    "Волгодонск",
    "Уссурийск",
    "Каменск-Уральский",
    "Новочеркасск",
    "Златоуст",
    "Электросталь",
    "Альметьевск",
    "Миасс",
    "Керчь",
    "Рубцовск",
    "Коломна",
    "Майкоп",
    "Пятигорск",
    "Одинцово",
    "Ковров",
    "Хасавюрт",
    "Кисловодск",
    "Серпухов",
    "Новомосковск",
    "Нефтеюганск",
    "Димитровград",
    "Нефтекамск",
    "Черкесск",
    "Орехово-Зуево",
    "Дербент",
    "Камышин",
    "Невинномысск",
    "Красногорск",
    "Муром",
    "Батайск",
    "Новочебоксарск",
    "Сергиев Посад",
    "Ноябрьск",
    "Щёлково",
    "Кызыл",
    "Октябрьский",
    "Ачинск",
    "Северск",
    "Новокуйбышевск",
    "Елец",
    "Арзамас",
    "Обнинск",
    "Каспийск",
    "Элиста",
    "Пушкино",
    "Жуковский",
    "Междуреченск",
    "Сарапул",
    "Ессентуки",
    "Воткинск",
    "Ногинск",
    "Тобольск",
    "Ухта",
    "Серов",
    "Бердск",
    "Великие Луки",
    "Мичуринск",
    "Киселёвск",
    "Новотроицк",
    "Зеленодольск",
    "Соликамск",
    "Раменское",
    "Домодедово",
    "Магадан",
    "Глазов",
    "Канск",
    "Железногорск",
    "Назрань",
    "Гатчина",
    "Саров",
    "Новый Уренгой",
    "Воскресенск",
    "Долгопрудный",
    "Бугульма",
    "Кузнецк",
    "Губкин",
    "Кинешма",
    "Ейск",
    "Реутов",
    "Усть-Илимск",
    "Железногорск-Илимский",
    # Federal subjects and common regional answers.
    "Московская область",
    "Ленинградская область",
    "Краснодарский край",
    "Республика Татарстан",
    "Республика Башкортостан",
    "Алтайский край",
    "Забайкальский край",
    "Камчатский край",
    "Красноярский край",
    "Пермский край",
    "Приморский край",
    "Ставропольский край",
    "Хабаровский край",
    "Амурская область",
    "Архангельская область",
    "Астраханская область",
    "Белгородская область",
    "Брянская область",
    "Владимирская область",
    "Волгоградская область",
    "Вологодская область",
    "Воронежская область",
    "Ивановская область",
    "Иркутская область",
    "Калининградская область",
    "Калужская область",
    "Кемеровская область",
    "Кировская область",
    "Костромская область",
    "Курганская область",
    "Курская область",
    "Липецкая область",
    "Магаданская область",
    "Мурманская область",
    "Нижегородская область",
    "Новгородская область",
    "Новосибирская область",
    "Омская область",
    "Оренбургская область",
    "Орловская область",
    "Пензенская область",
    "Псковская область",
    "Ростовская область",
    "Рязанская область",
    "Самарская область",
    "Саратовская область",
    "Сахалинская область",
    "Свердловская область",
    "Смоленская область",
    "Тамбовская область",
    "Тверская область",
    "Томская область",
    "Тульская область",
    "Тюменская область",
    "Ульяновская область",
    "Челябинская область",
    "Ярославская область",
    "Республика Адыгея",
    "Республика Алтай",
    "Республика Бурятия",
    "Республика Дагестан",
    "Республика Ингушетия",
    "Кабардино-Балкарская Республика",
    "Республика Калмыкия",
    "Карачаево-Черкесская Республика",
    "Республика Карелия",
    "Республика Коми",
    "Республика Крым",
    "Республика Марий Эл",
    "Республика Мордовия",
    "Республика Саха",
    "Республика Северная Осетия",
    "Республика Тыва",
    "Удмуртская Республика",
    "Республика Хакасия",
    "Чеченская Республика",
    "Чувашская Республика",
    "Еврейская автономная область",
    "Ненецкий автономный округ",
    "Ханты-Мансийский автономный округ",
    "Ямало-Ненецкий автономный округ",
    "Чукотский автономный округ",
)

_AMBIGUOUS_SHORT_FRAGMENTS = {
    "нижний",
    "ростов",
}

_FILLER_TOKENS = {
    "a",
    "ok",
    "okay",
    "yes",
    "no",
    "you",
    "ну",
    "да",
    "нет",
    "а",
    "э",
    "ээ",
}

_LOCATION_DETAIL_PATTERNS = (
    r"\bрайон\b",
    r"\bгородской округ\b",
    r"\bокруг\b",
    r"\bгород\b",
    r"\bг\.\b",
    r"\bдеревня\b",
    r"\bд\.\b",
    r"\bсело\b",
    r"\bс\.\b",
    r"\bпоселок\b",
    r"\bпосёлок\b",
    r"\bп\.\b",
    r"\bрабочий поселок\b",
    r"\bрабочий посёлок\b",
    r"\bрп\b",
    r"\bстаница\b",
    r"\bхутор\b",
    r"\bаул\b",
    r"\bулица\b",
    r"\bул\.\b",
    r"\bпроспект\b",
    r"\bпр-т\b",
    r"\bпереулок\b",
    r"\bдом\b",
    r"\bкорпус\b",
    r"\bстроение\b",
    r"\bофис\b",
)


def normalize_city_text(text: str) -> str:
    """Normalize transcript text for exact deterministic city lookup."""
    normalized = text.casefold().replace("ё", "е")
    normalized = normalized.strip()
    normalized = re.sub(r"^[\s\"'«».,!?;:]+|[\s\"'«».,!?;:]+$", "", normalized)
    normalized = re.sub(r"\b(?:город|г\.|из|с|со|я\s+из|мы\s+из)\b", " ", normalized)
    normalized = normalized.replace("–", "-").replace("—", "-").replace("‑", "-")
    normalized = re.sub(r"\s*-\s*", "-", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip(" .,!?:;\"'«»")


def _key(text: str) -> str:
    return normalize_city_text(text)


_CITY_LEXICON: dict[str, str] = {_key(name): name for name in _CITY_CANONICAL_NAMES}
_ANCHOR_KEYS_BY_LENGTH = sorted(_CITY_LEXICON, key=len, reverse=True)


def _contains_anchor(text: str) -> bool:
    return _find_anchor(text) is not None


def _find_anchor(text: str) -> tuple[str, str] | None:
    for key in _ANCHOR_KEYS_BY_LENGTH:
        if re.search(rf"(?<![а-я]){re.escape(key)}(?![а-я])", text):
            return key, _CITY_LEXICON[key]
    return None


def _looks_like_location_detail(detail: str) -> bool:
    if not detail or re.search(r"[a-z]", detail):
        return False
    if not re.search(r"[а-я]", detail):
        return False
    if any(re.search(pattern, detail) for pattern in _LOCATION_DETAIL_PATTERNS):
        return True
    return _contains_anchor(detail)


def _detail_from_raw(raw: str, canonical: str) -> str:
    raw = raw.strip(" .,!?:;\"'«»")
    if "," in raw:
        return raw.split(",", 1)[1].strip(" .,!?:;\"'«»")
    pattern = r"\s+".join(re.escape(part) for part in canonical.split())
    match = re.match(rf"^\s*(?:из|с|со)?\s*{pattern}\s+(.+)$", raw, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip(" .,!?:;\"'«»")
    return ""


def _validate_compound_city(raw: str, normalized: str) -> CityValidationResult | None:
    parts = [part.strip() for part in re.split(r"[,;]+", normalized) if part.strip()]
    if parts:
        first = parts[0]
        canonical = _CITY_LEXICON.get(first) or _CITY_ALIASES.get(first)
        if canonical and len(parts) > 1:
            detail = " ".join(parts[1:])
            if _looks_like_location_detail(detail):
                return CityValidationResult(
                    raw,
                    normalized,
                    True,
                    canonical,
                    "region_with_location_detail",
                    lexicon_matched=first in _CITY_LEXICON,
                    alias_matched=first in _CITY_ALIASES,
                    location_detail=_detail_from_raw(raw, canonical),
                )

    for key in _ANCHOR_KEYS_BY_LENGTH:
        if normalized == key:
            continue
        if normalized.startswith(key + " "):
            detail = normalized[len(key) :].strip()
            if _looks_like_location_detail(detail):
                return CityValidationResult(
                    raw,
                    normalized,
                    True,
                    _CITY_LEXICON[key],
                    "region_with_location_detail",
                    lexicon_matched=True,
                    location_detail=_detail_from_raw(raw, _CITY_LEXICON[key]),
                )

    anchor = _find_anchor(normalized)
    if anchor:
        key, canonical = anchor
        detail = normalized.replace(key, " ", 1).strip()
        if _looks_like_location_detail(detail):
            return CityValidationResult(
                raw,
                normalized,
                True,
                canonical,
                "city_with_location_detail",
                lexicon_matched=True,
                location_detail=_detail_from_raw(raw, canonical),
            )
    return None


def validate_city_transcript(text: str) -> CityValidationResult:
    raw = text or ""
    normalized = normalize_city_text(raw)
    if not normalized:
        return CityValidationResult(raw, normalized, False, None, "empty_transcript")
    if normalized in _FILLER_TOKENS:
        return CityValidationResult(raw, normalized, False, None, "filler")
    if re.search(r"[a-z]", normalized) and not re.search(r"[а-я]", normalized):
        return CityValidationResult(raw, normalized, False, None, "latin_only")
    if normalized in _AMBIGUOUS_SHORT_FRAGMENTS:
        return CityValidationResult(raw, normalized, False, None, "ambiguous_fragment")
    alias = _CITY_ALIASES.get(normalized)
    if alias:
        return CityValidationResult(raw, normalized, True, alias, "alias_match", alias_matched=True)
    if len(re.findall(r"[а-я]", normalized)) < 4:
        return CityValidationResult(raw, normalized, False, None, "city_transcript_not_plausible")
    canonical = _CITY_LEXICON.get(normalized)
    if canonical:
        return CityValidationResult(raw, normalized, True, canonical, "lexicon_match", lexicon_matched=True)
    compound = _validate_compound_city(raw, normalized)
    if compound:
        return compound
    return CityValidationResult(raw, normalized, False, None, "invalid_city_transcript")
