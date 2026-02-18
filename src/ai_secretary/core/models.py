"""Core data models used across modules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True)
class Message:
    """A single message in a dialogue."""

    role: str
    content: str


@dataclass(frozen=True)
class Summary:
    """Summary text produced by the summarizer."""

    text: str


@dataclass(frozen=True)
class Response:
    """Response text produced by the response agent."""

    text: str


@dataclass(frozen=True)
class Chunk:
    """A knowledge base chunk."""

    id: str
    text: str
    source: str


@dataclass(frozen=True)
class CallRecord:
    """Stored call metadata."""

    call_id: str
    caller: str
    started_at: datetime
    messages: Sequence[Message]
