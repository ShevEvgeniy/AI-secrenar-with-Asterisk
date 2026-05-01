"""Tests for latency report script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_events(path: Path) -> None:
    events = [
        {"ts": "2026-03-22T09:59:59.700000+00:00", "call_id": "ch-1", "action": "play_prompt", "state": "ASKING", "status": "ok", "dur_ms": 180},
        {"ts": "2026-03-22T10:00:00+00:00", "call_id": "ch-1", "action": "record_start", "state": "RECORDING", "status": "start"},
        {"ts": "2026-03-22T10:00:01+00:00", "call_id": "ch-1", "action": "record_done", "state": "RECORDING", "status": "ok", "dur_ms": 900},
        {"ts": "2026-03-22T10:00:01.030000+00:00", "call_id": "ch-1", "action": "download_recording", "state": "RECORDING", "status": "ok", "dur_ms": 30},
        {"ts": "2026-03-22T10:00:01.080000+00:00", "call_id": "ch-1", "action": "user_transcribed", "state": "RECORDING", "status": "ok", "dur_ms": 50},
        {"ts": "2026-03-22T10:00:01.090000+00:00", "call_id": "ch-1", "action": "dialog_decision", "state": "RECORDING", "status": "ok", "dur_ms": 10},
        {"ts": "2026-03-22T10:00:01.100000+00:00", "call_id": "ch-1", "action": "pipeline_start", "state": "THINKING", "status": "start"},
        {"ts": "2026-03-22T10:00:02+00:00", "call_id": "ch-1", "action": "pipeline_done", "state": "THINKING", "status": "ok", "dur_ms": 850},
        {"ts": "2026-03-22T10:00:02.100000+00:00", "call_id": "ch-1", "action": "tts_start", "state": "RESPONDING", "status": "start"},
        {"ts": "2026-03-22T10:00:03+00:00", "call_id": "ch-1", "action": "tts_done", "state": "RESPONDING", "status": "ok", "dur_ms": 700},
        {"ts": "2026-03-22T10:00:03.100000+00:00", "call_id": "ch-1", "action": "publish", "state": "RESPONDING", "status": "ok", "dur_ms": 120},
        {"ts": "2026-03-22T10:00:03.300000+00:00", "call_id": "ch-1", "action": "play_transfer_phrase", "state": "RESPONDING", "status": "ok", "dur_ms": 200},
        {"ts": "2026-03-22T10:00:03.360000+00:00", "call_id": "ch-1", "action": "transfer", "state": "DONE", "status": "ok", "dur_ms": 60},
        {"ts": "2026-03-22T10:00:04+00:00", "call_id": "ch-1", "action": "playback", "state": "DONE", "status": "ok"},
    ]
    path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in events), encoding="utf-8")


def test_latency_report_summary_and_json(tmp_path: Path) -> None:
    events_path = tmp_path / "events.jsonl"
    _write_events(events_path)
    script_path = Path("scripts") / "latency_report.py"

    run_summary = subprocess.run(
        [sys.executable, str(script_path), "--events", str(events_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_summary.returncode == 0
    summary_line = run_summary.stdout.strip().splitlines()[0]
    assert summary_line == (
        "CALL ch-1 prompt=180 record=900 download=30 stt=50 decision=10 "
        "pipeline=850 tts=700 publish=120 transfer_phrase=200 transfer=60 total=4300"
    )

    run_json = subprocess.run(
        [sys.executable, str(script_path), "--events", str(events_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_json.returncode == 0
    payload = json.loads(run_json.stdout.strip())
    assert payload["call_id"] == "ch-1"
    assert payload["prompt_ms"] == 180
    assert payload["record_ms"] == 900
    assert payload["download_ms"] == 30
    assert payload["stt_ms"] == 50
    assert payload["decision_ms"] == 10
    assert payload["pipeline_ms"] == 850
    assert payload["tts_ms"] == 700
    assert payload["publish_ms"] == 120
    assert payload["transfer_phrase_ms"] == 200
    assert payload["transfer_ms"] == 60
    assert payload["total_ms"] == 4300
