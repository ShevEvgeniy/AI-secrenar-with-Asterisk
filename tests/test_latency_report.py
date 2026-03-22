"""Tests for latency report script."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _write_events(path: Path) -> None:
    events = [
        {"ts": "2026-03-22T10:00:00+00:00", "call_id": "ch-1", "action": "record_start", "state": "RECORDING", "status": "start"},
        {"ts": "2026-03-22T10:00:01+00:00", "call_id": "ch-1", "action": "record_done", "state": "RECORDING", "status": "ok", "dur_ms": 900},
        {"ts": "2026-03-22T10:00:01.100000+00:00", "call_id": "ch-1", "action": "pipeline_start", "state": "THINKING", "status": "start"},
        {"ts": "2026-03-22T10:00:02+00:00", "call_id": "ch-1", "action": "pipeline_done", "state": "THINKING", "status": "ok", "dur_ms": 850},
        {"ts": "2026-03-22T10:00:02.100000+00:00", "call_id": "ch-1", "action": "tts_start", "state": "RESPONDING", "status": "start"},
        {"ts": "2026-03-22T10:00:03+00:00", "call_id": "ch-1", "action": "tts_done", "state": "RESPONDING", "status": "ok", "dur_ms": 700},
        {"ts": "2026-03-22T10:00:03.100000+00:00", "call_id": "ch-1", "action": "publish", "state": "RESPONDING", "status": "ok", "dur_ms": 120},
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
    assert summary_line == "CALL ch-1 record=900 pipeline=850 tts=700 publish=120 total=4000"

    run_json = subprocess.run(
        [sys.executable, str(script_path), "--events", str(events_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_json.returncode == 0
    payload = json.loads(run_json.stdout.strip())
    assert payload["call_id"] == "ch-1"
    assert payload["record_ms"] == 900
    assert payload["pipeline_ms"] == 850
    assert payload["tts_ms"] == 700
    assert payload["publish_ms"] == 120
    assert payload["total_ms"] == 4000
