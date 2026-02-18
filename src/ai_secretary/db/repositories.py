"""Repositories for persistence."""

from __future__ import annotations

from dataclasses import dataclass
from .sqlite import SQLiteClient
from ..core.models import CallRecord


@dataclass
class CallRepository:
    """Store and retrieve call records."""

    client: SQLiteClient

    def save_call(self, record: CallRecord) -> None:
        """Persist a call record (placeholder)."""
        _ = record
        return None
