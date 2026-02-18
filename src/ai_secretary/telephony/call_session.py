"""Call session state container."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CallSession:
    """Represents a single call session."""

    call_id: str
    caller: str
    started_at: datetime
