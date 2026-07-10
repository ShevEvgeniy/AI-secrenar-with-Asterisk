# Stage 4 Experiment History

## Experiment 1: Simple Prompt Without Role Or Knowledge Base

### Goal

Check whether a simple direct prompt can answer a client request without a role, extraction, or knowledge base.

### Full Prompt / Algorithm Description

The client message is passed directly to a generic assistant instruction:

```text
Answer the client politely and briefly.
Client message:
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

No company role is provided. No fields are extracted. No knowledge base is loaded. No retrieval or chunk search is performed.

### Test Input

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Observed Result

The response can be polite, but it is generic. It does not reliably identify structured fields, does not know company delivery rules, and may invent details.

### Limitations

- No neuro-secretary role.
- No structured extraction.
- No customer knowledge base.
- High risk of unsupported answers.
- No TTS-ready output.

### Decision

Rejected. The approach is too simple for the final course task.

## Experiment 2: Role Prompt For AI Secretary

### Goal

Check whether adding a secretary role improves tone and business usefulness.

### Full Prompt / Algorithm Description

The client message is passed to a role-based prompt:

```text
You are Анна, a polite AI secretary for a B2B equipment company.
Your task is to greet the client, understand the request, and prepare a short business response.
Do not invent facts. If details are missing, say that a manager will clarify them.

Client message:
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

No deterministic field extraction is performed. No knowledge base is loaded. The answer depends only on the role prompt and client text.

### Test Input

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Observed Result

The answer sounds more like a secretary. It can greet the client and say that a manager will respond, but it still lacks reliable extracted fields and company-specific delivery information.

### Limitations

- Better tone, but weak data handling.
- Contact details and INN are not guaranteed to be captured.
- No RAG/knowledge-base search.
- No visible experiment evidence for chunk selection.

### Decision

Partially useful. Keep the role idea, but add structured extraction and knowledge search.

## Experiment 3: Role Prompt Plus Structured Extraction Of Client Fields

### Goal

Check whether the secretary can produce a clearer workflow by extracting name, city, phone, INN, and intent before answering.

### Full Prompt / Algorithm Description

The workflow is:

1. Use the role: "Анна, AI secretary for a B2B equipment company."
2. Extract fields:
   - name;
   - city;
   - phone;
   - INN;
   - intent.
3. Use the extracted fields to build a response.

Prompt/algorithm:

```text
You are Анна, a polite AI secretary.
First extract structured fields from the client message:
- name
- city
- phone
- INN
- intent
Then answer politely and say what will happen next.
Do not invent company delivery rules.

Client message:
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Test Input

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Observed Result

The answer is clearer. It can show that the client is Иван from Казань and that the request is about delivery timing. However, without a knowledge base, the answer still cannot provide company-specific delivery expectations.

### Limitations

- Structured fields improve handoff quality.
- Still no company knowledge base.
- Delivery timing remains vague.
- No chunk search evidence.

### Decision

Accepted as an intermediate step. Keep structured extraction and add knowledge-base chunk search.

## Experiment 4: Role Prompt Plus Knowledge Base Chunk Search / RAG

### Goal

Check whether knowledge-base retrieval makes the answer more grounded and useful.

### Full Prompt / Algorithm Description

The workflow is:

1. Read the client message.
2. Extract name, city, phone, INN, and intent.
3. Load the company knowledge base.
4. Split it into category chunks.
5. Score chunks by keywords from the client request and detected intent.
6. Use selected chunks in the answer.

Prompt/algorithm:

```text
You are Анна, a polite AI secretary for a B2B equipment company.
Use only the selected knowledge chunks below.
Extract client fields, summarize the intent, and answer politely.
Prepare the answer so it can later be voiced.

Selected knowledge chunks:
1. Сроки и логистика: Стандартный срок поставки составляет 10-20 рабочих дней после подтверждения заказа и оплаты.
2. Поставка оборудования: Мы поставляем промышленное оборудование по договору. Сроки зависят от наличия на складе и логистики.
3. Документы: Для оформления необходимы реквизиты компании, ИНН/КПП и контактные данные ответственного лица.

Client message:
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Test Input

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Observed Result

The answer becomes grounded: it can mention that standard delivery is 10-20 working days after order confirmation and payment, while still passing the request to a responsible specialist.

### Limitations

- Keyword scoring is simpler than embeddings.
- Semantic accuracy depends on knowledge-base quality.
- Offline demo does not prove production telephony behavior.

### Decision

Accepted for the course demo because it demonstrates the full neuro-employee logic without requiring servers or API keys.

## Experiment 5: Final Selected Algorithm With Extraction + RAG + Secretary Response + TTS-Ready Text

### Goal

Create a finished reviewer-friendly neuro-employee version that runs locally and shows all required stages.

### Full Prompt / Algorithm Description

The final demo uses this deterministic local algorithm:

1. Ask the reviewer to enter a client message.
2. Extract client fields:
   - name;
   - city;
   - phone;
   - INN;
   - intent.
3. Load `knowledge_base/mikizol_by_category.md`.
4. Split the knowledge base by category headings.
5. Score every chunk with deterministic keyword overlap and intent-specific bonuses.
6. Select the top relevant chunks.
7. Generate a polite AI secretary answer as "Анна".
8. Generate a TTS-ready version by normalizing spacing and expanding sensitive abbreviations such as INN for voice.
9. Print the result and save JSON evidence.

Full local instruction represented by the code:

```text
You are Анна, a virtual AI secretary.
Use extracted client fields and selected knowledge-base chunks.
Do not require servers or API keys.
Do not invent unsupported facts.
Return a clear business response and a TTS-ready text.
```

### Test Input

```text
Здравствуйте, меня зовут Иван. Я из Казани. Хочу уточнить сроки поставки оборудования. Телефон 8 903 678 46 53. ИНН 7701234567.
```

### Observed Result

The final demo prints:

- extracted fields;
- selected knowledge chunks;
- a final answer from "Анна";
- TTS-ready text;
- saved JSON output path.

The answer is grounded in the knowledge base and is understandable for a course reviewer.

### Limitations

- It is an educational offline demo, not a production live-call proof.
- Keyword scoring is deterministic and simple.
- Optional GPT mode is not required and is not enabled by default.

### Decision

Selected as the final Stage 4 algorithm because it demonstrates the full course-required flow while remaining safe and easy to run.

## Final Conclusion

The selected variant is Experiment 5: extraction + RAG-style knowledge chunk search + secretary answer + TTS-ready text.

It is selected because it shows the full neuro-employee process: client input, structured field extraction, knowledge-base search, grounded response generation, and voice-oriented output. The desired course result is achieved for a local educational demo.

Remaining limitations:

- The demo does not prove production Asterisk/Gateway/live-call behavior.
- It does not use real customer audio.
- It does not measure latency or production reliability.
- Keyword retrieval can be improved with embeddings or a vector database.

Possible future improvements:

- Add optional OpenAI/GPT mode with explicit API-key opt-in.
- Add speech-to-text and text-to-speech screenshots or video.
- Add a small web interface for reviewers.
- Add more knowledge-base categories and test scenarios.
- Add automated unit tests for extraction and chunk scoring.
