"""Deterministic offline appeal-processing pipeline for Stage 4."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
DEFAULT_KB_PATH = ROOT / "knowledge_base" / "mikizol_by_category.md"
DEFAULT_RUNTIME_PATH = ROOT / "runtime" / "processed_appeals.jsonl"


@dataclass
class KnowledgeChunk:
    title: str
    text: str
    score: int = 0


def _normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def extract_fields(text: str, appeal_type: str) -> dict:
    name = re.search(r"(?:меня зовут|я)\s+([А-ЯЁA-Z][а-яёa-z-]+)", text, re.I)
    city = re.search(r"(?:я\s+из|из|город(?:а)?|в городе)\s+([А-ЯЁA-Z][а-яёa-z-]+)", text, re.I)
    phone = re.search(r"(?:\+7|8)[\s()\-]*\d{3}[\s()\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}", text)
    inn = re.search(r"(?<!\d)(?:\d{10}|\d{12})(?!\d)", text)
    normalized = _normalized(text)
    intents = {
        "сроки поставки": ("срок", "постав", "достав", "логист"),
        "оплата и документы": ("оплат", "счет", "документ", "акт", "накладн", "инн", "кпп"),
        "гарантия и сервис": ("гарант", "сервис", "ремонт", "обслуж", "не работает"),
    }
    scored = [(sum(k in normalized for k in keys), label) for label, keys in intents.items()]
    score, intent = max(scored)
    if not score:
        intent = "общая консультация"
    return {
        "name": name.group(1).capitalize() if name else None,
        "city": city.group(1).capitalize() if city else None,
        "phone": phone.group(0) if phone else None,
        "inn": inn.group(0) if inn else None,
        "intent": intent,
        "appeal_type": appeal_type,
    }


def load_chunks(path: Path = DEFAULT_KB_PATH) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    title = "Общая информация"
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if lines:
                chunks.append(KnowledgeChunk(title, " ".join(lines)))
            title, lines = line[3:].strip(), []
        elif line and not line.startswith("# "):
            lines.append(line)
    if lines:
        chunks.append(KnowledgeChunk(title, " ".join(lines)))
    return chunks


def select_chunks(text: str, fields: dict, chunks: list[KnowledgeChunk], limit: int = 3) -> list[KnowledgeChunk]:
    query_words = set(re.findall(r"[а-яёa-z0-9]{4,}", _normalized(text + " " + fields["intent"])))
    for chunk in chunks:
        haystack = _normalized(chunk.title + " " + chunk.text)
        chunk.score = sum(2 if word in _normalized(chunk.title) else 1 for word in query_words if word in haystack)
    return sorted(chunks, key=lambda item: item.score, reverse=True)[:limit]


def process_appeal(appeal_type: str, text: str, source_label: str = "", save: bool = True,
                   runtime_path: Path = DEFAULT_RUNTIME_PATH) -> tuple[dict, Path | None]:
    fields = extract_fields(text, appeal_type)
    selected = select_chunks(text, fields, load_chunks())
    name = f", {fields['name']}" if fields["name"] else ""
    facts = " ".join(chunk.text for chunk in selected[:2])
    answer = (f"Здравствуйте{name}! Я Анна, виртуальный секретарь компании. "
              f"Я зафиксировала обращение по теме «{fields['intent']}». {facts} "
              "Передаю запрос ответственному менеджеру для уточнения деталей.")
    manager_card = {
        "priority": "обычный",
        "client": fields["name"] or "не указано",
        "contacts": fields["phone"] or "не указаны",
        "city": fields["city"] or "не указан",
        "inn": fields["inn"] or "не указан",
        "topic": fields["intent"],
        "recommended_action": "Проверить данные обращения и связаться с клиентом.",
    }
    result = {
        "appeal_id": str(uuid4()),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "source_label": source_label.strip() or "не указан",
        "input_text": text,
        "extracted_fields": fields,
        "selected_knowledge_chunks": [asdict(chunk) for chunk in selected],
        "client_answer": answer,
        "manager_card": manager_card,
        "tts_ready_text": re.sub(r"\s+", " ", answer.replace("ИНН", "И Н Н")).strip(),
        "mode": "offline",
    }
    saved_path = None
    if save:
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        with runtime_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(result, ensure_ascii=False) + "\n")
        saved_path = runtime_path
    return result, saved_path
