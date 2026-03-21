"""Shared pipeline runner for CLI and API."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ..config.settings import Settings
from ..llm.parsers import parse_update_profile_fields
from ..rag.chunker import chunk_by_paragraphs
from ..rag.kb_loader import load_kb_text
from ..rag.search import search_top_k
from ..storage.files import save_json, save_text
from ..storage.paths import ensure_dirs
from ..tts.normalize_for_tts import normalize_text


@dataclass(frozen=True)
class PipelineResult:
    """Structured pipeline result."""

    call_id: str
    mode: str
    checks: dict[str, Any]
    profile: dict[str, Any]
    selected_chunks: list[str]
    artifact_dir: str
    paths: dict[str, str]
    rag: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "call_id": self.call_id,
            "mode": self.mode,
            "checks": self.checks,
            "profile": self.profile,
            "selected_chunks": self.selected_chunks,
            "artifact_dir": self.artifact_dir,
            "paths": self.paths,
            "rag": self.rag,
        }


def _resolve_demo_audio_path(mode: str) -> Path:
    if mode == "real":
        return Path("./data/demo/client_real.wav")
    return Path("./data/demo/client_synth.wav")


def _ensure_synth_audio(audio_path: Path) -> None:
    if audio_path.exists():
        return
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "make_demo_audio.py"
    subprocess.run([sys.executable, str(script_path)], check=True)


def _load_audio(path: Path) -> bytes:
    return path.read_bytes()


def _demo_transcribe(mode: str, audio_bytes: bytes) -> str:
    _ = audio_bytes
    if mode == "real":
        return "Мой телефон 903 678 46 53."
    return (
        "Здравствуйте, меня зовут Светлана Иванова. Я из Казани. "
        "Хочу уточнить условия поставки оборудования. "
        "Мой телефон 9 903 678 46 53. ИНН 7701234567."
    )


def _build_summary(transcript_text: str, profile: dict[str, Any]) -> str:
    phone_digits = profile.get("phone_digits", "")
    inn_digits = profile.get("inn_digits", "")
    command_parts = []
    if phone_digits:
        command_parts.append(f"phone={phone_digits}")
    if inn_digits:
        command_parts.append(f"inn={inn_digits}")
    command_payload = ",".join(command_parts)
    system_command = (
        f"[SYSTEM_COMMAND]UPDATE_PROFILE_FIELD:{command_payload}[/SYSTEM_COMMAND]"
        if command_payload
        else "[SYSTEM_COMMAND]UPDATE_PROFILE_FIELD:[/SYSTEM_COMMAND]"
    )
    return f"{system_command}\n{transcript_text}"


def _build_response(summary_text: str, selected_chunks: list[str]) -> str:
    _ = summary_text
    if selected_chunks:
        return f"Мы получили ваш запрос. Контекст: {selected_chunks[0]}"
    return "Мы получили ваш запрос и скоро ответим."


def _save_artifacts(
    artifact_dir: Path,
    profile: dict[str, Any],
    transcript_text: str,
    summary_text: str,
    response_text: str,
    tts_text: str,
    chunks_payload: dict[str, Any],
) -> dict[str, str]:
    ensure_dirs(artifact_dir)

    profile_path = artifact_dir / "profile.json"
    save_json(profile_path, profile)

    transcript_path = artifact_dir / "transcript.txt"
    save_text(transcript_path, transcript_text)

    summary_path = artifact_dir / "summary.txt"
    save_text(summary_path, summary_text)

    response_path = artifact_dir / "response.txt"
    save_text(response_path, response_text)

    response_tts_path = artifact_dir / "response_for_tts.txt"
    save_text(response_tts_path, tts_text)

    chunks_path = artifact_dir / "chunks.json"
    save_json(chunks_path, chunks_payload)

    return {
        "profile": str(profile_path.as_posix()),
        "transcript": str(transcript_path.as_posix()),
        "summary": str(summary_path.as_posix()),
        "response": str(response_path.as_posix()),
        "response_for_tts": str(response_tts_path.as_posix()),
        "chunks": str(chunks_path.as_posix()),
    }


def _append_event(
    events_path: Path,
    call_id: str,
    channel_id: str,
    state: str,
    action: str,
    status: str,
    reason: str | None = None,
    http_status: int | None = None,
    media: str | None = None,
    sound_id: str | None = None,
    remote_path: str | None = None,
    dur_ms: int | None = None,
) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "call_id": call_id,
        "channel_id": channel_id,
        "state": state,
        "action": action,
        "status": status,
        "reason": reason,
        "http_status": http_status,
        "media": media,
        "sound_id": sound_id,
        "remote_path": remote_path,
        "dur_ms": dur_ms,
    }
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with events_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def run_pipeline(
    mode: str,
    settings: Settings,
    audio_path_override: Path | None = None,
    call_id_override: str | None = None,
    artifact_dir_override: Path | None = None,
    events_path_override: Path | None = None,
    channel_id: str | None = None,
) -> dict[str, Any]:
    """Run a single pipeline pass and return a structured result."""
    if call_id_override is not None:
        call_id = call_id_override
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        call_id = f"{mode}_{timestamp}"

    artifact_dir_path = (
        artifact_dir_override
        if artifact_dir_override is not None
        else settings.storage_dir / "artifacts" / call_id
    )
    events_path = events_path_override if events_path_override is not None else artifact_dir_path / "events.jsonl"
    event_channel_id = channel_id if channel_id is not None else call_id
    _append_event(events_path, call_id, event_channel_id, "INIT", "pipeline_start", "start")

    audio_path = (
        audio_path_override
        if audio_path_override is not None
        else (settings.demo_audio_path if mode == settings.demo_mode else _resolve_demo_audio_path(mode))
    )

    checks: dict[str, Any] = {}
    if mode == "synth" and audio_path_override is None:
        _ensure_synth_audio(audio_path)
        if audio_path.exists():
            checks["synth_audio_ready"] = str(audio_path.as_posix())
            _append_event(events_path, call_id, event_channel_id, "ASKING", "synth_audio_ready", "ok")

    if not audio_path.exists():
        checks["audio_missing"] = str(audio_path.as_posix())
        _append_event(
            events_path,
            call_id,
            event_channel_id,
            "FAILED",
            "audio_missing",
            "fail",
            reason="audio_missing",
        )
        result = PipelineResult(
            call_id=call_id,
            mode=mode,
            checks=checks,
            profile={},
            selected_chunks=[],
            artifact_dir=str(artifact_dir_path.as_posix()),
            paths={"events": str(events_path.as_posix())},
            rag={"chunks_total": 0, "top_k": settings.rag_top_k, "scores": []},
        )
        return result.to_dict()

    audio_bytes = _load_audio(audio_path)
    _append_event(events_path, call_id, event_channel_id, "RECORDING", "audio_loaded", "ok")
    transcript_text = _demo_transcribe(mode, audio_bytes)
    _append_event(events_path, call_id, event_channel_id, "THINKING", "transcribe", "ok")

    profile = parse_update_profile_fields(transcript_text)
    summary_text = _build_summary(transcript_text, profile)

    kb_text = load_kb_text(settings.kb_path)
    chunks = chunk_by_paragraphs(kb_text)
    selected_chunks, scores = search_top_k(summary_text, chunks, settings.rag_top_k)

    response_text = _build_response(summary_text, selected_chunks)
    tts_text = normalize_text(response_text, profile.get("inn_digits"))
    _append_event(events_path, call_id, event_channel_id, "RESPONDING", "build_response", "ok")

    chunks_payload = {
        "kb_path": str(settings.kb_path.as_posix()),
        "chunks_total": len(chunks),
        "top_k": settings.rag_top_k,
        "selected": [
            {"rank": idx + 1, "score": float(scores[idx]), "text": selected_chunks[idx]}
            for idx in range(len(selected_chunks))
        ],
    }

    paths = _save_artifacts(
        artifact_dir_path,
        profile,
        transcript_text,
        summary_text,
        response_text,
        tts_text,
        chunks_payload,
    )
    paths["events"] = str(events_path.as_posix())
    _append_event(events_path, call_id, event_channel_id, "DONE", "save_artifacts", "ok")

    if mode == "real":
        expected = settings.expected_real_phone
        actual = profile.get("phone_digits")
        checks["phone_check_real"] = "OK" if actual == expected else f"FAIL expected={expected} actual={actual}"

    if mode == "synth":
        expected_phone = "79036784653"
        expected_inn = "7701234567"
        actual_phone = profile.get("phone_digits")
        actual_inn = profile.get("inn_digits")
        inn_error = profile.get("inn_error")

        checks["phone_check_synth"] = (
            "OK" if actual_phone == expected_phone else f"FAIL expected={expected_phone} actual={actual_phone}"
        )
        if inn_error:
            checks["inn_check_synth"] = f"FAIL {inn_error}"
        elif not actual_inn:
            checks["inn_check_synth"] = "FAIL inn_digits missing"
        elif len(actual_inn) not in (10, 12):
            checks["inn_check_synth"] = f"FAIL invalid inn length: {len(actual_inn)}"
        elif actual_inn != expected_inn:
            checks["inn_check_synth"] = f"FAIL expected={expected_inn} actual={actual_inn}"
        else:
            checks["inn_check_synth"] = "OK"

    artifact_dir = str(artifact_dir_path.as_posix())
    result = PipelineResult(
        call_id=call_id,
        mode=mode,
        checks=checks,
        profile=profile,
        selected_chunks=selected_chunks,
        artifact_dir=artifact_dir,
        paths=paths,
        rag={
            "chunks_total": len(chunks),
            "top_k": settings.rag_top_k,
            "scores": scores,
        },
    )
    return result.to_dict()


def run_pipeline_from_transcript(
    mode: str,
    settings: Settings,
    transcript_text: str,
    profile_override: dict[str, Any] | None = None,
    call_id_override: str | None = None,
    artifact_dir_override: Path | None = None,
    events_path_override: Path | None = None,
    channel_id: str | None = None,
) -> dict[str, Any]:
    """Run pipeline steps from existing transcript/profile without STT pass."""
    if call_id_override is not None:
        call_id = call_id_override
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        call_id = f"{mode}_{timestamp}"

    artifact_dir_path = (
        artifact_dir_override
        if artifact_dir_override is not None
        else settings.storage_dir / "artifacts" / call_id
    )
    events_path = events_path_override if events_path_override is not None else artifact_dir_path / "events.jsonl"
    event_channel_id = channel_id if channel_id is not None else call_id
    _append_event(events_path, call_id, event_channel_id, "INIT", "pipeline_start", "start")
    _append_event(events_path, call_id, event_channel_id, "THINKING", "transcribe", "ok")

    parsed_profile = parse_update_profile_fields(transcript_text)
    profile = dict(parsed_profile)
    if profile_override:
        profile.update(profile_override)
    summary_text = _build_summary(transcript_text, profile)

    kb_text = load_kb_text(settings.kb_path)
    chunks = chunk_by_paragraphs(kb_text)
    selected_chunks, scores = search_top_k(summary_text, chunks, settings.rag_top_k)

    response_text = _build_response(summary_text, selected_chunks)
    tts_text = normalize_text(response_text, profile.get("inn_digits"))
    _append_event(events_path, call_id, event_channel_id, "RESPONDING", "build_response", "ok")

    chunks_payload = {
        "kb_path": str(settings.kb_path.as_posix()),
        "chunks_total": len(chunks),
        "top_k": settings.rag_top_k,
        "selected": [
            {"rank": idx + 1, "score": float(scores[idx]), "text": selected_chunks[idx]}
            for idx in range(len(selected_chunks))
        ],
    }

    paths = _save_artifacts(
        artifact_dir_path,
        profile,
        transcript_text,
        summary_text,
        response_text,
        tts_text,
        chunks_payload,
    )
    paths["events"] = str(events_path.as_posix())
    _append_event(events_path, call_id, event_channel_id, "DONE", "save_artifacts", "ok")

    checks: dict[str, Any] = {}
    if mode == "real":
        expected = settings.expected_real_phone
        actual = profile.get("phone_digits")
        checks["phone_check_real"] = "OK" if actual == expected else f"FAIL expected={expected} actual={actual}"

    return PipelineResult(
        call_id=call_id,
        mode=mode,
        checks=checks,
        profile=profile,
        selected_chunks=selected_chunks,
        artifact_dir=str(artifact_dir_path.as_posix()),
        paths=paths,
        rag={
            "chunks_total": len(chunks),
            "top_k": settings.rag_top_k,
            "scores": scores,
        },
    ).to_dict()
