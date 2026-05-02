"""Bounded department intent routing for post-confirmation transfer."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Literal, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

Department = Literal["sales", "accounting", "delivery"]
Intent = Literal["sales", "accounting", "delivery", "unclear"]
BusinessHoursMode = Literal["working_hours", "after_hours"]

DEFAULT_TRANSFER_CONTEXT = "from-internal"
DEFAULT_TRANSFER_EXTEN = "sales_real"
DEFAULT_TRANSFER_PRIORITY = 1
DEFAULT_DEPARTMENT: Department = "sales"
ALLOWED_DEPARTMENTS: tuple[Department, ...] = ("sales", "accounting", "delivery")
ALLOWED_BUSINESS_HOURS_MODES: tuple[BusinessHoursMode, ...] = ("working_hours", "after_hours")
DEFAULT_BUSINESS_HOURS_TZ = "Europe/Moscow"
DEFAULT_BUSINESS_HOURS_START = "09:00"
DEFAULT_BUSINESS_HOURS_END = "18:00"
DEFAULT_BUSINESS_HOURS_DAYS = (0, 1, 2, 3, 4)

_DEFAULT_ROUTE_EXTENSIONS: dict[Department, str] = {
    "sales": DEFAULT_TRANSFER_EXTEN,
    "accounting": "accounting",
    "delivery": "delivery",
}

_INTENT_KEYWORDS: dict[Department, tuple[str, ...]] = {
    "sales": (
        "buy",
        "purchase",
        "price",
        "quote",
        "sales",
        "new order",
        "place an order",
        "cylinder",
        "product",
        "\u043a\u0443\u043f\u0438\u0442\u044c",
        "\u043f\u043e\u043a\u0443\u043f",
        "\u0446\u0435\u043d\u0430",
        "\u0441\u0442\u043e\u0438\u043c",
        "\u0437\u0430\u043a\u0430\u0437\u0430\u0442\u044c",
        "\u043f\u0440\u043e\u0434\u0430\u0436",
        "\u0442\u043e\u0432\u0430\u0440",
        "\u0431\u0430\u043b\u043b\u043e\u043d",
        "\u0446\u0438\u043b\u0438\u043d\u0434\u0440",
    ),
    "accounting": (
        "accounting",
        "billing",
        "bill",
        "invoice",
        "payment",
        "paid",
        "pay",
        "receipt",
        "documents",
        "docs",
        "reconciliation",
        "\u0430\u043a\u0442 \u0441\u0432\u0435\u0440\u043a\u0438",
        "\u0431\u0443\u0445\u0433\u0430\u043b\u0442\u0435\u0440",
        "\u0441\u0447\u0435\u0442",
        "\u0441\u0447\u0451\u0442",
        "\u043e\u043f\u043b\u0430\u0442",
        "\u043f\u043b\u0430\u0442\u0435\u0436",
        "\u043f\u043b\u0430\u0442\u0451\u0436",
        "\u043d\u0430\u043a\u043b\u0430\u0434\u043d",
        "\u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442",
        "\u0441\u0432\u0435\u0440\u043a",
    ),
    "delivery": (
        "delivery",
        "shipping",
        "shipment",
        "ship",
        "arrive",
        "arrival",
        "logistics",
        "courier",
        "tracking",
        "where is my order",
        "order status",
        "\u0434\u043e\u0441\u0442\u0430\u0432",
        "\u043e\u0442\u0433\u0440\u0443\u0437",
        "\u043b\u043e\u0433\u0438\u0441\u0442",
        "\u043a\u0443\u0440\u044c\u0435\u0440",
        "\u0433\u0440\u0443\u0437",
        "\u0442\u0440\u0435\u043a",
        "\u043a\u043e\u0433\u0434\u0430 \u043f\u0440\u0438\u0435\u0434",
        "\u043a\u043e\u0433\u0434\u0430 \u043f\u0440\u0438\u0432\u0435\u0437",
        "\u0433\u0434\u0435 \u0437\u0430\u043a\u0430\u0437",
    ),
}


@dataclass(frozen=True)
class TransferTarget:
    """Dialplan destination for a bounded department route."""

    department: Department
    context: str
    extension: str
    priority: int

    def to_dict(self) -> dict[str, str | int]:
        return {
            "department": self.department,
            "context": self.context,
            "extension": self.extension,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class IntentDecision:
    """Deterministic intent classification and route resolution."""

    intent: Intent
    department: Department
    target: TransferTarget
    reason: str
    scores: dict[Department, int]
    matched_keywords: dict[Department, tuple[str, ...]]

    def to_dict(self) -> dict[str, object]:
        return {
            "intent": self.intent,
            "department": self.department,
            "target": self.target.to_dict(),
            "reason": self.reason,
            "scores": self.scores,
            "matched_keywords": {key: list(value) for key, value in self.matched_keywords.items()},
        }


@dataclass(frozen=True)
class BusinessHoursDecision:
    """Bounded working-hours result for one department route."""

    department: Department
    mode: BusinessHoursMode
    reason: str
    timezone: str
    local_time: str
    start: str
    end: str
    days: tuple[int, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "department": self.department,
            "mode": self.mode,
            "reason": self.reason,
            "timezone": self.timezone,
            "local_time": self.local_time,
            "start": self.start,
            "end": self.end,
            "days": list(self.days),
        }


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value >= 0 else default


def _env_text(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _env_text_optional(*names: str) -> str | None:
    for name in names:
        raw = os.getenv(name)
        if raw is not None and raw.strip():
            return raw.strip()
    return None


def _default_department() -> Department:
    raw = os.getenv("DEPARTMENT_INTENT_DEFAULT", DEFAULT_DEPARTMENT).strip().lower()
    return cast(Department, raw) if raw in ALLOWED_DEPARTMENTS else DEFAULT_DEPARTMENT


def route_for_department(department: Department) -> TransferTarget:
    """Resolve the configured transfer target for one bounded department."""
    prefix = f"DEPARTMENT_ROUTE_{department.upper()}_"
    default_extension = _DEFAULT_ROUTE_EXTENSIONS[department]
    if department == "sales":
        context = _env_text(prefix + "CONTEXT", _env_text("TRANSFER_CONTEXT", DEFAULT_TRANSFER_CONTEXT))
        extension = _env_text(prefix + "EXTEN", _env_text("TRANSFER_EXTEN", DEFAULT_TRANSFER_EXTEN))
        priority = _env_int(prefix + "PRIORITY", _env_int("TRANSFER_PRIORITY", DEFAULT_TRANSFER_PRIORITY))
    else:
        context = _env_text(prefix + "CONTEXT", DEFAULT_TRANSFER_CONTEXT)
        extension = _env_text(prefix + "EXTEN", default_extension)
        priority = _env_int(prefix + "PRIORITY", DEFAULT_TRANSFER_PRIORITY)
    return TransferTarget(department=department, context=context, extension=extension, priority=priority)


def _business_hours_mode_override(department: Department) -> BusinessHoursMode | None:
    raw = _env_text_optional(
        f"DEPARTMENT_WORKING_HOURS_{department.upper()}_MODE",
        "BUSINESS_HOURS_MODE",
    )
    if raw is None:
        return None
    normalized = raw.strip().lower()
    return cast(BusinessHoursMode, normalized) if normalized in ALLOWED_BUSINESS_HOURS_MODES else None


def _parse_hhmm(value: str, default: str) -> tuple[int, int, str]:
    candidate = value.strip() or default
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", candidate)
    if not match:
        candidate = default
        match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", candidate)
    assert match is not None
    return int(match.group(1)), int(match.group(2)), f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"


def _parse_days(value: str | None) -> tuple[int, ...]:
    if not value:
        return DEFAULT_BUSINESS_HOURS_DAYS
    days: list[int] = []
    for item in re.split(r"[,;\s]+", value):
        if not item:
            continue
        try:
            day = int(item)
        except ValueError:
            return DEFAULT_BUSINESS_HOURS_DAYS
        if day < 0 or day > 6:
            return DEFAULT_BUSINESS_HOURS_DAYS
        days.append(day)
    return tuple(dict.fromkeys(days)) or DEFAULT_BUSINESS_HOURS_DAYS


def _timezone_for_name(tz_name: str) -> tuple[tzinfo, str, str | None]:
    try:
        return ZoneInfo(tz_name), tz_name, None
    except ZoneInfoNotFoundError:
        if tz_name == DEFAULT_BUSINESS_HOURS_TZ:
            return timezone(timedelta(hours=3)), tz_name, "fixed_utc_plus_03_fallback"
        return timezone(timedelta(hours=3)), DEFAULT_BUSINESS_HOURS_TZ, "invalid_timezone_defaulted"


def business_hours_for_department(
    department: Department,
    *,
    now: datetime | None = None,
) -> BusinessHoursDecision:
    """Resolve working-hours vs after-hours for a bounded department schedule."""
    override = _business_hours_mode_override(department)
    tz_name = _env_text_optional(
        f"DEPARTMENT_WORKING_HOURS_{department.upper()}_TZ",
        "BUSINESS_HOURS_TZ",
    ) or DEFAULT_BUSINESS_HOURS_TZ
    tz, tz_name, _timezone_reason = _timezone_for_name(tz_name)

    local_now = (now or datetime.now(tz)).astimezone(tz)
    start_hour, start_minute, start_text = _parse_hhmm(
        _env_text_optional(f"DEPARTMENT_WORKING_HOURS_{department.upper()}_START", "BUSINESS_HOURS_START")
        or DEFAULT_BUSINESS_HOURS_START,
        DEFAULT_BUSINESS_HOURS_START,
    )
    end_hour, end_minute, end_text = _parse_hhmm(
        _env_text_optional(f"DEPARTMENT_WORKING_HOURS_{department.upper()}_END", "BUSINESS_HOURS_END")
        or DEFAULT_BUSINESS_HOURS_END,
        DEFAULT_BUSINESS_HOURS_END,
    )
    days = _parse_days(
        _env_text_optional(f"DEPARTMENT_WORKING_HOURS_{department.upper()}_DAYS", "BUSINESS_HOURS_DAYS")
    )
    if override is not None:
        return BusinessHoursDecision(
            department=department,
            mode=override,
            reason="mode_override",
            timezone=tz_name,
            local_time=local_now.isoformat(),
            start=start_text,
            end=end_text,
            days=days,
        )

    start_minutes = start_hour * 60 + start_minute
    end_minutes = end_hour * 60 + end_minute
    current_minutes = local_now.hour * 60 + local_now.minute
    in_day = local_now.weekday() in days
    in_time = start_minutes <= current_minutes < end_minutes if start_minutes < end_minutes else False
    mode: BusinessHoursMode = "working_hours" if in_day and in_time else "after_hours"
    reason = "within_schedule" if mode == "working_hours" else "outside_schedule"
    return BusinessHoursDecision(
        department=department,
        mode=mode,
        reason=reason,
        timezone=tz_name,
        local_time=local_now.isoformat(),
        start=start_text,
        end=end_text,
        days=days,
    )


def _keyword_matches(text: str, keyword: str) -> bool:
    if re.search(r"\s", keyword) or not keyword.isascii():
        return keyword in text
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(keyword)}", text))


def classify_department_intent(issue_text: str) -> IntentDecision:
    """Classify ISSUE text into sales/accounting/delivery with explicit unclear fallback."""
    normalized = issue_text.strip().lower()
    matched: dict[Department, tuple[str, ...]] = {}
    scores: dict[Department, int] = {}
    for department, keywords in _INTENT_KEYWORDS.items():
        hits = tuple(keyword for keyword in keywords if _keyword_matches(normalized, keyword))
        matched[department] = hits
        scores[department] = len(hits)

    best_score = max(scores.values()) if scores else 0
    default_department = _default_department()
    if best_score <= 0:
        department = default_department
        return IntentDecision(
            intent="unclear",
            department=department,
            target=route_for_department(department),
            reason=f"unclear_default_{department}",
            scores=scores,
            matched_keywords=matched,
        )

    winners = tuple(department for department, score in scores.items() if score == best_score)
    if len(winners) != 1:
        department = default_department
        return IntentDecision(
            intent="unclear",
            department=department,
            target=route_for_department(department),
            reason=f"ambiguous_default_{department}",
            scores=scores,
            matched_keywords=matched,
        )

    department = winners[0]
    return IntentDecision(
        intent=department,
        department=department,
        target=route_for_department(department),
        reason=f"matched_{department}",
        scores=scores,
        matched_keywords=matched,
    )
