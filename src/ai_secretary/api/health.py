"""Health check endpoints."""

from __future__ import annotations

from typing import Mapping

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check() -> Mapping[str, str]:
    """Return a basic health response."""
    return {"status": "ok"}
