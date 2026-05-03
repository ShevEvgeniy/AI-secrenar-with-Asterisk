"""Bounded local JSONL persistence for callback-worthy calls."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


CallbackOutcomeType = Literal["after_hours_callback", "safe_finish"]


@dataclass(frozen=True)
class CallbackRecord:
    """One inspectable callback/support record."""

    record_id: str
    call_id: str
    timestamp: str
    department: str
    issue: str
    name: str
    city: str
    phone: str
    outcome_type: CallbackOutcomeType
    outcome_reason: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def callback_records_path(storage_dir: Path) -> Path:
    """Return the local JSONL file used for callback capture."""
    return storage_dir / "callbacks" / "callback_records.jsonl"


def build_callback_record(
    *,
    call_id: str,
    profile: dict[str, Any],
    outcome_type: CallbackOutcomeType,
    outcome_reason: str,
    department: str = "",
) -> CallbackRecord:
    """Create a flat record with a deterministic schema."""
    timestamp = datetime.now(timezone.utc).isoformat()
    resolved_department = department or str(profile.get("department") or profile.get("department_intent") or "")
    phone = str(profile.get("phone_digits") or profile.get("phone") or "")
    record_id_source = "|".join((call_id, timestamp, outcome_type, outcome_reason))
    record_id = hashlib.sha256(record_id_source.encode("utf-8")).hexdigest()[:16]
    return CallbackRecord(
        record_id=record_id,
        call_id=call_id,
        timestamp=timestamp,
        department=resolved_department,
        issue=str(profile.get("issue") or ""),
        name=str(profile.get("name") or ""),
        city=str(profile.get("city") or ""),
        phone=phone,
        outcome_type=outcome_type,
        outcome_reason=outcome_reason,
    )


def append_callback_record(path: Path, record: CallbackRecord) -> str:
    """Append one record as JSONL and return the persisted record id."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    return record.record_id
