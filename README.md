# 🇲🇦 Assistant ONSSA — RAG Chatbot

Customer-assistance chatbot for the official website of **ONSSA** (Office National
de Sécurité Sanitaire des produits Alimentaires, Morocco —
https://www.onssa.gov.ma/). Ask questions in natural language; answers are
grounded **exclusively** in ONSSA website content, in French, with source
citations — and the app runs **fully locally with no paid API**.

**Stack:** Python · Streamlit · Ollama (Mistral 7B) · FAISS · sentence-transformers
· hybrid retrieval (vector + BM25) · local voice (faster-whisper + Piper).

![ONSSA assistant answering a grounded question](docs/screenshots/injection-authority.png)

---

## Highlights

- **Grounded RAG** — retrieval always precedes generation; a relevance gate refuses
  off-topic questions *before* the LLM is called (anti-hallucination).
- **Hybrid retrieval** — FAISS vector search + BM25 keyword search fused with RRF.
  Measured **hit@5 = 14/15** vs 13/15 for naive vector-only ([eval.py](eval.py)).
- **Fully local, no API key** — Ollama for the LLM, sentence-transformers for
  embeddings, FAISS for search, Whisper + Piper for voice. Nothing leaves the machine.
- **Real chat UX** — persistent conversations with search/delete, streaming answers,
  source citations, live retrieval status, settings panel, 👍/👎 feedback.
- **Voice in & out** — 🎙️ speak your question (faster-whisper), 🔊 hear the answer
  (Piper), both offline.
- **Red-teamed** — prompt-injection tested and hardened; findings documented
  honestly in [docs/security.md](docs/security.md).

## Documentation

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Full architecture & every design decision with justifications and diagrams |
| [docs/security.md](docs/security.md) | Safety guardrails + prompt-injection red-team report |
| [docs/sample_questions.md](docs/sample_questions.md) | Sample questions with expected behavior |
| [docs/indexed_pages.md](docs/indexed_pages.md) | Auto-generated list of indexed ONSSA pages |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Original project plan / blueprint |

---

## Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.com/download)** installed and running
- ≈ 8 GB RAM for the default model (`mistral:7b`); 3B fallbacks documented below

## Setup

```bash
# 1. virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. dependencies + the project package
pip install -r requirements.txt
pip install -e .

# 3. pull the local LLM
ollama pull mistral:7b

# 4. verify everything is in place
python scripts/check_setup.py
```

## Build the knowledge base

```bash
python ingest.py        # scrape ONSSA pages → clean → chunk → embed → FAISS
```

Indexed pages are configured in [`data/pages.yaml`](data/pages.yaml).
Current corpus: **284 pages · 333 sections · 1,187 chunks**.

## Run the app

```bash
streamlit run app.py
```

> **Latency note:** on a CPU-only machine, `mistral:7b` takes several minutes per
> answer (prompt reading dominates). The live status box shows retrieved pages
> while it works. For faster demos, `ollama pull llama3.2:3b` and pick it in
> **⚙️ Paramètres**, or set `OLLAMA_MODEL=llama3.2:3b` in `.env`.

## Evaluate retrieval

```bash
python eval.py          # hit@5 over data/eval_questions.yaml (naive vs hybrid)
```

## Run the tests

```bash
pytest -q               # 24 unit & smoke tests
```

---

## Environment variables

Everything is optional — defaults live in `src/onssa_rag/config.py`. Copy
`.env.example` to `.env` to override. Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `mistral:7b` | LLM (any pulled model: `llama3.2:3b`, `qwen2.5:3b`…) |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-base` | sentence-transformers model |
| `TOP_K` | `5` | chunks kept after fusion |
| `SIMILARITY_THRESHOLD` / `BM25_GATE` | `0.825` / `12.0` | relevance gate (calibrated) |
| `WHISPER_MODEL` | `small` | voice input model (`tiny`/`base`/`small`/`medium`) |
| `PIPER_VOICE` | `fr_FR-siwis-medium` | French TTS voice |

**No paid LLM API key is required anywhere** — by construction.

## Repository layout

```
app.py                  Streamlit chat UI
ingest.py               knowledge-base build CLI
eval.py                 retrieval evaluation (hit@5)
src/onssa_rag/          pipeline package (config, scraping, cleaning, chunking,
                        embeddings, vectorstore, retriever, llm, rag,
                        conversations, voice)
data/pages.yaml         indexed ONSSA pages (source of truth)
data/eval_questions.yaml  retrieval eval set
scripts/check_setup.py  environment doctor
docs/                   architecture, security, sample questions, screenshots
tests/                  unit & smoke tests
```

## Data & ethics notice

Content is fetched from the public ONSSA website politely (1 request/second,
identifiable User-Agent, local caching so the site is hit once) for an
educational internship project. This is an **unofficial** assistant; answers are
generated automatically from published ONSSA content and are not an official
position, nor legal/medical/veterinary advice.
