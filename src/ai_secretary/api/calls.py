"""Call-related endpoints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config.settings import Settings
from ..core.runner import run_pipeline

router = APIRouter()


class DemoRunRequest(BaseModel):
    """Request body for demo run."""

    mode: str


@router.post("/demo/run")
def run_demo(request: DemoRunRequest) -> Mapping[str, Any]:
    """Run demo pipeline for the requested mode."""
    mode = request.mode.strip().lower()
    if mode not in {"real", "synth"}:
        raise HTTPException(status_code=400, detail="mode must be real or synth")

    settings = Settings.from_env()
    result = run_pipeline(mode, settings)
    return result


def _read_text(path: Path) -> str | None:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/calls/{call_id}")
def get_call(call_id: str) -> Mapping[str, Any]:
    """Return stored artifacts for a call id."""
    settings = Settings.from_env()
    base = settings.storage_dir / "artifacts" / call_id
    if not base.exists():
        raise HTTPException(status_code=404, detail="call_id not found")

    return {
        "call_id": call_id,
        "profile": _read_json(base / "profile.json"),
        "summary": _read_text(base / "summary.txt"),
        "response": _read_text(base / "response.txt"),
        "response_for_tts": _read_text(base / "response_for_tts.txt"),
        "chunks": _read_json(base / "chunks.json"),
        "transcript": _read_text(base / "transcript.txt"),
    }
