"""Central configuration: every tunable comes from environment variables (.env).

Defaults are chosen so the project runs with no .env file at all.
See .env.example for documentation of each variable.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
RAW_HTML_DIR = DATA_DIR / "raw_html"
CLEAN_DIR = DATA_DIR / "clean"
INDEX_DIR = DATA_DIR / "index"
PAGES_CONFIG = DATA_DIR / "pages.yaml"
EVAL_QUESTIONS = DATA_DIR / "eval_questions.yaml"

# --- Ollama ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b")

# --- Embeddings ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

# --- RAG ---
TOP_K = int(os.getenv("TOP_K", "5"))
RETRIEVER_CANDIDATES = int(os.getenv("RETRIEVER_CANDIDATES", "20"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))
MAX_CONTEXT_CHARS = int(os.getenv("MAX_CONTEXT_CHARS", "8000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# --- Ingestion ---
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))
USER_AGENT = os.getenv(
    "USER_AGENT",
    "ONSSA-RAG-Chatbot/0.1 (educational internship project)",
)
SITEMAP_URL = "https://www.onssa.gov.ma/sitemap.xml"
