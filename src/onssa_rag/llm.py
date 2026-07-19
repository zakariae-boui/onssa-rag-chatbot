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


def chat_stream(messages: list[dict], temperature: float = 0.2) -> Iterator[str]:
    for part in _client().chat(
        model=config.OLLAMA_MODEL,
        messages=messages,
        stream=True,
        options={"temperature": temperature},
    ):
        yield part["message"]["content"]


def complete(prompt: str, temperature: float = 0.0, max_tokens: int = 150) -> str:
    resp = _client().generate(
        model=config.OLLAMA_MODEL,
        prompt=prompt,
        options={"temperature": temperature, "num_predict": max_tokens},
    )
    return resp["response"].strip()
