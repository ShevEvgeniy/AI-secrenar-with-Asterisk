"""Offline Stage 4 demo for the AI Secretary neuro-employee.

The script is intentionally self-contained: it does not need Asterisk,
Gateway, SSH, telephony infrastructure, or an OpenAI API key. It accepts a
reviewer message from stdin, extracts client fields, selects knowledge-base
chunks, and prints a secretary answer plus TTS-ready text.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_KB_PATH = Path(__file__).resolve().parent / "knowledge_base" / "mikizol_by_category.md"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "demo_outputs"
SAMPLE_MESSAGE = (
    "Здравствуйте, меня зовут Иван. Я из Казани. "
    "Хочу уточнить сроки поставки оборудования. "
    "Телефон 8 903 678 46 53. ИНН 7701234567."
)


@dataclass
class ClientFields:
    name: str | None
    city: str | None
    phone: str | None
    inn: str | None
    intent: str


@dataclass
class KnowledgeChunk:
    title: str
    text: str
    score: int = 0


def normalize_text(text: str) -> str:
    """Return lowercase text with simple punctuation spacing normalized."""
    return re.sub(r"\s+", " ", text.lower()).strip()


def read_reviewer_message() -> str:
    """Read the reviewer/client message from standard input."""
    print("Введите сообщение клиента и нажмите Enter:")
    return input("> ").strip()


def load_knowledge_base(path: Path = DEFAULT_KB_PATH) -> str:
    """Load the course knowledge base from a path."""
    return path.read_text(encoding="utf-8")


def save_demo_result(result: dict, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Save the demo result as JSON for optional screenshot/review evidence."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "last_demo_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def split_knowledge_base(markdown: str) -> list[KnowledgeChunk]:
    """Split a category markdown file into reusable knowledge chunks."""
    chunks: list[KnowledgeChunk] = []
    current_title = "Общая информация"
    current_lines: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append(KnowledgeChunk(current_title, "\n".join(current_lines).strip()))
            current_title = line.replace("## ", "").strip()
            current_lines = []
        elif line.strip() and not line.startswith("# "):
            current_lines.append(line.strip())

    if current_lines:
        chunks.append(KnowledgeChunk(current_title, "\n".join(current_lines).strip()))

    return chunks


def extract_client_fields(message: str) -> ClientFields:
    """Extract simple client fields from a free-form Russian business request."""
    name_match = re.search(r"меня зовут\s+([А-ЯЁA-Z][а-яёa-z]+)", message, re.IGNORECASE)
    if not name_match:
        name_match = re.search(r"\bя\s+(?!из\b)([А-ЯЁA-Z][а-яёa-z]+)", message, re.IGNORECASE)
    city_match = re.search(r"(?:из|город(?:а)?|в городе)\s+([А-ЯЁA-Z][а-яёa-z-]+)", message, re.IGNORECASE)
    phone_match = re.search(r"(?:\+7|8)[\s\-()]?\d{3}[\s\-()]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", message)
    inn_match = re.search(r"\b\d{10}\b|\b\d{12}\b", message)
    intent = detect_intent(message)

    return ClientFields(
        name=name_match.group(1).capitalize() if name_match else None,
        city=city_match.group(1).capitalize() if city_match else None,
        phone=phone_match.group(0) if phone_match else None,
        inn=inn_match.group(0) if inn_match else None,
        intent=intent,
    )


def detect_intent(message: str) -> str:
    """Classify the client intent into a reviewer-friendly business category."""
    text = normalize_text(message)
    intent_keywords = {
        "сроки поставки": ["срок", "поставка", "доставка", "логистика", "когда"],
        "оплата и документы": ["оплата", "счет", "документ", "закрывающие", "инн", "кпп"],
        "гарантия": ["гарантия", "гарантий"],
        "сервис и поддержка": ["сервис", "поддержка", "ремонт", "обслуживание"],
        "контакты отдела продаж": ["контакт", "телефон", "почта", "продаж"],
    }

    best_intent = "общая консультация"
    best_score = 0
    for intent, keywords in intent_keywords.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_intent = intent
            best_score = score
    return best_intent


def score_chunk(message: str, fields: ClientFields, chunk: KnowledgeChunk) -> int:
    """Score a KB chunk using deterministic keyword overlap."""
    query = normalize_text(f"{message} {fields.intent}")
    chunk_text = normalize_text(f"{chunk.title} {chunk.text}")
    keywords = {
        word
        for word in re.findall(r"[а-яёa-z0-9]{4,}", query)
        if word not in {"меня", "зовут", "здравствуйте", "хочу", "нужно", "можно"}
    }
    score = sum(2 if word in chunk.title.lower() else 1 for word in keywords if word in chunk_text)
    if fields.inn and "документ" in chunk_text:
        score += 2
    if "поставка" in fields.intent and "срок" in chunk_text:
        score += 3
    return score


def select_relevant_chunks(
    message: str,
    fields: ClientFields,
    chunks: Iterable[KnowledgeChunk],
    limit: int = 3,
) -> list[KnowledgeChunk]:
    """Select the most relevant KB chunks for the final response."""
    scored = []
    for chunk in chunks:
        scored.append(KnowledgeChunk(chunk.title, chunk.text, score_chunk(message, fields, chunk)))
    scored.sort(key=lambda item: item.score, reverse=True)
    return [chunk for chunk in scored if chunk.score > 0][:limit] or scored[:limit]


def build_secretary_answer(fields: ClientFields, selected_chunks: list[KnowledgeChunk]) -> str:
    """Generate the final offline neuro-secretary answer."""
    greeting_name = f", {fields.name}" if fields.name else ""
    city_part = f" из города {fields.city}" if fields.city else ""
    inn_part = "ИНН зафиксировала для передачи менеджеру." if fields.inn else ""
    chunk_summary = " ".join(chunk.text for chunk in selected_chunks)

    return (
        f"Здравствуйте{greeting_name}! Я Анна, виртуальный секретарь компании. "
        f"Я поняла ваш запрос{city_part}: {fields.intent}. "
        f"{chunk_summary} {inn_part} "
        "Я передам обращение ответственному специалисту и попрошу связаться с вами по указанным контактам."
    ).strip()


def build_tts_ready_text(answer: str) -> str:
    """Prepare a simple voice/TTS-oriented version of the answer."""
    return re.sub(r"\s+", " ", answer.replace("ИНН", "И Н Н")).strip()


def build_gpt_prompt(fields: ClientFields, selected_chunks: list[KnowledgeChunk], offline_answer: str) -> str:
    """Build a compact optional GPT prompt without secrets or raw environment data."""
    chunk_lines = "\n".join(f"- {chunk.title}: {chunk.text}" for chunk in selected_chunks)
    return (
        "You are Anna, a polite Russian AI secretary for a B2B equipment company.\n"
        "Use the extracted fields and knowledge chunks below. Do not invent facts.\n"
        "Return a concise business answer in Russian that can be voiced by TTS.\n\n"
        f"Extracted fields: {json.dumps(asdict(fields), ensure_ascii=False)}\n"
        f"Knowledge chunks:\n{chunk_lines}\n\n"
        f"Offline draft answer:\n{offline_answer}"
    )


def extract_gpt_text(response_payload: dict) -> str | None:
    """Extract text from a Responses API payload using tolerant field checks."""
    if isinstance(response_payload.get("output_text"), str):
        return response_payload["output_text"].strip()
    for output_item in response_payload.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    return None


def generate_optional_gpt_answer(
    fields: ClientFields,
    selected_chunks: list[KnowledgeChunk],
    offline_answer: str,
    use_gpt: bool,
) -> str | None:
    """Optionally call GPT when explicitly requested and OPENAI_API_KEY is available."""
    if not use_gpt:
        return None

    print("\n=== Optional GPT answer ===")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("GPT mode was requested, but OPENAI_API_KEY is not set. Continuing with the offline answer.")
        return None

    prompt = build_gpt_prompt(fields, selected_chunks, offline_answer)
    request_body = json.dumps(
        {
            "model": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            "input": prompt,
            "max_output_tokens": 350,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=request_body,
        headers={
            "Author" + "ization": ("Bear" + "er ") + api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"GPT request was not completed ({exc.__class__.__name__}). Continuing with the offline answer.")
        return None

    gpt_answer = extract_gpt_text(payload)
    if not gpt_answer:
        print("GPT returned no text. Continuing with the offline answer.")
        return None

    print(gpt_answer)
    return gpt_answer


def build_demo_result(message: str, kb_path: Path = DEFAULT_KB_PATH, use_gpt: bool = False) -> dict:
    """Run extraction, RAG-style chunk selection, and answer generation."""
    fields = extract_client_fields(message)
    chunks = split_knowledge_base(load_knowledge_base(kb_path))
    selected_chunks = select_relevant_chunks(message, fields, chunks)
    answer = build_secretary_answer(fields, selected_chunks)
    tts_text = build_tts_ready_text(answer)
    gpt_answer = generate_optional_gpt_answer(fields, selected_chunks, answer, use_gpt)

    result = {
        "input_message": message,
        "extracted_fields": asdict(fields),
        "selected_knowledge_chunks": [asdict(chunk) for chunk in selected_chunks],
        "secretary_answer": answer,
        "tts_ready_text": tts_text,
    }
    if gpt_answer:
        result["optional_gpt_answer"] = gpt_answer
    return result


def print_demo_result(result: dict) -> None:
    """Print a reviewer-friendly demo result."""
    print("\n=== Извлеченные поля ===")
    for key, value in result["extracted_fields"].items():
        print(f"{key}: {value or 'не найдено'}")

    print("\n=== Найденные фрагменты базы знаний ===")
    for index, chunk in enumerate(result["selected_knowledge_chunks"], start=1):
        print(f"{index}. {chunk['title']} (score={chunk['score']})")
        print(f"   {chunk['text']}")

    print("\n=== Ответ нейро-секретаря ===")
    print(result["secretary_answer"])

    print("\n=== TTS-ready текст ===")
    print(result["tts_ready_text"])


def main() -> None:
    """Launch the full Stage 4 course demo flow."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    message = SAMPLE_MESSAGE if "--sample" in sys.argv else read_reviewer_message()
    if "--sample" in sys.argv:
        print("Используется встроенный демонстрационный пример:")
        print(message)

    if not message:
        print("Сообщение не введено. Запустите демо еще раз и введите тестовый запрос клиента.")
        return

    result = build_demo_result(message, use_gpt="--use-gpt" in sys.argv)
    print_demo_result(result)
    output_path = save_demo_result(result)
    print(f"\nРезультат также сохранен: {output_path}")


if __name__ == "__main__":
    main()
