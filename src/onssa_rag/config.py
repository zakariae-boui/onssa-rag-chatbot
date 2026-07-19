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
# Calibrated empirically for multilingual-e5-base: in-scope questions score
# 0.83+, out-of-scope 0.82 and below (e5 has a high cosine floor, so classic
# values like 0.30 would never trigger the fallback).
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.825"))
# BM25 leg of the gate: common-word matches reach ~8 (e.g. "prix" in tariff
# pages), confident keyword hits (Codex, Aid Al Adha) score 13+.
BM25_GATE = float(os.getenv("BM25_GATE", "12.0"))
# BM25 is a precision leg: only its top few, most confident exact-match hits
# join the fusion (at full weight) — its deeper tail is common-stem noise that
# demotes good vector results. Eval sweep: this setup 14/15 vs 13/15 vector-only.
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "1.0"))
BM25_CANDIDATES = int(os.getenv("BM25_CANDIDATES", "5"))
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
