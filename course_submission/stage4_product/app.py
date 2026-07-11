"""Local browser product for processing incoming client appeals."""

from __future__ import annotations

import argparse
import html
import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from pipeline import DEFAULT_RUNTIME_PATH, process_appeal


SAMPLE = "Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567."
LABELS = {"call_transcript": "Расшифровка звонка", "text_message": "Текстовое сообщение", "email": "Email"}


def page(result: dict | None = None, saved_path: str = "") -> bytes:
    def esc(value: object) -> str:
        return html.escape(str(value if value is not None else "не найдено"))
    output = ""
    if result:
        fields = "".join(f"<div><b>{esc(k)}</b><span>{esc(v)}</span></div>" for k, v in result["extracted_fields"].items())
        chunks = "".join(f"<article><b>{esc(c['title'])}</b><p>{esc(c['text'])}</p><small>релевантность: {c['score']}</small></article>" for c in result["selected_knowledge_chunks"])
        card = "".join(f"<div><b>{esc(k)}</b><span>{esc(v)}</span></div>" for k, v in result["manager_card"].items())
        output = f'''<section id="result"><div class="success">✓ Обращение обработано и сохранено: {esc(saved_path)}</div>
        <h2>Результат обработки</h2><h3>Извлечённые поля</h3><div class="grid">{fields}</div>
        <h3>Ответ клиенту</h3><div class="answer">{esc(result['client_answer'])}</div>
        <h3>Карточка менеджера</h3><div class="grid">{card}</div>
        <h3>Фрагменты базы знаний</h3>{chunks}<h3>TTS-ready текст</h3><div class="answer">{esc(result['tts_ready_text'])}</div></section>'''
    options = "".join(f'<option value="{k}">{v}</option>' for k, v in LABELS.items())
    document = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
    <title>Нейро-секретарь Анна</title><style>
    *{{box-sizing:border-box}}body{{margin:0;background:#f4f7fb;color:#172033;font:16px system-ui,Segoe UI,sans-serif}}header{{background:linear-gradient(120deg,#14213d,#2855a6);color:white;padding:38px max(5vw,20px)}}main{{max-width:1050px;margin:28px auto;padding:0 20px;display:grid;gap:24px}}section{{background:white;border-radius:16px;padding:26px;box-shadow:0 8px 30px #18345b18}}h1{{margin:0 0 8px}}h2{{margin-top:0}}label{{display:block;font-weight:650;margin:16px 0 7px}}select,input,textarea{{width:100%;padding:12px;border:1px solid #c9d2e3;border-radius:9px;font:inherit}}textarea{{min-height:170px;resize:vertical}}button{{margin-top:18px;padding:13px 22px;border:0;border-radius:9px;background:#2463d4;color:white;font-weight:700;cursor:pointer}}.hint{{color:#657086}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}}.grid div,article,.answer{{border:1px solid #dce3ef;border-radius:10px;padding:13px}}.grid b,.grid span{{display:block}}.grid b{{color:#657086;font-size:13px;text-transform:uppercase}}.success{{background:#e9f8ef;color:#176238;padding:12px;border-radius:9px;margin-bottom:20px;overflow-wrap:anywhere}}article{{margin:10px 0}}article p{{margin:8px 0}}small{{color:#657086}}footer{{text-align:center;color:#657086;padding:24px}}
    </style></head><body><header><h1>Нейро-секретарь «Анна»</h1><div>Локальный контур: входящее обращение → обработка → готовый результат</div></header><main>
    <section><h2>Новое обращение</h2><p class="hint">Работает локально, без телефонии, серверов и API-ключей.</p><form method="post" action="/process">
    <label>Тип обращения</label><select name="appeal_type">{options}</select><label>Источник (необязательно)</label><input name="source_label" placeholder="Например: сайт или общий email">
    <label>Текст обращения</label><textarea name="text" required>{esc(SAMPLE)}</textarea><button>Обработать обращение</button></form></section>{output}</main><footer>Stage 4 · демонстрационный продукт · синтетические данные</footer></body></html>'''
    return document.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(404); return
        self._send(page())

    def do_POST(self) -> None:
        if self.path != "/process":
            self.send_error(404); return
        length = int(self.headers.get("Content-Length", "0"))
        values = parse_qs(self.rfile.read(length).decode("utf-8"))
        text = values.get("text", [""])[0].strip()
        if not text:
            self.send_error(400, "Appeal text is required"); return
        result, saved = process_appeal(values.get("appeal_type", ["text_message"])[0], text, values.get("source_label", [""])[0])
        self._send(page(result, str(saved)))

    def _send(self, body: bytes) -> None:
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-smoke", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.sample_smoke:
        result, path = process_appeal("call_transcript", SAMPLE, "встроенный пример")
        assert result["extracted_fields"]["name"] == "Иван" and result["selected_knowledge_chunks"]
        print(json.dumps({"status": "ok", "appeal_id": result["appeal_id"], "intent": result["extracted_fields"]["intent"], "saved_to": str(path)}, ensure_ascii=False, indent=2))
        return
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Нейро-секретарь «Анна» запущена: http://{args.host}:{args.port}/")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nОстановка приложения.")
    finally: server.server_close()


if __name__ == "__main__":
    main()
