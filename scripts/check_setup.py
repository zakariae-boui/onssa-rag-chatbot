"""Environment doctor for the ONSSA RAG chatbot.

Verifies Python version, dependencies, the Ollama server/model, and the
knowledge-base artifacts. Run after setup and before demos:

    python scripts/check_setup.py
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

OK, WARN, FAIL = "[ OK ]", "[WARN]", "[FAIL]"

REQUIRED_IMPORTS = {
    "streamlit": "streamlit",
    "requests": "requests",
    "trafilatura": "trafilatura",
    "bs4": "beautifulsoup4",
    "yaml": "PyYAML",
    "sentence_transformers": "sentence-transformers",
    "faiss": "faiss-cpu",
    "rank_bm25": "rank-bm25",
    "ollama": "ollama",
    "pandas": "pandas",
    "dotenv": "python-dotenv",
}


def check_python() -> bool:
    ok = sys.version_info >= (3, 10)
    print(f"{OK if ok else FAIL} Python {sys.version.split()[0]} (>= 3.10 required)")
    return ok


def check_imports() -> bool:
    all_ok = True
    for module, package in REQUIRED_IMPORTS.items():
        try:
            importlib.import_module(module)
            print(f"{OK} import {module} ({package})")
        except ImportError as exc:
            print(f"{FAIL} import {module} -> pip install {package} ({exc})")
            all_ok = False
    return all_ok


def check_ollama() -> None:
    import requests

    from onssa_rag import config

    try:
        resp = requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=5)
        resp.raise_for_status()
    except Exception as exc:
        print(
            f"{WARN} Ollama unreachable at {config.OLLAMA_HOST} — install and start it "
            f"(https://ollama.com/download). ({type(exc).__name__})"
        )
        return
    models = [m.get("name", "") for m in resp.json().get("models", [])]
    print(f"{OK} Ollama server up — models: {', '.join(models) or 'none'}")
    wanted = config.OLLAMA_MODEL.split(":")[0]
    if any(m.startswith(wanted) for m in models):
        print(f"{OK} configured model available: {config.OLLAMA_MODEL}")
    else:
        print(f"{WARN} model '{config.OLLAMA_MODEL}' not pulled -> run: ollama pull {config.OLLAMA_MODEL}")


def check_knowledge_base() -> None:
    from onssa_rag import config

    manifest = config.INDEX_DIR / "manifest.json"
    if manifest.exists():
        print(f"{OK} knowledge base present: {manifest}")
    else:
        print(f"{WARN} no index yet -> run: python ingest.py (Phases 1-2)")


def main() -> int:
    print("--- ONSSA RAG setup check ---")
    ok = check_python()
    ok = check_imports() and ok
    if ok:
        check_ollama()
        check_knowledge_base()
    else:
        print(f"{FAIL} fix the items above, then re-run.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
