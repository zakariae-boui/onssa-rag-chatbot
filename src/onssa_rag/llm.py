"""Ollama client: health check, streaming chat, short completions."""
from __future__ import annotations

from collections.abc import Iterator

import ollama

from . import config


def _client() -> ollama.Client:
    return ollama.Client(host=config.OLLAMA_HOST)


def health() -> tuple[bool, str]:
    """(ok, message) — server reachable and configured model pulled?"""
    try:
        models = [m.model or "" for m in _client().list().models]
    except Exception as exc:
        return False, f"Serveur Ollama injoignable ({config.OLLAMA_HOST}) : {exc}"
    base = config.OLLAMA_MODEL.split(":")[0]
    if not any(m.startswith(base) for m in models):
        return False, (
            f"Modèle {config.OLLAMA_MODEL} absent — exécutez : "
            f"ollama pull {config.OLLAMA_MODEL}"
        )
    return True, f"{config.OLLAMA_MODEL} prêt"


def available_models() -> list[str]:
    """Models pulled in the local Ollama, [] when the server is unreachable."""
    try:
        return sorted(m.model for m in _client().list().models if m.model)
    except Exception:
        return []


def chat_stream(
    messages: list[dict], temperature: float = config.LLM_TEMPERATURE, model: str | None = None
) -> Iterator[str]:
    for part in _client().chat(
        model=model or config.OLLAMA_MODEL,
        messages=messages,
        stream=True,
        keep_alive=config.OLLAMA_KEEP_ALIVE,
        options={"temperature": temperature, "num_ctx": config.OLLAMA_NUM_CTX},
    ):
        yield part["message"]["content"]


def complete(
    prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 150,
    model: str | None = None,
) -> str:
    resp = _client().generate(
        model=model or config.OLLAMA_MODEL,
        prompt=prompt,
        keep_alive=config.OLLAMA_KEEP_ALIVE,
        options={"temperature": temperature, "num_predict": max_tokens},
    )
    return resp["response"].strip()
