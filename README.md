# 🇲🇦 Assistant ONSSA — RAG Chatbot

> Customer-assistance chatbot for the official **ONSSA** website
> (Office National de Sécurité Sanitaire des produits Alimentaires, Morocco —
> https://www.onssa.gov.ma/). It answers visitor questions in **French**, grounded
> **exclusively** in ONSSA website content, with source citations — and runs
> **100 % locally with no paid API**.

<p align="center">
  <code>Python</code> · <code>Streamlit</code> · <code>Ollama (Mistral 7B)</code> ·
  <code>FAISS</code> · <code>sentence-transformers</code> ·
  <code>hybrid retrieval (vector + BM25)</code> · <code>local voice (Whisper + Piper)</code>
</p>

---

## 📑 Table of contents

1. [What it does](#-what-it-does)
2. [Key features](#-key-features)
3. [Architecture](#-architecture)
4. [How a question is answered](#-how-a-question-is-answered)
5. [Evaluation results](#-evaluation-results)
6. [Technology choices](#-technology-choices)
7. [Setup & run](#-setup--run)
8. [Configuration](#-configuration)
9. [Deliverables map](#-deliverables-map)
10. [Documentation](#-documentation)
11. [Project structure](#-project-structure)

---

## 🎯 What it does

A visitor asks a natural-language question about ONSSA (missions, organisation,
métiers, réglementation, e-services, contacts, démarches). The system embeds the
question, retrieves the most relevant ONSSA text from a local vector database,
and a local LLM writes a **grounded French answer with citations**. If nothing
relevant is found, it says so instead of inventing — the anti-hallucination rule.

| | |
|---|---|
| **Corpus** | 284 ONSSA pages · 333 sections · **1,187 indexed chunks** |
| **Retrieval quality** | **hit@5 = 14/15** (hybrid) vs 13/15 (naive vector-only) |
| **Cost** | **€0** — no paid API; everything runs on the local machine |
| **Languages** | Answers in French; multilingual embeddings; voice in French |
| **Tests** | 24 unit & smoke tests |

---

## ✨ Key features

| Area | Feature |
|---|---|
| **RAG core** | Retrieval **always** precedes generation; relevance gate refuses off-topic questions *before* the LLM runs |
| **Hybrid retrieval** | FAISS vector search **+** BM25 keyword search fused with Reciprocal Rank Fusion |
| **Grounding** | Strict French system prompt: answer only from extracts, cite sources `[n]`, no legal/medical/veterinary advice |
| **Follow-ups** | Question-condensation rewrites "et pour l'exportation ?" into a standalone query |
| **Chat UX** | Persistent conversations (disk-backed) with **search / new / switch / delete**, streaming answers, live retrieval status |
| **Settings** | In-app model picker, temperature, top-k, context-size sliders |
| **Voice** | 🎙️ speak your question (faster-whisper) · 🔊 hear the answer (Piper) — both offline |
| **Feedback** | 👍/👎 per answer, logged to disk |
| **Safety** | Red-teamed against prompt injection; findings documented honestly |

---

## 🏗️ Architecture

Two independent halves share one artifact — the knowledge base. The **online** app
never touches the website.

```mermaid
flowchart LR
    subgraph OFFLINE["🔧 OFFLINE — ingest.py (run once)"]
        W[ONSSA website] --> S[Scrape + clean<br/>trafilatura]
        S --> C[Chunk<br/>heading-aware]
        C --> E[Embed<br/>multilingual-e5]
        E --> KB[(FAISS index<br/>+ metadata)]
    end
    subgraph ONLINE["💬 ONLINE — app.py (Streamlit)"]
        Q[User question] --> R[Hybrid retrieval<br/>vector + BM25 + gate]
        KB -. loaded once .-> R
        R --> G[Ollama LLM<br/>grounded, streamed]
        G --> A[French answer<br/>+ sources]
    end
```

Full rationale and diagrams: **[docs/architecture.md](docs/architecture.md)**.

---

## 🔄 How a question is answered

```mermaid
flowchart TD
    Q[Question] --> COND[Condense follow-ups<br/>→ standalone question]
    COND --> VEC[FAISS vector search]
    COND --> BM[BM25 keyword search]
    VEC --> RRF[Reciprocal Rank Fusion]
    BM --> RRF
    RRF --> GATE{Relevant enough?<br/>gate calibrated on e5}
    GATE -- no --> FB[« Information non trouvée »<br/>+ contacts · LLM NOT called]
    GATE -- yes --> EXP[Expand to full parent sections]
    EXP --> GEN[Ollama · grounded · streamed]
    GEN --> OUT[Answer + source URLs]
```

1. **Condense** follow-ups into standalone questions.
2. **Embed** and search FAISS (semantic) **and** BM25 (keywords) in parallel.
3. **Fuse** both rankings with RRF.
4. **Gate**: below threshold → fixed French fallback, LLM never called.
5. **Expand** winning chunks to their full sections (small-to-big).
6. **Generate** a grounded French answer, streamed, with citations.

---

## 📊 Evaluation results

Retrieval quality is **measured, not assumed** (`python eval.py`) — hit@5 over 15
questions with verified expected URLs:

| Retrieval strategy | hit@5 |
|---|:---:|
| Naive (vector-only) | 13 / 15 |
| **Hybrid (vector + BM25 + RRF)** | **14 / 15** ✅ |

The BM25 parameters were **chosen by a sweep** against this set — the engineering
story is *measure → diagnose → fix → re-measure*, not adding fashionable techniques.
(Hybrid initially *lost* 10/15 due to French morphology; a prefix-stemmer and using
BM25 as a precision leg fixed it. Details in [docs/architecture.md §5](docs/architecture.md).)

---

## 🧰 Technology choices

| Concern | Choice | Why (vs the alternative) |
|---|---|---|
| Orchestration | Plain Python (no LangChain) | 5 clear steps; every line justifiable, fewer deps |
| Scraping | `requests` + `trafilatura` | Site is server-rendered → no Selenium/Playwright needed |
| Embeddings | `multilingual-e5-base` | French-strong; rejected English-centric `all-MiniLM` |
| Vector DB | **FAISS** `IndexFlatIP` | Assignment requirement; exact search is instant at this size |
| Retrieval | Hybrid + RRF + relevance gate | Vectors miss acronyms; BM25 catches them; gate stops hallucination |
| LLM | **Mistral 7B** via Ollama | Strong French, open-source, local; **no API key** |
| Voice | faster-whisper + Piper | Fully local STT/TTS, consistent with no-API constraint |

---

## 🚀 Setup & run

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.com/download) running,
≈ 8 GB RAM for `mistral:7b`.

```bash
# 1. environment
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
pip install -e .

# 2. local LLM
ollama pull mistral:7b

# 3. verify setup
python scripts/check_setup.py

# 4. build the knowledge base (scrape → clean → chunk → embed → FAISS)
python ingest.py

# 5. run the app
streamlit run app.py
```

> ⏱️ **Latency note:** on a CPU-only machine, `mistral:7b` takes several minutes
> per answer (prompt reading dominates); the live status box shows retrieved pages
> meanwhile. For faster demos: `ollama pull llama3.2:3b` and pick it in
> **⚙️ Paramètres**, or set `OLLAMA_MODEL=llama3.2:3b` in `.env`.

```bash
python eval.py      # retrieval evaluation (hit@5, naive vs hybrid)
pytest -q           # 24 tests
```

---

## ⚙️ Configuration

All settings are environment variables with sane defaults
(`src/onssa_rag/config.py`); copy `.env.example` to `.env` to override. **No paid
API key exists anywhere.** Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | `mistral:7b` | LLM (any pulled model: `llama3.2:3b`, `qwen2.5:3b`…) |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-base` | sentence-transformers model |
| `TOP_K` | `5` | chunks kept after fusion |
| `SIMILARITY_THRESHOLD` / `BM25_GATE` | `0.825` / `12.0` | relevance gate (calibrated for e5) |
| `WHISPER_MODEL` | `small` | voice input (`tiny`/`base`/`small`/`medium`) |
| `PIPER_VOICE` | `fr_FR-siwis-medium` | French read-aloud voice |

---

## ✅ Deliverables map

Every assignment deliverable and where it lives:

| Deliverable | Location |
|---|---|
| Source code (GitHub) | this repository |
| Streamlit application | [`app.py`](app.py) |
| ONSSA ingestion/indexing script | [`ingest.py`](ingest.py) |
| Reusable knowledge base (clean text + vector DB) | `data/clean/` + `data/index/` |
| List of ONSSA pages indexed | [`data/pages.yaml`](data/pages.yaml) · [`docs/indexed_pages.md`](docs/indexed_pages.md) |
| README with setup & run | this file |
| Architecture decisions | [`docs/architecture.md`](docs/architecture.md) |
| Sample questions + expected behavior | [`docs/sample_questions.md`](docs/sample_questions.md) |
| Environment variable documentation | [`.env.example`](.env.example) + [Configuration](#-configuration) |
| No paid LLM API required | by construction (Ollama, local) |
| **Bonus:** retrieval evaluation | [`eval.py`](eval.py) — hit@5 |
| **Bonus:** security / red-team | [`docs/security.md`](docs/security.md) |
| **Bonus:** voice input & output | [`src/onssa_rag/voice.py`](src/onssa_rag/voice.py) |

---

## 📚 Documentation

| Doc | Contents |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Full architecture & design decisions, 4 diagrams |
| [docs/security.md](docs/security.md) | Safety guardrails + prompt-injection red-team report |
| [docs/sample_questions.md](docs/sample_questions.md) | 18 sample questions with expected behavior |
| [docs/indexed_pages.md](docs/indexed_pages.md) | Auto-generated list of indexed ONSSA pages |
| [PROJECT_PLAN.md](PROJECT_PLAN.md) | Original project blueprint |

### Example: prompt-injection resistance (from [docs/security.md](docs/security.md))

The bot was red-teamed. A fake-authority attack ("le directeur a approuvé…") is
cleanly refused:

![Authority injection blocked](docs/screenshots/injection-authority.png)

---

## 📁 Project structure

```
app.py                  Streamlit chat UI
ingest.py               knowledge-base build CLI (scrape → index)
eval.py                 retrieval evaluation (hit@5)
src/onssa_rag/
  config.py  scraping.py  cleaning.py  chunking.py  embeddings.py
  vectorstore.py  retriever.py  llm.py  rag.py  conversations.py  voice.py
data/
  pages.yaml            indexed ONSSA pages (source of truth)
  eval_questions.yaml   15-question eval set
  index/                FAISS index + metadata + manifest
docs/                   architecture · security · sample questions · screenshots
scripts/check_setup.py  environment doctor
tests/                  24 unit & smoke tests
```

---

## ⚖️ Data & ethics notice

Content is fetched from the public ONSSA website politely (1 request/second,
identifiable User-Agent, local caching so the site is hit once) for an educational
internship project. This is an **unofficial** assistant; answers are generated
automatically from published ONSSA content and are not an official position, nor
legal/medical/veterinary advice.
