"""Build latency report from call events.jsonl."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def _parse_ts(value: str) -> datetime:
    fixed = value.replace("Z", "+00:00")
    return datetime.fromisoformat(fixed)


def _load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _first_ts(events: list[dict[str, Any]], action: str) -> datetime | None:
    for event in events:
        if event.get("action") == action and event.get("ts"):
            return _parse_ts(str(event["ts"]))
    return None


def _last_ts(events: list[dict[str, Any]], action: str) -> datetime | None:
    for event in reversed(events):
        if event.get("action") == action and event.get("ts"):
            return _parse_ts(str(event["ts"]))
    return None


def _dur_ms_or_diff(
    events: list[dict[str, Any]],
    action_with_dur: str,
    fallback_start_action: str,
    fallback_end_action: str,
) -> int | None:
    for event in reversed(events):
        if event.get("action") == action_with_dur and event.get("dur_ms") is not None:
            try:
                return int(event["dur_ms"])
            except (TypeError, ValueError):
                pass
    start_ts = _first_ts(events, fallback_start_action)
    end_ts = _last_ts(events, fallback_end_action)
    if start_ts is None or end_ts is None:
        return None
    return int((end_ts - start_ts).total_seconds() * 1000)


def _sum_dur_ms(events: list[dict[str, Any]], action: str) -> int | None:
    total = 0
    seen = False
    for event in events:
        if event.get("action") != action or event.get("dur_ms") is None:
            continue
        try:
            total += int(event["dur_ms"])
            seen = True
        except (TypeError, ValueError):
            continue
    return total if seen else None


def compute_latency_report(events: list[dict[str, Any]]) -> dict[str, Any]:
    call_id = ""
    for event in events:
        value = event.get("call_id")
        if isinstance(value, str) and value:
            call_id = value
            break

    prompt_ms = _sum_dur_ms(events, "play_prompt")
    record_sum_ms = _sum_dur_ms(events, "record_done")
    record_ms = (
        record_sum_ms
        if record_sum_ms is not None
        else _dur_ms_or_diff(events, "record_done", "record_start", "record_done")
    )
    download_ms = _sum_dur_ms(events, "download_recording")
    stt_ms = _sum_dur_ms(events, "user_transcribed")
    decision_ms = _sum_dur_ms(events, "dialog_decision")
    pipeline_ms = _dur_ms_or_diff(events, "pipeline_done", "pipeline_start", "pipeline_done")
    tts_ms = _dur_ms_or_diff(events, "tts_done", "tts_start", "tts_done")
    publish_ms = _dur_ms_or_diff(events, "publish", "publish_start", "publish")
    transfer_phrase_ms = _dur_ms_or_diff(
        events,
        "play_transfer_phrase",
        "play_transfer_phrase",
        "play_transfer_phrase",
    )
    transfer_ms = _dur_ms_or_diff(events, "transfer", "transfer", "transfer")

    if events and events[0].get("ts") and events[-1].get("ts"):
        total_ms = int(((_parse_ts(str(events[-1]["ts"])) - _parse_ts(str(events[0]["ts"]))).total_seconds()) * 1000)
    else:
        total_ms = None

    return {
        "call_id": call_id,
        "prompt_ms": prompt_ms,
        "record_ms": record_ms,
        "download_ms": download_ms,
        "stt_ms": stt_ms,
        "decision_ms": decision_ms,
        "pipeline_ms": pipeline_ms,
        "tts_ms": tts_ms,
        "publish_ms": publish_ms,
        "transfer_phrase_ms": transfer_phrase_ms,
        "transfer_ms": transfer_ms,
        "total_ms": total_ms,
    }


def _resolve_latest(storage_dir: Path) -> Path:
    candidates = list((storage_dir / "artifacts").glob("*/events.jsonl"))
    if not candidates:
        raise FileNotFoundError("No events.jsonl files found under artifacts/")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _resolve_events_path(args: argparse.Namespace) -> Path:
    storage_dir = Path("data/storage")
    if args.events:
        return Path(args.events)
    if args.call_id:
        return storage_dir / "artifacts" / args.call_id / "events.jsonl"
    if args.latest:
        return _resolve_latest(storage_dir)
    raise ValueError("Provide one of: --events PATH, --call-id ID, or --latest")


def main() -> int:
    parser = argparse.ArgumentParser(description="Latency report from events.jsonl")
    parser.add_argument("--events", type=str, default="")
    parser.add_argument("--call-id", type=str, default="")
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    try:
        events_path = _resolve_events_path(args)
        events = _load_events(events_path)
        if not events:
            raise RuntimeError(f"No events in {events_path}")
        report = compute_latency_report(events)
    except Exception as exc:
        print(f"ERROR {exc}")
        return 1

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
        return 0

    def _fmt(value: Any) -> str:
        return "n/a" if value is None else str(value)

    print(
        f"CALL {report['call_id']} "
        f"prompt={_fmt(report['prompt_ms'])} "
        f"record={_fmt(report['record_ms'])} "
        f"download={_fmt(report['download_ms'])} "
        f"stt={_fmt(report['stt_ms'])} "
        f"decision={_fmt(report['decision_ms'])} "
        f"pipeline={_fmt(report['pipeline_ms'])} "
        f"tts={_fmt(report['tts_ms'])} "
        f"publish={_fmt(report['publish_ms'])} "
        f"transfer_phrase={_fmt(report['transfer_phrase_ms'])} "
        f"transfer={_fmt(report['transfer_ms'])} "
        f"total={_fmt(report['total_ms'])}"
    )

    if args.verbose:
        for event in events:
            print(f"{event.get('ts')} {event.get('action')} state={event.get('state')} status={event.get('status')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
