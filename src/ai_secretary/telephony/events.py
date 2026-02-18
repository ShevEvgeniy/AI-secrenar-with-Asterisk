"""Telephony event models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AriEvent:
    """Represents an incoming ARI event."""

    event_type: str
    payload: dict
