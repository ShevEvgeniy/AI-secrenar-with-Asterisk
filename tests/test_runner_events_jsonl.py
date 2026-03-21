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
        assert payload.get("channel_id") == result["call_id"]
        assert "action" in payload
        assert "status" in payload


def test_events_and_artifacts_overrides_use_single_directory(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    call_id_override = "call-override-1"
    channel_id = "channel-override-1"
    artifact_dir = tmp_path / "artifacts" / channel_id
    events_path = artifact_dir / "events.jsonl"
    input_path = tmp_path / "input.wav"
    input_path.write_bytes(b"fake-wav")

    result = run_pipeline(
        "real",
        settings,
        audio_path_override=input_path,
        call_id_override=call_id_override,
        artifact_dir_override=artifact_dir,
        events_path_override=events_path,
        channel_id=channel_id,
    )

    assert result["call_id"] == call_id_override
    assert Path(result["artifact_dir"]) == artifact_dir
    assert Path(result["paths"]["events"]) == events_path

    assert events_path.exists()
    lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    for raw in lines:
        payload = json.loads(raw)
        assert payload.get("call_id") == call_id_override
        assert payload.get("channel_id") == channel_id

    for key, value in result["paths"].items():
        if key == "events":
            continue
        assert Path(value).parent == artifact_dir

    artifacts_root = tmp_path / "artifacts"
    subdirs = sorted(path.name for path in artifacts_root.iterdir() if path.is_dir())
    assert subdirs == [channel_id]
    assert not (artifacts_root / call_id_override).exists()
