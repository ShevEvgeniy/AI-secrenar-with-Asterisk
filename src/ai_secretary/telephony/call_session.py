"""Call session state machine and event logging."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


class CallState(str, Enum):
    """Minimal call-flow state machine."""

    INIT = "INIT"
    ANSWERED = "ANSWERED"
    ASKING = "ASKING"
    RECORDING = "RECORDING"
    THINKING = "THINKING"
    RESPONDING = "RESPONDING"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass(slots=True)
class CallSession:
    """Represents a single call session with persisted JSONL events."""

    call_id: str
    channel_id: str
    artifact_dir: Path
    state: CallState = CallState.INIT
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.log_event(action="session_created", status="ok")

    @property
    def events_path(self) -> Path:
        """Return path to per-call JSONL event file."""
        return self.artifact_dir / "events.jsonl"

    def transition(
        self,
        new_state: CallState,
        action: str,
        status: str = "ok",
        reason: str | None = None,
        http_status: int | None = None,
        dur_ms: int | None = None,
        media: str | None = None,
        sound_id: str | None = None,
        remote_path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Change state and persist one transition event."""
        self.state = new_state
        self.log_event(
            action=action,
            status=status,
            reason=reason,
            http_status=http_status,
            dur_ms=dur_ms,
            media=media,
            sound_id=sound_id,
            remote_path=remote_path,
            details=details,
        )

    def log_event(
        self,
        action: str,
        status: str,
        reason: str | None = None,
        http_status: int | None = None,
        dur_ms: int | None = None,
        media: str | None = None,
        sound_id: str | None = None,
        remote_path: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append one structured event to events.jsonl."""
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "call_id": self.call_id,
            "channel_id": self.channel_id,
            "state": self.state.value,
            "action": action,
            "status": status,
            "reason": reason,
            "http_status": http_status,
            "media": media,
            "sound_id": sound_id,
            "remote_path": remote_path,
            "dur_ms": dur_ms,
            "details": details or {},
        }
        with self.events_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
