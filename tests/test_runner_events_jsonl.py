"""Tests for pipeline JSONL events artifact."""

from __future__ import annotations

import json
from pathlib import Path

from ai_secretary.config.settings import Settings
from ai_secretary.core.runner import run_pipeline


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        openai_api_key="",
        elevenlabs_api_key="",
        ari_url="http://localhost:8088/ari",
        ari_user="",
        ari_password="",
        sqlite_path=tmp_path / "db.sqlite",
        storage_dir=tmp_path,
        demo_mode="synth",
        demo_audio_path=Path("./data/demo/client_synth.wav"),
        expected_real_phone="79000000000",
        kb_path=Path("./data/kb/mikizol_by_category.md"),
        rag_top_k=3,
        asterisk_sounds_dir=Path("/var/lib/asterisk/sounds"),
        asterisk_sounds_subdir="ai_secretary",
        asterisk_ssh_host="",
        asterisk_ssh_user="",
        asterisk_ssh_key="",
        asterisk_ssh_password="",
        asterisk_docker_container="",
    )


def test_events_jsonl_created_and_valid(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    result = run_pipeline("synth", settings)
    events_path = Path(result["paths"]["events"])

    assert events_path.exists()
    lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1

    for raw in lines:
        payload = json.loads(raw)
        assert isinstance(payload, dict)
        assert payload.get("call_id") == result["call_id"]
        assert "action" in payload
        assert "status" in payload
