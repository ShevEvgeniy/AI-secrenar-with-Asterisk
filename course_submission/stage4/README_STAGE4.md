# Stage 4 GPT Final Submission Package

This folder contains the final course submission package for "Этап 4. GPT. Создание финальной версии нейро-сотрудника".

## What The Neuro-Employee Does

The demo presents the AI Secretary "Анна" as a local, offline-friendly neuro-employee. A client writes or says what they need, and the secretary:

1. accepts the client message as text input;
2. extracts useful fields such as name, city, phone, INN, and intent;
3. loads a small customer knowledge base;
4. splits the knowledge base into chunks;
5. selects relevant chunks with deterministic keyword scoring;
6. generates a polite business answer;
7. prepares a TTS-ready text version that can be voiced later.

This solves the course task of showing the full neuro-employee algorithm: client input, summary/extraction, knowledge-base search, final model-style response, and voice-oriented output.

## Production Boundary

The broader repository contains production-oriented Asterisk, Gateway, and live-call work. That integration is not required for this course demo. The Stage 4 demo is intentionally local and offline-friendly so a reviewer can run it without Asterisk, Gateway, SSH, telephony infrastructure, server credentials, or API keys.

The basic demo does not require OpenAI or any other API key. Optional GPT usage is available with `--use-gpt` only when `OPENAI_API_KEY` is present, but it is not required for this package.

## Final Algorithm

The final selected algorithm is:

1. Receive client text.
2. Extract structured client fields with deterministic rules.
3. Detect the business intent.
4. Load `knowledge_base/mikizol_by_category.md`.
5. Split the knowledge base by category headings.
6. Score chunks by keyword overlap and intent-specific bonuses.
7. Build a secretary response using extracted fields and selected chunks.
8. Build a TTS-ready variant.
9. Print and save the result for reviewer evidence.

## How To Run

From the repository root:

```powershell
python course_submission/stage4/final_demo.py
```

For a deterministic built-in reviewer example, run:

```powershell
python course_submission/stage4/final_demo.py --sample
```

Optional GPT mode is available only when the coordinator explicitly wants to show a real GPT-backed variant:

```powershell
python course_submission/stage4/final_demo.py --sample --use-gpt
```

GPT mode is optional and requires `OPENAI_API_KEY` in the local environment. If `--use-gpt` is provided but `OPENAI_API_KEY` is absent, the script prints a friendly fallback message and continues with the offline answer. The basic course demo can be checked without API keys.

Then enter a sample client request, for example:

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

The script prints:

- extracted fields;
- selected knowledge-base chunks;
- final secretary answer;
- TTS-ready text;
- path to the saved JSON result in `course_submission/stage4/demo_outputs/`.

## Included Files

- `README_STAGE4.md` - this overview and run guide.
- `experiments_stage4.md` - experiment history and final decision.
- `final_demo.py` - runnable local demo.
- `knowledge_base/mikizol_by_category.md` - non-confidential demo knowledge base.
- `screenshots/README_screenshots.md` - screenshots/video guidance.
- `stage3/README_stage3_document.md` - Stage 3 document link and export note.
- `submission_checklist.md` - final coordinator checklist.

## Screenshots To Make

See `screenshots/README_screenshots.md`. At minimum, capture:

1. terminal before running `final_demo.py`;
2. entered client message;
3. extracted fields, selected chunks, and final answer output.

## Stage 3 Document

The Stage 3 document link is recorded in `stage3/README_stage3_document.md`.

If the final course submission folder requires actual files instead of links, the coordinator should export or copy the Stage 3 Google document as `.docx` or `.pdf` into the final Drive/Yandex/Google folder.

## What To Submit

Submit a final folder or link that contains this Stage 4 package, the Stage 3 document link or exported file, and the requested screenshots/video evidence. Ensure that document access is set correctly before submitting.
