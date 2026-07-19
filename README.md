# 🇲🇦 Assistant ONSSA — RAG Chatbot

Customer-assistance chatbot for the official website of **ONSSA** (Office National de
Sécurité Sanitaire des produits Alimentaires, Morocco — https://www.onssa.gov.ma/).
Ask questions in natural language; answers are grounded exclusively in ONSSA website
content, in French, with source citations.

**Stack:** Python · Streamlit · Ollama (local open-source LLM) · FAISS ·
sentence-transformers · hybrid retrieval (vector + BM25). **No paid API key required.**

> 📐 Full architecture, decision justifications, and build plan: [PROJECT_PLAN.md](PROJECT_PLAN.md)

## Project status

| Phase | Content | Status |
|---|---|---|
| 0 | Repo skeleton, config, environment checks | ✅ |
| 1–2 | Ingestion: scrape → clean → chunk → embed → FAISS | ⏳ |
| 3 | RAG core (hybrid retrieval) + retrieval eval | ⏳ |
| 4 | Streamlit chat app | ⏳ |
| 5 | Hardening, docs, demo | ⏳ |

## Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.com/download)** installed and running
- ≈ 8 GB RAM for the default model (`mistral:7b`) — 3B fallbacks documented in `.env.example`

## Setup

```bash
# 1. create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. install dependencies + the project package
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

The list of indexed pages is configured in [`data/pages.yaml`](data/pages.yaml).

## Run the app

```bash
streamlit run app.py
```

## Evaluate retrieval

```bash
python eval.py          # hit@5 over data/eval_questions.yaml (naive vs hybrid)
```

## Environment variables

Everything is optional — copy `.env.example` to `.env` to override defaults
(LLM model, embedding model, top-k, similarity threshold, chunking, request throttle).
Defaults live in `src/onssa_rag/config.py`; each variable is documented in
[`.env.example`](.env.example).

## Repository layout

```
app.py                  Streamlit chat UI
ingest.py               knowledge-base build CLI (scrape → index)
eval.py                 retrieval evaluation (hit@5)
src/onssa_rag/          pipeline package (config, scraping, cleaning, chunking,
                        embeddings, vectorstore, retriever, llm, rag)
data/pages.yaml         indexed ONSSA pages (source of truth)
data/eval_questions.yaml  retrieval eval set
scripts/check_setup.py  environment doctor
tests/                  unit & smoke tests
docs/                   architecture, indexed pages, sample questions, screenshots
```

## Data notice

Content is fetched from the public ONSSA website politely (1 request/second,
identifiable User-Agent, local caching so the site is hit once) for an
educational internship project.
